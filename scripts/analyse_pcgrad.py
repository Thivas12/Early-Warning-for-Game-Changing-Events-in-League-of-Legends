"""Verify completed PCGrad fits, replay warnings and compare whole paired matches."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.notebook_experiment import SEEDS
from scripts.analyse_neural_screen import (
    BOOTSTRAP_SEED,
    DRAWS,
    METRICS,
    analyse,
    calibration_routes,
    load_completed,
)
from scripts.analyse_task_sharing import load_independent, replay_fit, validate_predictions
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, load_partition


def load_pcgrad(study, control, independent, cal, rows):
    summary = json.loads((study / "summary.json").read_bytes())
    freeze = json.loads((study / "freeze.json").read_bytes())
    binding = sha(study / "freeze.json")
    require(
        summary["schema_version"] == "league-pcgrad-results-v1"
        and summary["status"] == "complete-exploratory-pcgrad"
        and summary["test_payloads_opened"] == 0
        and summary["freeze_sha256"] == binding,
        "PCGrad study incomplete or mismatched",
    )
    plan = freeze["plan"]
    require(
        freeze["archive_sha256"] == EXPECTED_ARCHIVE
        and plan["control_summary_sha256"] == sha(control / "summary.json")
        and plan["control_freeze_sha256"] == sha(control / "freeze.json")
        and plan["independent_summary_sha256"] == sha(independent / "summary.json")
        and plan["events"] == list(EVENTS)
        and plan["seeds"] == list(SEEDS),
        "Control or data binding changed",
    )
    require(set(summary["models"]) == {f"pcgrad/{s}" for s in SEEDS}, "Three fits required")
    repo = Path(__file__).resolve().parents[1]
    for name, digest in freeze["source_sha256"].items():
        require(sha(repo / name) == digest, f"Frozen source changed: {name}")
    require(sha(repo / plan["diagnostic_file"]) == plan["diagnostic_sha256"], "Diagnostic changed")
    # Verify every checkpoint before opening any new prediction.
    artifacts = {}
    for seed in SEEDS:
        folder = study / "pcgrad" / f"seed-{seed}"
        report = json.loads((folder / "report.json").read_bytes())
        progress = json.loads((folder / "progress.json").read_bytes())
        require(
            progress["completed_units"] == 576
            and progress["family"] == report["family"] == "pcgrad"
            and progress["seed"] == report["seed"] == seed
            and progress["freeze_sha256"] == report["freeze_sha256"] == binding
            and report == summary["models"][f"pcgrad/{seed}"]
            and report["test_payloads_opened"] == 0,
            "Fit identity, completion or summary differs",
        )
        require(
            report["checkpoint_sha256"] == sha(folder / "checkpoint.pt")
            and report["scores_sha256"] == sha(folder / "calibration-scores.npz"),
            "PCGrad checkpoint or scores changed",
        )
        artifacts[str(seed)] = {k: report[k] for k in ("checkpoint_sha256", "scores_sha256")}
        artifacts[str(seed)]["report_sha256"] = sha(folder / "report.json")
    counts, audit = {30: [], 60: []}, {}
    for seed in SEEDS:
        folder = study / "pcgrad" / f"seed-{seed}"
        report = summary["models"][f"pcgrad/{seed}"]
        with np.load(folder / "calibration-scores.npz", allow_pickle=False) as saved:
            # Decode compressed arrays once per fit, before event/match loops.
            probabilities, targets, offsets = (
                saved["probabilities"],
                saved["targets"],
                saved["match_offsets"],
            )
            require(probabilities.shape == targets.shape == cal["targets"].shape, "Bad score shape")
            per_seed, audit[str(seed)] = {30: [], 60: []}, {}
            for e, event in enumerate(EVENTS):
                selected = {
                    "probabilities": probabilities[:, 4 * e : 4 * e + 4],
                    "targets": targets[:, 4 * e : 4 * e + 4],
                    "match_offsets": offsets,
                    **{f"counts_{event}_{h}": saved[f"counts_{event}_{h}"] for h in (30, 60)},
                }
                validate_predictions(selected, cal, event)
                replayed, audit[str(seed)][event] = replay_fit(selected, report, cal, rows, event)
                for h in (30, 60):
                    per_seed[h].append(replayed[h])
            for h in (30, 60):
                counts[h].append(np.stack(per_seed[h]))
    return {h: np.stack(c) for h, c in counts.items()}, artifacts, audit


def positive_every_seed_and_mean_interval(event):
    return all(event["by_seed"][str(s)]["timely_recall"]["estimate"] > 0 for s in SEEDS) and (
        event["mean_over_fixed_seeds"]["timely_recall"]["conditional_95_interval"][0] > 0
    )


def diagnostic_rules(analysis):
    section = analysis["overall"]["30"]["contrasts"]
    joint = section["pcgrad_minus_leagueews"]
    result = {
        "baron_recovery": positive_every_seed_and_mean_interval(joint["baron"]),
        "no_mean_task_harm": all(
            joint[e]["mean_over_fixed_seeds"]["timely_recall"]["estimate"] >= 0 for e in EVENTS
        ),
        "macro_gain": positive_every_seed_and_mean_interval(joint["macro"]),
        "strong_control_gain": all(
            section[f"pcgrad_minus_{f}"]["macro"]["mean_over_fixed_seeds"]["timely_recall"][
                "conditional_95_interval"
            ][0]
            > 0
            for f in ("independent", "tcn")
        ),
        "all_pcgrad_primary_regional_budgets": all(
            analysis[r]["30"]["families"]["pcgrad"][e]["by_seed"][str(s)][
                "false_plus_late_per_match"
            ]["estimate"]
            <= 1
            for r in ("europe", "americas")
            for e in EVENTS
            for s in SEEDS
        ),
    }
    result["practical_screen"] = all(result.values())
    return result


def run(args):
    routes = calibration_routes(args.archive)
    cal, rows = load_partition(args.archive, "calibration")
    counts, _, controls = load_completed(args.control, reference=cal)
    independent, _, independent_artifacts, independent_audit = load_independent(
        args.independent, args.control, cal, rows
    )
    counts["independent"] = independent
    counts["pcgrad"], artifacts, audit = load_pcgrad(
        args.study, args.control, args.independent, cal, rows
    )
    for family in counts:
        for h in (30, 60):
            for column in (0, 5):
                require(
                    np.array_equal(
                        counts[family][h][..., column], counts["leagueews"][h][..., column]
                    ),
                    "Paired event denominators or opportunities differ",
                )
    pairs = [("pcgrad", f) for f in ("leagueews", "independent", "tcn", "gru", "snapshot")]
    pairs += [("leagueews", f) for f in ("gru", "tcn", "snapshot", "independent")]
    analysis = analyse(counts, routes, pairs)
    original = json.loads((args.control / "summary.json").read_bytes())
    registered = analysis["overall"]["30"]["contrasts"]["leagueews_minus_gru"]["macro"]
    require(
        np.allclose(
            [registered["by_seed"][str(s)]["timely_recall"]["estimate"] for s in SEEDS],
            original["macro_30s_timely_recall_differences_by_seed"],
            rtol=0,
            atol=1e-12,
        ),
        "Registered primary changed",
    )
    result = {
        "schema_version": "league-pcgrad-paired-analysis-v1",
        "study_freeze_sha256": sha(args.study / "freeze.json"),
        "study_summary_sha256": sha(args.study / "summary.json"),
        "control_summary_sha256": sha(args.control / "summary.json"),
        "independent_summary_sha256": sha(args.independent / "summary.json"),
        "analysis_source_sha256": {
            str(p): sha(p)
            for p in (
                Path(__file__),
                Path("scripts/analyse_neural_screen.py"),
                Path("scripts/analyse_task_sharing.py"),
                Path("scripts/audit_neural_results.py"),
            )
        },
        "archive_sha256": EXPECTED_ARCHIVE,
        "matched_evaluation_matches": len(routes),
        "bootstrap": {
            "draws": DRAWS,
            "seed": BOOTSTRAP_SEED,
            "unit": "whole-match",
            "strata": "region",
            "paired_across": "all models, events and fixed fitted seeds",
            "scope": (
                "Conditional on fitted models and early-selected policies; "
                "unadjusted exploratory intervals. Fixed-seed mean is not an ensemble "
                "or extra independent matches."
            ),
        },
        "registered_original_screen_passed": original["consistent_positive_exploratory_screen"],
        "diagnostic_rules": diagnostic_rules(analysis),
        "analysis": analysis,
        "artifacts": {
            "pcgrad": artifacts,
            "original": controls,
            "independent": independent_artifacts,
        },
        "pcgrad_reference_replay": audit,
        "independent_reference_replay": independent_audit,
        "test_payloads_opened": 0,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "analysis.json", result)
    fields = ["region", "horizon", "model", "event", "seed", *METRICS]
    with (args.output / "by-seed.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for region, horizons in analysis.items():
            for horizon, section in horizons.items():
                for model, events in section["families"].items():
                    for event, values in events.items():
                        for seed, metrics in values["by_seed"].items():
                            writer.writerow(
                                {
                                    "region": region,
                                    "horizon": horizon,
                                    "model": model,
                                    "event": event,
                                    "seed": seed,
                                    **{m: metrics[m]["estimate"] for m in METRICS},
                                }
                            )
    return {"diagnostic_rules": result["diagnostic_rules"], "output": str(args.output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("study", "control", "independent", "archive", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    print(json.dumps(run(parser.parse_args()), indent=2))
