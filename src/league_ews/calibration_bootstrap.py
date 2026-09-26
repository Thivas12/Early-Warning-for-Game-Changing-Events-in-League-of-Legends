"""Paired whole-match calibration uncertainty for the frozen B2 and B3 controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import joblib  # type: ignore[import-untyped]
import numpy as np
from sklearn.metrics import average_precision_score

from league_ews.baseline_floor import LABELS, _probabilities, _read_match
from league_ews.baseline_floor import _rows as floor_rows
from league_ews.final_split import freeze_final_split
from league_ews.raw_validation import ProcessingManifest
from league_ews.tabular_baseline import FEATURES, _bound_floor
from league_ews.tabular_baseline import _rows as tabular_rows

REPLICATES = 1000
SEED = 20260915


def _sorted_ap_inputs(
    truth: np.ndarray, scores: np.ndarray, groups: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sort once, preserving the ends of equal-score groups for exact AP."""

    if len(truth) == 0 or not (truth.shape == scores.shape == groups.shape):
        raise ValueError("AP inputs must have equal nonempty shapes")
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError("AP scores must be finite probabilities")
    order = np.argsort(-scores, kind="stable")
    ordered_scores = scores[order]
    ends = np.r_[np.flatnonzero(np.diff(ordered_scores) != 0), len(order) - 1]
    return truth[order], groups[order], ends


def _weighted_ap(
    sorted_truth: np.ndarray,
    sorted_groups: np.ndarray,
    tie_ends: np.ndarray,
    match_counts: np.ndarray,
) -> float:
    """Exact average precision when each complete match is repeated by its weight."""

    weights = match_counts[sorted_groups]
    tp = np.cumsum(weights * sorted_truth)
    total = np.cumsum(weights)
    tp_at_end = tp[tie_ends]
    positives = int(tp_at_end[-1])
    if positives == 0:
        return 0.0
    total_at_end = total[tie_ends]
    precision = np.divide(
        tp_at_end,
        total_at_end,
        out=np.zeros(len(tie_ends), dtype=np.float64),
        where=total_at_end > 0,
    )
    newly_found = np.diff(tp_at_end, prepend=0)
    return float(np.sum(precision * newly_found) / positives)


def _interval(values: np.ndarray) -> list[float]:
    return [float(value) for value in np.quantile(values, [0.025, 0.975])]


def paired_match_bootstrap(
    truth: np.ndarray,
    b2: np.ndarray,
    b3: np.ndarray,
    groups: np.ndarray,
    *,
    matches: int,
    replicates: int = REPLICATES,
    seed: int = SEED,
) -> dict[str, object]:
    """Use identical resampled whole matches for both prediction methods."""

    if (
        matches < 1
        or replicates < 1
        or len(groups) == 0
        or groups.min() < 0
        or groups.max() >= matches
    ):
        raise ValueError("Invalid match groups or bootstrap replicates")
    b2_sorted = _sorted_ap_inputs(truth, b2, groups)
    b3_sorted = _sorted_ap_inputs(truth, b3, groups)
    draws = {"B2": np.empty(replicates), "B3": np.empty(replicates)}
    rng = np.random.default_rng(seed)
    for index in range(replicates):
        counts = np.bincount(rng.integers(matches, size=matches), minlength=matches)
        draws["B2"][index] = _weighted_ap(*b2_sorted, counts)
        draws["B3"][index] = _weighted_ap(*b3_sorted, counts)
        if (index + 1) % 250 == 0 and replicates == REPLICATES:
            print(f"Bootstrap {index + 1}/{replicates}", flush=True)
    observed_b2 = float(average_precision_score(truth, b2)) if truth.any() else 0.0
    observed_b3 = float(average_precision_score(truth, b3)) if truth.any() else 0.0
    delta = draws["B3"] - draws["B2"]
    return {
        "observed_ap": {"B2": observed_b2, "B3": observed_b3, "delta": observed_b3 - observed_b2},
        "ci95": {
            "B2": _interval(draws["B2"]),
            "B3": _interval(draws["B3"]),
            "paired_delta": _interval(delta),
        },
        "bootstrap_ap": {"B2": draws["B2"].tolist(), "B3": draws["B3"].tolist()},
        "replicates": replicates,
        "seed": seed,
        "resampling_unit": "whole-match",
    }


def _collect_calibration(
    root: Path,
    entries: list[dict[str, object]],
    by_id: dict[str, Any],
    label: str,
    floor_model: dict[str, Any],
    classifier: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    truth: list[int] = []
    b2_scores: list[float] = []
    vectors: list[list[float]] = []
    groups: list[int] = []
    event_name = label.split("_", 2)[1]
    for index, entry in enumerate(entries):
        match_id = str(entry["match_id"])
        payload = _read_match(root, match_id, by_id[match_id].sha256)
        floor = list(floor_rows(payload, match_id))
        tabular = list(tabular_rows(payload, match_id, label))
        if len(floor) != len(tabular) or len(floor) != by_id[match_id].observations:
            raise ValueError("Calibration observations differ from audited manifest")
        for (clock, labels, history), (vector, target) in zip(floor, tabular, strict=True):
            if labels[label] != target:
                raise ValueError("Calibration target differs across baseline feature paths")
            truth.append(target)
            b2_scores.append(_probabilities(floor_model, label, clock, history[event_name])[2])
            vectors.append(vector)
            groups.append(index)
        if (index + 1) % 1000 == 0:
            print(f"Calibration: {index + 1}/{len(entries)} matches", flush=True)
    x = np.asarray(vectors, dtype=np.float32)
    if x.ndim != 2 or x.shape[1] != len(FEATURES):
        raise ValueError("Calibration feature matrix is invalid")
    risk = np.asarray(classifier.predict_proba(x)[:, 1], dtype=np.float64)
    return (
        np.asarray(truth, dtype=np.int8),
        np.asarray(b2_scores, dtype=np.float64),
        risk,
        np.asarray(groups, dtype=np.int32),
    )


def run_calibration_bootstrap(
    raw_root: str | Path,
    processed_root: str | Path,
    frame_path: str | Path,
    g2_report: str | Path,
    processed_audit: str | Path,
    split_path: str | Path,
    floor_root: str | Path,
    tabular_root: str | Path,
    output_root: str | Path,
    label: str,
) -> dict[str, object]:
    """Validate provenance and resample calibration matches without reading test files."""

    if label not in LABELS:
        raise ValueError("Unsupported event/horizon target")
    split_bytes = Path(split_path).read_bytes()
    frozen = freeze_final_split(raw_root, processed_root, frame_path, g2_report, processed_audit)
    if json.loads(split_bytes) != frozen:
        raise ValueError("Private split differs from audited registered partitions")
    split_sha = hashlib.sha256(split_bytes).hexdigest()
    floor_sha = _bound_floor(Path(floor_root), split_sha)
    floor_model = json.loads((Path(floor_root) / "model.json").read_bytes())
    floor_report = json.loads((Path(floor_root) / "calibration-report.json").read_bytes())
    processing_bytes = (Path(processed_root) / "processing-manifest.json").read_bytes()
    processing_sha = hashlib.sha256(processing_bytes).hexdigest()
    processing = ProcessingManifest.model_validate_json(processing_bytes)
    by_id = {record.match_id: record for record in processing.matches}
    entries = cast(dict[str, list[dict[str, object]]], frozen["partitions"])["calibration"]
    if len(entries) != 6000 or len(by_id) != 36000:
        raise ValueError("Calibration membership or processed inventory is incomplete")
    b3_report_path = Path(tabular_root) / f"report.{label}.json"
    b3_report_bytes = b3_report_path.read_bytes()
    b3_report_sha = hashlib.sha256(b3_report_bytes).hexdigest()
    b3_report = json.loads(b3_report_bytes)
    b3_model_path = Path(tabular_root) / f"model.{label}.joblib"
    if not (
        b3_report.get("schema_version") == "league-ews-final-tabular-calibration-v1"
        and b3_report.get("label") == label
        and b3_report.get("feature_names") == list(FEATURES)
        and b3_report.get("split_sha256") == split_sha
        and b3_report.get("processing_manifest_sha256") == processing_sha
        and b3_report.get("floor_model_sha256") == floor_sha
        and b3_report.get("test_matches_unread") == 6000
        and b3_report.get("model_sha256") == hashlib.sha256(b3_model_path.read_bytes()).hexdigest()
    ):
        raise ValueError("B3 calibration artifacts differ from frozen inputs")
    root = Path(output_root)
    output = root / f"bootstrap.{label}.json"
    if output.exists():
        stored = json.loads(output.read_bytes())
        if not (
            stored.get("schema_version") == "league-ews-calibration-bootstrap-v1"
            and stored.get("label") == label
            and stored.get("split_sha256") == split_sha
            and stored.get("processing_manifest_sha256") == processing_sha
            and stored.get("floor_model_sha256") == floor_sha
            and stored.get("b3_report_sha256") == b3_report_sha
            and stored.get("replicates") == REPLICATES
            and stored.get("seed") == SEED
            and stored.get("calibration_matches") == 6000
            and stored.get("test_matches_unread") == 6000
            and stored.get("resampling_unit") == "whole-match"
        ):
            raise ValueError("Existing bootstrap artifact differs from frozen inputs")
        return {
            key: stored[key]
            for key in (
                "schema_version",
                "label",
                "observed_ap",
                "ci95",
                "replicates",
                "resampling_unit",
                "test_matches_unread",
                "identifiers_in_summary",
            )
        }
    classifier = joblib.load(b3_model_path)
    truth, b2, b3, groups = _collect_calibration(
        Path(processed_root), entries, by_id, label, floor_model, classifier
    )
    result = paired_match_bootstrap(truth, b2, b3, groups, matches=len(entries))
    observed = cast(dict[str, float], result["observed_ap"])
    if (
        abs(observed["B2"] - floor_report["metrics"]["B2"][label]["average_precision"]) > 1e-8
        or abs(observed["B3"] - b3_report["metrics"]["average_precision"]) > 1e-8
    ):
        raise ValueError("Recomputed calibration scores differ from original reports")
    result.update(
        {
            "schema_version": "league-ews-calibration-bootstrap-v1",
            "label": label,
            "split_sha256": split_sha,
            "processing_manifest_sha256": processing_sha,
            "floor_model_sha256": floor_sha,
            "b3_report_sha256": b3_report_sha,
            "calibration_matches": len(entries),
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        }
    )
    root.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    temporary.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    temporary.replace(output)
    return {
        key: result[key]
        for key in (
            "schema_version",
            "label",
            "observed_ap",
            "ci95",
            "replicates",
            "resampling_unit",
            "test_matches_unread",
            "identifiers_in_summary",
        )
    }


def summarize_calibration_bootstrap(root: str | Path) -> dict[str, object]:
    """Aggregate paired replicate deltas using the same match draws across targets."""

    reports = [
        json.loads((Path(root) / f"bootstrap.{label}.json").read_bytes()) for label in LABELS
    ]
    split_sha = reports[0]["split_sha256"]
    processing_sha = reports[0]["processing_manifest_sha256"]
    floor_sha = reports[0]["floor_model_sha256"]
    for label, report in zip(LABELS, reports, strict=True):
        if not (
            report.get("schema_version") == "league-ews-calibration-bootstrap-v1"
            and report.get("label") == label
            and report.get("split_sha256") == split_sha
            and report.get("processing_manifest_sha256") == processing_sha
            and report.get("floor_model_sha256") == floor_sha
            and isinstance(report.get("b3_report_sha256"), str)
            and report.get("replicates") == REPLICATES
            and report.get("seed") == SEED
            and report.get("calibration_matches") == 6000
            and report.get("test_matches_unread") == 6000
            and report.get("resampling_unit") == "whole-match"
            and all(len(report["bootstrap_ap"][name]) == REPLICATES for name in ("B2", "B3"))
        ):
            raise ValueError("Incomplete or inconsistent calibration bootstrap target")
    macro_draws = {
        name: np.mean([report["bootstrap_ap"][name] for report in reports], axis=0)
        for name in ("B2", "B3")
    }
    observed = {
        name: float(np.mean([report["observed_ap"][name] for report in reports]))
        for name in ("B2", "B3")
    }
    observed["delta"] = observed["B3"] - observed["B2"]
    return {
        "schema_version": "league-ews-calibration-bootstrap-summary-v1",
        "targets": len(LABELS),
        "replicates": REPLICATES,
        "resampling_unit": "whole-match",
        "observed_macro_ap": observed,
        "ci95": {
            "B2": _interval(macro_draws["B2"]),
            "B3": _interval(macro_draws["B3"]),
            "paired_delta": _interval(macro_draws["B3"] - macro_draws["B2"]),
        },
        "split_sha256": split_sha,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
