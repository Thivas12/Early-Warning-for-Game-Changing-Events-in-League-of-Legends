"""Threshold-resolution and global-gate checks; fixtures are not research evidence."""

from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.coordination_experiment import sha, write_json
from scripts import analyse_dense_policy as analysis
from scripts import evaluate_dense_policy as runner
from scripts.warning_efficiency import BUDGETS, THRESHOLD_VALUES, select_deterministic


def test_nested_grid_and_selector_match_independent_budget_search():
    assert len(runner.GRID) == 1002
    assert tuple(runner.GRID[i] for i in runner.COARSE_IDS) == THRESHOLD_VALUES
    assert np.all(np.diff(runner.GRID[1:]) < 0)
    counts = np.zeros((2, len(runner.GRID), 6), dtype=int)
    rng = np.random.default_rng(711)
    counts[:, 1:, 2] = rng.integers(0, 300, (2, 1001))
    counts[:, 1:, 3] = counts[:, 1:, 2] + rng.integers(0, 2000, (2, 1001))
    for budget in BUDGETS:
        feasible = [
            i
            for i in range(len(runner.GRID))
            if all((counts[r, i, 3] - counts[r, i, 2]) / 1500 <= budget for r in (0, 1))
        ]
        reference = sorted(
            feasible,
            key=lambda i: (-counts[:, i, 2].sum(), (counts[:, i, 3] - counts[:, i, 2]).sum(), i),
        )[0]
        assert runner.select(counts, [1500, 1500], budget) == reference
        coarse = select_deterministic(counts[:, runner.COARSE_IDS], [1500, 1500], budget)
        assert counts[:, reference, 2].sum() >= counts[:, runner.COARSE_IDS[coarse], 2].sum()
    # Equal reward/cost keeps the higher threshold; silence wins an all-zero tie.
    assert runner.select(np.zeros_like(counts), [1500, 1500], 1) == 0
    counts.fill(0)
    counts[:, [3, 4], 2:4] = 5
    assert runner.select(counts, [1500, 1500], 1) == 3


def test_dense_evaluation_checks_every_match_and_preserves_regions():
    cal = {
        "times_ms": np.tile([0, 60000, 120000], 4),
        "match_offsets": np.arange(0, 13, 3),
        "baron_offsets": np.arange(5),
        "baron_ms": np.array([20000] * 4),
    }
    scores = np.full(12, 0.95)
    regions = np.array(["europe", "americas"] * 2)
    selected = {
        "policies": {
            "dense_deterministic": {str(b): 2 for b in BUDGETS},
            "dense_regional_deterministic": {str(b): {"europe": 2, "americas": 0} for b in BUDGETS},
        }
    }
    values, checks = runner.evaluate_head(
        cal, scores, {"event": "baron", "horizon": 30}, selected, list(range(4)), regions
    )
    assert checks == 8
    np.testing.assert_array_equal(
        values[runner.NEW_POLICIES[0]][:, ::2], values[runner.NEW_POLICIES[1]][:, ::2]
    )
    assert np.all(values[runner.NEW_POLICIES[1]][:, 1::2, 1:5] == 0)


def test_pairing_keeps_zero_policy_target_interaction():
    base = np.broadcast_to(
        np.array([[2, 1, 1, 1, 0, 2], [2, 1, 0, 2, 1, 1], [2, 2, 1, 3, 1, 2], [2, 0, 0, 1, 1, 1]]),
        (4, 3, 3, 4, 6),
    ).copy()
    counts = {
        p: {f: {h: base.copy() for h in (30, 60)} for f in runner.FAMILIES} for p in runner.POLICIES
    }
    result, _, effects = analysis.analyse(
        counts,
        np.array(["europe"] * 2 + ["americas"] * 2),
        [("timely_leagueews", "leagueews")],
        draws=20,
    )
    for region in result.values():
        for h in region.values():
            for p in h.values():
                assert p["1.0"]["contrasts"]["timely_leagueews-minus-leagueews"]["macro"][
                    "timely_recall"
                ]["ci95"] == [0, 0]
    for region in effects.values():
        for h in region.values():
            for b in h.values():
                for name in ("target_interaction_leagueews", "target_interaction_tcn"):
                    for e in b[name].values():
                        for metrics in e.values():
                            for v in metrics.values():
                                assert v["mean"] == 0 and v["ci95"] == [0, 0]


def test_all_early_heads_gate_resume_and_tamper(tmp_path, monkeypatch):
    args = SimpleNamespace(
        output=tmp_path / "output",
        reference=tmp_path / "reference",
        plan=tmp_path / "plan.json",
        control_plan=tmp_path / "control.json",
        archive=tmp_path / "unused",
        early_only=True,
    )
    args.output.mkdir()
    args.reference.mkdir()
    write_json(args.control_plan, {})
    write_json(args.reference / "freeze.json", {"source_sha256": {}})
    binding = sha(args.reference / "freeze.json")
    gate = runner.freeze_policies(args.reference, [], binding)
    write_json(
        args.reference / "summary.json",
        {
            "status": "complete-exploratory-timely-policy",
            "freeze_sha256": binding,
            "policy_freeze_sha256": gate,
            "heads": {},
        },
    )
    write_json(
        args.plan,
        {
            "families": list(runner.FAMILIES),
            "thresholds": list(runner.GRID),
            "budgets": list(BUDGETS),
            "policies": list(runner.POLICIES),
            "control_plan_sha256": sha(args.control_plan),
            "reference_summary_sha256": sha(args.reference / "summary.json"),
        },
    )
    heads = [{"key": str(i), "family": "leagueews", "column": 0} for i in range(72)]
    for h in heads:
        write_json(args.reference / "early" / f"{h['key']}.json", {})
    monkeypatch.setattr(runner, "verify_inputs", lambda *_: (heads, {}))
    monkeypatch.setattr(runner, "calibration_routes", lambda *_: None)
    rows = [{"regional_route": "europe" if i % 2 else "americas"} for i in range(6000)]
    monkeypatch.setattr(runner, "load_partition", lambda *_: ({}, rows))
    monkeypatch.setattr(
        runner, "_chronological_halves", lambda *_: (list(range(3000)), list(range(3000, 6000)))
    )
    monkeypatch.setattr(runner.ScoreCache, "get", lambda *_: {"probabilities": np.zeros((1, 1))})
    selected = []
    evaluated = []

    def select(cal, scores, head, early, regions, binding, prior):
        selected.append(head["key"])
        return {"head": head["key"], "freeze_sha256": binding}

    def evaluate(cal, scores, head, selection, later, regions):
        assert len(selected) == 72 and (args.output / "policy-freeze.json").exists()
        evaluated.append(head["key"])
        return {p: np.zeros((4, 3000, 6), dtype=int) for p in runner.NEW_POLICIES}, 3000

    monkeypatch.setattr(runner, "select_head", select)
    monkeypatch.setattr(runner, "evaluate_head", evaluate)
    assert runner.run(args)["status"] == "all-72-early-heads-frozen"
    assert not evaluated
    args.early_only = False
    assert runner.run(args)["status"] == "complete-exploratory-dense-policy"
    runner.run(args)
    assert len(selected) == len(evaluated) == 72
    p = args.output / "later/0.npz"
    p.write_bytes(p.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Later artifact differs"):
        runner.run(args)
