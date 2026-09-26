from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import pytest

from league_ews.event_review import create_final_event_review_packet
from league_ews.processed_validation import validate_processed_collection
from league_ews.processing import process_raw_collection
from league_ews.raw_validation import validate_raw_collection
from league_ews.riot import collect_match_bundles


class _Fetcher:
    def get_match(self, match_id):
        return {
            "metadata": {"matchId": match_id, "participants": ["private"] * 10},
            "info": {
                "gameVersion": "16.17.1",
                "gameCreation": 123,
                "platformId": "EUW1",
                "participants": [
                    {"participantId": participant, "teamId": 100 if participant <= 5 else 200}
                    for participant in range(1, 11)
                ],
            },
        }

    def get_timeline(self, match_id):
        participants = {
            str(participant): {
                "totalGold": 500,
                "xp": 0,
                "level": 1,
                "minionsKilled": 0,
                "jungleMinionsKilled": 0,
            }
            for participant in range(1, 11)
        }
        events = [
            {"timestamp": 20_000, "type": "ELITE_MONSTER_KILL", "monsterType": "DRAGON"},
            {"timestamp": 30_000, "type": "CHAMPION_KILL"},
            {"timestamp": 35_000, "type": "CHAMPION_KILL"},
            {"timestamp": 40_000, "type": "CHAMPION_KILL"},
            {"timestamp": 50_000, "type": "ELITE_MONSTER_KILL", "monsterType": "BARON_NASHOR"},
        ]
        return {
            "metadata": {"matchId": match_id, "participants": ["private"] * 10},
            "info": {
                "frames": [
                    {"timestamp": 0, "participantFrames": participants, "events": []},
                    {"timestamp": 60_000, "participantFrames": participants, "events": events},
                ]
            },
        }


def _fixture(tmp_path):
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    collect_match_bundles(
        ["EUW1_1", "EUW1_2"],
        regional_route="europe",
        output_root=raw,
        fetcher=_Fetcher(),
        collected_at=datetime(2026, 9, 15, tzinfo=UTC),
    )
    raw_report = validate_raw_collection(raw, min_routes=1, min_patches=1)
    assert raw_report["passed"] is True
    raw_report_path = tmp_path / "raw-report.json"
    raw_report_path.write_text(json.dumps(raw_report), encoding="utf-8")
    process_raw_collection(raw, output_root=processed)
    audit = validate_processed_collection(raw, processed, raw_report_path)
    assert audit["passed"] is True
    audit_path = tmp_path / "processed-report.json"
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    return raw, processed, audit_path


def test_review_packet_selects_deterministic_event_rich_sample(tmp_path) -> None:
    raw, processed, audit = _fixture(tmp_path)
    packet = create_final_event_review_packet(raw, processed, audit, required_cells=1)
    assert packet["human_review_status"] == "pending"
    assert len(packet["samples"]) == 1
    sample = packet["samples"][0]
    expected_id = min(
        ("EUW1_1", "EUW1_2"),
        key=lambda match_id: hashlib.sha256(
            f"{packet['raw_manifest_sha256']}:{match_id}".encode()
        ).hexdigest(),
    )
    assert sample["match_id"] == expected_id
    assert sample["source_event_index"] == {
        "baron_ms": [50_000],
        "dragon_ms": [20_000],
        "teamfight_ms": [30_000],
    }
    assert sample["source_teamfight_episodes"] == [
        {"onset_ms": 30_000, "kill_ms": [30_000, 35_000, 40_000]}
    ]
    assert all(witness["expected"] == witness["processed"] for witness in sample["label_witnesses"])
    assert len(sample["label_witnesses"]) == 12


def test_review_packet_rejects_stale_audit(tmp_path) -> None:
    raw, processed, audit_path = _fixture(tmp_path)
    report = json.loads(audit_path.read_text(encoding="utf-8"))
    report["processing_manifest_sha256"] = "0" * 64
    audit_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="bind the current manifests"):
        create_final_event_review_packet(raw, processed, audit_path, required_cells=1)
