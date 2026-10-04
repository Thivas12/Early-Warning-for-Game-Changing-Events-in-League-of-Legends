"""Policy-gate and paired-analysis fixtures, not empirical League evidence."""

from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.coordination_experiment import write_json
from scripts import analyse_timely_neural as analysis
from scripts import evaluate_timely_neural as runner
from scripts.analyse_neural_screen import metrics, resample_weights
from scripts.warning_efficiency import BUDGETS, THRESHOLD_VALUES


def test_regional_deterministic_control_is_distinct_and_budget_feasible(monkeypatch):
    counts = np.zeros((3000, len(THRESHOLD_VALUES), 6), dtype=np.int64)
    for row in (0, 1500):
        counts[row, :, 0] = 5000
    counts[0, 1, 1:5] = [1000, 1000, 1250, 250]
    counts[1500, 1, 1:5] = [500, 500, 2250, 1750]
    for row in (0, 1500):
        counts[row, 2, 1:5] = [600, 600, 1100, 500]
        counts[row, 3, 3:5] = 3000
    monkeypatch.setattr(runner, "replay_calibration", lambda *_: counts)
    regions = np.array(["europe"] * 1500 + ["americas"] * 1500)
    selected = runner.select_head(
        {},
        [],
        {"family": "timely_tcn", "key": "fixture", "event": "baron", "horizon": 30},
        list(range(3000)),
        regions,
        "frozen",
    )
    p = selected["policies"]
    assert p["deterministic"]["1.0"] == 2
    assert p["regional_deterministic"]["1.0"] == {"europe": 1, "americas": 2}
    for budget in BUDGETS:
        for i, region in enumerate(runner.REGIONS):
            n = p["regional_deterministic"][str(budget)][region]
            total = np.asarray(selected["early_threshold_counts_by_region"])[i, n]
            assert (total[3] - total[2]) / 1500 <= budget
            assert p["matched_early_mixture"][str(budget)][region]["early_burden"] == pytest.approx(
                budget
            )


def test_regional_evaluation_preserves_match_assignment_and_credit():
    cal = {
        "times_ms": np.tile([0, 60000, 120000], 4),
        "match_offsets": np.arange(0, 13, 3),
        "baron_offsets": np.arange(5),
        "baron_ms": np.array([20000] * 4),
    }
    saved = {"probabilities": np.full((12, 1), 0.9, dtype=np.float32)}
    regions = np.array(["europe", "americas", "europe", "americas"])
    head = {"family": "timely_tcn", "column": 0, "event": "baron", "horizon": 30}
    policies = {
        "deterministic": {str(b): 2 for b in BUDGETS},
        "regional_deterministic": {str(b): {"europe": 2, "americas": 0} for b in BUDGETS},
        "matched_early_mixture": {
            str(b): {r: {"indices": [0, 2], "weights": [1 - b, b]} for r in runner.REGIONS}
            for b in BUDGETS
        },
    }
    actual, checks, full = runner.evaluate_head(
        cal, saved, head, {"policies": policies}, list(range(4)), regions
    )
    assert checks == 8 and full == 4
    np.testing.assert_array_equal(
        actual["regional_deterministic"][:, regions == "europe"],
        actual["deterministic"][:, regions == "europe"],
    )
    assert np.all(actual["regional_deterministic"][:, regions == "americas", 1:5] == 0)
    for i, b in enumerate(BUDGETS):
        np.testing.assert_allclose(
            actual["matched_early_mixture"][i, :, 1:5], b * actual["deterministic"][i, :, 1:5]
        )
        np.testing.assert_array_equal(
            actual["matched_early_mixture"][i, :, 0], actual["deterministic"][i, :, 0]
        )


def test_every_early_head_is_frozen_before_later_evaluation_and_resume(tmp_path, monkeypatch):
    args = SimpleNamespace(
        output=tmp_path / "output",
        plan=tmp_path / "plan.json",
        archive=tmp_path / "unused",
        warning=tmp_path / "unused",
        max_new_heads=1,
        early_only=False,
    )
    args.output.mkdir()
    write_json(
        args.plan,
        {
            "evaluation_families": list(runner.FAMILIES),
            "policies": list(runner.POLICIES),
            "budgets": list(BUDGETS),
            "thresholds": list(THRESHOLD_VALUES),
        },
    )
    heads = [{"key": k, "column": 0, "family": "timely_tcn"} for k in ("first", "last")]
    monkeypatch.setattr(runner, "verify_inputs", lambda *_: (heads, {}))
    monkeypatch.setattr(runner, "calibration_routes", lambda *_: None)
    rows = [{"regional_route": "europe" if i % 2 else "americas"} for i in range(6000)]
    monkeypatch.setattr(runner, "load_partition", lambda *_: ({}, rows))
    monkeypatch.setattr(
        runner, "_chronological_halves", lambda _: (list(range(3000)), list(range(3000, 6000)))
    )
    target = np.zeros((1, 1))
    monkeypatch.setattr(runner, "fitted_targets", lambda _: target)
    monkeypatch.setattr(
        runner.ScoreCache, "get", lambda *_: {"probabilities": target, "fitted_targets": target}
    )
    selected = []
    evaluated = []

    def select(cal, p, head, early, regions, binding):
        selected.append(head["key"])
        return {"head": head["key"], "freeze_sha256": binding}

    def evaluate(cal, saved, head, selection, later, regions, reference):
        assert selected == ["first", "last"] and (args.output / "policy-freeze.json").exists()
        evaluated.append(head["key"])
        return {p: np.zeros((4, 3000, 6)) for p in runner.POLICIES}, 0, 3000

    monkeypatch.setattr(runner, "select_head", select)
    monkeypatch.setattr(runner, "evaluate_head", evaluate)
    assert runner.run(args)["status"] == "paused-after-early-selection"
    assert not evaluated and not (args.output / "policy-freeze.json").exists()
    args.max_new_heads = 0
    args.early_only = True
    assert runner.run(args)["status"] == "all-early-policies-frozen"
    assert not evaluated
    args.early_only = False
    assert runner.run(args)["status"] == "complete-exploratory-timely-policy"
    runner.run(args)
    assert evaluated == ["first", "last"]
    p = args.output / "later/first.npz"
    p.write_bytes(p.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Later artifact changed"):
        runner.run(args)


def test_differences_in_differences_and_policy_effects_are_paired():
    one = np.array(
        [[2, 1, 1, 1, 0, 2], [2, 1, 0, 2, 1, 1], [2, 2, 1, 3, 1, 2], [2, 0, 0, 1, 1, 1]],
        dtype=float,
    )
    base = np.broadcast_to(one, (4, 3, 3, 4, 6)).copy()
    counts = {
        p: {f: {h: base.copy() for h in (30, 60)} for f in runner.FAMILIES} for p in runner.POLICIES
    }
    # Identical target effects in the two families, so DID must be identically zero.
    for p in runner.POLICIES:
        for f in ("timely_leagueews", "timely_tcn"):
            for h in (30, 60):
                counts[p][f][h][..., 2] *= 0.5
    routes = np.array(["europe", "europe", "americas", "americas"])
    result, _, effects = analysis.analyse(
        counts,
        routes,
        [("timely_leagueews", "leagueews"), ("timely_leagueews", "timely_tcn")],
        draws=30,
    )
    for region in result.values():
        for horizon in region.values():
            for policy in horizon.values():
                for budget in policy.values():
                    for event in budget["contrasts"][
                        "target_effect_difference_leagueews_minus_tcn"
                    ].values():
                        for value in event.values():
                            assert value["mean"] == 0 and value["ci95"] == [0, 0]
    v = effects["overall"]["30"]["mean"]["timely_leagueews"][
        "regional_deterministic-minus-deterministic"
    ]["macro"]["timely_recall"]
    assert v["mean"] == 0 and v["ci95"] == [0, 0]
    direct = metrics(
        counts["deterministic"]["timely_leagueews"][30].mean(0), resample_weights(routes, 30)
    )[:, 0, 0, 0]
    v = result["overall"]["30"]["deterministic"]["mean"]["models"]["timely_leagueews"]["baron"][
        "timely_recall"
    ]
    np.testing.assert_allclose(v["ci95"], np.percentile(direct, [2.5, 97.5]))
    assert v["sd"] == 0


def test_each_frozen_gate_is_required():
    metric = {"mean": 0.01, "ci95": [0.001, 0.02], "seeds": [0.01, 0.02, 0.0_01]}
    event = {
        "timely_recall": metric,
        "false_plus_late_per_match": {"mean": -0.02, "ci95": [-0.03, -0.01]},
    }
    base = {e: deepcopy(event) for e in (*runner.EVENTS, "macro")}
    groups = {
        "timely_leagueews-minus-leagueews": deepcopy(base),
        "timely_leagueews-minus-timely_tcn": deepcopy(base),
    }
    result = {"overall": {"30": {"matched_early_mixture": {"mean": {"contrasts": groups}}}}}
    assert analysis.frozen_rules(result, [])["practical_promotion"]
    for name in (
        "objective_alignment_effect",
        "no_mean_event_harm",
        "no_extra_burden",
        "strong_control_gain",
        "regional_hard_budget",
    ):
        r = deepcopy(result)
        v = []
        g = r["overall"]["30"]["matched_early_mixture"]["mean"]["contrasts"]
        p = g["timely_leagueews-minus-leagueews"]
        if name == "objective_alignment_effect":
            p["macro"]["timely_recall"]["seeds"][0] = -1
        elif name == "no_mean_event_harm":
            p["baron"]["timely_recall"]["mean"] = -1
        elif name == "no_extra_burden":
            p["macro"]["false_plus_late_per_match"]["ci95"][1] = 0.001
        elif name == "strong_control_gain":
            g["timely_leagueews-minus-timely_tcn"]["macro"]["timely_recall"]["ci95"][0] = -0.001
        else:
            v = [
                {
                    "family": "timely_tcn",
                    "policy": "matched_early_mixture",
                    "horizon": 30,
                    "above_hard_one": True,
                }
            ]
        gates = analysis.frozen_rules(r, v)
        assert not gates[name] and not gates["practical_promotion"]
