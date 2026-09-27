"""M1 calibration requires all seeds and preserves the sealed test partition."""

import hashlib
import json

import numpy as np
import pytest

from league_ews import m1_calibration
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.graph import FEATURE_NAMES
from league_ews.m1_backend import TorchM1Backend
from league_ews.m1_graph_window import EDGE_TYPES
from league_ews.m1_normalizer import CONTINUOUS
from league_ews.m1_training_plan import SEEDS


def _calibration_fixture(tmp_path, monkeypatch):
    pytest.importorskip("torch")
    stage = tmp_path / "staging"
    shard_dir = stage / "shards"
    shard_dir.mkdir(parents=True)
    manifest_bytes = b"private-staging-manifest\n"
    (stage / "staging-manifest.json").write_bytes(manifest_bytes)
    normalizer = {
        "schema_version": "league-ews-m1-normalizer-v1",
        "node_features": list(FEATURE_NAMES),
        "normalized_feature_indices": list(CONTINUOUS),
        "mean": [0.0] * 7,
        "scale": [1.0] * 7,
    }
    normalizer_path = tmp_path / "normalizer.json"
    normalizer_path.write_text(json.dumps(normalizer))
    nodes = np.zeros((100, 8, 12, len(FEATURE_NAMES)), dtype=np.float32)
    nodes[:, -1, :10, 0] = 1
    nodes[:, -1, 10:, 1] = 1
    edges = np.zeros((100, 8, len(EDGE_TYPES), 12, 12), dtype=np.bool_)
    mask = np.zeros((100, 8), dtype=np.bool_)
    mask[:, -1] = True
    ages = np.zeros((100, 8), dtype=np.float32)
    hazards = np.zeros((100, 3, 6), dtype=np.float32)
    hazards[::7, 0, 1] = 1
    hazards[::5, 1, 2] = 1
    hazards[::3, 2, 0] = 1
    targets = np.maximum.accumulate(hazards, axis=-1)[:, :, [0, 1, 2, 5]]
    shard_path = shard_dir / "calibration.00000.npz"
    np.savez_compressed(
        shard_path,
        nodes=nodes,
        edges=edges,
        history_mask=mask,
        ages_minutes=ages,
        hazard_targets=hazards,
        targets=targets.reshape(100, len(LABELS)).astype(np.int8),
        match_offsets=np.arange(101, dtype=np.int64),
    )
    entry = {
        "partition": "calibration",
        "file": shard_path.name,
        "observations": 100,
        "sha256": hashlib.sha256(shard_path.read_bytes()).hexdigest(),
    }
    monkeypatch.setattr(m1_calibration, "TRAIN_SHARDS", 1)
    monkeypatch.setattr(m1_calibration, "CAL_SHARDS", 1)
    monkeypatch.setattr(m1_calibration, "CAL_MATCHES", 100)
    monkeypatch.setattr(
        m1_calibration,
        "_bound_inputs",
        lambda *args: ({"shards": [{"partition": "train"}, entry]}, normalizer, "f" * 64),
    )
    backend = TorchM1Backend(SEEDS[0])
    hashes = {str(seed): str(seed) for seed in SEEDS}
    states = {SEEDS[0]: {"device": "cpu", "backend": backend.state_dict()}}
    monkeypatch.setattr(m1_calibration, "_completed_checkpoints", lambda *args: (hashes, states))
    args = (
        stage,
        normalizer_path,
        tmp_path / "plan.yaml",
        tmp_path / "hazards.yaml",
        tmp_path / "freeze.json",
        tmp_path / "training",
        tmp_path / "scoring",
    )
    return args, entry


def test_calibration_scores_all_horizons_and_recovers_report(tmp_path, monkeypatch):
    args, _ = _calibration_fixture(tmp_path, monkeypatch)
    report = m1_calibration.score_m1_calibration_seed(*args, seed=SEEDS[0])
    assert report["calibration_matches"] == 100
    assert report["calibration_observations"] == 100
    assert report["test_matches_unread"] == 6000
    assert set(report["metrics"]) == set(LABELS)
    score_file = args[-1] / f"seed-{SEEDS[0]}" / "calibration-scores.npz"
    with np.load(score_file, allow_pickle=False) as stored:
        risk = stored["probabilities"].reshape(100, 3, 4)
        assert np.all(np.diff(risk, axis=-1) >= 0)
        assert np.all((risk >= 0) & (risk <= 1))
        assert stored["match_offsets"][-1] == 100
    assert m1_calibration.score_m1_calibration_seed(*args, seed=SEEDS[0]) == report
    (score_file.parent / "calibration-report.json").unlink()
    assert m1_calibration.score_m1_calibration_seed(*args, seed=SEEDS[0]) == report
    score_file.write_bytes(score_file.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="Existing"):
        m1_calibration.score_m1_calibration_seed(*args, seed=SEEDS[0])


def test_incomplete_seed_blocks_calibration_and_changed_shard_fails(tmp_path, monkeypatch):
    args, entry = _calibration_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        m1_calibration,
        "_completed_checkpoints",
        lambda *args: (_ for _ in ()).throw(ValueError("Every M1 seed must complete")),
    )
    monkeypatch.setattr(
        m1_calibration,
        "_calibration_shard",
        lambda *args: pytest.fail("incomplete training opened calibration arrays"),
    )
    with pytest.raises(ValueError, match="Every M1 seed must complete"):
        m1_calibration.score_m1_calibration_seed(*args, seed=SEEDS[0])
    monkeypatch.undo()
    args, entry = _calibration_fixture(tmp_path / "second", monkeypatch)
    entry["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="checksum"):
        m1_calibration.score_m1_calibration_seed(*args, seed=SEEDS[0])


def test_completed_checkpoint_gate_checks_every_registered_seed(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    backend = TorchM1Backend(SEEDS[0])
    freeze_sha = "f" * 64
    for seed in SEEDS:
        folder = tmp_path / f"seed-{seed}"
        folder.mkdir()
        backend.save(
            {
                "schema_version": "league-ews-m1-training-checkpoint-v1",
                "freeze_sha256": freeze_sha,
                "seed": seed,
                "device": "cpu",
                "torch_version": str(torch.__version__),
                "completed_shards": 720,
                "backend": backend.state_dict(),
            },
            str(folder / "checkpoint.pt"),
        )
    hashes, states = m1_calibration._completed_checkpoints(tmp_path, freeze_sha)
    assert len(hashes) == len(states) == 10
    path = tmp_path / f"seed-{SEEDS[-1]}" / "checkpoint.pt"
    value = torch.load(path, weights_only=True)
    value["completed_shards"] = 719
    torch.save(value, path)
    with pytest.raises(ValueError, match="Every M1 seed must complete"):
        m1_calibration._completed_checkpoints(tmp_path, freeze_sha)


def test_cli_exposes_m1_calibration_without_test_inputs():
    args = build_parser().parse_args(
        [
            "score-m1-calibration",
            "--staging-root",
            "stage",
            "--normalizer",
            "norm.json",
            "--plan",
            "plan.yaml",
            "--hazards",
            "hazards.yaml",
            "--freeze",
            "freeze.json",
            "--training-root",
            "training",
            "--output",
            "scoring",
            "--seed",
            "20260915",
        ]
    )
    assert args.seed == SEEDS[0]
    assert not hasattr(args, "test_root")
