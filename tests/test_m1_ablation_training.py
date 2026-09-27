"""Bounded graph ablation training refuses stale freezes and resumes by shard."""

import json

import numpy as np
import pytest

from league_ews import m1_ablation_training as runner
from league_ews.cli import build_parser


class FakeBackend:
    def __init__(self, seed, device):
        self.device = device
        self.version = "fake"
        self.count = 0

    def train_shard(self, nodes, edges, mask, ages, hazards, *, seed):
        assert nodes.shape == (2, 8, 12, 11)
        assert edges.shape == (2, 8, 5, 12, 12)
        assert hazards.shape == (2, 3, 6)
        assert seed >= 20260915
        self.count += 1
        return 0.25, len(nodes)

    def state_dict(self):
        return {"count": self.count}

    def load_state_dict(self, saved):
        self.count = saved["count"]

    def save(self, saved, path):
        with open(path, "w") as handle:
            json.dump(saved, handle)

    def load(self, path):
        with open(path) as handle:
            return json.load(handle)


class FakeObjectiveFreeBackend(FakeBackend):
    def train_shard(self, nodes, edges, mask, ages, hazards, *, seed):
        assert nodes.shape == (2, 8, 10, 11)
        assert edges.shape == (2, 8, 3, 10, 10)
        assert hazards.shape == (2, 3, 6)
        assert seed >= 20260915
        self.count += 1
        return 0.25, len(nodes)


def _inputs(tmp_path, monkeypatch):
    nodes = np.zeros((2, 8, 12, 11), dtype=np.float32)
    edges = np.zeros((2, 8, 5, 12, 12), dtype=np.bool_)
    mask = np.zeros((2, 8), dtype=np.bool_)
    mask[:, -1] = True
    ages = np.zeros((2, 8), dtype=np.float32)
    hazards = np.zeros((2, 3, 6), dtype=np.float32)
    nodes[:, -1, :10, 8:11] = 1.0
    edges[:, -1, :, 0, 1] = True
    inputs = (nodes, edges, mask, ages, hazards)
    monkeypatch.setattr(runner, "TRAIN_SHARDS", 2)
    monkeypatch.setattr(runner, "UNITS_PER_SEED", 6)
    monkeypatch.setattr(
        runner,
        "_bound_inputs",
        lambda *args: ({"split_sha256": "s", "shards": [{}, {}]}, {}, "original"),
    )
    monkeypatch.setattr(runner, "_training_shard", lambda *args: inputs)
    monkeypatch.setattr(
        runner,
        "freeze_m1_ablations",
        lambda *args: {"training_freeze_sha256": runner._sha(b"training"), "split_sha256": "s"},
    )
    monkeypatch.setattr(runner, "_new_backend", FakeBackend)
    monkeypatch.setattr(runner, "_new_objective_free_backend", FakeObjectiveFreeBackend)
    training_freeze = tmp_path / "original.json"
    training_freeze.write_bytes(b"training")
    ablation_freeze = tmp_path / "ablation.json"
    ablation_freeze.write_bytes(b"ablation")
    arguments = (
        tmp_path / "staging",
        tmp_path / "normalizer",
        tmp_path / "training-plan",
        tmp_path / "hazards",
        training_freeze,
        tmp_path / "ablation-plan",
        ablation_freeze,
        tmp_path / "calibration-summary",
        tmp_path / "alert-summary",
        tmp_path / "out",
    )
    return inputs, arguments


def test_checkpoint_resume_and_freeze_binding(tmp_path, monkeypatch):
    _, arguments = _inputs(tmp_path, monkeypatch)
    first = runner.train_m1_graph_ablation_seed(
        *arguments,
        variant="no-positions-or-proximity",
        seed=20260915,
        max_new_shards=1,
    )
    assert first["completed_shards"] == 1
    assert first["total_shards"] == 6
    second = runner.train_m1_graph_ablation_seed(
        *arguments,
        variant="no-positions-or-proximity",
        seed=20260915,
        max_new_shards=1,
    )
    assert second["completed_shards"] == 2
    with pytest.raises(ValueError, match="checkpoint differs"):
        runner.train_m1_graph_ablation_seed(
            *arguments,
            variant="no-positions-or-proximity",
            seed=20260915,
            device="cuda",
        )
    arguments[6].write_bytes(b"changed")
    with pytest.raises(ValueError, match="checkpoint differs"):
        runner.train_m1_graph_ablation_seed(
            *arguments,
            variant="no-positions-or-proximity",
            seed=20260915,
        )


@pytest.mark.parametrize(
    "variant", ("no-interaction-edges", "no-objective-nodes", "no-assistance-history")
)
def test_variants_keep_separate_checkpoints(tmp_path, monkeypatch, variant):
    _, arguments = _inputs(tmp_path, monkeypatch)
    result = runner.train_m1_graph_ablation_seed(*arguments, variant=variant, seed=20260916)
    assert result["completed_shards"] == 1
    assert result["node_count"] == (10 if variant == "no-objective-nodes" else 12)
    assert (arguments[-1] / variant / "seed-20260916" / "checkpoint.pt").is_file()


def test_objective_free_checkpoint_rejects_architecture_change(tmp_path, monkeypatch):
    _, arguments = _inputs(tmp_path, monkeypatch)
    first = runner.train_m1_graph_ablation_seed(
        *arguments, variant="no-objective-nodes", seed=20260915
    )
    assert first["node_count"] == 10 and first["relation_count"] == 3
    checkpoint = arguments[-1] / "no-objective-nodes" / "seed-20260915" / "checkpoint.pt"
    saved = json.loads(checkpoint.read_text())
    saved["node_count"] = 12
    checkpoint.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="checkpoint differs"):
        runner.train_m1_graph_ablation_seed(*arguments, variant="no-objective-nodes", seed=20260915)


def test_reject_unfrozen_and_unimplemented_variants(tmp_path, monkeypatch):
    _, arguments = _inputs(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="supported backend"):
        runner.train_m1_graph_ablation_seed(
            *arguments, variant="independent-horizon-heads", seed=20260915
        )
    arguments[6].unlink()
    with pytest.raises(ValueError, match="freeze must be created"):
        runner.train_m1_graph_ablation_seed(
            *arguments, variant="no-interaction-edges", seed=20260915
        )
    with pytest.raises(ValueError, match="seed or shard budget"):
        runner.train_m1_graph_ablation_seed(
            *arguments,
            variant="no-interaction-edges",
            seed=20260915,
            max_new_shards=0,
        )


def test_cli_exposes_bounded_variant_options():
    parser = build_parser()
    args = parser.parse_args(
        [
            "train-m1-graph-ablation-seed",
            "--staging-root",
            "stage",
            "--normalizer",
            "normalizer.json",
            "--training-plan",
            "training.yaml",
            "--hazards",
            "hazards.yaml",
            "--training-freeze",
            "original.json",
            "--ablation-plan",
            "ablations.yaml",
            "--ablation-freeze",
            "ablations.json",
            "--calibration-summary",
            "calibration.json",
            "--alert-summary",
            "alert.json",
            "--output",
            "private",
            "--variant",
            "no-objective-nodes",
            "--seed",
            "20260915",
            "--device",
            "cuda",
            "--max-new-shards",
            "1",
        ]
    )
    assert args.variant == "no-objective-nodes"
    assert args.device == "cuda"
