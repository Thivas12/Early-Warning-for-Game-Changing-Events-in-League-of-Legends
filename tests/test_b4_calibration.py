from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from league_ews import b4_calibration
from league_ews.b4_backend import TorchBackend
from league_ews.b4_sequence import SEQUENCE_FEATURES
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.tabular_baseline import FEATURES


def _private_experiment(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    stage = tmp_path / "staging"
    (stage / "shards").mkdir(parents=True)
    freeze = tmp_path / "freeze.json"
    freeze.write_text("frozen\n")
    norm = tmp_path / "normalizer.json"
    norm.write_text(
        json.dumps(
            {
                "schema_version": "league-ews-b4-normalizer-v1",
                "features": list(FEATURES),
                "mean": [0.0] * len(FEATURES),
                "scale": [1.0] * len(FEATURES),
            }
        )
    )
    seeds = list(range(20260915, 20260925))
    training = tmp_path / "training"
    freeze_sha = hashlib.sha256(freeze.read_bytes()).hexdigest()
    for seed in seeds:
        backend = TorchBackend(seed)
        directory = training / f"seed-{seed}"
        directory.mkdir(parents=True)
        backend.save(
            {
                "schema_version": "league-ews-b4-training-checkpoint-v1",
                "freeze_sha256": freeze_sha,
                "seed": seed,
                "device": "cpu",
                "torch_version": str(torch.__version__),
                "completed_shards": 144,
                "backend": backend.state_dict(),
            },
            str(directory / "checkpoint.pt"),
        )
    shards = [{"partition": "train", "file": "unread-train.npz"}] * 48
    for index in range(12):
        filename = f"calibration.{index * 500:05d}.npz"
        x = np.zeros((500, 8, len(SEQUENCE_FEATURES)), dtype=np.float32)
        x[:, -1, 0] = np.arange(500) / 500
        mask = np.zeros((500, 8), dtype=np.bool_)
        mask[:, -1] = True
        truth = np.zeros((500, len(LABELS)), dtype=np.int8)
        truth[::7, :] = 1
        np.savez_compressed(
            stage / "shards" / filename,
            inputs=x,
            history_mask=mask,
            targets=truth,
            match_offsets=np.arange(501, dtype=np.int64),
        )
        shards.append({"partition": "calibration", "file": filename, "observations": 500})
    monkeypatch.setattr(b4_calibration, "freeze_b4_plan", lambda *args: {"seeds": seeds})
    monkeypatch.setattr(
        b4_calibration,
        "_validated_manifest",
        lambda *args: (b"staging-manifest\n", {"shards": shards}),
    )
    return stage, norm, tmp_path / "plan", freeze, training, tmp_path / "scores"


def test_calibration_scores_all_targets_and_preserves_test_holdout(tmp_path, monkeypatch):
    args = _private_experiment(tmp_path, monkeypatch)
    report = b4_calibration.score_b4_calibration_seed(*args, seed=20260915)
    assert report["calibration_matches"] == 6000
    assert report["calibration_observations"] == 6000
    assert report["test_matches_unread"] == 6000
    assert set(report["metrics"]) == set(LABELS)
    assert 0 <= report["macro_average_precision"] <= 1
    assert len(report["all_seed_checkpoint_sha256"]) == 10
    scores_path = args[-1] / "seed-20260915" / "calibration-scores.npz"
    with np.load(scores_path, allow_pickle=False) as scores:
        assert scores["probabilities"].shape == (6000, 12)
        assert scores["targets"].shape == (6000, 12)
        assert scores["match_offsets"].shape == (6001,)
        assert scores["match_offsets"][-1] == 6000
        assert np.all((scores["probabilities"] >= 0) & (scores["probabilities"] <= 1))
    assert b4_calibration.score_b4_calibration_seed(*args, seed=20260915) == report
    report_path = args[-1] / "seed-20260915" / "calibration-report.json"
    report_path.unlink()  # interruption after score-file rename is recoverable
    assert b4_calibration.score_b4_calibration_seed(*args, seed=20260915) == report


def test_incomplete_or_changed_seed_blocks_calibration_before_arrays(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    args = _private_experiment(tmp_path, monkeypatch)
    checkpoint = args[-2] / "seed-20260924" / "checkpoint.pt"
    saved = torch.load(checkpoint, weights_only=True)
    saved["completed_shards"] = 143
    torch.save(saved, checkpoint)
    monkeypatch.setattr(
        b4_calibration,
        "_load_calibration_shard",
        lambda *args: pytest.fail("incomplete training opened calibration arrays"),
    )
    with pytest.raises(ValueError, match="Every B4 seed must complete"):
        b4_calibration.score_b4_calibration_seed(*args, seed=20260915)


def test_calibration_rejects_unfrozen_seed_and_changed_score_file(tmp_path, monkeypatch):
    args = _private_experiment(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="absent"):
        b4_calibration.score_b4_calibration_seed(*args, seed=1)
    b4_calibration.score_b4_calibration_seed(*args, seed=20260915)
    scores = args[-1] / "seed-20260915" / "calibration-scores.npz"
    scores.write_bytes(scores.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="Existing B4 calibration differs"):
        b4_calibration.score_b4_calibration_seed(*args, seed=20260915)


def test_cli_exposes_calibration_without_test_inputs():
    args = build_parser().parse_args(
        [
            "score-b4-calibration",
            "--staging-root",
            "stage",
            "--normalizer",
            "norm.json",
            "--plan",
            "plan.yaml",
            "--freeze",
            "freeze.json",
            "--training-root",
            "training",
            "--output",
            "out",
            "--seed",
            "20260915",
        ]
    )
    assert args.seed == 20260915
    assert not hasattr(args, "test_root")
