"""Verify the held-out half and score integrity of M2 calibration utility."""

from __future__ import annotations

import unittest

import numpy as np

from league_ews.m2_utility import _later_alerts, _validate_scores


class M2UtilityTests(unittest.TestCase):
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
            event: [(20_000,), (), (20_000,), ()]
            for event in ("baron", "dragon", "teamfight")
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
