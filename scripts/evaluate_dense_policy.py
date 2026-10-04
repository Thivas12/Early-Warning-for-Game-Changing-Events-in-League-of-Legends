"""Frozen finer-grid deterministic control using completed neural scores only."""

from __future__ import annotations

import argparse
import fcntl
import json
import platform
from contextlib import ExitStack
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from scripts.analyse_neural_screen import calibration_routes
from scripts.audit_neural_results import reference_counts
from scripts.evaluate_timely_neural import REGIONS, ScoreCache, freeze_policies, verify_inputs
from scripts.export_league_development import require
from scripts.league_compact_data import load_partition
from scripts.warning_efficiency import BUDGETS, THRESHOLD_VALUES, replay_calibration

FAMILIES = ("leagueews", "tcn", "timely_leagueews", "timely_tcn")
NEW_POLICIES = ("dense_deterministic", "dense_regional_deterministic")
POLICIES = ("deterministic", "regional_deterministic", "matched_early_mixture", *NEW_POLICIES)


def dense_grid():
    """Ten log intervals per old interval, retaining old endpoints bit-for-bit."""
    old = THRESHOLD_VALUES[1:]
    values = [None, old[0]]
    for high, low in pairwise(old):
        values.extend(float(high * (low / high) ** (j / 10)) for j in range(1, 10))
        values.append(low)
    return tuple(values)


GRID = dense_grid()
COARSE_IDS = [GRID.index(t) for t in THRESHOLD_VALUES]


def select(totals, sizes, budget):
    """Same feasible-budget and hit/cost/high-threshold tie rule on the dense grid."""
    require(totals.shape[1:] == (len(GRID), 6), "Grid/count mismatch")
    cost = (totals[:, :, 3] - totals[:, :, 2]) / np.asarray(sizes)[:, None]
    valid = np.flatnonzero(np.all(cost <= budget, axis=0))
    require(len(valid) > 0, "Silent policy must be feasible")
    sums = totals.sum(0)
    return int(max(valid, key=lambda i: (sums[i, 2], -(sums[i, 3] - sums[i, 2]), -i)))


def select_head(cal, scores, head, early, regions, binding, prior):
    counts = replay_calibration(cal, scores, head["event"], early, head["horizon"], GRID)
    totals = np.stack([counts[regions == r].sum(0) for r in REGIONS])
    sizes = [int((regions == r).sum()) for r in REGIONS]
    require(sizes == [1500, 1500], "Early regions differ")
    require(
        np.array_equal(totals[:, COARSE_IDS], prior["early_threshold_counts_by_region"]),
        "Coarse-grid early replay differs",
    )
    policies = {p: {} for p in NEW_POLICIES}
    for budget in BUDGETS:
        common = select(totals, sizes, budget)
        policies[NEW_POLICIES[0]][str(budget)] = common
        policies[NEW_POLICIES[1]][str(budget)] = {
            r: select(totals[i : i + 1], sizes[i : i + 1], budget) for i, r in enumerate(REGIONS)
        }
        # A nested candidate set cannot reduce the selected EARLY hit objective.
        coarse = prior["policies"]["deterministic"][str(budget)]
        require(
            totals[:, common, 2].sum() >= totals[:, COARSE_IDS[coarse], 2].sum(),
            "Nested common grid lost early hits",
        )
        for i, r in enumerate(REGIONS):
            coarse = prior["policies"]["regional_deterministic"][str(budget)][r]
            require(
                totals[i, policies[NEW_POLICIES[1]][str(budget)][r], 2]
                >= totals[i, COARSE_IDS[coarse], 2],
                "Nested regional grid lost early hits",
            )
    return {
        "head": head["key"],
        "freeze_sha256": binding,
        "policies": policies,
        "early_region_sizes": sizes,
        "early_threshold_counts_by_region": totals.tolist(),
    }


def evaluate_head(cal, scores, head, selected, later, regions):
    policies = selected["policies"]
    ids = set(policies[NEW_POLICIES[0]].values())
    for v in policies[NEW_POLICIES[1]].values():
        ids.update(v.values())
    ids = sorted(ids)
    counts = replay_calibration(
        cal, scores, head["event"], later, head["horizon"], tuple(GRID[i] for i in ids)
    )
    values = {p: [] for p in NEW_POLICIES}
    for budget in BUDGETS:
        values[NEW_POLICIES[0]].append(counts[:, ids.index(policies[NEW_POLICIES[0]][str(budget)])])
        local = np.empty((len(later), 6), dtype=np.int64)
        for r in REGIONS:
            idx = regions == r
            local[idx] = counts[idx, ids.index(policies[NEW_POLICIES[1]][str(budget)][r])]
        values[NEW_POLICIES[1]].append(local)
    # Reference-check both new budget-one policies on EVERY later match, plus
    # every selected threshold on a fixed sample of matches.
    checks = 0
    sample = set(np.linspace(0, len(later) - 1, min(31, len(later)), dtype=int))
    for n, i in enumerate(later):
        selected_ids = (
            set(ids)
            if n in sample
            else {policies[NEW_POLICIES[0]]["1.0"], policies[NEW_POLICIES[1]]["1.0"][regions[n]]}
        )
        a, b = cal["match_offsets"][i : i + 2]
        left, right = cal[f"{head['event']}_offsets"][i : i + 2]
        for j in selected_ids:
            reference = reference_counts(
                cal["times_ms"][a:b],
                cal[f"{head['event']}_ms"][left:right],
                scores[a:b],
                GRID[j],
                head["horizon"],
            )
            require(np.array_equal(counts[n, ids.index(j)], reference), "Reference replay differs")
            checks += 1
    return {p: np.stack(v) for p, v in values.items()}, checks


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    require(
        plan["families"] == list(FAMILIES)
        and plan["thresholds"] == list(GRID)
        and plan["budgets"] == list(BUDGETS)
        and plan["policies"] == list(POLICIES)
        and plan["control_plan_sha256"] == sha(args.control_plan),
        "Plan mismatch",
    )
    old_args = SimpleNamespace(**{**vars(args), "plan": args.control_plan})
    heads, bindings = verify_inputs(old_args, json.loads(args.control_plan.read_bytes()))
    heads = [h for h in heads if h["family"] in FAMILIES]
    require(len(heads) == 72, "Head inventory differs")
    reference = json.loads((args.reference / "summary.json").read_bytes())
    require(
        reference["status"] == "complete-exploratory-timely-policy"
        and sha(args.reference / "summary.json") == plan["reference_summary_sha256"]
        and sha(args.reference / "freeze.json") == reference["freeze_sha256"]
        and sha(args.reference / "policy-freeze.json") == reference["policy_freeze_sha256"],
        "Reference study changed",
    )
    old_freeze = json.loads((args.reference / "freeze.json").read_bytes())
    files = {
        *old_freeze["source_sha256"],
        "scripts/evaluate_dense_policy.py",
        "scripts/analyse_dense_policy.py",
        "scripts/analyse_timely_neural.py",
    }
    source = {p: sha(repo / p) for p in sorted(files)}
    require(
        all(source[p] == v for p, v in old_freeze["source_sha256"].items()),
        "Reference source changed",
    )
    frozen = {
        "schema_version": "league-dense-policy-freeze-v1",
        "plan": plan,
        "plan_sha256": sha(args.plan),
        "studies": bindings,
        "source_sha256": source,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "test_payloads_opened": 0,
    }
    path = args.output / "freeze.json"
    if path.exists():
        require(json.loads(path.read_bytes()) == frozen, "Frozen study differs")
    else:
        write_json(path, frozen)
    binding = sha(path)
    calibration_routes(args.archive)
    # Validate the complete reference early selection before reading new scores.
    reference_heads = [{"key": k} for k in reference["heads"]]
    require(
        freeze_policies(args.reference, reference_heads, reference["freeze_sha256"])
        == reference["policy_freeze_sha256"],
        "Reference early policy changed",
    )
    cal, rows = load_partition(args.archive, "calibration")
    early, later = _chronological_halves(rows)
    require(len(early) == len(later) == 3000 and not set(early) & set(later), "Split differs")
    early_regions = np.array([rows[i]["regional_route"] for i in early])
    later_regions = np.array([rows[i]["regional_route"] for i in later])
    cache = ScoreCache(cal)
    for head in heads:
        key = head["key"]
        path = args.output / "early" / f"{key}.json"
        if path.exists():
            selected = json.loads(path.read_bytes())
            require(
                selected["head"] == key and selected["freeze_sha256"] == binding,
                "Early binding differs",
            )
        else:
            saved = cache.get(head)
            prior = json.loads((args.reference / "early" / f"{key}.json").read_bytes())
            selected = select_head(
                cal,
                saved["probabilities"][:, head["column"]],
                head,
                early,
                early_regions,
                binding,
                prior,
            )
            write_json(path, selected)
            print(f"Selected {key}", flush=True)
    gate = freeze_policies(args.output, heads, binding)
    if args.early_only:
        return {"status": "all-72-early-heads-frozen", "policy_freeze_sha256": gate}
    reports = {}
    for head in heads:
        key = head["key"]
        path = args.output / "later" / f"{key}.json"
        arrays = path.with_suffix(".npz")
        if path.exists():
            report = json.loads(path.read_bytes())
            require(
                report["head"] == key
                and report["freeze_sha256"] == binding
                and report["policy_freeze_sha256"] == gate
                and report["counts_sha256"] == sha(arrays),
                "Later artifact differs",
            )
        else:
            selected = json.loads((args.output / "early" / f"{key}.json").read_bytes())
            scores = cache.get(head)["probabilities"][:, head["column"]]
            values, checks = evaluate_head(cal, scores, head, selected, later, later_regions)
            path.parent.mkdir(exist_ok=True)
            with arrays.with_suffix(".partial").open("wb") as stream:
                np.savez_compressed(stream, **values)
            arrays.with_suffix(".partial").replace(arrays)
            report = {
                "head": key,
                "freeze_sha256": binding,
                "policy_freeze_sha256": gate,
                "counts_sha256": sha(arrays),
                "independent_reference_checks": checks,
            }
            write_json(path, report)
            print(f"Evaluated {key}", flush=True)
        reports[key] = report
    summary = {
        "schema_version": "league-dense-policy-summary-v1",
        "status": "complete-exploratory-dense-policy",
        "freeze_sha256": binding,
        "policy_freeze_sha256": gate,
        "heads": reports,
        "new_fits": 0,
        "test_payloads_opened": 0,
    }
    write_json(args.output / "summary.json", summary)
    return {"status": summary["status"], "summary": str(args.output / "summary.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "archive",
        "control",
        "history",
        "independent",
        "pcgrad",
        "study",
        "warning",
        "reference",
        "control-plan",
        "plan",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--early-only", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        lock = stack.enter_context((args.output / "experiment.lock").open("a+b"))
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for p in (
            args.control,
            args.history,
            args.independent,
            args.pcgrad,
            args.study,
            args.warning,
            args.reference,
        ):
            lock = stack.enter_context((p / "experiment.lock").open("rb"))
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        print(json.dumps(run(args), indent=2))
