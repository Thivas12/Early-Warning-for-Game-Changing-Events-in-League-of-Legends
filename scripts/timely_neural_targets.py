"""Replace only evaluated output labels with next-event useful-lead targets."""

from __future__ import annotations

from itertools import pairwise

import numpy as np

from league_ews.constants import EVENTS
from scripts.export_league_development import require


def next_event_delays(data, event):
    """Next strictly future event per observed cutoff; never cross matches."""
    times = data["times_ms"]
    result = np.full(len(times), np.iinfo(np.int64).max, dtype=np.int64)
    offsets = data[f"{event}_offsets"]
    for i, (a, b) in enumerate(pairwise(data["match_offsets"])):
        events = data[f"{event}_ms"][offsets[i] : offsets[i + 1]]
        require(np.all(np.diff(events) > 0), "Events must be strictly chronological")
        indices = np.searchsorted(events, times[a:b], side="right")
        valid = indices < len(events)
        result[a:b][valid] = events[indices[valid]] - times[a:b][valid]
    return result


def fitted_targets(data):
    """Preserve 10/20-second auxiliaries; replace 30/60 heads only.

    Next-event semantics agree with one-to-one warning credit under 60s cooldown
    and horizons <=60s. Any event later in the interval cannot rescue a warning
    whose first future event is too soon. Both useful-lead boundaries are inclusive.
    """
    target = data["targets"].copy()
    require(
        target.shape == (len(data["times_ms"]), 12) and np.isin(target, (0, 1)).all(),
        "Expected original twelve binary targets",
    )
    for e, event in enumerate(EVENTS):
        delay = next_event_delays(data, event)
        for column, lower, upper in ((2, 10000, 30000), (3, 20000, 60000)):
            target[:, 4 * e + column] = (delay >= lower) & (delay <= upper)
    return target
