import numpy as np
import pytest

from league_ews.graph import ObjectiveRules, build_interaction_graph
from league_ews.timeline import Observation, ParticipantState, Position


def _observation() -> Observation:
    participants = tuple(
        ParticipantState(
            participant_id=participant_id,
            team_id=100 if participant_id <= 5 else 200,
            total_gold=1000,
            xp=500,
            level=2,
            lane_minions=10,
            jungle_minions=0,
            position=Position(x=5000 + participant_id * 10, y=10470 + participant_id * 10),
        )
        for participant_id in range(1, 11)
    )
    return Observation(timestamp_ms=1_200_000, participants=participants, events=())


def _rules() -> ObjectiveRules:
    return ObjectiveRules(
        baron_position=Position(x=5007.0, y=10471.0),
        dragon_position=Position(x=9866.0, y=4414.0),
        baron_spawn_seconds=1200,
        dragon_spawn_seconds=300,
    )


def test_interaction_graph_has_stable_nodes_features_and_edges() -> None:
    graph = build_interaction_graph(_observation(), objective_rules=_rules())
    assert graph.node_ids[:2] == ("participant:1", "participant:2")
    assert graph.node_ids[-2:] == ("objective:baron", "objective:dragon")
    assert graph.node_features.shape == (12, 11)
    assert graph.edge_index.shape[0] == 2
    assert len(graph.edge_types) == graph.edge_index.shape[1]
    assert "same-team" in graph.edge_types
    assert "near-baron" in graph.edge_types
    assert graph.node_features[10, -1] == pytest.approx(1.0)
    assert np.isfinite(graph.node_features).all()


def test_invalid_proximity_radius_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        build_interaction_graph(_observation(), objective_rules=_rules(), proximity_radius=0)


def test_invalid_objective_rules_are_rejected() -> None:
    with pytest.raises(ValueError, match="spawn times"):
        ObjectiveRules(
            baron_position=Position(x=1, y=1),
            dragon_position=Position(x=2, y=2),
            baron_spawn_seconds=0,
            dragon_spawn_seconds=300,
        )
