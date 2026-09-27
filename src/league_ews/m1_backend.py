"""Optional PyTorch backend for the frozen relation-aware M1 graph hazards."""

from __future__ import annotations

import importlib
import os
from collections.abc import Iterator
from typing import Any, cast

import numpy as np

from league_ews.graph import FEATURE_NAMES
from league_ews.m1_graph_window import EDGE_TYPES, STEPS


def right_pad_graphs(
    nodes: np.ndarray,
    edges: np.ndarray,
    mask: np.ndarray,
    ages: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Move real left-padded frames to the front for a packed GRU."""

    rows = len(nodes)
    if (
        nodes.shape != (rows, STEPS, 12, len(FEATURE_NAMES))
        or edges.shape != (rows, STEPS, len(EDGE_TYPES), 12, 12)
        or mask.shape != (rows, STEPS)
        or ages.shape != (rows, STEPS)
        or nodes.dtype != np.float32
        or edges.dtype != np.bool_
        or mask.dtype != np.bool_
        or ages.dtype != np.float32
        or not np.all(mask[:, -1])
        or not np.isfinite(nodes).all()
        or not np.isfinite(ages).all()
        or np.any(ages < 0)
        or np.any(ages[:, -1] != 0)
    ):
        raise ValueError("M1 graph inputs differ from frozen causal window shapes")
    lengths = mask.sum(axis=1).astype(np.int64)
    if any(
        not np.array_equal(row, np.arange(STEPS) >= STEPS - length)
        for row, length in zip(mask, lengths, strict=True)
    ):
        raise ValueError("M1 histories must be contiguous real frames ending at prediction time")
    if (
        np.any(nodes[~mask] != 0)
        or np.any(edges[~mask])
        or np.any(ages[~mask] != 0)
        or any(
            np.any(np.diff(row[-length:]) > 0) for row, length in zip(ages, lengths, strict=True)
        )
    ):
        raise ValueError("M1 padded or historical graph frames are invalid")
    packed_nodes = np.zeros_like(nodes)
    packed_edges = np.zeros_like(edges)
    packed_ages = np.zeros_like(ages)
    for length in range(1, STEPS + 1):
        indices = np.flatnonzero(lengths == length)
        packed_nodes[indices, :length] = nodes[indices, STEPS - length :]
        packed_edges[indices, :length] = edges[indices, STEPS - length :]
        packed_ages[indices, :length] = ages[indices, STEPS - length :]
    return packed_nodes, packed_edges, packed_ages, lengths


def at_risk_mask(targets: np.ndarray) -> np.ndarray:
    """Keep each event type at risk through its first positive bin."""

    if (
        targets.ndim != 3
        or targets.shape[1:] != (3, 6)
        or not np.isin(targets, (0, 1)).all()
        or np.any(targets.sum(axis=-1) > 1)
    ):
        raise ValueError("M1 event-specific hazard targets must have at most one onset per type")
    return cast(np.ndarray, (1 - np.cumsum(targets, axis=-1) + targets).astype(np.float32))


def _batches(indices: np.ndarray, batch_size: int) -> Iterator[np.ndarray]:
    for start in range(0, len(indices), batch_size):
        yield indices[start : start + batch_size]


class TorchM1Backend:
    """Keep neural imports out of non-training CLI commands."""

    def __init__(self, seed: int, device: str = "cpu") -> None:
        if device not in ("cpu", "cuda"):
            raise ValueError("M1 device must be cpu or cuda")
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        try:
            torch = importlib.import_module("torch")
        except ImportError as exc:
            raise RuntimeError("Install the optional neural dependency before M1 training") from exc
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable in this PyTorch/WSL runtime")
        self.torch = torch
        self.device = device
        self.version = str(torch.__version__)
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(seed)
        if device == "cuda":
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.benchmark = False

        class GraphHazards(torch.nn.Module):  # type: ignore[name-defined,misc]
            def __init__(self) -> None:
                super().__init__()
                self.input = torch.nn.Linear(len(FEATURE_NAMES), 64)
                self.self_updates = torch.nn.ModuleList([torch.nn.Linear(64, 64) for _ in range(2)])
                self.relation_updates = torch.nn.ModuleList(
                    [torch.nn.Linear(len(EDGE_TYPES) * 64, 64) for _ in range(2)]
                )
                self.dropout = torch.nn.Dropout(0.1)
                self.temporal = torch.nn.GRU(65, 64, batch_first=True)
                self.head = torch.nn.Linear(64, 18)

            def forward(self, nodes: Any, edges: Any, ages: Any, lengths: Any) -> Any:
                mask = (
                    torch.arange(STEPS, device=nodes.device)[None]
                    < lengths.to(nodes.device)[:, None]
                )
                hidden = torch.relu(self.input(nodes)) * mask[:, :, None, None]
                adjacency = edges.float()
                adjacency = adjacency / adjacency.sum(dim=-1, keepdim=True).clamp(min=1)
                for own, relation in zip(self.self_updates, self.relation_updates, strict=True):
                    messages = torch.einsum("bteij,btjh->bteih", adjacency, hidden)
                    messages = messages.permute(0, 1, 3, 2, 4).reshape(
                        len(nodes), STEPS, 12, len(EDGE_TYPES) * 64
                    )
                    hidden = self.dropout(torch.relu(own(hidden) + relation(messages)))
                    hidden = hidden * mask[:, :, None, None]
                pooled = hidden.mean(dim=2)
                temporal_input = torch.cat((pooled, ages.unsqueeze(-1)), dim=-1)
                packed = torch.nn.utils.rnn.pack_padded_sequence(
                    temporal_input, lengths.cpu(), batch_first=True, enforce_sorted=False
                )
                _, state = self.temporal(packed)
                return self.head(state[-1]).reshape(len(nodes), 3, 6)

        self.model = GraphHazards().to(device)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=0.001, weight_decay=0.01)

    def train_shard(
        self,
        nodes: np.ndarray,
        edges: np.ndarray,
        mask: np.ndarray,
        ages: np.ndarray,
        targets: np.ndarray,
        *,
        seed: int,
    ) -> tuple[float, int]:
        """Train on one shard with independent event hazards and at-risk masking."""

        packed_nodes, packed_edges, packed_ages, lengths = right_pad_graphs(
            nodes, edges, mask, ages
        )
        risk = at_risk_mask(targets)
        self.model.train()
        total_loss = 0.0
        total_weight = 0
        rng = np.random.default_rng(seed)
        for indices in _batches(rng.permutation(len(nodes)), 256):
            torch = self.torch
            x = torch.from_numpy(packed_nodes[indices]).to(self.device)
            e = torch.from_numpy(packed_edges[indices]).to(self.device)
            a = torch.from_numpy(packed_ages[indices]).to(self.device)
            lengths_batch = torch.from_numpy(lengths[indices])
            truth = torch.from_numpy(targets[indices].astype(np.float32)).to(self.device)
            at_risk = torch.from_numpy(risk[indices]).to(self.device)
            self.optimizer.zero_grad(set_to_none=True)
            logits = self.model(x, e, a, lengths_batch)
            per_bin = torch.nn.functional.binary_cross_entropy_with_logits(
                logits, truth, reduction="none"
            )
            loss = (per_bin * at_risk).sum() / at_risk.sum()
            loss.backward()
            self.optimizer.step()
            weight = int(risk[indices].sum())
            total_loss += float(loss.detach()) * weight
            total_weight += weight
        return total_loss / total_weight, len(nodes)

    def state_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "rng": self.torch.get_rng_state(),
            "cuda_rng": self.torch.cuda.get_rng_state_all() if self.device == "cuda" else [],
        }

    def load_state_dict(self, state: dict[str, Any]) -> None:
        self.model.load_state_dict(state["model"])
        self.optimizer.load_state_dict(state["optimizer"])
        self.torch.set_rng_state(state["rng"])
        if self.device == "cuda":
            self.torch.cuda.set_rng_state_all(state["cuda_rng"])

    def save(self, state: dict[str, Any], path: str) -> None:
        self.torch.save(state, path)

    def load(self, path: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.torch.load(path, map_location="cpu", weights_only=True))
