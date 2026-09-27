from copy import deepcopy

import numpy as np
import pytest

from league_ews.graph import ObjectiveRules
from league_ews.labels import EventIndex, future_event_labels
from league_ews.m1_graph_window import EDGE_TYPES, build_causal_graph_windows
from league_ews.timeline import Position


def _rules():
    return ObjectiveRules(Position(x=5000, y=10000), Position(x=9900, y=4400), 1200, 300)


def _payload():
    times = (0, 60_000, 121_000)
    event_index = EventIndex(baron_ms=(), dragon_ms=(60_000,), teamfight_ms=(121_000,))
    labels = future_event_labels(times, event_index).to_dict(orient="records")
    participants = [
        {
            "participant_id": i,
            "team_id": 100 if i <= 5 else 200,
            "total_gold": 500,
            "xp": 0,
            "level": 1,
            "lane_minions": 0,
            "jungle_minions": 0,
            "position": {"x": 5000 + i, "y": 10000 + i},
        }
        for i in range(1, 11)
    ]
    observations = [
        {"timestamp_ms": t, "participants": deepcopy(participants), "events": []} for t in times
    ]
    observations[1]["events"] = [
        {
            "timestamp_ms": 50_000,
            "event_type": "CHAMPION_KILL",
            "killer_id": 1,
            "assisting_participant_ids": [2],
        }
    ]
    return {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "match_id": "EUW1_1",
            "platform_id": "EUW1",
            "game_version": "16.16.1",
            "game_creation_ms": 1,
            "observations": observations,
        },
        "event_index": {
            "baron_ms": list(event_index.baron_ms),
            "dragon_ms": list(event_index.dragon_ms),
            "teamfight_ms": list(event_index.teamfight_ms),
        },
        "labels": labels,
    }


def test_graph_windows_keep_inputs_causal_and_targets_separate():
    source = _payload()
    result = build_causal_graph_windows(source, "EUW1_1", objective_rules=_rules())
    assert result.nodes.shape == (3, 8, 12, 11)
    assert result.edges.shape == (3, 8, 5, 12, 12)
    assert result.history_mask.sum(axis=1).tolist() == [1, 2, 3]
    assert result.ages_minutes[2, -3:].tolist() == pytest.approx([121 / 60, 61 / 60, 0])
    assert result.targets.shape == (3, 12)
    assert result.hazard_targets.shape == (3, 3, 6)
    assert result.hazard_targets[0, 1, 5] == 1
    assert result.hazard_targets[1, 1].sum() == 0  # Event at t is not future.
    assistance = EDGE_TYPES.index("assistance")
    assert result.edges[1, -1, assistance, 0, 1]
    assert not result.edges[0, -1, assistance].any()

    changed = deepcopy(source)
    changed["timeline"]["observations"][2]["participants"][0]["total_gold"] = 5_000
    later = build_causal_graph_windows(changed, "EUW1_1", objective_rules=_rules())
    np.testing.assert_array_equal(result.nodes[:2], later.nodes[:2])
    np.testing.assert_array_equal(result.edges[:2], later.edges[:2])
    assert not np.array_equal(result.nodes[2], later.nodes[2])


def test_graph_windows_reject_inconsistent_future_labels():
    source = _payload()
    source["labels"][0]["y_dragon_60"] = 0
    with pytest.raises(ValueError, match="strict future"):
        build_causal_graph_windows(source, "EUW1_1", objective_rules=_rules())


def test_graph_windows_reject_future_events_in_snapshot():
    source = _payload()
    source["timeline"]["observations"][1]["events"][0]["timestamp_ms"] = 61_000
    with pytest.raises(ValueError, match="future event"):
        build_causal_graph_windows(source, "EUW1_1", objective_rules=_rules())
