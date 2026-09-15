from __future__ import annotations

import json

import pytest

from league_ews.processing import process_raw_collection


def _raw_payloads(match_id: str = "EUW1_1") -> tuple[dict[str, object], dict[str, object]]:
    detail = {
        "metadata": {"matchId": match_id, "participants": ["private"] * 10},
        "info": {
            "gameVersion": "16.18.1",
            "gameCreation": 123,
            "platformId": "EUW1",
            "participants": [
                {"participantId": participant, "teamId": 100 if participant <= 5 else 200}
                for participant in range(1, 11)
            ],
        },
    }

    def participant_frames() -> dict[str, object]:
        return {
            str(participant): {
                "totalGold": 500,
                "xp": 0,
                "level": 1,
                "minionsKilled": 0,
                "jungleMinionsKilled": 0,
                "position": {"x": participant, "y": participant},
            }
            for participant in range(1, 11)
        }

    timeline = {
        "metadata": {"matchId": match_id, "participants": ["private"] * 10},
        "info": {
            "frames": [
                {"timestamp": 0, "participantFrames": participant_frames(), "events": []},
                {
                    "timestamp": 60_000,
                    "participantFrames": participant_frames(),
                    "events": [
                        {
                            "timestamp": 20_000,
                            "type": "ELITE_MONSTER_KILL",
                            "monsterType": "DRAGON",
                            "killerTeamId": 100,
                        },
                        {"timestamp": 31_000, "type": "CHAMPION_KILL"},
                        {"timestamp": 37_000, "type": "CHAMPION_KILL"},
                        {"timestamp": 40_000, "type": "CHAMPION_KILL"},
                    ],
                },
            ]
        },
    }
    return detail, timeline


def _write_raw(root, *, with_timeline: bool = True) -> None:
    detail, timeline = _raw_payloads()
    (root / "matches").mkdir(parents=True)
    (root / "matches" / "EUW1_1.json").write_text(json.dumps(detail), encoding="utf-8")
    if with_timeline:
        (root / "timelines").mkdir(parents=True)
        (root / "timelines" / "EUW1_1.json").write_text(json.dumps(timeline), encoding="utf-8")


def test_processing_normalizes_labels_and_removes_identifiers(tmp_path) -> None:
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    _write_raw(raw)

    manifest = process_raw_collection(raw, output_root=output)

    assert manifest["contains_player_identifiers"] is False
    assert len(manifest["matches"]) == 1
    content = (output / "matches" / "EUW1_1.json").read_text(encoding="utf-8")
    assert "private" not in content
    processed = json.loads(content)
    assert processed["event_index"]["dragon_ms"] == [20_000]
    assert processed["event_index"]["teamfight_ms"] == [31_000]
    assert processed["labels"][0]["y_dragon_20"] == 1


def test_processing_requires_raw_pairs(tmp_path) -> None:
    with pytest.raises(ValueError, match="no match"):
        process_raw_collection(tmp_path, output_root=tmp_path / "out")

    raw = tmp_path / "raw"
    _write_raw(raw, with_timeline=False)
    with pytest.raises(FileNotFoundError, match="Missing timeline"):
        process_raw_collection(raw, output_root=tmp_path / "out")
