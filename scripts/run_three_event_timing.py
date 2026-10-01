"""Follow-up after the history screen: align three targets with useful lead time.

Known objective-alignment control, not a new algorithm or a neural transfer test.
The earlier screen and its failed advancement gate remain immutable.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.metrics import probabilistic_metrics
from league_ews.timely_policy import compare_counts
from scripts.export_league_development import require
from scripts.league_compact_data import (
    EXPECTED_ARCHIVE,
    load_partition,
    tabular_features,
    validate_archive,
)
from scripts.run_three_event_trees import PLAN as CONTROL_PLAN
from scripts.run_three_event_trees import policy_report

PLAN = {
    "schema_version": "league-three-event-timing-plan-v1",
    "status": "adaptive-exploratory-control-follow-up",
    "reason": "History screen macro gain is null; test whether within-30 target rewards late alerts",
    "estimator": CONTROL_PLAN["estimator"],
    "features": "same-history-219-as-fixed-tree-control",
    "targets": "next-strictly-future-event;closed-10-through-30-second-interval",
    "events": list(EVENTS),
    "fits": 3,
    "policy": CONTROL_PLAN["policy"],
    "threshold_selection": CONTROL_PLAN["threshold_selection"],
    "primary": "timely-target-minus-within30-history;macro-three-event-timely-recall",
    "claim_limit": "Objective alignment is established prior work; no novelty claim",
}


def timely_targets(data, event):
    target = np.zeros(len(data["times_ms"]), dtype=np.int8)
    offsets, eo = data["match_offsets"], data[f"{event}_offsets"]
    for i, (a, b) in enumerate(zip(offsets[:-1], offsets[1:], strict=True)):
        times = data["times_ms"][a:b]
        events = data[f"{event}_ms"][eo[i] : eo[i + 1]]
        next_index = np.searchsorted(events, times, side="right")
        present = next_index < len(events)
        delay = np.full(len(times), np.iinfo(np.int64).max, dtype=np.int64)
        delay[present] = events[next_index[present]] - times[present]
        target[a:b] = (delay >= 10000) & (delay <= 30000)
    return target


def run(archive, control, output, repo):
    validate_archive(archive, repo)
    baseline = json.loads((control / "summary.json").read_bytes())
    require(baseline["archive_sha256"] == EXPECTED_ARCHIVE, "Wrong control data")
    require(baseline["freeze_sha256"] == sha(control / "freeze.json"), "Control freeze changed")
    output.mkdir(parents=True, exist_ok=True)
    frozen = {
        "plan": PLAN,
        "archive_sha256": EXPECTED_ARCHIVE,
        "control_summary_sha256": sha(control / "summary.json"),
        "source_sha256": {
            p: sha(repo / p)
            for p in (
                "scripts/run_three_event_timing.py",
                "scripts/run_three_event_trees.py",
                "scripts/league_compact_data.py",
                "src/league_ews/notebook_policy.py",
            )
        },
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
    }
    path = output / "freeze.json"
    if path.exists():
        require(json.loads(path.read_bytes()) == frozen, "Timing freeze changed")
    else:
        write_json(path, frozen)
    binding = sha(path)
    train, _ = load_partition(archive, "train")
    x = tabular_features(train, "history")
    with threadpool_limits(limits=6):
        for event in EVENTS:
            path = output / f"{event}.joblib"
            meta = output / f"{event}-fit.json"
            if meta.exists():
                saved = json.loads(meta.read_bytes())
                require(
                    saved["freeze_sha256"] == binding and saved["model_sha256"] == sha(path),
                    "Fit changed",
                )
                continue
            started = time.perf_counter()
            print(f"Fitting timely 10–30s/{event} on all {len(x):,} training rows", flush=True)
            model = HistGradientBoostingClassifier(**PLAN["estimator"])
            model.fit(x, timely_targets(train, event))
            temporary = path.with_suffix(".partial")
            joblib.dump(model, temporary)
            temporary.replace(path)
            write_json(
                meta,
                {
                    "freeze_sha256": binding,
                    "model_sha256": sha(path),
                    "fit_seconds": time.perf_counter() - started,
                },
            )
            print(f"Completed {event}: {time.perf_counter() - started:.1f}s", flush=True)
    del train, x
    cal, rows = load_partition(archive, "calibration")
    x = tabular_features(cal, "history")
    _, later = _chronological_halves(rows)
    offsets = cal["match_offsets"]
    row_indices = np.concatenate([np.arange(offsets[i], offsets[i + 1]) for i in later])
    routes = [rows[i]["regional_route"] for i in later]
    reports, counts, differences, controls = {}, {}, {}, {}
    with threadpool_limits(limits=6):
        for event in EVENTS:
            scores = joblib.load(output / f"{event}.joblib").predict_proba(x)[:, 1]
            warnings, values = policy_report(cal, rows, scores, event)
            np.savez_compressed(
                output / f"{event}-scores.npz",
                probabilities=scores,
                counts=values,
                match_offsets=offsets,
            )
            counts[event] = values
            with np.load(control / f"history-{event}-scores.npz", allow_pickle=False) as original:
                controls[event] = original["counts"].copy()
            differences[event] = compare_counts(values, controls[event], routes)
            reports[event] = {
                "warnings": warnings,
                "row_metrics_on_timely_target": probabilistic_metrics(
                    timely_targets(cal, event)[row_indices], scores[row_indices]
                ),
            }
            print(
                f"{event}: recall {warnings['later']['timely_event_recall']:.4f}; budget {warnings['regional_budget_met']}",
                flush=True,
            )
    rng = np.random.default_rng(20261001)
    groups = [np.flatnonzero(np.asarray(routes) == r) for r in ("europe", "americas")]
    draws = []
    for _ in range(2000):
        idx = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups])
        draws.append(
            float(
                np.mean(
                    [
                        (counts[e][idx, 2].sum() - controls[e][idx, 2].sum())
                        / counts[e][idx, 0].sum()
                        for e in EVENTS
                    ]
                )
            )
        )
    summary = {
        "schema_version": "league-three-event-timing-results-v1",
        "status": "complete-exploratory-target-control",
        "freeze_sha256": binding,
        "archive_sha256": EXPECTED_ARCHIVE,
        "models": reports,
        "timely_minus_within30_history": differences,
        "macro_timely_recall_difference": float(
            np.mean([r["timely_recall_difference"] for r in differences.values()])
        ),
        "macro_conditional_95_interval": np.percentile(draws, [2.5, 97.5]).tolist(),
        "both_families_all_regional_budgets_met": all(
            reports[e]["warnings"]["regional_budget_met"]
            and baseline["models"][f"history-{e}"]["warnings"]["regional_budget_met"]
            for e in EVENTS
        ),
        "interpretation": "Adaptive development study; known objective alignment; not novelty or confirmation; one tree seed",
        "test_payloads_opened": 0,
    }
    write_json(output / "summary.json", summary)
    print(
        json.dumps(
            {
                k: v
                for k, v in summary.items()
                if k not in ("models", "timely_minus_within30_history")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--control", type=Path, default=Path("data/private/three-event-tree-v1"))
    parser.add_argument("--output", type=Path, default=Path("data/private/three-event-timing-v1"))
    args = parser.parse_args()
    run(args.archive, args.control, args.output, Path.cwd())
