"""Causal capped warning replay and fixed-sequence bounded-risk diagnostics.

Nominal risk statements require a fixed predictor and IID calibration/test
matches. Repeatedly inspected League calibration does not meet fresh-validation
requirements; this module does not turn those data into a certified release.
"""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np

from scripts.evaluate_dense_policy import GRID
from scripts.export_league_development import require

CAP = 4
FAMILIES = (
    "timely_equal_sum",
    "timely_equal_tcn",
    "timely_equal_gru",
    "timely_independent",
    "timely_leagueews",
)
POLICIES = ("uncapped_empirical", "capped_empirical", "capped_sequence", "capped_kl_sequence")
REGIONS = ("europe", "americas")
DELTA = 0.05
REGIONAL_SEQUENCES = len(FAMILIES) * 3 * 3 * 2 * 4 * len(REGIONS)
SEQUENCE_LEVEL = DELTA / REGIONAL_SEQUENCES


def replay_capped(times, events, scores, thresholds=GRID, horizon=30, cap=CAP, batch_size=128):
    """Count chronological warnings; only past warning count enforces the cap."""
    require(horizon in (30, 60), "Invalid horizon")
    require(type(cap) is int and cap > 0, "Cap must be a positive integer")
    require(type(batch_size) is int and batch_size > 0, "Invalid batch size")
    require(len(times) > 0 and len(times) == len(events) == len(scores), "Invalid population")
    require(
        len(thresholds) > 0
        and all(t is None or (np.isfinite(t) and 0 < t <= 1) for t in thresholds),
        "Invalid thresholds",
    )
    for t, e, s in zip(times, events, scores, strict=True):
        require(
            len(t) > 0
            and len(t) == len(s)
            and np.isfinite(t).all()
            and np.isfinite(e).all()
            and np.isfinite(s).all()
            and np.array_equal(t, np.rint(t))
            and np.array_equal(e, np.rint(e))
            and np.all(np.diff(t) > 0)
            and np.all(np.diff(e) > 0)
            and np.all(np.asarray(t) >= 0)
            and np.all(np.asarray(e) >= 0)
            and np.all(np.asarray(s) >= 0)
            and np.all(np.asarray(s) <= 1),
            "Invalid chronology or scores",
        )
    threshold = np.array([np.inf if t is None else t for t in thresholds])
    out = np.zeros((len(times), len(threshold), 6), dtype=np.int64)
    for start in range(0, len(times), batch_size):
        stop = min(start + batch_size, len(times))
        n, width = stop - start, len(threshold)
        length = max(len(t) for t in times[start:stop])
        max_events = max(len(e) for e in events[start:stop])
        clock = np.zeros((n, length), dtype=np.int64)
        risk = np.full((n, length), -np.inf)
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
            alarm = (
                (risk[:, step, None] >= threshold)
                & (time[:, None] - last >= 60000)
                & (c[:, :, 3] < cap)
            )
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
    require(np.all(out[:, :, 3] <= cap), "Causal warning cap failed")
    return out


def reference_capped(times, events, scores, threshold, horizon, cap=CAP):
    """Scalar oracle: decide warnings first, then credit events independently."""
    warnings = []
    if threshold is not None:
        for time, score in zip(times, scores, strict=True):
            if len(warnings) == cap:
                break
            if score >= threshold and (not warnings or time - warnings[-1] >= 60000):
                warnings.append(time)
    used, hit, timely = set(), 0, 0
    for time in warnings:
        eligible = [
            i
            for i, event in enumerate(events)
            if i not in used and time < event <= time + horizon * 1000
        ]
        if eligible:
            i = eligible[0]
            used.add(i)
            hit += 1
            timely += events[i] - time >= horizon * 1000 // 3
    opportunities = sum(
        any(event - horizon * 1000 <= time <= event - horizon * 1000 // 3 for time in times)
        for event in events
    )
    return np.array([len(events), hit, timely, len(warnings), len(warnings) - hit, opportunities])


def calibration_inputs(cal, probabilities, event, indices):
    times, events, scores = [], [], []
    for i in indices:
        a, b = cal["match_offsets"][i : i + 2]
        left, right = cal[f"{event}_offsets"][i : i + 2]
        times.append(cal["times_ms"][a:b])
        events.append(cal[f"{event}_ms"][left:right])
        scores.append(probabilities[a:b])
    return times, events, scores


def kl_pvalue(total_cost, matches, budget, cap=CAP):
    """Hoeffding's Bernoulli-KL lower-tail bound for losses in [0, cap]."""
    require(type(matches) is int and matches > 0, "Invalid match count")
    require(type(cap) is int and cap > 0, "Invalid cap")
    require(np.isfinite(total_cost) and 0 <= total_cost <= matches * cap, "Unbounded cost")
    require(np.isfinite(budget) and 0 < budget < cap, "Invalid risk budget")
    a, b = total_cost / (matches * cap), budget / cap
    if a >= b:
        return 1.0
    divergence = (a * math.log(a / b) if a else 0.0) + (1 - a) * math.log((1 - a) / (1 - b))
    return min(1.0, math.exp(-matches * divergence))


def select_capped(region_totals, region_sizes, budget, thresholds=GRID, level=SEQUENCE_LEVEL):
    """Three controls with the same cap, grid, regional constraints and tie rule.

    Fixed sequences visit thresholds in descending order and stop at the FIRST
    failed regional test. They never skip a failure to use a favorable later
    threshold. Each region receives the prespecified allocated error level.
    """
    totals = np.asarray(region_totals)
    sizes = np.asarray(region_sizes)
    require(totals.shape == (2, len(thresholds), 6), "Count shape differs")
    require(
        sizes.shape == (2,) and np.all(sizes > 0) and np.array_equal(sizes, np.rint(sizes)),
        "Region sizes differ",
    )
    require(0 < level < 1, "Invalid sequence level")
    require(
        thresholds[0] is None
        and all(t is not None for t in thresholds[1:])
        and all(a > b for a, b in pairwise(thresholds[1:])),
        "Sequence order differs",
    )
    require(
        np.isfinite(totals).all()
        and np.all(totals >= 0)
        and np.array_equal(totals, np.rint(totals))
        and np.all(totals[:, :, 2] <= totals[:, :, 1])
        and np.all(totals[:, :, 1] <= totals[:, :, 0])
        and np.all(totals[:, :, 2] <= totals[:, :, 5])
        and np.all(totals[:, :, 1] + totals[:, :, 4] == totals[:, :, 3])
        and np.all(totals[:, :, 3] <= sizes[:, None] * CAP)
        and np.all(totals[:, 0, 1:5] == 0),
        "Invalid capped counts or silent policy",
    )
    cost = totals[:, :, 3] - totals[:, :, 2]
    means = cost / sizes[:, None]
    pvalues = np.array(
        [
            [kl_pvalue(int(c), int(n), budget) for c in region]
            for region, n in zip(cost, sizes, strict=True)
        ]
    )
    pvalues[:, 0] = 0.0  # Silence is structurally zero risk, not an estimated mean.
    feasible = np.all(means <= budget, axis=0)
    certified = np.all(pvalues <= level, axis=0)
    sums = totals.sum(0)

    def choose(mask):
        ids = np.flatnonzero(mask)
        require(len(ids) > 0 and ids[0] == 0, "Silent fallback missing")
        return int(max(ids, key=lambda i: (sums[i, 2], -(sums[i, 3] - sums[i, 2]), -i)))

    empirical_prefix = np.logical_and.accumulate(feasible)
    kl_prefix = np.logical_and.accumulate(certified)
    selected = {
        "capped_empirical": choose(feasible),
        "capped_sequence": choose(empirical_prefix),
        "capped_kl_sequence": choose(kl_prefix),
    }
    return {
        "indices": selected,
        "pvalues_by_region": pvalues.tolist(),
        "empirical_prefix_length": int(empirical_prefix.sum()),
        "kl_prefix_length": int(kl_prefix.sum()),
        "sequence_level": level,
        "early_burden_by_region": means.tolist(),
    }
