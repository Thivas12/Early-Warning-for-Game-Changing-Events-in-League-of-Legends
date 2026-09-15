"""Online-style event extraction, alert generation and one-to-one matching."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd

from league_ews.constants import EVENTS


@dataclass(frozen=True)
class OperationalMetrics:
    event: str
    horizon_seconds: int
    threshold: float
    matches: int
    events: int
    alerts: int
    hits: int
    false_alerts: int
    precision: float
    recall: float
    f1: float
    false_alerts_per_game: float
    false_alerts_per_hour: float
    median_lead_seconds: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def extract_event_times(match: pd.DataFrame, event: str) -> npt.NDArray[np.int64]:
    """Recover observed event times from a causal timer reset.

    The legacy table does not provide a separate event table. A timer changing
    from a positive value to zero indicates an event at that timestamp. This is
    an audit-compatible reconstruction, not the research-v2 label source.
    """

    if event not in EVENTS:
        raise ValueError(f"Unsupported event: {event}")
    timer = f"time_since_last_{event}"
    ordered = match.sort_values("t")
    if timer in ordered:
        values = ordered[timer].to_numpy(dtype=np.float64)
        previous = np.r_[np.nan, values[:-1]]
        mask = np.isclose(values, 0.0) & (~np.isclose(previous, 0.0)) & np.isfinite(previous)
        times = np.asarray(ordered.loc[mask, "t"], dtype=np.int64)
        if len(times):
            return times

    label = f"y_{event}_10"
    if label not in ordered:
        raise ValueError(f"Cannot reconstruct {event} events: missing {timer} and {label}")
    positive = ordered[label].to_numpy(dtype=np.int8) == 1
    ends = positive & ~np.r_[positive[1:], False]
    cadence = int(ordered["t"].diff().dropna().median()) if len(ordered) > 1 else 10
    return np.asarray(ordered.loc[ends, "t"], dtype=np.int64) + cadence


def threshold_crossing_alerts(
    times: npt.NDArray[np.int64],
    probabilities: npt.NDArray[np.float64],
    *,
    threshold: float,
    cooldown_seconds: int,
) -> npt.NDArray[np.int64]:
    """Emit an alert on an upward threshold crossing, subject to cooldown."""

    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0, 1]")
    if cooldown_seconds < 0:
        raise ValueError("cooldown_seconds cannot be negative")
    if len(times) != len(probabilities):
        raise ValueError("times and probabilities must have equal length")
    selected: list[int] = []
    previous_probability = -np.inf
    last_alert = -np.inf
    for timestamp, probability in zip(times, probabilities, strict=True):
        crossed = probability >= threshold and previous_probability < threshold
        if crossed and timestamp - last_alert >= cooldown_seconds:
            selected.append(int(timestamp))
            last_alert = float(timestamp)
        previous_probability = float(probability)
    return np.asarray(selected, dtype=np.int64)


def match_alerts(
    alerts: npt.NDArray[np.int64],
    events: npt.NDArray[np.int64],
    *,
    horizon_seconds: int,
) -> tuple[int, list[int]]:
    """Greedily match each event to at most one preceding alert."""

    if horizon_seconds <= 0:
        raise ValueError("horizon_seconds must be positive")
    used: set[int] = set()
    leads: list[int] = []
    for alert in np.sort(alerts):
        candidates = [
            index
            for index, event in enumerate(events)
            if index not in used and 0 < int(event - alert) <= horizon_seconds
        ]
        if candidates:
            index = min(candidates, key=lambda candidate: int(events[candidate]))
            used.add(index)
            leads.append(int(events[index] - alert))
    return len(used), leads


def evaluate_operating_point(
    frame: pd.DataFrame,
    probabilities: npt.NDArray[np.float64],
    *,
    event: str,
    threshold: float,
    horizon_seconds: int = 30,
    cooldown_seconds: int = 60,
) -> OperationalMetrics:
    """Evaluate distinct alerts against distinct events across complete matches."""

    if len(frame) != len(probabilities):
        raise ValueError("Frame and probability array lengths differ")
    working = frame[
        [
            column
            for column in frame.columns
            if column in {"match_id", "t", f"time_since_last_{event}", f"y_{event}_10"}
        ]
    ].copy()
    working["__probability"] = probabilities

    total_events = total_alerts = total_hits = 0
    total_seconds = 0.0
    all_leads: list[int] = []
    for _, match in working.groupby("match_id", sort=False, observed=True):
        ordered = match.sort_values("t")
        events = extract_event_times(ordered, event)
        alerts = threshold_crossing_alerts(
            ordered["t"].to_numpy(dtype=np.int64),
            ordered["__probability"].to_numpy(dtype=np.float64),
            threshold=threshold,
            cooldown_seconds=cooldown_seconds,
        )
        hits, leads = match_alerts(alerts, events, horizon_seconds=horizon_seconds)
        total_events += len(events)
        total_alerts += len(alerts)
        total_hits += hits
        all_leads.extend(leads)
        if len(ordered):
            total_seconds += float(ordered["t"].max() - ordered["t"].min() + 10)

    false_alerts = total_alerts - total_hits
    precision = total_hits / total_alerts if total_alerts else 0.0
    recall = total_hits / total_events if total_events else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    matches = int(working["match_id"].nunique())
    return OperationalMetrics(
        event=event,
        horizon_seconds=horizon_seconds,
        threshold=threshold,
        matches=matches,
        events=total_events,
        alerts=total_alerts,
        hits=total_hits,
        false_alerts=false_alerts,
        precision=precision,
        recall=recall,
        f1=f1,
        false_alerts_per_game=false_alerts / matches if matches else 0.0,
        false_alerts_per_hour=false_alerts / (total_seconds / 3600) if total_seconds else 0.0,
        median_lead_seconds=float(np.median(all_leads)) if all_leads else None,
    )


def select_operating_threshold(
    frame: pd.DataFrame,
    probabilities: npt.NDArray[np.float64],
    *,
    event: str,
    horizon_seconds: int = 30,
    cooldown_seconds: int = 60,
    candidates: int = 31,
) -> tuple[float, OperationalMetrics]:
    """Choose an event-level F1 threshold using validation data only."""

    if candidates < 3:
        raise ValueError("At least three threshold candidates are required")
    finite = np.asarray(probabilities, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if not len(finite):
        raise ValueError("No finite probabilities")
    quantiles = np.linspace(0.50, 0.999, candidates)
    thresholds = np.unique(np.r_[0.0, np.quantile(finite, quantiles), 1.0])
    scored = [
        evaluate_operating_point(
            frame,
            probabilities,
            event=event,
            threshold=float(threshold),
            horizon_seconds=horizon_seconds,
            cooldown_seconds=cooldown_seconds,
        )
        for threshold in thresholds
    ]
    best = max(scored, key=lambda result: (result.f1, result.precision, -result.alerts))
    return best.threshold, best
