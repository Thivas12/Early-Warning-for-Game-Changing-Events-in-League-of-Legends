import numpy as np
import pandas as pd
import pytest

from league_ews.events import (
    evaluate_operating_point,
    extract_event_times,
    match_alerts,
    threshold_crossing_alerts,
)


def _match(match_id: str = "m1") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "match_id": [match_id] * 7,
            "t": [0, 10, 20, 30, 40, 50, 60],
            "time_since_last_baron": [9999, 9999, 0, 10, 20, 30, 40],
            "y_baron_10": [0, 1, 0, 0, 0, 0, 0],
        }
    )


def test_event_extraction_uses_observed_timer_reset() -> None:
    assert extract_event_times(_match(), "baron").tolist() == [20]


def test_threshold_crossing_and_cooldown() -> None:
    alerts = threshold_crossing_alerts(
        np.asarray([0, 10, 20, 30, 40, 50, 80]),
        np.asarray([0.1, 0.8, 0.9, 0.1, 0.8, 0.1, 0.9]),
        threshold=0.5,
        cooldown_seconds=60,
    )
    assert alerts.tolist() == [10, 80]


def test_one_event_cannot_satisfy_two_alerts() -> None:
    hits, leads = match_alerts(np.asarray([0, 10]), np.asarray([20]), horizon_seconds=30)
    assert hits == 1
    assert leads == [20]


def test_operational_metrics_count_false_alerts() -> None:
    frame = _match()
    probabilities = np.asarray([0.1, 0.8, 0.1, 0.1, 0.9, 0.1, 0.1])
    metrics = evaluate_operating_point(
        frame,
        probabilities,
        event="baron",
        threshold=0.5,
        horizon_seconds=30,
        cooldown_seconds=0,
    )
    assert metrics.events == 1
    assert metrics.alerts == 2
    assert metrics.hits == 1
    assert metrics.false_alerts == 1
    assert metrics.precision == pytest.approx(0.5)
    assert metrics.recall == pytest.approx(1.0)
    assert metrics.median_lead_seconds == 10


def test_invalid_event_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        extract_event_times(_match(), "nexus")
