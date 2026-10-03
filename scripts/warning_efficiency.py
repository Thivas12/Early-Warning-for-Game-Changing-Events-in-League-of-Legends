"""Whole-match warning replay and early-only operating-point selection.

Threshold mixtures choose one threshold at match start, not at each timestamp.
Expected whole-match counts preserve cooldown and one-to-one event credit.
"""

from __future__ import annotations

import numpy as np

from league_ews.alert_policy import THRESHOLDS

BUDGETS = (0.25, 0.5, 0.75, 1.0)
THRESHOLD_VALUES = (None, *reversed(THRESHOLDS))


def replay_thresholds(
    times, events, scores, thresholds=THRESHOLD_VALUES, horizon=30, batch_size=128
):
    """Return match x threshold x six counts; vectorize thresholds and matches.

    A monotone event pointer matches the registered chronological policy. The
    pointer only affects credit; score/cooldown alone decide whether to warn.
    """
    if horizon not in (30, 60) or not len(times) or not len(times) == len(events) == len(scores):
        raise ValueError("Invalid replay population or horizon")
    if not thresholds or any(
        t is not None and (not np.isfinite(t) or not 0 < t <= 1) for t in thresholds
    ):
        raise ValueError("Invalid thresholds")
    for t, e, s in zip(times, events, scores, strict=True):
        if (
            not len(t)
            or len(t) != len(s)
            or np.any(np.diff(t) <= 0)
            or np.any(np.diff(e) <= 0)
            or np.any(np.asarray(t) < 0)
            or np.any(np.asarray(e) < 0)
            or not np.isfinite(s).all()
            or np.any(np.asarray(s) < 0)
            or np.any(np.asarray(s) > 1)
        ):
            raise ValueError("Invalid chronology or scores")
    threshold = np.asarray([np.inf if t is None else t for t in thresholds], dtype=np.float64)
    out = np.zeros((len(times), len(threshold), 6), dtype=np.int64)
    for start in range(0, len(times), batch_size):
        stop = min(start + batch_size, len(times))
        n, width = stop - start, len(threshold)
        length = max(len(t) for t in times[start:stop])
        max_events = max(len(e) for e in events[start:stop])
        clock = np.zeros((n, length), dtype=np.int64)
        risk = np.full((n, length), -np.inf, dtype=np.float64)
        future = np.full((n, max_events + 1), np.iinfo(np.int64).max // 2, dtype=np.int64)
        opportunity = np.zeros((n, max_events + 1), dtype=bool)
        c = out[start:stop]
        for i, (t, e, s) in enumerate(
            zip(times[start:stop], events[start:stop], scores[start:stop], strict=True)
        ):
            clock[i, : len(t)] = t
            risk[i, : len(t)] = s
            future[i, : len(e)] = e
            c[i, :, 0] = len(e)
        last = np.full((n, width), -60000, dtype=np.int64)
        pointer = np.zeros((n, width), dtype=np.int64)
        for step in range(length):
            time = clock[:, step]
            valid = np.isfinite(risk[:, step])
            opportunity |= (
                valid[:, None]
                & (time[:, None] >= future - horizon * 1000)
                & (time[:, None] <= future - horizon * 1000 // 3)
            )
            alarm = (risk[:, step, None] >= threshold) & (time[:, None] - last >= 60000)
            last = np.where(alarm, time[:, None], last)
            pointer = np.maximum(pointer, (future <= time[:, None]).sum(1)[:, None])
            next_event = np.take_along_axis(future, pointer, axis=1)
            hit = alarm & (next_event <= time[:, None] + horizon * 1000)
            timely = hit & (next_event - time[:, None] >= horizon * 1000 // 3)
            pointer += hit
            c[:, :, 1] += hit
            c[:, :, 2] += timely
            c[:, :, 3] += alarm
            c[:, :, 4] += alarm & ~hit
        c[:, :, 5] = opportunity.sum(1)[:, None]
    return out


def replay_calibration(cal, probabilities, event, indices, horizon, thresholds=THRESHOLD_VALUES):
    times, events, scores = [], [], []
    for i in indices:
        a, b = cal["match_offsets"][i : i + 2]
        left, right = cal[f"{event}_offsets"][i : i + 2]
        times.append(cal["times_ms"][a:b])
        events.append(cal[f"{event}_ms"][left:right])
        scores.append(probabilities[a:b])
    return replay_thresholds(times, events, scores, thresholds, horizon)


def select_deterministic(region_totals, region_sizes, budget):
    """Original grid/tie rule at a prespecified common regional budget."""
    costs = (region_totals[:, :, 3] - region_totals[:, :, 2]) / np.asarray(region_sizes)[:, None]
    totals = region_totals.sum(0)
    candidates = np.flatnonzero(np.all(costs <= budget, axis=0))
    if not len(candidates):
        raise ValueError("No feasible silent policy")
    return int(
        max(
            candidates,
            key=lambda i: (
                totals[i, 2],
                -(totals[i, 3] - totals[i, 2]),
                2 if THRESHOLD_VALUES[i] is None else THRESHOLD_VALUES[i],
            ),
        )
    )


def select_mixture(totals, matches, budget):
    """Solve the two-equality linear program by exhaustive vertex enumeration.

    Maximize early timely hits subject to weight sum=1 and expected early
    non-timely warnings/match=budget. An optimum uses at most two thresholds.
    Candidate order resolves ties deterministically; no later counts are inputs.
    """
    cost = (totals[:, 3] - totals[:, 2]) / matches
    hit = totals[:, 2].astype(np.float64)
    best = None
    for i in range(len(cost)):
        if abs(cost[i] - budget) <= 1e-12:
            candidate = {"indices": [i], "weights": [1.0], "early_timely": float(hit[i])}
            if best is None or candidate["early_timely"] > best["early_timely"] + 1e-12:
                best = candidate
        for j in range(i + 1, len(cost)):
            if cost[i] == cost[j] or not min(cost[i], cost[j]) < budget < max(cost[i], cost[j]):
                continue
            w = float((budget - cost[j]) / (cost[i] - cost[j]))
            value = float(w * hit[i] + (1 - w) * hit[j])
            if best is None or value > best["early_timely"] + 1e-12:
                best = {"indices": [i, j], "weights": [w, 1 - w], "early_timely": value}
    if best is None:
        raise ValueError("Exact early budget is infeasible; do not change the frozen budget")
    best["early_burden"] = float(np.dot(cost[best["indices"]], best["weights"]))
    if not np.isclose(best["early_burden"], budget, rtol=0, atol=1e-12):
        raise ValueError("Mixture budget mismatch")
    return best


def expected_counts(counts, policy):
    return np.einsum("ntk,t->nk", counts[:, policy["indices"]], policy["weights"])
