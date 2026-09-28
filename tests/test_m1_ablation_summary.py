"""Audited ten-seed graph removal comparison on calibration only."""

import hashlib
import json

import numpy as np
import pytest

from league_ews import m1_ablation_summary as summary_module
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.m1_training_plan import SEEDS
from league_ews.metrics import probabilistic_metrics


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _fixture(tmp_path, monkeypatch, variant="no-objective-nodes"):
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "staging-manifest.json").write_text("manifest")
    normalizer = tmp_path / "normalizer"
    normalizer.write_text("norm")
    training_freeze = tmp_path / "training-freeze"
    training_freeze.write_text("training")
    ablation_freeze = tmp_path / "ablation-freeze"
    ablation_freeze.write_text("ablation")
    training_sha, ablation_sha = _sha(b"training"), _sha(b"ablation")
    original = {
        "schema_version": "league-ews-m1-ten-seed-calibration-v1",
        "freeze_sha256": training_sha,
        "split_sha256": "split",
        "seed_count": len(SEEDS),
        "seed_results": [{"seed": seed, "macro_average_precision": 0.4} for seed in SEEDS],
        "macro_average_precision": {"mean": 0.4},
        "per_target_average_precision": {label: {"mean": 0.4} for label in LABELS},
        "selected_seed": None,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    original_path = tmp_path / "m1-summary.json"
    original_path.write_text(json.dumps(original))
    hashes = {str(seed): f"hash-{seed}" for seed in SEEDS}
    states = {seed: {"device": "cpu", "torch_version": "fake"} for seed in SEEDS}
    monkeypatch.setattr(
        summary_module,
        "freeze_m1_ablations",
        lambda *args: {"training_freeze_sha256": training_sha, "split_sha256": "split"},
    )
    monkeypatch.setattr(
        summary_module,
        "_bound_inputs",
        lambda *args: ({"split_sha256": "split"}, {}, training_sha),
    )
    monkeypatch.setattr(
        summary_module, "_completed_variant_checkpoints", lambda *args: (hashes, states)
    )
    calibration = tmp_path / "calibration"
    truth = np.zeros((6000, len(LABELS)), dtype=np.int8)
    truth[::7] = 1
    offsets = np.arange(6001, dtype=np.int64)
    for index, seed in enumerate(SEEDS):
        folder = calibration / variant / f"seed-{seed}"
        folder.mkdir(parents=True)
        base = np.roll(np.linspace(0, 0.05, 6000, dtype=np.float32), index * 37)
        scores = (
            np.broadcast_to(
                base[:, None, None] + np.arange(4, dtype=np.float32)[None, None, :] * 0.15 + 0.1,
                (6000, 3, 4),
            )
            .copy()
            .reshape(6000, len(LABELS))
        )
        if variant == "independent-horizon-heads":
            scores = scores.reshape(6000, 3, 4)[:, :, ::-1].copy().reshape(6000, len(LABELS))
        score_path = folder / "calibration-scores.npz"
        np.savez_compressed(score_path, probabilities=scores, targets=truth, match_offsets=offsets)
        metrics = {
            label: probabilistic_metrics(truth[:, column], scores[:, column])
            for column, label in enumerate(LABELS)
        }
        report = {
            "schema_version": "league-ews-m1-graph-ablation-calibration-v1",
            "variant": variant,
            "seed": seed,
            "ablation_freeze_sha256": ablation_sha,
            "training_freeze_sha256": training_sha,
            "staging_manifest_sha256": _sha(b"manifest"),
            "normalizer_sha256": _sha(b"norm"),
            "all_seed_checkpoint_sha256": hashes,
            "checkpoint_sha256": hashes[str(seed)],
            "scores_sha256": _sha(score_path.read_bytes()),
            "device": "cpu",
            "torch_version": "fake",
            "node_count": 10 if variant == "no-objective-nodes" else 12,
            "relation_count": 3 if variant == "no-objective-nodes" else 5,
            **({"output_mode": "independent-heads"}
               if variant == "independent-horizon-heads" else {}),
            "calibration_matches": 6000,
            "calibration_observations": 6000,
            "targets": list(LABELS),
            "test_matches_unread": 6000,
            "identifiers_in_report": False,
            "metrics": metrics,
            "macro_average_precision": float(
                np.mean([float(metrics[label]["average_precision"] or 0.0) for label in LABELS])
            ),
        }
        (folder / "calibration-report.json").write_text(json.dumps(report))
    return (
        stage,
        normalizer,
        tmp_path / "plan",
        tmp_path / "hazards",
        training_freeze,
        tmp_path / "ablation-plan",
        ablation_freeze,
        original_path,
        tmp_path / "alerts",
        tmp_path / "training",
        calibration,
    )


def test_summary_audits_ten_seeds_and_preserves_test(tmp_path, monkeypatch):
    args = _fixture(tmp_path, monkeypatch)
    result = summary_module.summarize_m1_graph_ablation(*args, variant="no-objective-nodes")
    assert result["seed_count"] == 10
    assert result["node_count"] == 10 and result["relation_count"] == 3
    assert result["test_matches_unread"] == 6000 and result["selected_seed"] is None
    assert result["mean_delta_vs_m1"] == pytest.approx(
        result["macro_average_precision"]["mean"] - 0.4
    )
    assert summary_module.summarize_m1_graph_ablation(*args, variant="no-objective-nodes") == result


def test_independent_head_summary_allows_nonmonotone_scores(tmp_path, monkeypatch):
    args = _fixture(tmp_path, monkeypatch, variant="independent-horizon-heads")
    report = summary_module.summarize_m1_graph_ablation(
        *args, variant="independent-horizon-heads"
    )
    assert report["output_mode"] == "independent-heads"
    assert report["seed_count"] == 10


def test_summary_detects_mutated_scores_and_cross_seed_truth(tmp_path, monkeypatch):
    args = _fixture(tmp_path, monkeypatch)
    folder = args[-1] / "no-objective-nodes" / f"seed-{SEEDS[-1]}"
    score_path = folder / "calibration-scores.npz"
    score_path.write_bytes(score_path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="report differs"):
        summary_module.summarize_m1_graph_ablation(*args, variant="no-objective-nodes")
    score_path.write_bytes(score_path.read_bytes()[:-8])
    report_path = folder / "calibration-report.json"
    report = json.loads(report_path.read_text())
    with np.load(score_path, allow_pickle=False) as stored:
        scores, truth, offsets = (
            stored["probabilities"].copy(),
            stored["targets"].copy(),
            stored["match_offsets"].copy(),
        )
    truth[1, 0] = 1
    np.savez_compressed(score_path, probabilities=scores, targets=truth, match_offsets=offsets)
    report["scores_sha256"] = _sha(score_path.read_bytes())
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="truth or match order"):
        summary_module.summarize_m1_graph_ablation(*args, variant="no-objective-nodes")


def test_summary_cli_has_no_test_path():
    args = build_parser().parse_args(
        [
            "summarize-m1-graph-ablation",
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
            "m1-summary",
            "--alert-summary",
            "alerts",
            "--training-root",
            "training",
            "--calibration-root",
            "calibration",
            "--variant",
            "no-objective-nodes",
        ]
    )
    assert args.variant == "no-objective-nodes"
    assert not hasattr(args, "test_root")
