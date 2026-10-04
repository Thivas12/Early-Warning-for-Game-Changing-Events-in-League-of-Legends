"""Paired whole-match input-mechanism analysis under useful-lead supervision."""

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
from scripts.evaluate_timely_inputs import FAMILIES, POLICIES, REGIONS, freeze_policies
from scripts.export_league_development import require
from scripts.warning_efficiency import BUDGETS


def load(study, plan_path):
    frozen = json.loads((study / "freeze.json").read_bytes())
    summary = json.loads((study / "summary.json").read_bytes())
    binding = sha(study / "freeze.json")
    require(summary["status"] == "complete-exploratory-timely-input-policy", "Incomplete study")
    require(
        summary["freeze_sha256"] == binding
        and summary["test_payloads_opened"] == 0
        and summary["new_neural_fits"] == 6,
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
                        and (
                            report["previous_counts_reproduced"]
                            or report["new_full_reference_checks"] == 6000
                        ),
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
                            if p != "matched_early_mixture":
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
                    comparisons["history_effect_difference_timely_minus_cumulative"] = summarise(
                        (p["timely_leagueews"] - p["timely_current_only"])
                        - (p["leagueews"] - p["current_only"]),
                        (b["timely_leagueews"] - b["timely_current_only"])
                        - (b["leagueews"] - b["current_only"]),
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
                        ("regional_deterministic", "deterministic"),
                        ("matched_early_mixture", "regional_deterministic"),
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
            policy_effects[region][str(h)] = effects
    return results, violations, policy_effects


def frozen_rules(results, violations):
    groups = results["overall"]["30"]["matched_early_mixture"]["mean"]["contrasts"]
    history = groups["timely_leagueews-minus-timely_current_only"]
    clock = groups["timely_leagueews-minus-timely_clock_only"]["macro"]["timely_recall"]
    primary = history["macro"]["timely_recall"]
    regional = [
        results[r]["30"]["matched_early_mixture"]["mean"]["contrasts"][
            "timely_leagueews-minus-timely_current_only"
        ]["macro"]["timely_recall"]
        for r in REGIONS
    ]
    return {
        "history_support": primary["ci95"][0] > 0 and all(v > 0 for v in primary["seeds"]),
        "beyond_timing_support": clock["ci95"][0] > 0 and all(v > 0 for v in clock["seeds"]),
        "history_event_nonharm": all(history[e]["timely_recall"]["mean"] >= 0 for e in EVENTS),
        "history_no_extra_burden": history["macro"]["false_plus_late_per_match"]["ci95"][1] <= 0,
        "regional_history_consistency": all(
            v["ci95"][0] > 0 and all(z > 0 for z in v["seeds"]) for v in regional
        ),
        "primary_full_input_regional_hard_one_violations": sum(
            v["family"] == "timely_leagueews"
            and v["policy"] == "matched_early_mixture"
            and v["horizon"] == 30
            and v["above_hard_one"]
            for v in violations
        ),
        "practical_promotion": (
            "not established; diagnostic study cannot erase prior failed budget gates"
        ),
    }


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
    results, violations, policy_effects = analyse(counts, routes, plan["contrasts"])
    analysis = {
        "schema_version": "league-timely-input-analysis-v1",
        "status": "exploratory-development-only",
        "test_payloads_opened": 0,
        "plan_sha256": sha(args.plan),
        "analysis_source_sha256": sha(Path(__file__)),
        "provenance": provenance,
        "uncertainty": plan["uncertainty"],
        "results": results,
        "policy_effects": policy_effects,
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
