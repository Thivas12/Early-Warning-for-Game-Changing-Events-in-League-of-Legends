"""Audit the nine independent fits and compare paired whole development matches."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.notebook_experiment import SEEDS
from scripts.analyse_neural_screen import (
    BOOTSTRAP_SEED,
    DRAWS,
    METRICS,
    analyse,
    calibration_routes,
    load_completed,
)
from scripts.audit_neural_results import check_report, reference_counts
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, load_partition


def validate_predictions(saved, reference, event):
    columns = slice(EVENTS.index(event) * 4, EVENTS.index(event) * 4 + 4)
    scores, targets, offsets = (saved["probabilities"], saved["targets"], saved["match_offsets"])
    require(
        offsets.dtype.kind in "iu" and np.array_equal(offsets, reference["match_offsets"]),
        "Calibration offsets differ",
    )
    require(
        targets.dtype.kind in "biu" and np.array_equal(targets, reference["targets"][:, columns]),
        "Selected-event labels differ",
    )
    require(
        scores.shape == targets.shape
        and scores.shape[1] == 4
        and np.isfinite(scores).all()
        and ((scores >= 0) & (scores <= 1)).all(),
        "Invalid selected-event probabilities",
    )


def replay_fit(saved, report, cal, rows, event):
    # NpzFile does not cache __getitem__: decode once, not once per match.
    probabilities = saved["probabilities"]
    early, later = _chronological_halves(rows)
    require(len(early) == len(later) == 3000 and not set(early) & set(later), "Halves differ")
    routes = np.array([row["regional_route"] for row in rows])
    result, policies = {}, {}
    for horizon, column in ((30, 2), (60, 3)):
        name = f"{event}_{horizon}"
        policy = report["warnings"][name]
        counts = []
        for i in range(len(rows)):
            a, b = cal["match_offsets"][i : i + 2]
            left, right = cal[f"{event}_offsets"][i : i + 2]
            counts.append(
                reference_counts(
                    cal["times_ms"][a:b],
                    cal[f"{event}_ms"][left:right],
                    probabilities[a:b, column],
                    policy["threshold"],
                    horizon,
                )
            )
        counts = np.asarray(counts, dtype=np.int64)
        stored = saved[f"counts_{name}"]
        require(
            stored.shape == (3000, 6)
            and stored.dtype.kind in "iu"
            and np.array_equal(stored, counts[later]),
            "Independent replay counts differ",
        )
        check_report(counts[later], policy["later"])
        early_burdens, late_budgets = {}, []
        for route in ("europe", "americas"):
            early_idx = [i for i in early if routes[i] == route]
            late_idx = [i for i in later if routes[i] == route]
            require(len(early_idx) == len(late_idx) == 1500, "Regional match counts differ")
            burden = float((counts[early_idx, 3] - counts[early_idx, 2]).mean())
            require(burden <= 1, "Early selected threshold violates budget")
            early_burdens[route] = burden
            check_report(counts[late_idx], policy["by_route"][route])
            late_budgets.append(float((counts[late_idx, 3] - counts[late_idx, 2]).mean()) <= 1)
        require(all(late_budgets) == policy["regional_budget_met"], "Budget flag differs")
        result[horizon] = stored
        policies[name] = {
            "counts_and_reports_reproduced": True,
            "early_false_plus_late_per_match": early_burdens,
            "later_regional_budget_met": all(late_budgets),
        }
    return result, policies


def load_independent(study, control, cal, rows):
    summary = json.loads((study / "summary.json").read_bytes())
    freeze = json.loads((study / "freeze.json").read_bytes())
    binding = sha(study / "freeze.json")
    require(
        summary["schema_version"] == "league-task-sharing-results-v1"
        and summary["status"] == "complete-exploratory-task-sharing"
        and summary["test_payloads_opened"] == 0
        and summary["freeze_sha256"] == binding,
        "Study is not a complete development-only task-sharing study",
    )
    require(
        freeze["archive_sha256"] == EXPECTED_ARCHIVE
        and freeze["plan"]["control_summary_sha256"] == sha(control / "summary.json")
        and freeze["plan"]["control_freeze_sha256"] == sha(control / "freeze.json")
        and freeze["plan"]["events"] == list(EVENTS)
        and freeze["plan"]["seeds"] == list(SEEDS),
        "Study or control binding differs",
    )
    require(
        set(summary["models"]) == {f"{e}/{s}" for e in EVENTS for s in SEEDS},
        "Nine event fits required",
    )
    repo = Path(__file__).resolve().parents[1]
    for name, digest in freeze["source_sha256"].items():
        require(sha(repo / name) == digest, f"Frozen training source changed: {name}")
    # Audit all checkpoint/progress bindings before any new prediction is opened.
    artifacts = {}
    for event in EVENTS:
        for seed in SEEDS:
            key = f"{event}/{seed}"
            folder = study / event / f"seed-{seed}"
            report = json.loads((folder / "report.json").read_bytes())
            progress = json.loads((folder / "progress.json").read_bytes())
            require(progress["completed_units"] == 576, "Independent training incomplete")
            require(
                progress["event"] == report["event"] == event
                and progress["seed"] == report["seed"] == seed
                and progress["freeze_sha256"] == report["freeze_sha256"] == binding
                and report == summary["models"][key]
                and report["test_payloads_opened"] == 0,
                "Independent fit identity or summary differs",
            )
            require(
                report["checkpoint_sha256"] == sha(folder / "checkpoint.pt")
                and report["scores_sha256"] == sha(folder / "calibration-scores.npz"),
                "Independent artifacts changed",
            )
            artifacts[key] = {k: report[k] for k in ("checkpoint_sha256", "scores_sha256")}
            artifacts[key]["report_sha256"] = sha(folder / "report.json")
    by_horizon, audit = {30: [], 60: []}, {}
    for seed in SEEDS:
        per_seed = {30: [], 60: []}
        for event in EVENTS:
            key = f"{event}/{seed}"
            with np.load(
                study / event / f"seed-{seed}" / "calibration-scores.npz", allow_pickle=False
            ) as saved:
                validate_predictions(saved, cal, event)
                counts, replay = replay_fit(saved, summary["models"][key], cal, rows, event)
                for horizon in (30, 60):
                    per_seed[horizon].append(counts[horizon])
            audit[key] = replay
        for horizon in (30, 60):
            by_horizon[horizon].append(np.stack(per_seed[horizon]))
    return {h: np.stack(v) for h, v in by_horizon.items()}, summary["models"], artifacts, audit


def diagnostic_rules(analysis):
    contrast = analysis["overall"]["30"]["contrasts"]["leagueews_minus_independent"]
    macro = contrast["macro"]
    positive_seeds = all(macro["by_seed"][str(s)]["timely_recall"]["estimate"] > 0 for s in SEEDS)
    positive_interval = (
        macro["mean_over_fixed_seeds"]["timely_recall"]["conditional_95_interval"][0] > 0
    )
    no_negative_event = all(
        contrast[e]["mean_over_fixed_seeds"]["timely_recall"]["estimate"] >= 0 for e in EVENTS
    )
    all_budgets = all(
        analysis[r]["30"]["families"][f][e]["by_seed"][str(s)]["false_plus_late_per_match"][
            "estimate"
        ]
        <= 1
        for r in ("europe", "americas")
        for f in ("leagueews", "independent")
        for e in EVENTS
        for s in SEEDS
    )
    return {
        "positive_macro_every_seed": positive_seeds,
        "macro_conditional_interval_positive": positive_interval,
        "descriptive_positive_macro_sharing": positive_seeds and positive_interval,
        "no_negative_event_mean": no_negative_event,
        "uniform_task_benefit": positive_seeds and positive_interval and no_negative_event,
        "both_variants_all_primary_regional_budgets": all_budgets,
        "practical_promotion_gate": positive_seeds
        and positive_interval
        and no_negative_event
        and all_budgets,
        "descriptive_task_harm": {
            e: (
                all(contrast[e]["by_seed"][str(s)]["timely_recall"]["estimate"] < 0 for s in SEEDS)
                and contrast[e]["mean_over_fixed_seeds"]["timely_recall"][
                    "conditional_95_interval"
                ][1]
                < 0
            )
            for e in EVENTS
        },
        "scope": (
            "Exploratory fixed-recipe diagnosis; no multiplicity adjustment, "
            "causal gradient diagnosis, novelty or fresh-test claim."
        ),
    }


def run(study: Path, control: Path, archive: Path, output: Path):
    routes = calibration_routes(archive)
    cal, rows = load_partition(archive, "calibration")
    counts, _reports, controls = load_completed(control, reference=cal)
    independent, new_reports, artifacts, audit = load_independent(study, control, cal, rows)
    for horizon in (30, 60):
        require(
            np.array_equal(independent[horizon][..., 0], counts["leagueews"][horizon][..., 0]),
            "Paired event denominators differ",
        )
        require(
            np.array_equal(independent[horizon][..., 5], counts["leagueews"][horizon][..., 5]),
            "Paired warning opportunities differ",
        )
    counts["independent"] = independent
    analysis = analyse(
        counts, routes, [("leagueews", f) for f in ("independent", "gru", "tcn", "snapshot")]
    )
    original = json.loads((control / "summary.json").read_bytes())
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
        "schema_version": "league-task-sharing-paired-analysis-v1",
        "study_freeze_sha256": sha(study / "freeze.json"),
        "study_summary_sha256": sha(study / "summary.json"),
        "control_summary_sha256": sha(control / "summary.json"),
        "archive_sha256": EXPECTED_ARCHIVE,
        "analysis_source_sha256": {
            str(p): sha(p)
            for p in (
                Path(__file__),
                Path("scripts/analyse_neural_screen.py"),
                Path("scripts/audit_neural_results.py"),
            )
        },
        "matched_evaluation_matches": len(routes),
        "bootstrap": {
            "draws": DRAWS,
            "seed": BOOTSTRAP_SEED,
            "unit": "whole-match",
            "strata": "region",
            "paired_across": "all events, models and fixed fitted seeds",
            "interval_scope": (
                "Conditional on fitted models and early-selected thresholds; "
                "no refitting; unadjusted exploratory intervals."
            ),
            "seed_mean": (
                "Mean of three fixed fitted model performances; "
                "not an ensemble or three independent populations."
            ),
        },
        "registered_original_screen_passed": original["consistent_positive_exploratory_screen"],
        "diagnostic_rules": diagnostic_rules(analysis),
        "analysis": analysis,
        "independent_reports": new_reports,
        "artifacts": {"original": controls, "independent": artifacts},
        "independent_reference_replay": audit,
        "test_payloads_opened": 0,
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "analysis.json", result)
    fields = ["region", "horizon", "model", "event", "seed", *METRICS]
    with (output / "by-seed.csv").open("w", newline="") as f:
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
    return {"diagnostic_rules": result["diagnostic_rules"], "output": str(output / "analysis.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("study", "control", "archive", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.study, args.control, args.archive, args.output), indent=2))
