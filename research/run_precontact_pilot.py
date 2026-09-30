"""Frozen comparisons with calibration-only alert thresholds and paired uncertainty."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from research.objective_onset import score_alarms


def emit_alarms(ticks: np.ndarray, scores: np.ndarray, threshold: float) -> list[int]:
    alarms: list[int] = []
    for tick in ticks[scores >= threshold]:
        if not alarms or tick - alarms[-1] >= 1800:
            alarms.append(int(tick))
    return alarms


def evaluate(
    data: list[dict],
    predictions: list[np.ndarray],
    threshold: float,
    target: str = "onsets",
    delay_ticks: int = 0,
) -> list[dict]:
    results = []
    for match, scores in zip(data, predictions, strict=True):
        alarms = [t + delay_ticks for t in emit_alarms(match["ticks"], scores, threshold)]
        result = score_alarms(alarms, match[target].tolist(), min_lead=600, max_lead=1800)
        results.append(
            {"match_id": match["match_id"], "day": match["day"], "alarm_ticks": alarms, **result}
        )
    return results


def aggregate(rows: list[dict]) -> dict:
    totals = {
        key: sum(row[key] for row in rows)
        for key in ("targets", "alarms", "hits", "unmatched_alarms")
    }
    return {
        **totals,
        "matches": len(rows),
        "recall": totals["hits"] / totals["targets"] if totals["targets"] else 0.0,
        "unmatched_per_match": totals["unmatched_alarms"] / len(rows) if rows else None,
    }


def calibrate(data: list[dict], predictions: list[np.ndarray], target: str) -> tuple[float, dict]:
    scores = np.concatenate(predictions)
    # Sparse events require finer resolution near the top of the score distribution.
    # These fixed quantile levels are shared by every model, never chosen on evaluation.
    levels = np.unique(np.r_[np.linspace(0, 1, 101), 1 - np.logspace(-4, 0, 101)])
    thresholds = np.unique(np.r_[np.quantile(scores, levels), np.inf])
    best = (-1, -float("inf"), -float("inf"), -float("inf"))
    chosen, metrics = float("inf"), {}
    for threshold in thresholds:
        trial = aggregate(evaluate(data, predictions, float(threshold), target))
        if trial["unmatched_per_match"] > 1:
            continue
        key = (trial["hits"], -trial["unmatched_alarms"], -trial["alarms"], float(threshold))
        if key > best:
            best, chosen, metrics = key, float(threshold), trial
    return chosen, metrics


def paired_interval(a: list[dict], b: list[dict], *, by_day: bool = False) -> dict:
    if [r["match_id"] for r in a] != [r["match_id"] for r in b]:
        raise ValueError("Pairing differs")
    if [r["targets"] for r in a] != [r["targets"] for r in b]:
        raise ValueError("Target denominators differ")
    units = sorted({r["day"] if by_day else r["match_id"] for r in a})
    mapping = {unit: i for i, unit in enumerate(units)}
    counts = np.zeros((len(units), 3))
    for first, second in zip(a, b, strict=True):
        unit = first["day"] if by_day else first["match_id"]
        counts[mapping[unit]] += [
            first["hits"] - second["hits"],
            first["targets"],
            first["unmatched_alarms"] - second["unmatched_alarms"],
        ]
    rng = np.random.default_rng(7391)
    draws = counts[rng.integers(0, len(units), size=(2000, len(units)))].sum(axis=1)
    draws = draws[draws[:, 1] > 0]
    difference = draws[:, 0] / draws[:, 1]
    return {
        "unit": "calendar_day" if by_day else "match",
        "units": len(units),
        "replicates_with_targets": len(draws),
        "recall_difference": float(counts[:, 0].sum() / counts[:, 1].sum())
        if counts[:, 1].sum()
        else None,
        "percentile_95": np.quantile(difference, [0.025, 0.975]).tolist()
        if len(draws)
        else [None, None],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality-report", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    quality = json.loads(args.quality_report.read_text())
    splits: dict[str, list[dict]] = {"train": [], "calibration": [], "evaluation": []}
    for row in quality["matches"]:
        if row["status"] != "accepted":
            continue
        path = args.data_dir / f"{row['match_id']}.npz"
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["arrays_sha256"]:
            raise ValueError("Changed feature arrays")
        loaded = dict(np.load(path, allow_pickle=False))
        loaded.update(match_id=str(row["match_id"]), day=row["start_time"] // 86400)
        splits[row["split"]].append(loaded)
    sizes = {name: len(data) for name, data in splits.items()}
    if min(sizes.values()) < 10:
        raise ValueError(f"Too few verified matches for this pilot: {sizes}")
    train, calibration, evaluation = (
        splits[name] for name in ("train", "calibration", "evaluation")
    )
    first = next(r for r in quality["matches"] if r["status"] == "accepted")
    boundaries = first["feature_boundaries"]
    report = {
        "schema": "precontact-pilot-v1",
        "scope": "exploratory observer-data Dota pilot; no breakthrough claim",
        "quality_report_sha256": hashlib.sha256(args.quality_report.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "split_matches": sizes,
        "decision_rows": {k: sum(len(m["ticks"]) for m in v) for k, v in splits.items()},
        "target_counts": {k: sum(len(m["onsets"]) for m in v) for k, v in splits.items()},
        "seeds": [17, 29, 43],
        "models": [],
        "comparisons": [],
    }
    xtrain = np.concatenate([m["X"] for m in train])
    models = [(name, name, "onset_y", "onsets") for name in boundaries]
    models.append(("completion_trained", "coordination", "kill_y", "kills"))
    # Fit and calibrate every policy before examining any evaluation metric.
    frozen = []
    with threadpool_limits(limits=4):
        for seed in report["seeds"]:
            for name, feature_set, label, cal_target in models:
                stop = boundaries[feature_set]
                ytrain = np.concatenate([m[label] for m in train])
                if len(np.unique(ytrain)) != 2:
                    raise ValueError("Training labels need both classes")
                model = HistGradientBoostingClassifier(
                    max_iter=120,
                    max_leaf_nodes=15,
                    min_samples_leaf=30,
                    l2_regularization=1.0,
                    early_stopping=False,
                    learning_rate=0.08,
                    random_state=seed,
                )
                model.fit(xtrain[:, :stop], ytrain)
                cp = [model.predict_proba(m["X"][:, :stop])[:, 1] for m in calibration]
                threshold, cal = calibrate(calibration, cp, cal_target)
                ep = [model.predict_proba(m["X"][:, :stop])[:, 1] for m in evaluation]
                frozen.append((name, seed, threshold, cal_target, cal, ep))
                print(f"Fitted and calibrated {name} seed={seed}", flush=True)
    rows_by_model = {}
    for name, seed, threshold, cal_target, cal, prediction in frozen:
        onset = evaluate(evaluation, prediction, threshold, "onsets")
        kills = evaluate(evaluation, prediction, threshold, "kills")
        rows_by_model[name, seed] = onset
        report["models"].append(
            {
                "name": name,
                "seed": seed,
                "features": boundaries["coordination" if name == "completion_trained" else name],
                "threshold": threshold if np.isfinite(threshold) else "silence",
                "calibration_target": cal_target,
                "calibration": cal,
                "onset": aggregate(onset),
                "completion": aggregate(kills),
                "onset_with_5s_delivery_delay": aggregate(
                    evaluate(evaluation, prediction, threshold, "onsets", delay_ticks=150)
                ),
                "per_match_onset": onset,
            }
        )
    reactive = []
    reactive_completion = []
    for match in evaluation:
        result = score_alarms(
            match["reactive"].tolist(), match["onsets"].tolist(), min_lead=600, max_lead=1800
        )
        reactive.append({"match_id": match["match_id"], "day": match["day"], **result})
        reactive_completion.append(
            score_alarms(
                match["reactive"].tolist(), match["kills"].tolist(), min_lead=600, max_lead=1800
            )
        )
    report["reactive"] = {
        "onset": aggregate(reactive),
        "completion": aggregate(reactive_completion),
        "per_match": reactive,
    }
    report["silence"] = {
        "onset": aggregate(
            evaluate(evaluation, [np.zeros(len(m["ticks"])) for m in evaluation], float("inf"))
        )
    }
    for seed in report["seeds"]:
        a, b = rows_by_model["coordination", seed], rows_by_model["history", seed]
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
                "comparison": "coordination minus individual history",
                "match_bootstrap": match_ci,
                "day_bootstrap": day_ci,
                "advancement_gate": advance,
            }
        )
    report["advancement_gate_all_seeds"] = all(r["advancement_gate"] for r in report["comparisons"])
    report["seed_note"] = (
        "Full-feature deterministic boosting may yield identical seeds; "
        "repeated fits are not independent evidence."
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps({"matches": sizes, "advance": report["advancement_gate_all_seeds"]}), flush=True
    )


if __name__ == "__main__":
    main()
