"""Independent integration of deployed policies and numerical derivative checks."""

from itertools import pairwise

import numpy as np
import pytest

from research.objective_onset import score_alarms
from research.run_precontact_pilot import emit_alarms

torch = pytest.importorskip("torch")
pytest.importorskip("numba")
shared_threshold_counts = pytest.importorskip("research.shared_threshold").shared_threshold_counts


def integrate(scores, ticks, targets):
    # Do not use prefix increments: directly score midpoint threshold policies.
    breaks = np.unique(np.r_[0.0, scores, 1.0])
    expected = np.zeros(2)
    for left, right in pairwise(breaks):
        alarms = emit_alarms(ticks, scores, float((left + right) / 2))
        metrics = score_alarms(alarms, targets, min_lead=600, max_lead=1800)
        expected += (right - left) * np.array([metrics["hits"], metrics["unmatched_alarms"]])
    return expected


@pytest.mark.parametrize("targets", [[], [1800], [1800, 2100, 3900], [600, 1200, 2400, 4200]])
@pytest.mark.parametrize(
    "scores", [[0.21, 0.44, 0.67, 0.32, 0.83, 0.56], [0.0, 1.0, 0.4, 0.4, 1.0, 0.0]]
)
def test_counts_agree_with_actual_policy_interval_integral(targets, scores):
    ticks = np.array([0, 150, 600, 1800, 1950, 3600])
    p = torch.tensor([scores], dtype=torch.float64)
    y = torch.tensor(
        [[any(600 <= t - a <= 1800 for t in targets) for a in ticks]], dtype=torch.float64
    )
    hits, wrong = shared_threshold_counts(
        p, torch.tensor(ticks[None]), y, torch.ones_like(y, dtype=torch.bool)
    )
    np.testing.assert_allclose(
        [hits.item(), wrong.item()], integrate(np.array(scores), ticks, targets), atol=1e-12
    )


def test_exact_region_gradient_against_independent_numerical_integration():
    ticks = np.array([1000, 1150, 1600, 2800, 2950, 4600])
    targets = [2800, 3100, 4900]
    scores = np.array([0.21, 0.44, 0.67, 0.32, 0.83, 0.56])
    p = torch.tensor(scores[None], requires_grad=True)
    y = torch.tensor(
        [[any(600 <= t - a <= 1800 for t in targets) for a in ticks]], dtype=torch.float64
    )
    h, w = shared_threshold_counts(
        p, torch.tensor(ticks[None]), y, torch.ones_like(y, dtype=torch.bool)
    )
    analytic = torch.autograd.grad((h - 0.7 * w).sum(), p)[0].numpy()[0]
    numerical = np.zeros_like(scores)
    for j in range(len(scores)):
        upper, lower = scores.copy(), scores.copy()
        upper[j] += 1e-6
        lower[j] -= 1e-6
        numerical[j] = (
            (integrate(upper, ticks, targets) - integrate(lower, ticks, targets))
            @ np.array([1, -0.7])
            / 2e-6
        )
    np.testing.assert_allclose(analytic, numerical, atol=1e-9)


def test_padding_boundaries_and_event_free_sequences():
    p = torch.tensor([[1.0, 1.0, 0.99], [0.8, 0.5, 0.2]], requires_grad=True)
    ticks = torch.tensor([[3000, 4800, 0], [3000, 4500, 4800]])
    y = torch.tensor([[1.0, 0.0, 1.0], [0.0, 0.0, 0.0]])
    valid = torch.tensor([[True, True, False], [True, True, True]])
    h, w = shared_threshold_counts(p, ticks, y, valid)
    torch.testing.assert_close(h, torch.tensor([1.0, 0.0]))
    torch.testing.assert_close(w, torch.tensor([1.0, 1.0]))
    gradient = torch.autograd.grad((w - h).sum(), p)[0]
    assert gradient[0, 2] == 0
    assert gradient[1, 0] > 0
    with pytest.raises(ValueError, match="precede padding"):
        shared_threshold_counts(
            p, ticks, y, torch.tensor([[True, False, True], [True, True, True]])
        )
