from __future__ import annotations

import json

import numpy as np
import pytest

from league_ews import b4_training
from league_ews.b4_backend import TorchBackend, right_pad_sequences
from league_ews.b4_sequence import SEQUENCE_FEATURES
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.tabular_baseline import FEATURES


def _batch(rows=4):
    x = np.zeros((rows, 8, len(SEQUENCE_FEATURES)), dtype=np.float32)
    mask = np.zeros((rows, 8), dtype=np.bool_)
    mask[:, -1] = True
    mask[1::2, -2] = True
    x[:, -1, 0] = np.arange(rows)
    x[1::2, -2, 0] = 2
    targets = np.zeros((rows, len(LABELS)), dtype=np.int8)
    targets[1::2, :] = 1
    return x, mask, targets


def test_history_is_packed_without_left_padding_leakage():
    x, mask, _ = _batch()
    x[0, 0, 0] = 9000  # invalid padding content is ignored by the mask
    packed, lengths = right_pad_sequences(x, mask)
    assert lengths.tolist() == [1, 2, 1, 2]
    assert packed[0, 0, 0] == 0
    assert packed[1, :2, 0].tolist() == [2, 1]
    assert np.all(packed[0, 1:] == 0)
    mask[0, 5] = True
    with pytest.raises(ValueError, match="contiguous"):
        right_pad_sequences(x, mask)


def test_cpu_gru_trains_and_roundtrips_checkpoint(tmp_path):
    torch = pytest.importorskip("torch")
    x, mask, targets = _batch()
    backend = TorchBackend(20260915)
    loss, rows = backend.train_shard(x, mask, targets, seed=20260915)
    assert rows == 4
    assert np.isfinite(loss)
    packed, lengths = right_pad_sequences(x, mask)
    backend.gru.eval()
    backend.head.eval()
    with torch.no_grad():
        before = backend._logits(torch.from_numpy(packed), torch.from_numpy(lengths)).clone()
    path = tmp_path / "checkpoint.pt"
    backend.save({"backend": backend.state_dict(), "step": 1}, str(path))
    recovered = TorchBackend(20260915)
    saved = recovered.load(str(path))
    assert saved["step"] == 1
    recovered.load_state_dict(saved["backend"])
    recovered.gru.eval()
    recovered.head.eval()
    with torch.no_grad():
        after = recovered._logits(torch.from_numpy(packed), torch.from_numpy(lengths))
    assert torch.equal(before, after)
    duplicate = TorchBackend(20260915)
    duplicate_loss, _ = duplicate.train_shard(x, mask, targets, seed=20260915)
    assert duplicate_loss == loss
    assert all(
        torch.equal(left, right)
        for left, right in zip(backend.gru.parameters(), duplicate.gru.parameters(), strict=True)
    )


class _FakeBackend:
    calls = 0

    def __init__(self, seed, device):
        self.count = 0
        self.device = device
        self.version = "fake"

    def train_shard(self, inputs, mask, targets, *, seed):
        assert len(inputs) == 500 and seed >= 20260915
        self.count += 1
        _FakeBackend.calls += 1
        return 0.25, len(inputs)

    def state_dict(self):
        return {"count": self.count}

    def load_state_dict(self, state):
        self.count = state["count"]

    def save(self, state, path):
        with open(path, "w") as handle:
            json.dump(state, handle)

    def load(self, path):
        with open(path) as handle:
            return json.load(handle)


def test_bounded_seed_resume_and_binding(tmp_path, monkeypatch):
    stage = tmp_path / "staging"
    (stage / "shards").mkdir(parents=True)
    x, mask, targets = _batch(500)
    np.savez_compressed(
        stage / "shards" / "train.npz",
        inputs=x,
        history_mask=mask,
        targets=targets,
        match_offsets=np.arange(501),
    )
    manifest = {"shards": [{"partition": "train", "file": "train.npz", "observations": 500}] * 48}
    monkeypatch.setattr(b4_training, "_validated_manifest", lambda root: (b"manifest", manifest))
    monkeypatch.setattr(
        b4_training,
        "freeze_b4_plan",
        lambda *args: {"seeds": [20260915]},
    )
    monkeypatch.setattr(b4_training, "_new_backend", _FakeBackend)
    normalizer = {
        "schema_version": "league-ews-b4-normalizer-v1",
        "features": list(FEATURES),
        "mean": [0.0] * len(FEATURES),
        "scale": [1.0] * len(FEATURES),
    }
    norm = tmp_path / "normalizer.json"
    norm.write_text(json.dumps(normalizer))
    freeze = tmp_path / "freeze.json"
    freeze.write_text("frozen")
    _FakeBackend.calls = 0
    args = (stage, norm, tmp_path / "plan", freeze, tmp_path / "out")
    first = b4_training.train_b4_seed(*args, seed=20260915, max_new_shards=1)
    assert first["completed_shards"] == 1
    assert first["device"] == "cpu"
    assert first["calibration_matches_unread"] == 6000
    with pytest.raises(ValueError, match="checkpoint differs"):
        b4_training.train_b4_seed(*args, seed=20260915, device="cuda")
    second = b4_training.train_b4_seed(*args, seed=20260915, max_new_shards=1)
    assert second["completed_shards"] == 2
    assert _FakeBackend.calls == 2
    freeze.write_text("changed")
    with pytest.raises(ValueError, match="checkpoint differs"):
        b4_training.train_b4_seed(*args, seed=20260915)


def test_cuda_requires_a_supported_runtime():
    with pytest.raises(RuntimeError, match="CUDA is unavailable"):
        TorchBackend(20260915, "cuda")


def test_train_rejects_unfrozen_seed_and_invalid_budget(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="budget"):
        b4_training.train_b4_seed(
            tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, seed=1, max_new_shards=0
        )
    monkeypatch.setattr(b4_training, "freeze_b4_plan", lambda *args: {"seeds": [1]})
    with pytest.raises(ValueError, match="seed"):
        b4_training.train_b4_seed(tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, seed=2)


def test_calibration_shard_cannot_be_loaded(tmp_path):
    with pytest.raises(ValueError, match="calibration"):
        b4_training._shard(tmp_path, {"partition": "calibration"}, {})


def test_cli_exposes_bounded_seed_training():
    args = build_parser().parse_args(
        [
            "train-b4-seed",
            "--staging-root",
            "stage",
            "--normalizer",
            "norm.json",
            "--plan",
            "plan.yaml",
            "--freeze",
            "freeze.json",
            "--output",
            "out",
            "--seed",
            "20260915",
            "--device",
            "cpu",
            "--max-new-shards",
            "1",
        ]
    )
    assert args.seed == 20260915 and args.device == "cpu" and args.max_new_shards == 1
