"""Train and stress-test the joint information/action controller on known worlds."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np

from research.joint_observation_warning import (
    World,
    bayes_reference,
    exact_rollout,
    features_at,
    generate,
    make_controller,
    sampled_rollout,
    utility,
)


def warm_start(controller: Any, x: Any, y: Any, world: World) -> None:
    """Common training-only empirical probability table with Laplace smoothing.

    All feasible latest-observation summaries receive supervision. The logits
    are multiplied by four for an identical near-threshold initialization across
    estimators. No generative probabilities, evaluation labels or hidden Z used.
    """
    import torch

    positives = torch.ones_like(controller.warn)
    totals = torch.full_like(controller.warn, 2)
    for t in range(world.steps):
        symbols, ages = features_at(x, t, t + 2)
        for slot in range(t + 2):
            for symbol in range(3):
                ids = symbols[:, slot] == symbol
                positives[t % world.period, ages[slot], symbol] += y[ids, t].sum()
                totals[t % world.period, ages[slot], symbol] += ids.sum()
    with torch.no_grad():
        controller.warn.copy_(4 * torch.logit(positives / totals))


def fit(world: World, x: Any, y: Any, method: str, seed: int, steps: int) -> tuple[Any, float]:
    import torch

    torch.manual_seed(seed)
    controller = make_controller(world, seed)
    warm_start(controller, x, y, world)
    optimizer = torch.optim.Adam(controller.parameters(), lr=0.08)
    started = time.perf_counter()
    mode = method if method in ("all", "none") or method.startswith("periodic-") else "joint"
    for _ in range(steps):
        ids = torch.randint(len(x), (min(len(x), 256),))
        if method == "sampled":
            # Eight independent action draws for each sampled data minibatch.
            # Leave-one-trajectory-out batch baseline is independent of own actions.
            sample_x, sample_y = x[ids].repeat((8, 1)), y[ids].repeat((8, 1))
            counts, log_score = sampled_rollout(controller, sample_x, sample_y, world)
            rewards = utility(counts, world).detach()
            baseline = (rewards.sum() - rewards) / (len(rewards) - 1)
            loss = -((rewards - baseline) * log_score).mean()
        else:
            counts = exact_rollout(controller, x[ids], y[ids], world, mode)
            loss = -utility(counts, world).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    return controller, time.perf_counter() - started


def evaluate(controller: Any, x: Any, y: Any, world: World, method: str) -> np.ndarray:
    import torch

    mode = method if method in ("all", "none") or method.startswith("periodic-") else "joint"
    with torch.no_grad():
        return np.concatenate(
            [
                exact_rollout(controller, x[i : i + 256], y[i : i + 256], world, mode).numpy()
                for i in range(0, len(x), 256)
            ]
        )


def summarize(counts: np.ndarray, y: np.ndarray, world: World) -> dict[str, float]:
    return {
        "utility": float(utility(counts, world).mean()),
        "timely_recall": float(counts[:, 0].sum() / y[:, :: world.period].sum()),
        "timely_per_trace": float(counts[:, 0].mean()),
        "wrong_per_trace": float(counts[:, 1].mean()),
        "observations_per_trace": float(counts[:, 2].mean()),
    }


def paired_interval(a: np.ndarray, b: np.ndarray, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    differences = a - b
    samples = np.asarray(
        [differences[rng.integers(len(a), size=len(a))].mean() for _ in range(1000)]
    )
    return {
        "difference": float(differences.mean()),
        "lower": float(np.quantile(samples, 0.025)),
        "upper": float(np.quantile(samples, 0.975)),
        "scope": "paired-trajectory-bootstrap;seed-averaged-fits;conditional-on-fitted-models",
    }


def run(output: Path, train_size: int, test_size: int, steps: int, seeds: list[int]) -> None:
    import torch

    torch.set_num_threads(2)
    if min(train_size, test_size, steps) < 1 or not seeds:
        raise ValueError("Positive experiment sizes required")
    world = World()
    train_x, train_y = generate(world, train_size, 602301)
    x, y = torch.tensor(train_x), torch.tensor(train_y, dtype=torch.float32)
    cases = {
        "matched": world,
        "weaker_sensor": replace(world, sensitivity=0.65, specificity=0.65),
        "higher_event_rate": replace(world, onset_probability=0.20),
        "uninformative_sensor": replace(world, sensitivity=0.5, specificity=0.5),
    }
    test_sets = {
        name: generate(case, test_size, 702301 + i) for i, (name, case) in enumerate(cases.items())
    }
    methods = (
        "joint",
        "sampled",
        "none",
        "all",
        "periodic-2",
        "periodic-2-1",
        "periodic-3",
        "periodic-3-1",
        "periodic-3-2",
    )
    stored: dict[str, Any] = {name: {} for name in cases}
    runs = []
    for seed in seeds:
        for method in methods:
            controller, seconds = fit(world, x, y, method, seed, steps)
            row: dict[str, Any] = {"seed": seed, "method": method, "training_seconds": seconds}
            for name, case in cases.items():
                test_x, test_y = test_sets[name]
                counts = evaluate(
                    controller, torch.tensor(test_x), torch.tensor(test_y), case, method
                )
                stored[name].setdefault(method, []).append(counts)
                row[name] = summarize(counts, test_y, case)
            runs.append(row)
            print(json.dumps(row), flush=True)
    aggregate = {}
    for name, case in cases.items():
        averaged = {method: np.mean(rows, axis=0) for method, rows in stored[name].items()}
        averaged["silent"] = np.zeros((test_size, 3))
        aggregate[name] = {
            "world": asdict(case),
            "metrics": {
                method: summarize(counts, test_sets[name][1], case)
                for method, counts in averaged.items()
            },
            "joint_minus": {
                method: paired_interval(
                    utility(averaged["joint"], case), utility(counts, case), 80301
                )
                for method, counts in averaged.items()
                if method != "joint"
            },
            "full_belief_known_world_reference": bayes_reference(case),
            "no_observation_known_world_reference": bayes_reference(case, observation_mode="none"),
        }
        print(name, json.dumps(aggregate[name]), flush=True)
    result = {
        "status": "research-prototype;synthetic-worlds;no-League-or-SOTA-result",
        "research_question": (
            "exact joint acquisition and repeated-warning credit without action-path sampling"
        ),
        "world": asdict(world),
        "protocol": {
            "train_trajectories": train_size,
            "evaluation_trajectories_per_case": test_size,
            "optimization_steps": steps,
            "seeds": seeds,
            "methods": list(methods),
            "evaluation_action_semantics": "exact-expectations-for-every-trained-policy",
            "prices": "same-fixed-Lagrangian-prices;not-matched-hard-budget-operating-points",
            "sampled_comparator": (
                "same-controller;8-action-draws-per-minibatch;training-time-reported"
            ),
            "warm_start": "training-only-Laplace-probability-table;logits-times-four",
            "shift": "train-on-matched-only;no-adaptation-or-selection-on-evaluation-cases",
            "reference": (
                "classical-full-belief-POMDP;knows-world-law;no-hidden-state-or-future-access"
            ),
            "confirmation": "designed-synthetic-study;not-independent-real-world-confirmation",
        },
        "runs": runs,
        "aggregate": aggregate,
        "code_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__), Path(__file__).with_name("joint_observation_warning.py")]
        },
        "environment": {"torch": str(torch.__version__), "numpy": np.__version__, "device": "cpu"},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/joint-observation-warning-2026-09-30.json")
    )
    parser.add_argument("--train-size", type=int, default=2048)
    parser.add_argument("--test-size", type=int, default=8192)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--seeds", type=int, nargs="+", default=[31, 32, 33])
    args = parser.parse_args()
    run(args.output, args.train_size, args.test_size, args.steps, args.seeds)
