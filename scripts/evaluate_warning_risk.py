"""Frozen capped-warning risk diagnostic using completed League scores only."""

from __future__ import annotations

import argparse
import fcntl
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from scripts.analyse_neural_screen import calibration_routes
from scripts.evaluate_dense_policy import GRID
from scripts.evaluate_dense_policy import select as select_dense
from scripts.evaluate_matched_optimization import ScoreCache, freeze_policies, verify_inputs
from scripts.export_league_development import require
from scripts.league_compact_data import load_partition
from scripts.scoring_release import committed_sources
from scripts.warning_efficiency import BUDGETS, replay_thresholds
from scripts.warning_risk import (
    CAP,
    DELTA,
    FAMILIES,
    POLICIES,
    REGIONAL_SEQUENCES,
    REGIONS,
    calibration_inputs,
    reference_capped,
    replay_capped,
    select_capped,
)


def previous_args(data_root, control_root, repo):
    """Resolve the unchanged provenance chain; no test payload path is constructed."""
    base = data_root / "data/private"
    paths = {
        "history": "league-history-ablation-v1",
        "independent": "league-task-sharing-v1",
        "pcgrad": "league-pcgrad-v1",
        "study": "league-timely-neural-v1",
        "inputs": "league-timely-inputs-v1",
        "warning": "league-warning-efficiency-v1",
        "reference": "league-timely-policy-v1",
        "dense": "league-dense-policy-v1",
        "previous": "league-timely-input-policy-v1",
        "new_study": "league-clock-history-v1",
        "latest": "league-clock-history-policy-v1",
        "independent_study": "league-timely-sharing-v1",
        "sharing_policy": "league-timely-sharing-policy-v1",
        "optimization_study": "league-timely-optimization-v1",
        "optimization_policy": "league-timely-optimization-policy-v1",
        "matched_study": "league-matched-optimization-v1",
    }
    plans = {
        "control_plan": "timely-neural-2026-10-03",
        "input_plan": "timely-inputs-2026-10-04",
        "clock_plan": "clock-history-2026-10-04",
        "sharing_plan": "timely-sharing-2026-10-05",
        "optimization_plan": "timely-optimization-2026-10-05",
        "plan": "matched-optimization-2026-10-06",
    }
    return SimpleNamespace(
        **{k: base / v for k, v in paths.items()},
        **{k: repo / "reports" / v / "plan.json" for k, v in plans.items()},
        archive=base / "league-three-event-export-v1/development.zip",
        control=control_root / "data/private/compact-notebook-v1",
    )


def validate_plan(plan):
    require(
        plan["schema_version"] == "league-warning-risk-plan-v1"
        and plan["families"] == list(FAMILIES)
        and plan["policies"] == list(POLICIES)
        and plan["thresholds"] == list(GRID)
        and plan["budgets"] == list(BUDGETS)
        and plan["cap"] == CAP
        and plan["delta"] == DELTA
        and plan["regional_sequences"] == REGIONAL_SEQUENCES
        and plan["uncertainty"] == {"draws": 2000, "seed": 20261001}
        and plan["new_neural_fits"] == 0,
        "Risk plan differs",
    )


def select_head(cal, scores, head, early, regions, binding, prior):
    inputs = calibration_inputs(cal, scores, head["event"], early)
    uncapped = replay_thresholds(*inputs, GRID, head["horizon"])
    counts = replay_capped(*inputs, GRID, head["horizon"])
    require(np.array_equal(counts[..., 3], np.minimum(uncapped[..., 3], CAP)), "Cap lost prefix")
    require(np.array_equal(counts[..., [0, 5]], uncapped[..., [0, 5]]), "Denominators differ")
    original_totals = np.stack([uncapped[regions == r].sum(0) for r in REGIONS])
    totals = np.stack([counts[regions == r].sum(0) for r in REGIONS])
    sizes = [int((regions == r).sum()) for r in REGIONS]
    require(sizes == [1500, 1500], "Early regions differ")
    require(
        np.array_equal(original_totals, prior["early_threshold_counts_by_region"]),
        "Previous early replay differs",
    )
    policies = {p: {} for p in POLICIES}
    diagnostics = {}
    for budget in BUDGETS:
        label = str(budget)
        original = select_dense(original_totals, sizes, budget)
        require(original == prior["policies"]["dense_deterministic"][label], "Prior policy differs")
        policies["uncapped_empirical"][label] = original
        selected = select_capped(totals, sizes, budget)
        diagnostics[label] = selected
        for policy, idx in selected["indices"].items():
            policies[policy][label] = idx
    return {
        "head": head["key"],
        "freeze_sha256": binding,
        "policies": policies,
        "early_region_sizes": sizes,
        "early_threshold_counts_by_region": totals.tolist(),
        "screening": diagnostics,
        "cap_truncated_matches_by_region_threshold": [
            (uncapped[regions == r, :, 3] > CAP).sum(0).tolist() for r in REGIONS
        ],
        "previous_policy_sha256": prior["freeze_sha256"],
    }


def evaluate_head(cal, scores, head, selected, later, regions, previous):
    policies = selected["policies"]
    ids = sorted({i for choices in policies.values() for i in choices.values()})
    thresholds = tuple(GRID[i] for i in ids)
    inputs = calibration_inputs(cal, scores, head["event"], later)
    counts = replay_capped(*inputs, thresholds, head["horizon"])
    uncapped = replay_thresholds(*inputs, thresholds, head["horizon"])
    require(np.array_equal(counts[..., 3], np.minimum(uncapped[..., 3], CAP)), "Cap lost prefix")
    require(np.array_equal(counts[..., [0, 5]], uncapped[..., [0, 5]]), "Denominators differ")
    values, cap_activity = {}, {}
    for policy in POLICIES:
        source = uncapped if policy == "uncapped_empirical" else counts
        indices = [ids.index(policies[policy][str(b)]) for b in BUDGETS]
        values[policy] = np.stack([source[:, i] for i in indices])
        cap_activity[policy] = {
            str(b): {r: int((uncapped[regions == r, i, 3] > CAP).sum()) for r in REGIONS}
            for b, i in zip(BUDGETS, indices, strict=True)
        }
    require(
        np.array_equal(values["uncapped_empirical"], previous["dense_deterministic"]),
        "Previous later match counts differ",
    )
    full_checks, sample_checks = 0, 0
    # Count all three policy checks, even where two policies share a threshold.
    for policy in POLICIES[1:]:
        threshold = GRID[policies[policy]["1.0"]]
        for n, (t, e, s) in enumerate(zip(*inputs, strict=True)):
            want = reference_capped(t, e, s, threshold, head["horizon"])
            require(np.array_equal(values[policy][-1, n], want), "Full capped replay differs")
            full_checks += 1
    for n in np.linspace(0, len(later) - 1, min(31, len(later)), dtype=int):
        for j, threshold in enumerate(thresholds):
            want = reference_capped(*(v[n] for v in inputs), threshold, head["horizon"])
            require(np.array_equal(counts[n, j], want), "Component capped replay differs")
            sample_checks += 1
    return values, full_checks, sample_checks, cap_activity


def bind_release(output, binding, commit, sources):
    path = output / "analysis-release.json"
    expected = {"analysis_commit": commit, "source_sha256": sources, "freeze_sha256": binding}
    if path.exists():
        saved = json.loads(path.read_bytes())
        require(all(saved[k] == v for k, v in expected.items()), "Analysis release changed")
    else:
        require(
            not list((output / "early").glob("*.json")) and not list((output / "later").glob("*")),
            "Cannot backfill a policy analysis release",
        )
        saved = {**expected, "recorded_at_utc": datetime.now(UTC).isoformat()}
        with path.open("x") as stream:
            json.dump(saved, stream, indent=2)
            stream.write("\n")
    return sha(path)


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    validate_plan(plan)
    plan_name = args.plan.resolve().relative_to(repo).as_posix()
    commit, sources = committed_sources(repo, args.analysis_commit, [*plan["sources"], plan_name])
    old_args = previous_args(args.data_root, args.control_root, repo)
    require(sha(old_args.plan) == plan["reference_plan_sha256"], "Reference plan differs")
    heads, bindings = verify_inputs(old_args, json.loads(old_args.plan.read_bytes()))
    previous = args.data_root / "data/private/league-matched-optimization-policy-v1"
    summary = json.loads((previous / "summary.json").read_bytes())
    frozen = json.loads((previous / "freeze.json").read_bytes())
    require(
        sha(previous / "summary.json") == plan["previous_summary_sha256"]
        and sha(previous / "freeze.json") == summary["freeze_sha256"]
        and summary["status"] == "complete-exploratory-matched-optimization-policy"
        and summary["test_payloads_opened"] == 0
        and set(summary["heads"]) == {h["key"] for h in heads}
        and all(sha(repo / name) == value for name, value in frozen["source_sha256"].items()),
        "Previous matched policy changed",
    )
    require(
        freeze_policies(previous, heads, summary["freeze_sha256"])
        == summary["policy_freeze_sha256"],
        "Previous early policy binding differs",
    )
    for key, report in summary["heads"].items():
        require(
            sha(previous / "later" / f"{key}.npz") == report["counts_sha256"],
            "Prior counts changed",
        )
    heads = [h for h in heads if h["family"] in FAMILIES]
    require(len(heads) == 90, "Risk head inventory differs")
    study = {
        "schema_version": "league-warning-risk-freeze-v1",
        "plan": plan,
        "plan_sha256": sha(args.plan),
        "source_sha256": sources,
        "analysis_commit": commit,
        "studies": bindings,
        "previous_summary_sha256": sha(previous / "summary.json"),
        "archive_sha256": sha(old_args.archive),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "test_payloads_opened": 0,
    }
    path = args.output / "freeze.json"
    if path.exists():
        require(json.loads(path.read_bytes()) == study, "Frozen risk study differs")
    else:
        write_json(path, study)
    binding = sha(path)
    release = bind_release(args.output, binding, commit, sources)
    calibration_routes(old_args.archive)
    cal, rows = load_partition(old_args.archive, "calibration")
    early, later = _chronological_halves(rows)
    require(len(early) == len(later) == 3000 and not set(early) & set(later), "Split differs")
    early_regions = np.array([rows[i]["regional_route"] for i in early])
    later_regions = np.array([rows[i]["regional_route"] for i in later])
    require(
        [int((later_regions == r).sum()) for r in REGIONS] == [1500, 1500], "Later regions differ"
    )
    cache = ScoreCache(cal)
    for head in heads:
        path = args.output / "early" / f"{head['key']}.json"
        if path.exists():
            saved = json.loads(path.read_bytes())
            require(
                saved["head"] == head["key"] and saved["freeze_sha256"] == binding,
                "Early binding differs",
            )
        else:
            require(not list((args.output / "later").glob("*")), "Cannot select after later replay")
            scores = cache.get(head)["probabilities"][:, head["column"]]
            prior = json.loads((previous / "early" / f"{head['key']}.json").read_bytes())
            write_json(path, select_head(cal, scores, head, early, early_regions, binding, prior))
            print(f"Selected {head['key']}", flush=True)
    policy_binding = freeze_policies(args.output, heads, binding)
    gate_path = args.output / "early-gate.json"
    if not gate_path.exists():
        require(
            not list((args.output / "later").glob("*")), "Early gate cannot follow later replay"
        )
        write_json(
            gate_path,
            {
                "recorded_at_utc": datetime.now(UTC).isoformat(),
                "early_heads": 90,
                "later_heads": 0,
                "policy_freeze_sha256": policy_binding,
                "analysis_release_sha256": release,
            },
        )
    gate = json.loads(gate_path.read_bytes())
    require(
        gate["policy_freeze_sha256"] == policy_binding
        and gate["analysis_release_sha256"] == release,
        "Early gate differs",
    )
    if args.early_only:
        return {"status": "all-90-early-heads-frozen", "policy_freeze_sha256": policy_binding}
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
                and report["policy_freeze_sha256"] == policy_binding
                and report["counts_sha256"] == sha(arrays),
                "Later binding differs",
            )
        else:
            scores = cache.get(head)["probabilities"][:, head["column"]]
            selected = json.loads((args.output / "early" / f"{key}.json").read_bytes())
            with np.load(previous / "later" / f"{key}.npz", allow_pickle=False) as prior:
                values, full, sample, activity = evaluate_head(
                    cal, scores, head, selected, later, later_regions, prior
                )
            arrays.parent.mkdir(parents=True, exist_ok=True)
            with arrays.with_suffix(".partial").open("wb") as stream:
                np.savez_compressed(stream, **values)
            arrays.with_suffix(".partial").replace(arrays)
            report = {
                "head": key,
                "freeze_sha256": binding,
                "policy_freeze_sha256": policy_binding,
                "counts_sha256": sha(arrays),
                "full_reference_checks": full,
                "component_reference_checks": sample,
                "previous_counts_reproduced": True,
                "cap_truncated_matches": activity,
            }
            write_json(path, report)
            print(f"Evaluated {key}", flush=True)
        reports[key] = report
    value = {
        "schema_version": "league-warning-risk-summary-v1",
        "status": "complete-exploratory-warning-risk",
        "freeze_sha256": binding,
        "policy_freeze_sha256": policy_binding,
        "analysis_release_sha256": release,
        "early_gate_sha256": sha(gate_path),
        "heads": reports,
        "new_neural_fits": 0,
        "total_completed_neural_fits": 69,
        "test_payloads_opened": 0,
    }
    write_json(args.output / "summary.json", value)
    return {"status": value["status"], "summary": str(args.output / "summary.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("data-root", "control-root", "plan", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--analysis-commit", required=True)
    parser.add_argument("--early-only", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "experiment.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(json.dumps(run(args), indent=2))
