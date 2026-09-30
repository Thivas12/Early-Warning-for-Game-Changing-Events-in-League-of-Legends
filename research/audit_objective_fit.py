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
    args = parser.parse_args()
    torch.set_num_threads(4)
    size = "expanded" if args.expanded else "small"
    report_path = Path(f"reports/objective-training-{size}-2026-09-30.json")
    report = json.loads(report_path.read_text())
    if len(report["models"]) != 21 or "gates" not in report:
        raise ValueError("Run this diagnostic only after all fits finish")
    data, bindings = inputs(args.expanded)
    freeze = json.loads(
        Path(f"reports/objective-training-{size}-freeze-2026-09-30.json").read_text()
    )
    if bindings != freeze["data_bindings"]:
        raise ValueError("Diagnostic data differ from the original experiment")
    result = {
        "scope": "post-fit descriptive train/calibration audit; no policy changes",
        "model_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "models": [],
    }
    for record in report["models"]:
        path = (
            Path(f"data/processed/objective-training-{size}")
            / f"{record['loss']}-{record['seed']}.pt"
        )
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
                    m = emitted(
                        p,
                        torch.from_numpy(match["ticks"])[None],
                        torch.ones_like(p, dtype=torch.bool),
                    )
                    y = torch.from_numpy(match["onset_y"].astype(np.float32))[None]
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
    destination = Path(f"reports/objective-fit-audit-{size}-2026-09-30.json")
    write_report(destination, result)
    print(destination)


if __name__ == "__main__":
    main()
