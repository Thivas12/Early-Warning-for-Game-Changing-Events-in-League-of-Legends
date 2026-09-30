"""Matched, resumable objective comparison on public development data only."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from league_ews.scheduled_model import standardizer
from league_ews.scheduled_policy import torch_marginals
from research.run_command_anticipation import FREEZE, QUALITY, load_data
from research.run_precontact_pilot import calibrate

LOSSES = (
    "bce",
    "weighted_bce",
    "sol_f1",
    "wsol_f1",
    "wsol_tss",
    "independent_utility",
    "cooldown_utility",
)
SEEDS = (17, 29, 43)


def write_report(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def normalize(x: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    missing = ~np.isfinite(x)
    return np.column_stack(
        (np.clip(np.where(missing, 0, (x - mean) / scale), -20, 20), missing)
    ).astype(np.float32)


def pooled_score_loss(
    p: torch.Tensor, y: torch.Tensor, valid: torch.Tensor, temporal: bool, score: str = "f1"
) -> torch.Tensor:
    """wSOL max equations; temporal shifts within matches, pooled valid counts."""
    y = y.to(p.dtype)
    p = p * valid
    if temporal:
        future, past = [], []
        for lag in (1, 2, 3):
            f, b = torch.zeros_like(y), torch.zeros_like(p)
            if lag < p.shape[1]:
                f[:, :-lag], b[:, lag:] = y[:, lag:] * valid[:, lag:], p[:, :-lag]
            future.append(f)
            past.append(b)
        weights = p.new_tensor([0.5, 0.25, 0.125])
        fp_discount = (torch.stack(future, -1) * weights).max(-1).values
        steps = weights - torch.cat((weights[1:], weights.new_zeros(1)))
        fn_discount = (
            (torch.stack(past, -1).cummax(-1).values - p[..., None]).clamp(min=0) * steps
        ).sum(-1)
    else:
        fp_discount = fn_discount = torch.zeros_like(p)
    tp = (y * p * valid).sum()
    tn = ((1 - y) * (1 - p) * valid).sum()
    fp = ((1 - fp_discount) * (1 - y) * p * valid).sum()
    fn = (y * (1 - p - fn_discount) * valid).sum()

    def ratio(a, b):
        return torch.where(
            b == 0, torch.zeros_like(a), a / torch.where(b == 0, torch.ones_like(b), b)
        )

    metric = (
        ratio(2 * tp, 2 * tp + fp + fn)
        if score == "f1"
        else ratio(tp, tp + fn) + ratio(tn, tn + fp) - 1
    )
    return 1 - metric


def emitted(p: torch.Tensor, ticks: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
    delta = ticks[:, :, None] - ticks[:, None, :]
    blocked = (delta > 0) & (delta < 1800) & valid[:, :, None] & valid[:, None, :]
    return torch_marginals(p * valid, blocked)


def network(prevalence: float) -> torch.nn.Module:
    net = torch.nn.Sequential(
        torch.nn.Linear(394, 64),
        torch.nn.GELU(),
        torch.nn.Linear(64, 64),
        torch.nn.GELU(),
        torch.nn.Linear(64, 1),
    )
    torch.nn.init.constant_(net[-1].bias, math.log(prevalence / (1 - prevalence)))
    return net


def make_batch(data: list[dict], indices: np.ndarray) -> tuple:
    lengths = [len(data[i]["ticks"]) for i in indices]
    width = max(lengths)
    x = torch.zeros(len(indices), width, 394)
    y = torch.zeros(len(indices), width)
    valid = torch.zeros(len(indices), width, dtype=torch.bool)
    ticks = torch.zeros(len(indices), width, dtype=torch.int64)
    for j, i in enumerate(indices):
        n = lengths[j]
        x[j, :n] = data[i]["normalized"]
        y[j, :n] = torch.from_numpy(data[i]["onset_y"].astype(np.float32))
        valid[j, :n] = True
        ticks[j, :n] = torch.from_numpy(data[i]["ticks"])
    return x, y, valid, ticks


def train(
    net: torch.nn.Module,
    data: list[dict],
    loss_name: str,
    epochs: int,
    seed: int,
    positive_weight: float,
) -> list[dict]:
    optimizer = torch.optim.AdamW(net.parameters(), lr=0.001, weight_decay=0.01)
    rng = np.random.default_rng(seed)
    order = np.argsort([len(m["ticks"]) for m in data], kind="stable")
    groups = [order[i : i + 8] for i in range(0, len(order), 8)]
    batches = [make_batch(data, g) for g in groups]
    multiplier = 0.1
    records = []
    for epoch in range(epochs):
        total = 0.0
        for index in rng.permutation(len(batches)):
            x, y, valid, ticks = batches[index]
            logits = net(x)[..., 0]
            p = torch.sigmoid(logits) * valid
            if loss_name in ("bce", "weighted_bce"):
                pw = logits.new_tensor(positive_weight if loss_name == "weighted_bce" else 1.0)
                rows = torch.nn.functional.binary_cross_entropy_with_logits(
                    logits, y, pos_weight=pw, reduction="none"
                )
                loss = ((rows * valid).sum(1) / valid.sum(1)).mean()
            elif loss_name in ("sol_f1", "wsol_f1", "wsol_tss"):
                loss = pooled_score_loss(
                    p, y, valid, loss_name != "sol_f1", "tss" if loss_name == "wsol_tss" else "f1"
                )
            else:
                m = emitted(p, ticks, valid) if loss_name == "cooldown_utility" else p
                hits = (m * y).sum(1)
                wrong = (m * (1 - y)).sum(1)
                loss = (-hits + multiplier * (wrong - 1)).mean()
            if not torch.isfinite(loss):
                raise ValueError(f"Nonfinite {loss_name} objective")
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0)
            optimizer.step()
            if loss_name.endswith("utility"):
                multiplier = float(
                    np.clip(multiplier + 0.01 * (wrong.detach().mean().item() - 1), 0, 100)
                )
            total += float(loss.detach()) * len(x)
        records.append(
            {
                "epoch": epoch + 1,
                "training_loss": total / len(data),
                "multiplier": multiplier if loss_name.endswith("utility") else None,
            }
        )
        if (epoch + 1) % 10 == 0:
            print(loss_name, "epoch", epoch + 1, "loss", records[-1]["training_loss"], flush=True)
    return records


def inputs(expanded: bool) -> tuple[dict, dict]:
    original_freeze = json.loads(FREEZE.read_text())
    if hashlib.sha256(QUALITY.read_bytes()).hexdigest() != original_freeze["quality_sha256"]:
        raise ValueError("Original quality changed")
    data = load_data(("train", "calibration"))
    bindings = {str(QUALITY): original_freeze["quality_sha256"]}
    if expanded:
        qp = Path("reports/objective-expansion-quality-2026-09-30.json")
        quality = json.loads(qp.read_text())
        if len(quality["matches"]) != 750:
            raise ValueError("Incomplete expansion quality report")
        bindings[str(qp)] = hashlib.sha256(qp.read_bytes()).hexdigest()
        for row in quality["matches"]:
            if row["split"] not in data:
                raise ValueError("Evaluation data forbidden")
            if row["status"] != "accepted":
                continue
            path = Path("data/processed/objective-expansion") / f"{row['match_id']}.npz"
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["arrays_sha256"]:
                raise ValueError("Expansion arrays changed")
            arrays = dict(np.load(path, allow_pickle=False))
            arrays.update(match_id=str(row["match_id"]), day=row["start_time"] // 86400)
            data[row["split"]].append(arrays)
        if len(data["train"]) < 200 or len(data["calibration"]) < 60:
            raise ValueError("Insufficient expanded development cohort")
    all_ids = [m["match_id"] for group in data.values() for m in group]
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("Development match overlap")
    return data, bindings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expanded", action="store_true")
    args = parser.parse_args()
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    data, bindings = inputs(args.expanded)
    size = "expanded" if args.expanded else "small"
    root = Path(f"data/processed/objective-training-{size}")
    root.mkdir(parents=True, exist_ok=True)
    output = Path(f"reports/objective-training-{size}-2026-09-30.json")
    freeze_path = Path(f"reports/objective-training-{size}-freeze-2026-09-30.json")
    code_paths = [
        Path(__file__),
        Path("docs/public-objective-training-protocol.md"),
        Path("docs/objective-training-expansion.md"),
        Path("src/league_ews/scheduled_model.py"),
        Path("src/league_ews/scheduled_policy.py"),
        Path("src/league_ews/policy_novelty.py"),
        Path("research/run_command_anticipation.py"),
        Path("research/run_precontact_pilot.py"),
        Path("research/precontact_data.py"),
        Path("research/objective_onset.py"),
        Path("tests/test_public_objective_training.py"),
    ]
    freeze = {
        "scope": "development only",
        "size": size,
        "seeds": SEEDS,
        "losses": LOSSES,
        "data_bindings": bindings,
        "torch_version": torch.__version__,
        "code_bindings": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths},
        "matches": {s: [m["match_id"] for m in v] for s, v in data.items()},
    }
    encoded = json.dumps(freeze, indent=2) + "\n"
    if freeze_path.exists() and freeze_path.read_text() != encoded:
        raise ValueError("Frozen objective experiment changed")
    freeze_path.write_text(encoded)
    report = (
        json.loads(output.read_text())
        if output.exists()
        else {
            "freeze_sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
            "models": [],
            "scope": "development only; no new held-out evidence",
            "size": size,
            "matches": {k: len(v) for k, v in data.items()},
            "targets": {k: sum(len(m["onsets"]) for m in v) for k, v in data.items()},
            "decision_rows": {k: sum(len(m["ticks"]) for m in v) for k, v in data.items()},
            "positive_rows": {k: sum(int(m["onset_y"].sum()) for m in v) for k, v in data.items()},
        }
    )
    if report["freeze_sha256"] != hashlib.sha256(freeze_path.read_bytes()).hexdigest():
        raise ValueError("Report freeze differs")
    xtrain = np.concatenate([m["X"][:, :197] for m in data["train"]])
    ytrain = np.concatenate([m["onset_y"] for m in data["train"]])
    prevalence = float(ytrain.mean())
    mean, scale = standardizer(xtrain)
    for group in data.values():
        for m in group:
            m["normalized"] = torch.from_numpy(normalize(m["X"][:, :197], mean, scale))
    if "hgb" not in report:
        with threadpool_limits(limits=4):
            hgb = HistGradientBoostingClassifier(
                max_iter=120,
                max_leaf_nodes=15,
                min_samples_leaf=30,
                l2_regularization=1.0,
                early_stopping=False,
                learning_rate=0.08,
                random_state=17,
            ).fit(xtrain, ytrain)
            pred = [hgb.predict_proba(m["X"][:, :197])[:, 1] for m in data["calibration"]]
            threshold, cal = calibrate(data["calibration"], pred, "onsets")
        report["hgb"] = {
            "calibration": cal,
            "threshold": threshold if np.isfinite(threshold) else "silence",
        }
        if not args.expanded and cal != next(
            r["calibration"]
            for r in json.loads(FREEZE.read_text())["models"]
            if r["name"] == "history"
        ):
            raise ValueError("Original history baseline did not reproduce")
        write_report(output, report)
    for seed in SEEDS:
        torch.manual_seed(seed)
        warm = network(prevalence)
        warm_path = root / f"warm-{seed}.pt"
        if warm_path.exists():
            recorded = report.get("warm_starts", {}).get(str(seed))
            if (
                not recorded
                or hashlib.sha256(warm_path.read_bytes()).hexdigest() != recorded["sha256"]
            ):
                raise ValueError("Unbound warm start")
            warm.load_state_dict(torch.load(warm_path, weights_only=True))
        else:
            history = train(warm, data["train"], "bce", 10, seed + 100, 1.0)
            torch.save(warm.state_dict(), warm_path)
            report.setdefault("warm_starts", {})[str(seed)] = {
                "sha256": hashlib.sha256(warm_path.read_bytes()).hexdigest(),
                "history": history,
            }
            write_report(output, report)
        for loss_name in LOSSES:
            prior = next(
                (r for r in report["models"] if r["seed"] == seed and r["loss"] == loss_name), None
            )
            model_path = root / f"{loss_name}-{seed}.pt"
            if prior:
                if hashlib.sha256(model_path.read_bytes()).hexdigest() != prior["weights_sha256"]:
                    raise ValueError("Model checkpoint changed")
                continue
            net = copy.deepcopy(warm)
            started = time.monotonic()
            history = train(
                net,
                data["train"],
                loss_name,
                30,
                seed + 200,
                math.sqrt((1 - prevalence) / prevalence),
            )
            with torch.no_grad():
                prediction = [
                    torch.sigmoid(net(m["normalized"])[:, 0]).numpy() for m in data["calibration"]
                ]
            threshold, cal = calibrate(data["calibration"], prediction, "onsets")
            torch.save(
                {
                    "state_dict": net.state_dict(),
                    "mean": torch.from_numpy(mean),
                    "scale": torch.from_numpy(scale),
                },
                model_path,
            )
            report["models"].append(
                {
                    "loss": loss_name,
                    "fit_seconds": time.monotonic() - started,
                    "seed": seed,
                    "weights_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                    "threshold": threshold if np.isfinite(threshold) else "silence",
                    "calibration": cal,
                    "training": history,
                }
            )
            write_report(output, report)
            print("CALIBRATED", seed, loss_name, cal, flush=True)
    report["gates"] = []
    for seed in SEEDS:
        rows = [r for r in report["models"] if r["seed"] == seed]
        primary = next(r for r in rows if r["loss"] == "cooldown_utility")["calibration"]
        controls = [r["calibration"] for r in rows if r["loss"] != "cooldown_utility"] + [
            report["hgb"]["calibration"]
        ]
        best_hits = max(c["hits"] for c in controls)
        gain = (primary["hits"] - best_hits) / primary["targets"]
        passes = primary["unmatched_per_match"] <= 1 and (
            primary["recall"] >= 0.25 and gain >= 0.10
            if args.expanded
            else primary["hits"] >= 8 and primary["hits"] >= best_hits + 3
        )
        report["gates"].append(
            {
                "seed": seed,
                "primary_hits": primary["hits"],
                "best_control_hits": best_hits,
                "recall_gain": gain,
                "passes": passes,
            }
        )
    report["advances_to_new_evaluation"] = all(r["passes"] for r in report["gates"])
    write_report(output, report)
    print("FINAL", size, report["gates"], flush=True)


if __name__ == "__main__":
    main()
