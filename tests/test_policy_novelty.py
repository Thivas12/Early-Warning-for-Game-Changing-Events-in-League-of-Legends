"""Independent checks of the narrower claim and the controls that challenge it."""

import numpy as np
import pytest

from league_ews.policy_novelty import (
    enumerated_score_gradient,
    exact_credit,
    pointwise_envelope,
    two_decision_plan,
    uniform_temporal_score_loss,
)
from league_ews.scheduled_policy import decision_trace, marginal_counts, summary, torch_marginals


def test_adjoint_scan_matches_dense_autograd_and_enumerated_policy():
    torch = pytest.importorskip("torch")
    rng = np.random.default_rng(96)
    for n in (1, 2, 8):
        for cooldown in (1, 30, 60):
            times = np.cumsum(rng.integers(1, 31, n))
            values, rewards = rng.uniform(0, 1, n), rng.normal(size=n)
            exact = exact_credit(times, values, rewards, cooldown)
            probabilities = torch.tensor(values[None, :], requires_grad=True)
            distances = times[:, None] - times[None, :]
            blocked = torch.tensor(((distances > 0) & (distances < cooldown))[None, :, :])
            dense = torch_marginals(probabilities, blocked)
            utility = (dense * torch.tensor(rewards)).sum()
            utility.backward()
            np.testing.assert_allclose(dense.detach()[0], exact["marginals"], atol=1e-12)
            np.testing.assert_allclose(probabilities.grad[0], exact["gradient_probabilities"])
            sampled = enumerated_score_gradient(times, values, rewards, cooldown)
            assert sampled["probability_mass"] == pytest.approx(1)
            assert exact["utility"] == pytest.approx(sampled["utility"])
            np.testing.assert_allclose(
                exact["gradient_logits"], sampled["gradient_logits"], atol=1e-12
            )
    assert np.any(sampled["single_sample_gradient_variance"] > 0)


def test_exclusion_boundary_empty_trace_and_invalid_duplicate_event_credit():
    times, p = np.array([0, 30_000, 60_000]), np.ones(3)
    exact = exact_credit(times, p, np.ones(3))
    np.testing.assert_array_equal(exact["marginals"], [1, 0, 1])
    np.testing.assert_array_equal(exact["gradient_logits"], [0, 0, 0])
    empty = np.array([])
    assert exact_credit(empty, empty, empty)["utility"] == 0
    assert enumerated_score_gradient(empty, empty, empty)["utility"] == 0
    # Both alarms can be 20--60 seconds ahead of the SAME event at 50 seconds.
    duplicate = exact_credit(times[:2], p[:2], p[:2], cooldown=30_000)
    assert duplicate["utility"] == 2
    assert len({50_000}) == 1
    with pytest.raises(ValueError):
        exact_credit(times[::-1], p, p)
    with pytest.raises(ValueError):
        exact_credit(times, p + 0.1, p)
    with pytest.raises(ValueError):
        exact_credit(times, p, p, cooldown=0)
    with pytest.raises(ValueError):
        enumerated_score_gradient(np.arange(13), np.ones(13), np.ones(13))


@pytest.mark.parametrize("mode", ["prod", "max"])
@pytest.mark.parametrize("score", ["tss", "f1"])
def test_temporal_score_loss_sequence_boundaries_and_gradients(mode, score):
    torch = pytest.importorskip("torch")
    p = torch.tensor([[0.12, 0.83, 0.31], [0.76, 0.22, 0.61]], dtype=torch.float64)
    p.requires_grad_()
    labels = torch.tensor([[0, 1, 1], [1, 0, 0]], dtype=torch.float64)
    together = uniform_temporal_score_loss(p, labels, mode=mode, score=score)
    separate = torch.stack(
        [
            uniform_temporal_score_loss(a[None], b[None], mode=mode, score=score)
            for a, b in zip(p, labels, strict=True)
        ]
    ).mean()
    torch.testing.assert_close(together, separate)
    assert torch.autograd.gradcheck(
        lambda values: uniform_temporal_score_loss(values, labels, mode=mode, score=score),
        (p,),
    )
    # One-slot sequences have no temporal neighbors: binary F1=2p/(1+p).
    single = uniform_temporal_score_loss(
        torch.tensor([[0.4]], dtype=torch.float64), torch.ones((1, 1)), mode=mode, score="f1"
    )
    assert float(single) == pytest.approx(1 - 0.8 / 1.4)
    # No positive predictions or labels: the authors' zero-denominator rule is finite.
    zero = uniform_temporal_score_loss(torch.zeros((1, 1)), torch.zeros((1, 1)), mode=mode)
    assert float(zero) == pytest.approx(1)


def test_temporal_score_rejects_unsupported_configurations():
    torch = pytest.importorskip("torch")
    p, y = torch.full((1, 2), 0.5), torch.ones((1, 2))
    for kwargs in (
        {"mode": "other"},
        {"score": "other"},
        {"weights": ()},
        {"weights": (0.2, 0.3)},
        {"weights": (0.5, 0.5)},
        {"weights": (1.1,), "mode": "max"},
        {"weights": (-0.1,)},
    ):
        with pytest.raises(ValueError):
            uniform_temporal_score_loss(p, y, **kwargs)


def test_bayes_planner_matches_candidate_and_pointwise_bound_is_not_general():
    conditional = np.array([[0.6, 1], [0.6, 0]])
    plan = two_decision_plan(conditional)
    np.testing.assert_array_equal(plan, [[0, 1], [1, 0]])
    events = [(50_000,)] * 6 + [(80_000,)] * 4 + [(40_000,)] * 6 + [()] * 4
    traces = [decision_trace((0, 30_000, 120_000), e, frame_only=True) for e in events]
    results = summary(marginal_counts(traces, [plan[i // 10] for i in range(20)]))
    assert results["timely_recall"] == 1
    assert results["non_timely_per_match"] == pytest.approx(0.2)
    bound = pointwise_envelope()
    assert bound["event_recall_upper_bound"] == pytest.approx(0.703125)
    r = bound["first_action_probability"]
    score_policy = np.array([[r, 1], [r, 0]])
    upper = summary(marginal_counts(traces, [score_policy[i // 10] for i in range(20)]))
    assert upper["timely_recall"] == pytest.approx(bound["event_recall_upper_bound"])
    assert upper["non_timely_per_match"] == pytest.approx(0.25)
    np.testing.assert_array_equal(two_decision_plan(np.zeros((1, 2))), [[0, 0]])
    with pytest.raises(ValueError):
        two_decision_plan(np.ones((2, 3)))
    with pytest.raises(ValueError):
        two_decision_plan(conditional, wrong_cost=-1)
    with pytest.raises(ValueError):
        pointwise_envelope(alpha=0.4)
