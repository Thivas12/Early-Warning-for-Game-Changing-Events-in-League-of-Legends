"""Statistical unit checks; fixtures are not empirical League evidence."""

import numpy as np

from scripts.analyse_neural_screen import metrics, resample_weights, summarise


def test_bootstrap_preserves_route_sizes_and_resamples_whole_matches():
    routes = np.array(["europe"] * 3 + ["americas"] * 2)
    weights = resample_weights(routes, draws=50)
    np.testing.assert_array_equal(weights[:, :3].sum(1), 3)
    np.testing.assert_array_equal(weights[:, 3:].sum(1), 2)
    assert (weights >= 0).all()
    assert (weights == weights.astype(int)).all()
    assert np.any(weights > 1)


def test_recall_uses_event_totals_not_mean_of_match_recalls():
    counts = np.array([[[[1, 1, 1, 2, 1, 1], [9, 3, 2, 5, 2, 3]]]])
    got = metrics(counts, np.ones((1, 2)))[0, 0, 0]
    np.testing.assert_allclose(got, [0.3, 2.0, 1.5, 0.5])


def test_identical_seeds_do_not_narrow_conditional_interval():
    one = np.array([[[[1, 1, 1, 2, 1, 1], [9, 3, 2, 5, 2, 3]]]])
    counts = np.tile(one, (3, 3, 1, 1))
    draws = metrics(counts, resample_weights(np.array(["europe", "europe"]), 100))
    point = metrics(counts, np.ones((1, 2)))[0]
    result = summarise(point, draws)["macro"]
    assert result["mean_over_fixed_seeds"] == result["by_seed"]["20260930"]
    zeros = summarise(point - point, draws - draws)["macro"]
    assert zeros["mean_over_fixed_seeds"]["timely_recall"]["conditional_95_interval"] == [0, 0]
