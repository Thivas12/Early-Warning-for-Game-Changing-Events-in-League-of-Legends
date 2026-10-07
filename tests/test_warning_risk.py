"""Independent replay and statistical contract checks; no empirical League claims."""

import math

import numpy as np
import pytest

from scripts.warning_efficiency import replay_thresholds
from scripts.warning_risk import (
    CAP,
    DELTA,
    REGIONAL_SEQUENCES,
    SEQUENCE_LEVEL,
    kl_pvalue,
    reference_capped,
    replay_capped,
    select_capped,
)


@pytest.mark.parametrize("horizon", [30, 60])
@pytest.mark.parametrize("cap", [1, 4, 100])
def test_capped_replay_matches_independent_scalar_oracle(horizon, cap):
    rng = np.random.default_rng(8017)
    times = [np.cumsum(rng.integers(1, 90_001, size=rng.integers(1, 40))) for _ in range(25)]
    events = [np.unique(rng.integers(0, int(t[-1]) + 70_000, size=20)) for t in times]
    scores = [rng.random(len(t)) for t in times]
    thresholds = (None, 1.0, 0.7, 0.4, 0.1)
    got = replay_capped(times, events, scores, thresholds, horizon, cap, batch_size=7)
    want = np.array(
        [
            [reference_capped(t, e, s, v, horizon, cap) for v in thresholds]
            for t, e, s in zip(times, events, scores, strict=True)
        ]
    )
    np.testing.assert_array_equal(got, want)
    assert np.all(got[:, :, 3] <= cap)
    assert np.all(got[:, :, 3] - got[:, :, 2] <= cap)
    if cap == 100:
        np.testing.assert_array_equal(
            got, replay_thresholds(times, events, scores, thresholds, horizon)
        )


def test_cap_retains_first_warnings_not_future_highest_scores():
    times = [np.arange(6) * 60_000]
    events = [np.array([320_000])]
    scores = [np.array([0.5, 0.5, 0.5, 0.5, 0.9, 1.0])]
    got = replay_capped(times, events, scores, (0.4,))
    np.testing.assert_array_equal(got[0, 0], [1, 0, 0, 4, 4, 1])
    scores[0][-2:] = 0.1
    np.testing.assert_array_equal(got, replay_capped(times, events, scores, (0.4,)))


def test_risk_is_not_monotone_in_threshold():
    counts = replay_capped(
        [np.array([0, 30_000])], [np.array([20_000])], [np.array([0.4, 0.8])], (0.3, 0.7)
    )
    np.testing.assert_array_equal(counts[0, :, 3] - counts[0, :, 2], [0, 1])


def test_horizon_and_cooldown_boundaries_preserve_counts():
    times = [np.array([0, 59_999, 60_000, 120_000, 180_000])]
    events = [np.array([10_000, 90_000, 120_001, 180_000])]
    scores = [np.ones(5)]
    counts = replay_capped(times, events, scores, (None, 1.0))
    np.testing.assert_array_equal(counts[0, 1], [4, 3, 2, 4, 1, 2])
    np.testing.assert_array_equal(counts[0, 0], [4, 0, 0, 0, 0, 2])


@pytest.mark.parametrize(
    "times,events,scores,kwargs",
    [
        ([np.array([0, 0])], [np.array([])], [np.array([0.2, 0.3])], {}),
        ([np.array([0.1])], [np.array([])], [np.array([0.2])], {}),
        ([np.array([0])], [np.array([np.nan])], [np.array([0.2])], {}),
        ([np.array([0])], [np.array([])], [np.array([1.1])], {}),
        ([np.array([0])], [np.array([])], [np.array([0.2])], {"cap": 0}),
        ([np.array([0])], [np.array([])], [np.array([0.2])], {"thresholds": (0.0,)}),
    ],
)
def test_replay_rejects_invalid_inputs(times, events, scores, kwargs):
    with pytest.raises(ValueError):
        replay_capped(times, events, scores, **kwargs)


def test_kl_bound_dominates_exact_bernoulli_lower_tail():
    for n in (3, 7, 12):
        for budget in (0.25, 0.5, 0.75, 1.0):
            probability = budget / CAP
            for successes in range(math.ceil(n * probability)):
                exact = sum(
                    math.comb(n, k) * probability**k * (1 - probability) ** (n - k)
                    for k in range(successes + 1)
                )
                assert exact <= kl_pvalue(CAP * successes, n, budget) + 1e-14


def test_kl_bound_boundaries_and_error_allocation():
    assert kl_pvalue(0, 12, 1) == pytest.approx(0.75**12)
    assert kl_pvalue(12, 12, 1) == 1
    assert kl_pvalue(48, 12, 1) == 1
    assert kl_pvalue(50, 1500, 1) < kl_pvalue(500, 1500, 1)
    assert REGIONAL_SEQUENCES == 720
    assert SEQUENCE_LEVEL * REGIONAL_SEQUENCES == DELTA


@pytest.mark.parametrize("args", [(-1, 10, 1), (41, 10, 1), (0, 0, 1), (0, 10, 0), (0, 10, 4)])
def test_invalid_risk_bound_inputs(args):
    with pytest.raises(ValueError):
        kl_pvalue(*args)


def make_totals(costs, hits, n=1500):
    counts = np.zeros((2, len(costs), 6), dtype=np.int64)
    counts[:, :, 0] = n * 3
    counts[:, :, 5] = n * 3
    counts[:, :, 1] = counts[:, :, 2] = hits
    counts[:, :, 3] = np.array(costs) + hits
    counts[:, :, 4] = costs
    return counts


def test_fixed_sequence_stops_at_first_failure_even_if_later_point_passes():
    totals = make_totals([0, 100, 1600, 200], [0, 100, 110, 200])
    got = select_capped(totals, [1500, 1500], 1, (None, 1.0, 0.8, 0.4))
    assert got["indices"] == {
        "capped_empirical": 3,
        "capped_sequence": 1,
        "capped_kl_sequence": 1,
    }
    assert got["empirical_prefix_length"] == got["kl_prefix_length"] == 2
    assert got["pvalues_by_region"][0][3] < SEQUENCE_LEVEL


def test_uncertainty_allowance_and_worst_region_are_separate_constraints():
    totals = make_totals([0, 100, 1400], [0, 100, 200])
    totals[1, 2, 3] -= 800
    totals[1, 2, 4] -= 800
    got = select_capped(totals, [1500, 1500], 1, (None, 1.0, 0.5))
    assert got["indices"]["capped_empirical"] == 2
    assert got["indices"]["capped_sequence"] == 2
    assert got["indices"]["capped_kl_sequence"] == 1
    assert got["pvalues_by_region"][0][2] > SEQUENCE_LEVEL
    assert got["pvalues_by_region"][1][2] < SEQUENCE_LEVEL


def test_silence_is_structurally_safe_even_when_small_sample_cannot_certify_zero():
    totals = make_totals([0, 0, 0], [0, 0, 1], n=1)
    got = select_capped(totals, [1, 1], 0.25, (None, 1.0, 0.5))
    assert got["indices"]["capped_kl_sequence"] == 0
    assert got["kl_prefix_length"] == 1
    assert got["pvalues_by_region"][0][0] == 0


def test_tie_rule_prefers_lower_cost_then_higher_threshold():
    totals = make_totals([0, 100, 50, 50], [0, 100, 100, 100])
    got = select_capped(totals, [1500, 1500], 1, (None, 1.0, 0.8, 0.4))
    assert all(i == 2 for i in got["indices"].values())


def test_selector_rejects_unbounded_cost_and_reordered_thresholds():
    totals = make_totals([0, 6001], [0, 0])
    with pytest.raises(ValueError, match="Invalid capped"):
        select_capped(totals, [1500, 1500], 1, (None, 0.5))
    totals = make_totals([0, 100, 200], [0, 0, 0])
    with pytest.raises(ValueError, match="Sequence order"):
        select_capped(totals, [1500, 1500], 1, (None, 0.5, 1.0))
