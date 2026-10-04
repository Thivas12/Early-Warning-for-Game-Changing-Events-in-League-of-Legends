"""Freeze every early policy before evaluating the timely-target neural controls."""

from __future__ import annotations

import argparse
import fcntl
import json
import platform
from contextlib import ExitStack
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.notebook_experiment import SEEDS
from scripts.analyse_neural_screen import calibration_routes
from scripts.audit_neural_results import reference_counts
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, load_partition
from scripts.run_warning_efficiency import FAMILIES as OLD_FAMILIES
from scripts.run_warning_efficiency import REGIONS, ScoreCache, freeze_policies, inputs
from scripts.timely_neural_targets import fitted_targets
from scripts.warning_efficiency import (
    BUDGETS,
    THRESHOLD_VALUES,
    expected_counts,
    replay_calibration,
    select_deterministic,
    select_mixture,
)

FAMILIES = (*OLD_FAMILIES, "timely_leagueews", "timely_tcn")
POLICIES = ("deterministic", "regional_deterministic", "matched_early_mixture")


def verify_inputs(args, plan):
    heads, bindings = inputs(args, plan)
    path = args.study
    frozen = json.loads((path / "freeze.json").read_bytes())
    summary = json.loads((path / "summary.json").read_bytes())
    binding = sha(path / "freeze.json")
    require(
        summary["status"] == "complete-exploratory-timely-neural-predictions"
        and summary["freeze_sha256"] == binding
        and summary["test_payloads_opened"] == 0
        and frozen["plan_sha256"] == sha(args.plan)
        and frozen["plan"] == plan
        and frozen["archive_sha256"] == EXPECTED_ARCHIVE,
        "Timely study incomplete or mismatched",
    )
    repo = Path(__file__).resolve().parents[1]
    for name, value in frozen["source_sha256"].items():
        require(sha(repo / name) == value, f"Training source changed: {name}")
    require(
        set(summary["models"]) == {f"{f}/{s}" for f in ("leagueews", "tcn") for s in SEEDS},
        "Six timely fits required",
    )
    bindings["timely"] = {
        "freeze_sha256": binding,
        "summary_sha256": sha(path / "summary.json"),
        "fits": {},
    }
    for family in ("leagueews", "tcn"):
        for seed in SEEDS:
            folder = path / family / f"seed-{seed}"
            report = json.loads((folder / "report.json").read_bytes())
            progress = json.loads((folder / "progress.json").read_bytes())
            key = f"{family}/{seed}"
            require(
                report == summary["models"][key]
                and report["freeze_sha256"] == progress["freeze_sha256"] == binding
                and report["family"] == progress["family"] == family
                and report["seed"] == progress["seed"] == seed
                and progress["completed_units"] == 576
                and report["test_payloads_opened"] == 0
                and report["checkpoint_sha256"] == sha(folder / "checkpoint.pt")
                and report["scores_sha256"] == sha(folder / "calibration-scores.npz"),
                "Timely fit changed",
            )
            bindings["timely"]["fits"][key] = {
                "report_sha256": sha(folder / "report.json"),
                "checkpoint_sha256": report["checkpoint_sha256"],
                "scores_sha256": report["scores_sha256"],
            }
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
    previous = json.loads((args.warning / "summary.json").read_bytes())
    record = json.loads(
        (repo / "reports/warning-efficiency-2026-10-03/execution-record.json").read_bytes()
    )
    require(
        sha(args.warning / "summary.json") == record["summary_sha256"]
        and sha(args.warning / "freeze.json")
        == record["study_freeze_sha256"]
        == previous["freeze_sha256"]
        and previous["status"] == "complete-exploratory-warning-efficiency"
        and previous["test_payloads_opened"] == 0,
        "Prior warning reference changed",
    )
    for head in heads[:126]:
        key = head["key"]
        report = previous["heads"][key]
        require(
            report["counts_sha256"] == sha(args.warning / "later" / f"{key}.npz"),
            "Prior policy counts changed",
        )
    bindings["warning_reference"] = {
        "summary_sha256": sha(args.warning / "summary.json"),
        "freeze_sha256": sha(args.warning / "freeze.json"),
    }
    require(len(heads) == 162, "All nine variants required")
    return heads, bindings


def select_head(cal, probabilities, head, early, regions, binding):
    counts = replay_calibration(cal, probabilities, head["event"], early, head["horizon"])
    totals = np.stack([counts[regions == r].sum(0) for r in REGIONS])
    sizes = [int((regions == r).sum()) for r in REGIONS]
    require(sizes == [1500, 1500], "Early regions differ")
    policies = {p: {} for p in POLICIES}
    for budget in BUDGETS:
        policies["deterministic"][str(budget)] = select_deterministic(totals, sizes, budget)
        policies["regional_deterministic"][str(budget)] = {
            r: select_deterministic(totals[i : i + 1], sizes[i : i + 1], budget)
            for i, r in enumerate(REGIONS)
        }
        policies["matched_early_mixture"][str(budget)] = {
            r: select_mixture(totals[i], sizes[i], budget) for i, r in enumerate(REGIONS)
        }
    if not head["family"].startswith("timely_"):
        require(
            THRESHOLD_VALUES[policies["deterministic"]["1.0"]]
            == head["report"]["warnings"][f"{head['event']}_{head['horizon']}"]["threshold"],
            "Original threshold changed",
        )
    return {
        "head": head["key"],
        "freeze_sha256": binding,
        "early_region_sizes": sizes,
        "early_threshold_counts_by_region": totals.tolist(),
        "policies": policies,
    }


def evaluate_head(cal, saved, head, selection, later, regions, reference=None):
    policies = selection["policies"]
    indices = set(policies["deterministic"].values())
    for regional in policies["regional_deterministic"].values():
        indices.update(regional.values())
    for regional in policies["matched_early_mixture"].values():
        for policy in regional.values():
            indices.update(policy["indices"])
    ids = sorted(indices)
    thresholds = tuple(THRESHOLD_VALUES[i] for i in ids)
    p = saved["probabilities"][:, head["column"]]
    counts = replay_calibration(cal, p, head["event"], later, head["horizon"], thresholds)
    outputs = {k: [] for k in POLICIES}
    for budget in BUDGETS:
        outputs["deterministic"].append(
            counts[:, ids.index(policies["deterministic"][str(budget)])].astype(float)
        )
        local = np.empty((len(later), 6))
        mixture = np.empty_like(local)
        for region in REGIONS:
            idx = regions == region
            local[idx] = counts[
                idx, ids.index(policies["regional_deterministic"][str(budget)][region])
            ]
            policy = policies["matched_early_mixture"][str(budget)][region]
            mapped = {**policy, "indices": [ids.index(i) for i in policy["indices"]]}
            mixture[idx] = expected_counts(counts[idx], mapped)
        outputs["regional_deterministic"].append(local)
        outputs["matched_early_mixture"].append(mixture)
    outputs = {k: np.stack(v) for k, v in outputs.items()}
    if reference is not None:
        for policy in ("deterministic", "matched_early_mixture"):
            require(
                np.array_equal(outputs[policy], reference[policy]), "Previous policy counts changed"
            )
        require(
            np.array_equal(
                outputs["deterministic"][-1], saved[f"counts_{head['event']}_{head['horizon']}"]
            ),
            "Registered counts changed",
        )
    sample = np.linspace(0, len(later) - 1, min(31, len(later)), dtype=int)
    checks = 0
    for n in sample:
        i = later[n]
        a, b = cal["match_offsets"][i : i + 2]
        left, right = cal[f"{head['event']}_offsets"][i : i + 2]
        for j, threshold in enumerate(thresholds):
            expected = reference_counts(
                cal["times_ms"][a:b],
                cal[f"{head['event']}_ms"][left:right],
                p[a:b],
                threshold,
                head["horizon"],
            )
            require(np.array_equal(counts[n, j], expected), "Independent component replay differs")
            checks += 1
    full_checks = 0
    if head["family"].startswith("timely_"):
        threshold = THRESHOLD_VALUES[policies["deterministic"]["1.0"]]
        for n, i in enumerate(later):
            a, b = cal["match_offsets"][i : i + 2]
            left, right = cal[f"{head['event']}_offsets"][i : i + 2]
            expected = reference_counts(
                cal["times_ms"][a:b],
                cal[f"{head['event']}_ms"][left:right],
                p[a:b],
                threshold,
                head["horizon"],
            )
            require(
                np.array_equal(outputs["deterministic"][-1, n], expected),
                "New full reference replay differs",
            )
            full_checks += 1
    return outputs, checks, full_checks


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    require(
        plan["evaluation_families"] == list(FAMILIES)
        and plan["policies"] == list(POLICIES)
        and plan["budgets"] == list(BUDGETS)
        and plan["thresholds"] == list(THRESHOLD_VALUES),
        "Plan differs",
    )
    heads, bindings = verify_inputs(args, plan)
    calibration_routes(args.archive)
    files = (
        "scripts/evaluate_timely_neural.py",
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
        "schema_version": "league-timely-policy-freeze-v1",
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
        value = select_head(
            cal, saved["probabilities"][:, head["column"]], head, early, early_regions, binding
        )
        write_json(path, value)
        used += 1
        print(f"Selected {head['key']}", flush=True)
        if args.max_new_heads and used >= args.max_new_heads:
            return {"status": "paused-after-early-selection", "new_heads": used}
    policy_binding = freeze_policies(args.output, heads, binding)
    print(f"All 162 early heads frozen: {policy_binding}", flush=True)
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
            reference = None
            if not head["family"].startswith("timely_"):
                with np.load(args.warning / "later" / f"{key}.npz", allow_pickle=False) as z:
                    reference = {k: z[k] for k in z.files}
            selected = json.loads((args.output / "early" / f"{key}.json").read_bytes())
            values, checks, full = evaluate_head(
                cal, saved, head, selected, later, late_regions, reference
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
                "independent_component_checks": checks,
                "new_full_reference_checks": full,
            }
            write_json(report_path, report)
            print(f"Evaluated {key}", flush=True)
        reports[key] = report
    summary = {
        "schema_version": "league-timely-policy-summary-v1",
        "status": "complete-exploratory-timely-policy",
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
        ):
            lock = stack.enter_context((p / "experiment.lock").open("rb"))
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        print(json.dumps(run(args), indent=2))
