"""Exact graph inputs for four registered M1 removal ablations."""

from __future__ import annotations

import numpy as np

from league_ews.graph import FEATURE_NAMES
from league_ews.m1_backend import right_pad_graphs
from league_ews.m1_graph_window import EDGE_TYPES, STEPS

GRAPH_ABLATIONS = (
    "no-positions-or-proximity",
    "no-interaction-edges",
    "no-objective-nodes",
    "no-assistance-history",
)


def ablate_graph_inputs(
    nodes: np.ndarray,
    edges: np.ndarray,
    history_mask: np.ndarray,
    ages: np.ndarray,
    *,
    variant: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Transform normalized graphs without modifying frozen shard arrays.

    The objective-free return uses ten nodes and three participant relation
    channels; its training backend must pool over ten rather than twelve.
    """

    if variant not in GRAPH_ABLATIONS:
        raise ValueError("Unknown registered M1 graph ablation")
    if (
        nodes.ndim != 4
        or nodes.shape[1:] != (STEPS, 12, len(FEATURE_NAMES))
        or edges.shape != (len(nodes), STEPS, len(EDGE_TYPES), 12, 12)
        or history_mask.shape != (len(nodes), STEPS)
        or ages.shape != (len(nodes), STEPS)
        or not len(nodes)
    ):
        raise ValueError("M1 ablation input dimensions differ from frozen graphs")
    # Also checks dtypes, finite channels, masks, age order and zero padding.
    right_pad_graphs(nodes, edges, history_mask, ages)
    result_nodes = nodes.copy()
    result_edges = edges.copy()
    if variant == "no-positions-or-proximity":
        result_nodes[:, :, :10, 8:11] = 0
        result_nodes[:, :, 10:, 8:10] = 0
        for relation in ("proximity", "near-baron", "near-dragon"):
            result_edges[:, :, EDGE_TYPES.index(relation)] = False
    elif variant == "no-interaction-edges":
        result_edges[:] = False
    elif variant == "no-objective-nodes":
        result_nodes = result_nodes[:, :, :10].copy()
        result_edges = result_edges[:, :, :3, :10, :10].copy()
    elif variant == "no-assistance-history":
        result_edges[:, :, EDGE_TYPES.index("assistance")] = False
    return result_nodes, result_edges
