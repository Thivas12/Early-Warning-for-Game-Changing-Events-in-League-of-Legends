from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from league_ews.processed_validation import validate_processed_collection
from league_ews.processing import process_raw_collection
from league_ews.raw_validation import validate_raw_collection
from league_ews.riot import collect_match_bundles


class _Fetcher:
    def get_match(self, match_id):
        return {
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
        return {
            "metadata": {"matchId": match_id, "participants": ["private"] * 10},
            "info": {
                "frames": [
                    {"timestamp": 0, "participantFrames": participants, "events": []},
                    {
                        "timestamp": 60_000,
                        "participantFrames": participants,
                        "events": [
                            {
                                "timestamp": 20_000,
                                "type": "ELITE_MONSTER_KILL",
                                "monsterType": "DRAGON",
                                "killerTeamId": 100,
                            }
                        ],
                    },
                ]
            },
        }


def _fixture(tmp_path):
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=raw,
        fetcher=_Fetcher(),
        collected_at=datetime(2026, 9, 15, tzinfo=UTC),
    )
    report = validate_raw_collection(raw, min_routes=1, min_patches=1)
    assert report["passed"] is True
    report_path = tmp_path / "raw-validation.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    process_raw_collection(raw, output_root=processed)
    return raw, processed, report_path


def test_processed_audit_binds_inventory_hashes_events_and_labels(tmp_path) -> None:
    raw, processed, report = _fixture(tmp_path)
    result = validate_processed_collection(raw, processed, report)
    assert result["passed"] is True
    assert result["failed_checks"] == []
    assert result["summary"]["validated_matches"] == 1
    assert "EUW1_1" not in json.dumps(result)

    (processed / "matches" / "NA1_2.json").write_text("{}", encoding="utf-8")
    result = validate_processed_collection(raw, processed, report)
    assert "processed-inventory" in result["failed_checks"]


def test_processed_audit_detects_relabeling_even_when_manifest_hash_is_updated(tmp_path) -> None:
    raw, processed, report = _fixture(tmp_path)
    path = processed / "matches" / "EUW1_1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["labels"][0]["y_dragon_60"] = 1 - payload["labels"][0]["y_dragon_60"]
    content = json.dumps(payload).encode()
    path.write_bytes(content)
    manifest_path = processed / "processing-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["matches"][0]["sha256"] = hashlib.sha256(content).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_processed_collection(raw, processed, report)
    assert result["passed"] is False
    assert "future-labels" in result["failed_checks"]
    assert "checksums" not in result["failed_checks"]


def test_processed_audit_rejects_stale_raw_validation_report(tmp_path) -> None:
    raw, processed, report = _fixture(tmp_path)
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["manifest_sha256"] = "0" * 64
    report.write_text(json.dumps(payload), encoding="utf-8")
    result = validate_processed_collection(raw, processed, report)
    assert "raw-validation-binding" in result["failed_checks"]
