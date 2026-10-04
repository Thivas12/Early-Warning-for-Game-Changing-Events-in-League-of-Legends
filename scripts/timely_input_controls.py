"""Input interventions for matched useful-lead LeagueEWS mechanism controls."""

from __future__ import annotations

import numpy as np

from league_ews.tabular_baseline import FEATURES
from scripts.export_league_development import require
from scripts.run_history_ablation import current_only

VARIANTS = ("current_only", "clock_only")
CLOCK_FEATURES = (
    "clock_minutes",
    "dragons_blue",
    "dragons_red",
    "barons_blue",
    "barons_red",
    "minutes_since_dragon",
    "minutes_since_baron",
)
CLOCK_COLUMNS = tuple(FEATURES.index(name) for name in CLOCK_FEATURES)


def intervene(inputs: np.ndarray, mask: np.ndarray, variant: str) -> np.ndarray:
    """Keep dimensions, mask and ages fixed; remove only the declared information."""
    require(variant in VARIANTS, "Unknown input control")
    require(inputs.ndim == 3 and inputs.shape[2] == 55, "Expected original channels")
    require(mask.shape == inputs.shape[:2] and mask.dtype == np.bool_, "Invalid mask")
    require(
        np.all(mask[:, -1]) and np.all(np.diff(mask.astype(int), axis=1) >= 0),
        "Expected right-aligned genuine frames",
    )
    if variant == "current_only":
        return current_only(inputs, mask)
    result = inputs.copy()
    dropped = [i for i in range(27) if i not in CLOCK_COLUMNS]
    # Also remove excluded features' missingness; those flags must not leak state.
    result[..., dropped] = 0
    result[..., [i + 27 for i in dropped]] = 0
    return result
