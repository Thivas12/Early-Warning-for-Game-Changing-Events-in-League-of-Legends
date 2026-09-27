"""Audit ten M1 event policies before opening the future-patch test set."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.alert_policy import COOLDOWN_MS, HORIZON_MS, THRESHOLDS, summarize_alert_policy
from league_ews.constants import EVENTS
from league_ews.m1_summary import summarize_m1_calibration
from league_ews.m1_training_plan import SEEDS

METRICS = ("precision", "event_recall", "event_f1", "false_alerts_per_game")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _range(values: list[float]) -> dict[str, float]:
    data = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(data)),
        "sample_standard_deviation": float(np.std(data, ddof=1)),
        "minimum": float(np.min(data)),
        "maximum": float(np.max(data)),
    }


def _check_event_metrics(metrics: Any) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise ValueError("M1 policy event metrics are missing")
    counts = ("matches", "events", "alerts", "matched_events", "false_alerts")
    if any(type(metrics.get(name)) is not int or metrics[name] < 0 for name in counts):
        raise ValueError("M1 policy event counts are invalid")
    matches, events, alerts, hits, false = (metrics[name] for name in counts)
    if matches != 6000 or hits > min(events, alerts) or false != alerts - hits:
        raise ValueError("M1 policy event inventory is inconsistent")
    expected = {
        "precision": hits / alerts if alerts else 0.0,
        "event_recall": hits / events if events else 0.0,
        "event_f1": 2 * hits / (alerts + events) if alerts + events else 0.0,
        "false_alerts_per_game": false / matches,
    }
    if any(
        type(metrics.get(key)) not in (float, int)
        or not math.isfinite(metrics[key])
        or abs(metrics[key] - value) > 1e-12
        for key, value in expected.items()
    ):
        raise ValueError("M1 policy event rates disagree with counts")
    for name in ("median_lead_seconds", "p10_lead_seconds"):
        value = metrics.get(name)
        if hits == 0 and value is None:
            continue
        if type(value) not in (float, int):
            raise ValueError("M1 policy lead time is invalid")
        lead = cast(float, value)
        if hits == 0 or not math.isfinite(lead) or not 0 < lead <= HORIZON_MS / 1000:
            raise ValueError("M1 policy lead time is invalid")
    return cast(dict[str, Any], metrics)


def summarize_m1_alert_policies(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    hazard_path: str | Path,
    freeze_path: str | Path,
    training_root: str | Path,
    calibration_root: str | Path,
    floor_root: str | Path,
    tabular_root: str | Path,
    policy_root: str | Path,
    b3_policy_root: str | Path,
) -> dict[str, Any]:
    """Bind all ten M1 thresholds and B3 operating points to one split."""

    calibration = summarize_m1_calibration(
        staging_root,
        normalizer_path,
        plan_path,
        hazard_path,
        freeze_path,
        training_root,
        calibration_root,
        floor_root,
        tabular_root,
    )
    calibration_sha = _sha((Path(calibration_root) / "ten-seed-summary.json").read_bytes())
    staging_bytes = (Path(staging_root) / "staging-manifest.json").read_bytes()
    if _sha(staging_bytes) != calibration["staging_manifest_sha256"]:
        raise ValueError("M1 policy staging differs from frozen calibration")
    processing_sha = json.loads(staging_bytes)["processing_manifest_sha256"]
    b3 = summarize_alert_policy(b3_policy_root)
    if b3["split_sha256"] != calibration["split_sha256"] or b3["test_matches_unread"] != 6000:
        raise ValueError("B3 alert policy differs from frozen M1 split")
    by_seed = {record["seed"]: record for record in calibration["seed_results"]}
    b3_events = cast(dict[str, dict[str, Any]], b3["events"])
    collected: dict[str, dict[str, list[float]]] = {
        event: {metric: [] for metric in METRICS} for event in EVENTS
    }
    thresholds: dict[str, list[dict[str, float | int]]] = {event: [] for event in EVENTS}
    counts: dict[str, int] = {}
    seed_reports: list[dict[str, Any]] = []
    root = Path(policy_root)
    for seed in SEEDS:
        data = (root / f"policy.seed-{seed}.json").read_bytes()
        report = json.loads(data)
        if (
            not isinstance(report, dict)
            or report.get("schema_version") != "league-ews-m1-alert-policy-v1"
            or report.get("seed") != seed
            or report.get("split_sha256") != calibration["split_sha256"]
            or report.get("processing_manifest_sha256") != processing_sha
            or report.get("ten_seed_summary_sha256") != calibration_sha
            or report.get("checkpoint_sha256") != by_seed[seed]["checkpoint_sha256"]
            or report.get("scores_sha256") != by_seed[seed]["scores_sha256"]
            or report.get("threshold_grid") != list(THRESHOLDS)
            or report.get("horizon_seconds") != HORIZON_MS // 1000
            or report.get("cooldown_seconds") != COOLDOWN_MS // 1000
            or report.get("criterion") != "max-event-f1-then-min-false-alerts-then-max-threshold"
            or report.get("calibration_matches") != 6000
            or report.get("selected_seed") is not None
            or report.get("test_matches_unread") != 6000
            or report.get("identifiers_in_report") is not False
            or not isinstance(report.get("events"), dict)
            or set(report["events"]) != set(EVENTS)
        ):
            raise ValueError("M1 alert policy differs from frozen calibration")
        for event in EVENTS:
            policy = report["events"][event]
            if not isinstance(policy, dict) or policy.get("threshold") not in THRESHOLDS:
                raise ValueError("M1 alert threshold differs from frozen grid")
            metrics = _check_event_metrics(policy.get("calibration_event_metrics"))
            if metrics["events"] != b3_events[event]["events"]:
                raise ValueError("M1 and B3 alert policies disagree on event inventory")
            if event in counts and counts[event] != metrics["events"]:
                raise ValueError("M1 seeds disagree on calibration event inventory")
            counts[event] = metrics["events"]
            thresholds[event].append({"seed": seed, "threshold": policy["threshold"]})
            for name in METRICS:
                collected[event][name].append(float(metrics[name]))
        seed_reports.append({"seed": seed, "policy_sha256": _sha(data)})

    result: dict[str, Any] = {
        "schema_version": "league-ews-m1-ten-seed-alert-summary-v1",
        "split_sha256": calibration["split_sha256"],
        "ten_seed_calibration_sha256": calibration_sha,
        "b3_policy_sha256": {
            event: _sha((Path(b3_policy_root) / f"policy.{event}.json").read_bytes())
            for event in EVENTS
        },
        "seed_count": len(SEEDS),
        "calibration_matches": 6000,
        "seed_reports": seed_reports,
        "events": {
            event: {
                "events": counts[event],
                "thresholds": thresholds[event],
                "m1": {name: _range(collected[event][name]) for name in METRICS},
                "b3": {name: b3_events[event][name] for name in METRICS},
            }
            for event in EVENTS
        },
        "selected_seed": None,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    output = root / "ten-seed-alert-summary.json"
    content = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    if output.exists():
        if output.read_bytes() != content:
            raise ValueError("Existing M1 alert summary differs from frozen inputs")
    else:
        temporary = output.with_suffix(".json.partial")
        temporary.write_bytes(content)
        temporary.replace(output)
    return result
