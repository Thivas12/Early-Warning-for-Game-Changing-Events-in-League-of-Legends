"""Audit ten registered M1 ablation seeds against the original M1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.m1_ablation_calibration import _completed_variant_checkpoints, _sha
from league_ews.m1_ablation_plan import freeze_m1_ablations
from league_ews.m1_ablation_training import SUPPORTED_VARIANTS
from league_ews.m1_summary import _range
from league_ews.m1_training import _bound_inputs
from league_ews.m1_training_plan import SEEDS
from league_ews.metrics import probabilistic_metrics


def summarize_m1_graph_ablation(
    staging_root: str | Path,
    normalizer_path: str | Path,
    training_plan_path: str | Path,
    hazard_path: str | Path,
    training_freeze_path: str | Path,
    ablation_plan_path: str | Path,
    ablation_freeze_path: str | Path,
    calibration_summary_path: str | Path,
    alert_summary_path: str | Path,
    training_root: str | Path,
    calibration_root: str | Path,
    *,
    variant: str,
) -> dict[str, Any]:
    """Recalculate all ten calibration scores without selecting a seed."""

    if variant not in SUPPORTED_VARIANTS:
        raise ValueError("M1 graph ablation variant is not registered for scoring")
    ablation_path = Path(ablation_freeze_path)
    if not ablation_path.is_file():
        raise ValueError("M1 ablation freeze must precede summary")
    frozen = freeze_m1_ablations(
        ablation_plan_path,
        training_plan_path,
        training_freeze_path,
        calibration_summary_path,
        alert_summary_path,
        ablation_path,
    )
    stage = Path(staging_root)
    manifest, _, training_sha = _bound_inputs(
        stage,
        Path(normalizer_path),
        Path(training_plan_path),
        Path(hazard_path),
        Path(training_freeze_path),
    )
    if (
        frozen["training_freeze_sha256"] != training_sha
        or frozen["split_sha256"] != manifest["split_sha256"]
    ):
        raise ValueError("Graph ablation summary differs from frozen split")
    ablation_sha = _sha(ablation_path.read_bytes())
    hashes, states = _completed_variant_checkpoints(
        Path(training_root), variant, ablation_sha, training_sha
    )
    original_bytes = Path(calibration_summary_path).read_bytes()
    original = json.loads(original_bytes)
    original_seeds = original.get("seed_results", []) if isinstance(original, dict) else []
    if (
        not isinstance(original, dict)
        or original.get("schema_version") != "league-ews-m1-ten-seed-calibration-v1"
        or original.get("freeze_sha256") != training_sha
        or original.get("split_sha256") != manifest["split_sha256"]
        or original.get("seed_count") != len(SEEDS)
        or not isinstance(original_seeds, list)
        or [entry.get("seed") for entry in original_seeds] != SEEDS
        or original.get("selected_seed") is not None
        or original.get("test_matches_unread") != 6000
        or original.get("identifiers_in_summary") is not False
        or not isinstance(original.get("per_target_average_precision"), dict)
    ):
        raise ValueError("Original M1 comparison differs from the frozen calibration split")
    original_macros = [float(entry["macro_average_precision"]) for entry in original_seeds]
    original_mean = float(np.mean(original_macros))
    if original["macro_average_precision"]["mean"] != original_mean:
        raise ValueError("Original M1 calibration mean differs from its ten seeds")
    root = Path(calibration_root) / variant
    manifest_sha = _sha((stage / "staging-manifest.json").read_bytes())
    normalizer_sha = _sha(Path(normalizer_path).read_bytes())
    device = states[SEEDS[0]]["device"]
    torch_version = states[SEEDS[0]]["torch_version"]
    node_count, relation_count = (10, 3) if variant == "no-objective-nodes" else (12, 5)
    by_label: dict[str, list[float]] = {label: [] for label in LABELS}
    macros: list[float] = []
    seed_results: list[dict[str, Any]] = []
    reference_truth: np.ndarray | None = None
    reference_offsets: np.ndarray | None = None
    observations: int | None = None
    for seed in SEEDS:
        folder = root / f"seed-{seed}"
        report_bytes = (folder / "calibration-report.json").read_bytes()
        score_bytes = (folder / "calibration-scores.npz").read_bytes()
        report = json.loads(report_bytes)
        if (
            not isinstance(report, dict)
            or report.get("schema_version") != "league-ews-m1-graph-ablation-calibration-v1"
            or report.get("variant") != variant
            or report.get("seed") != seed
            or report.get("ablation_freeze_sha256") != ablation_sha
            or report.get("training_freeze_sha256") != training_sha
            or report.get("staging_manifest_sha256") != manifest_sha
            or report.get("normalizer_sha256") != normalizer_sha
            or report.get("all_seed_checkpoint_sha256") != hashes
            or report.get("checkpoint_sha256") != hashes[str(seed)]
            or report.get("scores_sha256") != _sha(score_bytes)
            or report.get("device") != device
            or report.get("torch_version") != torch_version
            or report.get("node_count") != node_count
            or report.get("relation_count") != relation_count
            or report.get("output_mode", "hazards")
            != ("independent-heads" if variant == "independent-horizon-heads" else "hazards")
            or report.get("calibration_matches") != 6000
            or report.get("targets") != list(LABELS)
            or report.get("test_matches_unread") != 6000
            or report.get("identifiers_in_report") is not False
        ):
            raise ValueError("Graph ablation calibration report differs from frozen inputs")
        with np.load(folder / "calibration-scores.npz", allow_pickle=False) as saved:
            if set(saved.files) != {"probabilities", "targets", "match_offsets"}:
                raise ValueError("Graph ablation score inventory differs")
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
            or (
                variant != "independent-horizon-heads"
                and np.any(np.diff(scores.reshape(len(scores), 3, 4), axis=-1) < -1e-7)
            )
            or report.get("calibration_observations") != len(scores)
        ):
            raise ValueError("Graph ablation scores differ from frozen calibration partition")
        if reference_truth is None:
            reference_truth = truth.copy()
            reference_offsets = offsets.copy()
            observations = len(scores)
        elif (
            reference_offsets is None
            or not np.array_equal(truth, reference_truth)
            or not np.array_equal(offsets, reference_offsets)
        ):
            raise ValueError("Graph ablation seeds disagree on truth or match order")
        metrics = {
            label: probabilistic_metrics(truth[:, col], scores[:, col])
            for col, label in enumerate(LABELS)
        }
        if report.get("metrics") != metrics:
            raise ValueError("Graph ablation metrics differ from saved probabilities")
        macro = float(
            np.mean([float(metrics[label]["average_precision"] or 0.0) for label in LABELS])
        )
        if report.get("macro_average_precision") != macro:
            raise ValueError("Graph ablation macro AP differs from target metrics")
        for label in LABELS:
            by_label[label].append(float(metrics[label]["average_precision"] or 0.0))
        macros.append(macro)
        seed_results.append(
            {
                "seed": seed,
                "macro_average_precision": macro,
                "report_sha256": _sha(report_bytes),
                "scores_sha256": _sha(score_bytes),
                "checkpoint_sha256": hashes[str(seed)],
            }
        )
    summary: dict[str, Any] = {
        "schema_version": "league-ews-m1-graph-ablation-ten-seed-summary-v1",
        "variant": variant,
        "ablation_freeze_sha256": ablation_sha,
        "training_freeze_sha256": training_sha,
        "original_m1_summary_sha256": _sha(original_bytes),
        "split_sha256": manifest["split_sha256"],
        "node_count": node_count,
        "relation_count": relation_count,
        **({"output_mode": "independent-heads"} if variant == "independent-horizon-heads" else {}),
        "seed_count": len(SEEDS),
        "calibration_matches": 6000,
        "calibration_observations": observations,
        "seed_results": seed_results,
        "macro_average_precision": _range(macros),
        "per_target_average_precision": {label: _range(by_label[label]) for label in LABELS},
        "original_m1_macro_average_precision": original_mean,
        "mean_delta_vs_m1": float(np.mean(macros)) - original_mean,
        "selected_seed": None,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    output = root / "ten-seed-summary.json"
    content = (json.dumps(summary, sort_keys=True, indent=2) + "\n").encode()
    if output.exists():
        if output.read_bytes() != content:
            raise ValueError("Existing graph ablation summary differs from frozen inputs")
    else:
        partial = output.with_suffix(".json.partial")
        partial.write_bytes(content)
        partial.replace(output)
    return summary
