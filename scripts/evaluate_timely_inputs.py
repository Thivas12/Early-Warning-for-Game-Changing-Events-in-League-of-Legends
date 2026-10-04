"""Gated policy evaluation for matched useful-lead input controls."""

from __future__ import annotations

import argparse
import fcntl
import json
import platform
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.notebook_experiment import SEEDS
from scripts.analyse_neural_screen import calibration_routes
from scripts.audit_neural_results import reference_counts
from scripts.evaluate_dense_policy import COARSE_IDS, GRID, NEW_POLICIES
from scripts.evaluate_dense_policy import select as select_dense
from scripts.evaluate_timely_neural import FAMILIES as OLD_FAMILIES
from scripts.evaluate_timely_neural import verify_inputs as verify_controls
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, load_partition
from scripts.run_warning_efficiency import REGIONS, ScoreCache, freeze_policies
from scripts.timely_neural_targets import fitted_targets
from scripts.warning_efficiency import (
    BUDGETS,
    THRESHOLD_VALUES,
    expected_counts,
    replay_calibration,
    select_deterministic,
    select_mixture,
)

FAMILIES = (*OLD_FAMILIES, "timely_current_only", "timely_clock_only")
OLD_POLICIES = ("deterministic", "regional_deterministic", "matched_early_mixture")
POLICIES = (*OLD_POLICIES, *NEW_POLICIES)


def verify_inputs(args, plan):
    require(plan["timely_plan_sha256"] == sha(args.control_plan), "Timely control plan differs")
    old_args = SimpleNamespace(**{**vars(args), "plan": args.control_plan})
    heads, bindings = verify_controls(old_args, json.loads(args.control_plan.read_bytes()))
    repo = Path(__file__).resolve().parents[1]
    frozen = json.loads((args.inputs / "freeze.json").read_bytes())
    summary = json.loads((args.inputs / "summary.json").read_bytes())
    binding = sha(args.inputs / "freeze.json")
    require(
        summary["status"] == "complete-exploratory-timely-inputs-predictions"
        and summary["freeze_sha256"] == binding
        and summary["test_payloads_opened"] == 0
        and frozen["plan"] == plan
        and frozen["plan_sha256"] == sha(args.plan)
        and frozen["archive_sha256"] == EXPECTED_ARCHIVE,
        "Input study incomplete or changed",
    )
    require(
        all(sha(repo / p) == v for p, v in frozen["source_sha256"].items()), "Input source changed"
    )
    require(
        set(summary["models"])
        == {f"{f}/{s}" for f in ("current_only", "clock_only") for s in SEEDS},
        "Six input fits required",
    )
    bindings["input_controls"] = {
        "freeze_sha256": binding,
        "summary_sha256": sha(args.inputs / "summary.json"),
        "fits": {},
    }
    for family in ("current_only", "clock_only"):
        for seed in SEEDS:
            folder = args.inputs / family / f"seed-{seed}"
            report = json.loads((folder / "report.json").read_bytes())
            progress = json.loads((folder / "progress.json").read_bytes())
            require(
                report == summary["models"][f"{family}/{seed}"]
                and report["family"] == progress["family"] == family
                and report["seed"] == progress["seed"] == seed
                and report["freeze_sha256"] == progress["freeze_sha256"] == binding
                and report["architecture"] == progress["architecture"] == "leagueews"
                and report["input_intervention"] == progress["input_intervention"] == family
                and report["parameters"] == 1751647
                and progress["completed_units"] == 576
                and report["checkpoint_sha256"] == sha(folder / "checkpoint.pt")
                and report["scores_sha256"] == sha(folder / "calibration-scores.npz"),
                "Input control artifact differs",
            )
            bindings["input_controls"]["fits"][f"{family}/{seed}"] = report
            for e, event in enumerate(EVENTS):
                for h, c in ((30, 2), (60, 3)):
                    heads.append(
                        {
                            "key": f"timely_{family}-{seed}-{event}-{h}",
                            "family": f"timely_{family}",
                            "seed": seed,
                            "event": event,
                            "horizon": h,
                            "column": 4 * e + c,
                            "folder": folder,
                            "report": report,
                        }
                    )
    for name, field, status in (
        ("reference", "reference_policy_summary_sha256", "complete-exploratory-timely-policy"),
        ("dense", "dense_reference_summary_sha256", "complete-exploratory-dense-policy"),
    ):
        folder = getattr(args, name)
        summary = json.loads((folder / "summary.json").read_bytes())
        require(
            sha(folder / "summary.json") == plan[field]
            and summary["status"] == status
            and sha(folder / "freeze.json") == summary["freeze_sha256"]
            and sha(folder / "policy-freeze.json") == summary["policy_freeze_sha256"],
            "Prior policy reference changed",
        )
        reference_heads = [{"key": k} for k in summary["heads"]]
        require(
            freeze_policies(folder, reference_heads, summary["freeze_sha256"])
            == summary["policy_freeze_sha256"],
            "Prior early policy changed",
        )
        for key, report in summary["heads"].items():
            require(
                sha(folder / "later" / f"{key}.npz") == report["counts_sha256"],
                "Prior match counts changed",
            )
        bindings[name] = {
            "summary_sha256": sha(folder / "summary.json"),
            "freeze_sha256": sha(folder / "freeze.json"),
        }
    require(len(heads) == 198, "All eleven variants required")
    return heads, bindings


def select_head(
    cal, probabilities, head, early, regions, binding, reference=None, dense_reference=None
):
    counts = replay_calibration(cal, probabilities, head["event"], early, head["horizon"], GRID)
    totals = np.stack([counts[regions == r].sum(0) for r in REGIONS])
    coarse = totals[:, COARSE_IDS]
    sizes = [int((regions == r).sum()) for r in REGIONS]
    require(sizes == [1500, 1500], "Early regions differ")
    policies = {p: {} for p in POLICIES}
    for budget in BUDGETS:
        policies["deterministic"][str(budget)] = select_deterministic(coarse, sizes, budget)
        policies["regional_deterministic"][str(budget)] = {
            r: select_deterministic(coarse[i : i + 1], sizes[i : i + 1], budget)
            for i, r in enumerate(REGIONS)
        }
        policies["matched_early_mixture"][str(budget)] = {
            r: select_mixture(coarse[i], sizes[i], budget) for i, r in enumerate(REGIONS)
        }
        policies[NEW_POLICIES[0]][str(budget)] = select_dense(totals, sizes, budget)
        policies[NEW_POLICIES[1]][str(budget)] = {
            r: select_dense(totals[i : i + 1], sizes[i : i + 1], budget)
            for i, r in enumerate(REGIONS)
        }
    if reference is not None:
        require(
            np.array_equal(coarse, reference["early_threshold_counts_by_region"])
            and all(policies[p] == reference["policies"][p] for p in OLD_POLICIES),
            "Old early policy differs",
        )
    if dense_reference is not None:
        require(
            np.array_equal(totals, dense_reference["early_threshold_counts_by_region"])
            and all(policies[p] == dense_reference["policies"][p] for p in NEW_POLICIES),
            "Dense early policy differs",
        )
    return {
        "head": head["key"],
        "freeze_sha256": binding,
        "early_region_sizes": sizes,
        "early_threshold_counts_by_region": totals.tolist(),
        "policies": policies,
    }


def evaluate_head(
    cal, saved, head, selection, later, regions, reference=None, dense_reference=None
):
    policies = selection["policies"]
    ids = {COARSE_IDS[i] for i in policies["deterministic"].values()}
    for v in policies["regional_deterministic"].values():
        ids.update(COARSE_IDS[i] for i in v.values())
    for v in policies["matched_early_mixture"].values():
        for p in v.values():
            ids.update(COARSE_IDS[i] for i in p["indices"])
    ids.update(policies[NEW_POLICIES[0]].values())
    for v in policies[NEW_POLICIES[1]].values():
        ids.update(v.values())
    ids = sorted(ids)
    thresholds = tuple(GRID[i] for i in ids)
    scores = saved["probabilities"][:, head["column"]]
    counts = replay_calibration(cal, scores, head["event"], later, head["horizon"], thresholds)
    outputs = {p: [] for p in POLICIES}
    for budget in BUDGETS:
        outputs["deterministic"].append(
            counts[:, ids.index(COARSE_IDS[policies["deterministic"][str(budget)]])]
        )
        outputs[NEW_POLICIES[0]].append(
            counts[:, ids.index(policies[NEW_POLICIES[0]][str(budget)])]
        )
        local = np.empty((len(later), 6))
        dense = np.empty_like(local)
        mixture = np.empty_like(local)
        for r in REGIONS:
            idx = regions == r
            local[idx] = counts[
                idx, ids.index(COARSE_IDS[policies["regional_deterministic"][str(budget)][r]])
            ]
            dense[idx] = counts[idx, ids.index(policies[NEW_POLICIES[1]][str(budget)][r])]
            p = policies["matched_early_mixture"][str(budget)][r]
            mixture[idx] = expected_counts(
                counts[idx], {**p, "indices": [ids.index(COARSE_IDS[i]) for i in p["indices"]]}
            )
        outputs["regional_deterministic"].append(local)
        outputs[NEW_POLICIES[1]].append(dense)
        outputs["matched_early_mixture"].append(mixture)
    outputs = {k: np.stack(v) for k, v in outputs.items()}
    for ref, keys in ((reference, OLD_POLICIES), (dense_reference, NEW_POLICIES)):
        if ref is not None:
            require(
                all(np.array_equal(outputs[p], ref[p]) for p in keys),
                "Previous match counts differ",
            )
    checks = 0
    for n in np.linspace(0, len(later) - 1, min(31, len(later)), dtype=int):
        i = later[n]
        a, b = cal["match_offsets"][i : i + 2]
        left, right = cal[f"{head['event']}_offsets"][i : i + 2]
        for j, t in enumerate(thresholds):
            expected = reference_counts(
                cal["times_ms"][a:b],
                cal[f"{head['event']}_ms"][left:right],
                scores[a:b],
                t,
                head["horizon"],
            )
            require(np.array_equal(counts[n, j], expected), "Independent component replay differs")
            checks += 1
    full = 0
    if head["family"] in ("timely_current_only", "timely_clock_only"):
        for policy, t in (
            ("deterministic", THRESHOLD_VALUES[policies["deterministic"]["1.0"]]),
            (NEW_POLICIES[0], GRID[policies[NEW_POLICIES[0]]["1.0"]]),
        ):
            for n, i in enumerate(later):
                a, b = cal["match_offsets"][i : i + 2]
                left, right = cal[f"{head['event']}_offsets"][i : i + 2]
                expected = reference_counts(
                    cal["times_ms"][a:b],
                    cal[f"{head['event']}_ms"][left:right],
                    scores[a:b],
                    t,
                    head["horizon"],
                )
                require(
                    np.array_equal(outputs[policy][-1, n], expected),
                    "Full new reference replay differs",
                )
                full += 1
    return outputs, checks, full


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    require(
        plan["evaluation_families"] == list(FAMILIES)
        and plan["policies"] == list(POLICIES)
        and plan["budgets"] == list(BUDGETS)
        and plan["thresholds"] == list(THRESHOLD_VALUES)
        and plan["dense_thresholds"] == list(GRID),
        "Plan differs",
    )
    heads, bindings = verify_inputs(args, plan)
    calibration_routes(args.archive)
    files = (
        "scripts/evaluate_timely_inputs.py",
        "scripts/analyse_timely_inputs.py",
        "scripts/evaluate_timely_neural.py",
        "scripts/evaluate_dense_policy.py",
        "scripts/timely_neural_targets.py",
        "scripts/warning_efficiency.py",
        "scripts/run_warning_efficiency.py",
        "scripts/analyse_neural_screen.py",
        "scripts/audit_neural_results.py",
        "scripts/league_compact_data.py",
        "scripts/export_league_development.py",
        "src/league_ews/coordination_experiment.py",
        "src/league_ews/m1_alert_diagnostics.py",
        "src/league_ews/alert_policy.py",
        "src/league_ews/constants.py",
        "src/league_ews/notebook_experiment.py",
    )
    frozen = {
        "schema_version": "league-timely-input-policy-freeze-v1",
        "plan": plan,
        "plan_sha256": sha(args.plan),
        "studies": bindings,
        "archive_sha256": EXPECTED_ARCHIVE,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "source_sha256": {p: sha(repo / p) for p in files},
        "test_payloads_opened": 0,
    }
    path = args.output / "freeze.json"
    if path.exists():
        require(
            json.loads(path.read_bytes()) == frozen, "Evaluation freeze changed; preserve artifacts"
        )
    else:
        write_json(path, frozen)
    binding = sha(path)
    cal, rows = load_partition(args.archive, "calibration")
    early, later = _chronological_halves(rows)
    require(
        len(early) == len(later) == 3000 and not set(early) & set(later),
        "Calibration split differs",
    )
    early_regions = np.array([rows[i]["regional_route"] for i in early])
    late_regions = np.array([rows[i]["regional_route"] for i in later])
    cache = ScoreCache(cal)
    useful = fitted_targets(cal)
    used = 0
    for head in heads:
        path = args.output / "early" / f"{head['key']}.json"
        if path.exists():
            value = json.loads(path.read_bytes())
            require(
                value["head"] == head["key"] and value["freeze_sha256"] == binding,
                "Early binding differs",
            )
            continue
        saved = cache.get(head)
        if head["family"].startswith("timely_"):
            require(
                np.array_equal(saved["fitted_targets"], useful), "Fitted-target alignment differs"
            )
        prior_path = args.reference / "early" / f"{head['key']}.json"
        dense_path = args.dense / "early" / f"{head['key']}.json"
        prior = json.loads(prior_path.read_bytes()) if prior_path.exists() else None
        dense = json.loads(dense_path.read_bytes()) if dense_path.exists() else None
        value = select_head(
            cal,
            saved["probabilities"][:, head["column"]],
            head,
            early,
            early_regions,
            binding,
            prior,
            dense,
        )
        write_json(path, value)
        used += 1
        print(f"Selected {head['key']}", flush=True)
        if args.max_new_heads and used >= args.max_new_heads:
            return {"status": "paused-after-early-selection", "new_heads": used}
    policy_binding = freeze_policies(args.output, heads, binding)
    print(f"All 198 early heads frozen: {policy_binding}", flush=True)
    if args.early_only:
        return {"status": "all-early-policies-frozen", "policy_freeze_sha256": policy_binding}
    reports = {}
    for head in heads:
        folder = args.output / "later"
        folder.mkdir(exist_ok=True)
        key = head["key"]
        report_path = folder / f"{key}.json"
        counts_path = folder / f"{key}.npz"
        if report_path.exists():
            report = json.loads(report_path.read_bytes())
            require(
                report["head"] == key
                and report["freeze_sha256"] == binding
                and report["policy_freeze_sha256"] == policy_binding
                and report["counts_sha256"] == sha(counts_path),
                "Later artifact changed",
            )
        else:
            saved = cache.get(head)
            references = []
            for folder in (args.reference, args.dense):
                path = folder / "later" / f"{key}.npz"
                if path.exists():
                    with np.load(path, allow_pickle=False) as z:
                        references.append({k: z[k] for k in z.files})
                else:
                    references.append(None)
            reference, dense_reference = references
            selected = json.loads((args.output / "early" / f"{key}.json").read_bytes())
            values, checks, full = evaluate_head(
                cal, saved, head, selected, later, late_regions, reference, dense_reference
            )
            with counts_path.with_suffix(".partial").open("wb") as stream:
                np.savez_compressed(stream, **values)
            counts_path.with_suffix(".partial").replace(counts_path)
            report = {
                "head": key,
                "freeze_sha256": binding,
                "policy_freeze_sha256": policy_binding,
                "counts_sha256": sha(counts_path),
                "previous_counts_reproduced": reference is not None,
                "dense_counts_reproduced": dense_reference is not None,
                "independent_component_checks": checks,
                "new_full_reference_checks": full,
            }
            write_json(report_path, report)
            print(f"Evaluated {key}", flush=True)
        reports[key] = report
    summary = {
        "schema_version": "league-timely-input-policy-summary-v1",
        "status": "complete-exploratory-timely-input-policy",
        "freeze_sha256": binding,
        "policy_freeze_sha256": policy_binding,
        "heads": reports,
        "test_payloads_opened": 0,
        "new_neural_fits": 6,
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
        "inputs",
        "reference",
        "dense",
        "control-plan",
        "plan",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--early-only", action="store_true")
    parser.add_argument("--max-new-heads", type=int, default=0)
    args = parser.parse_args()
    require(args.max_new_heads >= 0, "Invalid head limit")
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
            args.inputs,
            args.reference,
            args.dense,
        ):
            lock = stack.enter_context((p / "experiment.lock").open("rb"))
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        print(json.dumps(run(args), indent=2))
