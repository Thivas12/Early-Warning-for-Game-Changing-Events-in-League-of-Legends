"""Six frozen follow-up fits using the established shared-threshold extension."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numba
import numpy as np
import torch

from research.public_objective_training import (
    SEEDS,
    inputs,
    make_batch,
    network,
    normalize,
    write_report,
)
from research.run_precontact_pilot import calibrate
from research.shared_threshold import shared_threshold_counts


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit(net, data, seed):
    optimizer = torch.optim.AdamW(net.parameters(), lr=0.001, weight_decay=0.01)
    rng = np.random.default_rng(seed + 200)
    order = np.argsort([len(m["ticks"]) for m in data], kind="stable")
    batches = [make_batch(data, order[i : i + 8]) for i in range(0, len(order), 8)]
    multiplier, history = 0.1, []
    for epoch in range(30):
        total = 0.0
        for index in rng.permutation(len(batches)):
            x, y, valid, ticks = batches[index]
            p = torch.sigmoid(net(x)[..., 0]) * valid
            hits, wrong = shared_threshold_counts(p, ticks, y, valid)
            loss = (-hits + multiplier * (wrong - 1)).mean()
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite shared-threshold objective")
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0)
            optimizer.step()
            multiplier = float(
                np.clip(multiplier + 0.01 * (wrong.detach().mean().item() - 1), 0, 100)
            )
            total += float(loss.detach()) * len(x)
        history.append(
            {"epoch": epoch + 1, "training_loss": total / len(data), "multiplier": multiplier}
        )
        if (epoch + 1) % 10 == 0:
            print("shared_threshold", seed, history[-1], flush=True)
    return history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expanded", action="store_true")
    args = parser.parse_args()
    size = "expanded" if args.expanded else "small"
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    original = Path(f"reports/objective-training-{size}-2026-09-30.json")
    controls = json.loads(original.read_text())
    if len(controls["models"]) != 21 or "gates" not in controls:
        raise ValueError("Finish the original 21-fit comparison first")
    original_freeze = Path(f"reports/objective-training-{size}-freeze-2026-09-30.json")
    base_freeze = json.loads(original_freeze.read_text())
    data, bindings = inputs(args.expanded)
    if bindings != base_freeze["data_bindings"]:
        raise ValueError("Follow-up data differ from controls")
    paths = [
        Path(__file__),
        Path("research/shared_threshold.py"),
        Path("tests/test_shared_threshold.py"),
        Path("docs/shared-threshold-training-protocol.md"),
    ]
    frozen = {
        "scope": "development only; post-original-result follow-up",
        "size": size,
        "control_report_sha256": digest(original),
        "control_freeze_sha256": digest(original_freeze),
        "code_bindings": {str(p): digest(p) for p in paths},
        "numpy_version": np.__version__,
        "numba_version": numba.__version__,
        "torch_version": torch.__version__,
        "seeds": SEEDS,
    }
    freeze_path = Path(f"reports/shared-threshold-{size}-freeze-2026-09-30.json")
    encoded = json.dumps(frozen, indent=2) + "\n"
    if freeze_path.exists() and freeze_path.read_text() != encoded:
        raise ValueError("Frozen follow-up changed")
    freeze_path.write_text(encoded)
    output = Path(f"reports/shared-threshold-{size}-2026-09-30.json")
    report = (
        json.loads(output.read_text())
        if output.exists()
        else {"freeze_sha256": digest(freeze_path), "size": size, "models": []}
    )
    if report["freeze_sha256"] != digest(freeze_path):
        raise ValueError("Report freeze differs")
    original_root = Path(f"data/processed/objective-training-{size}")
    checkpoint_path = original_root / "bce-17.pt"
    expected_hash = next(
        r["weights_sha256"] for r in controls["models"] if r["loss"] == "bce" and r["seed"] == 17
    )
    if digest(checkpoint_path) != expected_hash:
        raise ValueError("Control checkpoint changed")
    preprocessing = torch.load(checkpoint_path, weights_only=True)
    mean, scale = preprocessing["mean"].numpy(), preprocessing["scale"].numpy()
    for group in data.values():
        for m in group:
            m["normalized"] = torch.from_numpy(normalize(m["X"][:, :197], mean, scale))
    root = Path(f"data/processed/shared-threshold-{size}")
    root.mkdir(parents=True, exist_ok=True)
    for seed in SEEDS:
        destination = root / f"shared-threshold-{seed}.pt"
        prior = next((r for r in report["models"] if r["seed"] == seed), None)
        if prior:
            if digest(destination) != prior["weights_sha256"]:
                raise ValueError("Follow-up checkpoint changed")
            continue
        warm_path = original_root / f"warm-{seed}.pt"
        if digest(warm_path) != controls["warm_starts"][str(seed)]["sha256"]:
            raise ValueError("Common warm start changed")
        torch.manual_seed(seed)
        net = network(0.5)
        net.load_state_dict(torch.load(warm_path, weights_only=True))
        started = time.monotonic()
        history = fit(net, data["train"], seed)
        with torch.no_grad():
            predictions = [
                torch.sigmoid(net(m["normalized"])[:, 0]).numpy() for m in data["calibration"]
            ]
        threshold, cal = calibrate(data["calibration"], predictions, "onsets")
        torch.save(
            {
                "state_dict": net.state_dict(),
                "mean": preprocessing["mean"],
                "scale": preprocessing["scale"],
            },
            destination,
        )
        best_hits = max(
            [r["calibration"]["hits"] for r in controls["models"] if r["seed"] == seed]
            + [controls["hgb"]["calibration"]["hits"]]
        )
        gain = (cal["hits"] - best_hits) / cal["targets"]
        passes = cal["unmatched_per_match"] <= 1 and (
            cal["recall"] >= 0.25 and gain >= 0.10
            if args.expanded
            else cal["hits"] >= 8 and cal["hits"] >= best_hits + 3
        )
        report["models"].append(
            {
                "loss": "shared_threshold_utility",
                "seed": seed,
                "fit_seconds": time.monotonic() - started,
                "weights_sha256": digest(destination),
                "threshold": threshold if np.isfinite(threshold) else "silence",
                "calibration": cal,
                "training": history,
                "best_control_hits": best_hits,
                "recall_gain": gain,
                "passes": passes,
            }
        )
        write_report(output, report)
        print("CALIBRATED", size, seed, cal, "gate", passes, flush=True)
    report["advances_to_new_evaluation"] = all(r["passes"] for r in report["models"])
    write_report(output, report)
    print("FINAL", size, report["advances_to_new_evaluation"], flush=True)


if __name__ == "__main__":
    main()
