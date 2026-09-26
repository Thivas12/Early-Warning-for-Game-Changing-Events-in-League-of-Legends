from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews import b4_staging
from league_ews.baseline_floor import LABELS


def _contract(tmp_path, monkeypatch):
    monkeypatch.setattr(b4_staging, "MATCHES_PER_SHARD", 2)
    partitions = {
        "train": [{"match_id": f"EUW1_{i}"} for i in (1, 2, 3)],
        "calibration": [{"match_id": f"EUW1_{i}"} for i in (4, 5)],
        "test": [{"match_id": "EUW1_6"}],
    }
    bindings = {
        "schema_version": "league-ews-b4-staging-v1",
        "split_sha256": "a" * 64,
        "processing_manifest_sha256": "b" * 64,
        "sequence_steps": 8,
        "matches_per_shard": 2,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    monkeypatch.setattr(
        b4_staging,
        "_bound_inputs",
        lambda *args: (
            bindings,
            partitions,
            {str(item["match_id"]): object() for group in partitions.values() for item in group},
        ),
    )
    calls = []

    def materialize(_root, entries, _by_id):
        assert all(entry["match_id"] != "EUW1_6" for entry in entries)
        calls.append(len(entries))
        n = len(entries)
        return {
            "inputs": np.zeros((n, 8, 55), dtype=np.float32),
            "history_mask": np.ones((n, 8), dtype=np.bool_),
            "targets": np.zeros((n, 12), dtype=np.int8),
            "match_offsets": np.arange(n + 1, dtype=np.int64),
        }

    monkeypatch.setattr(b4_staging, "_materialize", materialize)
    args = (
        tmp_path / "raw",
        tmp_path / "processed",
        tmp_path / "frame",
        tmp_path / "g2",
        tmp_path / "audit",
        tmp_path / "split",
        tmp_path / "output",
    )
    return args, calls


def test_bounded_staging_resumes_and_verifies_checksums(tmp_path, monkeypatch):
    args, calls = _contract(tmp_path, monkeypatch)
    first = b4_staging.stage_b4_sequences(*args, max_new_shards=1)
    assert first["staged_matches"] == 2
    assert first["complete"] is False
    assert first["test_matches_unread"] == 6000
    assert "EUW1_" not in json.dumps(first)
    assert b4_staging.stage_b4_sequences(*args, max_new_shards=2)["complete"] is True
    assert calls == [2, 1, 2]
    assert b4_staging.stage_b4_sequences(*args)["staged_shards"] == 3
    shard = args[-1] / "shards" / "train.00000.npz"
    shard.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        b4_staging.stage_b4_sequences(*args)


def test_orphan_shard_is_checked_against_recomputed_source(tmp_path, monkeypatch):
    args, calls = _contract(tmp_path, monkeypatch)
    b4_staging.stage_b4_sequences(*args, max_new_shards=1)
    orphan = args[-1] / "shards" / "train.00002.npz"
    arrays = b4_staging._materialize(args[1], [{"match_id": "EUW1_3"}], {})
    np.savez_compressed(orphan, **arrays)
    assert b4_staging.stage_b4_sequences(*args, max_new_shards=1)["staged_matches"] == 3
    assert calls == [2, 1, 1]
    manifest = json.loads((args[-1] / "staging-manifest.json").read_text())
    assert manifest["shards"][1]["sha256"] == hashlib.sha256(orphan.read_bytes()).hexdigest()


def test_invalid_budget_and_unregistered_files_stop(tmp_path, monkeypatch):
    args, _ = _contract(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="positive"):
        b4_staging.stage_b4_sequences(*args, max_new_shards=0)
    args[-1].mkdir()
    (args[-1] / "unexpected").write_text("no")
    with pytest.raises(ValueError, match="Unregistered"):
        b4_staging.stage_b4_sequences(*args, max_new_shards=1)


def test_materialize_verifies_source_bytes_and_match_offsets(tmp_path):
    participants = [
        {
            "participant_id": i,
            "team_id": 100 if i <= 5 else 200,
            "total_gold": 500,
            "xp": 0,
            "level": 1,
            "lane_minions": 0,
            "jungle_minions": 0,
            "position": None,
        }
        for i in range(1, 11)
    ]
    root = tmp_path / "processed"
    (root / "matches").mkdir(parents=True)
    records = {}
    for i, count in ((1, 2), (2, 3)):
        match_id = f"EUW1_{i}"
        times = [60_000 * step for step in range(count)]
        payload = {
            "schema_version": "league-ews-processed-match-v1",
            "timeline": {
                "match_id": match_id,
                "platform_id": "EUW1",
                "game_version": "16.16.1",
                "game_creation_ms": 1,
                "observations": [
                    {"timestamp_ms": time, "participants": participants, "events": []}
                    for time in times
                ],
            },
            "event_index": {"baron_ms": [], "dragon_ms": [], "teamfight_ms": []},
            "labels": [{"timestamp_ms": time, **dict.fromkeys(LABELS, 0)} for time in times],
        }
        content = json.dumps(payload).encode()
        (root / "matches" / f"{match_id}.json").write_bytes(content)
        records[match_id] = SimpleNamespace(
            sha256=hashlib.sha256(content).hexdigest(), observations=count
        )
    entries = [{"match_id": "EUW1_1"}, {"match_id": "EUW1_2"}]
    arrays = b4_staging._materialize(root, entries, records)
    assert arrays["match_offsets"].tolist() == [0, 2, 5]
    assert arrays["targets"].shape == (5, len(LABELS))
    assert arrays["history_mask"].sum(axis=1).tolist() == [1, 2, 1, 2, 3]
    records["EUW1_2"].sha256 = "0" * 64
    with pytest.raises(ValueError, match="checksum"):
        b4_staging._materialize(root, entries, records)
