import pandas as pd
import pytest

from league_ews.features import (
    causal_feature_columns,
    history_feature_columns,
    legacy_post_match_feature_columns,
    require_features,
)


def test_known_future_and_broken_fields_are_never_features() -> None:
    frame = pd.DataFrame(
        {
            "match_id": ["m"],
            "t": [10],
            "gold_diff": [1.0],
            "kills_30_t1": [1.0],
            "time_since_last_baron": [50.0],
            "alive_t1": [0.0],
            "kills_blue": [20],
            "y_baron_30": [0],
        }
    )
    causal = causal_feature_columns(frame)
    assert "gold_diff" in causal
    assert "t" in causal
    assert "alive_t1" not in causal
    assert "kills_blue" not in causal
    assert "y_baron_30" not in causal
    history = history_feature_columns(frame)
    assert history == ["t", "kills_30_t1", "time_since_last_baron"]
    assert legacy_post_match_feature_columns(frame) == ["kills_blue"]


def test_required_features_fail_loudly() -> None:
    with pytest.raises(ValueError, match="missing"):
        require_features(pd.DataFrame({"a": [1]}), ["a", "missing"])
