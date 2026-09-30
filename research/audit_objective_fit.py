"""Post-fit development diagnostic; never selects or changes a model or policy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from research.public_objective_training import emitted, inputs, network, normalize, write_report
from research.run_precontact_pilot import aggregate, evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expanded", action="store_true")
    parser.add_argument("--shared", action="store_true")
    args = parser.parse_args()
    torch.set_num_threads(4)
    size = "expanded" if args.expanded else "small"
    stem = "shared-threshold" if args.shared else "objective-training"
    report_path = Path(f"reports/{stem}-{size}-2026-09-30.json")
    report = json.loads(report_path.read_text())
    if (
        len(report["models"]) != (3 if args.shared else 21)
        or "advances_to_new_evaluation" not in report
    ):
        raise ValueError("Run this diagnostic only after all fits finish")
    data, bindings = inputs(args.expanded)
    freeze = json.loads(
        Path(f"reports/objective-training-{size}-freeze-2026-09-30.json").read_text()
    )
    if bindings != freeze["data_bindings"]:
        raise ValueError("Diagnostic data differ from the original experiment")
    if args.shared:
        from research.shared_threshold import shared_threshold_counts
    result = {
        "scope": "post-fit descriptive train/calibration audit; no policy changes",
        "model_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "models": [],
    }
    for record in report["models"]:
        filename = "shared-threshold" if args.shared else record["loss"]
        path = Path(f"data/processed/{stem}-{size}") / f"{filename}-{record['seed']}.pt"
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["weights_sha256"]:
            raise ValueError("Saved model changed")
        checkpoint = torch.load(path, weights_only=True)
        net = network(0.5)
        net.load_state_dict(checkpoint["state_dict"])
        net.eval()
        row = {"loss": record["loss"], "seed": record["seed"], "splits": {}}
        for split, matches in data.items():
            predictions, expected_hits, expected_wrong = [], 0.0, 0.0
            with torch.no_grad():
                for match in matches:
                    x = normalize(
                        match["X"][:, :197], checkpoint["mean"].numpy(), checkpoint["scale"].numpy()
                    )
                    p = torch.sigmoid(net(torch.from_numpy(x))[:, 0])[None]
                    predictions.append(p[0].numpy())
                    y = torch.from_numpy(match["onset_y"].astype(np.float32))[None]
                    ticks = torch.from_numpy(match["ticks"])[None]
                    valid = torch.ones_like(p, dtype=torch.bool)
                    if args.shared:
                        hits, wrong = shared_threshold_counts(p, ticks, y, valid)
                        expected_hits += float(hits.sum())
                        expected_wrong += float(wrong.sum())
                    else:
                        m = emitted(p, ticks, valid)
                        expected_hits += float((m * y).sum())
                        expected_wrong += float((m * (1 - y)).sum())
            threshold = record["threshold"]
            threshold = np.inf if threshold == "silence" else threshold
            deterministic = aggregate(evaluate(matches, predictions, threshold, "onsets"))
            if split == "calibration" and deterministic != record["calibration"]:
                raise ValueError("Checkpoint does not reproduce saved calibration policy")
            row["splits"][split] = {
                "fixed_calibration_threshold": deterministic,
                "uncalibrated_stochastic_expected_recall": expected_hits
                / sum(len(m["onsets"]) for m in matches),
                "uncalibrated_stochastic_expected_unmatched_per_match": expected_wrong
                / len(matches),
            }
        result["models"].append(row)
    name = "shared-threshold-audit" if args.shared else "objective-fit-audit"
    destination = Path(f"reports/{name}-{size}-2026-09-30.json")
    write_report(destination, result)
    print(destination)


if __name__ == "__main__":
    main()
