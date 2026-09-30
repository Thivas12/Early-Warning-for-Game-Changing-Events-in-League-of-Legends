"""Exact joint acquisition/emission training on exogenous complete panels.

Research prototype. The finite controller retains the latest acquired observation,
its age, and cooldown. It does not retain arbitrary acquisition history. Dynamic
programming and analytical action marginalization are established techniques.
"""

from __future__ import annotations

import functools
import itertools
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class World:
    steps: int = 9
    cooldown: int = 3
    period: int = 3
    onset_probability: float = 0.10
    persistence: float = 0.80
    sensitivity: float = 0.85
    specificity: float = 0.85
    wrong_price: float = 1.0
    observation_price: float = 0.05

    def __post_init__(self) -> None:
        if (
            self.steps < 1
            or self.period < 1
            or self.steps % self.period
            or self.cooldown < self.period
            or not 0 < self.onset_probability < self.persistence < 1
            or not 0 < self.sensitivity < 1
            or not 0 < self.specificity < 1
            or not np.isfinite(self.wrong_price)
            or not np.isfinite(self.observation_price)
            or min(self.wrong_price, self.observation_price) < 0
        ):
            raise ValueError("Invalid finite binary world or credit/cooldown condition")

    @property
    def prior(self) -> float:
        return self.onset_probability / (1 - self.persistence + self.onset_probability)


def generate(world: World, n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Complete sensor panel, plus events at registered opportunities.

    Sensors exist at these ticks only. Acquiring reveals x[t] and cannot change
    the hidden trajectory. Event/reward feedback is never a policy input.
    """
    if n < 1:
        raise ValueError("Need at least one independent trajectory")
    rng = np.random.default_rng(seed)
    z = np.zeros((n, world.steps + 1), dtype=bool)
    z[:, 0] = rng.random(n) < world.prior
    for t in range(1, world.steps + 1):
        chance = np.where(z[:, t - 1], world.persistence, world.onset_probability)
        z[:, t] = rng.random(n) < chance
    observation_chance = np.where(z[:, :-1], world.sensitivity, 1 - world.specificity)
    x = (rng.random((n, world.steps)) < observation_chance).astype(np.int64)
    event_indices = ((np.arange(world.steps) // world.period) + 1) * world.period
    y = z[:, event_indices].astype(float)
    return x, y


def features_at(x: Any, t: int, slots: int) -> tuple[Any, Any]:
    """Controller symbols for all possible latest-observation indices.

    Slot zero denotes no observation. Slot j+1 denotes acquisition at time j.
    This returns current x[t] only when slots includes t+2 (post-acquisition).
    """
    import torch

    if slots not in (t + 1, t + 2):
        raise ValueError("Slots must describe pre- or post-acquisition information")
    symbols = torch.cat((torch.full_like(x[:, :1], 2), x[:, : slots - 1]), dim=1)
    age = t + 1 - torch.arange(slots, device=x.device)
    return symbols, age


def make_controller(world: World, seed: int = 0) -> Any:
    """Shared causal parameter tables, never indexed by trajectory or outcome."""
    import torch

    class Controller(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            generator = torch.Generator().manual_seed(seed)
            shape = (world.period, world.steps + 1, 3)
            self.acquire = torch.nn.Parameter(
                -1 + 0.01 * torch.randn((*shape, world.cooldown), generator=generator)
            )
            self.warn = torch.nn.Parameter(-1 + 0.01 * torch.randn(shape, generator=generator))

        def tables(self, x: Any, t: int, mode: str = "joint") -> tuple[Any, Any]:
            phase = t % world.period
            old_symbols, old_age = features_at(x, t, t + 1)
            new_symbols, new_age = features_at(x, t, t + 2)
            q = torch.sigmoid(self.acquire[phase, old_age[None, :], old_symbols])
            p = torch.sigmoid(self.warn[phase, new_age[None, :], new_symbols])
            if mode == "all":
                q = torch.ones_like(q)
            elif mode == "none":
                q = torch.zeros_like(q)
            elif mode.startswith("periodic-"):
                parts = mode.split("-")
                every = int(parts[1])
                offset = int(parts[2]) if len(parts) == 3 else 0
                if every < 1 or not 0 <= offset < every:
                    raise ValueError("Invalid observation interval or phase")
                q = torch.full_like(q, float(t % every == offset))
            elif mode != "joint":
                raise ValueError("Unknown observation policy")
            return q, p

    return Controller()


def exact_rollout(controller: Any, x: Any, y: Any, world: World, mode: str = "joint") -> Any:
    """Return per-trace [timely, wrong, acquisitions] integrating ALL action coins.

    d[last_read_index, cooldown] is a joint distribution; factorizing it is wrong
    in general. States with identical retained information merge exactly. Runtime
    O(B*T^2*C), rolling state O(B*T*C); autograd storage is larger.
    """
    import torch

    dtype = controller.warn.dtype
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] != world.steps:
        raise ValueError("Expected complete aligned [trajectory,time] panels")
    mass = torch.zeros((len(x), 1, world.cooldown), dtype=dtype, device=x.device)
    mass[:, 0, 0] = 1
    counts = torch.zeros((len(x), 3), dtype=dtype, device=x.device)
    for t in range(world.steps):
        q, p = controller.tables(x, t, mode)
        acquired = mass * q
        # Read paths merge by new observation index while preserving cooldown.
        after_read = torch.cat((mass * (1 - q), acquired.sum(1, keepdim=True)), dim=1)
        emitted = after_read[:, :, 0] * p
        alarm_mass = emitted.sum(1)
        counts = counts + torch.stack(
            (alarm_mass * y[:, t], alarm_mass * (1 - y[:, t]), acquired.sum((1, 2))), dim=1
        )
        columns = [after_read[:, :, 0] - emitted]
        for _c in range(1, world.cooldown):
            columns.append(torch.zeros_like(emitted))
        next_mass = torch.stack(columns, dim=-1)
        if world.cooldown > 1:
            next_mass = next_mass + torch.cat(
                (after_read[:, :, 1:], torch.zeros_like(after_read[:, :, :1])), dim=-1
            )
        reset = torch.nn.functional.one_hot(
            torch.tensor(world.cooldown - 1, device=x.device), world.cooldown
        ).to(dtype)
        mass = next_mass + emitted[:, :, None] * reset
    return counts


def sampled_rollout(controller: Any, x: Any, y: Any, world: World) -> tuple[Any, Any]:
    """Unbiased score-function comparator with identical controller/information."""
    import torch

    ids = torch.arange(len(x), device=x.device)
    last = torch.zeros(len(x), dtype=torch.long, device=x.device)
    cooldown = torch.zeros_like(last)
    counts = torch.zeros((len(x), 3), device=x.device)
    log_score = torch.zeros(len(x), device=x.device)
    for t in range(world.steps):
        q, p = controller.tables(x, t)
        distribution = torch.distributions.Bernoulli(q[ids, last, cooldown])
        read = distribution.sample()
        log_score = log_score + distribution.log_prob(read)
        last = torch.where(read.bool(), t + 1, last)
        eligible = cooldown == 0
        alarm_distribution = torch.distributions.Bernoulli(p[ids, last])
        coins = alarm_distribution.sample()
        emitted = coins * eligible
        log_score = log_score + alarm_distribution.log_prob(coins) * eligible
        counts = counts + torch.stack((emitted * y[:, t], emitted * (1 - y[:, t]), read), 1)
        cooldown = torch.where(emitted.bool(), world.cooldown, cooldown)
        cooldown = (cooldown - 1).clamp(min=0)
    return counts, log_score


def utility(counts: Any, world: World) -> Any:
    return (
        counts[..., 0]
        - world.wrong_price * counts[..., 1]
        - world.observation_price * counts[..., 2]
    )


def exhaustive_counts(controller: Any, x: Any, y: Any, world: World) -> np.ndarray:
    """Independent literal action-tree enumeration, at most five ticks."""
    import torch

    if world.steps > 5 or len(x) != 1:
        raise ValueError("Literal enumeration supports one short trace")
    with torch.no_grad():
        tables = [
            (q.numpy()[0], p.numpy()[0])
            for q, p in [controller.tables(x, t) for t in range(world.steps)]
        ]
    result = np.zeros(3)
    for actions in itertools.product(range(4), repeat=world.steps):
        last, cooldown, probability = 0, 0, 1.0
        counts = np.zeros(3)
        for t, action in enumerate(actions):
            read, alarm = divmod(action, 2)
            q, p = tables[t]
            chance = q[last, cooldown]
            probability *= chance if read else 1 - chance
            if read:
                last = t + 1
                counts[2] += 1
            alarm_chance = p[last] if cooldown == 0 else 0.0
            probability *= alarm_chance if alarm else 1 - alarm_chance
            if alarm:
                counts[int(not bool(y[0, t]))] += 1
                cooldown = world.cooldown
            cooldown = max(0, cooldown - 1)
        result += probability * counts
    return result


def bayes_reference(world: World, *, observation_mode: str = "optional") -> dict[str, Any]:
    """Known-world, full-belief planning reference; exact finite-horizon recursion.

    Beliefs are floating point, never grid-quantized. The planner knows transition
    and sensor laws, NOT hidden states, future readings, events, or reward feedback.
    This is classical POMDP planning, not claimed as a new algorithm.
    """
    if observation_mode not in ("optional", "all", "none"):
        raise ValueError("Unknown reference information restriction")
    rho = world.persistence - world.onset_probability

    def advance(b: float, n: int = 1) -> float:
        return world.prior + (b - world.prior) * rho**n

    def worth(counts: tuple[float, float, float]) -> float:
        return float(utility(np.asarray(counts), world))

    @functools.cache
    def choose_alarm(t: int, belief: float, cooldown: int) -> tuple[float, float, float]:
        wait = value(t + 1, advance(belief), max(0, cooldown - 1))
        if cooldown:
            return wait
        lead = world.period - t % world.period
        timely = advance(belief, lead)
        future = value(t + 1, advance(belief), world.cooldown - 1)
        alarm = (future[0] + timely, future[1] + 1 - timely, future[2])
        return alarm if worth(alarm) > worth(wait) else wait

    @functools.cache
    def value(t: int, belief: float, cooldown: int) -> tuple[float, float, float]:
        if t == world.steps:
            return (0.0, 0.0, 0.0)
        wait = choose_alarm(t, belief, cooldown)
        if observation_mode == "none":
            return wait
        positive = belief * world.sensitivity + (1 - belief) * (1 - world.specificity)
        b1 = belief * world.sensitivity / positive
        b0 = belief * (1 - world.sensitivity) / (1 - positive)
        yes = choose_alarm(t, b1, cooldown)
        no = choose_alarm(t, b0, cooldown)
        read = tuple(positive * a + (1 - positive) * b for a, b in zip(yes, no, strict=True))
        read = (read[0], read[1], read[2] + 1)
        if observation_mode == "all" or worth(read) > worth(wait):
            return read
        return wait

    counts = value(0, world.prior, 0)
    return {"counts": list(counts), "utility": worth(counts), "states": value.cache_info().currsize}
