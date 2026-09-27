"""The ten-seed M1 summary audits private scores without test access."""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from league_ews import m1_summary
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.m1_training_plan import SEEDS
from league_ews.metrics import probabilistic_metrics


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _experiment(tmp_path, monkeypatch):
    stage = tmp_path / "staging"
    stage.mkdir()
    (stage / "staging-manifest.json").write_bytes(b"staging\n")
    normalizer = tmp_path / "normalizer.json"
    normalizer.write_bytes(b"normalizer\n")
    training = tmp_path / "training"
    training.mkdir()
    calibration = tmp_path / "calibration"
    calibration.mkdir()
    floor = tmp_path / "floor"
    floor.mkdir()
    (floor / "calibration-report.json").write_bytes(b"floor\n")
    tabular = tmp_path / "tabular"
    tabular.mkdir()
    for label in LABELS:
        (tabular / f"report.{label}.json").write_text(label)
    freeze_sha = "f" * 64
    hashes = {str(seed): f"{seed:064x}" for seed in SEEDS}
    states = {seed: {"device": "cuda", "torch_version": "fake"} for seed in SEEDS}
    monkeypatch.setattr(
        m1_summary, "_bound_inputs", lambda *args: ({"split_sha256": "split"}, {}, freeze_sha)
    )
    monkeypatch.setattr(m1_summary, "_completed_checkpoints", lambda *args: (hashes, states))
    monkeypatch.setattr(
        m1_summary,
        "summarize_final_tabular",
        lambda *args: {
            "split_sha256": "split",
            "targets": len(LABELS),
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
            "calibration_macro_average_precision": {"B3": 0.3},
        },
    )
    truth = np.zeros((6000, 3, 4), dtype=np.int8)
    truth[::7] = 1
    offsets = np.arange(6001, dtype=np.int64)
    base = np.linspace(0, 0.05, 6000, dtype=np.float32)
    for index, seed in enumerate(SEEDS):
        folder = calibration / f"seed-{seed}"
        folder.mkdir()
        probs = np.broadcast_to(
            np.roll(base, 37 * index)[:, None, None]
            + np.arange(4, dtype=np.float32)[None, None, :] * 0.15
            + 0.1,
            (6000, 3, 4),
        ).copy()
        scores = probs.reshape(6000, len(LABELS))
        targets = truth.reshape(6000, len(LABELS))
        score_path = folder / "calibration-scores.npz"
        np.savez_compressed(
            score_path, probabilities=scores, targets=targets, match_offsets=offsets
        )
        metrics = {
            label: probabilistic_metrics(targets[:, column], scores[:, column])
            for column, label in enumerate(LABELS)
        }
        report = {
            "schema_version": "league-ews-m1-calibration-v1",
            "seed": seed,
            "freeze_sha256": freeze_sha,
            "normalizer_sha256": _sha(normalizer.read_bytes()),
            "staging_manifest_sha256": _sha((stage / "staging-manifest.json").read_bytes()),
            "all_seed_checkpoint_sha256": hashes,
            "checkpoint_sha256": hashes[str(seed)],
            "scores_sha256": _sha(score_path.read_bytes()),
            "device": "cuda",
            "torch_version": "fake",
            "calibration_matches": 6000,
            "calibration_observations": 6000,
            "targets": list(LABELS),
            "test_matches_unread": 6000,
            "identifiers_in_report": False,
            "metrics": metrics,
            "macro_average_precision": float(
                np.mean([metrics[label]["average_precision"] for label in LABELS])
            ),
        }
        (folder / "calibration-report.json").write_text(json.dumps(report))
    return (
        stage,
        normalizer,
        tmp_path / "plan",
        tmp_path / "hazards",
        tmp_path / "freeze",
        training,
        calibration,
        floor,
        tabular,
    )


def test_summary_reports_all_seeds_and_b3_without_selection(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    summary = m1_summary.summarize_m1_calibration(*args)
    assert summary["seed_count"] == 10
    assert [record["seed"] for record in summary["seed_results"]] == SEEDS
    assert summary["selected_seed"] is None
    assert summary["test_matches_unread"] == 6000
    assert summary["calibration_observations"] == 6000
    assert set(summary["per_target_average_precision"]) == set(LABELS)
    values = [record["macro_average_precision"] for record in summary["seed_results"]]
    assert summary["macro_average_precision"]["mean"] == pytest.approx(np.mean(values))
    assert summary["macro_average_precision"]["sample_standard_deviation"] == pytest.approx(
        np.std(values, ddof=1)
    )
    assert summary["mean_delta_vs_b3"] == pytest.approx(np.mean(values) - 0.3)
    assert m1_summary.summarize_m1_calibration(*args) == summary


def test_summary_detects_mutated_scores_and_missing_seed(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    last = args[6] / f"seed-{SEEDS[-1]}"
    score_path = last / "calibration-scores.npz"
    score_path.write_bytes(score_path.read_bytes() + b"modified")
    with pytest.raises(ValueError, match="report differs"):
        m1_summary.summarize_m1_calibration(*args)
    assert not (args[6] / "ten-seed-summary.json").exists()
    score_path.write_bytes(score_path.read_bytes()[: -len(b"modified")])
    (last / "calibration-report.json").unlink()
    with pytest.raises(FileNotFoundError):
        m1_summary.summarize_m1_calibration(*args)


def test_summary_detects_cross_seed_truth_and_incoherent_risk(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    last = args[6] / f"seed-{SEEDS[-1]}"
    report_path = last / "calibration-report.json"
    report = json.loads(report_path.read_text())
    score_path = last / "calibration-scores.npz"
    with np.load(score_path, allow_pickle=False) as saved:
        scores = saved["probabilities"].copy()
        truth = saved["targets"].copy()
        offsets = saved["match_offsets"].copy()
    truth[1, 0] = 1
    np.savez_compressed(score_path, probabilities=scores, targets=truth, match_offsets=offsets)
    report["scores_sha256"] = _sha(score_path.read_bytes())
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="truth or match order"):
        m1_summary.summarize_m1_calibration(*args)
    truth[1, 0] = 0
    scores[0, 1] = 0.0
    np.savez_compressed(score_path, probabilities=scores, targets=truth, match_offsets=offsets)
    report["scores_sha256"] = _sha(score_path.read_bytes())
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="frozen partition"):
        m1_summary.summarize_m1_calibration(*args)


def test_summary_rejects_b3_on_different_split(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    monkeypatch.setattr(
        m1_summary,
        "summarize_final_tabular",
        lambda *args: {
            "split_sha256": "different",
            "targets": len(LABELS),
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        },
    )
    with pytest.raises(ValueError, match="different frozen splits"):
        m1_summary.summarize_m1_calibration(*args)


def test_cli_exposes_summary_without_test_path():
    args = build_parser().parse_args(
        [
            "summarize-m1-calibration",
            "--staging-root",
            "stage",
            "--normalizer",
            "norm",
            "--plan",
            "plan",
            "--hazards",
            "hazards",
            "--freeze",
            "freeze",
            "--training-root",
            "training",
            "--calibration-root",
            "calibration",
            "--floor-root",
            "floor",
            "--tabular-root",
            "tabular",
        ]
    )
    assert args.calibration_root.name == "calibration"
    assert not hasattr(args, "test_root")
