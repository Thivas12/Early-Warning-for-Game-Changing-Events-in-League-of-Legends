"""Versioned research constants and legacy exclusions."""

from __future__ import annotations

EVENTS: tuple[str, ...] = ("baron", "dragon", "teamfight")
HORIZONS_SECONDS: tuple[int, ...] = (10, 20, 30)

LABEL_COLUMNS: tuple[str, ...] = tuple(
    f"y_{event}_{horizon}" for event in EVENTS for horizon in HORIZONS_SECONDS
)

# These are final match-summary values repeated at every timestamp in the
# released legacy table. They are unavailable at prediction time.
LEGACY_POST_MATCH_COLUMNS: tuple[str, ...] = (
    "kills_blue",
    "kills_red",
    "deaths_blue",
    "deaths_red",
    "assists_blue",
    "assists_red",
    "totdmgdealt_blue",
    "totdmgdealt_red",
    "totdmgtochamp_blue",
    "totdmgtochamp_red",
    "totheal_blue",
    "totheal_red",
    "wardsplaced_blue",
    "wardsplaced_red",
    "wardskilled_blue",
    "wardskilled_red",
)

# The legacy generator requested fields that Match-V5 timeline participant
# frames do not contain, and read the wrong objective-team field.
LEGACY_BROKEN_COLUMNS: tuple[str, ...] = (
    "alive_t1",
    "alive_t2",
    "alive_diff",
    "low_hp_t1",
    "low_hp_t2",
    "dragons_t1",
    "dragons_t2",
    "barons_t1",
    "barons_t2",
    "heralds_t1",
    "heralds_t2",
)

IDENTIFIER_COLUMNS: tuple[str, ...] = ("match_id",)
TIME_COLUMN = "t"

FEATURE_POLICY_VERSION = "legacy-causal-v1"
LABEL_POLICY_VERSION = "legacy-label-audit-v1"
SPLIT_POLICY_VERSION = "chronological-match-v1"
