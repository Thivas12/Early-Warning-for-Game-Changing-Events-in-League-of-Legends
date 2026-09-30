"""Matched neural controls and exact expected cooldown-policy training.

The encoder is intentionally ordinary. The method hypothesis concerns credit
assignment through the alarm policy, not architectural novelty.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import numpy as np

from league_ews.scheduled_policy import Decisions, exclusion_matrix, torch_marginals

MODELS = (
    "history-bce",
    "history-pmf",
    "history-utility",
    "history-refractory",
    "clock-bce",
    "history-refractory-frame",
)
CLOCK_COLUMNS = (0, 18, 19, 22)  # observed clock, Dragon counts, time since observed Dragon


@dataclass(frozen=True)
class Settings:
    epochs: int = 8
    warm_epochs: int = 2
    batch_matches: int = 32
    width: int = 128
    learning_rate: float = 0.001
    dual_rate: float = 0.02
    training_budget: float = 1.0


def runtime(device: str) -> tuple[Any, str]:
    # Set before CUDA initialization, including for determinism of matrix multiplication.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch

    if device not in ("cpu", "cuda", "auto"):
        raise ValueError("Device must be cpu, cuda or auto")
    chosen = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
    if chosen == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is unavailable in this Python environment. Inspect nvidia-smi and "
            "torch.version.cuda; install the appropriate PyTorch CUDA build or "
            "explicitly choose --device cpu. No experiment has been trained."
        )
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    return torch, chosen


def standardizer(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    count = np.zeros(x.shape[1], dtype=np.float64)
    total, squares = count.copy(), count.copy()
    for start in range(0, len(x), 8192):
        part = np.asarray(x[start : start + 8192], dtype=np.float64)
        finite = np.isfinite(part)
        values = np.where(finite, part, 0)
        count += finite.sum(axis=0)
        total += values.sum(axis=0)
        squares += (values * values).sum(axis=0)
    mean = total / np.maximum(count, 1)
    scale = np.sqrt(np.maximum(squares / np.maximum(count, 1) - mean * mean, 0))
    scale = np.where(scale < 1e-6, 1, scale)
    return mean.astype(np.float32), scale.astype(np.float32)


def feature_array(
    raw: np.ndarray, ages: np.ndarray, mean: np.ndarray, scale: np.ndarray, clock: bool
) -> np.ndarray:
    if clock:
        raw, mean, scale = (
            raw[:, CLOCK_COLUMNS],
            mean[list(CLOCK_COLUMNS)],
            scale[list(CLOCK_COLUMNS)],
        )
    missing = ~np.isfinite(raw)
    values = np.where(missing, 0, (raw - mean) / scale)
    # Clipping is fitted nowhere and avoids extreme covariate magnitudes.
    return np.concatenate(
        (
            np.clip(values, -20, 20),
            missing.astype(np.float32),
            (ages / 60_000).astype(np.float32)[:, None],
        ),
        axis=1,
    ).astype(np.float32)


def network(torch: Any, features: int, settings: Settings, pmf: bool) -> Any:
    return torch.nn.Sequential(
        torch.nn.Linear(features, settings.width),
        torch.nn.GELU(),
        torch.nn.Linear(settings.width, settings.width),
        torch.nn.GELU(),
        torch.nn.Linear(settings.width, 25 if pmf else 1),
    )


def batches(lengths: list[int], batch_size: int, rng: np.random.Generator) -> list[np.ndarray]:
    # Length bucketing bounds padded triangular-solve memory without truncating matches.
    order = np.argsort(np.asarray(lengths), kind="stable")
    groups = [order[i : i + batch_size] for i in range(0, len(order), batch_size)]
    rng.shuffle(groups)
    return groups


def make_batch(
    data: dict[str, Any],
    traces: list[Decisions],
    indices: np.ndarray,
    mean: np.ndarray,
    scale: np.ndarray,
    *,
    clock: bool,
    pmf: bool,
    torch: Any,
    device: str,
) -> dict[str, Any]:
    lengths = [len(data["times"][i]) - 1 if pmf else len(traces[i].times) for i in indices]
    width = max(1, max(lengths))
    nfeatures = 2 * (len(CLOCK_COLUMNS) if clock else len(mean)) + 1
    x = np.zeros((len(indices), width, nfeatures), dtype=np.float32)
    valid = np.zeros((len(indices), width), dtype=bool)
    times = np.zeros((len(indices), width), dtype=np.int64)
    target = np.zeros((len(indices), width), dtype=np.int64)
    late = np.zeros((len(indices), width), dtype=np.float32)
    for j, i in enumerate(indices):
        n, trace = lengths[j], traces[i]
        start = data["offsets"][i]
        if pmf:
            stamp = np.asarray(data["times"][i][:-1], dtype=np.int64)
            e = np.asarray(data["events"][i], dtype=np.int64)
            nxt = np.searchsorted(e, stamp, side="right")
            delays = np.full(n, 121_000, dtype=np.int64)
            present = nxt < len(e)
            delays[present] = e[nxt[present]] - stamp[present]
            target[j, :n] = np.minimum((delays - 1) // 5000, 24)
            raw = data["x"][start : start + n]
            age = np.zeros(n, dtype=np.int64)
        else:
            stamp, raw, age = trace.times, data["x"][start + trace.rows], trace.ages
            target[j, :n], late[j, :n] = trace.timely, trace.late
        x[j, :n] = feature_array(raw, age, mean, scale, clock)
        valid[j, :n], times[j, :n] = True, stamp
    return {
        "x": torch.as_tensor(x, device=device),
        "valid": torch.as_tensor(valid, device=device),
        "times": torch.as_tensor(times, device=device),
        "target": torch.as_tensor(target, device=device),
        "late": torch.as_tensor(late, device=device),
    }


def fit(
    data: dict[str, Any],
    traces: list[Decisions],
    routes: list[str],
    model_name: str,
    seed: int,
    settings: Settings,
    device: str,
    *,
    progress: bool = True,
) -> tuple[Any, dict[str, Any]]:
    if (
        model_name not in MODELS
        or settings.epochs <= settings.warm_epochs
        or settings.warm_epochs < 1
        or settings.batch_matches < 1
        or settings.width < 1
        or settings.learning_rate <= 0
        or settings.dual_rate <= 0
        or settings.training_budget < 0
        or len(traces) != len(routes)
        or not traces
    ):
        raise ValueError("Invalid matched training configuration")
    torch, device = runtime(device)
    torch.manual_seed(seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)
    rng = np.random.default_rng(seed)
    mean, scale = standardizer(data["x"])
    clock, pmf = model_name == "clock-bce", model_name == "history-pmf"
    net = network(torch, 2 * (len(CLOCK_COLUMNS) if clock else len(mean)) + 1, settings, pmf).to(
        device
    )
    optimizer = torch.optim.AdamW(net.parameters(), lr=settings.learning_rate, weight_decay=0.01)
    route_names = sorted(set(routes))
    route_ids = np.asarray([route_names.index(r) for r in routes])
    dual = torch.ones(len(route_names), dtype=torch.float32, device=device)
    records = []
    lengths = [len(data["times"][i]) - 1 if pmf else len(t.times) for i, t in enumerate(traces)]
    for epoch in range(settings.epochs):
        total, seen = 0.0, 0
        for indices in batches(lengths, settings.batch_matches, rng):
            batch = make_batch(
                data, traces, indices, mean, scale, clock=clock, pmf=pmf, torch=torch, device=device
            )
            logits = net(batch["x"])
            mask, y = batch["valid"], batch["target"]
            fine = epoch >= settings.warm_epochs and (
                "refractory" in model_name or "utility" in model_name
            )
            if pmf:
                values = torch.nn.functional.cross_entropy(
                    logits.transpose(1, 2), y, reduction="none"
                )
                loss = ((values * mask).sum(1) / mask.sum(1).clamp(min=1)).mean()
            elif not fine:
                values = torch.nn.functional.binary_cross_entropy_with_logits(
                    logits[:, :, 0], y.float(), reduction="none"
                )
                loss = ((values * mask).sum(1) / mask.sum(1).clamp(min=1)).mean()
            else:
                p = torch.sigmoid(logits[:, :, 0]) * mask
                m = (
                    torch_marginals(p, exclusion_matrix(batch["times"], mask))
                    if "refractory" in model_name
                    else p
                )
                timely = (m * y).sum(1)
                wrong = (m * (1 - y)).sum(1)
                groups = torch.as_tensor(route_ids[indices], device=device)
                loss = (-timely + dual[groups].detach() * (wrong - settings.training_budget)).mean()
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0)
            optimizer.step()
            if fine:
                with torch.no_grad():
                    for group in range(len(route_names)):
                        members = groups == group
                        if members.any():
                            dual[group] = (
                                dual[group]
                                + settings.dual_rate
                                * (wrong[members].mean() - settings.training_budget)
                            ).clamp(0.01, 50)
            total += float(loss.detach().cpu()) * len(indices)
            seen += len(indices)
        row = {
            "epoch": epoch + 1,
            "loss": total / seen,
            "dual_by_route": dict(zip(route_names, dual.detach().cpu().tolist(), strict=True)),
        }
        records.append(row)
        if progress:
            print(
                f"{model_name} seed={seed} epoch={epoch + 1}/{settings.epochs} "
                f"loss={row['loss']:.5f}",
                flush=True,
            )
    net.eval()
    payload = {
        "state_dict": {k: v.detach().cpu() for k, v in net.state_dict().items()},
        "mean": torch.from_numpy(mean),
        "scale": torch.from_numpy(scale),
        "model_name": model_name,
        "seed": seed,
    }
    info = {
        "training": records,
        "device": device,
        "torch_version": str(torch.__version__),
        "cuda_version": torch.version.cuda,
        "device_name": torch.cuda.get_device_name() if device == "cuda" else "CPU",
        "parameters": sum(p.numel() for p in net.parameters()),
        "normalizer_scope": "training rows only",
    }
    return payload, info


def predict(
    data: dict[str, Any],
    traces: list[Decisions],
    payload: dict[str, Any],
    settings: Settings,
    device: str,
) -> list[np.ndarray]:
    torch, device = runtime(device)
    name = payload["model_name"]
    clock, pmf = name == "clock-bce", name == "history-pmf"
    mean, scale = payload["mean"].numpy(), payload["scale"].numpy()
    net = network(torch, 2 * (len(CLOCK_COLUMNS) if clock else len(mean)) + 1, settings, pmf).to(
        device
    )
    net.load_state_dict(payload["state_dict"])
    net.eval()
    output: list[np.ndarray] = [np.empty(0)] * len(traces)
    with torch.no_grad():
        for indices in batches(
            [len(t.times) for t in traces], settings.batch_matches, np.random.default_rng(0)
        ):
            batch = make_batch(
                data,
                traces,
                indices,
                mean,
                scale,
                clock=clock,
                pmf=False,
                torch=torch,
                device=device,
            )
            if pmf:
                # Forecast issued at the last observed frame. Age affects only the queried interval.
                batch["x"][:, :, -1] = 0
            raw = net(batch["x"])
            for j, i in enumerate(indices):
                n = len(traces[i].times)
                if pmf:
                    dist = torch.softmax(raw[j, :n], -1).cpu().numpy()
                    low = traces[i].ages[:, None] + 20_000
                    high = traces[i].ages[:, None] + 60_000
                    edges = np.arange(25) * 5000
                    weights = (
                        np.maximum(0, np.minimum(high, edges[1:]) - np.maximum(low, edges[:-1]))
                        / 5000
                    )
                    probability = np.clip((dist[:, :24] * weights).sum(1), 1e-7, 1 - 1e-7)
                    output[i] = np.log(probability / (1 - probability))
                else:
                    output[i] = raw[j, :n, 0].cpu().numpy().astype(np.float64)
    return output
