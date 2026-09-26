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


def test_processing_resumes_prefix_and_finalizes_without_rewriting(tmp_path) -> None:
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    for match_id in ("EUW1_1", "EUW1_2"):
        detail, timeline = _raw_payloads(match_id)
        for kind, payload in (("matches", detail), ("timelines", timeline)):
            directory = raw / kind
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{match_id}.json").write_text(json.dumps(payload), encoding="utf-8")

    first = process_raw_collection(raw, output_root=output, max_new_matches=1)
    assert first["complete"] is False
    assert first["new_matches"] == 1
    assert not (output / "processing-manifest.json").exists()
    saved = (output / "matches" / "EUW1_1.json").read_bytes()

    second = process_raw_collection(raw, output_root=output, max_new_matches=1)
    assert second["complete"] is True
    assert second["new_matches"] == 1
    assert (output / "matches" / "EUW1_1.json").read_bytes() == saved
    on_disk = json.loads((output / "processing-manifest.json").read_text(encoding="utf-8"))
    assert len(on_disk["matches"]) == 2
    assert "complete" not in on_disk
    assert process_raw_collection(raw, output_root=output, max_new_matches=1)["new_matches"] == 0


def test_processing_rejects_gaps_and_corrupt_existing_match(tmp_path) -> None:
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    for match_id in ("EUW1_1", "EUW1_2"):
        detail, timeline = _raw_payloads(match_id)
        for kind, payload in (("matches", detail), ("timelines", timeline)):
            directory = raw / kind
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{match_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="positive"):
        process_raw_collection(raw, output_root=output, max_new_matches=0)
    process_raw_collection(raw, output_root=output, max_new_matches=1)
    saved = output / "matches" / "EUW1_1.json"
    (output / "matches" / "EUW1_2.json").write_bytes(saved.read_bytes())
    with pytest.raises(ValueError, match="identity"):
        process_raw_collection(raw, output_root=output)
    (output / "matches" / "EUW1_2.json").unlink()
    saved.rename(output / "matches" / "EUW1_2.json")
    with pytest.raises(ValueError, match="contiguous prefix"):
        process_raw_collection(raw, output_root=output)
