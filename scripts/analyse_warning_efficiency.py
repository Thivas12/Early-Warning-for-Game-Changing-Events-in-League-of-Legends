"""Paired, whole-match analysis of the frozen warning-efficiency diagnostic."""

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
from scripts.export_league_development import require
from scripts.run_warning_efficiency import FAMILIES, POLICIES, REGIONS, freeze_policies
from scripts.warning_efficiency import BUDGETS


def load(study, plan_path):
    frozen = json.loads((study / "freeze.json").read_bytes())
    summary = json.loads((study / "summary.json").read_bytes())
    binding = sha(study / "freeze.json")
    require(summary["status"] == "complete-exploratory-warning-efficiency", "Incomplete study")
    require(
        summary["freeze_sha256"] == binding
        and summary["test_payloads_opened"] == 0
        and summary["new_neural_fits"] == 0,
        "Summary boundary differs",
    )
    require(frozen["plan_sha256"] == sha(plan_path), "Plan differs")
    repo = Path(__file__).resolve().parents[1]
    require(
        all(sha(repo / p) == v for p, v in frozen["source_sha256"].items()), "Frozen source differs"
    )
    plan = json.loads(plan_path.read_bytes())
    require(
        plan == frozen["plan"]
        and plan["uncertainty"]["draws"] == 2000
        and plan["uncertainty"]["seed"] == 20261001,
        "Analysis plan differs",
    )
    heads = [
        {"key": f"{family}-{seed}-{event}-{h}"}
        for family in FAMILIES
        for seed in SEEDS
        for event in EVENTS
        for h in (30, 60)
    ]
    require(set(summary["heads"]) == {head["key"] for head in heads}, "Head inventory differs")
    policy_binding = freeze_policies(study, heads, binding)
    require(policy_binding == summary["policy_freeze_sha256"], "Policy freeze differs")
    counts = {
        p: {f: {h: np.empty((4, 3, 3, 3000, 6)) for h in (30, 60)} for f in FAMILIES}
        for p in POLICIES
    }
    artifacts, selected_policies = {}, {}
    for family in FAMILIES:
        for s, seed in enumerate(SEEDS):
            for e, event in enumerate(EVENTS):
                for h in (30, 60):
                    key = f"{family}-{seed}-{event}-{h}"
                    path = study / "later" / f"{key}.npz"
                    report = json.loads(path.with_suffix(".json").read_bytes())
                    require(
                        report == summary["heads"][key]
                        and report["head"] == key
                        and report["freeze_sha256"] == binding
                        and report["policy_freeze_sha256"] == policy_binding
                        and report["counts_sha256"] == sha(path)
                        and report["original_counts_reproduced"],
                        "Later binding differs",
                    )
                    with np.load(path, allow_pickle=False) as saved:
                        require(set(saved.files) == set(POLICIES), "Policy inventory differs")
                        for p in POLICIES:
                            c = saved[p]
                            require(
                                c.shape == (4, 3000, 6)
                                and np.isfinite(c).all()
                                and np.all(c >= -1e-12)
                                and np.all(c[..., 2] <= c[..., 1] + 1e-12)
                                and np.all(c[..., 1] <= c[..., 0] + 1e-12)
                                and np.all(c[..., 2] <= c[..., 5] + 1e-12)
                                and np.allclose(
                                    c[..., 3], c[..., 1] + c[..., 4], atol=1e-12, rtol=0
                                ),
                                "Invalid match counts",
                            )
                            if p == "deterministic":
                                require(
                                    np.array_equal(c, np.rint(c)), "Fractional deterministic count"
                                )
                            counts[p][family][h][:, s, e] = c
                    artifacts[key] = report
                    selected_policies[key] = json.loads(
                        (study / "early" / f"{key}.json").read_bytes()
                    )
    reference = counts[POLICIES[0]][FAMILIES[0]]
    for p in POLICIES:
        for family in FAMILIES:
            for h in (30, 60):
                c = counts[p][family][h]
                for column in (0, 5):
                    require(
                        np.allclose(
                            c[..., column], reference[h][0, 0, :, :, column], rtol=0, atol=1e-12
                        ),
                        "Event/opportunity denominators differ",
                    )
    return (
        counts,
        plan,
        {
            "study_freeze_sha256": binding,
            "policy_freeze_sha256": policy_binding,
            "summary_sha256": sha(study / "summary.json"),
            "heads": artifacts,
        },
        selected_policies,
    )


def summarise(point, draws):
    """Retain fixed-seed points; bootstrap averages, never resample seed identities."""
    result = {}
    for event, p, b in [
        *((event, point[:, i], draws[:, :, i]) for i, event in enumerate(EVENTS)),
        ("macro", point.mean(1), draws.mean(2)),
    ]:
        result[event] = {
            m: {
                "mean": float(p[:, k].mean()),
                "ci95": np.percentile(b[:, :, k].mean(1), [2.5, 97.5]).tolist(),
                "seeds": p[:, k].tolist(),
                "min": float(p[:, k].min()),
                "max": float(p[:, k].max()),
                "sd": float(p[:, k].std(ddof=1)),
            }
            for k, m in enumerate(METRICS)
        }
    return result


def analyse(counts, routes, contrasts, draws=2000):
    results, violations = {}, []
    for region in ("overall", *REGIONS):
        idx = np.arange(len(routes)) if region == "overall" else np.flatnonzero(routes == region)
        weights = resample_weights(routes[idx], draws)
        results[region] = {}
        for h in (30, 60):
            results[region][str(h)] = {}
            for policy in POLICIES:
                points, sampled = {}, {}
                for family in FAMILIES:
                    # Each budget observes the SAME matches. Average rates over fixed
                    # budget points, without concatenating them into extra observations.
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
                    group[str(budget)] = {
                        "models": {f: summarise(p[f], b[f]) for f in FAMILIES},
                        "contrasts": {
                            f"{a}-minus-{z}": summarise(p[a] - p[z], b[a] - b[z])
                            for a, z in contrasts
                        },
                    }
                results[region][str(h)][policy] = group
                print(f"Analysed {region}/{h}/{policy}", flush=True)
    return results, violations


def frozen_rules(results, violations):
    groups = results["overall"]["30"]["matched_early_mixture"]
    contrast = "pcgrad-minus-leagueews"
    primary = groups["mean"]["contrasts"][contrast]
    macro = primary["macro"]
    rules = {
        "positive_recall": macro["timely_recall"]["ci95"][0] > 0
        and all(v > 0 for v in macro["timely_recall"]["seeds"]),
        "no_extra_burden": macro["false_plus_late_per_match"]["ci95"][1] <= 0,
        "no_mean_event_harm": all(primary[e]["timely_recall"]["mean"] >= 0 for e in EVENTS),
        "consistent_across_budgets": all(
            groups[str(b)]["contrasts"][contrast]["macro"]["timely_recall"]["mean"] > 0
            for b in BUDGETS
        ),
        "regional_hard_budget": not any(
            v["family"] == "pcgrad"
            and v["policy"] == "matched_early_mixture"
            and v["horizon"] == 30
            and v["above_hard_one"]
            for v in violations
        ),
    }
    rules["warning_efficiency_screen"] = all(rules.values())
    return rules


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
    counts, plan, provenance, selected = load(args.study, args.plan)
    routes = calibration_routes(args.archive)
    require(
        len(routes) == 3000 and all((routes == r).sum() == 1500 for r in REGIONS),
        "Later regions differ",
    )
    results, violations = analyse(counts, routes, plan["contrasts"])
    analysis = {
        "schema_version": "league-warning-efficiency-analysis-v1",
        "status": "exploratory-development-only",
        "test_payloads_opened": 0,
        "plan_sha256": sha(args.plan),
        "analysis_source_sha256": sha(Path(__file__)),
        "provenance": provenance,
        "uncertainty": plan["uncertainty"],
        "results": results,
        "nominal_budget_violations": violations,
        "frozen_rules": frozen_rules(results, violations),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "analysis.json", analysis)
    write_json(args.output / "early-policies.json", selected)
    write_aggregates(args.output, counts, routes, results)
    print(json.dumps(analysis["frozen_rules"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("study", "archive", "plan", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    main(parser.parse_args())
