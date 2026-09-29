"""Explicit timely/late targets and policies; frozen coordination definitions stay intact."""

from __future__ import annotations

from typing import Any

import numpy as np

from league_ews.alert_policy import THRESHOLDS, MatchRisk
from league_ews.coordination_policy import paired_intervals, replay

BURDENS = ("non_timely", "false")


def interval_targets(times: tuple[int, ...], events: tuple[int, ...]) -> dict[str, np.ndarray]:
    """Classify the next strictly future Dragon, including exact 20s and 60s boundaries."""
    t, e = np.asarray(times, dtype=np.int64), np.asarray(events, dtype=np.int64)
    if (
        not len(t)
        or np.any(t < 0)
        or np.any(e < 0)
        or np.any(np.diff(t) <= 0)
        or np.any(np.diff(e) <= 0)
        or (len(e) and e[-1] > t[-1])
    ):
        raise ValueError("Invalid complete-match timestamps")
    positions = np.searchsorted(e, t, side="right")
    delays = np.full(len(t), np.iinfo(np.int64).max, dtype=np.int64)
    present = positions < len(e)
    delays[present] = e[positions[present]] - t[present]
    within = delays <= 60_000
    timely = within & (delays >= 20_000)
    late = within & ~timely
    return {
        "within60": within.astype(np.int8),
        "timely20_60": timely.astype(np.int8),
        "late0_20": late.astype(np.int8),
    }


def summarize(
    matches: list[MatchRisk], threshold: float | None
) -> tuple[dict[str, Any], np.ndarray]:
    result, counts = replay(matches, threshold)
    non_timely = counts[:, 3] - counts[:, 2]
    result.update(
        non_timely_alerts=int(non_timely.sum()),
        non_timely_alerts_per_game=float(non_timely.mean()),
        non_timely_alerts_per_game_quantiles={
            str(q): float(np.percentile(non_timely, q)) for q in (50, 90, 95)
        },
        opportunity_ceiling=(
            result["timely_opportunities"] / result["events"] if result["events"] else None
        ),
    )
    return result, counts


def select_policies(
    tuning: list[MatchRisk], budget: float = 1.0
) -> tuple[dict[str, Any], list[Any]]:
    if not np.isfinite(budget) or budget < 0:
        raise ValueError("Budget must be finite and nonnegative")
    curve = [{"threshold": t, **summarize(tuning, t)[0]} for t in (*THRESHOLDS, None)]
    selected = {}
    for burden in BURDENS:
        key = f"{burden}_alerts_per_game"
        feasible = [row for row in curve if row[key] <= budget]
        selected[burden] = max(
            feasible,
            key=lambda row: (
                row["timely_matched_events"],
                -row[key],
                -row["non_timely_alerts_per_game"],
                row["threshold"] if row["threshold"] is not None else 2.0,
            ),
        )
    return selected, curve


def compare_counts(candidate: np.ndarray, control: np.ndarray, routes: list[str]) -> dict[str, Any]:
    """Same paired matches for recall, false burden and false-plus-late burden."""
    result = paired_intervals(candidate, control, routes)
    left, right = candidate.copy(), control.copy()
    left[:, 4], right[:, 4] = left[:, 3] - left[:, 2], right[:, 3] - right[:, 2]
    non_timely = paired_intervals(left, right, routes)
    result["non_timely_alerts_per_game_difference"] = non_timely["false_alerts_per_game_difference"]
    if result["percentile_95_intervals"] is not None:
        result["percentile_95_intervals"]["non_timely_alerts_per_game_difference"] = non_timely[
            "percentile_95_intervals"
        ]["false_alerts_per_game_difference"]
    return result
