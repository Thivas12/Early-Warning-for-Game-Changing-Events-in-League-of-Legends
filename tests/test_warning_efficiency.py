"""Implementation fixtures, never empirical League findings."""

import numpy as np
import pytest

from scripts.audit_neural_results import reference_counts
from scripts.warning_efficiency import (
    THRESHOLD_VALUES,
    expected_counts,
    replay_thresholds,
    select_deterministic,
    select_mixture,
)


@pytest.mark.parametrize("horizon", [30, 60])
@pytest.mark.parametrize("batch_size", [1, 7, 128])
def test_vectorized_replay_matches_independent_reference(horizon, batch_size):
    rng = np.random.default_rng(31)
    times = [np.cumsum(rng.integers(1, 80001, size=n)) for n in range(1, 22)]
    events = [np.unique(rng.integers(0, t[-1] + 60001, size=n % 9)) for n, t in enumerate(times)]
    scores = [rng.random(len(t)).astype(np.float32) for t in times]
    thresholds = (None, 1.0, 0.7, 0.5, 0.3, 1e-5)
    actual = replay_thresholds(times, events, scores, thresholds, horizon, batch_size)
    expected = [
        [reference_counts(t, e, s, q, horizon) for q in thresholds]
        for t, e, s in zip(times, events, scores, strict=True)
    ]
    np.testing.assert_array_equal(actual, expected)


def test_boundaries_cooldown_credit_and_future_score_isolation():
    times = [np.array([0, 10000, 30000, 59000, 60000, 61000, 120000])]
    events = [np.array([0, 10000, 30000, 60000, 80000, 90000, 150000])]
    scores = [np.array([0.5, 0.1, 0.9, 1, 0.5, 1, 0.5], dtype=np.float32)]
    thresholds = (None, 0.5, 1.0)
    actual = replay_thresholds(times, events, scores, thresholds, 30)
    np.testing.assert_array_equal(
        actual[0], [reference_counts(times[0], events[0], scores[0], q, 30) for q in thresholds]
    )
    # Decisions in the prefix cannot change when later scores change.
    prefix = replay_thresholds([times[0][:4]], events, [scores[0][:4]], thresholds, 30)
    scores[0][4:] = 0
    np.testing.assert_array_equal(
        prefix, replay_thresholds([times[0][:4]], events, [scores[0][:4]], thresholds, 30)
    )


def test_exact_float32_threshold_boundary_and_no_events():
    value = np.float32(0.1)
    thresholds = (float(value), np.nextafter(float(value), 1.0), None)
    c = replay_thresholds(
        [np.array([0])], [np.array([], dtype=int)], [np.array([value])], thresholds
    )
    np.testing.assert_array_equal(c[0, :, 3], [1, 0, 0])


def totals(cost, timely):
    a = np.zeros((len(cost), 6), dtype=np.int64)
    a[:, 0] = 100
    a[:, 1] = a[:, 2] = timely
    a[:, 3] = np.array(cost) + np.array(timely)
    a[:, 4] = cost
    return a


def test_mixture_solves_linear_program_and_matches_expected_counts():
    from scipy.optimize import linprog

    rng = np.random.default_rng(9)
    for _ in range(20):
        counts = totals(np.r_[0, rng.integers(1, 401, 8)], rng.integers(0, 50, 9))
        for budget in (0.25, 0.5, 0.75, 1):
            policy = select_mixture(counts, 100, budget)
            costs = (counts[:, 3] - counts[:, 2]) / 100
            opt = linprog(
                -counts[:, 2].astype(float),
                A_eq=[np.ones(9), costs],
                b_eq=[1, budget],
                bounds=(0, None),
                method="highs",
            )
            assert opt.success
            assert policy["early_timely"] == pytest.approx(-opt.fun, abs=1e-10)
            expected = expected_counts(counts[None], policy)[0]
            assert (expected[3] - expected[2]) / 100 == pytest.approx(budget, abs=1e-12)
            assert expected[3] == pytest.approx(expected[1] + expected[4])


def test_original_selector_ties_and_each_region_budget():
    count = np.zeros((2, len(THRESHOLD_VALUES), 6), dtype=np.int64)
    count[:, :, 0] = 20
    count[:, 1:4, 1:3] = 4
    count[:, 1:4, 3] = 5
    assert select_deterministic(count, [2, 2], 1) == 1  # Highest tied threshold.
    count[0, 1, 3] = 7  # Pooled burden would pass, one region fails.
    assert select_deterministic(count, [2, 2], 1) == 2
    count[:, :, 1:4] = 0
    assert select_deterministic(count, [2, 2], 1) == 0  # Silence wins a zero-utility tie.


def test_mixture_ignores_cost_order_and_rejects_infeasibility():
    a = totals([0, 100, 50], [0, 4, 9])
    policy = select_mixture(a, 100, 0.75)
    assert policy["early_timely"] == 6.5
    assert policy["early_burden"] == 0.75
    with pytest.raises(ValueError, match="infeasible"):
        select_mixture(a, 100, 2)


@pytest.mark.parametrize("risk", [np.nan, 1.1, -0.1])
def test_invalid_scores_rejected(risk):
    with pytest.raises(ValueError, match="chronology or scores"):
        replay_thresholds([np.array([0])], [np.array([30000])], [np.array([risk])])
