"""Source-field audit distinguishes absent raw inputs from genuine zeroes."""

import hashlib
import json
from collections import Counter

import pytest

from league_ews import raw_field_coverage as coverage_module
from league_ews.raw_field_coverage import _audit_members, _count_timeline_fields, _usable_number


def test_source_field_coverage_counts_absent_and_invalid_without_identifiers():
    state = {
        "totalGold": 0,
        "xp": 0,
        "level": 1,
        "minionsKilled": 0,
        "jungleMinionsKilled": 0,
        "position": {"x": 0, "y": 0},
    }
    participants = {str(index): state.copy() for index in range(1, 11)}
    participants["2"].pop("totalGold")
    participants["3"]["xp"] = None
    participants["4"]["level"] = 0
    participants["5"]["position"] = {"x": 1}
    participants["6"].pop("position")
    counts: Counter[tuple[str, str, str, str]] = Counter()
    states: Counter[tuple[str, str]] = Counter()
    timeline = {"info": {"frames": [{"participantFrames": participants}]}}
    assert _count_timeline_fields(timeline, "europe", "16.12", counts, states) == 1
    assert states["europe", "16.12"] == 10
    assert counts["europe", "16.12", "totalGold", "absent"] == 1
    assert counts["europe", "16.12", "xp", "absent"] == 1
    assert counts["europe", "16.12", "level", "invalid"] == 1
    assert counts["europe", "16.12", "position", "invalid"] == 1
    assert counts["europe", "16.12", "position", "absent"] == 1
    assert counts["europe", "16.12", "minionsKilled", "absent"] == 0


def test_source_field_audit_rejects_missing_participants_and_non_numeric_values():
    with pytest.raises(ValueError, match="participant inventory"):
        _count_timeline_fields(
            {"info": {"frames": [{"participantFrames": {}}]}},
            "europe",
            "16.12",
            Counter(),
            Counter(),
        )
    assert _usable_number(0)
    assert not _usable_number(-1)
    assert not _usable_number(float("nan"))
    assert not _usable_number("0")
    assert not _usable_number(True)
    assert not _usable_number(0, level=True)


def test_source_field_audit_checks_checksum_without_opening_test_timeline(tmp_path):
    (tmp_path / "timelines").mkdir()
    state = {str(i): {} for i in range(1, 11)}
    content = json.dumps({"info": {"frames": [{"participantFrames": state}]}}).encode()
    (tmp_path / "timelines" / "EUW1_1.json").write_bytes(content)
    members = [{"match_id": "EUW1_1", "regional_route": "europe", "game_version_patch": "16.12"}]
    inventory = {
        "EUW1_1": {
            "regional_route": "europe",
            "game_version": "16.12.1",
            "timeline_sha256": hashlib.sha256(content).hexdigest(),
        },
        # No test-patch file exists. Only the passed train membership is opened.
        "EUW1_2": {
            "regional_route": "europe",
            "game_version": "16.17.1",
            "timeline_sha256": "a" * 64,
        },
    }
    counts: Counter[tuple[str, str, str, str]] = Counter()
    states: Counter[tuple[str, str]] = Counter()
    assert _audit_members(members, "train", inventory, tmp_path, set(), counts, states) == 1
    assert counts["europe", "16.12", "totalGold", "absent"] == 10
    inventory["EUW1_1"]["timeline_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="checksum"):
        _audit_members(members, "train", inventory, tmp_path, set(), Counter(), Counter())


def test_bound_source_audit_counts_train_and_calibration_without_test_payload(
    tmp_path, monkeypatch
):
    for name, value in (("TRAIN_MATCHES", 2), ("CALIBRATION_MATCHES", 1), ("TEST_MATCHES", 1)):
        monkeypatch.setattr(coverage_module, name, value)
    raw = tmp_path / "raw"
    (raw / "timelines").mkdir(parents=True)
    selected = [
        ("EUW1_1", "train", "16.12"),
        ("EUW1_2", "train", "16.13"),
        ("EUW1_3", "calibration", "16.16"),
        ("EUW1_4", "test", "16.17"),
    ]
    entries = []
    partitions = {name: [] for name in ("train", "calibration", "test")}
    for match_id, partition, patch in selected:
        states = {str(i): {"level": 1, "totalGold": 0} for i in range(1, 11)}
        content = json.dumps({"info": {"frames": [{"participantFrames": states}]}}).encode()
        if partition != "test":
            (raw / "timelines" / f"{match_id}.json").write_bytes(content)
        entries.append(
            {
                "match_id": match_id,
                "regional_route": "europe",
                "game_version": f"{patch}.1",
                "timeline_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
        partitions[partition].append(
            {"match_id": match_id, "regional_route": "europe", "game_version_patch": patch}
        )
    manifest = raw / "collection-manifest.json"
    manifest.write_text(
        json.dumps({"schema_version": "riot-raw-collection-v2", "available": entries})
    )
    manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    g2 = tmp_path / "g2.json"
    g2.write_text(
        json.dumps(
            {
                "schema_version": "riot-raw-validation-v5",
                "passed": True,
                "g2_complete": True,
                "manifest_sha256": manifest_sha,
            }
        )
    )
    split = tmp_path / "split.json"
    split.write_text(
        json.dumps(
            {
                "schema_version": "league-ews-final-split-v1",
                "g2_report_sha256": hashlib.sha256(g2.read_bytes()).hexdigest(),
                "raw_manifest_sha256": manifest_sha,
                "summary": {"counts": {"train": 2, "calibration": 1, "test": 1}},
                "partitions": partitions,
            }
        )
    )
    output = tmp_path / "audit.json"
    report = coverage_module.write_raw_field_coverage(raw, g2, split, output)
    assert report["matches"] == 3
    assert report["frames"] == 3
    assert report["participant_states"] == 30
    assert report["test_timelines_unread"] is True
    assert "EUW1_" not in output.read_text()
    calibration = next(cell for cell in report["cells"] if cell["patch"] == "16.16")
    assert calibration["fields"]["xp"]["absent"] == 10
    (raw / "timelines" / "EUW1_3.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        coverage_module.audit_raw_field_coverage(raw, g2, split)
    g2.write_text("{}")
    with pytest.raises(ValueError, match="passed, bound final collection"):
        coverage_module.audit_raw_field_coverage(raw, g2, split)
