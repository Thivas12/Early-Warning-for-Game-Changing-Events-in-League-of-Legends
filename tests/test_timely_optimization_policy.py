"""Optimizer factorial policy alignment, paired interactions and leakage-gate checks."""

import json
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.coordination_experiment import write_json
from scripts import analyse_timely_optimization as analysis
from scripts import evaluate_timely_optimization as runner
from scripts.evaluate_dense_policy import COARSE_IDS, GRID
from scripts.warning_efficiency import BUDGETS, THRESHOLD_VALUES


@pytest.mark.parametrize("interaction", [0.0, 0.2, -0.2])
def test_factorial_uncertainty_is_paired_before_intervals(interaction):
    one = np.array(
        [[2, 1, 1, 1, 0, 2], [2, 1, 0, 2, 1, 1], [2, 2, 1, 3, 1, 2], [2, 0, 0, 1, 1, 1]],
        dtype=float,
    )
    base = np.broadcast_to(one, (4, 3, 3, 4, 6)).copy()
    counts = {
        p: {f: {h: base.copy() for h in (30, 60)} for f in runner.FAMILIES} for p in runner.POLICIES
    }
    for p in runner.POLICIES:
        for h in (30, 60):
            for f, scale in (
                ("timely_leagueews", 0.4),
                ("timely_equal_sum", 0.5),
                ("timely_original_pcgrad", 0.6),
                ("timely_equal_pcgrad", 0.7 + interaction),
            ):
                counts[p][f][h][..., 2] *= scale
    contrast = "timely_equal_sum-minus-timely_leagueews"
    results, _, _ = analysis.analyse(
        counts,
        np.array(["europe"] * 2 + ["americas"] * 2),
        [("timely_equal_sum", "timely_leagueews")],
        draws=20,
    )
    for region in results.values():
        for h in region.values():
            for policy in h.values():
                for budget in policy.values():
                    compared = budget["contrasts"]
                    for event, values in compared["projection_by_weighting_interaction"].items():
                        for metric, value in values.items():
                            reference = compared[contrast][event][metric]
                            scale = interaction / 0.1
                            assert value["mean"] == pytest.approx(scale * reference["mean"])
                            np.testing.assert_allclose(
                                value["seeds"], scale * np.array(reference["seeds"]), atol=1e-12
                            )
                            np.testing.assert_allclose(
                                value["ci95"],
                                np.sort(scale * np.array(reference["ci95"])),
                                atol=1e-12,
                            )


def test_coarse_dense_and_mixture_indices_preserve_policy_and_match_assignment():
    cal = {
        "times_ms": np.tile([0, 60000, 120000], 4),
        "match_offsets": np.arange(0, 13, 3),
        "baron_offsets": np.arange(5),
        "baron_ms": np.array([20000] * 4),
    }
    saved = {"probabilities": np.full((12, 1), 0.95)}
    regions = np.array(["europe", "americas"] * 2)
    head = {"family": "timely_equal_pcgrad", "column": 0, "event": "baron", "horizon": 30}
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


@pytest.mark.parametrize("independent_target_gain", [0.0, 0.25])
def test_target_sharing_interaction_uses_same_paired_draws(independent_target_gain):
    one = np.array(
        [[2, 1, 1, 1, 0, 2], [2, 1, 0, 2, 1, 1], [2, 2, 1, 3, 1, 2], [2, 0, 0, 1, 1, 1]],
        dtype=float,
    )
    base = np.broadcast_to(one, (4, 3, 3, 4, 6)).copy()
    counts = {
        p: {f: {h: base.copy() for h in (30, 60)} for f in runner.FAMILIES} for p in runner.POLICIES
    }
    for p in runner.POLICIES:
        for h in (30, 60):
            counts[p]["independent"][h][..., 2] *= 0.5
            counts[p]["timely_independent"][h][..., 2] *= 0.5 + independent_target_gain
    comparisons = [
        ("timely_leagueews", "timely_independent"),
        ("leagueews", "independent"),
        ("timely_independent", "independent"),
    ]
    results, _, _ = analysis.analyse(
        counts,
        np.array(["europe"] * 2 + ["americas"] * 2),
        comparisons,
        draws=20,
    )
    for region in results.values():
        for h in region.values():
            for policy in h.values():
                for b in policy.values():
                    c = b["contrasts"]
                    did = c["sharing_effect_difference_timely_minus_cumulative"]
                    if independent_target_gain == 0:
                        assert (
                            c["timely_leagueews-minus-timely_independent"]
                            == c["leagueews-minus-independent"]
                        )
                    for event, values in did.items():
                        for metric, value in values.items():
                            target = c["timely_independent-minus-independent"][event][metric]
                            assert value["mean"] == pytest.approx(-target["mean"], abs=1e-12)
                            np.testing.assert_allclose(
                                value["ci95"], [-target["ci95"][1], -target["ci95"][0]], atol=1e-12
                            )
                            np.testing.assert_allclose(
                                value["seeds"], -np.array(target["seeds"]), atol=1e-12
                            )


def test_every_early_head_is_frozen_before_later_evaluation_and_resume(tmp_path, monkeypatch):
    args = SimpleNamespace(
        output=tmp_path / "output",
        plan=tmp_path / "plan.json",
        archive=tmp_path / "unused",
        warning=tmp_path / "unused",
        reference=tmp_path / "reference",
        dense=tmp_path / "dense",
        previous=tmp_path / "previous",
        latest=tmp_path / "latest",
        sharing_policy=tmp_path / "sharing-policy",
        max_new_heads=1,
        early_only=False,
    )
    args.output.mkdir()
    write_json(
        args.plan,
        {
            "analysis_sources": [
                "scripts/evaluate_timely_optimization.py",
                "scripts/analyse_timely_optimization.py",
            ],
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
    assert runner.run(args)["status"] == "complete-exploratory-timely-optimization-policy"
    runner.run(args)
    assert evaluated == ["first", "last"]
    p = args.output / "later/first.npz"
    p.write_bytes(p.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Later artifact changed"):
        runner.run(args)


def test_independent_score_cache_validates_selected_event_columns(tmp_path):
    from scripts.timely_neural_targets import fitted_targets
    from tests.test_compact_research import sample

    cal = sample()
    event = "dragon"
    columns = slice(4, 8)
    probabilities = np.full((len(cal["targets"]), 4), 0.4)
    saved = dict(
        probabilities=probabilities,
        targets=cal["targets"][:, columns],
        fitted_targets=fitted_targets(cal)[:, columns],
        match_offsets=cal["match_offsets"],
    )
    path = tmp_path / "calibration-scores.npz"
    np.savez(path, **saved)
    head = {"folder": tmp_path, "family": "timely_independent", "event": event}
    result = runner.ScoreCache(cal).get(head)
    np.testing.assert_array_equal(result["probabilities"], probabilities)
    saved["targets"] = cal["targets"]
    np.savez(path, **saved)
    with pytest.raises(ValueError, match="Prediction alignment or range differs"):
        runner.ScoreCache(cal).get(head)


def test_all_nine_fit_bindings_and_new_event_columns_are_verified(tmp_path, monkeypatch):
    from scripts.timely_optimization_backend import VARIANTS

    args = SimpleNamespace(
        plan=tmp_path / "plan.json",
        sharing_plan=tmp_path / "prior-plan.json",
        optimization_study=tmp_path / "training",
        sharing_policy=tmp_path / "prior-policy",
    )
    write_json(args.sharing_plan, {})
    previous_heads = [
        {"key": f"{f}-{s}-{e}-{h}"}
        for f in runner.OLD_FAMILIES
        for s in runner.SEEDS
        for e in runner.EVENTS
        for h in (30, 60)
    ]
    monkeypatch.setattr(runner, "verify_controls", lambda *_: (previous_heads.copy(), {}))
    released = []
    monkeypatch.setattr(runner, "verify_scoring_release", lambda *a: released.append(a))
    prior_freeze = args.sharing_policy / "freeze.json"
    write_json(prior_freeze, {"source_sha256": {}})
    prior_binding = runner.sha(prior_freeze)
    reports = {}
    for head in previous_heads:
        key = head["key"]
        write_json(
            args.sharing_policy / "early" / f"{key}.json",
            {
                "head": key,
                "freeze_sha256": prior_binding,
            },
        )
        path = args.sharing_policy / "later" / f"{key}.npz"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"fixture")
        reports[key] = {"counts_sha256": runner.sha(path)}
    prior_policy_binding = runner.freeze_policies(
        args.sharing_policy, previous_heads, prior_binding
    )
    write_json(
        args.sharing_policy / "summary.json",
        {
            "status": "complete-exploratory-timely-sharing-policy",
            "test_payloads_opened": 0,
            "freeze_sha256": prior_binding,
            "policy_freeze_sha256": prior_policy_binding,
            "heads": reports,
        },
    )
    plan = {
        "sharing_control_plan_sha256": runner.sha(args.sharing_plan),
        "sharing_policy_summary_sha256": runner.sha(args.sharing_policy / "summary.json"),
        "analysis_sources": [],
        "variants": json.loads(json.dumps(VARIANTS)),
    }
    write_json(args.plan, plan)
    study = args.optimization_study
    write_json(study / "analysis-release.json", {})
    write_json(
        study / "freeze.json",
        {
            "plan": plan,
            "plan_sha256": runner.sha(args.plan),
            "source_sha256": {},
            "archive_sha256": runner.EXPECTED_ARCHIVE,
        },
    )
    binding = runner.sha(study / "freeze.json")
    models = {}
    for variant in runner.NEW_VARIANTS:
        for seed in runner.SEEDS:
            folder = study / variant / f"seed-{seed}"
            folder.mkdir(parents=True)
            (folder / "checkpoint.pt").write_bytes(b"fixture")
            (folder / "calibration-scores.npz").write_bytes(b"fixture")
            report = {
                "family": variant,
                "seed": seed,
                "freeze_sha256": binding,
                "variant_specification": plan["variants"][variant],
                "parameters": 1751647,
                "test_payloads_opened": 0,
                "checkpoint_sha256": runner.sha(folder / "checkpoint.pt"),
                "scores_sha256": runner.sha(folder / "calibration-scores.npz"),
            }
            write_json(folder / "report.json", report)
            write_json(folder / "progress.json", {**report, "completed_units": 576})
            models[f"{variant}/{seed}"] = report
    write_json(
        study / "summary.json",
        {
            "status": "complete-exploratory-timely-optimization-predictions",
            "freeze_sha256": binding,
            "test_payloads_opened": 0,
            "models": models,
        },
    )
    heads, _ = runner.verify_inputs(args, plan)
    assert len(heads) == 288 and len(released) == 1
    assert {h["family"] for h in heads[234:]} == set(runner.NEW_FAMILIES)
    for head in heads[234:]:
        assert head["column"] == 4 * runner.EVENTS.index(head["event"]) + (
            2 if head["horizon"] == 30 else 3
        )
    progress_path = study / "equal_sum" / f"seed-{runner.SEEDS[0]}" / "progress.json"
    progress = json.loads(progress_path.read_bytes())
    progress["variant_specification"] = plan["variants"]["original_sum"]
    write_json(progress_path, progress)
    with pytest.raises(ValueError, match="Optimization artifact differs"):
        runner.verify_inputs(args, plan)
