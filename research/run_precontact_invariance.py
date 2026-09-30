"""Fresh-cohort comparison of fixed original models and invariant feature ablations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from research.objective_onset import score_alarms
from research.run_precontact_pilot import aggregate, calibrate, evaluate, paired_interval


def invariant_features(x: np.ndarray, *, motion: bool) -> np.ndarray:
    """Remove map origin, player ordering, and team ordering from archived features."""
    if x.ndim != 2 or x.shape[1] != 225:
        raise ValueError("Expected the frozen 225-column feature schema")
    player = x[:, 5:65].reshape(-1, 2, 5, 6)
    # Four entity-local values: health fraction, mana fraction, level, alive.
    state = player[:, :, :, 2:6]
    summary = np.concatenate((state.min(2), state.mean(2), state.max(2)), axis=2)
    geometry = x[:, 197:225].reshape(-1, 2, 14)
    keep = list(range(14)) if motion else [0, 1, 2, 3, 4, 5, 6, 7, 8, 12]
    teams = np.concatenate((geometry[:, :, keep], summary), axis=2)
    key_order = [4] + [i for i in range(teams.shape[2]) if i != 4]
    keys = np.nan_to_num(teams[:, :, key_order], nan=np.inf)
    equal = np.ones(len(x), dtype=bool)
    swap = np.zeros(len(x), dtype=bool)
    for i in range(keys.shape[2]):
        swap |= equal & (keys[:, 0, i] > keys[:, 1, i])
        equal &= keys[:, 0, i] == keys[:, 1, i]
    ordered = np.where(swap[:, None, None], teams[:, ::-1], teams)
    return np.column_stack((x[:, :5], ordered.reshape(len(x), -1)))


def load_rows(report: dict, folder: Path, keep_splits: set[str]) -> list[dict]:
    loaded = []
    for row in report["matches"]:
        if row["status"] != "accepted" or row["split"] not in keep_splits:
            continue
        path = folder / f"{row['match_id']}.npz"
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["arrays_sha256"]:
            raise ValueError("Feature archive SHA256 mismatch")
        match = dict(np.load(path, allow_pickle=False))
        match.update(
            match_id=str(row["match_id"]), day=row["start_time"] // 86400, split=row["split"]
        )
        loaded.append(match)
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-quality", type=Path, required=True)
    parser.add_argument("--fresh-quality", type=Path, required=True)
    parser.add_argument("--original-results", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original_quality = json.loads(args.original_quality.read_text())
    fresh_quality = json.loads(args.fresh_quality.read_text())
    previous = json.loads(args.original_results.read_text())
    if {r["match_id"] for r in original_quality["matches"]} & {
        r["match_id"] for r in fresh_quality["matches"]
    }:
        raise ValueError("Fresh cohort overlaps original cohort")
    old = load_rows(original_quality, args.data_dir, {"train", "calibration"})
    train, calibration = (
        [m for m in old if m["split"] == split] for split in ("train", "calibration")
    )
    fresh = load_rows(fresh_quality, args.data_dir, {"evaluation"})
    if len(fresh) < 20:
        raise ValueError("Fewer than 20 quality-verified fresh matches")
    report = {
        "schema": "precontact-invariance-v1",
        "scope": "Follow-up developed after initial negative results; disjoint fresh evaluation",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_results_sha256": hashlib.sha256(args.original_results.read_bytes()).hexdigest(),
        "fresh_quality_sha256": hashlib.sha256(args.fresh_quality.read_bytes()).hexdigest(),
        "split_matches": {
            "train": len(train),
            "calibration": len(calibration),
            "fresh_evaluation": len(fresh),
        },
        "fresh_targets": sum(len(m["onsets"]) for m in fresh),
        "fresh_decisions": sum(len(m["ticks"]) for m in fresh),
        "models": [],
        "comparisons": [],
    }
    boundaries = {
        "clock": 5,
        "current": 77,
        "history": 197,
        "coordination": 225,
        "completion_trained": 225,
    }
    names = [*boundaries, "invariant_current", "invariant_motion"]

    def transform(x, name):
        if name in boundaries:
            return x[:, : boundaries[name]]
        return invariant_features(x, motion=name == "invariant_motion")

    train_x = np.concatenate([m["X"] for m in train])
    frozen = []
    selected_comparator = {}
    with threadpool_limits(limits=4):
        for seed in (17, 29, 43):
            selection = []
            for name in names:
                is_completion = name == "completion_trained"
                label, target = ("kill_y", "kills") if is_completion else ("onset_y", "onsets")
                x, y = transform(train_x, name), np.concatenate([m[label] for m in train])
                model = HistGradientBoostingClassifier(
                    max_iter=120,
                    max_leaf_nodes=15,
                    min_samples_leaf=30,
                    l2_regularization=1.0,
                    early_stopping=False,
                    learning_rate=0.08,
                    random_state=seed,
                )
                model.fit(x, y)
                cp = [model.predict_proba(transform(m["X"], name))[:, 1] for m in calibration]
                threshold, cal_target = calibrate(calibration, cp, target)
                cal_onset = aggregate(evaluate(calibration, cp, threshold, "onsets"))
                verified = None
                if name in boundaries:
                    original = next(
                        m for m in previous["models"] if m["name"] == name and m["seed"] == seed
                    )
                    encoded = threshold if np.isfinite(threshold) else "silence"
                    if encoded != original["threshold"] or cal_target != original["calibration"]:
                        raise ValueError(f"Original policy refit changed: {name} seed {seed}")
                    verified = True
                if name != "invariant_motion":
                    selection.append(
                        (
                            -cal_onset["hits"],
                            cal_onset["unmatched_alarms"],
                            cal_onset["alarms"],
                            name,
                        )
                    )
                ep = [model.predict_proba(transform(m["X"], name))[:, 1] for m in fresh]
                frozen.append(
                    (name, seed, x.shape[1], threshold, cal_target, cal_onset, verified, ep)
                )
                print(f"Frozen {name} seed={seed}", flush=True)
            selected_comparator[seed] = min(selection)[-1]
    # No evaluation scores are computed until every threshold and comparator is fixed.
    results = {}
    for name, seed, width, threshold, cal_target, cal_onset, verified, prediction in frozen:
        onset = evaluate(fresh, prediction, threshold, "onsets")
        results[name, seed] = onset
        report["models"].append(
            {
                "name": name,
                "seed": seed,
                "features": width,
                "threshold": threshold if np.isfinite(threshold) else "silence",
                "original_calibration_exactly_reproduced": verified,
                "calibration": cal_target,
                "calibration_onset": cal_onset,
                "onset": aggregate(onset),
                "completion": aggregate(evaluate(fresh, prediction, threshold, "kills")),
                "onset_with_5s_delivery_delay": aggregate(
                    evaluate(fresh, prediction, threshold, "onsets", delay_ticks=150)
                ),
                "per_match_onset": onset,
            }
        )
    for seed in (17, 29, 43):
        comparator = selected_comparator[seed]
        a, b = results["invariant_motion", seed], results[comparator, seed]
        match_ci, day_ci = paired_interval(a, b), paired_interval(a, b, by_day=True)
        advance = (
            aggregate(a)["unmatched_per_match"] <= 1
            and match_ci["percentile_95"][0] is not None
            and match_ci["percentile_95"][0] > 0
            and day_ci["percentile_95"][0] > 0
        )
        report["comparisons"].append(
            {
                "seed": seed,
                "calibration_selected_comparator": comparator,
                "match_bootstrap": match_ci,
                "day_bootstrap": day_ci,
                "advancement_gate": advance,
            }
        )
    reactive = {}
    for target in ("onsets", "kills"):
        rows = [
            score_alarms(m["reactive"].tolist(), m[target].tolist(), min_lead=600, max_lead=1800)
            for m in fresh
        ]
        reactive[target] = aggregate(rows)
    report["reactive"] = reactive
    report["advancement_gate_all_seeds"] = all(c["advancement_gate"] for c in report["comparisons"])
    report["seed_note"] = previous["seed_note"]
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps({"fresh_matches": len(fresh), "advance": report["advancement_gate_all_seeds"]}),
        flush=True,
    )


if __name__ == "__main__":
    main()
