"""Scientific invariants: clocks, prefix access, attribution, and alert budgets."""

import numpy as np
import pandas as pd
import pytest

from research.precontact_data import (
    assert_unpaused_clock,
    coordination_features,
    prefix_indices,
    teams_before_horn,
)
from research.run_precontact_invariance import invariant_features
from research.run_precontact_pilot import calibrate, emit_alarms, paired_interval


def test_history_never_rounds_forward_or_wraps_before_start():
    ticks = np.array([100, 130, 160])
    np.testing.assert_array_equal(prefix_indices(ticks, np.array([100, 129, 159])), [0, 0, 1])
    with pytest.raises(ValueError, match="precedes"):
        prefix_indices(ticks, np.array([99]))


def test_pause_and_wrong_clock_offset_fail_closed():
    ticks = np.array([100, 130, 160, 190])
    assert_unpaused_clock(ticks, np.array([0.0, 1.0, 2.0, 3.0]), 100)
    with pytest.raises(ValueError, match="pause_clock"):
        assert_unpaused_clock(ticks, np.array([0.0, 1.0, 2.0, 1.0]), 100)
    with pytest.raises(ValueError, match="pause_clock"):
        assert_unpaused_clock(ticks, np.array([60.0, 61.0, 62.0, 63.0]), 100)


def test_future_team_records_cannot_resolve_missing_pregame_identity():
    rows = [
        {
            "tick": 99,
            "is_target_hero": True,
            "is_target_illusion": False,
            "target_team": 2 if i % 2 == 0 else 3,
            "target_name": f"npc_dota_hero_test{i}",
        }
        for i in range(10)
    ]
    heroes = [f"CDOTA_Unit_Hero_Test{i}" for i in range(10)]
    teams = teams_before_horn(pd.DataFrame(rows), heroes, 100)
    np.testing.assert_array_equal(teams, [2, 3] * 5)
    rows[0]["tick"] = 101
    with pytest.raises(ValueError, match="pregame_team"):
        teams_before_horn(pd.DataFrame(rows), heroes, 100)


def test_geometry_is_invariant_to_within_team_permutation():
    rng = np.random.default_rng(10)
    pos, past = rng.normal(size=(2, 10, 2)), rng.normal(size=(2, 10, 2))
    alive, target = np.ones((2, 10)), np.zeros((2, 2))
    teams = np.array([2] * 5 + [3] * 5)
    order = [4, 2, 0, 1, 3, 9, 8, 6, 5, 7]
    a = coordination_features(pos, past, alive, target, teams)
    b = coordination_features(pos[:, order], past[:, order], alive[:, order], target, teams[order])
    np.testing.assert_allclose(a, b, atol=1e-12)


def test_alert_cooldown_and_calibration_count_late_and_duplicate_alarms():
    ticks = np.array([0, 1799, 1800, 3600])
    assert emit_alarms(ticks, np.ones(4), 0.5) == [0, 1800, 3600]
    data = [{"match_id": "one", "day": 0, "ticks": ticks, "onsets": np.array([600])}]
    # All four above threshold yields two unmatched alarms, so the budget forces silence.
    threshold, metrics = calibrate(data, [np.ones(4)], "onsets")
    assert np.isinf(threshold)
    assert metrics["unmatched_alarms"] == 0


def test_paired_intervals_do_not_treat_seed_repeats_as_matches():
    a = [
        {"match_id": str(i), "day": i // 2, "targets": 2, "hits": 1, "unmatched_alarms": 0}
        for i in range(6)
    ]
    b = [{**row, "hits": 0} for row in a]
    result = paired_interval(a, b, by_day=True)
    assert result["units"] == 3
    assert result["percentile_95"] == [0.5, 0.5]


def test_invariant_ablation_removes_player_team_order_and_map_origin():
    rng = np.random.default_rng(21)
    x = rng.normal(size=(4, 225)).astype(np.float32)
    # Equal target-distance keys exercise the summary-based tie breaker too.
    x[:, 201] = x[:, 215]
    transformed = x.copy()
    players = transformed[:, 5:65].reshape(-1, 10, 6)
    order = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    players[:] = players[:, order].copy()
    players[:, :, :2] += 1000
    geometry = transformed[:, 197:225].reshape(-1, 2, 14)
    geometry[:] = geometry[:, ::-1].copy()
    for motion in (False, True):
        np.testing.assert_allclose(
            invariant_features(x, motion=motion),
            invariant_features(transformed, motion=motion),
            atol=1e-6,
        )
