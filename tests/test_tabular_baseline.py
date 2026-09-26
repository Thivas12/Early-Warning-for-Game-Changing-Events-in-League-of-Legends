from __future__ import annotations

import hashlib
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.baseline_floor import LABELS
from league_ews.tabular_baseline import (
    FEATURES,
    _bound_floor,
    _matrix,
    _rows,
    run_final_tabular,
    summarize_final_tabular,
)


def _payload(match_id):
    participants = [
        {
            "participant_id": index,
            "team_id": 100 if index <= 5 else 200,
            "total_gold": 500 + index,
            "xp": 200 + index,
            "level": 2,
            "lane_minions": index,
            "jungle_minions": 0,
            "position": {"x": index * 10.0, "y": index * 5.0},
        }
        for index in range(1, 11)
    ]
    return {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "schema_version": "riot-match-v5-normalized-v1",
            "match_id": match_id,
            "platform_id": "EUW1",
            "game_version": "16.12.1",
            "game_creation_ms": 1,
            "observations": [
                {
                    "timestamp_ms": 0,
                    "participants": participants,
                    "events": [
                        {
                            "timestamp_ms": 30_000,
                            "event_type": "CHAMPION_KILL",
                            "killer_team_id": 100,
                        },
                    ],
                },
                {
                    "timestamp_ms": 60_000,
                    "participants": participants,
                    "events": [
                        {
                            "timestamp_ms": 55_000,
                            "event_type": "ELITE_MONSTER_KILL",
                            "monster_type": "DRAGON",
                            "killer_team_id": 200,
                        },
                        {
                            "timestamp_ms": 50_000,
                            "event_type": "CHAMPION_KILL",
                            "killer_team_id": 100,
                        },
                    ],
                },
            ],
        },
        "event_index": {"teamfight_ms": [30_000]},
        "labels": [
            {"timestamp_ms": 0, **{name: 0 for name in LABELS}},
            {"timestamp_ms": 60_000, **{name: 1 for name in LABELS}},
        ],
    }


def test_tabular_features_are_strictly_observed_and_ignore_future_index():
    payload = _payload("EUW1_1")
    first, second = list(_rows(payload, "EUW1_1", "y_dragon_30"))
    assert len(FEATURES) == len(first[0])
    assert first[0][FEATURES.index("recent_kills_blue")] == 0
    assert first[0][FEATURES.index("dragons_red")] == 0
    assert math.isnan(first[0][FEATURES.index("minutes_since_dragon")])
    assert second[0][FEATURES.index("recent_kills_blue")] == 1
    assert second[0][FEATURES.index("dragons_red")] == 1
    assert second[0][FEATURES.index("minutes_since_dragon")] == pytest.approx(5 / 60)
    assert second[0][FEATURES.index("gold_diff")] == -25
    assert first[1] == 0 and second[1] == 1
    payload["event_index"]["teamfight_ms"] = [0, 30_000, 60_000]
    assert next(_rows(payload, "EUW1_1", "y_dragon_30"))[0][3] == first[0][3]

    payload["timeline"]["observations"][1]["participants"][0]["position"] = None
    assert math.isnan(list(_rows(payload, "EUW1_1", "y_dragon_30"))[1][0][-1])
    payload["labels"][0]["y_dragon_30"] = 2
    with pytest.raises(ValueError, match="binary"):
        list(_rows(payload, "EUW1_1", "y_dragon_30"))


def test_matrix_checks_processed_checksum_and_observation_count(tmp_path):
    processed = tmp_path / "processed"
    (processed / "matches").mkdir(parents=True)
    content = json.dumps(_payload("EUW1_1")).encode()
    (processed / "matches" / "EUW1_1.json").write_bytes(content)
    record = SimpleNamespace(observations=2, sha256=hashlib.sha256(content).hexdigest())
    x, y = _matrix(processed, [{"match_id": "EUW1_1"}], {"EUW1_1": record}, "y_dragon_30", "train")
    assert x.shape == (2, len(FEATURES))
    assert y.tolist() == [0, 1]
    with pytest.raises(ValueError, match="checksum"):
        _matrix(
            processed,
            [{"match_id": "EUW1_1"}],
            {"EUW1_1": SimpleNamespace(observations=2, sha256="0" * 64)},
            "y_dragon_30",
            "train",
        )
    with pytest.raises(ValueError, match="observation count"):
        _matrix(
            processed,
            [{"match_id": "EUW1_1"}],
            {"EUW1_1": SimpleNamespace(observations=3, sha256=record.sha256)},
            "y_dragon_30",
            "train",
        )


def _large_contract(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    processed.mkdir()
    records = []
    partitions = {"train": [], "calibration": [], "test": []}
    for index in range(36000):
        match_id = f"EUW1_{index + 1}"
        partition = "train" if index < 24000 else "calibration" if index < 30000 else "test"
        partitions[partition].append({"match_id": match_id})
        records.append(
            {
                "match_id": match_id,
                "game_version": "16.12.1",
                "observations": 2,
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
        "matches": records,
        "contains_player_identifiers": False,
    }
    (processed / "processing-manifest.json").write_text(json.dumps(manifest))
    frozen = {"partitions": partitions}
    monkeypatch.setattr("league_ews.tabular_baseline.freeze_final_split", lambda *args: frozen)
    split = tmp_path / "split.json"
    split.write_text(json.dumps(frozen))
    split_sha = hashlib.sha256(split.read_bytes()).hexdigest()
    floor = tmp_path / "floor"
    floor.mkdir()
    floor_model = {"schema_version": "league-ews-baseline-floor-v1", "split_sha256": split_sha}
    (floor / "model.json").write_text(json.dumps(floor_model))
    floor_sha = hashlib.sha256((floor / "model.json").read_bytes()).hexdigest()
    floor_report = {
        "schema_version": "league-ews-baseline-floor-calibration-v1",
        "model_sha256": floor_sha,
        "split_sha256": split_sha,
        "train_matches": 24000,
        "calibration_matches": 6000,
        "test_matches_unread": 6000,
        "macro_average_precision": {"B0": 0.05, "B1": 0.1, "B2": 0.2},
    }
    (floor / "calibration-report.json").write_text(json.dumps(floor_report))
    return processed, split, floor, floor_sha


def test_one_target_checkpoint_and_all_target_summary(tmp_path, monkeypatch):
    processed, split, floor, floor_sha = _large_contract(tmp_path, monkeypatch)
    assert _bound_floor(floor, hashlib.sha256(split.read_bytes()).hexdigest()) == floor_sha

    def fake_matrix(_root, _entries, _by_id, _label, partition):
        if partition == "train":
            return np.zeros((6, len(FEATURES)), dtype=np.float32), np.array([0, 1, 0, 1, 0, 1])
        return np.zeros((4, len(FEATURES)), dtype=np.float32), np.array([0, 1, 0, 1])

    monkeypatch.setattr("league_ews.tabular_baseline._matrix", fake_matrix)
    output = tmp_path / "b3"
    args = (
        tmp_path / "raw",
        processed,
        tmp_path / "frame",
        tmp_path / "g2",
        tmp_path / "audit",
        split,
        floor,
        output,
    )
    first = run_final_tabular(*args, "y_baron_10")
    assert first["label"] == "y_baron_10"
    assert first["floor_model_sha256"] == floor_sha
    assert first["test_matches_unread"] == 6000
    assert "EUW1_1" not in json.dumps(first)
    assert run_final_tabular(*args, "y_baron_10") == first
    for label in LABELS[1:]:
        model_path = output / f"model.{label}.joblib"
        model_path.write_bytes(b"model")
        report = dict(first, label=label, model_sha256=hashlib.sha256(b"model").hexdigest())
        (output / f"report.{label}.json").write_text(json.dumps(report))
    summary = summarize_final_tabular(output, floor)
    assert summary["targets"] == 12
    assert summary["calibration_macro_average_precision"]["B3"] == pytest.approx(0.5)
    assert summary["test_matches_unread"] == 6000
    assert "EUW1_1" not in json.dumps(summary)
    (output / "model.y_baron_10.joblib").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="audited inputs"):
        run_final_tabular(*args, "y_baron_10")
    with pytest.raises(ValueError, match="frozen inputs"):
        summarize_final_tabular(output, floor)


def test_floor_binding_and_unsupported_label_fail_closed(tmp_path, monkeypatch):
    processed, split, floor, _ = _large_contract(tmp_path, monkeypatch)
    args = (
        tmp_path / "raw",
        processed,
        tmp_path / "frame",
        tmp_path / "g2",
        tmp_path / "audit",
        split,
        floor,
        tmp_path / "b3",
    )
    with pytest.raises(ValueError, match="Unsupported"):
        run_final_tabular(*args, "y_win_30")
    model = json.loads((floor / "model.json").read_text())
    model["split_sha256"] = "0" * 64
    (floor / "model.json").write_text(json.dumps(model))
    with pytest.raises(ValueError, match="B0-B2 artifacts"):
        run_final_tabular(*args, "y_baron_20")
