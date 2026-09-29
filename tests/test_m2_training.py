"""A hybrid seed cannot fit before its spatial audit and immutable freeze."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from league_ews.cli import build_parser
from league_ews.m1_training_plan import SEEDS
from league_ews.m2_plan import _checked_inputs, freeze_m2_hybrid
from league_ews.m2_training import train_m2_seed


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FakeBackend:
    def __init__(self, seed, device, *, mode):
        self.device = device
        self.version = "fake"

    def train_shard(self, *inputs, seed):
        return 0.2, 12

    def state_dict(self):
        return {"model": "mock"}

    def load_state_dict(self, state):
        if state != self.state_dict():
            raise AssertionError("wrong checkpoint state")

    def save(self, state, path):
        Path(path).write_text(json.dumps(state))

    def load(self, path):
        return json.loads(Path(path).read_text())


class M2TrainingTests(unittest.TestCase):
    def test_plan_requires_actual_audit_and_exact_protocol(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / "stage"
            stage.mkdir()
            (stage / "staging-manifest.json").write_text("manifest")
            audit = root / "audit.json"
            plan = Path(__file__).resolve().parents[1] / "configs/rifthazard-m2-hybrid-plan.yaml"
            source = root / "source"
            source.write_text("source")
            manifest = {"split_sha256": "split"}
            payload = {
                "schema_version": "league-ews-m2-preprocessing-audit-v1",
                "staging_manifest_sha256": _sha(stage / "staging-manifest.json"),
                "training_freeze_sha256": "m1",
                "split_sha256": "split",
                "test_matches_unread": 6000,
                "identifiers_in_report": False,
                "partitions": {"train": {"matches": 24000}, "calibration": {"matches": 6000}},
            }
            audit.write_text(json.dumps(payload))
            args = (stage, source, source, source, source, audit, plan)
            with patch("league_ews.m2_plan._bound_inputs", return_value=(manifest, {}, "m1")):
                self.assertEqual(_checked_inputs(*args)[2], "m1")
                payload["test_matches_unread"] = 0
                audit.write_text(json.dumps(payload))
                with self.assertRaisesRegex(ValueError, "frozen input boundary"):
                    _checked_inputs(*args)

    def test_freeze_and_one_shard_resume_reject_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / "stage"
            stage.mkdir()
            (stage / "staging-manifest.json").write_text("staging")
            normalizer = root / "normalizer.json"
            normalizer.write_text("normalizer")
            m1_freeze = root / "m1-freeze.json"
            m1_freeze.write_text("m1-freeze")
            audit = root / "audit.json"
            audit.write_text("audit")
            plan = root / "m2.yaml"
            plan.write_text("plan")
            m1_plan = root / "m1.yaml"
            m1_plan.write_text("m1-plan")
            hazards = root / "hazards.yaml"
            hazards.write_text("hazards")
            freeze_path = root / "m2-freeze.json"
            manifest = {"split_sha256": "split", "shards": [{"partition": "train"}] * 240}
            with patch("league_ews.m2_plan._checked_inputs", return_value=(manifest, {}, "m1")):
                freeze = freeze_m2_hybrid(
                    stage, normalizer, m1_plan, hazards, m1_freeze, audit, plan, freeze_path
                )
            self.assertEqual(freeze["modes"], ["gated", "ungated", "spatial-only"])
            self.assertEqual(freeze["spatial_audit_sha256"], _sha(audit))
            self.assertEqual(freeze["seeds"], SEEDS)
            self.assertEqual(freeze["test_matches_unread"], 6000)
            output = root / "output"
            with (
                patch("league_ews.m2_training._checked_inputs", return_value=(manifest, {}, "m1")),
                patch("league_ews.m2_training._training_input", return_value=(1, 2, 3, 4, 5, 6)),
                patch("league_ews.m2_training.TorchM2Backend", FakeBackend),
            ):
                params = (stage, normalizer, m1_plan, hazards, m1_freeze, audit, plan, freeze_path, output)
                first = train_m2_seed(*params, mode="gated", seed=SEEDS[0], max_new_shards=1)
                self.assertEqual(first["completed_shards"], 1)
                second = train_m2_seed(*params, mode="gated", seed=SEEDS[0], max_new_shards=1)
                self.assertEqual(second["completed_shards"], 2)
                audit.write_text("changed")
                with self.assertRaisesRegex(ValueError, "prefit freeze"):
                    train_m2_seed(*params, mode="gated", seed=SEEDS[0], max_new_shards=1)

    def test_cli_has_no_test_or_raw_argument(self):
        args = build_parser().parse_args(
            [
                "train-m2-seed",
                "--staging-root", "stage", "--normalizer", "normalizer",
                "--training-plan", "m1-plan", "--hazards", "hazards",
                "--training-freeze", "m1-freeze", "--spatial-audit", "audit",
                "--hybrid-plan", "plan", "--hybrid-freeze", "freeze",
                "--output", "output", "--mode", "gated", "--seed", str(SEEDS[0]),
            ]
        )
        self.assertFalse(hasattr(args, "test_root"))
        self.assertFalse(hasattr(args, "raw"))
