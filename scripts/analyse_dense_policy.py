"""Paired analysis of the frozen threshold-resolution control."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.notebook_experiment import SEEDS
from scripts.analyse_neural_screen import METRICS, calibration_routes, metrics, resample_weights
from scripts.analyse_timely_neural import load as load_reference
from scripts.analyse_timely_neural import summarise
from scripts.evaluate_dense_policy import FAMILIES, NEW_POLICIES, POLICIES, REGIONS, freeze_policies
from scripts.export_league_development import require
from scripts.warning_efficiency import BUDGETS


def load(args):
    old, _, provenance, _ = load_reference(args.reference, args.control_plan)
    frozen = json.loads((args.study / "freeze.json").read_bytes())
    summary = json.loads((args.study / "summary.json").read_bytes())
    plan = json.loads(args.plan.read_bytes())
    binding = sha(args.study / "freeze.json")
    require(
        frozen["plan"] == plan
        and frozen["plan_sha256"] == sha(args.plan)
        and plan["reference_summary_sha256"] == sha(args.reference / "summary.json")
        and summary["freeze_sha256"] == binding
        and summary["status"] == "complete-exploratory-dense-policy"
        and summary["test_payloads_opened"] == 0
        and summary["new_fits"] == 0,
        "Completed study binding differs",
    )
    repo = Path(__file__).resolve().parents[1]
    require(all(sha(repo / p) == v for p, v in frozen["source_sha256"].items()), "Source changed")
    counts = {p: {f: old[p][f] for f in FAMILIES} for p in POLICIES if p not in NEW_POLICIES}
    counts.update(
        {
            p: {f: {h: np.empty((4, 3, 3, 3000, 6)) for h in (30, 60)} for f in FAMILIES}
            for p in NEW_POLICIES
        }
    )
    heads = [
        {"key": f"{f}-{s}-{e}-{h}"}
        for f in FAMILIES
        for s in SEEDS
        for e in EVENTS
        for h in (30, 60)
    ]
    require(set(summary["heads"]) == {h["key"] for h in heads}, "Head inventory differs")
    gate = freeze_policies(args.study, heads, binding)
    require(gate == summary["policy_freeze_sha256"], "Early freeze differs")
    selected = {}
    for family in FAMILIES:
        for s, seed in enumerate(SEEDS):
            for e, event in enumerate(EVENTS):
                for h in (30, 60):
                    key = f"{family}-{seed}-{event}-{h}"
                    path = args.study / "later" / f"{key}.npz"
                    report = json.loads(path.with_suffix(".json").read_bytes())
                    require(
                        report == summary["heads"][key]
                        and report["head"] == key
                        and report["freeze_sha256"] == binding
                        and report["policy_freeze_sha256"] == gate
                        and report["counts_sha256"] == sha(path),
                        "Count binding differs",
                    )
                    with np.load(path, allow_pickle=False) as saved:
                        require(set(saved.files) == set(NEW_POLICIES), "Policy inventory differs")
                        for p in NEW_POLICIES:
                            c = saved[p]
                            require(
                                c.shape == (4, 3000, 6)
                                and np.isfinite(c).all()
                                and np.array_equal(c, np.rint(c))
                                and np.all(c >= 0)
                                and np.all(c[..., 2] <= c[..., 1])
                                and np.all(c[..., 1] <= c[..., 0])
                                and np.all(c[..., 2] <= c[..., 5])
                                and np.array_equal(c[..., 3], c[..., 1] + c[..., 4]),
                                "Invalid counts",
                            )
                            for col in (0, 5):
                                require(
                                    np.array_equal(
                                        c[..., col],
                                        old["deterministic"][family][h][:, s, e, :, col],
                                    ),
                                    "Denominator mismatch",
                                )
                            counts[p][family][h][:, s, e] = c
                    value = json.loads((args.study / "early" / f"{key}.json").read_bytes())
                    selected[key] = {
                        k: v for k, v in value.items() if k != "early_threshold_counts_by_region"
                    }
    return (
        counts,
        plan,
        {
            "reference": provenance,
            "summary": summary,
            "summary_sha256": sha(args.study / "summary.json"),
        },
        selected,
    )


def rules(results, violations):
    g = results["overall"]["30"]["dense_deterministic"]["1.0"]["contrasts"][
        "timely_leagueews-minus-leagueews"
    ]
    r = g["macro"]["timely_recall"]
    return {
        "primary_target_gain": r["ci95"][0] > 0 and all(v > 0 for v in r["seeds"]),
        "no_mean_event_harm": all(g[e]["timely_recall"]["mean"] >= 0 for e in EVENTS),
        "no_extra_burden": g["macro"]["false_plus_late_per_match"]["ci95"][1] <= 0,
        "regional_hard_budget": not any(
            v["policy"] == "dense_deterministic"
            and v["family"] in ("timely_leagueews", "timely_tcn")
            and v["horizon"] == 30
            and v["above_hard_one"]
            for v in violations
        ),
    }


def analyse(counts, routes, contrasts, draws=2000):
    results, violations, policy_effects = {}, [], {}
    for region in ("overall", *REGIONS):
        idx = np.arange(len(routes)) if region == "overall" else np.flatnonzero(routes == region)
        weights = resample_weights(routes[idx], draws)
        results[region], policy_effects[region] = {}, {}
        for h in (30, 60):
            results[region][str(h)] = {}
            all_points, all_sampled = {}, {}
            for policy in POLICIES:
                points, sampled = {}, {}
                for family in FAMILIES:
                    c = counts[policy][family][h]
                    points[family] = np.stack(
                        [metrics(x[:, :, idx], np.ones((1, len(idx))))[0] for x in c]
                    )
                    sampled[family] = np.stack([metrics(x[:, :, idx], weights) for x in c])
                    if region != "overall":
                        for bi, budget in enumerate(BUDGETS):
                            for s, seed in enumerate(SEEDS):
                                for e, event in enumerate(EVENTS):
                                    cost = float(points[family][bi, s, e, 1])
                                    if cost > budget + 1e-12:
                                        violations.append(
                                            {
                                                "policy": policy,
                                                "horizon": h,
                                                "budget": budget,
                                                "family": family,
                                                "region": region,
                                                "seed": seed,
                                                "event": event,
                                                "burden": cost,
                                                "above_nominal": cost - budget,
                                                "above_hard_one": cost > 1 + 1e-12,
                                            }
                                        )
                all_points[policy], all_sampled[policy] = points, sampled
                group = {}
                for bi, budget in enumerate((*BUDGETS, "mean")):
                    p = {
                        f: points[f].mean(0) if budget == "mean" else points[f][bi]
                        for f in FAMILIES
                    }
                    b = {
                        f: sampled[f].mean(0) if budget == "mean" else sampled[f][bi]
                        for f in FAMILIES
                    }
                    comparisons = {
                        f"{a}-minus-{z}": summarise(p[a] - p[z], b[a] - b[z]) for a, z in contrasts
                    }
                    comparisons["target_effect_difference_leagueews_minus_tcn"] = summarise(
                        (p["timely_leagueews"] - p["leagueews"]) - (p["timely_tcn"] - p["tcn"]),
                        (b["timely_leagueews"] - b["leagueews"]) - (b["timely_tcn"] - b["tcn"]),
                    )
                    group[str(budget)] = {
                        "models": {f: summarise(p[f], b[f]) for f in FAMILIES},
                        "contrasts": comparisons,
                    }
                results[region][str(h)][policy] = group
                print(f"Analysed {region}/{h}/{policy}", flush=True)
            effects = {}
            for bi, budget in enumerate((*BUDGETS, "mean")):
                effects[str(budget)] = {}
                for family in FAMILIES:
                    effects[str(budget)][family] = {}
                    for a, z in (
                        ("dense_deterministic", "deterministic"),
                        ("dense_regional_deterministic", "regional_deterministic"),
                        ("matched_early_mixture", "dense_regional_deterministic"),
                    ):
                        p = all_points[a][family] - all_points[z][family]
                        b = all_sampled[a][family] - all_sampled[z][family]
                        effects[str(budget)][family][f"{a}-minus-{z}"] = summarise(
                            p.mean(0) if budget == "mean" else p[bi],
                            b.mean(0) if budget == "mean" else b[bi],
                        )
            for bi, budget in enumerate((*BUDGETS, "mean")):
                for family in ("leagueews", "tcn"):
                    name = "target_interaction_" + family
                    effects[str(budget)][name] = {}
                    for a, z in (
                        ("dense_deterministic", "deterministic"),
                        ("dense_regional_deterministic", "regional_deterministic"),
                    ):
                        t = "timely_" + family
                        p = (all_points[a][t] - all_points[z][t]) - (
                            all_points[a][family] - all_points[z][family]
                        )
                        b = (all_sampled[a][t] - all_sampled[z][t]) - (
                            all_sampled[a][family] - all_sampled[z][family]
                        )
                        effects[str(budget)][name][f"{a}-minus-{z}"] = summarise(
                            p.mean(0) if budget == "mean" else p[bi],
                            b.mean(0) if budget == "mean" else b[bi],
                        )
            policy_effects[region][str(h)] = effects
    return results, violations, policy_effects


def write_aggregates(output, counts, routes, results):
    with (output / "aggregate-counts.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "policy",
                "budget",
                "family",
                "seed",
                "event",
                "horizon",
                "region",
                "matches",
                "events",
                "matched",
                "timely",
                "alerts",
                "false",
                "opportunities",
            ]
        )
        for policy in POLICIES:
            for family in FAMILIES:
                for h in (30, 60):
                    for bi, budget in enumerate(BUDGETS):
                        for s, seed in enumerate(SEEDS):
                            for e, event in enumerate(EVENTS):
                                for region in ("overall", *REGIONS):
                                    idx = (
                                        np.arange(len(routes))
                                        if region == "overall"
                                        else np.flatnonzero(routes == region)
                                    )
                                    sums = counts[policy][family][h][bi, s, e, idx].sum(0)
                                    writer.writerow(
                                        [
                                            policy,
                                            budget,
                                            family,
                                            seed,
                                            event,
                                            h,
                                            region,
                                            len(idx),
                                            *sums,
                                        ]
                                    )
    with (output / "by-seed.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["region", "horizon", "policy", "budget", "family", "seed", "event", *METRICS]
        )
        for region, horizons in results.items():
            for h, policies in horizons.items():
                for policy, budgets in policies.items():
                    for budget, groups in budgets.items():
                        for family, events in groups["models"].items():
                            for event, values in events.items():
                                for i, seed in enumerate(SEEDS):
                                    writer.writerow(
                                        [
                                            region,
                                            h,
                                            policy,
                                            budget,
                                            family,
                                            seed,
                                            event,
                                            *(values[m]["seeds"][i] for m in METRICS),
                                        ]
                                    )


def main(args):
    counts, plan, provenance, selected = load(args)
    routes = calibration_routes(args.archive)
    require(
        len(routes) == 3000 and all((routes == r).sum() == 1500 for r in REGIONS), "Routes differ"
    )
    require(
        plan["uncertainty"]["draws"] == 2000 and plan["uncertainty"]["seed"] == 20261001,
        "Bootstrap plan differs",
    )
    results, violations, effects = analyse(counts, routes, plan["contrasts"])
    output = {
        "schema_version": "league-dense-policy-analysis-v1",
        "status": "exploratory-development-only",
        "test_payloads_opened": 0,
        "plan_sha256": sha(args.plan),
        "analysis_source_sha256": sha(Path(__file__)),
        "provenance": provenance,
        "uncertainty": plan["uncertainty"],
        "results": results,
        "policy_effects": effects,
        "nominal_budget_violations": violations,
        "frozen_rules": rules(results, violations),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "analysis.json", output)
    write_json(args.output / "early-policies.json", selected)
    write_aggregates(args.output, counts, routes, results)
    print(json.dumps(output["frozen_rules"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("study", "reference", "control-plan", "archive", "plan", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    main(parser.parse_args())
