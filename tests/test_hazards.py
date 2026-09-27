import numpy as np
import pytest

from league_ews.hazards import (
    cumulative_risk,
    discrete_hazard_target,
    event_hazard_targets,
    risk_at_horizons,
)
from league_ews.labels import EventIndex, future_event_labels


def test_cumulative_risk_is_monotonic() -> None:
    hazards = np.asarray([[0.1, 0.2, 0.5]], dtype=np.float64)
    risk = cumulative_risk(hazards)
    np.testing.assert_allclose(risk, [[0.1, 0.28, 0.64]])
    assert np.all(np.diff(risk, axis=-1) >= 0)


def test_risk_at_horizons_uses_aligned_bins() -> None:
    hazards = np.full((2, 3), 0.1)
    selected = risk_at_horizons(hazards, bin_seconds=10, horizons_seconds=(10, 30))
    assert selected.shape == (2, 2)
    assert selected[0].tolist() == pytest.approx([0.1, 0.271])


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (None, [0, 0, 0]),
        (-1, [0, 0, 0]),
        (1, [1, 0, 0]),
        (10, [1, 0, 0]),
        (11, [0, 1, 0]),
        (31, [0, 0, 0]),
    ],
)
def test_discrete_hazard_target(seconds: float | None, expected: list[int]) -> None:
    assert discrete_hazard_target(seconds, bin_seconds=10, bins=3).tolist() == expected


@pytest.mark.parametrize(
    "hazards",
    [np.asarray([-0.1]), np.asarray([1.1]), np.asarray([np.nan])],
)
def test_invalid_hazards_are_rejected(hazards: np.ndarray) -> None:
    with pytest.raises(ValueError, match="finite probabilities"):
        cumulative_risk(hazards)


def test_invalid_horizon_alignment_is_rejected() -> None:
    with pytest.raises(ValueError, match="multiples"):
        risk_at_horizons(np.ones(3) * 0.1, bin_seconds=10, horizons_seconds=(15,))


def test_event_hazards_preserve_overlapping_events_and_exact_future_labels() -> None:
    events = EventIndex(
        baron_ms=(20_000, 40_000),
        dragon_ms=(10_000, 20_000),
        teamfight_ms=(20_000, 60_000),
    )
    for observation_time in (0, 10_000, 20_000, 60_000):
        targets = event_hazard_targets(observation_time, events)
        assert targets.shape == (3, 6)
        assert (targets.sum(axis=1) <= 1).all()
        expected = future_event_labels((observation_time,), events)
        for row, event in enumerate(("baron", "dragon", "teamfight")):
            for horizon in (10, 20, 30, 60):
                assert int(targets[row, : horizon // 10].sum()) == int(
                    expected.loc[0, f"y_{event}_{horizon}"]
                )
    overlapping = event_hazard_targets(10_000, events)
    assert overlapping[:, 0].tolist() == [1, 1, 1]


def test_event_hazards_reject_bad_inputs() -> None:
    events = EventIndex(baron_ms=(20_000, 10_000), dragon_ms=(), teamfight_ms=())
    with pytest.raises(ValueError, match="strictly increasing"):
        event_hazard_targets(0, events)
    with pytest.raises(ValueError, match="non-negative"):
        event_hazard_targets(-1, EventIndex((), (), ()))
    with pytest.raises(ValueError, match="positive"):
        event_hazard_targets(0, EventIndex((), (), ()), bins=0)
