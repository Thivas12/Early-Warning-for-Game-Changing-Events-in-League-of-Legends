"""Training-only scaling of the frozen M1 graph inventory."""

import hashlib
import json

import numpy as np
import pytest

from league_ews import m1_normalizer
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.graph import FEATURE_NAMES
from league_ews.m1_graph_window import EDGE_TYPES


def _staged(tmp_path, monkeypatch):
    monkeypatch.setattr(m1_normalizer, "MATCHES_PER_SHARD", 2)
    monkeypatch.setattr(m1_normalizer, "TRAIN_SHARDS", 2)
    monkeypatch.setattr(m1_normalizer, "TOTAL_SHARDS", 3)
    root = tmp_path / "staging"
    directory = root / "shards"
    directory.mkdir(parents=True)
    entries = []
    for i in range(3):
        partition = "train" if i < 2 else "calibration"
        start = i * 2 if i < 2 else 0
        filename = f"{partition}.{start:05d}.npz"
        path = directory / filename
        nodes = np.zeros((2, 8, 12, len(FEATURE_NAMES)), dtype=np.float32)
        nodes[:, -1, :10, 0] = 1
        nodes[:, -1, :10, 3] = (2, 4, 1_000_000)[i]
        nodes[:, -1, :10, 8] = (5, 7, 1_000_000)[i]
        nodes[:, -1, :10, 10] = (0, 1, 1)[i]
        if i == 0:
            nodes[:, -1, :10, 8] = 0
        if i == 1:
            nodes[1, -1, :10, 8] = 9
        nodes[:, -1, 10:, 1] = 1
        mask = np.zeros((2, 8), dtype=np.bool_)
        mask[:, -1] = True
        np.savez_compressed(
            path,
            nodes=nodes,
            edges=np.zeros((2, 8, len(EDGE_TYPES), 12, 12), dtype=np.bool_),
            history_mask=mask,
            ages_minutes=np.zeros((2, 8), dtype=np.float32),
            targets=np.zeros((2, len(LABELS)), dtype=np.int8),
            hazard_targets=np.zeros((2, 3, 6), dtype=np.float32),
            match_offsets=np.arange(3, dtype=np.int64),
        )
        entries.append(
            {
                "partition": partition,
                "start": start,
                "matches": 2,
                "observations": 2,
                "file": filename,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "schema_version": "league-ews-m1-graph-staging-v1",
        "complete": True,
        "steps": 8,
        "edge_types": list(EDGE_TYPES),
        "targets": list(LABELS),
        "matches_per_shard": 2,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
        "split_sha256": "a" * 64,
        "processing_manifest_sha256": "b" * 64,
        "plan_sha256": "c" * 64,
        "freeze_sha256": "d" * 64,
        "shards": entries,
    }
    (root / "staging-manifest.json").write_text(json.dumps(manifest))
    return root


def test_train_only_moments_and_immutability(tmp_path, monkeypatch):
    root = _staged(tmp_path, monkeypatch)
    original = np.load

    def guarded_load(path, *args, **kwargs):
        assert "calibration" not in str(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(np, "load", guarded_load)
    output = root / "normalizer.json"
    summary = m1_normalizer.fit_m1_normalizer(root, output)
    data = json.loads(output.read_text())
    assert summary["training_observations"] == 4
    assert summary["calibration_matches_unread"] == 6000
    assert data["mean"][0] == 3
    assert data["scale"][0] == 1
    assert data["present_counts"][0] == 40
    assert data["mean"][5] == 8
    assert data["scale"][5] == 1
    assert data["present_counts"][5] == 20
    assert "EUW1_" not in output.read_text()
    unchanged = output.read_bytes()
    assert m1_normalizer.fit_m1_normalizer(root, output) == summary
    assert output.read_bytes() == unchanged
    output.write_text("wrong")
    with pytest.raises(ValueError, match="Existing"):
        m1_normalizer.fit_m1_normalizer(root, output)


def test_fit_rejects_incomplete_inventory_or_tampered_calibration(tmp_path, monkeypatch):
    root = _staged(tmp_path, monkeypatch)
    path = root / "staging-manifest.json"
    manifest = json.loads(path.read_text())
    manifest["complete"] = False
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="incomplete"):
        m1_normalizer.fit_m1_normalizer(root, root / "normalizer.json")
    manifest["complete"] = True
    path.write_text(json.dumps(manifest))
    (root / "shards" / "calibration.00000.npz").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        m1_normalizer.fit_m1_normalizer(root, root / "normalizer.json")


def test_apply_preserves_padding_objectives_and_missing_coordinates():
    nodes = np.zeros((1, 8, 12, len(FEATURE_NAMES)), dtype=np.float32)
    mask = np.zeros((1, 8), dtype=np.bool_)
    mask[0, -2:] = True
    nodes[0, -2, 0, 3] = 4
    nodes[0, -1, 0, 3] = 2
    nodes[0, -1, 0, 8] = 0
    nodes[0, -1, 0, 10] = 0
    nodes[0, -1, 1, 8] = 7
    nodes[0, -1, 1, 10] = 1
    nodes[0, -1, 10, 8] = 0.3
    nodes[0, 0, 0, 3] = 123  # masked padding stays unchanged
    stats = {
        "schema_version": "league-ews-m1-normalizer-v1",
        "node_features": list(FEATURE_NAMES),
        "normalized_feature_indices": list(m1_normalizer.CONTINUOUS),
        "mean": [3, 0, 0, 0, 0, 5, 0],
        "scale": [1] * 7,
    }
    result = m1_normalizer.apply_m1_normalizer(nodes, mask, stats)
    assert result[0, -2, 0, 3] == 1
    assert result[0, -1, 0, 3] == -1
    assert result[0, -1, 0, 8] == 0
    assert result[0, -1, 1, 8] == 2
    assert result[0, 0, 0, 3] == 123
    assert result[0, -1, 10, 8] == 0.3
    assert np.array_equal(nodes[0, -1, :2, 3], [2, 0])
    stats["scale"][0] = 0
    with pytest.raises(ValueError, match="invalid"):
        m1_normalizer.apply_m1_normalizer(nodes, mask, stats)


def test_cli_exposes_m1_normalization():
    args = build_parser().parse_args(
        ["fit-m1-normalizer", "--staging-root", "staging", "--output", "normalizer.json"]
    )
    assert args.staging_root.name == "staging"
