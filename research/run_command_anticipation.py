"""Fit/freeze, then independently score the declared command-stream screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from research.run_precontact_pilot import aggregate, calibrate, evaluate, paired_interval

MODELS = (
    "clock",
    "current",
    "history",
    "coordination",
    "command_rate",
    "command_destination",
    "rotated_destination",
)
CONTROL_NAMES = MODELS[:5]
QUALITY = Path("reports/command-anticipation-quality-2026-09-30.json")
FREEZE = Path("reports/command-anticipation-freeze-2026-09-30.json")
WEIGHTS = Path("data/processed/commands/frozen_models.joblib")


def features(match: dict, name: str) -> np.ndarray:
    boundaries = {"clock": 5, "current": 77, "history": 197, "coordination": 225}
    if name in boundaries:
        return match["X"][:, : boundaries[name]]
    arrays = [match["X"][:, :77], match["command_rate"]]
    if name in ("command_destination", "rotated_destination"):
        arrays.append(
            match["command_destination" if name == "command_destination" else "command_rotated"]
        )
    return np.column_stack(arrays)


def load_data(splits: tuple[str, ...]) -> dict:
    quality = json.loads(QUALITY.read_text())
    data = {s: [] for s in splits}
    for row in quality["matches"]:
        if row["status"] != "accepted" or row["split"] not in splits:
            continue
        path = Path("data/processed/commands") / f"{row['match_id']}.npz"
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["arrays_sha256"]:
            raise ValueError("Feature file changed")
        arrays = dict(np.load(path, allow_pickle=False))
        arrays.update(
            match_id=str(row["match_id"]),
            day=row["start_time"] // 86400,
            league_id=row["league_id"],
        )
        data[row["split"]].append(arrays)
    return data


def fit() -> None:
    if FREEZE.exists() or WEIGHTS.exists():
        raise ValueError("Refusing to overwrite already frozen policies")
    data = load_data(("train", "calibration"))
    train, calibration = data["train"], data["calibration"]
    if len(train) < 20 or len(calibration) < 20:
        raise ValueError("Insufficient verified development data")
    y = np.concatenate([m["onset_y"] for m in train])
    frozen, results = {}, []
    with threadpool_limits(limits=4):
        for name in MODELS:
            model = HistGradientBoostingClassifier(
                max_iter=120,
                max_leaf_nodes=15,
                min_samples_leaf=30,
                l2_regularization=1.0,
                early_stopping=False,
                learning_rate=0.08,
                random_state=17,
            )
            x = np.concatenate([features(m, name) for m in train])
            model.fit(x, y)
            prediction = [model.predict_proba(features(m, name))[:, 1] for m in calibration]
            threshold, cal = calibrate(calibration, prediction, "onsets")
            frozen[name] = {"model": model, "threshold": threshold}
            results.append(
                {
                    "name": name,
                    "features": x.shape[1],
                    "threshold": threshold if np.isfinite(threshold) else "silence",
                    "calibration": cal,
                }
            )
            print("Frozen", name, "calibration", cal, flush=True)
    controls = [r for r in results if r["name"] in CONTROL_NAMES]
    comparator = min(
        controls,
        key=lambda r: (
            -r["calibration"]["hits"],
            r["calibration"]["unmatched_alarms"],
            r["calibration"]["alarms"],
            r["name"],
        ),
    )["name"]
    reproduced = None
    if len(train) == 110 and len(calibration) == 37:
        previous = json.loads(Path("reports/precontact-pilot-2026-09-30.json").read_text())
        reproduced = {}
        for result in results[:4]:
            old = next(
                r for r in previous["models"] if r["name"] == result["name"] and r["seed"] == 17
            )
            reproduced[result["name"]] = (
                old["threshold"] == result["threshold"]
                and old["calibration"] == result["calibration"]
            )
        if not all(reproduced.values()):
            raise ValueError(f"Original control policies changed: {reproduced}")
    joblib.dump(frozen, WEIGHTS)
    report = {
        "schema": "command-anticipation-freeze-v1",
        "seed": 17,
        "quality_sha256": hashlib.sha256(QUALITY.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(
            Path("docs/command-anticipation-protocol.md").read_bytes()
        ).hexdigest(),
        "weights_sha256": hashlib.sha256(WEIGHTS.read_bytes()).hexdigest(),
        "development_matches": {k: len(v) for k, v in data.items()},
        "original_controls_reproduced": reproduced,
        "selected_comparator": comparator,
        "models": results,
    }
    FREEZE.write_text(json.dumps(report, indent=2) + "\n")


def score() -> None:
    report = json.loads(FREEZE.read_text())
    for key, path in (
        ("quality_sha256", QUALITY),
        ("weights_sha256", WEIGHTS),
        ("runner_sha256", Path(__file__)),
        ("protocol_sha256", Path("docs/command-anticipation-protocol.md")),
    ):
        if hashlib.sha256(path.read_bytes()).hexdigest() != report[key]:
            raise ValueError(f"Frozen input changed: {key}")
    # Load only a locally generated, hash-verified model artifact.
    frozen = joblib.load(WEIGHTS)
    data = load_data(("evaluation",))["evaluation"]
    if len(data) < 20:
        raise ValueError("Too few verified fresh matches")
    report.update(
        schema="command-anticipation-results-v1",
        scope="exploratory third public-data screen; no breakthrough claim",
        fresh_matches=len(data),
        fresh_targets=sum(len(m["onsets"]) for m in data),
        fresh_decision_rows=sum(len(m["ticks"]) for m in data),
        league_counts={
            str(k): sum(m["league_id"] == k for m in data)
            for k in sorted({m["league_id"] for m in data})
        },
    )
    rows = {}
    with threadpool_limits(limits=4):
        for result in report["models"]:
            name = result["name"]
            model, threshold = frozen[name]["model"], frozen[name]["threshold"]
            predictions = [model.predict_proba(features(m, name))[:, 1] for m in data]
            rows[name] = evaluate(data, predictions, threshold)
            result.update(
                onset=aggregate(rows[name]),
                per_match_onset=rows[name],
                onset_with_5s_delivery_delay=aggregate(
                    evaluate(data, predictions, threshold, delay_ticks=150)
                ),
            )
            print(name, result["onset"], flush=True)
    primary = "command_destination"
    comparisons = []
    for comparator in (report["selected_comparator"], "rotated_destination"):
        match_ci = paired_interval(rows[primary], rows[comparator])
        day_ci = paired_interval(rows[primary], rows[comparator], by_day=True)
        advance = (
            aggregate(rows[primary])["unmatched_per_match"] <= 1
            and match_ci["percentile_95"][0] is not None
            and match_ci["percentile_95"][0] > 0
            and day_ci["percentile_95"][0] > 0
        )
        comparisons.append(
            {
                "candidate": primary,
                "comparator": comparator,
                "match_interval": match_ci,
                "day_interval": day_ci,
                "passes": advance,
            }
        )
    report["comparisons"] = comparisons
    report["screen_advances"] = all(c["passes"] for c in comparisons)
    Path("reports/command-anticipation-results-2026-09-30.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print("screen_advances", report["screen_advances"], flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("fit", "score"))
    args = parser.parse_args()
    fit() if args.stage == "fit" else score()


if __name__ == "__main__":
    main()
