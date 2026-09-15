"""Framework-independent temporal interaction graph construction."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from league_ews.timeline import Observation, ParticipantState, Position

MAP_SCALE = 15000.0


@dataclass(frozen=True)
class ObjectiveRules:
    """Patch-specific map geometry and spawn rules supplied by the experiment."""

    baron_position: Position
    dragon_position: Position
    baron_spawn_seconds: int
    dragon_spawn_seconds: int

    def __post_init__(self) -> None:
        if self.baron_spawn_seconds <= 0 or self.dragon_spawn_seconds <= 0:
            raise ValueError("Objective spawn times must be positive")


@dataclass(frozen=True)
class GraphSnapshot:
    """A deterministic graph tensor contract independent of model library."""

    node_ids: tuple[str, ...]
    node_features: NDArray[np.float32]
    edge_index: NDArray[np.int64]
    edge_types: tuple[str, ...]
    feature_names: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.node_features.shape[0] != len(self.node_ids):
            raise ValueError("One node-feature row is required per node")
        if self.edge_index.shape != (2, len(self.edge_types)):
            raise ValueError("edge_index must have shape [2, number_of_edges]")


def _distance(left: Position, right: Position) -> float:
    return float(np.hypot(left.x - right.x, left.y - right.y))


def _participant_features(state: ParticipantState) -> list[float]:
    position = state.position
    return [
        1.0,
        0.0,
        -1.0 if state.team_id == 100 else 1.0,
        state.total_gold / 20000.0,
        state.xp / 25000.0,
        state.level / 18.0,
        state.lane_minions / 400.0,
        state.jungle_minions / 300.0,
        position.x / MAP_SCALE if position else 0.0,
        position.y / MAP_SCALE if position else 0.0,
        1.0 if position else 0.0,
    ]


def build_interaction_graph(
    observation: Observation,
    *,
    objective_rules: ObjectiveRules,
    proximity_radius: float = 2500.0,
) -> GraphSnapshot:
    """Create team, proximity and objective-proximity relations."""

    if proximity_radius <= 0:
        raise ValueError("proximity_radius must be positive")
    ordered = sorted(observation.participants, key=lambda participant: participant.participant_id)
    if [participant.participant_id for participant in ordered] != list(range(1, 11)):
        raise ValueError("Graph requires participant IDs 1..10 exactly once")

    node_ids = tuple(
        [f"participant:{participant.participant_id}" for participant in ordered]
        + ["objective:baron", "objective:dragon"]
    )
    node_features = [_participant_features(participant) for participant in ordered]
    timestamp_seconds = observation.timestamp_ms / 1000.0
    node_features.extend(
        [
            [
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                objective_rules.baron_position.x / MAP_SCALE,
                objective_rules.baron_position.y / MAP_SCALE,
                1.0 if timestamp_seconds >= objective_rules.baron_spawn_seconds else 0.0,
            ],
            [
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                objective_rules.dragon_position.x / MAP_SCALE,
                objective_rules.dragon_position.y / MAP_SCALE,
                1.0 if timestamp_seconds >= objective_rules.dragon_spawn_seconds else 0.0,
            ],
        ]
    )

    sources: list[int] = []
    targets: list[int] = []
    edge_types: list[str] = []

    def add_bidirectional(left: int, right: int, relation: str) -> None:
        sources.extend((left, right))
        targets.extend((right, left))
        edge_types.extend((relation, relation))

    for left in range(10):
        for right in range(left + 1, 10):
            left_state = ordered[left]
            right_state = ordered[right]
            if left_state.team_id == right_state.team_id:
                add_bidirectional(left, right, "same-team")
            if (
                left_state.position is not None
                and right_state.position is not None
                and _distance(left_state.position, right_state.position) <= proximity_radius
            ):
                add_bidirectional(left, right, "proximity")

    for participant_index, participant in enumerate(ordered):
        if participant.position is None:
            continue
        for objective_index, objective_position, relation in (
            (10, objective_rules.baron_position, "near-baron"),
            (11, objective_rules.dragon_position, "near-dragon"),
        ):
            if _distance(participant.position, objective_position) <= proximity_radius:
                add_bidirectional(participant_index, objective_index, relation)

    edge_index = np.asarray([sources, targets], dtype=np.int64)
    return GraphSnapshot(
        node_ids=node_ids,
        node_features=np.asarray(node_features, dtype=np.float32),
        edge_index=edge_index,
        edge_types=tuple(edge_types),
        feature_names=(
            "is_participant",
            "is_objective",
            "team_sign",
            "total_gold_scaled",
            "xp_scaled",
            "level_scaled",
            "lane_minions_scaled",
            "jungle_minions_scaled",
            "x_scaled",
            "y_scaled",
            "observed_or_available",
        ),
    )
