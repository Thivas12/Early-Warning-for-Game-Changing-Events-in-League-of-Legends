"""Fixed full-data CPU controls for the original three-event League question.

This is a tabular history screen, not a replacement for the CUDA LeagueEWS study.
No architecture or hyperparameter is selected using later calibration.
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from itertools import pairwise
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from league_ews.alert_policy import MatchRisk
from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.metrics import probabilistic_metrics
from league_ews.notebook_policy import replay, select
from league_ews.timely_policy import compare_counts
from scripts.export_league_development import require
from scripts.league_compact_data import (
    EXPECTED_ARCHIVE,
    load_partition,
    tabular_features,
    validate_archive,
)

PLAN = {
    "schema_version": "league-three-event-tree-plan-v1",
    "status": "exploratory-development-controls-not-neural-mechanism-or-novelty",
    "seed": 20261001,
    "families": ["snapshot", "history"],
    "events": list(EVENTS),
    "target": "next-30-seconds;existing-exact-binary-target",
    "features": (
        "snapshot=27-values+27-missing;history=plus-lags-1-3-7-and-their-ages;no-cross-match-lags"
    ),
    "estimator": {
        "max_iter": 200,
        "learning_rate": 0.06,
        "max_leaf_nodes": 31,
        "min_samples_leaf": 100,
        "l2_regularization": 1.0,
        "early_stopping": False,
        "class_weight": None,
        "random_state": 20261001,
    },
    "training": "all-24000-matches;704967-rows;patches-16.12-through-16.15",
    "policy": "notebook-policy;10-to-30-second-lead;60-second-cooldown",
    "threshold_selection": (
        "earlier-1500-calibration-matches-per-region;"
        "<=1-false-plus-late-per-match-per-event-per-region"
    ),
    "evaluation": "later-1500-per-region;already-inspected-exploratory-calibration",
    "primary": (
        "history-minus-snapshot-macro-3-event-timely-recall;report-all-event-and-route-budgets"
    ),
    "test_payloads": "not-in-archive;never-requested",
}


def policy_report(data, rows, probabilities, event, horizon=30):
    early, later = _chronological_halves(rows)
    offsets = data["match_offsets"]
    ends, events = data[f"{event}_offsets"], data[f"{event}_ms"]
    matches = [
        MatchRisk(
            tuple(int(v) for v in data["times_ms"][a:b]),
            tuple(int(v) for v in events[ends[i] : ends[i + 1]]),
            tuple(float(v) for v in probabilities[a:b]),
        )
        for i, (a, b) in enumerate(pairwise(offsets))
    ]
    routes = [r["regional_route"] for r in rows]
    threshold = select([matches[i] for i in early], [routes[i] for i in early], horizon)
    overall, counts = replay([matches[i] for i in later], threshold, horizon)
    regions = {
        r: replay([matches[i] for i in later if routes[i] == r], threshold, horizon)[0]
        for r in ("europe", "americas")
    }
    return {
        "threshold": threshold,
        "later": overall,
        "by_route": regions,
        "regional_budget_met": all(v["non_timely_alerts_per_match"] <= 1 for v in regions.values()),
    }, counts


def run(archive: Path, output: Path, repo: Path):
    output.mkdir(parents=True, exist_ok=True)
    validation = validate_archive(archive, repo)
    write_json(output / "validation.json", validation)
    source = [
        repo / "scripts/run_three_event_trees.py",
        repo / "scripts/league_compact_data.py",
        *(
            repo / "src/league_ews" / p
            for p in (
                "notebook_policy.py",
                "metrics.py",
                "timely_policy.py",
                "coordination_policy.py",
            )
        ),
    ]
    frozen = {
        "plan": PLAN,
        "archive_sha256": EXPECTED_ARCHIVE,
        "source_sha256": {str(p.relative_to(repo)): sha(p) for p in source},
        "python": platform.python_version(),
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
    }
    freeze_path = output / "freeze.json"
    if freeze_path.exists():
        require(json.loads(freeze_path.read_bytes()) == frozen, "Existing tree freeze differs")
    else:
        write_json(freeze_path, frozen)
    binding = sha(freeze_path)
    train, _ = load_partition(archive, "train")
    with threadpool_limits(limits=6):
        for family in PLAN["families"]:
            x = tabular_features(train, family)
            for index, event in enumerate(EVENTS):
                path = output / f"{family}-{event}.joblib"
                meta = path.with_suffix(".json")
                if meta.exists():
                    saved = json.loads(meta.read_bytes())
                    require(
                        saved["freeze_sha256"] == binding and sha(path) == saved["model_sha256"],
                        "Existing model changed",
                    )
                    continue
                print(
                    f"Fitting {family}/{event}: {len(x):,} real training rows, "
                    f"{x.shape[1]} features",
                    flush=True,
                )
                started = time.perf_counter()
                model = HistGradientBoostingClassifier(**PLAN["estimator"])
                model.fit(x, train["targets"][:, index * 4 + 2])
                temporary = path.with_suffix(".partial")
                joblib.dump(model, temporary)
                temporary.replace(path)
                write_json(
                    meta,
                    {
                        "freeze_sha256": binding,
                        "model_sha256": sha(path),
                        "fit_seconds": time.perf_counter() - started,
                        "features": x.shape[1],
                        "training_rows": len(x),
                        "iterations": int(model.n_iter_),
                    },
                )
                print(
                    f"Completed fit {family}/{event}: {time.perf_counter() - started:.1f}s",
                    flush=True,
                )
            del x
    del train
    print(
        "All six fits completed. Scoring calibration and selecting thresholds on its early halves.",
        flush=True,
    )
    cal, rows = load_partition(archive, "calibration")
    _, later = _chronological_halves(rows)
    offsets = cal["match_offsets"]
    selected_rows = np.concatenate([np.arange(offsets[i], offsets[i + 1]) for i in later])
    reports, count_arrays = {}, {}
    with threadpool_limits(limits=6):
        for family in PLAN["families"]:
            x = tabular_features(cal, family)
            for index, event in enumerate(EVENTS):
                key = f"{family}-{event}"
                # Only trusted, locally generated models bound above are deserialized.
                model = joblib.load(output / f"{key}.joblib")
                scores = model.predict_proba(x)[:, 1]
                warning, counts = policy_report(cal, rows, scores, event)
                np.savez_compressed(
                    output / f"{key}-scores.npz",
                    probabilities=scores,
                    counts=counts,
                    match_offsets=offsets,
                )
                reports[key] = {
                    "fit": json.loads((output / f"{key}.json").read_bytes()),
                    "warnings": warning,
                    "row_metrics": probabilistic_metrics(
                        cal["targets"][selected_rows, index * 4 + 2], scores[selected_rows]
                    ),
                }
                count_arrays[key] = counts
                write_json(output / f"{key}-report.json", reports[key])
                print(
                    f"{key}: timely recall={warning['later']['timely_event_recall']:.4f}; "
                    f"regional budget={warning['regional_budget_met']}",
                    flush=True,
                )
            del x
    later_routes = [rows[i]["regional_route"] for i in later]
    comparisons = {
        e: compare_counts(count_arrays[f"history-{e}"], count_arrays[f"snapshot-{e}"], later_routes)
        for e in EVENTS
    }
    # Bootstrap all event types with the same sampled matches; preserve their dependence.
    rng = np.random.default_rng(20261001)
    groups = [np.flatnonzero(np.asarray(later_routes) == r) for r in ("europe", "americas")]
    differences = []
    for _ in range(2000):
        idx = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups])
        differences.append(
            float(
                np.mean(
                    [
                        (
                            count_arrays[f"history-{e}"][idx, 2].sum()
                            - count_arrays[f"snapshot-{e}"][idx, 2].sum()
                        )
                        / count_arrays[f"history-{e}"][idx, 0].sum()
                        for e in EVENTS
                    ]
                )
            )
        )
    summary = {
        "schema_version": "league-three-event-tree-results-v1",
        "status": "complete-exploratory-control-screen",
        "freeze_sha256": binding,
        "archive_sha256": EXPECTED_ARCHIVE,
        "models": reports,
        "history_minus_snapshot": comparisons,
        "macro_timely_recall_difference": float(
            np.mean([v["timely_recall_difference"] for v in comparisons.values()])
        ),
        "macro_conditional_95_interval": np.percentile(differences, [2.5, 97.5]).tolist(),
        "all_regional_budgets_met": all(
            v["warnings"]["regional_budget_met"] for v in reports.values()
        ),
        "bootstrap": (
            "2000 whole-match paired draws stratified by region; same draws across events; "
            "conditional on fits and thresholds"
        ),
        "interpretation": (
            "Not a hybrid or task-sharing test; not novel or confirmatory; "
            "one tree seed; secondary event intervals unadjusted"
        ),
        "test_payloads_opened": 0,
    }
    write_json(output / "summary.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/private/three-event-tree-v1"))
    args = parser.parse_args()
    result = run(args.archive, args.output, Path.cwd())
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("models", "history_minus_snapshot")},
            indent=2,
        )
    )
