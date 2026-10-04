"""Keep genuine timing history and current full state; remove past other state."""

from __future__ import annotations

import numpy as np

from scripts.export_league_development import require
from scripts.timely_input_controls import CLOCK_COLUMNS
from scripts.timely_input_controls import intervene as original_intervention

VARIANTS = ("clock_history",)


def intervene(inputs: np.ndarray, mask: np.ndarray, variant: str) -> np.ndarray:
    require(variant == "clock_history", "Unknown input control")
    result = original_intervention(inputs, mask, "current_only")
    retained = list(CLOCK_COLUMNS) + [i + 27 for i in CLOCK_COLUMNS]
    result[..., retained] = inputs[..., retained]
    return result
