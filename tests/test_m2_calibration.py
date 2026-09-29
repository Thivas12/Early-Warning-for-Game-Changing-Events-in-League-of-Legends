"""Hybrid scoring is restricted to complete seeds and the calibration split."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from league_ews.cli import build_parser
from league_ews.m1_training_plan import SEEDS
from league_ews.m2_calibration import score_m2_calibration_seed


class FakeBackend:
    def __init__(self, seed, device, *, mode):
        self.device = device
        self.version = "fake"

    def load_state_dict(self, state):
        if state != {"model": "mock"}:
            raise AssertionError("wrong checkpoint")

    def predict_shard(self, raw, nodes, edges, mask, ages):
        return np.full((len(raw), 12), 0.2, dtype=np.float32)


class M2CalibrationTests(unittest.TestCase):
    def test_complete_mode_scores_only_calibration_and_checks_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / "stage"
            stage.mkdir()
            (stage / "staging-manifest.json").write_text("manifest")
            normalizer = root / "normalizer.json"
            normalizer.write_text("normalizer")
            source = root / "source"
            source.write_text("source")
            output = root / "scores"
            entry = {"partition": "calibration"}
            manifest = {
                "shards": [{"partition": "train"}] * 240 + [entry] * 60,
                "split_sha256": "split",
            }
            states = {
                seed: {"backend": {"model": "mock"}, "device": "cpu"} for seed in SEEDS
            }
            hashes = {str(seed): str(seed) for seed in SEEDS}
            args = (stage, normalizer, source, source, source, source, source, source,
                    root / "training", output)
            with (
                patch("league_ews.m2_calibration._bound_hybrid", return_value=(manifest, {}, "bound")),
                patch("league_ews.m2_calibration._completed_checkpoints", return_value=(hashes, states)),
                patch("league_ews.m2_calibration._raw_calibration_nodes", return_value=np.zeros((100, 8, 12, 11), dtype=np.float32)),
                patch("league_ews.m2_calibration._calibration_shard", return_value=(
                    np.zeros((100, 8, 12, 11), dtype=np.float32),
                    np.zeros((100, 8, 5, 12, 12), dtype=np.bool_),
                    np.ones((100, 8), dtype=np.bool_),
                    np.zeros((100, 8), dtype=np.float32),
                    np.zeros((100, 12), dtype=np.int8),
                    np.arange(101, dtype=np.int64),
                )),
                patch("league_ews.m2_calibration.TorchM2Backend", FakeBackend),
            ):
                result = score_m2_calibration_seed(*args, mode="gated", seed=SEEDS[0])
                self.assertEqual(result["calibration_matches"], 6000)
                self.assertEqual(result["test_matches_unread"], 6000)
                self.assertEqual(result["calibration_observations"], 6000)
                self.assertEqual(score_m2_calibration_seed(*args, mode="gated", seed=SEEDS[0]), result)
                report = output / "gated" / f"seed-{SEEDS[0]}" / "calibration-report.json"
                altered = json.loads(report.read_text())
                altered["checkpoint_sha256"] = "bad"
                report.write_text(json.dumps(altered))
                with self.assertRaisesRegex(ValueError, "differs from frozen inputs"):
                    score_m2_calibration_seed(*args, mode="gated", seed=SEEDS[0])

    def test_parser_excludes_test_paths(self):
        args = build_parser().parse_args(
            [
                "score-m2-calibration", "--staging-root", "stage", "--normalizer", "norm",
                "--training-plan", "m1-plan", "--hazards", "hazards",
                "--training-freeze", "m1-freeze", "--spatial-audit", "audit",
                "--hybrid-plan", "m2-plan", "--hybrid-freeze", "m2-freeze",
                "--training-root", "training", "--output", "calibration",
                "--mode", "gated", "--seed", str(SEEDS[0]),
            ]
        )
        self.assertFalse(hasattr(args, "test_root"))
        self.assertFalse(hasattr(args, "raw"))
