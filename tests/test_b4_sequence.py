from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest

from league_ews.b4_sequence import SEQUENCE_FEATURES, STEPS, build_causal_sequences
from league_ews.baseline_floor import LABELS
from league_ews.tabular_baseline import FEATURES


def _payload():
    participants = [
        {
            "participant_id": i,
            "team_id": 100 if i <= 5 else 200,
            "total_gold": 500,
            "xp": 0,
            "level": 1,
            "lane_minions": 0,
            "jungle_minions": 0,
            "position": None,
        }
        for i in range(1, 11)
    ]
    times = (0, 60_000, 121_000)
    return {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "match_id": "EUW1_1",
            "platform_id": "EUW1",
            "game_version": "16.16.1",
            "game_creation_ms": 1,
            "observations": [
                {"timestamp_ms": t, "participants": deepcopy(participants), "events": []}
                for t in times
            ],
        },
        "event_index": {"baron_ms": [], "dragon_ms": [], "teamfight_ms": []},
        "labels": [
            {"timestamp_ms": t, **{label: int(t == 60_000) for label in LABELS}} for t in times
        ],
    }


def test_right_aligned_real_snapshots_and_missingness():
    result = build_causal_sequences(_payload(), "EUW1_1")
    assert result.inputs.shape == (3, STEPS, len(SEQUENCE_FEATURES))
    assert result.targets.shape == (3, len(LABELS))
    assert result.targets[:, 0].tolist() == [0, 1, 0]
    assert result.history_mask.sum(axis=1).tolist() == [1, 2, 3]
    assert np.all(result.inputs[0, :-1] == 0)
    assert result.inputs[2, -3:, -1].tolist() == pytest.approx([121 / 60, 61 / 60, 0])
    # Unknown player positions are represented as value zero plus a missing bit.
    position_column = FEATURES.index("blue_spread")
    assert result.inputs[2, -1, position_column] == 0
    assert result.inputs[2, -1, len(FEATURES) + position_column] == 1
    assert result.inputs[2, 0, len(FEATURES) + position_column] == 0


def test_future_observation_cannot_change_past_windows():
    source = _payload()
    first = build_causal_sequences(source, "EUW1_1")
    changed = deepcopy(source)
    changed["timeline"]["observations"][2]["participants"][0]["total_gold"] = 50_000
    changed["timeline"]["observations"][2]["events"].append(
        {"timestamp_ms": 120_000, "event_type": "CHAMPION_KILL", "killer_team_id": 100}
    )
    second = build_causal_sequences(changed, "EUW1_1")
    np.testing.assert_array_equal(first.inputs[:2], second.inputs[:2])
    assert not np.array_equal(first.inputs[2], second.inputs[2])


def test_labels_and_ordering_are_validated():
    source = _payload()
    source["labels"][1]["y_dragon_30"] = 2
    with pytest.raises(ValueError, match="binary"):
        build_causal_sequences(source, "EUW1_1")
    source = _payload()
    source["timeline"]["observations"][1]["timestamp_ms"] = 0
    source["labels"][1]["timestamp_ms"] = 0
    with pytest.raises(ValueError, match="strictly increase"):
        build_causal_sequences(source, "EUW1_1")
