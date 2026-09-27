"""Summarize all ten frozen B4 calibration runs without seed selection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.b4_calibration import _completed_checkpoints
from league_ews.b4_normalizer import _validated_manifest
from league_ews.b4_plan import SEEDS, freeze_b4_plan
from league_ews.baseline_floor import LABELS
from league_ews.metrics import probabilistic_metrics


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _range(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(array)),
        "sample_standard_deviation": float(np.std(array, ddof=1)),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
    }


def summarize_b4_calibration(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    freeze_path: str | Path,
    training_root: str | Path,
    calibration_root: str | Path,
) -> dict[str, Any]:
    """Verify every score against its source and report across all fixed seeds."""

    stage = Path(staging_root)
    frozen = freeze_b4_plan(stage, normalizer_path, plan_path, freeze_path)
    if frozen["seeds"] != SEEDS:
        raise ValueError("B4 summary requires all ten frozen seeds")
    manifest_bytes, _ = _validated_manifest(stage)
    freeze_sha = _sha(Path(freeze_path).read_bytes())
    normalizer_sha = _sha(Path(normalizer_path).read_bytes())
    checkpoints, states = _completed_checkpoints(Path(training_root), SEEDS, freeze_sha)
    device = states[SEEDS[0]]["device"]
    torch_version = states[SEEDS[0]]["torch_version"]
    root = Path(calibration_root)
    seed_results: list[dict[str, Any]] = []
    by_label: dict[str, list[float]] = {label: [] for label in LABELS}
    macro_values: list[float] = []
    reference_truth: np.ndarray | None = None
    reference_offsets: np.ndarray | None = None
    observations: int | None = None

    for seed in SEEDS:
        folder = root / f"seed-{seed}"
        report_bytes = (folder / "calibration-report.json").read_bytes()
        report = json.loads(report_bytes)
        score_bytes = (folder / "calibration-scores.npz").read_bytes()
        if (
            not isinstance(report, dict)
            or report.get("schema_version") != "league-ews-b4-calibration-v1"
            or report.get("seed") != seed
            or report.get("freeze_sha256") != freeze_sha
            or report.get("normalizer_sha256") != normalizer_sha
            or report.get("staging_manifest_sha256") != _sha(manifest_bytes)
            or report.get("all_seed_checkpoint_sha256") != checkpoints
            or report.get("checkpoint_sha256") != checkpoints[str(seed)]
            or report.get("scores_sha256") != _sha(score_bytes)
            or report.get("device") != device
            or report.get("torch_version") != torch_version
            or report.get("calibration_matches") != 6000
            or report.get("targets") != list(LABELS)
            or report.get("test_matches_unread") != 6000
            or report.get("identifiers_in_report") is not False
        ):
            raise ValueError("B4 calibration report differs from frozen seed inputs")
        with np.load(folder / "calibration-scores.npz", allow_pickle=False) as saved:
            if set(saved.files) != {"probabilities", "targets", "match_offsets"}:
                raise ValueError("B4 calibration score array inventory differs")
            scores = saved["probabilities"]
            truth = saved["targets"]
            offsets = saved["match_offsets"]
        if (
            scores.ndim != 2
            or scores.shape[1] != len(LABELS)
            or scores.shape != truth.shape
            or offsets.shape != (6001,)
            or offsets[0] != 0
            or offsets[-1] != len(scores)
            or np.any(np.diff(offsets) <= 0)
            or not np.isin(truth, (0, 1)).all()
            or not np.isfinite(scores).all()
            or np.any((scores < 0) | (scores > 1))
            or report.get("calibration_observations") != len(scores)
        ):
            raise ValueError("B4 calibration scores differ from the frozen partition")
        if reference_truth is None:
            reference_truth = truth.copy()
            reference_offsets = offsets.copy()
            observations = len(scores)
        elif (
            reference_offsets is None
            or not np.array_equal(truth, reference_truth)
            or not np.array_equal(offsets, reference_offsets)
        ):
            raise ValueError("B4 seeds disagree on calibration truth or match order")
        metrics = {
            label: probabilistic_metrics(truth[:, column], scores[:, column])
            for column, label in enumerate(LABELS)
        }
        if report.get("metrics") != metrics:
            raise ValueError("B4 calibration metrics differ from the score arrays")
        macro = float(
            np.mean([float(metrics[label]["average_precision"] or 0.0) for label in LABELS])
        )
        if report.get("macro_average_precision") != macro:
            raise ValueError("B4 calibration macro AP differs from target metrics")
        for label in LABELS:
            by_label[label].append(float(metrics[label]["average_precision"] or 0.0))
        macro_values.append(macro)
        seed_results.append(
            {
                "seed": seed,
                "macro_average_precision": macro,
                "report_sha256": _sha(report_bytes),
                "scores_sha256": _sha(score_bytes),
                "checkpoint_sha256": checkpoints[str(seed)],
            }
        )

    summary: dict[str, Any] = {
        "schema_version": "league-ews-b4-ten-seed-calibration-v1",
        "freeze_sha256": freeze_sha,
        "staging_manifest_sha256": _sha(manifest_bytes),
        "normalizer_sha256": normalizer_sha,
        "device": device,
        "torch_version": torch_version,
        "seed_count": len(SEEDS),
        "calibration_matches": 6000,
        "calibration_observations": observations,
        "seed_results": seed_results,
        "macro_average_precision": _range(macro_values),
        "per_target_average_precision": {label: _range(by_label[label]) for label in LABELS},
        "selected_seed": None,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    output = root / "ten-seed-summary.json"
    content = (json.dumps(summary, sort_keys=True, indent=2) + "\n").encode()
    if output.exists():
        if output.read_bytes() != content:
            raise ValueError("Existing B4 ten-seed summary differs from frozen inputs")
    else:
        temporary = output.with_suffix(".json.partial")
        temporary.write_bytes(content)
        temporary.replace(output)
    return summary
