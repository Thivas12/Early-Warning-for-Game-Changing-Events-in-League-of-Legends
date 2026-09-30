"""Loss adaptation and actual one-to-one event-credit checks, before fitting."""

import itertools

import numpy as np
import pytest
import torch

from league_ews.policy_novelty import uniform_temporal_score_loss
from research.objective_onset import score_alarms
from research.public_objective_training import emitted, pooled_score_loss


@pytest.mark.parametrize("score", ["f1", "tss"])
@pytest.mark.parametrize("length", [1, 2, 9])
def test_pooled_loss_agrees_with_author_checked_single_sequence(score, length):
    rng = np.random.default_rng(381 + length)
    p = torch.tensor(rng.uniform(0.05, 0.95, (1, length)), requires_grad=True)
    y = torch.tensor(rng.integers(0, 2, (1, length)), dtype=torch.float64)
    got = pooled_score_loss(p, y, torch.ones_like(y, dtype=torch.bool), True, score)
    reference = uniform_temporal_score_loss(
        p, y, weights=(0.5, 0.25, 0.125), mode="max", score=score
    )
    torch.testing.assert_close(got, reference)
    torch.testing.assert_close(torch.autograd.grad(got, p)[0], torch.autograd.grad(reference, p)[0])


@pytest.mark.parametrize("score", ["f1", "tss"])
@pytest.mark.parametrize("temporal", [False, True])
def test_padding_cannot_change_value_or_gradient(score, temporal):
    p = torch.tensor([[0.12, 0.73], [0.82, 0.39]], dtype=torch.float64, requires_grad=True)
    y = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.float64)
    original = pooled_score_loss(p, y, torch.ones_like(y, dtype=torch.bool), temporal, score)
    # Deliberately put positive labels and high scores in padding.
    pp = torch.cat((p.detach(), torch.full((2, 4), 0.99)), 1).requires_grad_()
    yy = torch.cat((y, torch.ones((2, 4))), 1)
    mask = torch.cat(
        (torch.ones_like(y, dtype=torch.bool), torch.zeros((2, 4), dtype=torch.bool)), 1
    )
    padded = pooled_score_loss(pp, yy, mask, temporal, score)
    torch.testing.assert_close(original, padded)
    gradient = torch.autograd.grad(padded, pp)[0]
    torch.testing.assert_close(torch.autograd.grad(original, p)[0], gradient[:, :2])
    torch.testing.assert_close(gradient[:, 2:], torch.zeros_like(gradient[:, 2:]))


def test_temporal_discount_does_not_cross_matches_and_event_free_matches_matter():
    # A false alarm at the end of match A must not precede the event in match B.
    p = torch.tensor([[0.8], [0.6]], dtype=torch.float64, requires_grad=True)
    y = torch.tensor([[0.0], [1.0]], dtype=torch.float64)
    loss = pooled_score_loss(p, y, torch.ones_like(y, dtype=torch.bool), True)
    assert loss.item() == pytest.approx(1 - 1.2 / (1.2 + 0.8 + 0.4))
    gradient = torch.autograd.grad(loss, p)[0]
    assert gradient[0, 0] > 0  # Decrease scores in the event-free match.
    assert gradient[1, 0] < 0


@pytest.mark.parametrize("targets", [[], [1800], [1800, 2100, 3900], [600, 1200, 2400, 4200]])
def test_expected_credit_matches_exhaustive_deployed_matching(targets):
    # Tick units, irregular gaps, overlapping event windows, and exact cooldown edge.
    ticks = np.array([0, 150, 600, 1800, 1950, 3600])
    p = torch.tensor(
        [[0.21, 0.44, 0.67, 0.32, 0.83, 0.56]], dtype=torch.float64, requires_grad=True
    )
    valid = torch.ones_like(p, dtype=torch.bool)
    timely = torch.tensor([[any(600 <= t - a <= 1800 for t in targets) for a in ticks]])
    marginal = emitted(p, torch.tensor(ticks[None]), valid)
    utility = (marginal * (timely.to(p.dtype) - 0.7 * (~timely))).sum()
    expected = p.new_zeros(())
    for choices in itertools.product((False, True), repeat=len(ticks)):
        mass = p.new_ones(())
        alarms = []
        for i, proposed in enumerate(choices):
            mass = mass * (p[0, i] if proposed else 1 - p[0, i])
            if proposed and (not alarms or ticks[i] - alarms[-1] >= 1800):
                alarms.append(int(ticks[i]))
        result = score_alarms(alarms, targets, min_lead=600, max_lead=1800)
        expected = expected + mass * (result["hits"] - 0.7 * result["unmatched_alarms"])
    torch.testing.assert_close(utility, expected)
    torch.testing.assert_close(
        torch.autograd.grad(utility, p)[0], torch.autograd.grad(expected, p)[0]
    )


def test_emitted_padding_and_independent_matches():
    p = torch.tensor([[1.0, 1.0, 0.9], [1.0, 1.0, 1.0]], requires_grad=True)
    ticks = torch.tensor([[3000, 4800, 0], [3000, 4500, 4800]])
    valid = torch.tensor([[True, True, False], [True, True, True]])
    m = emitted(p, ticks, valid)
    torch.testing.assert_close(m, torch.tensor([[1.0, 1.0, 0.0], [1.0, 0.0, 1.0]]))
    assert torch.autograd.grad(m.sum(), p)[0][0, 2] == 0
