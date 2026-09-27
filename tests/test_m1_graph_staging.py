import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from league_ews import m1_graph_staging
from league_ews.m1_graph_plan import freeze_graph_plan, load_graph_plan

PLAN = Path(__file__).resolve().parents[1] / "configs" / "rifthazard-m1-graph-plan.yaml"


def _save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_graph_freeze_binds_split_and_processing_without_match_reads(tmp_path):
    processed = tmp_path / "processed"
    _save(processed / "processing-manifest.json", {"schema_version": "fixture"})
    processing_sha = hashlib.sha256(
        (processed / "processing-manifest.json").read_bytes()
    ).hexdigest()
    split = tmp_path / "split.json"
    _save(
        split,
        {
            "schema_version": "league-ews-final-split-v1",
            "processing_manifest_sha256": processing_sha,
            "summary": {"counts": {"train": 24000, "calibration": 6000, "test": 6000}},
        },
    )
    output = tmp_path / "private" / "freeze.json"
    first = freeze_graph_plan(PLAN, split, processed, output)
    assert first["test_matches_unread"] == 6000
    assert freeze_graph_plan(PLAN, split, processed, output) == first
    assert "EUW1_" not in output.read_text()
    changed = tmp_path / "changed.yaml"
    changed.write_text(PLAN.read_text().replace("2500", "3000"))
    with pytest.raises(ValueError, match="input contract"):
        load_graph_plan(changed)
    (processed / "processing-manifest.json").write_text("modified")
    with pytest.raises(ValueError, match="not bound"):
        freeze_graph_plan(PLAN, split, processed, output)


def _contract(tmp_path, monkeypatch):
    monkeypatch.setattr(m1_graph_staging, "MATCHES_PER_SHARD", 2)
    partitions = {
        "train": [{"match_id": f"EUW1_{i}"} for i in (1, 2, 3)],
        "calibration": [{"match_id": "EUW1_4"}],
        "test": [{"match_id": "EUW1_5"}],
    }
    bindings = {"split_sha256": "a" * 64, "processing_manifest_sha256": "b" * 64}
    monkeypatch.setattr(
        m1_graph_staging,
        "_bound_inputs",
        lambda *args: (bindings, partitions, {}),
    )
    calls = []

    def materialize(_root, entries, _by_id, _plan):
        assert all(entry["match_id"] != "EUW1_5" for entry in entries)
        calls.append(len(entries))
        return {
            "nodes": np.zeros((len(entries), 8, 12, 11), dtype=np.float32),
            "targets": np.zeros((len(entries), 12), dtype=np.int8),
            "match_offsets": np.arange(len(entries) + 1, dtype=np.int64),
        }

    monkeypatch.setattr(m1_graph_staging, "_materialize", materialize)
    plan_sha, _, _ = load_graph_plan(PLAN)
    freeze = tmp_path / "freeze.json"
    _save(
        freeze,
        {
            "schema_version": "league-ews-m1-graph-freeze-v1",
            "plan_sha256": plan_sha,
            **bindings,
            "train_matches": 24000,
            "calibration_matches": 6000,
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        },
    )
    args = (
        tmp_path / "raw",
        tmp_path / "processed",
        tmp_path / "frame",
        tmp_path / "g2",
        tmp_path / "audit",
        tmp_path / "split",
        PLAN,
        freeze,
        tmp_path / "output",
    )
    return args, calls


def test_m1_staging_is_bounded_resumable_and_checksum_bound(tmp_path, monkeypatch):
    args, calls = _contract(tmp_path, monkeypatch)
    first = m1_graph_staging.stage_m1_graphs(*args, max_new_shards=1)
    assert first["staged_shards"] == 1
    assert first["complete"] is False
    assert m1_graph_staging.stage_m1_graphs(*args, max_new_shards=2)["complete"] is True
    assert calls == [2, 1, 1]
    manifest = (args[-1] / "staging-manifest.json").read_text()
    assert "EUW1_" not in manifest
    shard = args[-1] / "shards" / "train.00000.npz"
    shard.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        m1_graph_staging.stage_m1_graphs(*args)


def test_m1_staging_rejects_changed_freeze(tmp_path, monkeypatch):
    args, _ = _contract(tmp_path, monkeypatch)
    freeze = json.loads(args[-2].read_text())
    freeze["split_sha256"] = "changed"
    _save(args[-2], freeze)
    with pytest.raises(ValueError, match="freeze"):
        m1_graph_staging.stage_m1_graphs(*args)
