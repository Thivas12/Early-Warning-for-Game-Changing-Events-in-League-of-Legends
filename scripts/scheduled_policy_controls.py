"""Small, fully enumerated scientific controls; these are NOT League results."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.coordination_experiment import sha, write_json
from league_ews.scheduled_model import runtime
from league_ews.scheduled_policy import (
    action_probabilities,
    decision_trace,
    exclusion_matrix,
    marginal_counts,
    select_policy,
    summary,
    torch_marginals,
)


def synthetic_controls() -> dict[str, Any]:
    torch, _ = runtime("cpu")
    # Two equally common contexts. Both have P(timely at 0)=.6.
    # C: waiting to 30s always works; D: only the first decision can work.
    events = [(50_000,)] * 6 + [(80_000,)] * 4 + [(40_000,)] * 6 + [()] * 4
    traces = [decision_trace((0, 30_000, 120_000), e, frame_only=True) for e in events]
    # decision_trace has two actual observed action opportunities, at 0 and 30.
    contexts = torch.tensor([0] * 10 + [1] * 10)
    targets = torch.tensor(np.stack([t.timely for t in traces]), dtype=torch.float64)
    block = exclusion_matrix(
        torch.tensor(np.stack([t.times for t in traces])),
        torch.ones_like(targets, dtype=torch.bool),
    )
    outputs = {}
    for coupled in (False, True):
        logits = torch.zeros((2, 2), dtype=torch.float64, requires_grad=True)
        optimizer = torch.optim.Adam([logits], lr=0.1)
        for _ in range(400):
            p = torch.sigmoid(logits[contexts])
            m = torch_marginals(p, block) if coupled else p
            loss = -(m * (targets - 0.25 * (1 - targets))).sum(1).mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        outputs["exact_credit" if coupled else "ignore_cooldown"] = logits.detach().numpy()
    # Bayes-optimal per-decision classifier: no classifier-estimation disadvantage.
    bayes = np.array([[0.6, 1 - 1e-9], [0.6, 1e-9]])
    outputs["oracle_pointwise_bce"] = np.log(bayes / (1 - bayes))
    results = {}
    for name, table in outputs.items():
        scores = [table[int(i)] for i in contexts]
        selected, _ = select_policy(traces, scores, ["synthetic"] * 20, budget=0.25)
        counts = marginal_counts(
            traces, [action_probabilities(s, selected["bias"], selected["family"]) for s in scores]
        )
        results[name] = {
            "counts": summary(counts),
            "policy": selected,
            "context_logits": table.tolist(),
        }
    # With p fixed, zero cooldown makes exact and independent credit identical.
    p = torch.tensor([[0.3, 0.7]], dtype=torch.float64)
    no_block = exclusion_matrix(torch.tensor([[0, 60_000]]), torch.ones((1, 2), dtype=torch.bool))
    no_conflict_error = float((torch_marginals(p, no_block) - p).abs().max())
    # No outcomes or clock tick proliferation can manufacture predictable signal.
    # Exchangeable contexts/slots with independent q=.2 outcomes have expected
    # timely hits=.2*alarms and wrong=.8*alarms for EVERY causal policy.
    null_q, budget = 0.2, 0.25
    return {
        "status": "synthetic-mechanism-check-not-real-data-evidence",
        "provenance": {
            "torch": str(torch.__version__),
            "numpy": np.__version__,
            "dtype": "float64",
            "optimizer": "Adam;lr=.1;400-steps;zero-initial-logits;no-random-draws",
            "training_wrong_cost": 0.25,
            "selection_wrong_budget": 0.25,
            "code_sha256": {
                str(path.relative_to(Path(__file__).resolve().parents[1])): sha(path)
                for path in (
                    Path(__file__).resolve(),
                    Path(__file__).resolve().parents[1] / "src/league_ews/scheduled_policy.py",
                )
            },
        },
        "design": "20 enumerated outcomes;2 observed decision times;known outcome probabilities",
        "selection_scope": "population illustration only; no generalization claim",
        "conflict_control": results,
        "no_conflict_max_difference": no_conflict_error,
        "exchangeable_null": {
            "event_probability": null_q,
            "wrong_budget": budget,
            "upper_bound_expected_timely_hits_per_episode": budget * null_q / (1 - null_q),
            "meaning": "all causal methods share the bound for information-independent labels",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/scheduled-policy-synthetic-controls-2026-09-30.json"),
    )
    args = parser.parse_args()
    result = synthetic_controls()
    write_json(args.output, result)
    for name, row in result["conflict_control"].items():
        print(name, row["counts"], flush=True)


if __name__ == "__main__":
    main()
