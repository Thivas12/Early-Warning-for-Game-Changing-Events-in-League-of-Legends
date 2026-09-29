"""Small CPU graphs verify hazard masking and bounded M1 checkpoint recovery."""

import hashlib
import json

import numpy as np
import pytest

from league_ews import m1_training
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.graph import FEATURE_NAMES
from league_ews.m1_backend import TorchM1Backend, at_risk_mask, right_pad_graphs
from league_ews.m1_graph_window import EDGE_TYPES
from league_ews.m1_normalizer import CONTINUOUS


def _batch(rows=4):
    nodes = np.zeros((rows, 8, 12, len(FEATURE_NAMES)), dtype=np.float32)
    edges = np.zeros((rows, 8, len(EDGE_TYPES), 12, 12), dtype=np.bool_)
    mask = np.zeros((rows, 8), dtype=np.bool_)
    ages = np.zeros((rows, 8), dtype=np.float32)
    mask[:, -1] = True
    mask[1::2, -2] = True
    ages[1::2, -2] = 1.0
    nodes[:, -1, :10, 0] = 1
    nodes[1::2, -2, :10, 0] = 1
    nodes[:, -1, 10:, 1] = 1
    nodes[1::2, -2, 10:, 1] = 1
    edges[:, -1, 0, 0, 1] = True
    edges[1::2, -2, 0, 0, 1] = True
    hazards = np.zeros((rows, 3, 6), dtype=np.float32)
    hazards[1::2, 0, 1] = 1
    hazards[1::2, 1, 1] = 1  # another event type in the same bin remains at risk
    labels = np.maximum.accumulate(hazards, axis=-1)[:, :, [0, 1, 2, 5]]
    return nodes, edges, mask, ages, hazards, labels.reshape(rows, len(LABELS)).astype(np.int8)


def test_at_risk_mask_keeps_event_bin_and_other_event_types():
    *_, hazards, _ = _batch(2)
    risk = at_risk_mask(hazards)
    assert risk[1, 0].tolist() == [1, 1, 0, 0, 0, 0]
    assert risk[1, 1].tolist() == [1, 1, 0, 0, 0, 0]
    assert risk[1, 2].tolist() == [1] * 6
    hazards[0, 0, 0] = hazards[0, 0, 1] = 1
    with pytest.raises(ValueError, match="at most one onset"):
        at_risk_mask(hazards)


def test_right_padding_preserves_real_frames_and_rejects_future_order():
    nodes, edges, mask, ages, _, _ = _batch(2)
    packed_nodes, packed_edges, packed_ages, lengths = right_pad_graphs(nodes, edges, mask, ages)
    assert lengths.tolist() == [1, 2]
    assert packed_nodes[1, 0, 0, 0] == nodes[1, -2, 0, 0]
    assert packed_edges[1, 1, 0, 0, 1]
    assert packed_ages[1, :2].tolist() == [1, 0]
    bad = ages.copy()
    bad[1, -2] = -1
    with pytest.raises(ValueError, match="shapes"):
        right_pad_graphs(nodes, edges, mask, bad)
    bad = mask.copy()
    bad[0, -3] = True
    with pytest.raises(ValueError, match="contiguous"):
        right_pad_graphs(nodes, edges, bad, ages)


def test_cpu_graph_trains_deterministically_and_restores_checkpoint(tmp_path):
    torch = pytest.importorskip("torch")
    nodes, edges, mask, ages, hazards, _ = _batch()
    backend = TorchM1Backend(20260915)
    loss, rows = backend.train_shard(nodes, edges, mask, ages, hazards, seed=20260915)
    assert rows == 4 and np.isfinite(loss)
    x, e, a, lengths = right_pad_graphs(nodes, edges, mask, ages)
    backend.model.eval()
    with torch.inference_mode():
        before = backend.model(
            torch.from_numpy(x),
            torch.from_numpy(e),
            torch.from_numpy(a),
            torch.from_numpy(lengths),
        ).clone()
    path = tmp_path / "checkpoint.pt"
    backend.save({"backend": backend.state_dict(), "step": 1}, str(path))
    recovered = TorchM1Backend(20260915)
    saved = recovered.load(str(path))
    recovered.load_state_dict(saved["backend"])
    recovered.model.eval()
    with torch.inference_mode():
        after = recovered.model(
            torch.from_numpy(x),
            torch.from_numpy(e),
            torch.from_numpy(a),
            torch.from_numpy(lengths),
        )
    assert torch.equal(before, after)
    duplicate = TorchM1Backend(20260915)
    duplicate_loss, _ = duplicate.train_shard(nodes, edges, mask, ages, hazards, seed=20260915)
    assert duplicate_loss == loss


def test_objective_free_backend_trains_and_scores_ten_nodes():
    pytest.importorskip("torch")
    nodes, edges, mask, ages, hazards, _ = _batch(2)
    nodes = nodes[:, :, :10].copy()
    edges = edges[:, :, :3, :10, :10].copy()
    backend = TorchM1Backend(20260915, node_count=10, relation_count=3)
    loss, rows = backend.train_shard(nodes, edges, mask, ages, hazards, seed=20260915)
    predictions = backend.predict_shard(nodes, edges, mask, ages)
    assert rows == 2 and np.isfinite(loss)
    assert predictions.shape == (2, 12) and np.isfinite(predictions).all()
    with pytest.raises(ValueError, match="frozen causal window shapes"):
        backend.predict_shard(_batch(2)[0], edges, mask, ages)


def test_independent_heads_use_direct_labels_and_allow_nonmonotone_scores():
    torch = pytest.importorskip("torch")
    nodes, edges, mask, ages, hazards, labels = _batch(2)
    backend = TorchM1Backend(20260915, output_mode="independent-heads")
    assert backend.model.head.out_features == 12
    with pytest.raises(ValueError, match="twelve exact-future labels"):
        backend.train_shard(nodes, edges, mask, ages, hazards, seed=20260915)
    loss, rows = backend.train_shard(nodes, edges, mask, ages, labels, seed=20260915)
    assert rows == 2 and np.isfinite(loss)
    with torch.no_grad():
        backend.model.head.weight.zero_()
        backend.model.head.bias.copy_(torch.tensor([1.0, -1.0, 0.5, -0.5] * 3, dtype=torch.float32))
    predictions = backend.predict_shard(nodes, edges, mask, ages)
    assert predictions.shape == (2, 12)
    assert np.any(np.diff(predictions.reshape(2, 3, 4), axis=-1) < 0)
    assert np.all((predictions > 0) & (predictions < 1))


class _FakeBackend:
    calls = 0

    def __init__(self, _seed, device):
        self.count = 0
        self.device = device
        self.version = "fake"

    def train_shard(self, nodes, edges, mask, ages, hazards, *, seed):
        assert len(nodes) == 100 and seed >= 20260915
        assert edges.shape[2] == 5 and mask.shape[1] == ages.shape[1] == 8
        assert hazards.shape == (100, 3, 6)
        self.count += 1
        _FakeBackend.calls += 1
        return 0.25, len(nodes)

    def state_dict(self):
        return {"count": self.count}

    def load_state_dict(self, value):
        self.count = value["count"]

    def save(self, value, path):
        with open(path, "w") as handle:
            json.dump(value, handle)

    def load(self, path):
        with open(path) as handle:
            return json.load(handle)


def _staged_shard(tmp_path):
    root = tmp_path / "stage"
    folder = root / "shards"
    folder.mkdir(parents=True)
    nodes, edges, mask, ages, hazards, labels = _batch(100)
    path = folder / "train.00000.npz"
    np.savez_compressed(
        path,
        nodes=nodes,
        edges=edges,
        history_mask=mask,
        ages_minutes=ages,
        hazard_targets=hazards,
        targets=labels,
        match_offsets=np.arange(101, dtype=np.int64),
    )
    entry = {
        "partition": "train",
        "file": path.name,
        "observations": 100,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    normalizer = {
        "schema_version": "league-ews-m1-normalizer-v1",
        "node_features": list(FEATURE_NAMES),
        "normalized_feature_indices": list(CONTINUOUS),
        "mean": [0.0] * 7,
        "scale": [1.0] * 7,
    }
    return root, entry, normalizer


def test_training_shard_checks_hazards_and_checksum(tmp_path):
    root, entry, normalizer = _staged_shard(tmp_path)
    assert m1_training._training_shard(root, entry, normalizer)[-1].shape == (100, 3, 6)
    assert m1_training._training_shard(root, entry, normalizer, independent_labels=True)[
        -1
    ].shape == (100, 12)
    entry["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="checksum"):
        m1_training._training_shard(root, entry, normalizer)
    entry["partition"] = "calibration"
    with pytest.raises(ValueError, match="calibration"):
        m1_training._training_shard(root, entry, normalizer)


def test_training_rejects_hazard_label_disagreement_even_with_valid_checksum(tmp_path):
    root, entry, normalizer = _staged_shard(tmp_path)
    path = root / "shards" / entry["file"]
    with np.load(path, allow_pickle=False) as shard:
        arrays = {name: shard[name] for name in shard.files}
    arrays["targets"][1, 0] = 1
    np.savez_compressed(path, **arrays)
    entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="disagree"):
        m1_training._training_shard(root, entry, normalizer)


def test_bounded_resume_rejects_changed_freeze_and_device(tmp_path, monkeypatch):
    root, entry, normalizer = _staged_shard(tmp_path)
    manifest = {"shards": [entry, entry]}
    binding = ["a" * 64]
    monkeypatch.setattr(m1_training, "TRAIN_SHARDS", 2)
    monkeypatch.setattr(m1_training, "UNITS_PER_SEED", 6)
    monkeypatch.setattr(
        m1_training, "_bound_inputs", lambda *args: (manifest, normalizer, binding[0])
    )
    monkeypatch.setattr(m1_training, "_new_backend", _FakeBackend)
    _FakeBackend.calls = 0
    args = (
        root,
        tmp_path / "norm",
        tmp_path / "plan",
        tmp_path / "hazards",
        tmp_path / "freeze",
        tmp_path / "out",
    )
    first = m1_training.train_m1_seed(*args, seed=20260915, max_new_shards=1)
    assert first["completed_shards"] == 1 and first["total_shards"] == 6
    with pytest.raises(ValueError, match="checkpoint differs"):
        m1_training.train_m1_seed(*args, seed=20260915, device="cuda")
    second = m1_training.train_m1_seed(*args, seed=20260915, max_new_shards=1)
    assert second["completed_shards"] == 2 and _FakeBackend.calls == 2
    binding[0] = "b" * 64
    with pytest.raises(ValueError, match="checkpoint differs"):
        m1_training.train_m1_seed(*args, seed=20260915)


def test_cli_exposes_m1_seed_training():
    args = build_parser().parse_args(
        [
            "train-m1-seed",
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
            "--output",
            "out",
            "--seed",
            "20260915",
            "--device",
            "cuda",
            "--max-new-shards",
            "1",
        ]
    )
    assert args.device == "cuda" and args.seed == 20260915
