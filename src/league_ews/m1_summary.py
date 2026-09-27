"""Audit all frozen M1 calibration scores and compare their mean with B3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.m1_calibration import _completed_checkpoints
from league_ews.m1_training import _bound_inputs
from league_ews.m1_training_plan import SEEDS
from league_ews.metrics import probabilistic_metrics
from league_ews.tabular_baseline import summarize_final_tabular


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


def summarize_m1_calibration(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    hazard_path: str | Path,
    freeze_path: str | Path,
    training_root: str | Path,
    calibration_root: str | Path,
    floor_root: str | Path,
    tabular_root: str | Path,
) -> dict[str, Any]:
    """Recompute all ten seed metrics on calibration without opening test data."""

    stage = Path(staging_root)
    manifest, _, freeze_sha = _bound_inputs(
        stage, Path(normalizer_path), Path(plan_path), Path(hazard_path), Path(freeze_path)
    )
    manifest_sha = _sha((stage / "staging-manifest.json").read_bytes())
    normalizer_sha = _sha(Path(normalizer_path).read_bytes())
    checkpoints, states = _completed_checkpoints(Path(training_root), freeze_sha)
    device = states[SEEDS[0]]["device"]
    torch_version = states[SEEDS[0]]["torch_version"]
    b3 = summarize_final_tabular(tabular_root, floor_root)
    if (
        b3["split_sha256"] != manifest["split_sha256"]
        or b3["targets"] != len(LABELS)
        or b3["test_matches_unread"] != 6000
        or b3["identifiers_in_summary"] is not False
    ):
        raise ValueError("B3 and M1 calibration are bound to different frozen splits")
    b3_macro = float(cast(dict[str, float], b3["calibration_macro_average_precision"])["B3"])
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
            or report.get("schema_version") != "league-ews-m1-calibration-v1"
            or report.get("seed") != seed
            or report.get("freeze_sha256") != freeze_sha
            or report.get("normalizer_sha256") != normalizer_sha
            or report.get("staging_manifest_sha256") != manifest_sha
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
            raise ValueError("M1 calibration report differs from frozen seed inputs")
        with np.load(folder / "calibration-scores.npz", allow_pickle=False) as saved:
            if set(saved.files) != {"probabilities", "targets", "match_offsets"}:
                raise ValueError("M1 calibration score array inventory differs")
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
            or np.any(np.diff(scores.reshape(len(scores), 3, 4), axis=-1) < 0)
            or report.get("calibration_observations") != len(scores)
        ):
            raise ValueError("M1 calibration scores differ from the frozen partition")
        if reference_truth is None:
            reference_truth = truth.copy()
            reference_offsets = offsets.copy()
            observations = len(scores)
        elif (
            reference_offsets is None
            or not np.array_equal(truth, reference_truth)
            or not np.array_equal(offsets, reference_offsets)
        ):
            raise ValueError("M1 seeds disagree on calibration truth or match order")
        metrics = {
            label: probabilistic_metrics(truth[:, column], scores[:, column])
            for column, label in enumerate(LABELS)
        }
        if report.get("metrics") != metrics:
            raise ValueError("M1 calibration metrics differ from the score arrays")
        macro = float(
            np.mean([float(metrics[label]["average_precision"] or 0.0) for label in LABELS])
        )
        if report.get("macro_average_precision") != macro:
            raise ValueError("M1 calibration macro AP differs from target metrics")
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
        "schema_version": "league-ews-m1-ten-seed-calibration-v1",
        "freeze_sha256": freeze_sha,
        "split_sha256": manifest["split_sha256"],
        "staging_manifest_sha256": manifest_sha,
        "normalizer_sha256": normalizer_sha,
        "b3_calibration_report_sha256": _sha(
            (Path(floor_root) / "calibration-report.json").read_bytes()
        ),
        "b3_target_report_sha256": {
            label: _sha((Path(tabular_root) / f"report.{label}.json").read_bytes())
            for label in LABELS
        },
        "device": device,
        "torch_version": torch_version,
        "seed_count": len(SEEDS),
        "calibration_matches": 6000,
        "calibration_observations": observations,
        "seed_results": seed_results,
        "macro_average_precision": _range(macro_values),
        "per_target_average_precision": {label: _range(by_label[label]) for label in LABELS},
        "b3_macro_average_precision": b3_macro,
        "mean_delta_vs_b3": float(np.mean(macro_values)) - b3_macro,
        "selected_seed": None,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    output = root / "ten-seed-summary.json"
    content = (json.dumps(summary, sort_keys=True, indent=2) + "\n").encode()
    if output.exists():
        if output.read_bytes() != content:
            raise ValueError("Existing M1 ten-seed summary differs from frozen inputs")
    else:
        temporary = output.with_suffix(".json.partial")
        temporary.write_bytes(content)
        temporary.replace(output)
    return summary
