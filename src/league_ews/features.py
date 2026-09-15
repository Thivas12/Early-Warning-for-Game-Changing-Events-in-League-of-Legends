"""Feature policies that make information availability explicit."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from league_ews.constants import (
    IDENTIFIER_COLUMNS,
    LEGACY_BROKEN_COLUMNS,
    LEGACY_LABEL_COLUMNS,
    LEGACY_POST_MATCH_COLUMNS,
    TIME_COLUMN,
)

HISTORY_PREFIXES: tuple[str, ...] = (
    "kills_",
    "deaths_",
    "wards_",
    "items_",
    "time_since_",
)
HISTORY_EXACT: tuple[str, ...] = (
    TIME_COLUMN,
    "teamfight_recent_20",
    "towers_t1",
    "towers_t2",
    "inhibs_t1",
    "inhibs_t2",
)


def causal_feature_columns(frame: pd.DataFrame) -> list[str]:
    """Select numeric legacy features after known leakage/breakage exclusions."""

    excluded = {
        *IDENTIFIER_COLUMNS,
        *LEGACY_LABEL_COLUMNS,
        *LEGACY_POST_MATCH_COLUMNS,
        *LEGACY_BROKEN_COLUMNS,
    }
    return [
        column for column in frame.select_dtypes(include="number").columns if column not in excluded
    ]


def history_feature_columns(frame: pd.DataFrame) -> list[str]:
    """Return the deliberately simple time and prior-event baseline features."""

    safe = set(causal_feature_columns(frame))
    candidates = [
        column
        for column in frame.columns
        if column in HISTORY_EXACT or column.startswith(HISTORY_PREFIXES)
    ]
    return [column for column in candidates if column in safe]


def legacy_post_match_feature_columns(frame: pd.DataFrame) -> list[str]:
    """Return unavailable final-summary fields for leakage diagnosis only."""

    return [column for column in LEGACY_POST_MATCH_COLUMNS if column in frame]


def require_features(frame: pd.DataFrame, columns: Sequence[str]) -> None:
    """Fail with a useful message when an experiment requests absent features."""

    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required feature columns: {', '.join(missing)}")
