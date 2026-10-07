"""Preserve original architecture controls and the revised LeagueEWS update stream."""

import copy

import pytest

from league_ews.notebook_ews import NotebookEWSBackend
from scripts.matched_optimization_backend import NEW_VARIANTS, MatchedOptimizationBackend
from scripts.run_compact_notebook import sequences
from scripts.timely_neural_targets import fitted_targets
from scripts.timely_optimization_backend import TimelyOptimizationBackend
from tests.test_compact_research import norm, sample
from tests.test_task_sharing import same


@pytest.mark.parametrize("family", ("leagueews", "tcn", "gru"))
def test_original_weights_exactly_preserve_each_architecture(family):
    data = sample()
    x, mask, _ = sequences(data, norm())
    target = fitted_targets(data)
    original = NotebookEWSBackend(9, family=family)
    loss = original.train_shard(x, mask, target, seed=13)
    expected = copy.deepcopy(original.state_dict())
    revised = MatchedOptimizationBackend(9, variant=f"original_{family}")
    assert revised.train_shard(x, mask, target, seed=13) == loss
    same(revised.torch, revised.state_dict(), expected)


def test_equal_leagueews_exactly_preserves_completed_weighting_control():
    data = sample()
    x, mask, _ = sequences(data, norm())
    target = fitted_targets(data)
    original = TimelyOptimizationBackend(9, variant="equal_sum")
    loss = original.train_shard(x, mask, target, seed=13)
    expected = copy.deepcopy(original.state_dict())
    revised = MatchedOptimizationBackend(9, variant="equal_leagueews")
    assert revised.train_shard(x, mask, target, seed=13) == loss
    same(revised.torch, revised.state_dict(), expected)


@pytest.mark.parametrize("variant", NEW_VARIANTS)
def test_every_new_architecture_resumes_exactly(variant):
    data = sample()
    x, mask, _ = sequences(data, norm())
    target = fitted_targets(data)
    original = MatchedOptimizationBackend(9, variant=variant)
    original.train_shard(x, mask, target, seed=13)
    state = copy.deepcopy(original.state_dict())
    loss = original.train_shard(x, mask, target, seed=14)
    expected = copy.deepcopy(original.state_dict())
    restored = MatchedOptimizationBackend(123, variant=variant)
    restored.load_state_dict(state)
    assert restored.train_shard(x, mask, target, seed=14) == loss
    same(restored.torch, restored.state_dict(), expected)
