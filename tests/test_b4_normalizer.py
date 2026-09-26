from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from league_ews.b4_normalizer import apply_b4_normalizer, fit_b4_normalizer
from league_ews.b4_sequence import SEQUENCE_FEATURES
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.tabular_baseline import FEATURES


def _staged(tmp_path):
    root = tmp_path / "staging"
    directory = root / "shards"
    directory.mkdir(parents=True)
    shards = []
    for i in range(60):
        partition = "train" if i < 48 else "calibration"
        start = (i if i < 48 else i - 48) * 500
        filename = f"{partition}.{start:05d}.npz"
        inputs = np.zeros((500, 8, len(SEQUENCE_FEATURES)), dtype=np.float32)
        inputs[:, -1, 0] = 2 if i % 2 == 0 else 4
        inputs[:, -1, 1] = 99999 if i >= 48 else 0
        inputs[:, -1, len(FEATURES) + 1] = 1  # missing: ignored in fit
        if i >= 48:
            inputs[:, -1, 0] = 1_000_000  # calibration cannot influence fit
        mask = np.zeros((500, 8), dtype=np.bool_)
        mask[:, -1] = True
        path = directory / filename
        np.savez_compressed(
            path,
            inputs=inputs,
            history_mask=mask,
            targets=np.zeros((500, len(LABELS)), dtype=np.int8),
            match_offsets=np.arange(501, dtype=np.int64),
        )
        shards.append(
            {
                "partition": partition,
                "start": start,
                "matches": 500,
                "observations": 500,
                "file": filename,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "schema_version": "league-ews-b4-staging-v1",
        "complete": True,
        "sequence_steps": 8,
        "sequence_features": list(SEQUENCE_FEATURES),
        "targets": list(LABELS),
        "matches_per_shard": 500,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
        "split_sha256": "a" * 64,
        "processing_manifest_sha256": "b" * 64,
        "shards": shards,
    }
    (root / "staging-manifest.json").write_text(json.dumps(manifest))
    return root


def test_train_only_fit_is_immutable_and_excludes_calibration(tmp_path, monkeypatch):
    root = _staged(tmp_path)
    original_load = np.load

    def guarded_load(path, *args, **kwargs):
        assert "calibration" not in str(path)
        return original_load(path, *args, **kwargs)

    monkeypatch.setattr(np, "load", guarded_load)
    output = root / "normalizer.json"
    summary = fit_b4_normalizer(root, output)
    normalizer = json.loads(output.read_text())
    assert summary["training_observations"] == 24000
    assert summary["test_matches_unread"] == 6000
    assert normalizer["mean"][0] == 3
    assert normalizer["scale"][0] == 1
    assert normalizer["present_counts"][0] == 24000
    assert normalizer["present_counts"][1] == 0
    assert normalizer["mean"][1] == 0
    assert normalizer["scale"][1] == 1
    assert "EUW1_" not in output.read_text()
    first = output.read_bytes()
    assert fit_b4_normalizer(root, output) == summary
    assert output.read_bytes() == first
    output.write_text("wrong")
    with pytest.raises(ValueError, match="Existing"):
        fit_b4_normalizer(root, output)


def test_fit_requires_complete_checksum_bound_staging(tmp_path):
    root = _staged(tmp_path)
    manifest_path = root / "staging-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["complete"] = False
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="incomplete"):
        fit_b4_normalizer(root, root / "normalizer.json")
    manifest["complete"] = True
    manifest_path.write_text(json.dumps(manifest))
    (root / "shards" / "calibration.00000.npz").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        fit_b4_normalizer(root, root / "normalizer.json")


def test_apply_scales_real_present_values_without_touching_other_channels():
    inputs = np.zeros((1, 8, len(SEQUENCE_FEATURES)), dtype=np.float32)
    mask = np.zeros((1, 8), dtype=np.bool_)
    mask[0, -2:] = True
    inputs[0, -2, 0] = 4
    inputs[0, -1, 0] = 2
    inputs[0, -1, 1] = 0
    inputs[0, -1, len(FEATURES) + 1] = 1
    inputs[0, -2, -1] = 1.1
    stats = {
        "schema_version": "league-ews-b4-normalizer-v1",
        "features": list(FEATURES),
        "mean": [3.0] + [0.0] * (len(FEATURES) - 1),
        "scale": [1.0] * len(FEATURES),
    }
    scaled = apply_b4_normalizer(inputs, mask, stats)
    assert scaled[0, -2, 0] == 1
    assert scaled[0, -1, 0] == -1
    assert np.array_equal(scaled[0, :-2], inputs[0, :-2])
    assert np.array_equal(scaled[:, :, len(FEATURES) :], inputs[:, :, len(FEATURES) :])
    assert np.array_equal(inputs[0, -2:, 0], [4, 2])
    stats["scale"][0] = 0
    with pytest.raises(ValueError, match="invalid"):
        apply_b4_normalizer(inputs, mask, stats)


def test_cli_registers_training_normalizer():
    args = build_parser().parse_args(
        ["fit-b4-normalizer", "--staging-root", "staging", "--output", "normalizer.json"]
    )
    assert args.staging_root.name == "staging"
