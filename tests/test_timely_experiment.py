"""Scientific boundary, matched-comparison, cache-integrity and recovery checks."""

from __future__ import annotations

import copy
import sys

import numpy as np
import pytest
from sklearn.metrics import average_precision_score
from threadpoolctl import threadpool_limits

from league_ews.alert_policy import MatchRisk
from league_ews.coordination_experiment import sha, write_json
from league_ews.coordination_features import FEATURE_NAMES, VARIANT_WIDTHS
from league_ews.timely_experiment import (
    MODELS,
    evaluate,
    fit_predict,
    freeze,
    load_partition,
    run,
)
from league_ews.timely_policy import compare_counts, interval_targets, select_policies, summarize
from scripts.render_coordination_results import render


def arrays(n=24):
    times = [(0, 60_000, 120_000, 180_000)] * n
    events = [(30_000,) if i % 3 == 0 else (10_000,) if i % 3 == 1 else () for i in range(n)]
    x = np.zeros((n * 4, len(FEATURE_NAMES)), dtype=np.float32)
    # Both event classes look equally impending on one feature; another separates timing.
    for i in range(n):
        x[4 * i, 0] = i % 3 != 2
        x[4 * i, 1] = i % 3 == 0
    targets = [interval_targets(t, e) for t, e in zip(times, events, strict=True)]
    return {
        "x": x,
        "times": times,
        "events": events,
        "offsets": np.arange(n + 1) * 4,
        "targets": {k: np.concatenate([v[k] for v in targets]) for k in targets[0]},
    }


def test_target_boundaries_and_completed_match_negatives():
    result = interval_targets((39_999, 40_000, 80_000, 80_001, 100_000, 120_000), (100_000,))
    assert result["within60"].tolist() == [0, 1, 1, 1, 0, 0]
    assert result["timely20_60"].tolist() == [0, 1, 1, 0, 0, 0]
    assert result["late0_20"].tolist() == [0, 0, 0, 1, 0, 0]
    np.testing.assert_array_equal(result["within60"], result["timely20_60"] + result["late0_20"])
    assert interval_targets((0, 10_000), ())["within60"].tolist() == [0, 0]
    # Never skip a late next event to label a more distant event timely.
    assert interval_targets((0, 60_000), (10_000, 40_000))["timely20_60"].tolist() == [0, 0]
    for t, e in (((1, 1), ()), ((0, 1), (2,)), ((0, 2), (1, 1)), ((-1, 0), ())):
        with pytest.raises(ValueError, match="timestamps"):
            interval_targets(t, e)


def test_late_alert_budget_and_disabled_policy_are_explicit():
    match = MatchRisk((0, 60_000, 120_000, 180_000), (30_000, 70_000, 130_000, 210_000), (0.9,) * 4)
    selected, _ = select_policies([match])
    assert selected["false"]["timely_matched_events"] == 2
    assert selected["false"]["late_alerts_per_game"] == 2
    assert selected["non_timely"]["threshold"] is None
    result, counts = summarize([match], 0.5)
    assert result["non_timely_alerts"] == 2
    assert result["non_timely_alerts_per_game_quantiles"]["95"] == 2
    identical = compare_counts(counts, counts, ["europe"])
    assert identical["non_timely_alerts_per_game_difference"] == 0
    assert identical["percentile_95_intervals"]["non_timely_alerts_per_game_difference"] == [0, 0]
    with pytest.raises(ValueError, match="Budget"):
        select_policies([match], -1)


def test_evaluation_outcomes_do_not_select_threshold_and_route_slices_reconcile():
    data = arrays(12)
    scores = np.where(data["targets"]["within60"], 0.8, 0.1)
    early, later = list(range(6)), list(range(6, 12))
    routes = ["europe", "americas"] * 6
    first, _ = evaluate(data, scores, early, later, routes, "within60")
    changed = copy.deepcopy(data)
    changed["events"][6:] = [()] * 6
    for value in changed["targets"].values():
        value[24:] = 0
    second, _ = evaluate(changed, scores, early, later, routes, "within60")
    for budget in ("false", "non_timely"):
        p = first["policies"][budget]
        assert p["threshold"] == second["policies"][budget]["threshold"]
        assert (
            sum(v["alerts"] for v in p["evaluation_by_route"].values()) == p["evaluation"]["alerts"]
        )
    with pytest.raises(ValueError, match="Invalid"):
        evaluate(data, scores, early, early, routes, "within60")
    with pytest.raises(ValueError, match="Invalid"):
        evaluate(data, scores * np.nan, early, later, routes, "within60")


def test_common_capacity_metric_and_synthetic_timing_signal():
    train, calibration = arrays(120), arrays(60)
    development = np.repeat(np.arange(120) >= 90, 4)
    with threadpool_limits(limits=1):
        results = {}
        for objective in ("within60", "timely20_60"):
            model, scores, candidates = fit_predict(
                train,
                calibration,
                development,
                "history",
                objective,
                leaf_grid=(3, 7),
                iterations=40,
                min_leaf=5,
            )
            # With identical train/development patterns, a single selected fit has exact ranking.
            assert max(c["timely_average_precision"] for c in candidates) == pytest.approx(
                average_precision_score(calibration["targets"]["timely20_60"], scores)
            )
            evaluation, _ = evaluate(
                calibration,
                scores,
                list(range(30)),
                list(range(30, 60)),
                ["europe", "americas"] * 30,
                objective,
            )
            results[objective] = evaluation
            assert model.named_steps["histgradientboostingclassifier"].early_stopping is False
        assert results["timely20_60"]["timely_ranking_average_precision"] == 1.0
        assert (
            results["timely20_60"]["timely_ranking_average_precision"]
            > results["within60"]["timely_ranking_average_precision"]
        )
        # Remove all feature information: narrower target must not magically create ranking signal.
        train["x"][:] = 0
        calibration["x"][:] = 0
        _, scores, _ = fit_predict(
            train,
            calibration,
            development,
            "history",
            "timely20_60",
            leaf_grid=(3,),
            iterations=10,
            min_leaf=5,
        )
        assert average_precision_score(
            calibration["targets"]["timely20_60"], scores
        ) == pytest.approx(calibration["targets"]["timely20_60"].mean())
        with pytest.raises(ValueError, match="Both classes"):
            fit_predict(
                train, calibration, np.ones(len(train["x"]), dtype=bool), "history", "within60"
            )
        with pytest.raises(ValueError, match="Unknown"):
            fit_predict(train, calibration, development, "coordination", "within60")


def cached_fixture(tmp_path, monkeypatch):
    import league_ews.timely_experiment as experiment

    source, output = tmp_path / "source", tmp_path / "timely"
    original = {"fixture": "synthetic-only"}
    write_json(source / "freeze.json", original)
    write_json(
        source / "summary.json",
        {
            "status": "complete-exploratory-calibration-screen",
            "test_matches_unread": 6000,
            "freeze_sha256": sha(source / "freeze.json"),
            "models": {key: {} for key in VARIANT_WIDTHS},
        },
    )
    split = {"partitions": {"train": [], "calibration": [], "test": [{"match_id": "NEVER_OPEN"}]}}
    for partition in ("train", "calibration"):
        data = arrays(24)
        split["partitions"][partition] = [
            {
                "game_version_patch": "16.15" if partition == "train" and i >= 18 else "16.12",
                "regional_route": "europe" if i % 2 else "americas",
            }
            for i in range(24)
        ]
        path = source / "shards" / f"{partition}.00000.npz"
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            x=data["x"],
            y=data["targets"]["within60"],
            times=np.concatenate(data["times"]),
            events=np.concatenate(data["events"]),
            offsets=data["offsets"],
            event_offsets=np.cumsum([0, *[len(e) for e in data["events"]]]),
        )
        write_json(
            path.with_suffix(".json"),
            {
                "freeze_sha256": sha(source / "freeze.json"),
                "sha256": sha(path),
                "matches": 24,
                "rows": len(data["x"]),
            },
        )
    split_path = tmp_path / "split.json"
    write_json(split_path, split)
    monkeypatch.setattr(experiment, "source_freeze", lambda *args: original)
    monkeypatch.setattr(
        experiment, "_chronological_halves", lambda rows: (list(range(12)), list(range(12, 24)))
    )
    return source, tmp_path / "processed", split_path, tmp_path / "audit", output


def test_freeze_and_cache_preserve_source_and_reject_changes(tmp_path, monkeypatch):
    args = cached_fixture(tmp_path, monkeypatch)
    source, _, _, _, output = args
    frozen, _ = freeze(*args)
    original_files = {str(p.relative_to(source)): sha(p) for p in source.rglob("*") if p.is_file()}
    data = load_partition(source, output, "train", frozen)
    assert data["x"].shape == (96, VARIANT_WIDTHS["history"])
    assert len(data["times"]) == 24
    assert original_files == {
        str(p.relative_to(source)): sha(p) for p in source.rglob("*") if p.is_file()
    }
    assert freeze(*args)[0] == frozen
    with pytest.raises(ValueError, match="prohibited"):
        load_partition(source, output, "test", frozen)
    with pytest.raises(ValueError, match="separate"):
        freeze(*args[:-1], source)
    changed = copy.deepcopy(frozen)
    changed["plan"]["seed"] = 0
    write_json(output / "freeze.json", changed)
    with pytest.raises(ValueError, match="freeze differs"):
        freeze(*args)
    shard = source / "shards" / "train.00000.npz"
    shard.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        load_partition(source, output, "train", frozen)
    with pytest.raises(ValueError, match="binding"):
        freeze(*args)


def test_full_four_model_run_resume_and_integrity(tmp_path, monkeypatch):
    import league_ews.timely_experiment as experiment

    args = cached_fixture(tmp_path, monkeypatch)
    original_fit = fit_predict

    def quick_fit(train, calibration, development, variant, objective):
        return original_fit(
            train,
            calibration,
            development,
            variant,
            objective,
            leaf_grid=(3,),
            iterations=8,
            min_leaf=2,
        )

    monkeypatch.setattr(experiment, "fit_predict", quick_fit)
    with threadpool_limits(limits=1):
        assert run(*args, max_new_models=1)["status"] == "models-paused-resume-same-command"
        result = run(*args)
        assert set(result["models"]) == set(MODELS)
        assert len(result["paired_comparisons"]) == 4
        assert result["test_matches_unread"] == 6000
        assert result["models"]["history-within60"]["rows"] == {"train": 96, "calibration": 96}
        monkeypatch.setattr(experiment, "fit_predict", lambda *args: pytest.fail("must resume"))
        assert run(*args) == result
        (args[-1] / MODELS[0] / "scores.npz").write_bytes(b"tampered")
        with pytest.raises(ValueError, match="Completed timely model"):
            run(*args)


def test_cli_locks_outputs_and_source(tmp_path, monkeypatch, capsys):
    import fcntl

    import league_ews.timely_experiment as experiment

    monkeypatch.setattr(sys, "argv", ["timely", "--threads", "0"])
    with pytest.raises(SystemExit):
        experiment.main()
    source, output = tmp_path / "source", tmp_path / "output"
    monkeypatch.setattr(sys, "argv", ["timely", "--source", str(source), "--output", str(output)])
    with pytest.raises(SystemExit):
        experiment.main()
    assert "Complete the coordination" in capsys.readouterr().err
    write_json(source / "summary.json", {})
    output.mkdir(parents=True)
    for root in (source, output):
        with (root / "execution.lock").open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with pytest.raises(SystemExit):
                experiment.main()
            assert "Another command" in capsys.readouterr().err


def test_real_report_is_reproducible_and_flags_no_clear_coordination_gain():
    from pathlib import Path

    source = Path("reports/coordination-screen-real-2026-09-29.json")
    text = render(source)
    assert "**+0.168 percentage points**" in text
    assert "**[-0.044, +0.389] points**" in text
    assert "66.69%" in text and "2.178 per match" in text
    assert text == source.with_suffix(".md").read_text()
