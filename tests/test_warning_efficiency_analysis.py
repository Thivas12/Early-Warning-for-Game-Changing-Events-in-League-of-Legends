"""Analysis checks use artificial counts, not empirical League evidence."""

from copy import deepcopy

import numpy as np
import pytest

from scripts import analyse_warning_efficiency as analysis
from scripts.analyse_neural_screen import metrics, resample_weights
from scripts.run_warning_efficiency import FAMILIES, POLICIES
from scripts.warning_efficiency import BUDGETS


def test_identical_models_paired_zero_and_fixed_budget_averaging():
    # Three copies of a fitted model do not create three independent matches.
    one = np.array(
        [[2, 1, 1, 1, 0, 2], [2, 1, 0, 2, 1, 1], [2, 2, 1, 3, 1, 2], [2, 0, 0, 1, 1, 1]],
        dtype=float,
    )
    base = np.broadcast_to(one, (3, 3, 4, 6)).copy()
    by_budget = np.stack([base.copy() for _ in BUDGETS])
    by_budget[0, ..., 1:5] = 0  # Silence at the smallest test budget.
    counts = {p: {f: {h: by_budget for h in (30, 60)} for f in FAMILIES} for p in POLICIES}
    routes = np.array(["europe", "europe", "americas", "americas"])
    result, violations = analysis.analyse(counts, routes, [("pcgrad", "leagueews")], draws=30)
    for region in result.values():
        for horizon in region.values():
            for policy in horizon.values():
                for budget in policy.values():
                    for event in budget["contrasts"]["pcgrad-minus-leagueews"].values():
                        for metric in event.values():
                            assert metric["mean"] == 0 and metric["ci95"] == [0, 0]
                            assert metric["seeds"] == [0, 0, 0]
    direct = metrics(by_budget.mean(0), resample_weights(routes, 30))[:, 0, 0, 0]
    actual = result["overall"]["30"]["matched_early_mixture"]["mean"]["models"]["pcgrad"]["baron"][
        "timely_recall"
    ]
    np.testing.assert_allclose(actual["ci95"], np.percentile(direct, [2.5, 97.5]))
    assert actual["sd"] == 0
    assert actual["mean"] == pytest.approx(one[:, 2].sum() / one[:, 0].sum() * 0.75)
    assert any(v["above_hard_one"] for v in violations)
    assert not analysis.frozen_rules(result, violations)["warning_efficiency_screen"]


def passing_result():
    metric = {"mean": 0.01, "ci95": [0.001, 0.02], "seeds": [0.02, 0.005, 0.005]}
    event = {
        "timely_recall": metric,
        "false_plus_late_per_match": {"mean": -0.02, "ci95": [-0.03, -0.01]},
    }
    contrast = {k: deepcopy(event) for k in ("baron", "dragon", "teamfight", "macro")}
    return {
        "overall": {
            "30": {
                "matched_early_mixture": {
                    str(b): {"contrasts": {"pcgrad-minus-leagueews": deepcopy(contrast)}}
                    for b in (*BUDGETS, "mean")
                }
            }
        }
    }


def test_every_prespecified_gate_is_required():
    result = passing_result()
    assert analysis.frozen_rules(result, [])["warning_efficiency_screen"]
    for name in (
        "positive_recall",
        "no_extra_burden",
        "no_mean_event_harm",
        "consistent_across_budgets",
        "regional_hard_budget",
    ):
        r, violations = deepcopy(result), []
        group = r["overall"]["30"]["matched_early_mixture"]
        primary = group["mean"]["contrasts"]["pcgrad-minus-leagueews"]
        if name == "positive_recall":
            primary["macro"]["timely_recall"]["seeds"][0] = -0.01
        elif name == "no_extra_burden":
            primary["macro"]["false_plus_late_per_match"]["ci95"][1] = 0.001
        elif name == "no_mean_event_harm":
            primary["baron"]["timely_recall"]["mean"] = -0.001
        elif name == "consistent_across_budgets":
            group["0.25"]["contrasts"]["pcgrad-minus-leagueews"]["macro"]["timely_recall"][
                "mean"
            ] = 0
        else:
            violations = [
                {
                    "family": "pcgrad",
                    "policy": "matched_early_mixture",
                    "horizon": 30,
                    "above_hard_one": True,
                }
            ]
        gates = analysis.frozen_rules(r, violations)
        assert not gates[name] and not gates["warning_efficiency_screen"]
