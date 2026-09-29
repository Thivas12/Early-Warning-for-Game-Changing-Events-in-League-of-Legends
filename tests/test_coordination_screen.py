"""Leakage, matching, artifact-integrity and injected-signal checks for the screen."""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from league_ews.alert_policy import MatchRisk
from league_ews.coordination_experiment import (
    bind_inputs,
    evaluate_scores,
    fit_predict,
    freeze,
    load_partition,
    run,
    sha,
    stage,
    write_json,
)
from league_ews.coordination_features import (
    COORDINATION_NAMES,
    FEATURE_NAMES,
    VARIANT_WIDTHS,
    coordination_matrix,
)
from league_ews.coordination_policy import paired_intervals, replay, select_budget_policy
from league_ews.timeline import NormalizedTimeline
from scripts.coordination_screen_smoke import synthetic_arrays, timeline


def test_features_are_causal_permutation_invariant_and_history_sensitive():
    source = timeline(True)
    expected = coordination_matrix(source)
    altered = source.model_dump()
    for observation in altered["observations"]:
        observation["participants"] = tuple(reversed(observation["participants"]))
    np.testing.assert_allclose(
        coordination_matrix(NormalizedTimeline.model_validate(altered)), expected, equal_nan=True
    )
    altered["observations"][-1]["participants"][0]["total_gold"] += 1_000_000
    altered["observations"][-1]["participants"][0]["position"] = {"x": 0, "y": 0}
    np.testing.assert_allclose(
        coordination_matrix(NormalizedTimeline.model_validate(altered))[:-1],
        expected[:-1],
        equal_nan=True,
    )
    altered = source.model_dump()
    altered["observations"][0]["events"] = [
        {
            "timestamp_ms": 900_000,
            "event_type": "ELITE_MONSTER_KILL",
            "monster_type": "DRAGON",
            "killer_team_id": 100,
        }
    ]
    np.testing.assert_allclose(
        coordination_matrix(NormalizedTimeline.model_validate(altered))[0],
        expected[0],
        equal_nan=True,
    )
    ordinary = coordination_matrix(timeline(False))
    np.testing.assert_allclose(
        expected[2, : VARIANT_WIDTHS["history"]],
        ordinary[2, : VARIANT_WIDTHS["history"]],
        equal_nan=True,
    )
    assert expected[2, FEATURE_NAMES.index("blue_displacement_rate_mean")] > 0
    assert ordinary[2, FEATURE_NAMES.index("blue_displacement_rate_mean")] == 0


def test_missing_stale_and_invalid_participants_are_explicit():
    source = timeline().model_dump()
    for obs in source["observations"]:
        for person in obs["participants"]:
            person["position"] = None
    matrix = coordination_matrix(NormalizedTimeline.model_validate(source))
    assert matrix[1, FEATURE_NAMES.index("blue_tracked_count")] == 0
    assert np.isnan(matrix[1, FEATURE_NAMES.index("blue_direction_coherence")])
    source["observations"][-1]["timestamp_ms"] += 240_000
    matrix = coordination_matrix(NormalizedTimeline.model_validate(source))
    assert np.isnan(matrix[-1, -len(COORDINATION_NAMES) :]).all()
    assert np.isnan(matrix[-1, FEATURE_NAMES.index("lag1_age_seconds")])
    invalid = copy.deepcopy(source)
    invalid["observations"][0]["participants"][0]["participant_id"] = 2
    with pytest.raises(ValueError, match="unique"):
        coordination_matrix(NormalizedTimeline.model_validate(invalid))
    invalid = copy.deepcopy(source)
    invalid["observations"][0]["participants"][0]["team_id"] = 200
    invalid["observations"][0]["participants"][5]["team_id"] = 100
    with pytest.raises(ValueError, match="identities"):
        coordination_matrix(NormalizedTimeline.model_validate(invalid))
    invalid = copy.deepcopy(source)
    invalid["observations"][1]["timestamp_ms"] = 480_000
    with pytest.raises(ValueError, match="ordered"):
        coordination_matrix(NormalizedTimeline.model_validate(invalid))


def test_policy_boundary_late_alerts_opportunity_and_no_alert_option():
    match = MatchRisk((300_000, 360_000, 420_000), (330_000, 390_000, 450_000), (1.0, 1.0, 1.0))
    summary, counts = replay([match], 1.0)
    assert summary["timely_event_recall"] == 1
    assert summary["false_alerts_per_game"] == 0
    assert summary["timely_opportunities"] == 3
    assert counts[0].tolist() == [3, 3, 3, 3, 0, 3]
    late, _ = replay([MatchRisk((300_000,), (310_000,), (1.0,))], 1.0)
    assert late["late_alerts_per_game"] == 1
    assert late["timely_event_recall"] == 0
    assert late["false_alerts_per_game"] == 0
    assert replay([match], None)[0]["alerts"] == 0
    threshold, _ = select_budget_policy([MatchRisk((0, 60_000, 120_000), (), (1.0, 1.0, 1.0))], 0)
    assert threshold is None
    with pytest.raises(ValueError, match="Invalid"):
        replay([MatchRisk((1, 1), (), (0.1, 0.2))], 0.5)
    with pytest.raises(ValueError, match="Invalid"):
        replay([match], 0)
    with pytest.raises(ValueError, match="Budget"):
        select_budget_policy([match], -1)


def test_threshold_never_uses_later_outcomes_and_bootstrap_is_paired():
    data = synthetic_arrays(8)
    scores = np.where(data["y"], 0.9, 0.1)
    early, later = list(range(4)), list(range(4, 8))
    original, counts = evaluate_scores(data, scores, early, later)
    changed = copy.deepcopy(data)
    changed["events"][4:] = [()] * 4
    changed["y"][4:] = 0
    changed_scores = scores.copy()
    changed_scores[4:] = 1.0
    updated, _ = evaluate_scores(changed, changed_scores, early, later)
    assert original["threshold"] == updated["threshold"]
    result = paired_intervals(
        counts, counts, ["europe", "europe", "americas", "americas"], draws=100
    )
    assert result["timely_recall_difference"] == 0
    assert result["percentile_95_intervals"]["timely_recall_difference"] == [0, 0]
    with pytest.raises(ValueError, match="partition"):
        evaluate_scores(data, scores, early, early)
    with pytest.raises(ValueError, match="scores"):
        evaluate_scores(data, scores * np.nan, early, later)
    with pytest.raises(ValueError, match="Paired"):
        paired_intervals(counts, counts[:-1], ["europe"] * 4, draws=100)


def test_injected_coordination_positive_and_negative_controls():
    train, calibration = synthetic_arrays(80), synthetic_arrays(40)
    development = np.arange(80) >= 60
    early, later = list(range(20)), list(range(20, 40))
    with threadpool_limits(limits=1):
        _, history_scores, _ = fit_predict(
            train, calibration, development, "history", leaf_grid=(3, 7), iterations=25, min_leaf=5
        )
        _, coordination_scores, _ = fit_predict(
            train,
            calibration,
            development,
            "coordination",
            leaf_grid=(3, 7),
            iterations=25,
            min_leaf=5,
        )
        history, _ = evaluate_scores(calibration, history_scores, early, later)
        coordination, _ = evaluate_scores(calibration, coordination_scores, early, later)
        assert (
            coordination["evaluation_row_metrics"]["average_precision"]
            > history["evaluation_row_metrics"]["average_precision"]
        )
        assert (
            coordination["evaluation"]["false_alerts_per_game"]
            < history["evaluation"]["false_alerts_per_game"]
        )
        # Remove the injected distinction: the larger representation must lose its advantage.
        train["x"][:] = train["x"][0]
        calibration["x"][:] = calibration["x"][0]
        _, null_scores, _ = fit_predict(
            train,
            calibration,
            development,
            "coordination",
            leaf_grid=(3,),
            iterations=25,
            min_leaf=5,
        )
        np.testing.assert_allclose(null_scores, history_scores)
        with pytest.raises(ValueError, match="both classes"):
            fit_predict(train, calibration, np.ones(80, dtype=bool), "history")


def test_stage_resume_checksums_and_sealed_test_nonaccess(tmp_path):
    processed, output = tmp_path / "processed", tmp_path / "screen"
    write_json(output / "freeze.json", {"fixture": "synthetic-only"})
    split = {"partitions": {"train": [], "calibration": [], "test": [{"match_id": "NEVER_OPEN"}]}}
    records = {}
    for partition, match_id in (("train", "EUW1_1"), ("calibration", "EUW1_2")):
        source = timeline(match_id=match_id)
        payload = {
            "schema_version": "league-ews-processed-match-v1",
            "timeline": source.model_dump(),
            "labels": [
                {"timestamp_ms": obs.timestamp_ms, "y_dragon_60": int(obs.timestamp_ms == 600_000)}
                for obs in source.observations
            ],
            "event_index": {"dragon_ms": [630_000]},
        }
        path = processed / "matches" / f"{match_id}.json"
        write_json(path, payload)
        records[match_id] = SimpleNamespace(
            sha256=sha(path), observations=4, game_version="16.12.1"
        )
        split["partitions"][partition].append({"match_id": match_id, "game_creation_ms": 1})
    assert stage(processed, split, records, output, max_new=1) is False
    assert stage(processed, split, records, output, max_new=1) is True
    assert stage(processed, split, records, output) is True
    loaded = load_partition(output, "calibration")
    assert loaded["y"].tolist() == [0, 0, 1, 0]
    assert loaded["events"] == [(630_000,)]
    assert loaded["offsets"].tolist() == [0, 4]
    path = output / "shards" / "calibration.00000.npz"
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="binding"):
        stage(processed, split, records, output)
    with pytest.raises(ValueError, match="checksum"):
        load_partition(output, "calibration")
    with pytest.raises(ValueError, match="No staged"):
        load_partition(output, "test")


def test_invalid_source_target_cannot_be_staged(tmp_path):
    source = timeline()
    processed, output = tmp_path / "processed", tmp_path / "output"
    write_json(output / "freeze.json", {})
    path = processed / "matches" / "EUW1_1.json"
    payload = {
        "timeline": source.model_dump(),
        "schema_version": "league-ews-processed-match-v1",
        "labels": [
            {"timestamp_ms": obs.timestamp_ms, "y_dragon_60": 0} for obs in source.observations
        ],
        "event_index": {"dragon_ms": [630_000]},
    }
    write_json(path, payload)
    entries = [{"match_id": "EUW1_1", "game_creation_ms": 1}]
    split = {"partitions": {"train": entries, "calibration": []}}
    records = {"EUW1_1": SimpleNamespace(sha256=sha(path), observations=4, game_version="16.12.1")}
    with pytest.raises(ValueError, match="targets"):
        stage(processed, split, records, output)
    payload["event_index"]["dragon_ms"] = [900_000]
    write_json(path, payload)
    records["EUW1_1"].sha256 = sha(path)
    with pytest.raises(ValueError, match="chronology"):
        stage(processed, split, records, output)
    entries[0]["game_creation_ms"] = 2
    with pytest.raises(ValueError, match="metadata"):
        stage(processed, split, records, output)


def _cohort_metadata(tmp_path):
    processed = tmp_path / "processed"
    partitions = {"train": [], "calibration": [], "test": []}
    records = []
    for patch in range(12, 18):
        partition = "train" if patch <= 15 else "calibration" if patch == 16 else "test"
        for index in range(6000):
            platform, route = ("EUW1", "europe") if index % 2 == 0 else ("NA1", "americas")
            match_id = f"{platform}_{patch * 10000 + index}"
            partitions[partition].append(
                {
                    "match_id": match_id,
                    "regional_route": route,
                    "game_version_patch": f"16.{patch}",
                    "game_creation_ms": patch * 10000 + index,
                }
            )
            records.append(
                {
                    "match_id": match_id,
                    "game_version": f"16.{patch}.1",
                    "observations": 1,
                    "baron_events": 0,
                    "dragon_events": 0,
                    "teamfight_events": 0,
                    "sha256": "a" * 64,
                }
            )
    manifest = processed / "processing-manifest.json"
    write_json(
        manifest,
        {
            "schema_version": "league-ews-processing-manifest-v1",
            "normalizer": "riot-match-v5-normalized-v1",
            "label_policy": "exact-future-events-v1",
            "matches": records,
            "contains_player_identifiers": False,
        },
    )
    audit = tmp_path / "audit.json"
    write_json(
        audit,
        {
            "schema_version": "league-ews-processed-validation-v1",
            "passed": True,
            "processing_manifest_sha256": sha(manifest),
            "raw_manifest_sha256": "b" * 64,
            "summary": {"validated_matches": 36000, "contains_player_identifiers": False},
        },
    )
    split = tmp_path / "split.json"
    write_json(
        split,
        {
            "schema_version": "league-ews-final-split-v1",
            "processing_manifest_sha256": sha(manifest),
            "processed_audit_sha256": sha(audit),
            "raw_manifest_sha256": "b" * 64,
            "partitions": partitions,
        },
    )
    return processed, split, audit


def test_freeze_validates_membership_without_match_access_and_detects_drift(tmp_path):
    processed, split_path, audit = _cohort_metadata(tmp_path)
    output = tmp_path / "screen"
    first = freeze(processed, split_path, audit, output)
    assert freeze(processed, split_path, audit, output) == first
    assert first["test_matches_unread"] == 6000
    assert not (processed / "matches").exists()
    stored = json.loads((output / "freeze.json").read_text())
    stored["plan"]["seed"] = 0
    write_json(output / "freeze.json", stored)
    with pytest.raises(ValueError, match="freeze differs"):
        freeze(processed, split_path, audit, output)
    original = json.loads(split_path.read_text())
    for key, value in (
        ("regional_route", "wrong"),
        ("game_version_patch", "16.17"),
        ("game_creation_ms", -1),
    ):
        changed = copy.deepcopy(original)
        changed["partitions"]["train"][1][key] = value
        write_json(split_path, changed)
        with pytest.raises(ValueError, match="membership"):
            bind_inputs(processed, split_path, audit)
    changed = copy.deepcopy(original)
    changed["partitions"]["train"][1] = changed["partitions"]["train"][0]
    write_json(split_path, changed)
    with pytest.raises(ValueError, match="membership"):
        bind_inputs(processed, split_path, audit)
    changed = copy.deepcopy(original)
    changed["processed_audit_sha256"] = "0" * 64
    write_json(split_path, changed)
    with pytest.raises(ValueError, match="audited cohort"):
        bind_inputs(processed, split_path, audit)


def test_resumable_orchestrator_fits_saves_and_compares_all_models(tmp_path, monkeypatch):
    import league_ews.coordination_experiment as experiment

    processed, output = tmp_path / "processed", tmp_path / "screen"
    split = {"partitions": {"train": [], "calibration": [], "test": [{"match_id": "NEVER_OPEN"}]}}
    records = {}
    for partition in ("train", "calibration"):
        for index in range(4):
            match_id = f"EUW1_{index + (1 if partition == 'train' else 100)}"
            source = timeline(bool(index % 2), match_id=match_id)
            patch = "16.15" if index >= 2 and partition == "train" else "16.12"
            source = source.model_copy(update={"game_version": patch + ".1"})
            payload = {
                "schema_version": "league-ews-processed-match-v1",
                "timeline": source.model_dump(),
                "labels": [
                    {
                        "timestamp_ms": obs.timestamp_ms,
                        "y_dragon_60": int(index % 2 and obs.timestamp_ms == 600_000),
                    }
                    for obs in source.observations
                ],
                "event_index": {"dragon_ms": [630_000] if index % 2 else []},
            }
            path = processed / "matches" / f"{match_id}.json"
            write_json(path, payload)
            records[match_id] = SimpleNamespace(
                sha256=sha(path), observations=4, game_version=source.game_version
            )
            split["partitions"][partition].append(
                {
                    "match_id": match_id,
                    "game_creation_ms": 1,
                    "game_version_patch": patch,
                    "regional_route": "europe",
                }
            )

    def fixture_freeze(*args):
        write_json(output / "freeze.json", {"synthetic_fixture": True})

    original_fit = fit_predict

    def quick_fit(train, calibration, development, variant):
        return original_fit(
            train, calibration, development, variant, leaf_grid=(3,), iterations=5, min_leaf=2
        )

    monkeypatch.setattr(experiment, "freeze", fixture_freeze)
    monkeypatch.setattr(experiment, "bind_inputs", lambda *args: (split, records))
    monkeypatch.setattr(experiment, "_chronological_halves", lambda entries: ([0, 1], [2, 3]))
    monkeypatch.setattr(experiment, "fit_predict", quick_fit)
    args = processed, tmp_path / "split", tmp_path / "audit", output
    with threadpool_limits(limits=1):
        assert run(*args, max_new_shards=1)["status"].startswith("staging-paused")
        assert run(*args, max_new_models=1)["status"].startswith("models-paused")
        result = run(*args, max_new_models=0)
        assert set(result["models"]) == set(VARIANT_WIDTHS)
        assert result["test_matches_unread"] == 6000
        assert run(*args) == result
        (output / "b3" / "model.joblib").write_bytes(b"tampered")
        with pytest.raises(ValueError, match="Completed model"):
            run(*args)


def test_cli_requires_inputs_and_serializes_execution(tmp_path, monkeypatch, capsys):
    import fcntl
    import sys

    import league_ews.coordination_experiment as experiment

    monkeypatch.setattr(sys, "argv", ["screen", "--threads", "0"])
    with pytest.raises(SystemExit):
        experiment.main()
    paths = [
        tmp_path / "processing-manifest.json",
        tmp_path / "split.json",
        tmp_path / "audit.json",
    ]
    output = tmp_path / "output"
    args = [
        "screen",
        "--processed",
        str(tmp_path),
        "--split",
        str(paths[1]),
        "--processed-audit",
        str(paths[2]),
        "--output",
        str(output),
    ]
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit):
        experiment.main()
    assert "Required private inputs" in capsys.readouterr().err
    for path in paths:
        write_json(path, {})
    monkeypatch.setattr(experiment, "freeze", lambda *args: {"status": "fixture-frozen"})
    monkeypatch.setattr(experiment, "run", lambda *args, **kwargs: {"status": "fixture-ran"})
    monkeypatch.setattr(sys, "argv", [*args, "--freeze-only"])
    experiment.main()
    assert "fixture-frozen" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", args)
    experiment.main()
    assert "fixture-ran" in capsys.readouterr().out
    with (output / "execution.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SystemExit):
            experiment.main()
        assert "Another coordination command" in capsys.readouterr().err
