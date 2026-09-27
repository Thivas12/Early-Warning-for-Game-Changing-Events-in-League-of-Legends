"""Causal within-match graph windows for the registered M1 experiment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from league_ews.baseline_floor import LABELS
from league_ews.graph import ObjectiveRules, build_interaction_graph
from league_ews.hazards import event_hazard_targets
from league_ews.labels import EventIndex, future_event_labels
from league_ews.timeline import NormalizedTimeline

STEPS = 8
EDGE_TYPES = ("same-team", "proximity", "assistance", "near-baron", "near-dragon")


@dataclass(frozen=True)
class CausalGraphWindows:
    """Inputs and targets kept in distinct arrays, with one row per real frame."""

    nodes: NDArray[np.float32]
    edges: NDArray[np.bool_]
    history_mask: NDArray[np.bool_]
    ages_minutes: NDArray[np.float32]
    targets: NDArray[np.int8]
    hazard_targets: NDArray[np.float32]
    times_ms: NDArray[np.int64]


def build_causal_graph_windows(
    payload: Mapping[str, Any],
    match_id: str,
    *,
    objective_rules: ObjectiveRules,
    proximity_radius: float = 2500.0,
) -> CausalGraphWindows:
    """Right-align the current and seven preceding graph snapshots from one match.

    The full event index is used only to validate stored future labels and
    construct separate targets; it cannot enter a graph input channel.
    """

    if payload.get("schema_version") != "league-ews-processed-match-v1":
        raise ValueError("M1 requires a supported processed match")
    timeline = NormalizedTimeline.model_validate(payload["timeline"])
    if timeline.match_id != match_id or not timeline.observations:
        raise ValueError("M1 timeline identity or observations are invalid")
    event_index = EventIndex(**payload["event_index"])
    times = np.asarray([obs.timestamp_ms for obs in timeline.observations], dtype=np.int64)
    if np.any(np.diff(times) <= 0):
        raise ValueError("M1 observation times must strictly increase")
    expected = future_event_labels(tuple(int(t) for t in times), event_index)
    rows = payload["labels"]
    if not isinstance(rows, list) or len(rows) != len(times):
        raise ValueError("M1 label inventory differs from observations")
    targets = np.empty((len(times), len(LABELS)), dtype=np.int8)
    hazards = np.empty((len(times), 3, 6), dtype=np.float32)
    for index, (observation, row) in enumerate(zip(timeline.observations, rows, strict=True)):
        timestamp = observation.timestamp_ms
        if not isinstance(row, dict) or row.get("timestamp_ms") != timestamp:
            raise ValueError("M1 label time differs from the prediction time")
        for column, label in enumerate(LABELS):
            value = row.get(label)
            if type(value) is not int or value != cast(int, expected.loc[index, label]):
                raise ValueError("M1 label differs from the strict future event index")
            targets[index, column] = value
        hazards[index] = event_hazard_targets(timestamp, event_index).astype(np.float32)

    graph_nodes = np.empty((len(times), 12, 11), dtype=np.float32)
    graph_edges = np.zeros((len(times), len(EDGE_TYPES), 12, 12), dtype=np.bool_)
    edge_channel = {name: index for index, name in enumerate(EDGE_TYPES)}
    for index, observation in enumerate(timeline.observations):
        graph = build_interaction_graph(
            observation, objective_rules=objective_rules, proximity_radius=proximity_radius
        )
        graph_nodes[index] = graph.node_features
        for (source, target), relation in zip(graph.edge_index.T, graph.edge_types, strict=True):
            graph_edges[index, edge_channel[relation], source, target] = True

    nodes = np.zeros((len(times), STEPS, 12, 11), dtype=np.float32)
    edges = np.zeros((len(times), STEPS, len(EDGE_TYPES), 12, 12), dtype=np.bool_)
    mask = np.zeros((len(times), STEPS), dtype=np.bool_)
    ages = np.zeros((len(times), STEPS), dtype=np.float32)
    for index, current in enumerate(times):
        start = max(0, index - STEPS + 1)
        count = index - start + 1
        nodes[index, -count:] = graph_nodes[start : index + 1]
        edges[index, -count:] = graph_edges[start : index + 1]
        mask[index, -count:] = True
        ages[index, -count:] = (current - times[start : index + 1]) / 60_000
    return CausalGraphWindows(nodes, edges, mask, ages, targets, hazards, times)
