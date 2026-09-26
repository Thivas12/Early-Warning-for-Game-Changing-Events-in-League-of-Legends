from __future__ import annotations

import hashlib
import json

import pytest

from league_ews.baseline_floor import LABELS, _rows, fit_baseline_floor, run_final_baseline_floor
from league_ews.raw_validation import ProcessingManifest


def _payload(match_id, first_positive=False):
    labels = []
    for timestamp, positive in ((0, first_positive), (60_000, True), (120_000, False)):
        labels.append({"timestamp_ms": timestamp, **{name: int(positive) for name in LABELS}})
    return {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "schema_version": "riot-match-v5-normalized-v1",
            "match_id": match_id,
            "platform_id": "EUW1",
            "game_version": "16.12.1",
            "game_creation_ms": 1,
            "observations": [
                {"timestamp_ms": 0, "participants": [], "events": []},
                {
                    "timestamp_ms": 60_000,
                    "participants": [],
                    "events": [
                        {"timestamp_ms": 59_000, "event_type": "CHAMPION_KILL"},
                        {"timestamp_ms": 59_100, "event_type": "CHAMPION_KILL"},
                        {"timestamp_ms": 59_200, "event_type": "CHAMPION_KILL"},
                        {
                            "timestamp_ms": 59_300,
                            "event_type": "ELITE_MONSTER_KILL",
                            "monster_type": "DRAGON",
                        },
                    ],
                },
                {"timestamp_ms": 120_000, "participants": [], "events": []},
            ],
        },
        "event_index": {},
        "labels": labels,
    }


def _fixture(tmp_path):
    processed = tmp_path / "processed"
    (processed / "matches").mkdir(parents=True)
    records = []
    partitions = {
        name: [{"match_id": match_id}]
        for name, match_id in (("train", "EUW1_1"), ("calibration", "EUW1_2"), ("test", "EUW1_3"))
    }
    for match_id in ("EUW1_1", "EUW1_2"):
        content = json.dumps(_payload(match_id)).encode()
        (processed / "matches" / f"{match_id}.json").write_bytes(content)
        sha = hashlib.sha256(content).hexdigest()
        records.append(
            {
                "match_id": match_id,
                "game_version": "16.12.1",
                "observations": 3,
                "baron_events": 0,
                "dragon_events": 0,
                "teamfight_events": 0,
                "sha256": sha,
            }
        )
    # A test entry exists in the audited inventory, but its file is deliberately absent.
    records.append(
        {
            "match_id": "EUW1_3",
            "game_version": "16.17.1",
            "observations": 3,
            "baron_events": 0,
            "dragon_events": 0,
            "teamfight_events": 0,
            "sha256": "a" * 64,
        }
    )
    manifest = {
        "schema_version": "league-ews-processing-manifest-v1",
        "normalizer": "riot-match-v5-normalized-v1",
        "label_policy": "exact-future-events-v1",
        "contains_player_identifiers": False,
        "matches": records,
    }
    (processed / "processing-manifest.json").write_text(json.dumps(manifest))
    return processed, partitions, ProcessingManifest.model_validate(manifest)


def test_history_uses_observed_kills_and_objectives_only():
    payload = _payload("EUW1_1")
    rows = list(_rows(payload, "EUW1_1"))
    assert rows[0][2] == {"baron": 0, "dragon": 0, "teamfight": 0}
    assert rows[1][2] == {"baron": 0, "dragon": 1, "teamfight": 3}
    assert rows[2][2] == {"baron": 0, "dragon": 1, "teamfight": 3}
    # A future event in the current frame cannot affect its prediction.
    payload["timeline"]["observations"][0]["events"].append(
        {"timestamp_ms": 20_000, "event_type": "ELITE_MONSTER_KILL", "monster_type": "BARON_NASHOR"}
    )
    assert next(_rows(payload, "EUW1_1"))[2]["baron"] == 0
    payload["labels"][0]["y_baron_10"] = 2
    with pytest.raises(ValueError, match="binary"):
        list(_rows(payload, "EUW1_1"))


def test_fit_calibrates_b0_b1_b2_without_opening_test(tmp_path):
    processed, partitions, manifest = _fixture(tmp_path)
    model, report = fit_baseline_floor(processed, partitions, manifest)
    assert set(report["macro_average_precision"]) == {"B0", "B1", "B2"}
    assert report["train_observations"] == report["calibration_observations"] == 3
    assert report["test_matches_unread"] == 1
    assert "EUW1_1" not in json.dumps(report)
    assert model["prevalence"]["y_dragon_10"] == pytest.approx(1 / 3)

    partitions["test"] = [{"match_id": "EUW1_1"}]
    with pytest.raises(ValueError, match="duplicated"):
        fit_baseline_floor(processed, partitions, manifest)


def test_run_binds_split_and_writes_deterministic_artifacts(tmp_path, monkeypatch):
    processed, partitions, _ = _fixture(tmp_path)
    frozen = {"partitions": partitions}
    monkeypatch.setattr("league_ews.baseline_floor.freeze_final_split", lambda *args: frozen)
    split = tmp_path / "split.json"
    split.write_text(json.dumps(frozen))
    output = tmp_path / "private"
    args = (
        tmp_path / "raw",
        processed,
        tmp_path / "frame",
        tmp_path / "g2",
        tmp_path / "audit",
        split,
        output,
    )
    summary = run_final_baseline_floor(*args)
    assert summary["test_matches_unread"] == 1
    assert summary["identifiers_in_report"] is False
    assert run_final_baseline_floor(*args) == summary
    assert (
        hashlib.sha256((output / "model.json").read_bytes()).hexdigest() == summary["model_sha256"]
    )
    split.write_text(json.dumps({"partitions": {}}))
    with pytest.raises(ValueError, match="audited registered partitions"):
        run_final_baseline_floor(*args)


def test_fit_rejects_checksum_drift(tmp_path):
    processed, partitions, manifest = _fixture(tmp_path)
    (processed / "matches" / "EUW1_1.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        fit_baseline_floor(processed, partitions, manifest)
