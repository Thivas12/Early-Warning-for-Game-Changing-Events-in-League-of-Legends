"""EDA respects the audited split and never publishes membership identifiers."""

import hashlib
import json

import pytest

from league_ews import eda
from league_ews.eda import audited_eda_data, write_eda


def _file(path, payload):
    path.write_text(json.dumps(payload, sort_keys=True))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sources(tmp_path):
    g2_path = tmp_path / "g2.json"
    audit_path = tmp_path / "audit.json"
    split_path = tmp_path / "split.json"
    events = {"baron": 3600, "dragon": 18000, "teamfight": 36000}
    g2 = {
        "schema_version": "riot-raw-validation-v5",
        "passed": True,
        "automated_passed": True,
        "g2_complete": True,
        "sampling_frame": {"status": "passed"},
        "manifest_sha256": "raw-sha",
        "summary": {
            "valid_bundles": 36000,
            "observations": 72000,
            "observation_cadence_ms": {
                "interval_count": 36000,
                "minimum": 28000,
                "median": 60018,
                "maximum": 64400,
            },
            "regional_routes": {"americas": 18000, "europe": 18000},
            "patches": dict.fromkeys(("16.12", "16.13", "16.14", "16.15", "16.16", "16.17"), 6000),
            "events": events,
            "event_labelability": {
                event: {
                    "total_events": count,
                    "by_horizon_seconds": {
                        str(horizon): {
                            "labelable_events": count * fraction // 10,
                            "fraction": fraction / 10,
                        }
                        for horizon, fraction in ((10, 1), (20, 3), (30, 5), (60, 10))
                    },
                }
                for event, count in events.items()
            },
        },
    }
    g2_sha = _file(g2_path, g2)
    audit_sha = _file(
        audit_path,
        {
            "schema_version": "league-ews-processed-validation-v1",
            "passed": True,
            "processing_manifest_sha256": "processed-sha",
            "summary": {"validated_matches": 36000, "contains_player_identifiers": False},
        },
    )
    partitions = {"train": [], "calibration": [], "test": []}
    for patch_index, patch in enumerate(("16.12", "16.13", "16.14", "16.15", "16.16", "16.17")):
        partition = "train" if patch_index < 4 else "calibration" if patch_index == 4 else "test"
        for route, platform in (("europe", "EUW1"), ("americas", "NA1")):
            partitions[partition].extend(
                {
                    "match_id": f"{platform}_{patch_index * 6000 + i}",
                    "regional_route": route,
                    "game_version_patch": patch,
                }
                for i in range(3000)
            )
    _file(
        split_path,
        {
            "schema_version": "league-ews-final-split-v1",
            "g2_report_sha256": g2_sha,
            "processed_audit_sha256": audit_sha,
            "raw_manifest_sha256": "raw-sha",
            "processing_manifest_sha256": "processed-sha",
            "summary": {"counts": {"train": 24000, "calibration": 6000, "test": 6000}},
            "partitions": partitions,
        },
    )
    return g2_path, split_path, audit_path


def test_eda_renders_audited_aggregates_without_identifiers(tmp_path, monkeypatch):
    sources = _sources(tmp_path)
    destination = tmp_path / "eda.html"
    monkeypatch.setattr(
        eda,
        "_training_calibration_aggregates",
        lambda *args: {
            "observations": 72000,
            "cadence_ms": {"minimum": 28000, "median": 60018, "maximum": 64400},
            "event_counts": {"baron": 3600, "dragon": 18000, "teamfight": 36000},
            "opportunity_percent": {event: [10, 30, 50, 100] for event in eda.EVENTS},
        },
    )
    summary = write_eda(*sources, tmp_path / "processed", destination)
    page = destination.read_text()
    assert summary["opportunity_percent"]["baron"] == [10, 30, 50, 100]
    assert summary["test_outcomes_unread"] is True
    assert "EUW1_" not in page and "NA1_" not in page
    assert "36,000" in page and "60.02 s" in page
    assert "strictly earlier genuine snapshot" in page


def test_eda_refuses_a_replaced_validation_report(tmp_path):
    g2, split, audit = _sources(tmp_path)
    payload = json.loads(g2.read_text())
    payload["summary"]["events"]["baron"] += 1
    _file(g2, payload)
    with pytest.raises(ValueError, match="checksum-bound"):
        audited_eda_data(g2, split, audit, tmp_path / "processed")


def test_eda_only_opens_train_and_calibration_match_files(tmp_path):
    root = tmp_path / "processed"
    (root / "matches").mkdir(parents=True)
    partitions = {
        "train": [{"match_id": "EUW1_1"}],
        "calibration": [{"match_id": "NA1_2"}],
        "test": [{"match_id": "EUW1_3"}],
    }
    records = [{"match_id": f"EUW1_{i + 4}"} for i in range(35998)]
    for name, event_time in (("EUW1_1", 12000), ("NA1_2", 22000)):
        payload = {
            "schema_version": "league-ews-processed-match-v1",
            "timeline": {
                "match_id": name,
                "observations": [{"timestamp_ms": 0}, {"timestamp_ms": 10000}],
            },
            "event_index": {f"{event}_ms": [event_time] for event in eda.EVENTS},
        }
        content = json.dumps(payload).encode()
        (root / "matches" / f"{name}.json").write_bytes(content)
        records.append(
            {
                "match_id": name,
                "sha256": hashlib.sha256(content).hexdigest(),
                "observations": 2,
                **{f"{event}_events": 1 for event in eda.EVENTS},
            }
        )
    manifest_sha = _file(
        root / "processing-manifest.json",
        {
            "schema_version": "league-ews-processing-manifest-v1",
            "contains_player_identifiers": False,
            "matches": records,
        },
    )
    # The test member has no processed file. Accessing it would fail.
    result = eda._training_calibration_aggregates(partitions, root, manifest_sha)
    assert result["observations"] == 4
    assert result["event_counts"] == dict.fromkeys(eda.EVENTS, 2)
    assert result["opportunity_percent"]["baron"] == [50, 100, 100, 100]
