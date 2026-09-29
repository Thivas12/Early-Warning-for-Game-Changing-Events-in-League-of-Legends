"""The hybrid candidate keeps observed coverage and hazard labels separate."""

import numpy as np
import pytest

from league_ews.m1_graph_window import STEPS
from league_ews.m2_backend import MODES, TorchM2Backend, spatial_inputs


def _batch(rows=2):
    nodes = np.zeros((rows, STEPS, 12, 11), dtype=np.float32)
    edges = np.zeros((rows, STEPS, 5, 12, 12), dtype=np.bool_)
    mask = np.zeros((rows, STEPS), dtype=np.bool_)
    ages = np.zeros((rows, STEPS), dtype=np.float32)
    mask[:, -1] = True
    nodes[:, -1, 0, 10] = 1
    nodes[:, -1, 0, 8:10] = [0.5, 0.25]
    nodes[:, -1, 5, 10] = 1
    nodes[:, -1, 5, 8:10] = [0.75, 0.25]
    nodes[:, -1, 10, 8:10] = [0.5, 0.5]
    nodes[:, -1, 11, 8:10] = [0.75, 0.75]
    nodes[:, -1, 11, 10] = 1
    hazards = np.zeros((rows, 3, 6), dtype=np.float32)
    hazards[0, 1, 2] = 1
    return nodes, edges, mask, ages, hazards


def test_spatial_inputs_preserve_explicit_coverage_and_fixed_scale():
    nodes, edges, mask, ages, _ = _batch()
    scaled, gate = spatial_inputs(nodes, edges, mask, ages)
    assert scaled.shape == (2, 24) and gate.shape == (2, 4)
    np.testing.assert_array_equal(gate[:, :3], [[0.1, 0.1, 1], [0.1, 0.1, 1]])
    assert scaled[0, 8] == pytest.approx(0.25 / 1.5)
    nodes[:, -1, 5, 10] = 0
    nodes[:, -1, 5, 8:10] = 0
    scaled, gate = spatial_inputs(nodes, edges, mask, ages)
    assert scaled[0, 8] == 0 and gate[0, 2] == 0


@pytest.mark.parametrize("mode", MODES)
def test_hybrid_modes_train_and_predict_monotone_horizons(mode):
    pytest.importorskip("torch")
    nodes, edges, mask, ages, hazards = _batch()
    backend = TorchM2Backend(20260915, mode=mode)
    loss, rows = backend.train_shard(nodes, nodes, edges, mask, ages, hazards, seed=1)
    assert rows == 2 and np.isfinite(loss)
    risks = backend.predict_shard(nodes, nodes, edges, mask, ages)
    assert risks.shape == (2, 12) and np.isfinite(risks).all()
    assert np.all(np.diff(risks.reshape(2, 3, 4), axis=-1) >= 0)
    state = backend.state_dict()
    again = TorchM2Backend(20260915, mode=mode)
    again.load_state_dict(state)
    np.testing.assert_allclose(again.predict_shard(nodes, nodes, edges, mask, ages), risks)
