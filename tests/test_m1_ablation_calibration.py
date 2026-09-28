"""Graph ablation scoring preserves the ten-seed gate and sealed test."""

import hashlib

import numpy as np
import pytest

from league_ews import m1_ablation_calibration as scorer
from league_ews.cli import build_parser
from league_ews.m1_training_plan import SEEDS


class FakeBackend:
    def __init__(self, seed, device, *, node_count, relation_count):
        assert seed == SEEDS[0] and device == "cpu"
        assert (node_count, relation_count) == (10, 3)
        self.device = device
        self.version = "fake"

    def load_state_dict(self, state):
        assert state == {"frozen": True}

    def predict_shard(self, nodes, edges, mask, ages):
        assert nodes.shape == (2, 8, 10, 11)
        assert edges.shape == (2, 8, 3, 10, 10)
        return np.tile([0.1, 0.2, 0.3, 0.4] * 3, (2, 1)).astype(np.float32)


def _inputs(tmp_path, monkeypatch):
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "staging-manifest.json").write_text("manifest")
    normalizer = tmp_path / "normalizer.json"
    normalizer.write_text("normalizer")
    training_freeze = tmp_path / "training-freeze.json"
    training_freeze.write_text("training")
    ablation_freeze = tmp_path / "ablation-freeze.json"
    ablation_freeze.write_text("ablation")
    training_sha = hashlib.sha256(training_freeze.read_bytes()).hexdigest()
    monkeypatch.setattr(scorer, "CAL_SHARDS", 1)
    monkeypatch.setattr(scorer, "CAL_MATCHES", 2)
    monkeypatch.setattr(scorer, "TRAIN_SHARDS", 1)
    monkeypatch.setattr(
        scorer,
        "freeze_m1_ablations",
        lambda *args: {"training_freeze_sha256": training_sha, "split_sha256": "split"},
    )
    monkeypatch.setattr(
        scorer,
        "_bound_inputs",
        lambda *args: (
            {
                "split_sha256": "split",
                "shards": [{"partition": "train"}, {"partition": "calibration"}],
            },
            {},
            training_sha,
        ),
    )
    monkeypatch.setattr(
        scorer,
        "_completed_variant_checkpoints",
        lambda *args: (
            {str(seed): f"sha-{seed}" for seed in SEEDS},
            {SEEDS[0]: {"device": "cpu", "backend": {"frozen": True}}},
        ),
    )
    nodes = np.zeros((2, 8, 12, 11), dtype=np.float32)
    edges = np.zeros((2, 8, 5, 12, 12), dtype=np.bool_)
    mask = np.zeros((2, 8), dtype=np.bool_)
    mask[:, -1] = True
    ages = np.zeros((2, 8), dtype=np.float32)
    truth = np.zeros((2, 12), dtype=np.int8)
    monkeypatch.setattr(
        scorer,
        "_calibration_shard",
        lambda *args: (nodes, edges, mask, ages, truth, np.array([0, 1, 2])),
    )
    monkeypatch.setattr(scorer, "TorchM1Backend", FakeBackend)
    return (
        stage,
        normalizer,
        tmp_path / "plan",
        tmp_path / "hazards",
        training_freeze,
        tmp_path / "ablation-plan",
        ablation_freeze,
        tmp_path / "summary",
        tmp_path / "alerts",
        tmp_path / "training",
        tmp_path / "output",
    )


def test_objective_free_scoring_and_retry(tmp_path, monkeypatch):
    args = _inputs(tmp_path, monkeypatch)
    report = scorer.score_m1_graph_ablation_seed(*args, variant="no-objective-nodes", seed=SEEDS[0])
    assert report["node_count"] == 10 and report["relation_count"] == 3
    assert report["calibration_matches"] == 2
    assert report["test_matches_unread"] == 6000
    scores = args[-1] / "no-objective-nodes" / f"seed-{SEEDS[0]}" / "calibration-scores.npz"
    with np.load(scores, allow_pickle=False) as stored:
        assert stored["probabilities"].shape == (2, 12)
        assert stored["match_offsets"].tolist() == [0, 1, 2]
    assert (
        scorer.score_m1_graph_ablation_seed(*args, variant="no-objective-nodes", seed=SEEDS[0])
        == report
    )
    (scores.parent / "calibration-report.json").unlink()
    assert (
        scorer.score_m1_graph_ablation_seed(*args, variant="no-objective-nodes", seed=SEEDS[0])
        == report
    )
    scores.write_bytes(scores.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Existing"):
        scorer.score_m1_graph_ablation_seed(*args, variant="no-objective-nodes", seed=SEEDS[0])


def test_independent_head_scoring_keeps_unconstrained_predictions(tmp_path, monkeypatch):
    args = _inputs(tmp_path, monkeypatch)

    class IndependentBackend:
        def __init__(self, seed, device, *, node_count, relation_count, output_mode):
            assert (node_count, relation_count, output_mode) == (12, 5, "independent-heads")
            self.device, self.version = device, "fake"

        def load_state_dict(self, state):
            assert state == {"frozen": True}

        def predict_shard(self, nodes, edges, mask, ages):
            return np.tile([0.8, 0.2, 0.7, 0.3] * 3, (len(nodes), 1)).astype(np.float32)

    monkeypatch.setattr(scorer, "TorchM1Backend", IndependentBackend)
    report = scorer.score_m1_graph_ablation_seed(
        *args, variant="independent-horizon-heads", seed=SEEDS[0]
    )
    assert report["output_mode"] == "independent-heads"
    with np.load(
        args[-1] / "independent-horizon-heads" / f"seed-{SEEDS[0]}" / "calibration-scores.npz",
        allow_pickle=False,
    ) as saved:
        assert saved["probabilities"][0, :4].tolist() == pytest.approx([0.8, 0.2, 0.7, 0.3])


def test_fixed_minute_grid_scoring_keeps_genuine_targets(tmp_path, monkeypatch):
    args = _inputs(tmp_path, monkeypatch)

    class StandardBackend:
        def __init__(self, seed, device, *, node_count, relation_count):
            assert (node_count, relation_count) == (12, 5)
            self.device, self.version = device, "fake"

        def load_state_dict(self, state):
            pass

        def predict_shard(self, nodes, edges, mask, ages):
            return np.tile([0.1, 0.2, 0.3, 0.4] * 3, (len(nodes), 1)).astype(np.float32)

    called = []

    def grid(nodes, edges, mask, ages, offsets):
        called.append(offsets.tolist())
        return nodes, edges, mask, ages

    monkeypatch.setattr(scorer, "TorchM1Backend", StandardBackend)
    monkeypatch.setattr(scorer, "fixed_minute_grid", grid)
    report = scorer.score_m1_graph_ablation_seed(
        *args, variant="fixed-minute-grid", seed=SEEDS[0]
    )
    assert called == [[0, 1, 2]] and report["calibration_matches"] == 2


def test_checkpoint_gate_blocks_calibration_reads(tmp_path, monkeypatch):
    args = _inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(
        scorer,
        "_completed_variant_checkpoints",
        lambda *args: (_ for _ in ()).throw(ValueError("All ten graph ablation seeds")),
    )
    monkeypatch.setattr(
        scorer, "_calibration_shard", lambda *args: pytest.fail("opened calibration early")
    )
    with pytest.raises(ValueError, match="All ten graph ablation seeds"):
        scorer.score_m1_graph_ablation_seed(*args, variant="no-objective-nodes", seed=SEEDS[0])


def test_real_checkpoint_gate_checks_all_seeds_and_architecture(tmp_path):
    torch = pytest.importorskip("torch")
    freeze_sha, training_sha = "a" * 64, "b" * 64
    for seed in SEEDS:
        path = tmp_path / "no-objective-nodes" / f"seed-{seed}" / "checkpoint.pt"
        path.parent.mkdir(parents=True)
        torch.save(
            {
                "schema_version": "league-ews-m1-graph-ablation-checkpoint-v1",
                "ablation_freeze_sha256": freeze_sha,
                "training_freeze_sha256": training_sha,
                "variant": "no-objective-nodes",
                "seed": seed,
                "device": "cpu",
                "torch_version": str(torch.__version__),
                "node_count": 10,
                "relation_count": 3,
                "completed_shards": 720,
                "backend": {},
            },
            path,
        )
    hashes, states = scorer._completed_variant_checkpoints(
        tmp_path, "no-objective-nodes", freeze_sha, training_sha
    )
    assert len(hashes) == len(states) == 10
    path = tmp_path / "no-objective-nodes" / f"seed-{SEEDS[-1]}" / "checkpoint.pt"
    state = torch.load(path, weights_only=True)
    state["relation_count"] = 5
    torch.save(state, path)
    with pytest.raises(ValueError, match="checkpoints differ"):
        scorer._completed_variant_checkpoints(
            tmp_path, "no-objective-nodes", freeze_sha, training_sha
        )


def test_cli_exposes_graph_ablation_scoring():
    args = build_parser().parse_args(
        [
            "score-m1-graph-ablation-seed",
            "--staging-root",
            "stage",
            "--normalizer",
            "norm",
            "--training-plan",
            "plan",
            "--hazards",
            "hazards",
            "--training-freeze",
            "freeze",
            "--ablation-plan",
            "ablation-plan",
            "--ablation-freeze",
            "ablation-freeze",
            "--calibration-summary",
            "summary",
            "--alert-summary",
            "alerts",
            "--training-root",
            "training",
            "--output",
            "scores",
            "--variant",
            "no-objective-nodes",
            "--seed",
            str(SEEDS[0]),
        ]
    )
    assert args.variant == "no-objective-nodes" and args.seed == SEEDS[0]
    assert not hasattr(args, "test_root")
