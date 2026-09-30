from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.audit_command_first_contact import first_damage_per_life
from research.command_features import summaries, validate_actions


def orders(ticks, xy, issuers=None):
    return pd.DataFrame(
        {
            "match_id": [123] * len(ticks),
            "tick": ticks,
            "game_time_sec": np.asarray(ticks) / 30,
            "order_type": [1] * len(ticks),
            "issuer_player_id": issuers or [42] * len(ticks),
            "queue": [False] * len(ticks),
            "pos_x": [p[0] for p in xy],
            "pos_y": [p[1] for p in xy],
        }
    )


def test_future_orders_cannot_change_any_feature():
    prefix = orders([100, 150], [(0, 0), (200, 400)])
    extended = pd.concat([prefix, orders([301, 800], [(9000, 9000), (-9000, -9000)])])
    a = summaries(prefix, np.array([300]), np.array([[16384, 16384]]))
    b = summaries(extended, np.array([300]), np.array([[16384, 16384]]))
    for name in a:
        np.testing.assert_equal(a[name], b[name])


def test_left_open_window_and_entity_deduplication():
    a = orders([150, 151, 200, 300], [(0, 0)] * 4, [3, 4, 4, 8])
    result = summaries(a, np.array([300]), np.array([[16384, 16384]]))
    # 150 is outside (150,300]; repeated issuer 4 counts twice as orders, once as issuer.
    np.testing.assert_equal(result["rate"][0, :8], [3, 3, 0, 0, 0, 0, 2, 2])
    np.testing.assert_equal(
        result["destination"][0, :15], [0, 0, 0, 3, 3, 3, 2, 2, 2, 0, 0, 0, 2, 2, 2]
    )


def test_coordinate_conversion_and_rotation_control():
    a = orders([200], [(5000, -5000)])
    result = summaries(a, np.array([300]), np.array([[21384, 11384]]))
    assert result["destination"][0, 0] == 0
    assert result["rotated"][0, 0] > 14000
    assert result["destination"][0, 3] == 1
    assert result["rotated"][0, 3] == 0


def test_stop_hold_category_does_not_count_ability_training():
    a = orders([200, 220, 250], [(0, 0)] * 3)
    a["order_type"] = [10, 11, 21]
    result = summaries(a, np.array([300]), np.array([[16384, 16384]]))
    assert result["rate"][0, 4] == 2


def test_empty_history_does_not_invent_distance():
    a = orders([400], [(0, 0)])
    result = summaries(a, np.array([300]), np.array([[16384, 16384]]))
    assert not result["rate"].any()
    assert np.isnan(result["destination"][0, :3]).all()
    assert not result["destination"][0, 3:9].any()


def test_bad_clocks_and_missing_move_destinations_are_rejected():
    a = orders([300], [(0, 0)])
    validate_actions(a, "123", 0, 600)
    a.loc[0, "game_time_sec"] = 7
    with pytest.raises(ValueError, match="unverified_pause_clock"):
        validate_actions(a, "123", 0, 600)
    a.loc[0, "game_time_sec"] = 10
    a.loc[0, "pos_x"] = float("nan")
    with pytest.raises(ValueError, match="missing_movement_destination"):
        validate_actions(a, "123", 0, 600)


def test_first_damage_per_life_does_not_reset_after_a_quiet_gap():
    combat = pd.DataFrame(
        {
            "target_name": ["npc_dota_roshan"] * 7,
            "tick": [100, 200, 1000, 1500, 2000, 3000, 4000],
            "event_type": ["DOTA_COMBATLOG_DAMAGE"] * 3
            + ["DOTA_COMBATLOG_DEATH"]
            + ["DOTA_COMBATLOG_DAMAGE"] * 3,
            "value": [0, 10, 20, 0, 0, 20, 10],
        }
    )
    assert first_damage_per_life(combat, 0, 5000) == [200, 3000]
