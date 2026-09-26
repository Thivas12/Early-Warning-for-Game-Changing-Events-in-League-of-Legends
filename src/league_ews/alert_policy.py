"""Calibration-only B3 alert policy with one-to-one event matching."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

import joblib  # type: ignore[import-untyped]
import numpy as np
from sklearn.metrics import average_precision_score

from league_ews.baseline_floor import _read_match
from league_ews.constants import EVENTS
from league_ews.final_split import freeze_final_split
from league_ews.raw_validation import ProcessingManifest
from league_ews.tabular_baseline import FEATURES, _bound_floor
from league_ews.tabular_baseline import _rows as tabular_rows

HORIZON_MS = 60_000
COOLDOWN_MS = 60_000
THRESHOLDS = tuple(float(v) for v in np.geomspace(1e-5, 1.0, 101))


@dataclass(frozen=True)
class MatchRisk:
    """One calibration match's prediction times, event onsets and scores."""

    times_ms: tuple[int, ...]
    events_ms: tuple[int, ...]
    risks: tuple[float, ...]


def evaluate_alerts(matches: list[MatchRisk], threshold: float) -> dict[str, float | int | None]:
    """Match chronological alerts to unique future event onsets within 60 seconds."""

    if not 0 < threshold <= 1 or not np.isfinite(threshold) or not matches:
        raise ValueError("Alert threshold and calibration matches must be valid")
    alerts = hits = events = 0
    leads: list[int] = []
    for match in matches:
        times, onsets, risks = match.times_ms, match.events_ms, match.risks
        if (
            len(times) != len(risks)
            or any(b <= a for a, b in pairwise(times))
            or any(b <= a for a, b in pairwise(onsets))
            or any(t < 0 for t in (*times, *onsets))
            or any(not 0 <= p <= 1 or not np.isfinite(p) for p in risks)
        ):
            raise ValueError("Invalid chronological alert input")
        events += len(onsets)
        last_alert = -COOLDOWN_MS - 1
        first_unmatched = 0
        for time, risk in zip(times, risks, strict=True):
            if risk < threshold or time - last_alert <= COOLDOWN_MS:
                continue
            alerts += 1
            last_alert = time
            while first_unmatched < len(onsets) and onsets[first_unmatched] <= time:
                first_unmatched += 1
            if first_unmatched < len(onsets) and onsets[first_unmatched] - time <= HORIZON_MS:
                hits += 1
                leads.append(onsets[first_unmatched] - time)
                first_unmatched += 1
    precision = hits / alerts if alerts else 0.0
    recall = hits / events if events else 0.0
    f1 = 2 * hits / (alerts + events) if alerts + events else 0.0
    return {
        "matches": len(matches),
        "events": events,
        "alerts": alerts,
        "matched_events": hits,
        "false_alerts": alerts - hits,
        "precision": precision,
        "event_recall": recall,
        "event_f1": f1,
        "false_alerts_per_game": (alerts - hits) / len(matches),
        "median_lead_seconds": float(np.median(leads)) / 1000 if leads else None,
        "p10_lead_seconds": float(np.percentile(leads, 10)) / 1000 if leads else None,
    }


def select_threshold(matches: list[MatchRisk]) -> tuple[float, dict[str, float | int | None]]:
    """Choose event F1; break ties by fewer false alerts and higher threshold."""

    results = [(threshold, evaluate_alerts(matches, threshold)) for threshold in THRESHOLDS]
    return max(
        results,
        key=lambda item: (
            cast(float, item[1]["event_f1"]),
            -cast(int, item[1]["false_alerts"]),
            item[0],
        ),
    )


def _calibration_risks(
    root: Path,
    entries: list[dict[str, object]],
    by_id: dict[str, Any],
    event: str,
    classifier: Any,
) -> tuple[list[MatchRisk], np.ndarray, np.ndarray]:
    """Reconstruct predictions with only checksum-verified calibration files."""

    label = f"y_{event}_60"
    vectors: list[list[float]] = []
    targets: list[int] = []
    pending: list[tuple[tuple[int, ...], tuple[int, ...], int]] = []
    for index, entry in enumerate(entries, start=1):
        match_id = str(entry["match_id"])
        record = by_id[match_id]
        payload = _read_match(root, match_id, record.sha256)
        observations = payload["timeline"]["observations"]
        rows = list(tabular_rows(payload, match_id, label))
        times = tuple(int(observation["timestamp_ms"]) for observation in observations)
        onsets = tuple(payload["event_index"][f"{event}_ms"])
        if len(rows) != record.observations or len(times) != len(rows):
            raise ValueError("Calibration observation inventory differs")
        vectors.extend(vector for vector, _ in rows)
        targets.extend(target for _, target in rows)
        pending.append((times, onsets, len(rows)))
        if index % 1000 == 0:
            print(f"Alert calibration: {index}/{len(entries)} matches", flush=True)
    x = np.asarray(vectors, dtype=np.float32)
    if x.ndim != 2 or x.shape[1] != len(FEATURES):
        raise ValueError("Invalid calibration feature matrix")
    scores = np.asarray(classifier.predict_proba(x)[:, 1], dtype=np.float64)
    if len(scores) != len(targets) or not np.isfinite(scores).all():
        raise ValueError("Invalid calibration predictions")
    matches: list[MatchRisk] = []
    offset = 0
    for times, onsets, size in pending:
        matches.append(
            MatchRisk(times, onsets, tuple(float(v) for v in scores[offset : offset + size]))
        )
        offset += size
    return matches, np.asarray(targets, dtype=np.int8), scores


def run_alert_policy(
    raw_root: str | Path,
    processed_root: str | Path,
    frame_path: str | Path,
    g2_report: str | Path,
    processed_audit: str | Path,
    split_path: str | Path,
    floor_root: str | Path,
    tabular_root: str | Path,
    output_root: str | Path,
    event: str,
) -> dict[str, object]:
    """Freeze B3's 60-second calibration threshold without opening test files."""

    if event not in EVENTS:
        raise ValueError("Unsupported alert event")
    split_bytes = Path(split_path).read_bytes()
    frozen = freeze_final_split(raw_root, processed_root, frame_path, g2_report, processed_audit)
    if json.loads(split_bytes) != frozen:
        raise ValueError("Private split differs from audited registered partitions")
    split_sha = hashlib.sha256(split_bytes).hexdigest()
    floor_sha = _bound_floor(Path(floor_root), split_sha)
    processing_bytes = (Path(processed_root) / "processing-manifest.json").read_bytes()
    processing_sha = hashlib.sha256(processing_bytes).hexdigest()
    processing = ProcessingManifest.model_validate_json(processing_bytes)
    by_id = {record.match_id: record for record in processing.matches}
    entries = cast(dict[str, list[dict[str, object]]], frozen["partitions"])["calibration"]
    if len(entries) != 6000 or len(by_id) != 36000:
        raise ValueError("Incomplete calibration or processed match inventory")
    label = f"y_{event}_60"
    report_path = Path(tabular_root) / f"report.{label}.json"
    report_bytes = report_path.read_bytes()
    b3_report_sha = hashlib.sha256(report_bytes).hexdigest()
    report = json.loads(report_bytes)
    model_path = Path(tabular_root) / f"model.{label}.joblib"
    if not (
        report.get("schema_version") == "league-ews-final-tabular-calibration-v1"
        and report.get("label") == label
        and report.get("feature_names") == list(FEATURES)
        and report.get("split_sha256") == split_sha
        and report.get("processing_manifest_sha256") == processing_sha
        and report.get("floor_model_sha256") == floor_sha
        and report.get("model_sha256") == hashlib.sha256(model_path.read_bytes()).hexdigest()
        and report.get("test_matches_unread") == 6000
    ):
        raise ValueError("B3 alert target differs from frozen calibration inputs")
    output = Path(output_root) / f"policy.{event}.json"
    bindings = {
        "schema_version": "league-ews-alert-policy-v1",
        "event": event,
        "label": label,
        "split_sha256": split_sha,
        "processing_manifest_sha256": processing_sha,
        "floor_model_sha256": floor_sha,
        "b3_report_sha256": b3_report_sha,
        "test_matches_unread": 6000,
        "threshold_grid": list(THRESHOLDS),
        "horizon_seconds": HORIZON_MS // 1000,
        "cooldown_seconds": COOLDOWN_MS // 1000,
        "criterion": "max-event-f1-then-min-false-alerts-then-max-threshold",
        "identifiers_in_report": False,
    }
    if output.exists():
        stored = json.loads(output.read_bytes())
        if (
            any(stored.get(key) != value for key, value in bindings.items())
            or stored.get("calibration_matches") != 6000
            or stored.get("selected_threshold") not in THRESHOLDS
            or abs(stored.get("calibration_row_ap", -1) - report["metrics"]["average_precision"])
            > 1e-8
            or not isinstance(stored.get("calibration_event_metrics"), dict)
            or stored["calibration_event_metrics"].get("matches") != 6000
        ):
            raise ValueError("Existing alert policy differs from frozen inputs")
        return cast(dict[str, object], stored)
    classifier = joblib.load(model_path)
    matches, targets, scores = _calibration_risks(
        Path(processed_root), entries, by_id, event, classifier
    )
    observed_ap = float(average_precision_score(targets, scores)) if targets.any() else 0.0
    if abs(observed_ap - report["metrics"]["average_precision"]) > 1e-8:
        raise ValueError("Recomputed calibration AP differs from original B3 report")
    threshold, metrics = select_threshold(matches)
    result: dict[str, object] = {
        **bindings,
        "calibration_matches": len(matches),
        "calibration_row_ap": observed_ap,
        "selected_threshold": threshold,
        "calibration_event_metrics": metrics,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    partial.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    partial.replace(output)
    return result


def summarize_alert_policy(root: str | Path) -> dict[str, object]:
    """Summarize three selected operating points without IDs or test access."""

    reports = [json.loads((Path(root) / f"policy.{event}.json").read_bytes()) for event in EVENTS]
    split_sha = reports[0]["split_sha256"]
    processing_sha = reports[0]["processing_manifest_sha256"]
    floor_sha = reports[0]["floor_model_sha256"]
    summary = {}
    for event, report in zip(EVENTS, reports, strict=True):
        if not (
            report.get("schema_version") == "league-ews-alert-policy-v1"
            and report.get("event") == event
            and report.get("label") == f"y_{event}_60"
            and report.get("split_sha256") == split_sha
            and report.get("processing_manifest_sha256") == processing_sha
            and report.get("floor_model_sha256") == floor_sha
            and isinstance(report.get("b3_report_sha256"), str)
            and report.get("threshold_grid") == list(THRESHOLDS)
            and report.get("selected_threshold") in THRESHOLDS
            and isinstance(report.get("calibration_event_metrics"), dict)
            and report["calibration_event_metrics"].get("matches") == 6000
            and report.get("horizon_seconds") == 60
            and report.get("cooldown_seconds") == 60
            and report.get("calibration_matches") == 6000
            and report.get("test_matches_unread") == 6000
            and report.get("identifiers_in_report") is False
        ):
            raise ValueError("Incomplete or inconsistent calibration alert policy")
        summary[event] = {
            "threshold": report["selected_threshold"],
            **report["calibration_event_metrics"],
        }
    return {
        "schema_version": "league-ews-alert-policy-summary-v1",
        "split_sha256": split_sha,
        "horizon_seconds": 60,
        "events": summary,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
