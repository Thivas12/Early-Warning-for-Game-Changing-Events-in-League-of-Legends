"""Checksum-bound M2 calibration comparison and chronological alert replay."""

from __future__ import annotations

import hashlib
import json
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.alert_policy import MatchRisk, evaluate_alerts, select_threshold
from league_ews.baseline_floor import LABELS, _read_match
from league_ews.constants import EVENTS
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.m1_summary import _range
from league_ews.m1_training_plan import SEEDS
from league_ews.m2_backend import MODES
from league_ews.metrics import probabilistic_metrics
from league_ews.raw_validation import ProcessingManifest


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_scores(
    scores: np.ndarray,
    truth: np.ndarray,
    offsets: np.ndarray,
    expected: np.ndarray,
    expected_offsets: np.ndarray,
) -> None:
    if (
        scores.shape != expected.shape
        or truth.shape != expected.shape
        or not np.array_equal(truth, expected)
        or not np.array_equal(offsets, expected_offsets)
        or not np.isfinite(scores).all()
        or np.any((scores < 0) | (scores > 1))
        or np.any(np.diff(scores.reshape(len(scores), 3, 4), axis=-1) < 0)
    ):
        raise ValueError("M2 probabilities, labels or match order differ from frozen calibration")


def _later_alerts(
    scores: np.ndarray,
    offsets: np.ndarray,
    times: list[tuple[int, ...]],
    onsets: dict[str, list[tuple[int, ...]]],
    early: list[int],
    later: list[int],
) -> dict[str, Any]:
    """Fit a threshold only on earlier calibration matches, score later matches."""

    output: dict[str, Any] = {}
    for event_index, event in enumerate(EVENTS):
        matches = [
            MatchRisk(
                times[index],
                onsets[event][index],
                tuple(float(v) for v in scores[start:end, event_index * 4 + 3]),
            )
            for index, (start, end) in enumerate(pairwise(offsets))
        ]
        threshold, early_metrics = select_threshold([matches[i] for i in early])
        output[event] = {
            "threshold_selected_on_early_half": threshold,
            "early_metrics": early_metrics,
            "later_metrics": evaluate_alerts([matches[i] for i in later], threshold),
        }
    return output


def audit_m2_calibration_utility(
    hybrid_freeze: str | Path,
    split_path: str | Path,
    processed_root: str | Path,
    calibration_root: str | Path,
    m1_summary_path: str | Path,
    m1_diagnostic_path: str | Path,
    output_root: str | Path,
    *,
    mode: str,
) -> dict[str, Any]:
    """Review ten seeds without accessing the sealed test patch or selecting a seed."""

    if mode not in MODES:
        raise ValueError("M2 utility mode differs from the hybrid plan")
    frozen_file, split_file = Path(hybrid_freeze), Path(split_path)
    frozen, split = json.loads(frozen_file.read_bytes()), json.loads(split_file.read_bytes())
    m1_file, diagnostic_file = Path(m1_summary_path), Path(m1_diagnostic_path)
    m1, diagnostic = json.loads(m1_file.read_bytes()), json.loads(diagnostic_file.read_bytes())
    root = Path(processed_root)
    manifest_file = root / "processing-manifest.json"
    inventory = ProcessingManifest.model_validate_json(manifest_file.read_bytes())
    entries = split["partitions"]["calibration"]
    if (
        frozen.get("schema_version") != "league-ews-m2-hybrid-freeze-v1"
        or frozen.get("split_sha256") != _sha(split_file)
        or frozen.get("modes") != list(MODES)
        or frozen.get("seeds") != SEEDS
        or split.get("schema_version") != "league-ews-final-split-v1"
        or split.get("processing_manifest_sha256") != _sha(manifest_file)
        or split.get("summary", {}).get("counts")
        != {"train": 24000, "calibration": 6000, "test": 6000}
        or split["summary"]["patches"]["calibration"] != ["16.16"]
        or len(entries) != 6000
        or len(inventory.matches) != 36000
        or m1.get("schema_version") != "league-ews-m1-ten-seed-calibration-v1"
        or m1.get("split_sha256") != _sha(split_file)
        or m1.get("seed_count") != len(SEEDS)
        or m1.get("selected_seed") is not None
        or diagnostic.get("schema_version")
        != "league-ews-m1-alert-opportunity-diagnostic-v1"
        or diagnostic.get("calibration_summary_sha256") != _sha(m1_file)
        or diagnostic.get("split_sha256") != _sha(split_file)
        or diagnostic.get("processing_manifest_sha256") != _sha(manifest_file)
        or diagnostic.get("seed_count") != len(SEEDS)
        or any(row.get("test_matches_unread") != 6000 for row in (frozen, m1, diagnostic))
    ):
        raise ValueError("M2 comparison differs from frozen split or M1 reference")
    early, later = _chronological_halves(entries)
    by_id = {record.match_id: record for record in inventory.matches}
    if len(by_id) != 36000 or len({row["match_id"] for row in entries}) != 6000:
        raise ValueError("M2 comparison match inventory is duplicated")
    times: list[tuple[int, ...]] = []
    onsets: dict[str, list[tuple[int, ...]]] = {event: [] for event in EVENTS}
    labels: list[list[int]] = []
    offsets = [0]
    for entry in entries:
        match_id = entry["match_id"]
        if entry["game_version_patch"] != "16.16" or match_id not in by_id:
            raise ValueError("M2 comparison match lies outside calibration")
        payload = _read_match(root, match_id, by_id[match_id].sha256)
        observations, rows = payload["timeline"]["observations"], payload["labels"]
        stamps = tuple(int(row["timestamp_ms"]) for row in observations)
        if (
            len(stamps) != by_id[match_id].observations
            or len(rows) != len(stamps)
            or any(b <= a for a, b in pairwise(stamps))
            or any(row["timestamp_ms"] != stamp for row, stamp in zip(rows, stamps, strict=True))
        ):
            raise ValueError("M2 comparison observation inventory differs")
        times.append(stamps)
        labels.extend([[row[label] for label in LABELS] for row in rows])
        offsets.append(offsets[-1] + len(stamps))
        for event in EVENTS:
            onsets[event].append(tuple(payload["event_index"][f"{event}_ms"]))
    truth = np.asarray(labels, dtype=np.int8)
    expected_offsets = np.asarray(offsets, dtype=np.int64)
    if truth.shape != (offsets[-1], len(LABELS)) or not np.isin(truth, (0, 1)).all():
        raise ValueError("M2 comparison labels differ from frozen calibration")

    seed_results: list[dict[str, Any]] = []
    per_target: dict[str, list[float]] = {label: [] for label in LABELS}
    per_target_brier: dict[str, list[float]] = {label: [] for label in LABELS}
    per_event: dict[str, dict[str, list[float]]] = {
        event: {metric: [] for metric in ("event_recall", "event_f1", "false_alerts_per_game")}
        for event in EVENTS
    }
    cal_root = Path(calibration_root) / mode
    reference_checkpoints: dict[str, str] | None = None
    for seed in SEEDS:
        folder = cal_root / f"seed-{seed}"
        report_file = folder / "calibration-report.json"
        scores_file = folder / "calibration-scores.npz"
        report = json.loads(report_file.read_bytes())
        if (
            report.get("schema_version") != "league-ews-m2-hybrid-calibration-v1"
            or report.get("mode") != mode
            or report.get("seed") != seed
            or report.get("freeze_sha256") != _sha(frozen_file)
            or report.get("scores_sha256") != _sha(scores_file)
            or report.get("calibration_matches") != 6000
            or report.get("calibration_observations") != len(truth)
            or report.get("targets") != list(LABELS)
            or report.get("test_matches_unread") != 6000
            or report.get("identifiers_in_report") is not False
            or set(report.get("all_seed_checkpoint_sha256", {})) != {str(value) for value in SEEDS}
            or report.get("checkpoint_sha256")
            != report["all_seed_checkpoint_sha256"].get(str(seed))
        ):
            raise ValueError("M2 calibration report differs from ten completed seeds")
        if reference_checkpoints is None:
            reference_checkpoints = report["all_seed_checkpoint_sha256"]
        elif report["all_seed_checkpoint_sha256"] != reference_checkpoints:
            raise ValueError("M2 calibration reports disagree on completed checkpoints")
        with np.load(scores_file, allow_pickle=False) as saved:
            if set(saved.files) != {"probabilities", "targets", "match_offsets"}:
                raise ValueError("M2 calibration score inventory differs")
            scores, saved_truth, saved_offsets = (
                saved["probabilities"], saved["targets"], saved["match_offsets"]
            )
        _validate_scores(scores, saved_truth, saved_offsets, truth, expected_offsets)
        metrics = {
            label: probabilistic_metrics(truth[:, column], scores[:, column])
            for column, label in enumerate(LABELS)
        }
        macro = float(
            np.mean([float(metrics[label]["average_precision"] or 0) for label in LABELS])
        )
        if metrics != report.get("metrics") or macro != report.get("macro_average_precision"):
            raise ValueError("M2 calibration metrics differ from saved probabilities")
        alert_results = _later_alerts(scores, saved_offsets, times, onsets, early, later)
        for label in LABELS:
            per_target[label].append(float(metrics[label]["average_precision"] or 0))
            per_target_brier[label].append(float(metrics[label]["brier"] or 0))
        for event in EVENTS:
            for metric in per_event[event]:
                per_event[event][metric].append(
                    float(alert_results[event]["later_metrics"][metric])
                )
        seed_results.append(
            {
                "seed": seed,
                "macro_average_precision": macro,
                "report_sha256": _sha(report_file),
                "scores_sha256": _sha(scores_file),
                "events": alert_results,
            }
        )
        print(f"M2 {mode}: audited seed {seed}", flush=True)
    result = {
        "schema_version": "league-ews-m2-calibration-utility-v1",
        "mode": mode,
        "hybrid_freeze_sha256": _sha(frozen_file),
        "split_sha256": _sha(split_file),
        "processing_manifest_sha256": _sha(manifest_file),
        "m1_calibration_summary_sha256": _sha(m1_file),
        "m1_alert_diagnostic_sha256": _sha(diagnostic_file),
        "calibration_matches": 6000,
        "earlier_half_matches": len(early),
        "later_half_matches": len(later),
        "seed_count": len(SEEDS),
        "seed_results": seed_results,
        "macro_average_precision": _range(
            [row["macro_average_precision"] for row in seed_results]
        ),
        "per_target_average_precision": {
            label: _range(values) for label, values in per_target.items()
        },
        "per_target_brier_score": {
            label: _range(values) for label, values in per_target_brier.items()
        },
        "later_half_alerts": {
            event: {metric: _range(values) for metric, values in metrics.items()}
            for event, metrics in per_event.items()
        },
        "m1_macro_average_precision": m1["macro_average_precision"]["mean"],
        "b3_macro_average_precision": m1["b3_macro_average_precision"],
        "m1_later_half_alerts": diagnostic["later_half_summary"],
        "selected_seed": None,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
        "interpretation": (
            "Exploratory calibration comparison. Each event threshold is fit on the earlier "
            "1,500 matches per route and replayed on the later 1,500 per route. "
            "B3 AP uses full calibration; M1 later-half alerts use its own earlier-half "
            "threshold. "
            "No original test or new confirmatory cohort is evaluated."
        ),
    }
    output = Path(output_root) / f"utility.{mode}.json"
    content = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if output.exists():
        if output.read_bytes() != content:
            raise ValueError("Existing M2 utility result differs from frozen inputs")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        partial = output.with_suffix(".json.partial")
        partial.write_bytes(content)
        partial.replace(output)
    return result
