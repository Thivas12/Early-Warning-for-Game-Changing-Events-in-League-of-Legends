"""Two-stream exploratory graph/spatial hazard model over real observation frames.

This backend is separate from the registered M1 fit and its sealed test.
"""

from __future__ import annotations

import importlib
import os
from typing import Any, cast

import numpy as np

from league_ews.hazards import risk_at_horizons
from league_ews.m1_backend import _batches, at_risk_mask, right_pad_graphs
from league_ews.m2_spatial import SPATIAL_FEATURES, spatial_summary

MODES = ("gated", "ungated", "spatial-only")
SPATIAL_SCALES = np.asarray(
    [10, 10, 1, 1, 1, 1, 1.5, 1, 1.5, 1, 1.5, 1.5, 1.5, 1.5, 1, 1, 1, 1, 1, 1, 50, 50, 8, 8],
    dtype=np.float32,
)


def spatial_inputs(
    nodes: np.ndarray, edges: np.ndarray, mask: np.ndarray, ages: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Fixed, outcome-blind scales and an explicit two-team coverage/age gate."""

    raw = spatial_summary(nodes, edges, mask, ages)
    if len(SPATIAL_FEATURES) != len(SPATIAL_SCALES) or np.any(SPATIAL_SCALES <= 0):
        raise ValueError("M2 spatial scale contract differs from source features")
    scaled = np.ascontiguousarray(raw / SPATIAL_SCALES, dtype=np.float32)
    gate = np.ascontiguousarray(raw[:, [0, 1, 7, 23]] / [10, 10, 1, 8], dtype=np.float32)
    return scaled, gate


class TorchM2Backend:
    """M1 graph stream plus a small spatial stream with event-specific gates."""

    def __init__(self, seed: int, device: str = "cpu", *, mode: str = "gated") -> None:
        if device not in ("cpu", "cuda") or mode not in MODES:
            raise ValueError("Unknown M2 device or fusion control")
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        try:
            torch = importlib.import_module("torch")
        except ImportError as exc:
            raise RuntimeError("Install the optional neural dependency before M2 training") from exc
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable in this PyTorch/WSL runtime")
        from league_ews.m1_backend import TorchM1Backend

        graph_backend = TorchM1Backend(seed, device)
        self.torch = torch
        self.device = device
        self.version = str(torch.__version__)
        self.mode = mode

        class HybridHazards(torch.nn.Module):  # type: ignore[name-defined,misc]
            def __init__(self) -> None:
                super().__init__()
                self.graph = graph_backend.model
                self.spatial = torch.nn.Sequential(
                    torch.nn.Linear(len(SPATIAL_FEATURES), 32),
                    torch.nn.ReLU(),
                    torch.nn.Dropout(0.1),
                    torch.nn.Linear(32, 18),
                )
                self.gate = torch.nn.Linear(4, 3)

            def forward(
                self, nodes: Any, edges: Any, ages: Any, lengths: Any, spatial: Any, coverage: Any
            ) -> Any:
                spatial_logits = self.spatial(spatial).reshape(-1, 3, 6)
                if mode == "spatial-only":
                    return spatial_logits
                graph_logits = self.graph(nodes, edges, ages, lengths)
                if mode == "ungated":
                    return (graph_logits + spatial_logits) / 2
                weight = torch.sigmoid(self.gate(coverage)).unsqueeze(-1)
                return weight * graph_logits + (1 - weight) * spatial_logits

        self.model = HybridHazards().to(device)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=0.001, weight_decay=0.01)

    def _inputs(
        self,
        raw_nodes: np.ndarray,
        normalized_nodes: np.ndarray,
        edges: np.ndarray,
        mask: np.ndarray,
        ages: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if raw_nodes.shape != normalized_nodes.shape:
            raise ValueError("M2 graph and spatial streams have different observations")
        spatial, coverage = spatial_inputs(raw_nodes, edges, mask, ages)
        graph, packed_edges, packed_ages, lengths = right_pad_graphs(
            normalized_nodes, edges, mask, ages
        )
        return graph, packed_edges, packed_ages, lengths, spatial, coverage

    def train_shard(
        self,
        raw_nodes: np.ndarray,
        normalized_nodes: np.ndarray,
        edges: np.ndarray,
        mask: np.ndarray,
        ages: np.ndarray,
        hazards: np.ndarray,
        *,
        seed: int,
    ) -> tuple[float, int]:
        """Use M1's at-risk likelihood and the same batch, optimizer and seed schedule."""

        x, e, a, lengths, spatial, coverage = self._inputs(
            raw_nodes, normalized_nodes, edges, mask, ages
        )
        risk = at_risk_mask(hazards)
        if hazards.shape[0] != len(x):
            raise ValueError("M2 hazard targets disagree with the graph row count")
        self.model.train()
        rng = np.random.default_rng(seed)
        total_loss = 0.0
        total_weight = 0
        for indices in _batches(rng.permutation(len(x)), 256):
            torch = self.torch
            graph_batch = torch.from_numpy(x[indices]).to(self.device)
            edge_batch = torch.from_numpy(e[indices]).to(self.device)
            ages_batch = torch.from_numpy(a[indices]).to(self.device)
            spatial_batch = torch.from_numpy(spatial[indices]).to(self.device)
            coverage_batch = torch.from_numpy(coverage[indices]).to(self.device)
            truth = torch.from_numpy(hazards[indices]).to(self.device)
            at_risk = torch.from_numpy(risk[indices]).to(self.device)
            self.optimizer.zero_grad(set_to_none=True)
            logits = self.model(
                graph_batch,
                edge_batch,
                ages_batch,
                torch.from_numpy(lengths[indices]),
                spatial_batch,
                coverage_batch,
            )
            per_bin = torch.nn.functional.binary_cross_entropy_with_logits(
                logits, truth, reduction="none"
            )
            loss = (per_bin * at_risk).sum() / at_risk.sum()
            loss.backward()
            self.optimizer.step()
            weight = int(risk[indices].sum())
            total_loss += float(loss.detach()) * weight
            total_weight += weight
        return total_loss / total_weight, len(x)

    def predict_shard(
        self,
        raw_nodes: np.ndarray,
        normalized_nodes: np.ndarray,
        edges: np.ndarray,
        mask: np.ndarray,
        ages: np.ndarray,
    ) -> np.ndarray:
        """Return 12 ordered event/horizon risks at the genuine prediction frames."""

        x, e, a, lengths, spatial, coverage = self._inputs(
            raw_nodes, normalized_nodes, edges, mask, ages
        )
        self.model.eval()
        chunks: list[np.ndarray] = []
        with self.torch.inference_mode():
            for start in range(0, len(x), 256):
                end = min(start + 256, len(x))
                logits = self.model(
                    self.torch.from_numpy(x[start:end]).to(self.device),
                    self.torch.from_numpy(e[start:end]).to(self.device),
                    self.torch.from_numpy(a[start:end]).to(self.device),
                    self.torch.from_numpy(lengths[start:end]),
                    self.torch.from_numpy(spatial[start:end]).to(self.device),
                    self.torch.from_numpy(coverage[start:end]).to(self.device),
                )
                hazards = self.torch.sigmoid(logits).cpu().numpy()
                chunks.append(
                    risk_at_horizons(hazards, bin_seconds=10, horizons_seconds=(10, 20, 30, 60))
                    .reshape(end - start, 12)
                    .astype(np.float32)
                )
        if not chunks:
            raise ValueError("M2 prediction shard is empty")
        result = np.concatenate(chunks)
        if not np.isfinite(result).all() or result.shape != (len(x), 12):
            raise ValueError("M2 predictions differ from the hazard output contract")
        return result

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
