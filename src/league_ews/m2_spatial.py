"""Exploratory, causal spatial channels from genuine M1 observation frames.

These controls are separate from the six frozen M1 ablations. They do not
change the original model or its registered test claim.
"""

from __future__ import annotations

import numpy as np

from league_ews.graph import FEATURE_NAMES
from league_ews.m1_graph_window import EDGE_TYPES, STEPS

SPATIAL_CONTROLS = (
    "coordinates-only-masked",
    "proximity-only-masked",
    "position-observed-only-masked",
    "objective-anchors-masked-fixed-nodes",
)

SPATIAL_FEATURES = (
    "blue_position_count",
    "red_position_count",
    "blue_mean_x",
    "blue_mean_y",
    "red_mean_x",
    "red_mean_y",
    "centroid_distance",
    "centroids_observed",
    "nearest_enemy_distance",
    "enemy_pair_observed",
    "blue_nearest_baron",
    "red_nearest_baron",
    "blue_nearest_dragon",
    "red_nearest_dragon",
    "blue_baron_observed",
    "red_baron_observed",
    "blue_dragon_observed",
    "red_dragon_observed",
    "baron_spawn_elapsed",
    "dragon_spawn_elapsed",
    "proximity_edge_count",
    "assistance_edge_count",
    "history_length",
    "previous_frame_age_minutes",
)


def _validate(
    nodes: np.ndarray, edges: np.ndarray, mask: np.ndarray, ages: np.ndarray
) -> None:
    rows = len(nodes)
    if (
        rows == 0
        or nodes.shape != (rows, STEPS, 12, len(FEATURE_NAMES))
        or edges.shape != (rows, STEPS, len(EDGE_TYPES), 12, 12)
        or mask.shape != (rows, STEPS)
        or ages.shape != (rows, STEPS)
        or nodes.dtype != np.float32
        or edges.dtype != np.bool_
        or mask.dtype != np.bool_
        or ages.dtype != np.float32
        or not np.isfinite(nodes).all()
        or not np.isfinite(ages).all()
        or not np.all(mask[:, -1])
        or np.any(nodes[~mask] != 0)
        or np.any(edges[~mask])
        or np.any(ages[~mask] != 0)
        or not np.isin(nodes[:, -1, :10, 10], (0, 1)).all()
        or np.any(nodes[:, -1, :10, 8:10][nodes[:, -1, :10, 10] == 0] != 0)
    ):
        raise ValueError("Spatial inputs differ from genuine staged M1 frames")
    lengths = mask.sum(axis=1)
    if any(
        not np.array_equal(row, np.arange(STEPS) >= STEPS - length)
        for row, length in zip(mask, lengths, strict=True)
    ) or any(
        np.any(np.diff(row[-length:]) > 0)
        for row, length in zip(ages, lengths, strict=True)
    ):
        raise ValueError("Spatial history must contain only prior, ordered observations")


def spatial_control(
    nodes: np.ndarray,
    edges: np.ndarray,
    mask: np.ndarray,
    ages: np.ndarray,
    *,
    variant: str,
) -> tuple[np.ndarray, np.ndarray]:
    """One-factor input removal; keep 12 nodes and all unmentioned channels."""

    if variant not in SPATIAL_CONTROLS:
        raise ValueError("Unknown exploratory spatial control")
    _validate(nodes, edges, mask, ages)
    changed_nodes, changed_edges = nodes.copy(), edges.copy()
    if variant == "coordinates-only-masked":
        changed_nodes[:, :, :10, 8:10] = 0
    elif variant == "proximity-only-masked":
        for relation in ("proximity", "near-baron", "near-dragon"):
            changed_edges[:, :, EDGE_TYPES.index(relation)] = False
    elif variant == "position-observed-only-masked":
        changed_nodes[:, :, :10, 10] = 0
    else:
        changed_nodes[:, :, 10:] = 0
        changed_edges[:, :, :, 10:, :] = False
        changed_edges[:, :, :, :, 10:] = False
    return changed_nodes, changed_edges


def spatial_summary(
    nodes: np.ndarray, edges: np.ndarray, mask: np.ndarray, ages: np.ndarray
) -> np.ndarray:
    """Twenty-four current/past-only values for a transparent hybrid branch.

    Distances are in normalized map coordinates. If an endpoint is absent, its
    distance is zero and a separate observed bit is zero. No label, future
    event index or interpolated frame enters these features.
    """

    _validate(nodes, edges, mask, ages)
    current = nodes[:, -1]
    rows = len(nodes)
    result = np.zeros((rows, len(SPATIAL_FEATURES)), dtype=np.float32)
    observed = current[:, :10, 10] == 1
    coords = current[:, :10, 8:10]
    for team, base in ((slice(0, 5), 0), (slice(5, 10), 1)):
        count = observed[:, team].sum(axis=1)
        result[:, base] = count
        result[:, 2 + 2 * base : 4 + 2 * base] = (
            np.sum(coords[:, team] * observed[:, team, None], axis=1)
            / np.maximum(count[:, None], 1)
        )
    both = (result[:, 0] > 0) & (result[:, 1] > 0)
    result[both, 6] = np.linalg.norm(result[both, 2:4] - result[both, 4:6], axis=1)
    result[:, 7] = both
    enemy_distance = np.linalg.norm(coords[:, :5, None] - coords[:, None, 5:10], axis=-1)
    enemy_distance = np.where(
        observed[:, :5, None] & observed[:, None, 5:10], enemy_distance, np.inf
    ).min(axis=(1, 2))
    result[both, 8] = enemy_distance[both]
    result[:, 9] = both
    for index, team in enumerate((slice(0, 5), slice(5, 10))):
        for objective_index, output_index in ((10, 10), (11, 12)):
            distances = np.linalg.norm(
                coords[:, team] - current[:, None, objective_index, 8:10], axis=-1
            )
            minimum = np.where(observed[:, team], distances, np.inf).min(axis=1)
            present = result[:, index] > 0
            result[present, output_index + index] = minimum[present]
            result[:, output_index + index + 4] = present
    result[:, 18:20] = current[:, 10:12, 10]
    # Bidirectional relations are counted once for each undirected pair.
    result[:, 20] = edges[:, -1, EDGE_TYPES.index("proximity")].sum(axis=(1, 2)) / 2
    result[:, 21] = edges[:, -1, EDGE_TYPES.index("assistance")].sum(axis=(1, 2)) / 2
    result[:, 22] = mask.sum(axis=1)
    result[:, 23] = np.where(mask[:, -2], ages[:, -2], 0)
    if not np.isfinite(result).all():
        raise ValueError("Spatial summary contains a nonfinite channel")
    return result
