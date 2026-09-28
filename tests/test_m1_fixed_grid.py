"""The minute control selects real frames at fixed anchors inside each match."""

import numpy as np
import pytest

from league_ews.m1_fixed_grid import fixed_minute_grid


def _source():
    times = np.array([0, 28_000, 62_000, 124_000], dtype=np.int64)
    offsets = np.arange(0, 401, 4, dtype=np.int64)
    nodes = np.zeros((400, 8, 12, 11), dtype=np.float32)
    edges = np.zeros((400, 8, 5, 12, 12), dtype=np.bool_)
    mask = np.zeros((400, 8), dtype=np.bool_)
    ages = np.zeros((400, 8), dtype=np.float32)
    for match in range(100):
        for index, current in enumerate(times):
            row = match * 4 + index
            history = np.arange(index + 1)
            nodes[row, -(index + 1) :, 0, 0] = match * 10 + history + 1
            edges[row, -(index + 1) :, 0, 0, 1] = True
            mask[row, -(index + 1) :] = True
            ages[row, -(index + 1) :] = (current - times[history]) / 60_000
    return nodes, edges, mask, ages, offsets


def test_irregular_grid_deduplicates_and_never_crosses_matches():
    source = _source()
    nodes, edges, mask, ages = fixed_minute_grid(*source)
    assert np.array_equal(mask[3], [False] * 5 + [True] * 3)
    assert nodes[3, -3:, 0, 0].tolist() == [1, 3, 4]
    assert ages[3, -3:].tolist() == pytest.approx([124 / 60, 62 / 60, 0])
    assert nodes[4, -1, 0, 0] == 11 and mask[4].sum() == 1
    assert not np.any(edges[4, :-1])
    assert np.array_equal(nodes[:, -1], source[0][:, -1])


def test_grid_rejects_inconsistent_cadence_or_boundaries():
    nodes, edges, mask, ages, offsets = _source()
    bad = ages.copy()
    bad[3, -3] += 0.1
    with pytest.raises(ValueError, match="ages disagree"):
        fixed_minute_grid(nodes, edges, mask, bad, offsets)
    wrong = offsets.copy()
    wrong[1] = 3
    with pytest.raises(ValueError, match="match boundary"):
        fixed_minute_grid(nodes, edges, mask, ages, wrong)
