"""Normalization of Riot Match-V5 detail and timeline payloads.

The normalized representation preserves the genuine observation cadence. It
does not invent health/alive values that are absent from Match-V5 timeline
participant frames and it attributes objective kills through ``killerTeamId``.
"""

from __future__ import annotations

from collections.abc import Mapping
from itertools import pairwise
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from league_ews.constants import RIFTHAZARD_MAX_CHAMPION_LEVEL


class Position(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: float
    y: float


class ParticipantState(BaseModel):
    model_config = ConfigDict(frozen=True)

    participant_id: int = Field(ge=1, le=10)
    team_id: int
    total_gold: float = Field(ge=0)
    xp: float = Field(ge=0)
    level: int = Field(ge=1, le=RIFTHAZARD_MAX_CHAMPION_LEVEL)
    lane_minions: float = Field(ge=0)
    jungle_minions: float = Field(ge=0)
    position: Position | None = None


class TimelineEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp_ms: int = Field(ge=0)
    event_type: str
    participant_id: int | None = None
    killer_id: int | None = None
    victim_id: int | None = None
    assisting_participant_ids: tuple[int, ...] = ()
    killer_team_id: int | None = None
    monster_type: str | None = None
    monster_sub_type: str | None = None
    ward_type: str | None = None
    item_id: int | None = None
    position: Position | None = None


class Observation(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp_ms: int = Field(ge=0)
    participants: tuple[ParticipantState, ...]
    events: tuple[TimelineEvent, ...]


class NormalizedTimeline(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "riot-match-v5-normalized-v1"
    match_id: str
    platform_id: str | None
    game_version: str
    game_creation_ms: int = Field(ge=0)
    observations: tuple[Observation, ...]


def _mapping(value: object) -> Mapping[object, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return int(value)
    raise TypeError(f"Expected a number-like value, received {type(value).__name__}")


def _optional_int(value: object) -> int | None:
    if value in (None, 0):
        return None
    return _int(value)


def _optional_text(value: object) -> str | None:
    return str(value) if value not in (None, "") else None


def _position(value: object) -> Position | None:
    raw = _mapping(value)
    if "x" not in raw or "y" not in raw:
        return None
    return Position(x=float(raw["x"]), y=float(raw["y"]))


def participant_team_map(match_detail: Mapping[str, Any]) -> dict[int, int]:
    """Build the authoritative participant-to-team mapping from match detail."""

    info = _mapping(match_detail.get("info"))
    mapping: dict[int, int] = {}
    for raw_participant in _sequence(info.get("participants")):
        participant = _mapping(raw_participant)
        participant_id = _int(participant.get("participantId"))
        team_id = _int(participant.get("teamId"))
        if 1 <= participant_id <= 10 and team_id in {100, 200}:
            mapping[participant_id] = team_id
    if set(mapping) != set(range(1, 11)):
        raise ValueError("Match detail must map participant IDs 1..10 to teams")
    return mapping


def _normalise_event(raw_event: object, teams: Mapping[int, int]) -> TimelineEvent:
    raw = _mapping(raw_event)
    killer_id = _optional_int(raw.get("killerId"))
    explicit_team = _optional_int(raw.get("killerTeamId"))
    killer_team_id = explicit_team if explicit_team in {100, 200} else teams.get(killer_id or -1)
    return TimelineEvent(
        timestamp_ms=_int(raw.get("timestamp")),
        event_type=str(raw.get("type", "UNKNOWN")),
        participant_id=_optional_int(raw.get("participantId")),
        killer_id=killer_id,
        victim_id=_optional_int(raw.get("victimId")),
        assisting_participant_ids=tuple(
            int(value) for value in _sequence(raw.get("assistingParticipantIds"))
        ),
        killer_team_id=killer_team_id,
        monster_type=_optional_text(raw.get("monsterType")),
        monster_sub_type=_optional_text(raw.get("monsterSubType")),
        ward_type=_optional_text(raw.get("wardType")),
        item_id=_optional_int(raw.get("itemId")),
        position=_position(raw.get("position")),
    )


def normalise_match_timeline(
    match_detail: Mapping[str, Any],
    timeline_payload: Mapping[str, Any],
) -> NormalizedTimeline:
    """Normalize supported Match-V5 payload fields without forward filling."""

    teams = participant_team_map(match_detail)
    detail_metadata = _mapping(match_detail.get("metadata"))
    detail_info = _mapping(match_detail.get("info"))
    timeline_info = _mapping(timeline_payload.get("info"))
    match_id = str(detail_metadata.get("matchId", ""))
    if not match_id:
        raise ValueError("Match detail is missing metadata.matchId")

    observations: list[Observation] = []
    for raw_frame in _sequence(timeline_info.get("frames")):
        frame = _mapping(raw_frame)
        participant_frames = _mapping(frame.get("participantFrames"))
        participants: list[ParticipantState] = []
        for participant_id in range(1, 11):
            raw_state = _mapping(
                participant_frames.get(str(participant_id), participant_frames.get(participant_id))
            )
            if not raw_state:
                raise ValueError(f"Timeline frame is missing participant {participant_id}")
            participants.append(
                ParticipantState(
                    participant_id=participant_id,
                    team_id=teams[participant_id],
                    total_gold=float(raw_state.get("totalGold", 0)),
                    xp=float(raw_state.get("xp", 0)),
                    level=max(1, _int(raw_state.get("level"), 1)),
                    lane_minions=float(raw_state.get("minionsKilled", 0)),
                    jungle_minions=float(raw_state.get("jungleMinionsKilled", 0)),
                    position=_position(raw_state.get("position")),
                )
            )
        observations.append(
            Observation(
                timestamp_ms=_int(frame.get("timestamp")),
                participants=tuple(participants),
                events=tuple(
                    _normalise_event(event, teams) for event in _sequence(frame.get("events"))
                ),
            )
        )

    if not observations:
        raise ValueError("Timeline contains no frames")
    if any(later.timestamp_ms <= earlier.timestamp_ms for earlier, later in pairwise(observations)):
        raise ValueError("Timeline frame timestamps must increase")

    platform_id = _optional_text(detail_info.get("platformId"))
    if platform_id is None and "_" in match_id:
        platform_id = match_id.split("_", maxsplit=1)[0]
    return NormalizedTimeline(
        match_id=match_id,
        platform_id=platform_id,
        game_version=str(detail_info.get("gameVersion", "unknown")),
        game_creation_ms=_int(detail_info.get("gameCreation")),
        observations=tuple(observations),
    )
