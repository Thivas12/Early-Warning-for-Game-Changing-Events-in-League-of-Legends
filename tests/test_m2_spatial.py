"""Causal feature construction and one-factor spatial controls."""

from __future__ import annotations

import unittest

import numpy as np

from league_ews.m2_spatial import SPATIAL_CONTROLS, spatial_control, spatial_summary


def _example() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    nodes = np.zeros((2, 8, 12, 11), dtype=np.float32)
    edges = np.zeros((2, 8, 5, 12, 12), dtype=np.bool_)
    mask = np.zeros((2, 8), dtype=np.bool_)
    ages = np.zeros((2, 8), dtype=np.float32)
    mask[:, -1] = True
    nodes[:, -1, :10, 0] = 1
    nodes[:, -1, 10, 8:11] = (0.2, 0.4, 1)
    nodes[:, -1, 11, 8:11] = (0.6, 0.4, 1)
    nodes[0, -1, 0, 8:11] = (0.2, 0.3, 1)
    nodes[0, -1, 5, 8:11] = (0.5, 0.7, 1)
    edges[0, -1, 1, 0, 5] = edges[0, -1, 1, 5, 0] = True
    edges[0, -1, 3, 0, 10] = edges[0, -1, 3, 10, 0] = True
    return nodes, edges, mask, ages


class SpatialTests(unittest.TestCase):
    def test_summary_uses_observed_current_frame_and_explicit_absence(self) -> None:
        nodes, edges, mask, ages = _example()
        features = spatial_summary(nodes, edges, mask, ages)
        self.assertEqual(features.shape, (2, 24))
        self.assertEqual(features[0, 0:2].tolist(), [1, 1])
        self.assertAlmostEqual(float(features[0, 8]), 0.5, places=5)
        self.assertAlmostEqual(float(features[0, 10]), 0.1, places=5)
        self.assertEqual(features[0, 20], 1)
        self.assertEqual(features[1, 0:18].tolist(), [0] * 18)
        self.assertEqual(features[1, 18:20].tolist(), [1, 1])
        nodes[0, -2, 0, 8:11] = (0.9, 0.9, 1)
        with self.assertRaises(ValueError):
            spatial_summary(nodes, edges, mask, ages)

    def test_controls_change_only_named_channels_and_leave_input_untouched(self) -> None:
        nodes, edges, mask, ages = _example()
        original_nodes, original_edges = nodes.copy(), edges.copy()
        for variant in SPATIAL_CONTROLS:
            changed_nodes, changed_edges = spatial_control(
                nodes, edges, mask, ages, variant=variant
            )
            self.assertEqual(changed_nodes.shape, nodes.shape)
            self.assertEqual(changed_edges.shape, edges.shape)
            if variant == "coordinates-only-masked":
                self.assertEqual(changed_nodes[0, -1, 0, 10], 1)
                self.assertEqual(changed_nodes[0, -1, 0, 8:10].tolist(), [0, 0])
                np.testing.assert_array_equal(changed_edges, edges)
            elif variant == "proximity-only-masked":
                np.testing.assert_array_equal(changed_nodes, nodes)
                self.assertFalse(changed_edges[0, -1, 1, 0, 5])
                self.assertFalse(changed_edges[0, -1, 3, 0, 10])
            elif variant == "position-observed-only-masked":
                self.assertEqual(changed_nodes[0, -1, 0, 10], 0)
                np.testing.assert_allclose(changed_nodes[0, -1, 0, 8:10], [0.2, 0.3])
                np.testing.assert_array_equal(changed_edges, edges)
            else:
                self.assertEqual(changed_nodes[0, -1, 10:].tolist(), [[0] * 11] * 2)
                self.assertFalse(changed_edges[0, -1, 3, 0, 10])
                self.assertTrue(changed_edges[0, -1, 1, 0, 5])
        np.testing.assert_array_equal(nodes, original_nodes)
        np.testing.assert_array_equal(edges, original_edges)

    def test_reject_unknown_variant_and_invalid_missing_coordinate(self) -> None:
        nodes, edges, mask, ages = _example()
        with self.assertRaises(ValueError):
            spatial_control(nodes, edges, mask, ages, variant="registered-m1")
        nodes[1, -1, 0, 8] = 0.4
        with self.assertRaises(ValueError):
            spatial_summary(nodes, edges, mask, ages)
