"""Mathematical and information-access tests for the isolated research prototype."""

from dataclasses import replace

import numpy as np
import pytest

from research.joint_observation_warning import (
    World,
    bayes_reference,
    exact_rollout,
    exhaustive_counts,
    generate,
    make_controller,
    sampled_rollout,
    utility,
)


def test_joint_state_recursion_matches_literal_action_tree_and_gradient():
    torch = pytest.importorskip("torch")
    world = World(steps=3)
    controller = make_controller(world).double()
    x, y = torch.tensor([[1, 0, 1]]), torch.tensor([[1.0, 1.0, 1.0]])
    counts = exact_rollout(controller, x, y, world)
    expected = exhaustive_counts(controller, x, y, world)
    np.testing.assert_allclose(counts.detach().numpy()[0], expected, atol=1e-12)
    value = utility(counts, world).sum()
    value.backward()
    for parameter, index in (
        (controller.acquire, (0, 1, 2, 0)),
        (controller.acquire, (1, 1, 1, 2)),
        (controller.warn, (0, 0, 1)),
        (controller.warn, (2, 3, 2)),
    ):
        analytic = float(parameter.grad[index])
        with torch.no_grad():
            saved = float(parameter[index])
            parameter[index] = saved + 1e-5
            plus = utility(exhaustive_counts(controller, x, y, world), world)
            parameter[index] = saved - 1e-5
            minus = utility(exhaustive_counts(controller, x, y, world), world)
            parameter[index] = saved
        assert analytic == pytest.approx((plus - minus) / 2e-5, abs=1e-9)


def test_acquisition_cannot_read_current_or_future_observation_before_paying():
    torch = pytest.importorskip("torch")
    world = World(steps=3)
    controller = make_controller(world)
    x, changed = torch.tensor([[0, 0, 0]]), torch.tensor([[0, 1, 1]])
    q1, p1 = controller.tables(x, 1)
    q2, p2 = controller.tables(changed, 1)
    torch.testing.assert_close(q1, q2)
    torch.testing.assert_close(p1[:, :-1], p2[:, :-1])
    y = torch.ones((1, 3))
    torch.testing.assert_close(
        exact_rollout(controller, x, y, world, "none"),
        exact_rollout(controller, 1 - x, y, world, "none"),
    )


def test_deterministic_boundaries_cooldown_and_repeated_events():
    torch = pytest.importorskip("torch")
    world = World(steps=6)
    controller = make_controller(world)
    with torch.no_grad():
        controller.warn.fill_(100)
    x, y = torch.zeros((1, 6), dtype=torch.long), torch.ones((1, 6))
    counts = exact_rollout(controller, x, y, world, "all")
    np.testing.assert_allclose(counts.detach(), [[2, 0, 6]], atol=1e-6)
    never_read = exact_rollout(controller, x, y, world, "none")
    np.testing.assert_allclose(never_read.detach(), [[2, 0, 0]], atol=1e-6)


def test_sampled_policy_matches_integrated_counts_and_score_gradient():
    torch = pytest.importorskip("torch")
    torch.set_num_threads(2)
    torch.manual_seed(914)
    world = World(steps=3)
    controller = make_controller(world)
    x, y = torch.tensor([[1, 0, 1]]), torch.ones((1, 3))
    exact = exact_rollout(controller, x, y, world)
    objective = utility(exact, world).sum()
    objective.backward()
    index = (0, 1, 2, 0)
    true_gradient = float(controller.acquire.grad[index])
    controller.zero_grad()
    counts, log_score = sampled_rollout(
        controller, x.repeat((30000, 1)), y.repeat((30000, 1)), world
    )
    np.testing.assert_allclose(counts.mean(0).detach(), exact[0].detach(), atol=0.016)
    rewards = utility(counts, world).detach()
    ((rewards - objective.detach()) * log_score).mean().backward()
    assert float(controller.acquire.grad[index]) == pytest.approx(true_gradient, abs=0.01)


def test_bayes_reference_rejects_useless_information_and_dominates_restrictions():
    world = World(steps=3)
    reference = bayes_reference(world)
    assert reference["utility"] >= bayes_reference(world, observation_mode="none")["utility"]
    assert reference["utility"] >= bayes_reference(world, observation_mode="all")["utility"]
    useless = replace(world, sensitivity=0.5, specificity=0.5)
    assert bayes_reference(useless)["counts"][2] == 0
    assert (
        bayes_reference(useless)["utility"]
        == bayes_reference(useless, observation_mode="none")["utility"]
    )
    with pytest.raises(ValueError):
        World(cooldown=2)
    with pytest.raises(ValueError):
        World(steps=4)


def test_generator_aligns_repeated_outcomes_and_is_reproducible():
    world = World()
    x, y = generate(world, 20, 45)
    x2, y2 = generate(world, 20, 45)
    np.testing.assert_array_equal(x, x2)
    np.testing.assert_array_equal(y, y2)
    for t in range(0, world.steps, world.period):
        np.testing.assert_array_equal(y[:, t], y[:, t + 1])
