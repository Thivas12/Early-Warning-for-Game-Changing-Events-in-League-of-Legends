"""PCGrad on the unchanged LeagueEWS shared encoder; ordinary event-head gradients.

Yu et al., NeurIPS 2020, Algorithm 1: sequential random-order projections onto
original other-task gradients, then SUM (not mean). Original loss weights remain.
"""

from __future__ import annotations

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.notebook_ews import NotebookEWSBackend, right_pad_sequences


def projected_sum(gradients, orders):
    """Equivalent to vector PCGrad, computed in a three-task Gram basis.

    Original gradients remain fixed; each row's coefficients are projected in
    the supplied order. Zero-norm tasks contribute no projection. This does not
    promise final pairwise nonnegative cosines for three or more tasks.
    """
    gram = gradients @ gradients.T
    coefficients = gram.new_zeros(gram.shape)
    coefficients.fill_diagonal_(1)
    for i, order in enumerate(orders):
        for j in order:
            dot = coefficients[i] @ gram[:, j]
            denominator = gram[j, j].clamp_min(1e-30)
            coefficients[i, j] -= dot.clamp_max(0) / denominator
    return coefficients.sum(0) @ gradients


class PCGradBackend(NotebookEWSBackend):
    """Same forward/dropout/optimizer; only shared-gradient aggregation changes."""

    def __init__(self, seed: int, device: str = "cpu"):
        super().__init__(seed, device, family="leagueews")

    def train_shard(self, inputs, mask, targets, *, seed):
        if targets.shape != (len(inputs), len(LABELS)) or not np.isin(targets, (0, 1)).all():
            raise ValueError("Expected twelve binary League targets")
        torch = self.torch
        packed, lengths = right_pad_sequences(inputs, mask)
        if not len(packed) or not np.isfinite(packed).all():
            raise ValueError("Empty or nonfinite observed features")
        named = list(self.model.named_parameters())
        parameters = [p for _, p in named]
        shared_indices = [i for i, (n, _) in enumerate(named) if not n.startswith("heads.")]
        private_indices = [i for i, (n, _) in enumerate(named) if n.startswith("heads.")]
        self.model.train()
        order = np.random.default_rng(seed).permutation(len(inputs))
        # Separate deterministic stream; neither model/dropout nor batch order is changed.
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
            weighted = losses * losses.new_tensor([1.0, 2.0, 2.5])
            per_task = [
                torch.autograd.grad(weighted[e], parameters, retain_graph=e < 2) for e in range(3)
            ]
            shared = torch.stack(
                [
                    torch.cat([gradient[i].flatten() for i in shared_indices])
                    for gradient in per_task
                ]
            )
            orders = [projection_rng.permutation([j for j in range(3) if j != i]) for i in range(3)]
            combined = projected_sum(shared, orders)
            offset = 0
            for i in shared_indices:
                p = parameters[i]
                p.grad = combined[offset : offset + p.numel()].view_as(p)
                offset += p.numel()
            for i in private_indices:
                parameters[i].grad = sum(gradient[i] for gradient in per_task)
            self.optimizer.step()
            total += float(weighted.sum().detach()) * len(indices)
        return total / len(inputs), len(inputs)
