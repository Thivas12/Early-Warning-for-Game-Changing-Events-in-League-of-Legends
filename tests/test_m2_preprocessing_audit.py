"""M2 preprocessing audit counts labels without matching future inputs."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.m2_preprocessing_audit import _accumulator, _add_shard, _summary


class PreprocessingAuditTests(unittest.TestCase):
    def test_position_and_objective_clock_strata_are_counted_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            nodes = np.zeros((2, 8, 12, 11), np.float32)
            edges = np.zeros((2, 8, 5, 12, 12), np.bool_)
            mask = np.zeros((2, 8), np.bool_)
            mask[:, -1] = True
            nodes[0, -1, :10, 10] = 1
            nodes[0, -1, 10, 10] = 1
            labels = np.zeros((2, len(LABELS)), np.int8)
            labels[0, 3] = 1
            hazards = np.zeros((2, 3, 6), np.float32)
            hazards[0, 0, 4] = 1
            path = Path(temp) / "example.npz"
            np.savez_compressed(
                path,
                nodes=nodes,
                edges=edges,
                history_mask=mask,
                ages_minutes=np.zeros((2, 8), np.float32),
                targets=labels,
                hazard_targets=hazards,
                match_offsets=np.array([0, 1, 2], np.int64),
            )
            totals = _accumulator()
            with np.load(path, allow_pickle=False) as shard:
                _add_shard(totals, shard, {"observations": 2, "matches": 2})
            result = _summary(totals)
            self.assertEqual(result["position_count_rows"][0], 1)
            self.assertEqual(result["position_count_rows"][10], 1)
            self.assertEqual(result["position_count_positive_rows"][LABELS[3]][10], 1)
            self.assertEqual(result["objective_spawn"]["baron"]["rows"], [1, 1])
            self.assertEqual(result["target_prevalence"][LABELS[3]], 0.5)

    def test_rejects_unobserved_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "invalid.npz"
            nodes = np.zeros((1, 8, 12, 11), np.float32)
            nodes[0, -1, 0, 8] = 0.1
            mask = np.zeros((1, 8), np.bool_)
            mask[0, -1] = True
            np.savez_compressed(
                path,
                nodes=nodes,
                edges=np.zeros((1, 8, 5, 12, 12), np.bool_),
                history_mask=mask,
                ages_minutes=np.zeros((1, 8), np.float32),
                targets=np.zeros((1, len(LABELS)), np.int8),
                hazard_targets=np.zeros((1, 3, 6), np.float32),
                match_offsets=np.array([0, 1], np.int64),
            )
            with np.load(path, allow_pickle=False) as shard, self.assertRaises(ValueError):
                _add_shard(_accumulator(), shard, {"observations": 1, "matches": 1})
