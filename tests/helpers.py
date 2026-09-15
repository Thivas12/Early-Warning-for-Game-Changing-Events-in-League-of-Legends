from __future__ import annotations

import pandas as pd

from league_ews.constants import EVENTS, HORIZONS_SECONDS


def synthetic_legacy_frame(matches: int = 12, timestamps: int = 10) -> pd.DataFrame:
    """Return a small, learnable legacy-shaped table for end-to-end tests."""

    rows: list[dict[str, float | int | str]] = []
    for match_index in range(matches):
        event_steps = {
            "baron": 4 + match_index % 2,
            "dragon": 5 + match_index % 2,
            "teamfight": 6 + match_index % 2,
        }
        for step in range(timestamps):
            timestamp = step * 10
            row: dict[str, float | int | str] = {
                "match_id": f"EUW1_{match_index:04d}",
                "t": timestamp,
                "gold_diff": float((match_index % 3 - 1) * 100 + step * 5),
                "xp_diff": float(step * 3 - match_index % 4),
                "kills_30_t1": int(step % 3),
                "teamfight_recent_20": int(step in {5, 6}),
            }
            for event in EVENTS:
                event_step = event_steps[event]
                row[f"time_since_last_{event}"] = (
                    9999 if step < event_step else (step - event_step) * 10
                )
                for horizon in HORIZONS_SECONDS:
                    seconds_until = (event_step - step) * 10
                    row[f"y_{event}_{horizon}"] = int(0 < seconds_until <= horizon)
            rows.append(row)
    return pd.DataFrame(rows)
