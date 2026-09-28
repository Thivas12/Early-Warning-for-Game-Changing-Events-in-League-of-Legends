"""Small, identifier-free audit of frozen M1 calibration reports.

Seed spreads describe training variability on one patch. They are not
confidence intervals across matches or evidence of future-patch transfer.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.m1_ablation_training import SUPPORTED_VARIANTS
from league_ews.m1_training_plan import SEEDS


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_summary(path: Path, schema: str) -> dict[str, Any]:
    summary = json.loads(path.read_bytes())
    if (
        not isinstance(summary, dict)
        or summary.get("schema_version") != schema
        or summary.get("seed_count") != len(SEEDS)
        or summary.get("calibration_matches") != 6000
        or summary.get("test_matches_unread") != 6000
        or summary.get("selected_seed") is not None
        or summary.get("identifiers_in_summary") is not False
        or [row.get("seed") for row in summary.get("seed_results", [])] != SEEDS
    ):
        raise ValueError(f"Calibration summary is incomplete or unbound: {path}")
    return summary


def _audited_reports(
    root: Path, summary: dict[str, Any], *, variant: str | None
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for row in summary["seed_results"]:
        folder = root / f"seed-{row['seed']}"
        report_path = folder / "calibration-report.json"
        scores_path = folder / "calibration-scores.npz"
        if _sha(report_path) != row["report_sha256"] or _sha(scores_path) != row["scores_sha256"]:
            raise ValueError("Calibration report or score checksum differs from audited summary")
        report = json.loads(report_path.read_bytes())
        schema = (
            "league-ews-m1-calibration-v1"
            if variant is None
            else "league-ews-m1-graph-ablation-calibration-v1"
        )
        if (
            not isinstance(report, dict)
            or report.get("schema_version") != schema
            or report.get("seed") != row["seed"]
            or report.get("variant") != variant
            or report.get("scores_sha256") != row["scores_sha256"]
            or report.get("checkpoint_sha256") != row["checkpoint_sha256"]
            or report.get("targets") != list(LABELS)
            or report.get("calibration_matches") != 6000
            or report.get("calibration_observations") != summary["calibration_observations"]
            or report.get("test_matches_unread") != 6000
            or report.get("identifiers_in_report") is not False
            or set(report.get("metrics", {})) != set(LABELS)
        ):
            raise ValueError("Calibration seed report differs from its audited summary")
        reports.append(report)
    for label in LABELS:
        values = [float(report["metrics"][label]["average_precision"]) for report in reports]
        if not np.isclose(
            float(summary["per_target_average_precision"][label]["mean"]),
            np.mean(values),
            rtol=0,
            atol=1e-12,
        ):
            raise ValueError("Per-target AP differs from the audited summary")
    return reports


def audit_m1_calibration(
    original_root: str | Path, ablation_root: str | Path, output: str | Path
) -> dict[str, Any]:
    """Compare available registered variants with paired seeds on calibration.

    Missing registered variants are explicit; no best model/seed is selected.
    Existing outputs are never overwritten with different results.
    """

    original = Path(original_root)
    variants = Path(ablation_root)
    original_path = original / "ten-seed-summary.json"
    baseline = _read_summary(original_path, "league-ews-m1-ten-seed-calibration-v1")
    baseline_reports = _audited_reports(original, baseline, variant=None)
    comparisons: dict[str, Any] = {}
    missing: list[str] = []
    for variant in SUPPORTED_VARIANTS:
        variant_path = variants / variant / "ten-seed-summary.json"
        if not variant_path.exists():
            missing.append(variant)
            continue
        summary = _read_summary(variant_path, "league-ews-m1-graph-ablation-ten-seed-summary-v1")
        if (
            summary.get("variant") != variant
            or summary.get("original_m1_summary_sha256") != _sha(original_path)
            or summary.get("training_freeze_sha256") != baseline["freeze_sha256"]
            or summary.get("split_sha256") != baseline["split_sha256"]
            or summary.get("calibration_observations") != baseline["calibration_observations"]
        ):
            raise ValueError("Ablation is not bound to the original calibration experiment")
        reports = _audited_reports(variants / variant, summary, variant=variant)
        by_target: dict[str, Any] = {}
        for label in LABELS:
            ref = [r["metrics"][label] for r in baseline_reports]
            changed = [r["metrics"][label] for r in reports]
            prevalence = float(ref[0]["prevalence"])
            if not 0 < prevalence < 1 or any(
                abs(float(r["prevalence"]) - prevalence) > 1e-12 for r in ref + changed
            ):
                raise ValueError("Target prevalence differs across paired calibration runs")
            ap_original = np.asarray([float(r["average_precision"]) for r in ref])
            ap_variant = np.asarray([float(r["average_precision"]) for r in changed])
            brier_original = np.asarray([float(r["brier"]) for r in ref])
            brier_variant = np.asarray([float(r["brier"]) for r in changed])
            if not all(
                np.isfinite(value).all()
                for value in (ap_original, ap_variant, brier_original, brier_variant)
            ):
                raise ValueError("Calibration metric must be finite")
            delta = ap_variant - ap_original
            by_target[label] = {
                "prevalence": prevalence,
                "m1_ap_mean": float(np.mean(ap_original)),
                "variant_ap_mean": float(np.mean(ap_variant)),
                "paired_ap_delta_mean": float(np.mean(delta)),
                "positive_delta_seeds": int(np.count_nonzero(delta > 0)),
                "m1_ap_lift_over_prevalence": float(np.mean(ap_original) / prevalence),
                "variant_ap_lift_over_prevalence": float(np.mean(ap_variant) / prevalence),
                "m1_brier_mean": float(np.mean(brier_original)),
                "variant_brier_mean": float(np.mean(brier_variant)),
                "m1_brier_skill_vs_constant_prevalence": float(
                    1 - np.mean(brier_original) / (prevalence * (1 - prevalence))
                ),
                "variant_brier_skill_vs_constant_prevalence": float(
                    1 - np.mean(brier_variant) / (prevalence * (1 - prevalence))
                ),
            }
        paired_macros = [
            float(new["macro_average_precision"] - old["macro_average_precision"])
            for old, new in zip(baseline_reports, reports, strict=True)
        ]
        comparisons[variant] = {
            "summary_sha256": _sha(variant_path),
            "paired_macro_ap_delta_mean": float(np.mean(paired_macros)),
            "positive_delta_seeds": sum(value > 0 for value in paired_macros),
            "per_target": by_target,
        }
    result: dict[str, Any] = {
        "schema_version": "league-ews-m1-calibration-diagnostic-v1",
        "original_summary_sha256": _sha(original_path),
        "split_sha256": baseline["split_sha256"],
        "calibration_matches": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
        "registered_variants": list(SUPPORTED_VARIANTS),
        "missing_variants": missing,
        "comparisons": comparisons,
        "interpretation": (
            "Descriptive calibration only; seeds are not independent matches or test sets"
        ),
    }
    destination = Path(output)
    content = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    if destination.exists():
        if destination.read_bytes() != content:
            raise ValueError("Existing calibration diagnostic differs from audited inputs")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".partial")
        temporary.write_bytes(content)
        temporary.replace(destination)
    return result
