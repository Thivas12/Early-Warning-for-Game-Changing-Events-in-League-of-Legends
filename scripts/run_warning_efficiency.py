"""Select all early-calibration policies before evaluating any later policy.

Reuses completed fits. No training, GPU allocation, model mutation or test access.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import platform
import time
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
from scripts.warning_efficiency import (
    BUDGETS,
    THRESHOLD_VALUES,
    expected_counts,
    replay_calibration,
    select_deterministic,
    select_mixture,
)

FAMILIES = ("leagueews", "gru", "tcn", "snapshot", "current_only", "independent", "pcgrad")
REGIONS = ("europe", "americas")
POLICIES = ("deterministic", "matched_early_mixture")


def inputs(args, plan):
    """Verify all 27 fits before reading a prediction; build 126 event/horizon heads."""
    studies = {
        name: getattr(args, name) for name in ("control", "history", "independent", "pcgrad")
    }
    summaries, bindings = {}, {}
    for name, folder in studies.items():
        summary = json.loads((folder / "summary.json").read_bytes())
        frozen = json.loads((folder / "freeze.json").read_bytes())
        require(
            summary["test_payloads_opened"] == 0 and summary["status"].startswith("complete-"),
            "Incomplete or test-using control",
        )
        require(
            sha(folder / "summary.json") == plan["studies"][name]["summary_sha256"],
            "Summary changed",
        )
        require(
            sha(folder / "freeze.json")
            == plan["studies"][name]["freeze_sha256"]
            == summary["freeze_sha256"],
            "Control freeze changed",
        )
        require(frozen["archive_sha256"] == EXPECTED_ARCHIVE, "Control archive differs")
        summaries[name] = summary
        bindings[name] = {
            "summary_sha256": sha(folder / "summary.json"),
            "freeze_sha256": sha(folder / "freeze.json"),
            "fits": {},
        }
        for key, saved in summary["models"].items():
            family, seed_text = key.split("/")
            p = folder / family / f"seed-{seed_text}"
            report = json.loads((p / "report.json").read_bytes())
            progress = json.loads((p / "progress.json").read_bytes())
            require(
                report == saved and progress["completed_units"] == 576,
                "Fit incomplete or report changed",
            )
            require(
                report["freeze_sha256"] == progress["freeze_sha256"] == summary["freeze_sha256"]
                and report["seed"] == progress["seed"] == int(seed_text),
                "Fit identity changed",
            )
            identity = "event" if name == "independent" else "family"
            require(
                report[identity] == progress[identity] == family
                and report["test_payloads_opened"] == 0,
                "Fit family or test boundary differs",
            )
            for artifact, field in (
                ("checkpoint.pt", "checkpoint_sha256"),
                ("calibration-scores.npz", "scores_sha256"),
            ):
                require(
                    sha(p / artifact) == report[field],
                    f"Changed control artifact: {name}/{key}/{artifact}",
                )
            bindings[name]["fits"][key] = {
                "report_sha256": sha(p / "report.json"),
                "checkpoint_sha256": report["checkpoint_sha256"],
                "scores_sha256": report["scores_sha256"],
            }
    heads = []
    for family in FAMILIES:
        study = (
            "control"
            if family in FAMILIES[:4]
            else {"current_only": "history", "independent": "independent", "pcgrad": "pcgrad"}[
                family
            ]
        )
        for seed in SEEDS:
            for e, event in enumerate(EVENTS):
                saved_family = (
                    event
                    if family == "independent"
                    else "leagueews"
                    if family == "current_only"
                    else family
                )
                folder = studies[study] / saved_family / f"seed-{seed}"
                report = summaries[study]["models"][f"{saved_family}/{seed}"]
                for h, c in ((30, 2), (60, 3)):
                    heads.append(
                        {
                            "key": f"{family}-{seed}-{event}-{h}",
                            "family": family,
                            "seed": seed,
                            "event": event,
                            "horizon": h,
                            "folder": folder,
                            "column": c if family == "independent" else 4 * e + c,
                            "report": report,
                        }
                    )
    require(len(heads) == 126, "Seven families and all seeds/events/horizons required")
    return heads, bindings


class ScoreCache:
    def __init__(self, cal):
        self.cal, self.path, self.saved = cal, None, None

    def get(self, head):
        path = head["folder"] / "calibration-scores.npz"
        if path != self.path:
            with np.load(path, allow_pickle=False) as loaded:
                saved = {k: loaded[k] for k in loaded.files}
            targets = self.cal["targets"]
            if head["family"] == "independent":
                e = EVENTS.index(head["event"])
                targets = targets[:, 4 * e : 4 * e + 4]
            p = saved["probabilities"]
            require(
                np.array_equal(saved["match_offsets"], self.cal["match_offsets"])
                and np.array_equal(saved["targets"], targets)
                and p.shape == targets.shape
                and np.isfinite(p).all()
                and ((p >= 0) & (p <= 1)).all(),
                "Prediction alignment or range differs",
            )
            self.path, self.saved = path, saved
        return self.saved


def select_head(cal, probabilities, head, early, regions, binding):
    counts = replay_calibration(cal, probabilities, head["event"], early, head["horizon"])
    totals = np.stack([counts[regions == r].sum(0) for r in REGIONS])
    sizes = [int((regions == r).sum()) for r in REGIONS]
    require(sizes == [1500, 1500], "Early region sizes differ")
    selected = {"deterministic": {}, "matched_early_mixture": {}}
    for budget in BUDGETS:
        selected["deterministic"][str(budget)] = select_deterministic(totals, sizes, budget)
        selected["matched_early_mixture"][str(budget)] = {
            r: select_mixture(totals[i], sizes[i], budget) for i, r in enumerate(REGIONS)
        }
    require(
        THRESHOLD_VALUES[selected["deterministic"]["1.0"]]
        == head["report"]["warnings"][f"{head['event']}_{head['horizon']}"]["threshold"],
        "Original threshold not reproduced",
    )
    return {
        "head": head["key"],
        "freeze_sha256": binding,
        "early_region_sizes": sizes,
        "early_threshold_counts_by_region": totals.tolist(),
        "policies": selected,
        "original_threshold_reproduced": True,
    }


def freeze_policies(output, heads, binding):
    digests = {}
    for head in heads:
        path = output / "early" / f"{head['key']}.json"
        require(path.exists(), "Cannot evaluate before every early policy is selected")
        data = json.loads(path.read_bytes())
        require(
            data["head"] == head["key"] and data["freeze_sha256"] == binding,
            "Early policy binding differs",
        )
        digests[head["key"]] = sha(path)
    frozen = {
        "schema_version": "league-warning-policy-freeze-v1",
        "freeze_sha256": binding,
        "policies_sha256": digests,
    }
    path = output / "policy-freeze.json"
    if path.exists():
        require(json.loads(path.read_bytes()) == frozen, "Selected policy changed")
    else:
        write_json(path, frozen)
    return sha(path)


def evaluate_head(cal, saved, head, selected, later, regions):
    indices = set(selected["policies"]["deterministic"].values())
    for per_region in selected["policies"]["matched_early_mixture"].values():
        for policy in per_region.values():
            indices.update(policy["indices"])
    ids = sorted(indices)
    thresholds = tuple(THRESHOLD_VALUES[i] for i in ids)
    probabilities = saved["probabilities"][:, head["column"]]
    counts = replay_calibration(
        cal, probabilities, head["event"], later, head["horizon"], thresholds
    )
    outputs = {k: [] for k in POLICIES}
    for budget in BUDGETS:
        i = selected["policies"]["deterministic"][str(budget)]
        outputs["deterministic"].append(counts[:, ids.index(i)].astype(np.float64))
        mixture = np.empty((len(later), 6), dtype=np.float64)
        for region in REGIONS:
            policy = selected["policies"]["matched_early_mixture"][str(budget)][region]
            mapped = {**policy, "indices": [ids.index(i) for i in policy["indices"]]}
            mixture[regions == region] = expected_counts(counts[regions == region], mapped)
        outputs["matched_early_mixture"].append(mixture)
    require(
        np.array_equal(
            outputs["deterministic"][-1], saved[f"counts_{head['event']}_{head['horizon']}"]
        ),
        "Original later counts changed",
    )
    # Independent implementation checks every component threshold on a fixed
    # early-blind subsample of later matches, in addition to full registered-count parity.
    sample = np.linspace(0, len(later) - 1, 31, dtype=int)
    for n in sample:
        i = later[n]
        a, b = cal["match_offsets"][i : i + 2]
        left, right = cal[f"{head['event']}_offsets"][i : i + 2]
        for j, threshold in enumerate(thresholds):
            expected = reference_counts(
                cal["times_ms"][a:b],
                cal[f"{head['event']}_ms"][left:right],
                probabilities[a:b],
                threshold,
                head["horizon"],
            )
            require(np.array_equal(counts[n, j], expected), "Independent component replay differs")
    return {k: np.stack(v) for k, v in outputs.items()}, len(sample) * len(ids)


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    require(
        plan["families"] == list(FAMILIES)
        and plan["budgets"] == list(BUDGETS)
        and plan["seeds"] == list(SEEDS)
        and plan["thresholds"] == list(THRESHOLD_VALUES),
        "Plan differs",
    )
    heads, bindings = inputs(args, plan)
    calibration_routes(args.archive)
    source_files = (
        "scripts/warning_efficiency.py",
        "scripts/run_warning_efficiency.py",
        "scripts/audit_neural_results.py",
        "scripts/analyse_neural_screen.py",
        "scripts/league_compact_data.py",
        "scripts/export_league_development.py",
        "src/league_ews/alert_policy.py",
        "src/league_ews/constants.py",
        "src/league_ews/notebook_experiment.py",
        "src/league_ews/coordination_experiment.py",
        "src/league_ews/m1_alert_diagnostics.py",
    )
    frozen = {
        "schema_version": "league-warning-efficiency-freeze-v1",
        "plan": plan,
        "plan_sha256": sha(args.plan),
        "studies": bindings,
        "archive_sha256": EXPECTED_ARCHIVE,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "source_sha256": {p: sha(repo / p) for p in source_files},
        "test_payloads_opened": 0,
    }
    path = args.output / "freeze.json"
    if path.exists():
        require(json.loads(path.read_bytes()) == frozen, "Freeze changed; preserve completed work")
    else:
        write_json(path, frozen)
    binding = sha(path)
    cal, rows = load_partition(args.archive, "calibration")
    early, later = _chronological_halves(rows)
    require(
        len(early) == len(later) == 3000 and not set(early) & set(later),
        "Calibration split differs",
    )
    cache = ScoreCache(cal)
    early_regions = np.array([rows[i]["regional_route"] for i in early])
    late_regions = np.array([rows[i]["regional_route"] for i in later])
    used = 0
    for head in heads:
        path = args.output / "early" / f"{head['key']}.json"
        if path.exists():
            value = json.loads(path.read_bytes())
            require(
                value["freeze_sha256"] == binding and value["head"] == head["key"],
                "Existing selection differs",
            )
            continue
        started = time.perf_counter()
        saved = cache.get(head)
        value = select_head(
            cal, saved["probabilities"][:, head["column"]], head, early, early_regions, binding
        )
        write_json(path, value)
        used += 1
        print(f"Selected {head['key']} in {time.perf_counter() - started:.2f}s", flush=True)
        if args.max_new_heads and used >= args.max_new_heads:
            return {"status": "paused-after-early-selection", "new_heads": used}
    policy_binding = freeze_policies(args.output, heads, binding)
    print(f"All 126 early policies frozen: {policy_binding}", flush=True)
    if args.early_only:
        return {"status": "all-early-policies-frozen", "policy_freeze_sha256": policy_binding}
    results = {}
    for head in heads:
        folder = args.output / "later"
        folder.mkdir(exist_ok=True)
        report_path = folder / f"{head['key']}.json"
        counts_path = folder / f"{head['key']}.npz"
        if report_path.exists():
            report = json.loads(report_path.read_bytes())
            require(
                report["freeze_sha256"] == binding
                and report["policy_freeze_sha256"] == policy_binding
                and report["head"] == head["key"]
                and report["counts_sha256"] == sha(counts_path),
                "Later artifact changed",
            )
        else:
            selected = json.loads((args.output / "early" / f"{head['key']}.json").read_bytes())
            values, checks = evaluate_head(
                cal, cache.get(head), head, selected, later, late_regions
            )
            with counts_path.with_suffix(".partial").open("wb") as stream:
                np.savez_compressed(stream, **values)
            counts_path.with_suffix(".partial").replace(counts_path)
            report = {
                "head": head["key"],
                "freeze_sha256": binding,
                "policy_freeze_sha256": policy_binding,
                "counts_sha256": sha(counts_path),
                "original_counts_reproduced": True,
                "independent_component_checks": checks,
            }
            write_json(report_path, report)
            print(f"Evaluated {head['key']}", flush=True)
        results[head["key"]] = report
    summary = {
        "schema_version": "league-warning-efficiency-summary-v1",
        "status": "complete-exploratory-warning-efficiency",
        "freeze_sha256": binding,
        "policy_freeze_sha256": policy_binding,
        "heads": results,
        "test_payloads_opened": 0,
        "new_neural_fits": 0,
    }
    write_json(args.output / "summary.json", summary)
    return {"status": summary["status"], "summary": str(args.output / "summary.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "control", "history", "independent", "pcgrad", "plan", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--max-new-heads", type=int, default=0)
    parser.add_argument("--early-only", action="store_true")
    args = parser.parse_args()
    require(args.max_new_heads >= 0, "Invalid head limit")
    args.output.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        lock = stack.enter_context((args.output / "experiment.lock").open("a+b"))
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for p in (args.control, args.history, args.independent, args.pcgrad):
            lock = stack.enter_context((p / "experiment.lock").open("rb"))
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        print(json.dumps(run(args), indent=2))
