"""Verify the held-out half and score integrity of M2 calibration utility."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.m2_utility import _later_alerts, _validate_scores, audit_m2_calibration_utility


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class M2UtilityTests(unittest.TestCase):
    def test_complete_synthetic_calibration_audit_and_checksum_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            processed = root / "processed"
            processed.mkdir()
            manifest = processed / "processing-manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            split_file = root / "split.json"
            entries = [
                {
                    "match_id": f"synthetic-{index}",
                    "regional_route": "europe" if index % 2 == 0 else "americas",
                    "game_creation_ms": index,
                    "game_version_patch": "16.16",
                }
                for index in range(6000)
            ]
            _write_json(
                split_file,
                {
                    "schema_version": "league-ews-final-split-v1",
                    "processing_manifest_sha256": _sha(manifest),
                    "partitions": {"calibration": entries},
                    "summary": {
                        "counts": {"train": 24000, "calibration": 6000, "test": 6000},
                        "patches": {"calibration": ["16.16"]},
                    },
                },
            )
            freeze = root / "freeze.json"
            _write_json(
                freeze,
                {
                    "schema_version": "league-ews-m2-hybrid-freeze-v1",
                    "split_sha256": _sha(split_file),
                    "modes": ["gated", "ungated", "spatial-only"],
                    "seeds": [1, 2],
                    "test_matches_unread": 6000,
                },
            )
            m1 = root / "m1.json"
            _write_json(
                m1,
                {
                    "schema_version": "league-ews-m1-ten-seed-calibration-v1",
                    "split_sha256": _sha(split_file),
                    "seed_count": 2,
                    "selected_seed": None,
                    "macro_average_precision": {"mean": 0.3},
                    "b3_macro_average_precision": 0.2,
                    "test_matches_unread": 6000,
                },
            )
            diagnostic = root / "diagnostic.json"
            _write_json(
                diagnostic,
                {
                    "schema_version": "league-ews-m1-alert-opportunity-diagnostic-v1",
                    "calibration_summary_sha256": _sha(m1),
                    "split_sha256": _sha(split_file),
                    "processing_manifest_sha256": _sha(manifest),
                    "seed_count": 2,
                    "later_half_summary": {},
                    "test_matches_unread": 6000,
                },
            )
            calibration = root / "calibration"
            checkpoints = {"1": "a", "2": "b"}
            scores = np.full((6000, 12), 0.2, dtype=np.float32)
            truth = np.zeros((6000, 12), dtype=np.int8)
            offsets = np.arange(6001, dtype=np.int64)
            metrics = {label: {"average_precision": 0.0, "brier": 0.04} for label in LABELS}
            for seed in (1, 2):
                folder = calibration / "gated" / f"seed-{seed}"
                folder.mkdir(parents=True)
                score_file = folder / "calibration-scores.npz"
                np.savez_compressed(
                    score_file,
                    probabilities=scores,
                    targets=truth,
                    match_offsets=offsets,
                )
                _write_json(
                    folder / "calibration-report.json",
                    {
                        "schema_version": "league-ews-m2-hybrid-calibration-v1",
                        "mode": "gated",
                        "seed": seed,
                        "freeze_sha256": _sha(freeze),
                        "scores_sha256": _sha(score_file),
                        "calibration_matches": 6000,
                        "calibration_observations": 6000,
                        "targets": list(LABELS),
                        "test_matches_unread": 6000,
                        "identifiers_in_report": False,
                        "all_seed_checkpoint_sha256": checkpoints,
                        "checkpoint_sha256": checkpoints[str(seed)],
                        "metrics": metrics,
                        "macro_average_precision": 0.0,
                    },
                )
            records = [
                SimpleNamespace(match_id=f"synthetic-{index}", sha256="bound", observations=1)
                for index in range(36000)
            ]
            row = {"timestamp_ms": 0, **dict.fromkeys(LABELS, 0)}
            payload = {
                "timeline": {"observations": [{"timestamp_ms": 0}]},
                "labels": [row],
                "event_index": {
                    "baron_ms": [],
                    "dragon_ms": [],
                    "teamfight_ms": [],
                },
            }
            with (
                patch("league_ews.m2_utility.SEEDS", [1, 2]),
                patch(
                    "league_ews.m2_utility.ProcessingManifest.model_validate_json",
                    return_value=SimpleNamespace(matches=records),
                ),
                patch("league_ews.m2_utility._read_match", return_value=payload),
                patch(
                    "league_ews.m2_utility._completed_checkpoints",
                    return_value=(checkpoints, {}),
                ),
                patch(
                    "league_ews.m2_utility.probabilistic_metrics",
                    return_value={"average_precision": 0.0, "brier": 0.04},
                ),
            ):
                arguments = (
                    freeze,
                    split_file,
                    processed,
                    root / "training",
                    calibration,
                    m1,
                    diagnostic,
                    root / "output",
                )
                first = audit_m2_calibration_utility(*arguments, mode="gated")
                second = audit_m2_calibration_utility(*arguments, mode="gated")
                self.assertEqual(first, second)
                self.assertEqual(first["seed_count"], 2)
                self.assertEqual(first["later_half_matches"], 3000)
                self.assertIsNone(first["selected_seed"])
                self.assertFalse(first["identifiers_in_summary"])
                self.assertEqual(first["per_target_brier_score"][LABELS[0]]["mean"], 0.04)
                report = calibration / "gated" / "seed-2" / "calibration-report.json"
                tampered = json.loads(report.read_text())
                tampered["scores_sha256"] = "unbound"
                _write_json(report, tampered)
                with self.assertRaisesRegex(ValueError, "completed seeds"):
                    audit_m2_calibration_utility(*arguments, mode="gated")

    def test_rejects_truth_order_change_even_with_valid_probability_shapes(self) -> None:
        scores = np.full((2, 12), 0.3, dtype=np.float32)
        truth = np.zeros((2, 12), dtype=np.int8)
        offsets = np.array([0, 1, 2], dtype=np.int64)
        _validate_scores(scores, truth, offsets, truth, offsets)
        wrong_truth = truth.copy()
        wrong_truth[1, 0] = 1
        with self.assertRaisesRegex(ValueError, "labels or match order"):
            _validate_scores(scores, wrong_truth, offsets, truth, offsets)
        with self.assertRaisesRegex(ValueError, "labels or match order"):
            _validate_scores(scores, truth, offsets[::-1], truth, offsets)

    def test_later_outcomes_cannot_change_earlier_threshold(self) -> None:
        times = [(0,), (0,), (0,), (0,)]
        onsets = {
            event: [(20_000,), (), (20_000,), ()] for event in ("baron", "dragon", "teamfight")
        }
        offsets = np.arange(5, dtype=np.int64)
        scores = np.zeros((4, 12), dtype=np.float32)
        scores[0, [3, 7, 11]] = 0.8
        scores[1, [3, 7, 11]] = 0.1
        scores[2, [3, 7, 11]] = 0.8
        scores[3, [3, 7, 11]] = 0.1
        original = _later_alerts(scores, offsets, times, onsets, [0, 1], [2, 3])
        changed = scores.copy()
        changed[2, [3, 7, 11]] = 0.01
        changed[3, [3, 7, 11]] = 0.9
        revised = _later_alerts(changed, offsets, times, onsets, [0, 1], [2, 3])
        for event in onsets:
            self.assertEqual(
                original[event]["threshold_selected_on_early_half"],
                revised[event]["threshold_selected_on_early_half"],
            )
            self.assertEqual(original[event]["early_metrics"], revised[event]["early_metrics"])
            self.assertNotEqual(original[event]["later_metrics"], revised[event]["later_metrics"])


if __name__ == "__main__":
    unittest.main()
