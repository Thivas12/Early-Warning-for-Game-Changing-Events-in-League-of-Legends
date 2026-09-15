"""Discrete-time hazard utilities for coherent multi-horizon forecasts."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray


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
