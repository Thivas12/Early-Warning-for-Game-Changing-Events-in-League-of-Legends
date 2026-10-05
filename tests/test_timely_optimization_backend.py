"""Protect the existing controls and exact resume across optimizer variants."""

import copy

import numpy as np
import pytest

from league_ews.notebook_ews import NotebookEWSBackend
from scripts.diagnose_timely_optimization import local_step
from scripts.pcgrad_backend import PCGradBackend
from scripts.run_compact_notebook import sequences
from scripts.timely_neural_targets import fitted_targets
from scripts.timely_optimization_backend import VARIANTS, TimelyOptimizationBackend
from tests.test_compact_research import norm, sample
from tests.test_task_sharing import same


@pytest.mark.parametrize(
    ("variant", "original"),
    [("original_sum", NotebookEWSBackend), ("original_pcgrad", PCGradBackend)],
)
def test_original_weight_controls_preserve_existing_backends(variant, original):
    data = sample()
    x, mask, _ = sequences(data, norm())
    y = fitted_targets(data)
    reference = original(9)
    reference_loss = reference.train_shard(x, mask, y, seed=13)
    expected = copy.deepcopy(reference.state_dict())
    control = TimelyOptimizationBackend(9, variant=variant)
    assert control.train_shard(x, mask, y, seed=13) == reference_loss
    same(control.torch, expected, control.state_dict())


@pytest.mark.parametrize("variant", tuple(VARIANTS))
def test_resume_exact_for_every_factorial_cell(variant):
    data = sample()
    x, mask, _ = sequences(data, norm())
    y = fitted_targets(data)
    original = TimelyOptimizationBackend(9, variant=variant)
    original.train_shard(x, mask, y, seed=13)
    state = copy.deepcopy(original.state_dict())
    loss = original.train_shard(x, mask, y, seed=14)
    expected = copy.deepcopy(original.state_dict())
    resumed = TimelyOptimizationBackend(123, variant=variant)
    resumed.load_state_dict(state)
    assert resumed.train_shard(x, mask, y, seed=14) == loss
    same(resumed.torch, expected, resumed.state_dict())


def test_equal_weights_preserve_total_and_all_heads_train():
    assert sum(VARIANTS["equal_sum"]["weights"]) == sum(VARIANTS["original_sum"]["weights"])
    data = sample()
    x, mask, _ = sequences(data, norm())
    backend = TimelyOptimizationBackend(9, variant="equal_sum")
    heads = [copy.deepcopy(head.state_dict()) for head in backend.model.heads]
    backend.train_shard(x, mask, fitted_targets(data), seed=13)
    for before, head in zip(heads, backend.model.heads, strict=True):
        assert any(
            not backend.torch.equal(value, head.state_dict()[name])
            for name, value in before.items()
        )
    with pytest.raises(ValueError, match="binary"):
        backend.train_shard(x, mask, np.full((len(x), 12), np.nan), seed=13)


def test_virtual_probes_restore_parameters_moments_and_dropout_without_mutating_source():
    data = sample()
    x, mask, _ = sequences(data, norm())
    target = fitted_targets(data)
    backend = TimelyOptimizationBackend(9, variant="original_sum")
    backend.train_shard(x, mask, target, seed=13)
    source = copy.deepcopy(backend.state_dict())
    original = copy.deepcopy(source)
    first = local_step(backend, source, x, mask, target, projection_seed=19)
    backend.weights = VARIANTS["equal_pcgrad"]["weights"]
    backend.aggregation = "pcgrad"
    other = local_step(backend, source, x, mask, target, projection_seed=19)
    assert first["unweighted_loss_before"] == other["unweighted_loss_before"]
    assert first["parameter_update_norm"] != other["parameter_update_norm"]
    backend.weights = VARIANTS["original_sum"]["weights"]
    backend.aggregation = "sum"
    assert local_step(backend, source, x, mask, target, projection_seed=19) == first
    same(backend.torch, original, source)
