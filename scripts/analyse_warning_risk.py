"""Paired capped-warning policy effects and matched architecture comparisons."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.notebook_experiment import SEEDS
from scripts.analyse_matched_optimization import summarise
from scripts.analyse_neural_screen import calibration_routes, metrics, resample_weights
from scripts.evaluate_matched_optimization import freeze_policies
from scripts.evaluate_warning_risk import validate_plan
from scripts.export_league_development import require
from scripts.warning_efficiency import BUDGETS
from scripts.warning_risk import CAP, FAMILIES, POLICIES, REGIONS

CONTRASTS = (*((FAMILIES[0], other) for other in FAMILIES[1:]), (FAMILIES[1], FAMILIES[2]))
POLICY_CONTRASTS = (
    (POLICIES[1], POLICIES[0]),
    (POLICIES[2], POLICIES[1]),
    (POLICIES[3], POLICIES[2]),
    (POLICIES[3], POLICIES[0]),
)
PRIMARY = "timely_equal_sum-minus-timely_equal_tcn"


def load(study, plan_path):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(plan_path.read_bytes())
    validate_plan(plan)
    frozen = json.loads((study / "freeze.json").read_bytes())
    summary = json.loads((study / "summary.json").read_bytes())
    binding = sha(study / "freeze.json")
    require(
        summary["status"] == "complete-exploratory-warning-risk"
        and summary["freeze_sha256"] == binding
        and summary["test_payloads_opened"] == summary["new_neural_fits"] == 0
        and summary["total_completed_neural_fits"] == 69
        and frozen["plan"] == plan
        and frozen["plan_sha256"] == sha(plan_path)
        and all(sha(repo / name) == value for name, value in frozen["source_sha256"].items())
        and summary["analysis_release_sha256"] == sha(study / "analysis-release.json")
        and summary["early_gate_sha256"] == sha(study / "early-gate.json"),
        "Risk study binding differs",
    )
    heads = [
        {"key": f"{f}-{s}-{e}-{h}"}
        for f in FAMILIES
        for s in SEEDS
        for e in EVENTS
        for h in (30, 60)
    ]
    require(set(summary["heads"]) == {h["key"] for h in heads}, "Risk inventory differs")
    policy_binding = freeze_policies(study, heads, binding)
    require(policy_binding == summary["policy_freeze_sha256"], "Early policy binding differs")
    counts = {
        p: {f: {h: np.empty((4, 3, 3, 3000, 6)) for h in (30, 60)} for f in FAMILIES}
        for p in POLICIES
    }
    selections = {}
    for family in FAMILIES:
        for si, seed in enumerate(SEEDS):
            for ei, event in enumerate(EVENTS):
                for h in (30, 60):
                    key = f"{family}-{seed}-{event}-{h}"
                    path = study / "later" / f"{key}.npz"
                    report = json.loads(path.with_suffix(".json").read_bytes())
                    require(
                        report == summary["heads"][key]
                        and report["freeze_sha256"] == binding
                        and report["head"] == key
                        and report["policy_freeze_sha256"] == policy_binding
                        and report["counts_sha256"] == sha(path)
                        and report["full_reference_checks"] == 9000
                        and report["previous_counts_reproduced"],
                        "Later report differs",
                    )
                    with np.load(path, allow_pickle=False) as saved:
                        require(set(saved.files) == set(POLICIES), "Policy inventory differs")
                        for p in POLICIES:
                            c = saved[p]
                            require(
                                c.shape == (4, 3000, 6)
                                and np.isfinite(c).all()
                                and np.all(c >= 0)
                                and np.array_equal(c, np.rint(c))
                                and np.all(c[..., 2] <= c[..., 1])
                                and np.all(c[..., 1] <= c[..., 0])
                                and np.all(c[..., 2] <= c[..., 5])
                                and np.all(c[..., 1] + c[..., 4] == c[..., 3])
                                and (p == POLICIES[0] or np.all(c[..., 3] <= CAP)),
                                "Invalid capped match counts",
                            )
                            counts[p][family][h][:, si, ei] = c
                    selections[key] = json.loads((study / "early" / f"{key}.json").read_bytes())
    for p in POLICIES:
        for f in FAMILIES:
            for h in (30, 60):
                for col in (0, 5):
                    require(
                        np.array_equal(
                            counts[p][f][h][..., col],
                            np.broadcast_to(
                                counts[POLICIES[0]][FAMILIES[0]][h][0, 0, :, :, col],
                                (4, 3, 3, 3000),
                            ),
                        ),
                        "Denominator mismatch",
                    )
    return counts, summary, selections


def analyse(counts, routes, draws=2000):
    results, effects, violations = {}, {}, []
    for region in ("overall", *REGIONS):
        idx = np.arange(len(routes)) if region == "overall" else np.flatnonzero(routes == region)
        weights = resample_weights(routes[idx], draws)
        results[region], effects[region] = {}, {}
        for h in (30, 60):
            results[region][str(h)] = {}
            all_points, all_draws = {}, {}
            for policy in POLICIES:
                points, samples = {}, {}
                for family in FAMILIES:
                    c = counts[policy][family][h]
                    points[family] = np.stack(
                        [metrics(x[:, :, idx], np.ones((1, len(idx))))[0] for x in c]
                    )
                    samples[family] = np.stack([metrics(x[:, :, idx], weights) for x in c])
                    if region != "overall":
                        for bi, budget in enumerate(BUDGETS):
                            for si, seed in enumerate(SEEDS):
                                for ei, event in enumerate(EVENTS):
                                    burden = float(points[family][bi, si, ei, 1])
                                    if burden > budget + 1e-12:
                                        violations.append(
                                            {
                                                "family": family,
                                                "policy": policy,
                                                "horizon": h,
                                                "budget": budget,
                                                "region": region,
                                                "seed": seed,
                                                "event": event,
                                                "burden": burden,
                                                "above_nominal": burden - budget,
                                                "above_hard_one": burden > 1 + 1e-12,
                                            }
                                        )
                all_points[policy], all_draws[policy] = points, samples
                group = {}
                for bi, budget in enumerate((*BUDGETS, "mean")):
                    p = {
                        f: points[f].mean(0) if budget == "mean" else points[f][bi]
                        for f in FAMILIES
                    }
                    b = {
                        f: samples[f].mean(0) if budget == "mean" else samples[f][bi]
                        for f in FAMILIES
                    }
                    group[str(budget)] = {
                        "models": {f: summarise(p[f], b[f]) for f in FAMILIES},
                        "contrasts": {
                            f"{a}-minus-{z}": summarise(p[a] - p[z], b[a] - b[z])
                            for a, z in CONTRASTS
                        },
                    }
                results[region][str(h)][policy] = group
                print(f"Analysed {region}/{h}/{policy}", flush=True)
            local = {}
            for bi, budget in enumerate((*BUDGETS, "mean")):
                local[str(budget)] = {}
                for f in FAMILIES:
                    local[str(budget)][f] = {}
                    for a, z in POLICY_CONTRASTS:
                        p = all_points[a][f] - all_points[z][f]
                        b = all_draws[a][f] - all_draws[z][f]
                        local[str(budget)][f][f"{a}-minus-{z}"] = summarise(
                            p.mean(0) if budget == "mean" else p[bi],
                            b.mean(0) if budget == "mean" else b[bi],
                        )
            effects[region][str(h)] = local
    return results, effects, violations


def frozen_rules(results, violations):
    group = results["overall"]["30"][POLICIES[3]]["mean"]["contrasts"]
    comparison = group[PRIMARY]
    primary = comparison["macro"]["timely_recall"]
    gru = group["timely_equal_sum-minus-timely_equal_gru"]["macro"]["timely_recall"]
    regional = [
        results[r]["30"][POLICIES[3]]["mean"]["contrasts"][PRIMARY]["macro"]["timely_recall"]
        for r in REGIONS
    ]
    return {
        "architecture_support": primary["ci95"][0] > 0 and all(x > 0 for x in primary["seeds"]),
        "event_point_nonharm": all(comparison[e]["timely_recall"]["mean"] >= 0 for e in EVENTS),
        "no_extra_burden": comparison["macro"]["false_plus_late_per_match"]["ci95"][1] <= 0,
        "regional_architecture_consistency": all(
            x["ci95"][0] > 0 and all(y > 0 for y in x["seeds"]) for x in regional
        ),
        "gru_support": gru["ci95"][0] > 0 and all(x > 0 for x in gru["seeds"]),
        "equal_leagueews_hard_one_budget_one": {
            str(h): not any(
                v["family"] == FAMILIES[0]
                and v["policy"] == POLICIES[3]
                and v["horizon"] == h
                and v["budget"] == 1.0
                and v["above_hard_one"]
                for v in violations
            )
            for h in (30, 60)
        },
        "practical_promotion": (
            "not established by adaptively reused calibration; previous failures remain "
            "and patch 16.17 stays sealed"
        ),
    }


def prior_reproduction(results, previous):
    """Require exact original fine-grid model and shared-contrast summaries."""
    models, contrasts = 0, 0
    for region in ("overall", *REGIONS):
        for h in ("30", "60"):
            for budget in (*map(str, BUDGETS), "mean"):
                old = previous["results"][region][h]["dense_deterministic"][budget]
                new = results[region][h][POLICIES[0]][budget]
                for f in FAMILIES:
                    require(new["models"][f] == old["models"][f], "Prior model estimate differs")
                    models += 1
                for name, estimate in new["contrasts"].items():
                    require(estimate == old["contrasts"][name], "Prior contrast estimate differs")
                    contrasts += 1
    return {"model_event_metric_groups": models, "contrast_event_metric_groups": contrasts}


def run(args):
    counts, summary, selections = load(args.study, args.plan)
    routes = calibration_routes(args.archive)
    results, effects, violations = analyse(counts, routes)
    previous_path = (
        Path(__file__).resolve().parents[1]
        / "reports/matched-optimization-2026-10-06/analysis.json"
    )
    plan = json.loads(args.plan.read_bytes())
    require(
        sha(previous_path) == plan["previous_analysis_sha256"],
        "Published reference analysis differs",
    )
    previous = json.loads(previous_path.read_bytes())
    reproduced = prior_reproduction(results, previous)
    analysis = {
        "schema_version": "league-warning-risk-analysis-v1",
        "results": results,
        "policy_effects": effects,
        "nominal_budget_violations": violations,
        "frozen_rules": frozen_rules(results, violations),
        "prior_exact_reproduction": reproduced,
        "study_summary_sha256": sha(args.study / "summary.json"),
        "test_payloads_opened": 0,
        "new_neural_fits": 0,
        "full_reference_checks": sum(v["full_reference_checks"] for v in summary["heads"].values()),
        "component_reference_checks": sum(
            v["component_reference_checks"] for v in summary["heads"].values()
        ),
        "cap_activity": {k: v["cap_truncated_matches"] for k, v in summary["heads"].items()},
    }
    write_json(args.output / "analysis.json", analysis)
    write_json(args.output / "early-policies.json", selections)
    with (args.output / "aggregate-counts.csv").open("w") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "region",
                "horizon",
                "policy",
                "budget",
                "family",
                "seed",
                "event",
                "matches",
                "events",
                "hits",
                "timely",
                "alerts",
                "false",
                "opportunities",
            ]
        )
        for region in ("overall", *REGIONS):
            idx = (
                np.arange(len(routes)) if region == "overall" else np.flatnonzero(routes == region)
            )
            for p in POLICIES:
                for f in FAMILIES:
                    for h in (30, 60):
                        for bi, budget in enumerate(BUDGETS):
                            for si, seed in enumerate(SEEDS):
                                for ei, event in enumerate(EVENTS):
                                    c = counts[p][f][h][bi, si, ei, idx].sum(0)
                                    writer.writerow(
                                        [
                                            region,
                                            h,
                                            p,
                                            budget,
                                            f,
                                            seed,
                                            event,
                                            len(idx),
                                            *c.astype(int),
                                        ]
                                    )
    with (args.output / "by-seed.csv").open("w") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "region",
                "horizon",
                "policy",
                "budget",
                "kind",
                "comparison",
                "event",
                "metric",
                "seed",
                "value",
            ]
        )
        for region, horizons in results.items():
            for h, policies in horizons.items():
                for p, budgets in policies.items():
                    for budget, groups in budgets.items():
                        for kind, names in groups.items():
                            for name, events in names.items():
                                for e, values in events.items():
                                    for metric, stats in values.items():
                                        for seed, value in zip(SEEDS, stats["seeds"], strict=True):
                                            writer.writerow(
                                                [
                                                    region,
                                                    h,
                                                    p,
                                                    budget,
                                                    kind,
                                                    name,
                                                    e,
                                                    metric,
                                                    seed,
                                                    value,
                                                ]
                                            )
    print(json.dumps(analysis["frozen_rules"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("study", "archive", "plan", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    run(args)
