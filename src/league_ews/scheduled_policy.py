"""Causal clock actions and exact alarm marginals under a refractory period.

The recurrence is a standard exclusion/renewal identity, not a new theorem.
It is exact only for exogenous traces and action probabilities which do not
otherwise depend on the sampled action history. Never condition on hidden events.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

COOLDOWN_MS = 60_000
STEP_MS = 10_000
MAX_AGE_MS = 60_000


@dataclass(frozen=True)
class Decisions:
    times: np.ndarray
    rows: np.ndarray
    ages: np.ndarray
    timely: np.ndarray
    late: np.ndarray
    events: int
    opportunities: int


def decision_trace(
    times: tuple[int, ...], events: tuple[int, ...], *, frame_only: bool = False
) -> Decisions:
    """Separate causal input selection from retrospective reward assignment.

    A terminal observation ends the trace; it is not an input predicting its end.
    Clock ticks use the last arrived observation, with no interpolation. An event
    between observations neither refreshes inputs nor suppresses an alarm.
    """
    t, e = np.asarray(times, dtype=np.int64), np.asarray(events, dtype=np.int64)
    if (
        not len(t)
        or t[0] < 0
        or np.any(np.diff(t) <= 0)
        or np.any(e < 0)
        or np.any(np.diff(e) <= 0)
        or (len(e) and e[-1] > t[-1])
    ):
        raise ValueError("Expected ordered, complete observed match")
    # The last observation is treated as the observable stop signal for ALL methods.
    ticks = (
        t[:-1]
        if frame_only
        else np.arange(((t[0] + STEP_MS - 1) // STEP_MS) * STEP_MS, t[-1], STEP_MS)
    )
    rows = np.searchsorted(t, ticks, side="right") - 1
    ages = ticks - t[rows]
    keep = ages < MAX_AGE_MS
    ticks, rows, ages = ticks[keep], rows[keep], ages[keep]
    nxt = np.searchsorted(e, ticks, side="right")
    delays = np.full(len(ticks), np.iinfo(np.int64).max, dtype=np.int64)
    present = nxt < len(e)
    delays[present] = e[nxt[present]] - ticks[present]
    timely = (delays >= 20_000) & (delays <= 60_000)
    late = (delays > 0) & (delays < 20_000)
    opportunities = sum(
        bool(np.any((ticks >= onset - 60_000) & (ticks <= onset - 20_000))) for onset in e
    )
    return Decisions(ticks, rows, ages, timely, late, len(e), opportunities)


def exclusion_matrix(times: Any, valid: Any) -> Any:
    """Torch batch mask B[j,i] = 1 when an earlier alarm i blocks decision j."""
    delta = times[:, :, None] - times[:, None, :]
    return (delta > 0) & (delta < COOLDOWN_MS) & valid[:, :, None] & valid[:, None, :]


def torch_marginals(probabilities: Any, blocked: Any) -> Any:
    """Differentiable batched triangular solve: (I + diag(p) B) m = p."""
    import torch

    n = probabilities.shape[-1]
    matrix = torch.eye(n, device=probabilities.device, dtype=probabilities.dtype)
    matrix = matrix + probabilities[:, :, None] * blocked.to(probabilities.dtype)
    return torch.linalg.solve_triangular(matrix, probabilities[:, :, None], upper=False)[:, :, 0]


def marginal_counts(traces: list[Decisions], probabilities: list[np.ndarray]) -> np.ndarray:
    """Exact expected counts [events, matched, timely, alerts, false, opportunities].

    Because cooldown >= matching horizon, distinct emitted alarms cannot claim
    the same event. Therefore summing marginal timely credit is event recall,
    including for dense event sequences (credit always goes to the next event).
    """
    if len(traces) != len(probabilities) or not traces:
        raise ValueError("Expected one probability vector per trace")
    width = max(len(t.times) for t in traces)
    probs = np.zeros((len(traces), width), dtype=np.float64)
    left = np.zeros((len(traces), width), dtype=np.int64)
    timely, late = np.zeros_like(probs), np.zeros_like(probs)
    for i, (trace, p) in enumerate(zip(traces, probabilities, strict=True)):
        n = len(trace.times)
        if p.shape != (n,) or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
            raise ValueError("Invalid action probabilities")
        probs[i, :n] = p
        left[i, :n] = np.searchsorted(trace.times, trace.times - COOLDOWN_MS, side="right")
        left[i, n:] = np.arange(n, width)
        timely[i, :n], late[i, :n] = trace.timely, trace.late
    cumulative = np.zeros((len(traces), width + 1), dtype=np.float64)
    marginals = np.zeros_like(probs)
    batch = np.arange(len(traces))
    for j in range(width):
        available = 1 - (cumulative[:, j] - cumulative[batch, left[:, j]])
        marginals[:, j] = probs[:, j] * np.clip(available, 0, 1)
        cumulative[:, j + 1] = cumulative[:, j] + marginals[:, j]
    hits = (marginals * timely).sum(axis=1)
    late_hits = (marginals * late).sum(axis=1)
    alerts = marginals.sum(axis=1)
    return np.column_stack(
        (
            [t.events for t in traces],
            hits + late_hits,
            hits,
            alerts,
            np.maximum(alerts - hits - late_hits, 0),
            [t.opportunities for t in traces],
        )
    )


def summary(counts: np.ndarray) -> dict[str, Any]:
    events, matched, timely, alerts, false, opportunities = counts.sum(axis=0)
    return {
        "matches": len(counts),
        "events": int(events),
        "expected_timely_events": float(timely),
        "timely_recall": float(timely / events) if events else None,
        "expected_alerts": float(alerts),
        "false_per_match": float(false / len(counts)),
        "late_per_match": float((matched - timely) / len(counts)),
        "non_timely_per_match": float((alerts - timely) / len(counts)),
        "timely_precision": float(timely / alerts) if alerts else None,
        "opportunity_ceiling": float(opportunities / events) if events else None,
    }


def action_probabilities(logits: np.ndarray, bias: float | None, family: str) -> np.ndarray:
    if family not in ("randomized", "deterministic"):
        raise ValueError("Unknown policy family")
    if bias is None:
        return np.zeros_like(logits, dtype=np.float64)
    if family == "deterministic":
        return (logits + bias >= 0).astype(np.float64)
    return 1 / (1 + np.exp(-np.clip(logits + bias, -60, 60)))


def select_policy(
    traces: list[Decisions],
    logits: list[np.ndarray],
    routes: list[str],
    *,
    budget: float = 0.9,
    biases: tuple[float, ...] = tuple(np.linspace(-12, 12, 49)),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Select family AND offset using tuning matches only; worst-route budget."""
    if (
        len(routes) != len(traces)
        or not np.isfinite(budget)
        or budget < 0
        or not all(np.isfinite(b) for b in biases)
    ):
        raise ValueError("Invalid tuning routes or budget")
    curve = []
    for family in ("randomized", "deterministic"):
        for bias in (*biases, None):
            counts = marginal_counts(
                traces, [action_probabilities(s, bias, family) for s in logits]
            )
            route_results = {
                r: summary(counts[np.asarray(routes) == r]) for r in sorted(set(routes))
            }
            curve.append(
                {"family": family, "bias": bias, **summary(counts), "by_route": route_results}
            )
    feasible = [
        r for r in curve if all(v["non_timely_per_match"] <= budget for v in r["by_route"].values())
    ]
    selected = max(
        feasible,
        key=lambda r: (
            r["expected_timely_events"],
            -r["non_timely_per_match"],
            r["family"] == "deterministic",
        ),
    )
    return selected, curve
