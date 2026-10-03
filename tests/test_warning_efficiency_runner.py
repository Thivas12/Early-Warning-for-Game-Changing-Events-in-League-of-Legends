"""Gate and checkpoint implementation fixtures; no empirical League conclusions."""

import json
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.coordination_experiment import write_json
from scripts import run_warning_efficiency as runner


def test_all_head_gate_resume_and_tamper_rejection(tmp_path, monkeypatch):
    plan = {
        "families": list(runner.FAMILIES),
        "budgets": list(runner.BUDGETS),
        "seeds": list(runner.SEEDS),
        "thresholds": list(runner.THRESHOLD_VALUES),
    }
    plan_path = tmp_path / "plan.json"
    write_json(plan_path, plan)
    output = tmp_path / "output"
    output.mkdir()
    args = SimpleNamespace(
        plan=plan_path,
        output=output,
        archive=tmp_path / "unused",
        max_new_heads=1,
        early_only=False,
    )
    heads = [{"key": k, "column": 0} for k in ("first", "last")]
    monkeypatch.setattr(runner, "inputs", lambda *_: (heads, {}))
    monkeypatch.setattr(runner, "calibration_routes", lambda *_: None)
    rows = [{"regional_route": "europe" if i % 2 else "americas"} for i in range(6000)]
    monkeypatch.setattr(runner, "load_partition", lambda *_: ({}, rows))
    monkeypatch.setattr(
        runner, "_chronological_halves", lambda _: (list(range(3000)), list(range(3000, 6000)))
    )
    monkeypatch.setattr(runner.ScoreCache, "get", lambda *_: {"probabilities": np.zeros((1, 1))})
    selected, evaluated = [], []

    def select(cal, p, head, early, regions, binding):
        selected.append(head["key"])
        assert len(early) == 3000
        return {"head": head["key"], "freeze_sha256": binding}

    def evaluate(cal, saved, head, selection, later, regions):
        assert selected == ["first", "last"]
        assert (output / "policy-freeze.json").exists()
        assert len(later) == 3000
        evaluated.append(head["key"])
        return {p: np.zeros((4, 3000, 6)) for p in runner.POLICIES}, 3

    monkeypatch.setattr(runner, "select_head", select)
    monkeypatch.setattr(runner, "evaluate_head", evaluate)
    assert runner.run(args)["status"] == "paused-after-early-selection"
    assert not evaluated and not (output / "policy-freeze.json").exists()
    with pytest.raises(ValueError, match="every early policy"):
        runner.freeze_policies(output, heads, runner.sha(output / "freeze.json"))
    args.max_new_heads, args.early_only = 0, True
    assert runner.run(args)["status"] == "all-early-policies-frozen"
    assert not evaluated
    args.early_only = False
    assert runner.run(args)["status"] == "complete-exploratory-warning-efficiency"
    assert evaluated == ["first", "last"]
    runner.run(args)
    assert evaluated == ["first", "last"]  # No duplicate evaluation on valid resume.
    p = output / "later" / "first.npz"
    p.write_bytes(p.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Later artifact changed"):
        runner.run(args)
    early_path = output / "early" / "first.json"
    data = json.loads(early_path.read_text())
    data["changed"] = True
    write_json(early_path, data)
    with pytest.raises(ValueError, match="Selected policy changed"):
        runner.run(args)


def test_score_cache_decodes_once_and_checks_alignment(tmp_path, monkeypatch):
    p = np.full((4, 12), 0.5)
    cal = {"match_offsets": np.array([0, 2, 4]), "targets": np.zeros((4, 12))}
    np.savez(tmp_path / "calibration-scores.npz", probabilities=p, **cal)
    actual_load = np.load
    calls = []

    def load(*args, **kwargs):
        calls.append(args[0])
        return actual_load(*args, **kwargs)

    monkeypatch.setattr(runner.np, "load", load)
    cache = runner.ScoreCache(cal)
    head = {"folder": tmp_path, "family": "leagueews", "event": "baron"}
    first = cache.get(head)
    assert cache.get({**head, "event": "dragon"}) is first
    assert len(calls) == 1
    with pytest.raises(ValueError, match="alignment"):
        runner.ScoreCache({**cal, "targets": np.ones((4, 12))}).get(head)


def test_later_mixtures_are_whole_match_expectations():
    times = np.tile([0, 60000, 120000], 4)
    cal = {
        "times_ms": times,
        "match_offsets": np.arange(0, 13, 3),
        "baron_offsets": np.arange(0, 5),
        "baron_ms": np.array([20000] * 4),
    }
    probabilities = np.full((12, 1), 0.9, dtype=np.float32)
    ids = [0, 2]  # Silence and 0.89125; two full-match policies.
    regions = np.array(["europe", "americas", "europe", "americas"])
    counts = runner.replay_calibration(
        cal,
        probabilities[:, 0],
        "baron",
        range(4),
        30,
        tuple(runner.THRESHOLD_VALUES[i] for i in ids),
    )
    selected = {
        "policies": {
            "deterministic": {str(b): 2 for b in runner.BUDGETS},
            "matched_early_mixture": {
                str(b): {r: {"indices": ids, "weights": [1 - b, b]} for r in runner.REGIONS}
                for b in runner.BUDGETS
            },
        }
    }
    saved = {"probabilities": probabilities, "counts_baron_30": counts[:, 1]}
    actual, checks = runner.evaluate_head(
        cal,
        saved,
        {"column": 0, "event": "baron", "horizon": 30},
        selected,
        list(range(4)),
        regions,
    )
    assert checks == 62
    for n, b in enumerate(runner.BUDGETS):
        np.testing.assert_allclose(
            actual["matched_early_mixture"][n], (1 - b) * counts[:, 0] + b * counts[:, 1]
        )
    saved["counts_baron_30"] = np.zeros((4, 6))
    with pytest.raises(ValueError, match="Original later counts changed"):
        runner.evaluate_head(
            cal,
            saved,
            {"column": 0, "event": "baron", "horizon": 30},
            selected,
            list(range(4)),
            regions,
        )
