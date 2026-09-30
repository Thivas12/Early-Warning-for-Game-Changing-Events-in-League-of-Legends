"""Adversarial novelty checks. Population examples, not private-data experiments."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import sys
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.coordination_experiment import sha, write_json
from league_ews.policy_novelty import (
    WSOL_REFERENCE,
    enumerated_score_gradient,
    exact_credit,
    pointwise_envelope,
    two_decision_plan,
    uniform_temporal_score_loss,
)
from league_ews.scheduled_model import runtime
from league_ews.scheduled_policy import (
    action_probabilities,
    decision_trace,
    marginal_counts,
    select_policy,
    summary,
)
from scripts.scheduled_policy_controls import synthetic_controls


def reference_parity(reference_root: Path) -> dict[str, Any]:
    """Optional local author-source verification; never vendor or publish their code."""
    torch, _ = runtime("cpu")
    path = reference_root / "wsol/torch/wsol.py"
    raw = path.read_bytes()
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if blob != WSOL_REFERENCE["blob"]:
        raise ValueError("Author implementation differs from pinned blob")
    config = (reference_root / "wsol/config.py").read_bytes()
    config_blob = hashlib.sha1(f"blob {len(config)}\0".encode() + config).hexdigest()
    if config_blob != "27aff3e70f9faf2ac3117c3ec9d56c721c8d83d6":
        raise ValueError("Author configuration differs from pinned blob")
    sys.path.insert(0, str(reference_root))
    try:
        module = importlib.import_module("wsol.torch.wsol")
        if Path(module.__file__).resolve() != path.resolve():
            raise ValueError("Unexpected imported reference module")
        rng = np.random.default_rng(20260930)
        checks, max_value, max_gradient = 0, 0.0, 0.0
        for length in (1, 2, 7, 19):
            p = rng.uniform(0.05, 0.95, size=(3, length)).astype(np.float32)
            y = rng.integers(0, 2, size=(3, length)).astype(np.float32)
            # Include missing-class cases and sequence boundaries.
            y[0] = 0
            y[1] = 1
            for mode in ("prod", "max"):
                for score in ("tss", "f1"):
                    ours = torch.tensor(p, requires_grad=True)
                    theirs = torch.tensor(p, requires_grad=True)
                    labels = torch.tensor(y)
                    left = uniform_temporal_score_loss(ours, labels, mode=mode, score=score)
                    criterion = module.WeightedSOLLoss(weight_mode=mode, score=score)
                    right = torch.stack(
                        [criterion(a, b) for a, b in zip(theirs, labels, strict=True)]
                    ).mean()
                    left.backward()
                    right.backward()
                    max_value = max(max_value, abs(float(left.detach() - right.detach())))
                    max_gradient = max(max_gradient, float((ours.grad - theirs.grad).abs().max()))
                    checks += 1
        if max_value > 2e-6 or max_gradient > 2e-6:
            raise AssertionError("Reference values or gradients differ")
        return {
            "status": "passed",
            "configurations": checks,
            "max_absolute_loss_difference": max_value,
            "max_absolute_gradient_difference": max_gradient,
            "implementation_sha256": sha(path),
            "git_blob": blob,
            "scope": "per-sequence loss and gradients;not-the-paper-training-benchmark",
        }
    finally:
        sys.path.pop(0)


def defense_experiments(reference_root: Path | None = None) -> dict[str, Any]:
    torch, _ = runtime("cpu")
    original = synthetic_controls()
    events = [(50_000,)] * 6 + [(80_000,)] * 4 + [(40_000,)] * 6 + [()] * 4
    traces = [decision_trace((0, 30_000, 120_000), e, frame_only=True) for e in events]
    context = torch.tensor([0] * 10 + [1] * 10)
    y = torch.tensor(np.stack([t.timely for t in traces]), dtype=torch.float64)
    controls = {}
    for mode in ("prod", "max"):
        for score in ("tss", "f1"):
            logits = torch.zeros((2, 2), dtype=torch.float64, requires_grad=True)
            optimizer = torch.optim.Adam([logits], lr=0.1)
            for _ in range(400):
                loss = uniform_temporal_score_loss(
                    torch.sigmoid(logits[context]), y, mode=mode, score=score
                )
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            scores = [logits.detach().numpy()[int(i)] for i in context]
            chosen, _ = select_policy(traces, scores, ["synthetic"] * 20, budget=0.25)
            counts = marginal_counts(
                traces, [action_probabilities(s, chosen["bias"], chosen["family"]) for s in scores]
            )
            controls[f"wsol-{mode}-{score}"] = {
                "metrics": summary(counts),
                "selected": chosen,
                "table_logits": logits.detach().tolist(),
                "scope": (
                    "uniform-threshold author-loss adaptation to timely-window labels;"
                    "no-paper-reproduction"
                ),
            }
    # Stronger causal control: plan using the population's known event distribution.
    conditional = np.asarray([[0.6, 1.0], [0.6, 0.0]])
    plan = two_decision_plan(conditional)
    planner_counts = marginal_counts(traces, [plan[int(i)] for i in context])
    controls["bayes-decision-planner"] = {
        "metrics": summary(planner_counts),
        "context_actions": plan.tolist(),
        "scope": (
            "known-population decision-theory control;"
            "no-realized-future-event-access;not-OTI-reproduction"
        ),
    }
    # Independently enumerate score-function gradients including an exact-return baseline.
    times = np.asarray([0, 13_000, 42_000, 60_000, 79_000, 130_000])
    p = np.asarray([0.25, 0.8, 0.45, 0.6, 0.3, 0.7])
    rewards = np.asarray([-0.25, 0.5, 1.0, -0.25, 0.75, 1.0])
    exact = exact_credit(times, p, rewards)
    sampled = enumerated_score_gradient(times, p, rewards)
    gradient_difference = float(
        np.max(np.abs(exact["gradient_logits"] - sampled["gradient_logits"]))
    )
    if gradient_difference > 1e-10:
        raise AssertionError("Exact and enumerated score-function gradients differ")
    recurrence = {
        "utility": exact["utility"],
        "enumerated_utility": sampled["utility"],
        "gradient_logits": exact["gradient_logits"].tolist(),
        "max_gradient_difference": gradient_difference,
        "reinforce_single_sample_gradient_variance": sampled[
            "single_sample_gradient_variance"
        ].tolist(),
        "action_integrated_gradient_variance": [0.0] * len(p),
        "scope": (
            "fixed trace and parameters;action-sampling variance only;not-total-training-variance"
        ),
    }
    noconflict = exact_credit(np.arange(6) * 60_000, p, rewards)
    no_conflict_error = float(np.max(np.abs(noconflict["gradient_probabilities"] - rewards)))
    # A deliberately incorrect use of additive credit demonstrates the horizon restriction.
    duplicate = exact_credit(np.asarray([0, 30_000]), np.ones(2), np.ones(2), cooldown=30_000)
    return {
        "status": "adversarial-novelty-evidence;synthetic-only",
        "prior_reference": WSOL_REFERENCE,
        "author_implementation_parity": reference_parity(reference_root)
        if reference_root
        else {"status": "not-run;provide-a-local-pinned-author-checkout"},
        "original_toy": original["conflict_control"],
        "stronger_controls": controls,
        "score_only_analytic_envelope": pointwise_envelope(),
        "gradient_comparison": recurrence,
        "no_conflict_gradient_max_error": no_conflict_error,
        "invalid_short_cooldown_example": {
            "true_unique_event_count": 1,
            "additive_timely_credit": duplicate["utility"],
            "conclusion": "shorter-cooldowns-require-a-new-unique-event-credit-proof",
        },
        "conclusion": {
            "exact_credit_beats_bayes_planner": False,
            "exact_credit_beats_tested_wsol_variants_on_this_toy": False,
            "broad_first_to_learn_when_to_warn_claim": "rejected-by-prior-art",
            "new_refractory_mathematics_claim": "rejected-by-prior-art",
            "publication_novelty_established": False,
            "remaining_candidate": (
                "exact-action-marginal-training-for-repeated-warnings-with-sparse-observations"
            ),
        },
        "reproducibility": {
            "torch": str(torch.__version__),
            "numpy": np.__version__,
            "toy_optimizer": (
                "Adam;lr=.1;400-steps;zero-initialization;float64;no-random-training-draws"
            ),
            "policy_selection": "same-two-families;49-offsets-plus-off;budget=.25",
            "warning": "finite-population algebra and diagnostics;not-held-out-performance",
            "code_sha256": {
                p.name: sha(p)
                for p in [
                    Path(__file__).resolve(),
                    Path(__file__).resolve().parents[1] / "src/league_ews/policy_novelty.py",
                ]
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-directory", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/policy-novelty-defense-2026-09-30.json")
    )
    args = parser.parse_args()
    result = defense_experiments(args.reference_directory)
    write_json(args.output, result)
    for name, row in result["stronger_controls"].items():
        print(name, row["metrics"], flush=True)
    print("Analytic score-only ceiling:", result["score_only_analytic_envelope"])
    print("Author parity:", result["author_implementation_parity"])


if __name__ == "__main__":
    main()
