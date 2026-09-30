"""Development-only nested command ablation; never loads prior evaluation data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from research.run_command_anticipation import FREEZE, QUALITY, WEIGHTS, load_data
from research.run_precontact_pilot import aggregate, calibrate, evaluate


def design(match: dict, name: str) -> np.ndarray:
    arrays = [match["X"][:, :197]]
    if name != "history":
        arrays.append(match["command_rate"])
    if name == "history_destination":
        arrays.append(match["command_destination"])
    elif name == "history_rotated":
        arrays.append(match["command_rotated"])
    return np.column_stack(arrays)


def main() -> None:
    output = Path("reports/command-history-development-2026-09-30.json")
    if output.exists():
        raise ValueError("Development result already exists; preserve it")
    previous = json.loads(FREEZE.read_text())
    for path, key in ((WEIGHTS, "weights_sha256"), (QUALITY, "quality_sha256")):
        if hashlib.sha256(path.read_bytes()).hexdigest() != previous[key]:
            raise ValueError(f"Frozen source changed: {key}")
    data = load_data(("train", "calibration"))
    train, calibration = data["train"], data["calibration"]
    original = joblib.load(WEIGHTS)["history"]
    policies = {"history": original}
    results = []
    with threadpool_limits(limits=4):
        for name in ("history", "history_rate", "history_destination", "history_rotated"):
            if name == "history":
                model = original["model"]
                threshold = original["threshold"]
                prediction = [model.predict_proba(design(m, name))[:, 1] for m in calibration]
                counts = aggregate(evaluate(calibration, prediction, threshold))
                old_counts = next(
                    r["calibration"] for r in previous["models"] if r["name"] == "history"
                )
                if counts != old_counts:
                    raise ValueError("Frozen history calibration not reproduced")
            else:
                model = HistGradientBoostingClassifier(
                    max_iter=120,
                    max_leaf_nodes=15,
                    min_samples_leaf=30,
                    l2_regularization=1.0,
                    early_stopping=False,
                    learning_rate=0.08,
                    random_state=17,
                )
                model.fit(
                    np.concatenate([design(m, name) for m in train]),
                    np.concatenate([m["onset_y"] for m in train]),
                )
                prediction = [model.predict_proba(design(m, name))[:, 1] for m in calibration]
                threshold, counts = calibrate(calibration, prediction, "onsets")
                policies[name] = {"model": model, "threshold": threshold}
            results.append(
                {
                    "name": name,
                    "features": design(train[0], name).shape[1],
                    "threshold": threshold if np.isfinite(threshold) else "silence",
                    "calibration": counts,
                }
            )
            print(name, counts, flush=True)
    primary = next(r for r in results if r["name"] == "history_destination")["calibration"]
    advances = primary["unmatched_per_match"] <= 1 and all(
        primary["hits"] >= r["calibration"]["hits"] + 3
        for r in results
        if r["name"] != "history_destination"
    )
    weights = Path("data/processed/commands/history_screen_models.joblib")
    joblib.dump(policies, weights)
    report = {
        "scope": "development only, after third-study negative result; no new evaluation",
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(
            Path("docs/command-history-development-screen.md").read_bytes()
        ).hexdigest(),
        "quality_sha256": previous["quality_sha256"],
        "weights_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
        "development_matches": {k: len(v) for k, v in data.items()},
        "models": results,
        "advances_to_new_evaluation": advances,
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print("advances_to_new_evaluation", advances, flush=True)


if __name__ == "__main__":
    main()
