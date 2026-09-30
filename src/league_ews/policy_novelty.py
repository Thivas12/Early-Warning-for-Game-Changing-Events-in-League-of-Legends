"""Independent mathematical checks and prior-loss controls for the novelty claim.

No functions here alter the frozen scheduled-policy experiment. Exact expectation
and score-function gradients are established tools, not inventions of this project.
The temporal score loss is an independently expressed mathematical implementation
of the authors' uniform-threshold wSOL, with each match kept separate.
"""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np

WSOL_REFERENCE = {
    "repository": "https://github.com/edoardolegnaro/ScoreOrientedLosses",
    "commit": "d929f0575833972c33826f1a41114fafb16ccb94",
    "file": "wsol/torch/wsol.py",
    "blob": "4380ee110fcbe78722f0e162d4356b8eba4177a1",
    "scope": "uniform-threshold distribution;prod/max temporal weighting;tss/f1 scores",
}


def _inputs(times: np.ndarray, p: np.ndarray, rewards: np.ndarray, cooldown: int) -> None:
    if (
        times.ndim != 1
        or p.shape != times.shape
        or rewards.shape != times.shape
        or np.any(np.diff(times) <= 0)
        or not np.isfinite(times).all()
        or not np.isfinite(p).all()
        or not np.isfinite(rewards).all()
        or np.any((p < 0) | (p > 1))
        or not np.isfinite(cooldown)
        or cooldown <= 0
    ):
        raise ValueError("Invalid ordered times, probabilities, rewards or cooldown")


def exact_credit(
    times: np.ndarray, p: np.ndarray, rewards: np.ndarray, cooldown: int = 60_000
) -> dict[str, Any]:
    """Forward exclusion and reverse adjoint scans; O(n) after time-bound lookup.

    Returns derivatives with respect to probability AND logit. Probability
    derivatives at 0/1 are polynomial one-sided extensions; logit derivatives
    there equal zero. No sampled-action or future-outcome input is a predictor.
    """
    _inputs(times, p, rewards, cooldown)
    n = len(p)
    left = np.searchsorted(times, times - cooldown, side="right")
    right = np.searchsorted(times, times + cooldown, side="left")
    cumulative = np.zeros(n + 1)
    marginals, available, adjoint = np.zeros(n), np.zeros(n), np.zeros(n)
    for i in range(n):
        available[i] = 1 - (cumulative[i] - cumulative[left[i]])
        marginals[i] = p[i] * available[i]
        cumulative[i + 1] = cumulative[i] + marginals[i]
    suffix = np.zeros(n + 1)
    for i in range(n - 1, -1, -1):
        adjoint[i] = rewards[i] - (suffix[i + 1] - suffix[right[i]])
        suffix[i] = suffix[i + 1] + p[i] * adjoint[i]
    gradient = available * adjoint
    return {
        "utility": float(marginals @ rewards),
        "marginals": marginals,
        "availability": available,
        "adjoint": adjoint,
        "gradient_probabilities": gradient,
        "gradient_logits": gradient * p * (1 - p),
    }


def enumerated_score_gradient(
    times: np.ndarray, p: np.ndarray, rewards: np.ndarray, cooldown: int = 60_000
) -> dict[str, Any]:
    """Enumerate REINFORCE outcomes and variance with an exact mean-return baseline.

    This is a gradient-estimator comparison on a fixed trace, not an RL benchmark.
    It removes action-sampling noise only, not dataset or optimization uncertainty.
    """
    _inputs(times, p, rewards, cooldown)
    if len(p) > 12:
        raise ValueError("Enumeration is limited to twelve decisions")
    weights, returns, scores = [], [], []
    for coins in itertools.product((0, 1), repeat=len(p)):
        z = np.asarray(coins)
        weight = float(np.prod(np.where(z, p, 1 - p)))
        last, reward = -np.inf, 0.0
        score = np.zeros(len(p))
        for i, stamp in enumerate(times):
            if stamp - last < cooldown:
                continue
            score[i] = z[i] - p[i]
            if z[i]:
                last = stamp
                reward += rewards[i]
        weights.append(weight)
        returns.append(reward)
        scores.append(score)
    w, r, score_matrix = np.asarray(weights), np.asarray(returns), np.asarray(scores)
    mean_return = float(w @ r)
    estimates = (r - mean_return)[:, None] * score_matrix
    gradient = (w[:, None] * estimates).sum(0)
    variance = (w[:, None] * (estimates - gradient) ** 2).sum(0)
    return {
        "utility": mean_return,
        "gradient_logits": gradient,
        "single_sample_gradient_variance": variance,
        "probability_mass": float(w.sum()),
    }


def uniform_temporal_score_loss(
    probabilities: Any,
    labels: Any,
    *,
    weights: tuple[float, ...] = (0.5, 0.25, 0.125),
    mode: str = "prod",
    score: str = "tss",
) -> Any:
    """Per-sequence uniform-threshold wSOL objective, averaged across sequences.

    Padded sequences must be sliced before calling. Weight distances are slot
    indices, not elapsed seconds. This diagnostic must not silently cross match
    boundaries or claim irregular-time weighting faithful to the original paper.
    """
    import torch

    if (
        probabilities.ndim != 2
        or labels.shape != probabilities.shape
        or not weights
        or mode not in ("prod", "max")
        or score not in ("tss", "f1")
        or any(not np.isfinite(w) or w <= 0 for w in weights)
        or any(a < b for a, b in itertools.pairwise(weights))
        or (mode == "prod" and sum(weights) >= 1)
        or (mode == "max" and max(weights) >= 1)
    ):
        raise ValueError("Unsupported or invalid temporal score configuration")
    p, y = probabilities, labels.to(probabilities.dtype)
    future_labels, previous_scores = [], []
    for lag in range(1, len(weights) + 1):
        future = torch.zeros_like(y)
        previous = torch.zeros_like(p)
        if lag < p.shape[1]:
            future[:, :-lag] = y[:, lag:]
            previous[:, lag:] = p[:, :-lag]
        future_labels.append(future)
        previous_scores.append(previous)
    future = torch.stack(future_labels, dim=-1)
    past = torch.stack(previous_scores, dim=-1)
    w = torch.as_tensor(weights, dtype=p.dtype, device=p.device)
    if mode == "prod":
        fp_discount = (future * w).sum(-1)
        fn_discount = ((past - p[..., None]).clamp(min=0) * w).sum(-1)
    else:
        fp_discount = (future * w).max(-1).values
        # Layer-cake form of the weighted running-maximum integral.
        weight_steps = w - torch.cat((w[1:], w.new_zeros(1)))
        fn_discount = ((past.cummax(-1).values - p[..., None]).clamp(min=0) * weight_steps).sum(-1)
    tp, tn = (y * p).sum(-1), ((1 - y) * (1 - p)).sum(-1)
    fp = ((1 - fp_discount) * (1 - y) * p).sum(-1)
    fn = (y * (1 - p - fn_discount)).sum(-1)

    def ratio(a: Any, b: Any) -> Any:
        denominator = torch.where(b == 0, torch.ones_like(b), b)
        return torch.where(b == 0, torch.zeros_like(a), a / denominator)

    metric = (
        ratio(2 * tp, 2 * tp + fp + fn)
        if score == "f1"
        else (ratio(tp, tp + fn) + ratio(tn, tn + fp) - 1)
    )
    return (1 - metric).mean()


def two_decision_plan(timely_probabilities: np.ndarray, wrong_cost: float = 0.25) -> np.ndarray:
    """Bayes planner for the explicit two-opportunity conflict population.

    Both opportunities lie inside one cooldown. The planner knows both conditional
    event probabilities from the specified population, but not the realized event.
    This is an established decision-theory control, not a reproduction of OTI.
    """
    if (
        timely_probabilities.ndim != 2
        or timely_probabilities.shape[1] != 2
        or not np.isfinite(timely_probabilities).all()
        or np.any((timely_probabilities < 0) | (timely_probabilities > 1))
        or not np.isfinite(wrong_cost)
        or wrong_cost < 0
    ):
        raise ValueError("Expected two conditional probabilities per context")
    rewards = timely_probabilities - wrong_cost * (1 - timely_probabilities)
    choice = np.column_stack((np.zeros(len(rewards)), rewards)).argmax(1)
    return np.column_stack((choice == 1, choice == 2)).astype(float)


def pointwise_envelope(alpha: float = 0.6, budget: float = 0.25) -> dict[str, float]:
    """Analytic bound for the declared balanced two-context population, alpha>=.5.

    Any policy using only the current event probability has a common first-action
    probability r in both contexts. It receives the most favorable second-stage
    choices (always in C, never in D). This upper bounds the entire score-only
    family, not just our finite calibration grid. It does not bound planners.
    """
    if not 0.5 <= alpha < 1 or not np.isfinite(budget) or budget < 0:
        raise ValueError("Require .5 <= alpha < 1 and finite nonnegative budget")
    r = min(1.0, budget / (1 - alpha))
    hits = 0.5 * (1 + (2 * alpha - 1) * r)
    return {
        "first_action_probability": r,
        "timely_hits_per_episode": hits,
        "event_recall_upper_bound": hits / (0.5 * (1 + alpha)),
        "non_timely_per_episode": (1 - alpha) * r,
    }
