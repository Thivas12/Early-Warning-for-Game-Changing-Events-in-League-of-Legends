"""Compare the completed history ablation to the frozen full-history control."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.notebook_experiment import SEEDS
from scripts.analyse_neural_screen import analyse, calibration_routes, load_completed
from scripts.export_league_development import require
from scripts.league_compact_data import load_partition


def run(control: Path, followup: Path, archive: Path, output: Path) -> dict:
    frozen = json.loads((followup / "freeze.json").read_bytes())
    family = frozen["plan"]["family"]
    require(
        sha(control / "summary.json") == frozen["plan"]["control_summary_sha256"],
        "Control summary changed",
    )
    routes = calibration_routes(archive)
    reference, _ = load_partition(archive, "calibration")
    original, original_reports, original_artifacts = load_completed(
        control, (family,), reference=reference
    )
    repeated, repeated_reports, repeated_artifacts = load_completed(
        followup, (family,), reference=reference
    )
    for h in (30, 60):
        require(
            np.array_equal(original[family][h][..., 0], repeated[family][h][..., 0]),
            "Event denominators differ",
        )
    analysis = analyse(
        {"full_history": original[family], "current_only": repeated[family]},
        routes,
        [("full_history", "current_only")],
    )
    primary = analysis["overall"]["30"]["contrasts"]["full_history_minus_current_only"]
    differences = [primary["macro"]["by_seed"][str(s)]["timely_recall"]["estimate"] for s in SEEDS]
    budgets = [
        all(
            reports[family][str(seed)]["warnings"][f"{event}_30"]["regional_budget_met"]
            for reports in (original_reports, repeated_reports)
            for event in EVENTS
        )
        for seed in SEEDS
    ]
    interval = primary["macro"]["mean_over_fixed_seeds"]["timely_recall"]["conditional_95_interval"]
    event_differences = {
        e: primary[e]["mean_over_fixed_seeds"]["timely_recall"]["estimate"] for e in EVENTS
    }
    result = {
        "schema_version": "league-history-ablation-analysis-v1",
        "family": family,
        "plan": frozen["plan"],
        "followup_freeze_sha256": sha(followup / "freeze.json"),
        "followup_summary_sha256": sha(followup / "summary.json"),
        "analysis_source_sha256": sha(Path(__file__)),
        "paired_analysis_source_sha256": sha(Path(__file__).with_name("analyse_neural_screen.py")),
        "artifacts": {"full_history": original_artifacts, "current_only": repeated_artifacts},
        "primary": {
            "contrast": "full_history_minus_current_only",
            "endpoint": "macro 10-30 second timely recall",
            "differences_by_seed": differences,
            "mean_conditional_95_interval": interval,
            "both_models_regional_budgets_by_seed": budgets,
            "event_mean_differences": event_differences,
            "descriptive_consistent_history_support": all(v > 0 for v in differences)
            and interval[0] > 0
            and all(budgets)
            and all(v >= 0 for v in event_differences.values()),
        },
        "analysis": analysis,
        "followup_reports": repeated_reports,
        "test_payloads_opened": 0,
        "interpretation": (
            "Adaptive exploratory retraining intervention; conditional intervals; "
            "task sharing remains untested"
        ),
    }
    write_json(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("control", "followup", "archive", "output"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.control, args.followup, args.archive, args.output)
    print(json.dumps(result["primary"], indent=2))
