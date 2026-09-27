"""Optional CPU PyTorch backend for the registered masked GRU control."""

from __future__ import annotations

import importlib
import os
from collections.abc import Iterator
from typing import Any, cast

import numpy as np

from league_ews.b4_sequence import SEQUENCE_FEATURES, STEPS
from league_ews.baseline_floor import LABELS


def right_pad_sequences(inputs: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Move each genuine left-padded history to the front for packed GRU input."""

    if (
        inputs.ndim != 3
        or inputs.shape[1:] != (STEPS, len(SEQUENCE_FEATURES))
        or mask.shape != inputs.shape[:2]
        or mask.dtype != np.bool_
        or not np.all(mask[:, -1])
    ):
        raise ValueError("B4 masked input contract differs from the frozen staging")
    lengths = mask.sum(axis=1).astype(np.int64)
    if any(
        not np.array_equal(row, np.arange(STEPS) >= STEPS - length)
        for row, length in zip(mask, lengths, strict=True)
    ):
        raise ValueError("B4 histories must have contiguous real frames ending at prediction time")
    packed = np.zeros_like(inputs)
    for length in range(1, STEPS + 1):
        rows = np.flatnonzero(lengths == length)
        packed[rows, :length] = inputs[rows, STEPS - length :]
    return packed, lengths


class TorchBackend:
    """Keep neural imports out of the base research installation."""

    def __init__(self, seed: int, device: str = "cpu") -> None:
        if device not in ("cpu", "cuda"):
            raise ValueError("B4 device must be cpu or cuda")
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        try:
            self.torch = importlib.import_module("torch")
        except ImportError as exc:
            raise RuntimeError("Install the optional B4 neural dependency before training") from exc
        torch = self.torch
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable in this PyTorch/WSL runtime")
        self.device = device
        self.version = str(torch.__version__)
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(seed)
        if device == "cuda":
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.benchmark = False
        self.gru = torch.nn.GRU(len(SEQUENCE_FEATURES), 48, batch_first=True).to(device)
        self.head = torch.nn.Linear(48, len(LABELS)).to(device)
        self.optimizer = torch.optim.AdamW(
            [*self.gru.parameters(), *self.head.parameters()], lr=0.001, weight_decay=0.01
        )

    def _logits(self, features: Any, lengths: Any) -> Any:
        torch = self.torch
        packed = torch.nn.utils.rnn.pack_padded_sequence(
            features, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, state = self.gru(packed)
        return self.head(state[-1])

    def train_shard(
        self, inputs: np.ndarray, mask: np.ndarray, targets: np.ndarray, *, seed: int
    ) -> tuple[float, int]:
        """Process one train shard and return average unweighted BCE over rows."""

        torch = self.torch
        if targets.shape != (len(inputs), len(LABELS)) or not np.isin(targets, (0, 1)).all():
            raise ValueError("B4 training targets must be twelve binary columns")
        packed, lengths = right_pad_sequences(inputs, mask)
        self.gru.train()
        self.head.train()
        rng = np.random.default_rng(seed)
        total_loss = 0.0
        batches = 0
        for indices in _batches(rng.permutation(len(inputs)), 1024):
            x = torch.from_numpy(packed[indices]).to(self.device)
            size = torch.from_numpy(lengths[indices])
            truth = torch.from_numpy(targets[indices].astype(np.float32)).to(self.device)
            self.optimizer.zero_grad(set_to_none=True)
            logits = self._logits(x, size)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, truth)
            loss.backward()
            self.optimizer.step()
            total_loss += float(loss.detach()) * len(indices)
            batches += len(indices)
        return total_loss / batches, batches

    def state_dict(self) -> dict[str, Any]:
        return {
            "gru": self.gru.state_dict(),
            "head": self.head.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "rng": self.torch.get_rng_state(),
            "cuda_rng": self.torch.cuda.get_rng_state_all() if self.device == "cuda" else [],
        }

    def load_state_dict(self, state: dict[str, Any]) -> None:
        self.gru.load_state_dict(state["gru"])
        self.head.load_state_dict(state["head"])
        self.optimizer.load_state_dict(state["optimizer"])
        self.torch.set_rng_state(state["rng"])
        if self.device == "cuda":
            self.torch.cuda.set_rng_state_all(state["cuda_rng"])

    def save(self, state: dict[str, Any], path: str) -> None:
        self.torch.save(state, path)

    def load(self, path: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.torch.load(path, map_location="cpu", weights_only=True))


def _batches(indices: np.ndarray, batch_size: int) -> Iterator[np.ndarray]:
    for start in range(0, len(indices), batch_size):
        yield indices[start : start + batch_size]
