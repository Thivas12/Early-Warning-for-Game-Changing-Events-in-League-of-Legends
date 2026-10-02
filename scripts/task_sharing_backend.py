"""Independent event training with the frozen LeagueEWS encoder and RNG stream."""

from __future__ import annotations

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.constants import EVENTS
from league_ews.notebook_ews import NotebookEWSBackend, right_pad_sequences


class IndependentEventBackend(NotebookEWSBackend):
    """Keep initialization/dropout identical; only one event supervises the encoder.

    The two unused heads stay allocated and frozen. Their original forward calls
    preserve dropout RNG consumption, including Baron dropout for the other tasks.
    Their predictions are never used or saved as trained event predictions.
    """

    def __init__(self, seed: int, device: str = "cpu", *, event: str):
        if event not in EVENTS:
            raise ValueError("Unknown League event")
        super().__init__(seed, device, family="leagueews")
        self.event = event
        self.event_index = EVENTS.index(event)
        self.columns = slice(self.event_index * 4, self.event_index * 4 + 4)
        self.loss_weight = (1.0, 2.0, 2.5)[self.event_index]
        for index, head in enumerate(self.model.heads):
            if index != self.event_index:
                head.requires_grad_(False)
        self.optimizer = self.torch.optim.AdamW(
            (p for p in self.model.parameters() if p.requires_grad), lr=1e-4, weight_decay=1e-4
        )

    def train_shard(
        self, inputs: np.ndarray, mask: np.ndarray, targets: np.ndarray, *, seed: int
    ) -> tuple[float, int]:
        if targets.shape != (len(inputs), len(LABELS)):
            raise ValueError("Expected twelve target columns")
        selected = targets[:, self.columns]
        if not np.isin(selected, (0, 1)).all():
            raise ValueError("Expected four binary selected-event targets")
        torch = self.torch
        packed, lengths = right_pad_sequences(inputs, mask)
        if not len(packed) or not np.isfinite(packed).all():
            raise ValueError("Empty or nonfinite observed features")
        self.model.train()
        order = np.random.default_rng(seed).permutation(len(inputs))
        total = 0.0
        for start in range(0, len(order), 256):
            indices = order[start : start + 256]
            self.optimizer.zero_grad(set_to_none=True)
            logits = self.model(
                torch.from_numpy(packed[indices]).to(self.device),
                torch.from_numpy(lengths[indices]),
            )[:, self.columns]
            truth = torch.from_numpy(selected[indices].astype(np.float32)).to(self.device)
            loss = self.loss_weight * torch.nn.functional.binary_cross_entropy_with_logits(
                logits, truth
            )
            loss.backward()
            self.optimizer.step()
            total += float(loss.detach()) * len(indices)
        return total / len(inputs), len(inputs)

    def predict_shard(self, inputs: np.ndarray, mask: np.ndarray) -> np.ndarray:
        return super().predict_shard(inputs, mask)[:, self.columns]
