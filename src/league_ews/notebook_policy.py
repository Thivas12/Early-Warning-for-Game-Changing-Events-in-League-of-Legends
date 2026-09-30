"""Chronological warning evaluation for the original 30s and registered 60s tasks."""

from __future__ import annotations

from bisect import bisect_left
from itertools import pairwise
from typing import Any

import numpy as np

from league_ews.alert_policy import THRESHOLDS, MatchRisk


def replay(
    matches: list[MatchRisk], threshold: float | None, horizon: int
) -> tuple[dict[str, Any], np.ndarray]:
    """One-to-one future matching; fixed 60s cooldown, minimum useful lead h/3."""
    if (
        horizon not in (30, 60)
        or not matches
        or (threshold is not None and (not np.isfinite(threshold) or not 0 < threshold <= 1))
    ):
        raise ValueError("Invalid notebook warning policy")
    counts = np.zeros((len(matches), 6), dtype=np.int64)
    leads = []
    for row, match in enumerate(matches):
        times, events, risks = match.times_ms, match.events_ms, match.risks
        if (
            not times
            or len(times) != len(risks)
            or any(t < 0 for t in (*times, *events))
            or any(b <= a for a, b in pairwise(times))
            or any(b <= a for a, b in pairwise(events))
            or any(not np.isfinite(p) or not 0 <= p <= 1 for p in risks)
        ):
            raise ValueError("Invalid warning chronology or probabilities")
        counts[row, 0] = len(events)
        for event in events:
            position = bisect_left(times, event - horizon * 1000)
            counts[row, 5] += (
                position < len(times) and times[position] <= event - horizon * 1000 // 3
            )
        last, pointer = -60_000, 0
        for time, risk in zip(times, risks, strict=True):
            if threshold is None or risk < threshold or time - last < 60_000:
                continue
            last = time
            counts[row, 3] += 1
            while pointer < len(events) and events[pointer] <= time:
                pointer += 1
            if pointer < len(events) and events[pointer] <= time + horizon * 1000:
                lead = events[pointer] - time
                counts[row, 1] += 1
                counts[row, 2] += lead >= horizon * 1000 // 3
                leads.append(lead / 1000)
                pointer += 1
            else:
                counts[row, 4] += 1
    event_count, hits, timely, alerts, false, opportunities = (int(v) for v in counts.sum(0))
    return {
        "matches": len(matches),
        "events": event_count,
        "alerts": alerts,
        "matched_events": hits,
        "timely_matched_events": timely,
        "event_recall": hits / event_count if event_count else None,
        "timely_event_recall": timely / event_count if event_count else None,
        "timely_precision": timely / alerts if alerts else None,
        "false_alerts_per_match": false / len(matches),
        "late_alerts_per_match": (hits - timely) / len(matches),
        "non_timely_alerts_per_match": (alerts - timely) / len(matches),
        "timely_opportunities": opportunities,
        "lead_seconds_median": float(np.median(leads)) if leads else None,
        "lead_seconds_p10": float(np.percentile(leads, 10)) if leads else None,
    }, counts


def select(matches: list[MatchRisk], routes: list[str], horizon: int) -> float | None:
    """Choose on early calibration only, with <=1 non-timely alert/match in each route."""
    if len(routes) != len(matches) or set(routes) != {"europe", "americas"}:
        raise ValueError("Expected both League routes")
    route_indices = [np.flatnonzero(np.asarray(routes) == r) for r in sorted(set(routes))]
    best_key, best = (-1, -float("inf"), -float("inf")), None
    for threshold in (*THRESHOLDS, None):
        metrics, counts = replay(matches, threshold, horizon)
        if any(float((counts[idx, 3] - counts[idx, 2]).mean()) > 1 for idx in route_indices):
            continue
        key = (
            metrics["timely_matched_events"],
            -metrics["non_timely_alerts_per_match"],
            2 if threshold is None else threshold,
        )
        if key > best_key:
            best_key, best = key, threshold
    return best
