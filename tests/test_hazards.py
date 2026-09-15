import numpy as np
import pytest

from league_ews.hazards import cumulative_risk, discrete_hazard_target, risk_at_horizons


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
