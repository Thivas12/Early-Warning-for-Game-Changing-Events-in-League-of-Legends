"""Graph removals preserve only their registered information channels."""

import numpy as np
import pytest

from league_ews.m1_ablation_inputs import GRAPH_ABLATIONS, ablate_graph_inputs


@pytest.fixture
def graphs():
    nodes = np.zeros((2, 8, 12, 11), dtype=np.float32)
    edges = np.zeros((2, 8, 5, 12, 12), dtype=np.bool_)
    mask = np.zeros((2, 8), dtype=np.bool_)
    ages = np.zeros((2, 8), dtype=np.float32)
    mask[:, -2:] = True
    ages[:, -2] = 1
    nodes[:, -2:, :10, 0] = 1
    nodes[:, -2:, :10, 8:11] = (0.4, 0.5, 1)
    nodes[:, -2:, 10:, 1] = 1
    nodes[:, -2:, 10:, 8:11] = (0.6, 0.7, 1)
    edges[:, -2:, :, 0, 1] = True
    edges[:, -2:, :, 1, 10] = True
    return nodes, edges, mask, ages


def test_position_ablation_erases_only_spatial_signals(graphs):
    nodes, edges, mask, ages = graphs
    changed, relations = ablate_graph_inputs(nodes, edges, mask, ages, variant=GRAPH_ABLATIONS[0])
    assert np.all(changed[:, -2:, :10, 8:11] == 0)
    assert np.all(changed[:, -2:, 10:, 8:10] == 0)
    assert np.all(changed[:, -2:, 10:, 10] == 1)  # retain objective spawn clock
    assert np.array_equal(changed[:, :, :, :8], nodes[:, :, :, :8])
    assert np.array_equal(relations[:, :, 0], edges[:, :, 0])
    assert np.array_equal(relations[:, :, 2], edges[:, :, 2])
    assert not relations[:, :, [1, 3, 4]].any()
    np.testing.assert_allclose(nodes[:, -2:, :10, 8], 0.4)  # source is unchanged


def test_edge_removal_retains_node_features(graphs):
    nodes, edges, mask, ages = graphs
    changed, relations = ablate_graph_inputs(nodes, edges, mask, ages, variant=GRAPH_ABLATIONS[1])
    assert np.array_equal(changed, nodes)
    assert not relations.any()
    assert edges.any()


def test_objective_removal_keeps_participant_only_graph(graphs):
    nodes, edges, mask, ages = graphs
    changed, relations = ablate_graph_inputs(nodes, edges, mask, ages, variant=GRAPH_ABLATIONS[2])
    assert changed.shape == (2, 8, 10, 11)
    assert relations.shape == (2, 8, 3, 10, 10)
    assert np.array_equal(changed, nodes[:, :, :10])
    assert np.array_equal(relations, edges[:, :, :3, :10, :10])
    assert np.all(nodes[:, -2:, 10:, 1] == 1)


def test_assistance_removal_keeps_other_edges(graphs):
    nodes, edges, mask, ages = graphs
    changed, relations = ablate_graph_inputs(nodes, edges, mask, ages, variant=GRAPH_ABLATIONS[3])
    assert np.array_equal(changed, nodes)
    assert not relations[:, :, 2].any()
    assert np.array_equal(relations[:, :, [0, 1, 3, 4]], edges[:, :, [0, 1, 3, 4]])


def test_bad_input_or_unregistered_variant_fails_closed(graphs):
    nodes, edges, mask, ages = graphs
    with pytest.raises(ValueError, match="Unknown"):
        ablate_graph_inputs(nodes, edges, mask, ages, variant="calibration-best-seed")
    ages[:, -2] = -1
    with pytest.raises(ValueError, match="frozen causal"):
        ablate_graph_inputs(nodes, edges, mask, ages, variant=GRAPH_ABLATIONS[0])
