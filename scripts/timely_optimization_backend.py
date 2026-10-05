"""Fixed loss-weight and PCGrad factorial controls for useful-lead League targets.

These are established optimization controls, not a proposed new algorithm.
All variants retain the original encoder, optimizer, dropout and batch stream.
"""

from __future__ import annotations

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.notebook_ews import NotebookEWSBackend, right_pad_sequences
from scripts.pcgrad_backend import projected_sum

VARIANTS = {
    "original_sum": {"weights": (1.0, 2.0, 2.5), "aggregation": "sum"},
    "equal_sum": {"weights": (11 / 6,) * 3, "aggregation": "sum"},
    "original_pcgrad": {"weights": (1.0, 2.0, 2.5), "aggregation": "pcgrad"},
    "equal_pcgrad": {"weights": (11 / 6,) * 3, "aggregation": "pcgrad"},
}
NEW_VARIANTS = ("equal_sum", "original_pcgrad", "equal_pcgrad")


def backward(backend, losses, projection_rng):
    """Project shared gradients only; retain ordinary weighted head gradients."""
    torch = backend.torch
    weighted = losses * losses.new_tensor(backend.weights)
    if backend.aggregation == "sum":
        weighted.sum().backward()
    else:
        named = list(backend.model.named_parameters())
        parameters = [p for _, p in named]
        shared_indices = [i for i, (name, _) in enumerate(named) if not name.startswith("heads.")]
        private_indices = [i for i, (name, _) in enumerate(named) if name.startswith("heads.")]
        per_task = [
            torch.autograd.grad(weighted[e], parameters, retain_graph=e < 2) for e in range(3)
        ]
        shared = torch.stack(
            [torch.cat([gradient[i].flatten() for i in shared_indices]) for gradient in per_task]
        )
        orders = [projection_rng.permutation([j for j in range(3) if j != i]) for i in range(3)]
        combined = projected_sum(shared, orders)
        offset = 0
        for i in shared_indices:
            parameter = parameters[i]
            parameter.grad = combined[offset : offset + parameter.numel()].view_as(parameter)
            offset += parameter.numel()
        for i in private_indices:
            parameters[i].grad = sum(gradient[i] for gradient in per_task)
    return weighted.sum()


class TimelyOptimizationBackend(NotebookEWSBackend):
    def __init__(self, seed, device="cpu", *, variant):
        if variant not in VARIANTS:
            raise ValueError("Unknown optimization control")
        super().__init__(seed, device, family="leagueews")
        self.variant = variant
        self.weights = VARIANTS[variant]["weights"]
        self.aggregation = VARIANTS[variant]["aggregation"]

    def train_shard(self, inputs, mask, targets, *, seed):
        if targets.shape != (len(inputs), len(LABELS)) or not np.isin(targets, (0, 1)).all():
            raise ValueError("Expected twelve binary League targets")
        torch = self.torch
        packed, lengths = right_pad_sequences(inputs, mask)
        if not len(packed) or not np.isfinite(packed).all():
            raise ValueError("Empty or nonfinite observed features")
        self.model.train()
        order = np.random.default_rng(seed).permutation(len(inputs))
        projection_rng = np.random.default_rng([seed, 20261002])
        total = 0.0
        for start in range(0, len(order), 256):
            indices = order[start : start + 256]
            self.optimizer.zero_grad(set_to_none=True)
            logits = self.model(
                torch.from_numpy(packed[indices]).to(self.device),
                torch.from_numpy(lengths[indices]),
            )
            truth = torch.from_numpy(targets[indices].astype(np.float32)).to(self.device)
            losses = (
                torch.nn.functional.binary_cross_entropy_with_logits(
                    logits, truth, reduction="none"
                )
                .reshape(-1, 3, 4)
                .mean((0, 2))
            )
            loss = backward(self, losses, projection_rng)
            self.optimizer.step()
            total += float(loss.detach()) * len(indices)
        return total / len(inputs), len(inputs)
