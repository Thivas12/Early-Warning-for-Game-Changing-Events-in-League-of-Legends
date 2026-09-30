"""LeagueEWS descendant of the MSc notebook, with explicit history masking.

The original TCN/SE + stacked BiGRU + cross-attention architecture is retained.
LayerNorm replaces BatchNorm so padded timesteps do not enter batch statistics.
Bidirectionality operates only inside an already observed history window.
"""

from __future__ import annotations

import importlib
import os
from typing import Any

import numpy as np

from league_ews.b4_backend import right_pad_sequences
from league_ews.b4_sequence import SEQUENCE_FEATURES
from league_ews.baseline_floor import LABELS

# Start with the original architecture so the one-shard CUDA canary exercises it.
FAMILIES = ("leagueews", "gru", "tcn", "snapshot")
MODEL_SPEC = {
    "tcn_filters": [80, 160, 160],
    "tcn_dilations": [1, 2, 4],
    "tcn_kernel": 3,
    "squeeze_excitation_ratio": 8,
    "gru_units_per_direction": 160,
    "gru_layers": 2,
    "attention_heads": 4,
    "attention_key_dimension": 64,
    "representation_width": 128,
    "shared_dense": [512, 256],
    "shared_dropout": 0.5,
    "event_loss_weights": [1.0, 2.0, 2.5],
    "horizons_seconds": [10, 20, 30, 60],
    "normalization": "per-token-layernorm;masked-squeeze-excitation",
}


def make_model(torch: Any, family: str, channels: int) -> Any:
    if family not in FAMILIES:
        raise ValueError("Unknown notebook continuation model")
    nn = torch.nn

    def mask_values(x: Any, valid: Any) -> Any:
        return x.masked_fill(~valid.unsqueeze(-1), 0)

    class ResidualTCN(nn.Module):  # type: ignore[name-defined,misc]
        def __init__(self, incoming: int, outgoing: int, dilation: int) -> None:
            super().__init__()
            self.padding = 2 * dilation
            self.first = nn.Conv1d(incoming, outgoing, 3, dilation=dilation)
            self.second = nn.Conv1d(outgoing, outgoing, 3, dilation=dilation)
            self.norm1 = nn.LayerNorm(outgoing)
            self.norm2 = nn.LayerNorm(outgoing)
            self.dropout = nn.Dropout(0.15)
            self.skip = nn.Linear(incoming, outgoing) if incoming != outgoing else nn.Identity()
            self.squeeze = nn.Sequential(
                nn.Linear(outgoing, outgoing // 8),
                nn.ReLU(),
                nn.Linear(outgoing // 8, outgoing),
                nn.Sigmoid(),
            )

        def convolution(self, layer: Any, x: Any) -> Any:
            padded = torch.nn.functional.pad(x.transpose(1, 2), (self.padding, 0))
            return layer(padded).transpose(1, 2)

        def forward(self, x: Any, valid: Any) -> Any:
            y = mask_values(
                self.dropout(self.norm1(torch.relu(self.convolution(self.first, x)))), valid
            )
            y = mask_values(self.norm2(self.convolution(self.second, y)), valid)
            average = y.sum(1) / valid.sum(1, keepdim=True)
            y = y * self.squeeze(average).unsqueeze(1)
            return mask_values(torch.relu(self.skip(x) + y), valid)

    class CrossAttention(nn.Module):  # type: ignore[name-defined,misc]
        def __init__(self, memory_width: int) -> None:
            super().__init__()
            # Keras MHA(num_heads=4, key_dim=64) uses a 256-wide internal projection.
            self.query = nn.Linear(128, 256)
            self.key = nn.Linear(memory_width, 256)
            self.value = nn.Linear(memory_width, 256)
            self.output = nn.Linear(256, 128)
            self.norm = nn.LayerNorm(128)

        def forward(self, query: Any, memory: Any, valid: Any) -> Any:
            # Explicit projections above; use functional attention to avoid double projection.
            batch, steps, _ = query.shape
            q = self.query(query).reshape(batch, steps, 4, 64).transpose(1, 2)
            k = self.key(memory).reshape(batch, steps, 4, 64).transpose(1, 2)
            v = self.value(memory).reshape(batch, steps, 4, 64).transpose(1, 2)
            logits = q @ k.transpose(-2, -1) / 8.0
            logits = logits.masked_fill(~valid[:, None, None, :], -torch.inf)
            attended = (logits.softmax(-1) @ v).transpose(1, 2).reshape(batch, steps, 256)
            return mask_values(self.norm(query + self.output(attended)), valid)

    class LeagueEWS(nn.Module):  # type: ignore[name-defined,misc]
        def __init__(self) -> None:
            super().__init__()
            if family in ("tcn", "leagueews"):
                self.tcn = nn.ModuleList(
                    [
                        ResidualTCN(channels, 80, 1),
                        ResidualTCN(80, 160, 2),
                        ResidualTCN(160, 160, 4),
                    ]
                )
                self.tcn_projection = nn.Linear(160, 128)
            if family in ("gru", "leagueews"):
                self.gru1 = nn.GRU(channels, 160, batch_first=True, bidirectional=True)
                self.gru2 = nn.GRU(320, 160, batch_first=True, bidirectional=True)
                self.gru_dropout = nn.Dropout(0.3)
            if family == "gru":
                self.gru_projection = nn.Linear(320, 128)
            if family == "leagueews":
                self.cross_gru = CrossAttention(320)
                self.cross_input = CrossAttention(channels)
                self.self_attention = CrossAttention(128)
                self.feed_forward = nn.Sequential(
                    nn.Linear(128, 256), nn.ReLU(), nn.Linear(256, 128)
                )
            if family == "snapshot":
                self.snapshot = nn.Sequential(nn.Linear(channels, 128), nn.ReLU())
            else:
                self.pool_score = nn.Linear(128, 1)
            self.shared = nn.Sequential(
                nn.Linear(128, 512),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(512, 256),
                nn.ReLU(),
            )
            self.baron_dropout = nn.Dropout(0.5)
            self.heads = nn.ModuleList([nn.Linear(256, 4) for _ in range(3)])

        def recurrent(self, x: Any, lengths: Any) -> Any:
            for layer in (self.gru1, self.gru2):
                packed = nn.utils.rnn.pack_padded_sequence(
                    self.gru_dropout(x),
                    lengths.cpu(),
                    batch_first=True,
                    enforce_sorted=False,
                )
                packed, _ = layer(packed)
                x, _ = nn.utils.rnn.pad_packed_sequence(
                    packed, batch_first=True, total_length=x.shape[1]
                )
            return x

        def forward(self, x: Any, lengths: Any) -> Any:
            valid = (
                torch.arange(x.shape[1], device=x.device)[None, :] < lengths.to(x.device)[:, None]
            )
            x = mask_values(x, valid)
            if family == "snapshot":
                pooled = self.snapshot(
                    x[torch.arange(len(x), device=x.device), lengths.to(x.device) - 1]
                )
            else:
                if family in ("tcn", "leagueews"):
                    temporal = x
                    for block in self.tcn:
                        temporal = block(temporal, valid)
                    temporal = mask_values(torch.relu(self.tcn_projection(temporal)), valid)
                if family in ("gru", "leagueews"):
                    recurrent = self.recurrent(x, lengths)
                if family == "tcn":
                    representation = temporal
                elif family == "gru":
                    representation = mask_values(torch.relu(self.gru_projection(recurrent)), valid)
                else:
                    representation = self.cross_gru(temporal, recurrent, valid)
                    representation = self.cross_input(representation, x, valid)
                    representation = self.self_attention(representation, representation, valid)
                    representation = mask_values(
                        representation + self.feed_forward(representation), valid
                    )
                weights = torch.tanh(self.pool_score(representation)).squeeze(-1)
                weights = weights.masked_fill(~valid, -torch.inf).softmax(1)
                pooled = (representation * weights.unsqueeze(-1)).sum(1)
            shared = self.shared(pooled)
            return torch.stack(
                [
                    head(self.baron_dropout(shared) if event == 0 else shared)
                    for event, head in enumerate(self.heads)
                ],
                dim=1,
            ).reshape(-1, len(LABELS))

    return LeagueEWS()


class NotebookEWSBackend:
    """Fixed family/seed, bounded batches, deterministic resumable training."""

    def __init__(self, seed: int, device: str = "cpu", *, family: str = "leagueews") -> None:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch = importlib.import_module("torch")
        if device not in ("cpu", "cuda") or (device == "cuda" and not torch.cuda.is_available()):
            raise RuntimeError("Requested device is unavailable; no silent CPU fallback")
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(seed)
        if device == "cuda":
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.benchmark = False
        self.torch, self.device, self.family = torch, device, family
        self.version = str(torch.__version__)
        self.model = make_model(torch, family, len(SEQUENCE_FEATURES)).to(device)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-4, weight_decay=1e-4)

    def train_shard(
        self, inputs: np.ndarray, mask: np.ndarray, targets: np.ndarray, *, seed: int
    ) -> tuple[float, int]:
        if targets.shape != (len(inputs), len(LABELS)) or not np.isin(targets, (0, 1)).all():
            raise ValueError("Expected twelve binary League targets")
        torch = self.torch
        packed, lengths = right_pad_sequences(inputs, mask)
        if not np.isfinite(packed).all():
            raise ValueError("Nonfinite observed features")
        self.model.train()
        order = np.random.default_rng(seed).permutation(len(inputs))
        total = 0.0
        for start in range(0, len(order), 256):
            indices = order[start : start + 256]
            self.optimizer.zero_grad(set_to_none=True)
            logits = self.model(
                torch.from_numpy(packed[indices]).to(self.device),
                torch.from_numpy(lengths[indices]),
            )
            truth = torch.from_numpy(targets[indices].astype(np.float32)).to(self.device)
            losses = torch.nn.functional.binary_cross_entropy_with_logits(
                logits, truth, reduction="none"
            )
            per_event = losses.reshape(-1, 3, 4).mean(dim=(0, 2))
            loss = (per_event * torch.tensor([1.0, 2.0, 2.5], device=self.device)).sum()
            loss.backward()
            self.optimizer.step()
            total += float(loss.detach()) * len(indices)
        return total / len(inputs), len(inputs)

    def predict_shard(self, inputs: np.ndarray, mask: np.ndarray) -> np.ndarray:
        packed, lengths = right_pad_sequences(inputs, mask)
        if not len(packed) or not np.isfinite(packed).all():
            raise ValueError("Empty or nonfinite prediction input")
        self.model.eval()
        scores = []
        with self.torch.inference_mode():
            for start in range(0, len(packed), 256):
                end = start + 256
                logits = self.model(
                    self.torch.from_numpy(packed[start:end]).to(self.device),
                    self.torch.from_numpy(lengths[start:end]),
                )
                scores.append(self.torch.sigmoid(logits).cpu().numpy())
        return np.concatenate(scores)

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
