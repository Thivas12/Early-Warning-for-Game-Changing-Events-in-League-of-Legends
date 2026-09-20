from typing import Any

import pytest
from pydantic import ValidationError

from league_ews.timeline import normalise_match_timeline, participant_team_map


def _match_detail() -> dict[str, Any]:
    return {
        "metadata": {"matchId": "EUW1_123"},
        "info": {
            "platformId": "EUW1",
            "gameVersion": "16.1.1.1234",
            "gameCreation": 1_700_000_000_000,
            "participants": [
                {"participantId": participant_id, "teamId": 100 if participant_id <= 5 else 200}
                for participant_id in range(1, 11)
            ],
        },
    }


def _participant_frame(participant_id: int, timestamp: int) -> dict[str, Any]:
    return {
        "participantId": participant_id,
        "totalGold": 500 + participant_id + timestamp / 1000,
        "xp": timestamp / 100,
        "level": 1 + timestamp // 60_000,
        "minionsKilled": timestamp // 10_000,
        "jungleMinionsKilled": 0,
        "position": {"x": 5000 + participant_id, "y": 10470 + participant_id},
        # This deliberately proves that unsupported health is not propagated.
        "currentHealth": 999,
    }


def _timeline() -> dict[str, Any]:
    frames = []
    for timestamp in (0, 60_000):
        events: list[dict[str, Any]] = []
        if timestamp:
            events = [
                {
                    "type": "ELITE_MONSTER_KILL",
                    "timestamp": 55_000,
                    "killerId": 0,
                    "killerTeamId": 100,
                    "monsterType": "DRAGON",
                },
                {
                    "type": "CHAMPION_KILL",
                    "timestamp": 58_000,
                    "killerId": 0,
                    "victimId": 6,
                },
            ]
        frames.append(
            {
                "timestamp": timestamp,
                "participantFrames": {
                    str(participant_id): _participant_frame(participant_id, timestamp)
                    for participant_id in range(1, 11)
                },
                "events": events,
            }
        )
    return {"info": {"frames": frames}}


def test_normalise_timeline_preserves_real_frames_and_objective_team() -> None:
    timeline = normalise_match_timeline(_match_detail(), _timeline())
    assert timeline.match_id == "EUW1_123"
    assert timeline.game_version == "16.1.1.1234"
    assert len(timeline.observations) == 2
    assert len(timeline.observations[0].participants) == 10
    dragon = timeline.observations[1].events[0]
    assert dragon.killer_team_id == 100
    assert dragon.monster_type == "DRAGON"
    null_killer = timeline.observations[1].events[1]
    assert null_killer.killer_team_id is None
    assert not hasattr(timeline.observations[0].participants[0], "current_health")


def test_participant_team_map_requires_all_ten_players() -> None:
    detail = _match_detail()
    detail["info"]["participants"] = detail["info"]["participants"][:-1]
    with pytest.raises(ValueError, match=r"1\.\.10"):
        participant_team_map(detail)


def test_non_increasing_frames_are_rejected() -> None:
    timeline = _timeline()
    timeline["info"]["frames"][1]["timestamp"] = 0
    with pytest.raises(ValueError, match="increase"):
        normalise_match_timeline(_match_detail(), timeline)


def test_2026_top_lane_level_cap_is_supported() -> None:
    timeline = _timeline()
    timeline["info"]["frames"][1]["participantFrames"]["1"]["level"] = 20
    normalized = normalise_match_timeline(_match_detail(), timeline)
    assert normalized.observations[1].participants[0].level == 20


def test_level_above_registered_cap_is_rejected() -> None:
    timeline = _timeline()
    timeline["info"]["frames"][1]["participantFrames"]["1"]["level"] = 21
    with pytest.raises(ValidationError, match="less than or equal to 20"):
        normalise_match_timeline(_match_detail(), timeline)
