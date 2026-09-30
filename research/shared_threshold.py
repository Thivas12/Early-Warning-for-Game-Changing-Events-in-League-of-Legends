"""Known sorted-increment extension applied to deterministic alarm counts."""

import numpy as np
import torch
from numba import njit


@njit(cache=True)
def count_increments(orders, ticks, labels, lengths):
    batch, width = orders.shape
    hit_grad = np.zeros((batch, width), dtype=np.float64)
    wrong_grad = np.zeros((batch, width), dtype=np.float64)
    for b in range(batch):
        n = lengths[b]
        rank = np.zeros(width, dtype=np.int64)
        for k in range(n):
            rank[orders[b, k]] = k
        previous_hits, previous_wrong = 0.0, 0.0
        for k in range(n):
            hits, wrong, last = 0.0, 0.0, -9223372036854775807
            for j in range(n):
                if rank[j] <= k and (last < 0 or ticks[b, j] - last >= 1800):
                    last = ticks[b, j]
                    hits += labels[b, j]
                    wrong += 1 - labels[b, j]
            hit_grad[b, orders[b, k]] = hits - previous_hits
            wrong_grad[b, orders[b, k]] = wrong - previous_wrong
            previous_hits, previous_wrong = hits, wrong
    return hit_grad, wrong_grad


def shared_threshold_counts(p, ticks, y, valid):
    """Integrate one shared uniform threshold; gradients exact off score ties."""
    if p.device.type != "cpu":
        raise ValueError("This frozen implementation uses CPU")
    mask = valid.detach().numpy()
    if np.any(np.diff(mask.astype(np.int8), axis=1) > 0):
        raise ValueError("Valid rows must precede padding")
    scores = np.where(mask, p.detach().numpy(), -np.inf)
    orders = np.argsort(-scores, axis=1, kind="stable")
    hit_grad, wrong_grad = count_increments(
        orders, ticks.detach().numpy(), y.detach().numpy(), mask.sum(1)
    )
    hit_grad = torch.from_numpy(hit_grad).to(p.dtype)
    wrong_grad = torch.from_numpy(wrong_grad).to(p.dtype)
    return (p * hit_grad).sum(1), (p * wrong_grad).sum(1)
