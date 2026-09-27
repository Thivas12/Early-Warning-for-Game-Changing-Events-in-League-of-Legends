"""Discrete-time hazard utilities for coherent multi-horizon forecasts."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from league_ews.labels import EventIndex

EVENT_TYPES = ("baron", "dragon", "teamfight")


def cumulative_risk(hazards: NDArray[np.floating]) -> NDArray[np.float64]:
    """Convert conditional hazards into monotonically non-decreasing risk."""

    values = np.asarray(hazards, dtype=np.float64)
    if values.ndim == 0:
        raise ValueError("Hazards must have at least one dimension")
    if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError("Hazards must be finite probabilities in [0, 1]")
    survival = np.cumprod(1.0 - values, axis=-1)
    return 1.0 - survival


def risk_at_horizons(
    hazards: NDArray[np.floating],
    *,
    bin_seconds: int,
    horizons_seconds: Sequence[int],
) -> NDArray[np.float64]:
    """Read cumulative event risk at requested, aligned horizons."""

    if bin_seconds <= 0:
        raise ValueError("bin_seconds must be positive")
    if not horizons_seconds:
        raise ValueError("At least one horizon is required")
    indices: list[int] = []
    for horizon in horizons_seconds:
        if horizon <= 0 or horizon % bin_seconds:
            raise ValueError("Horizons must be positive multiples of bin_seconds")
        indices.append(horizon // bin_seconds - 1)
    risks = cumulative_risk(hazards)
    if max(indices) >= risks.shape[-1]:
        raise ValueError("Hazard sequence is shorter than the requested horizon")
    return np.take(risks, indices, axis=-1)


def discrete_hazard_target(
    seconds_to_event: float | None,
    *,
    bin_seconds: int,
    bins: int,
) -> NDArray[np.float64]:
    """Encode the event bin; an absent/out-of-window event is all zero."""

    if bin_seconds <= 0 or bins <= 0:
        raise ValueError("bin_seconds and bins must be positive")
    target = np.zeros(bins, dtype=np.float64)
    if seconds_to_event is None or seconds_to_event <= 0:
        return target
    index = int(np.ceil(seconds_to_event / bin_seconds)) - 1
    if index < bins:
        target[index] = 1.0
    return target


def event_hazard_targets(
    observation_time_ms: int,
    event_index: EventIndex,
    *,
    bin_seconds: int = 10,
    bins: int = 6,
) -> NDArray[np.float64]:
    """Encode the next strictly future event independently for each event type.

    Multiple event types can occur in one bin. These are cause-specific binary
    hazards, not mutually exclusive outcomes of a single softmax.
    """

    if observation_time_ms < 0:
        raise ValueError("Observation time must be non-negative")
    if bin_seconds <= 0 or bins <= 0:
        raise ValueError("bin_seconds and bins must be positive")
    targets = np.zeros((len(EVENT_TYPES), bins), dtype=np.float64)
    for row, event_type in enumerate(EVENT_TYPES):
        times = np.asarray(event_index.for_event(event_type), dtype=np.int64)
        if (times < 0).any() or (np.diff(times) <= 0).any():
            raise ValueError("Event times must be non-negative and strictly increasing")
        next_index = int(np.searchsorted(times, observation_time_ms, side="right"))
        if next_index < len(times):
            targets[row] = discrete_hazard_target(
                (int(times[next_index]) - observation_time_ms) / 1000,
                bin_seconds=bin_seconds,
                bins=bins,
            )
    return targets
