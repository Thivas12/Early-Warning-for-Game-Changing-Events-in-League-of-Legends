"""Conditional history policy mapping, decomposition and leakage-gate checks."""

from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.coordination_experiment import write_json
from scripts import analyse_clock_history as analysis
from scripts import evaluate_clock_history as runner
from scripts.evaluate_dense_policy import COARSE_IDS, GRID
from scripts.warning_efficiency import BUDGETS, THRESHOLD_VALUES


def test_coarse_dense_and_mixture_indices_preserve_policy_and_match_assignment():
    cal = {
        "times_ms": np.tile([0, 60000, 120000], 4),
        "match_offsets": np.arange(0, 13, 3),
        "baron_offsets": np.arange(5),
        "baron_ms": np.array([20000] * 4),
    }
    saved = {"probabilities": np.full((12, 1), 0.95)}
    regions = np.array(["europe", "americas"] * 2)
    head = {"family": "timely_clock_history", "column": 0, "event": "baron", "horizon": 30}
    policies = {
        "deterministic": {str(b): 2 for b in BUDGETS},
        "regional_deterministic": {str(b): {"europe": 2, "americas": 0} for b in BUDGETS},
        "matched_early_mixture": {
            str(b): {r: {"indices": [0, 2], "weights": [1 - b, b]} for r in runner.REGIONS}
            for b in BUDGETS
        },
        "dense_deterministic": {str(b): 3 for b in BUDGETS},
        "dense_regional_deterministic": {
            str(b): {"europe": COARSE_IDS[2], "americas": 3} for b in BUDGETS
        },
    }
    out, checks, full = runner.evaluate_head(
        cal, saved, head, {"policies": policies}, list(range(4)), regions
    )
    assert checks == 12 and full == 8
    assert np.all(out["dense_deterministic"][..., 1:5] == 0)
    np.testing.assert_array_equal(
        out["dense_regional_deterministic"], out["regional_deterministic"]
    )
    for i, b in enumerate(BUDGETS):
        np.testing.assert_allclose(
            out["matched_early_mixture"][i, :, 1:5], b * out["deterministic"][i, :, 1:5]
        )
    old = {p: out[p].copy() for p in runner.OLD_POLICIES}
    dense = {p: out[p].copy() for p in runner.NEW_POLICIES}
    runner.evaluate_head(
        cal, saved, head, {"policies": policies}, list(range(4)), regions, old, dense
    )
    previous = {p: out[p].copy() for p in runner.POLICIES}
    runner.evaluate_head(
        cal, saved, head, {"policies": policies}, list(range(4)), regions, old, dense, previous
    )
    previous["matched_early_mixture"][0, 0, 2] = 99
    with pytest.raises(ValueError, match="Previous match counts differ"):
        runner.evaluate_head(
            cal, saved, head, {"policies": policies}, list(range(4)), regions, old, dense, previous
        )
    dense["dense_deterministic"][0, 0, 2] = 99
    with pytest.raises(ValueError, match="Previous match counts differ"):
        runner.evaluate_head(
            cal, saved, head, {"policies": policies}, list(range(4)), regions, old, dense
        )


def test_conditional_history_uses_paired_draws_and_timer_component_recovers_total():
    one = np.array(
        [[2, 1, 1, 1, 0, 2], [2, 1, 0, 2, 1, 1], [2, 2, 1, 3, 1, 2], [2, 0, 0, 1, 1, 1]],
        dtype=float,
    )
    base = np.broadcast_to(one, (4, 3, 3, 4, 6)).copy()
    counts = {
        p: {f: {h: base.copy() for h in (30, 60)} for f in runner.FAMILIES} for p in runner.POLICIES
    }
    # Full and timer-history are identical; removing all history hurts.
    for p in runner.POLICIES:
        for h in (30, 60):
            counts[p]["timely_current_only"][h][..., 2] *= 0.5
    conditional = "timely_leagueews-minus-timely_clock_history"
    timer = "timely_clock_history-minus-timely_current_only"
    total = "timely_leagueews-minus-timely_current_only"
    results, _, _ = analysis.analyse(
        counts,
        np.array(["europe"] * 2 + ["americas"] * 2),
        [tuple(v.split("-minus-")) for v in (conditional, timer, total)],
        draws=20,
    )
    for region in results.values():
        for h in region.values():
            for policy in h.values():
                for b in policy.values():
                    contrasts = b["contrasts"]
                    for event in contrasts[conditional].values():
                        for value in event.values():
                            assert value["mean"] == 0 and value["ci95"] == [0, 0]
                    assert contrasts[timer] == contrasts[total]
                    assert contrasts[total]["macro"]["timely_recall"]["mean"] > 0
                    assert contrasts[total]["macro"]["timely_recall"]["ci95"][0] >= 0


def test_every_early_head_is_frozen_before_later_evaluation_and_resume(tmp_path, monkeypatch):
    args = SimpleNamespace(
        output=tmp_path / "output",
        plan=tmp_path / "plan.json",
        archive=tmp_path / "unused",
        warning=tmp_path / "unused",
        reference=tmp_path / "reference",
        dense=tmp_path / "dense",
        previous=tmp_path / "previous",
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
            "dense_thresholds": list(GRID),
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

    def select(cal, p, head, early, regions, binding, prior, dense, previous):
        selected.append(head["key"])
        return {"head": head["key"], "freeze_sha256": binding}

    def evaluate(cal, saved, head, selection, later, regions, reference, dense_reference, previous):
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
    assert runner.run(args)["status"] == "complete-exploratory-clock-history-policy"
    runner.run(args)
    assert evaluated == ["first", "last"]
    p = args.output / "later/first.npz"
    p.write_bytes(p.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Later artifact changed"):
        runner.run(args)
