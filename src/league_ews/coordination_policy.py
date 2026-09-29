"""Disjoint-tuning warning policy and paired whole-match uncertainty.

Primary: timely recall (20--60 seconds) subject to <=1 false alert/match.
An alert matched inside 20 seconds is late, not false; both are reported.
The new protocol allows alerts exactly 60 seconds apart. Frozen M1 is unchanged.
"""

from __future__ import annotations

from bisect import bisect_left
from itertools import pairwise
from typing import Any

import numpy as np

from league_ews.alert_policy import THRESHOLDS, MatchRisk

COUNT_NAMES = ("events", "matched", "timely", "alerts", "false", "opportunities")


def replay(
    matches: list[MatchRisk],
    threshold: float | None,
) -> tuple[dict[str, Any], np.ndarray]:
    """Replay one-to-one chronological matching; None is the explicit no-alert policy."""
    if not matches or (
        threshold is not None and (not np.isfinite(threshold) or not 0 < threshold <= 1)
    ):
        raise ValueError("Invalid matches or threshold")
    counts = np.zeros((len(matches), len(COUNT_NAMES)), dtype=np.int64)
    leads: list[float] = []
    for index, match in enumerate(matches):
        times, onsets, risks = match.times_ms, match.events_ms, match.risks
        if (
            len(times) != len(risks)
            or not times
            or any(b <= a for a, b in pairwise(times))
            or any(b <= a for a, b in pairwise(onsets))
            or any(t < 0 for t in (*times, *onsets))
            or any(not np.isfinite(p) or not 0 <= p <= 1 for p in risks)
        ):
            raise ValueError("Invalid chronological warning input")
        counts[index, 0] = len(onsets)
        for onset in onsets:
            position = bisect_left(times, onset - 60_000)
            counts[index, 5] += position < len(times) and times[position] <= onset - 20_000
        last_alert: int | None = None
        first_unmatched = 0
        for time, risk in zip(times, risks, strict=True):
            if (
                threshold is None
                or risk < threshold
                or (last_alert is not None and time - last_alert < 60_000)
            ):
                continue
            last_alert = time
            counts[index, 3] += 1
            while first_unmatched < len(onsets) and onsets[first_unmatched] <= time:
                first_unmatched += 1
            if first_unmatched < len(onsets) and onsets[first_unmatched] <= time + 60_000:
                delay = onsets[first_unmatched] - time
                counts[index, 1] += 1
                counts[index, 2] += delay >= 20_000
                leads.append(delay / 1000)
                first_unmatched += 1
            else:
                counts[index, 4] += 1
    totals = counts.sum(axis=0)
    events, hits, timely, alerts, false, opportunities = (int(value) for value in totals)
    summary = {
        "matches": len(matches),
        "events": events,
        "alerts": alerts,
        "matched_events": hits,
        "timely_matched_events": timely,
        "event_recall": hits / events if events else None,
        "timely_event_recall": timely / events if events else None,
        "precision": hits / alerts if alerts else None,
        "timely_precision": timely / alerts if alerts else None,
        "false_alerts_per_game": false / len(matches),
        "late_alerts_per_game": (hits - timely) / len(matches),
        "timely_opportunities": opportunities,
        "opportunity_conditional_timely_recall": timely / opportunities if opportunities else None,
        "lead_seconds_median": float(np.median(leads)) if leads else None,
        "lead_seconds_p10": float(np.percentile(leads, 10)) if leads else None,
        "false_alerts_per_game_quantiles": {
            str(q): float(np.percentile(counts[:, 4], q)) for q in (50, 90, 95)
        },
    }
    return summary, counts


def select_budget_policy(
    tuning: list[MatchRisk],
    budget: float = 1.0,
) -> tuple[float | None, list[dict[str, Any]]]:
    """Maximize timely hits, then fewer false/late alerts, then higher threshold."""
    if not np.isfinite(budget) or budget < 0:
        raise ValueError("Budget must be finite and nonnegative")
    curve = []
    for threshold in (*THRESHOLDS, None):
        summary, _ = replay(tuning, threshold)
        curve.append({"threshold": threshold, **summary})
    feasible = [row for row in curve if row["false_alerts_per_game"] <= budget]
    chosen = max(
        feasible,
        key=lambda row: (
            row["timely_matched_events"],
            -row["false_alerts_per_game"],
            -row["late_alerts_per_game"],
            row["threshold"] if row["threshold"] is not None else 2.0,
        ),
    )
    return chosen["threshold"], curve


def paired_intervals(
    candidate: np.ndarray,
    control: np.ndarray,
    routes: list[str],
    *,
    draws: int = 2000,
    seed: int = 20260929,
) -> dict[str, Any]:
    """Route-stratified paired bootstrap conditional on the fitted models/policies."""
    if (
        candidate.shape != control.shape
        or candidate.shape != (len(routes), len(COUNT_NAMES))
        or not routes
        or draws < 100
        or not np.array_equal(candidate[:, 0], control[:, 0])
        or np.any(candidate < 0)
        or np.any(control < 0)
    ):
        raise ValueError("Paired match counts or bootstrap specification differ")
    strata = [np.flatnonzero(np.asarray(routes) == route) for route in sorted(set(routes))]
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(draws):
        indices = np.concatenate(
            [rng.choice(group, size=len(group), replace=True) for group in strata]
        )
        left, right = candidate[indices].sum(axis=0), control[indices].sum(axis=0)
        if left[0]:
            values.append([(left[2] - right[2]) / left[0], (left[4] - right[4]) / len(indices)])
    totals_left, totals_right = candidate.sum(axis=0), control.sum(axis=0)
    return {
        "draws_requested": draws,
        "draws_with_events": len(values),
        "seed": seed,
        "timely_recall_difference": (
            float((totals_left[2] - totals_right[2]) / totals_left[0]) if totals_left[0] else None
        ),
        "false_alerts_per_game_difference": float((totals_left[4] - totals_right[4]) / len(routes)),
        "percentile_95_intervals": (
            {
                name: np.percentile(np.asarray(values)[:, column], [2.5, 97.5]).tolist()
                for column, name in enumerate(
                    ("timely_recall_difference", "false_alerts_per_game_difference")
                )
            }
            if values
            else None
        ),
        "scope": (
            "Exploratory; conditional on models and tuned policies; "
            "no refit or patch-population uncertainty"
        ),
    }
