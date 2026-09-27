from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from league_ews import b4_summary
from league_ews.b4_plan import SEEDS
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.metrics import probabilistic_metrics


def _experiment(tmp_path, monkeypatch):
    stage = tmp_path / "staging"
    stage.mkdir()
    normalizer = tmp_path / "normalizer.json"
    normalizer.write_text("normalizer\n")
    freeze = tmp_path / "freeze.json"
    freeze.write_text("freeze\n")
    training = tmp_path / "training"
    training.mkdir()
    root = tmp_path / "calibration"
    root.mkdir()
    freeze_sha = hashlib.sha256(freeze.read_bytes()).hexdigest()
    normalizer_sha = hashlib.sha256(normalizer.read_bytes()).hexdigest()
    staging_sha = hashlib.sha256(b"staging\n").hexdigest()
    hashes = {str(seed): f"{seed:064x}" for seed in SEEDS}
    states = {seed: {"device": "cpu", "torch_version": "fake"} for seed in SEEDS}
    monkeypatch.setattr(b4_summary, "freeze_b4_plan", lambda *args: {"seeds": SEEDS})
    monkeypatch.setattr(b4_summary, "_validated_manifest", lambda *args: (b"staging\n", {}))
    monkeypatch.setattr(b4_summary, "_completed_checkpoints", lambda *args: (hashes, states))
    truth = np.zeros((6000, len(LABELS)), dtype=np.int8)
    truth[::7, :] = 1
    offsets = np.arange(6001, dtype=np.int64)
    base = np.linspace(0.01, 0.99, 6000, dtype=np.float32)
    for index, seed in enumerate(SEEDS):
        folder = root / f"seed-{seed}"
        folder.mkdir()
        score_column = np.roll(base, 37 * index)
        scores = np.tile(score_column[:, None], (1, len(LABELS)))
        np.savez_compressed(
            folder / "calibration-scores.npz",
            probabilities=scores,
            targets=truth,
            match_offsets=offsets,
        )
        metrics = {
            label: probabilistic_metrics(truth[:, column], scores[:, column])
            for column, label in enumerate(LABELS)
        }
        report = {
            "schema_version": "league-ews-b4-calibration-v1",
            "seed": seed,
            "freeze_sha256": freeze_sha,
            "normalizer_sha256": normalizer_sha,
            "staging_manifest_sha256": staging_sha,
            "all_seed_checkpoint_sha256": hashes,
            "checkpoint_sha256": hashes[str(seed)],
            "scores_sha256": hashlib.sha256(
                (folder / "calibration-scores.npz").read_bytes()
            ).hexdigest(),
            "device": "cpu",
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
    return stage, normalizer, tmp_path / "plan", freeze, training, root


def test_summary_reports_all_seeds_without_selection_or_test_reads(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    summary = b4_summary.summarize_b4_calibration(*args)
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
    assert b4_summary.summarize_b4_calibration(*args) == summary


def test_summary_detects_mutated_scores_and_missing_seed(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    last = args[-1] / f"seed-{SEEDS[-1]}"
    score_path = last / "calibration-scores.npz"
    score_path.write_bytes(score_path.read_bytes() + b"modified")
    with pytest.raises(ValueError, match="report differs"):
        b4_summary.summarize_b4_calibration(*args)
    assert not (args[-1] / "ten-seed-summary.json").exists()
    score_path.write_bytes(score_path.read_bytes()[: -len(b"modified")])
    (last / "calibration-report.json").unlink()
    with pytest.raises(FileNotFoundError):
        b4_summary.summarize_b4_calibration(*args)


def test_summary_detects_cross_seed_truth_change(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    last = args[-1] / f"seed-{SEEDS[-1]}"
    report_path = last / "calibration-report.json"
    report = json.loads(report_path.read_text())
    score_path = last / "calibration-scores.npz"
    with np.load(score_path, allow_pickle=False) as saved:
        scores = saved["probabilities"]
        truth = saved["targets"].copy()
        offsets = saved["match_offsets"]
    truth[1, 0] = 1
    np.savez_compressed(score_path, probabilities=scores, targets=truth, match_offsets=offsets)
    report["scores_sha256"] = hashlib.sha256(score_path.read_bytes()).hexdigest()
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="truth or match order"):
        b4_summary.summarize_b4_calibration(*args)


def test_cli_exposes_summary_without_test_path():
    args = build_parser().parse_args(
        [
            "summarize-b4-calibration",
            "--staging-root",
            "stage",
            "--normalizer",
            "norm",
            "--plan",
            "plan",
            "--freeze",
            "freeze",
            "--training-root",
            "train",
            "--calibration-root",
            "cal",
        ]
    )
    assert args.calibration_root.name == "cal"
    assert not hasattr(args, "test_root")
