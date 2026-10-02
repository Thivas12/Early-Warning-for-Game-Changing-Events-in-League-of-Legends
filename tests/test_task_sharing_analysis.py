"""Reject alignment errors and prevent a positive macro hiding task/budget failure."""

from copy import deepcopy

import numpy as np
import pytest

from scripts.analyse_task_sharing import EVENTS, SEEDS, diagnostic_rules, validate_predictions
from tests.test_compact_research import sample


@pytest.mark.parametrize("event", EVENTS)
def test_predictions_must_match_exact_selected_event_and_match_order(event):
    cal = sample()
    columns = slice(EVENTS.index(event) * 4, EVENTS.index(event) * 4 + 4)
    saved = {
        "match_offsets": cal["match_offsets"].copy(),
        "targets": cal["targets"][:, columns].copy(),
        "probabilities": np.full(cal["targets"][:, columns].shape, 0.5),
    }
    validate_predictions(saved, cal, event)
    for key, replacement, message in (
        ("match_offsets", saved["match_offsets"] + 1, "offsets"),
        ("targets", 1 - saved["targets"], "labels"),
        ("probabilities", np.zeros(cal["targets"].shape), "probabilities"),
        ("probabilities", np.full(saved["targets"].shape, np.nan), "probabilities"),
        ("probabilities", np.full(saved["targets"].shape, 1.01), "probabilities"),
    ):
        with pytest.raises(ValueError, match=message):
            validate_predictions({**saved, key: replacement}, cal, event)


def positive_analysis():
    seeds = {
        str(s): {
            "timely_recall": {"estimate": 0.02},
            "false_plus_late_per_match": {"estimate": 0.8},
        }
        for s in SEEDS
    }
    item = {
        "by_seed": seeds,
        "mean_over_fixed_seeds": {
            "timely_recall": {"estimate": 0.02, "conditional_95_interval": [0.01, 0.03]}
        },
    }
    events = {e: deepcopy(item) for e in (*EVENTS, "macro")}
    section = {
        "contrasts": {"leagueews_minus_independent": deepcopy(events)},
        "families": {f: deepcopy(events) for f in ("leagueews", "independent")},
    }
    return {r: {"30": deepcopy(section)} for r in ("overall", "europe", "americas")}


def test_positive_macro_does_not_override_regional_budget_or_task_harm():
    analysis = positive_analysis()
    assert diagnostic_rules(analysis)["practical_promotion_gate"]
    analysis["americas"]["30"]["families"]["independent"]["baron"]["by_seed"][str(SEEDS[1])][
        "false_plus_late_per_match"
    ]["estimate"] = 1.001
    rule = diagnostic_rules(analysis)
    assert rule["descriptive_positive_macro_sharing"]
    assert not rule["practical_promotion_gate"]
    dragon = analysis["overall"]["30"]["contrasts"]["leagueews_minus_independent"]["dragon"]
    dragon["mean_over_fixed_seeds"]["timely_recall"] = {
        "estimate": -0.02,
        "conditional_95_interval": [-0.03, -0.01],
    }
    for seed in SEEDS:
        dragon["by_seed"][str(seed)]["timely_recall"]["estimate"] = -0.02
    rule = diagnostic_rules(analysis)
    assert rule["descriptive_positive_macro_sharing"]
    assert rule["descriptive_task_harm"]["dragon"]
    assert not rule["uniform_task_benefit"]


def test_seed_disagreement_and_interval_crossing_zero_block_macro_support():
    analysis = positive_analysis()
    macro = analysis["overall"]["30"]["contrasts"]["leagueews_minus_independent"]["macro"]
    macro["by_seed"][str(SEEDS[0])]["timely_recall"]["estimate"] = -0.001
    assert not diagnostic_rules(analysis)["descriptive_positive_macro_sharing"]
    macro["by_seed"][str(SEEDS[0])]["timely_recall"]["estimate"] = 0.02
    macro["mean_over_fixed_seeds"]["timely_recall"]["conditional_95_interval"][0] = -0.001
    assert not diagnostic_rules(analysis)["descriptive_positive_macro_sharing"]


def test_loader_checks_every_fit_before_opening_predictions(tmp_path, monkeypatch):
    from scripts import analyse_task_sharing as analysis

    study, control = tmp_path / "study", tmp_path / "control"
    study.mkdir()
    control.mkdir()
    analysis.write_json(control / "summary.json", {})
    analysis.write_json(control / "freeze.json", {})
    analysis.write_json(
        study / "freeze.json",
        {
            "archive_sha256": analysis.EXPECTED_ARCHIVE,
            "plan": {
                "events": list(EVENTS),
                "seeds": list(SEEDS),
                "control_summary_sha256": analysis.sha(control / "summary.json"),
                "control_freeze_sha256": analysis.sha(control / "freeze.json"),
            },
            "source_sha256": {},
        },
    )
    binding = analysis.sha(study / "freeze.json")
    reports = {}
    for event in EVENTS:
        for seed in SEEDS:
            folder = study / event / f"seed-{seed}"
            folder.mkdir(parents=True)
            (folder / "checkpoint.pt").write_bytes(b"fixture checkpoint")
            (folder / "calibration-scores.npz").write_bytes(b"must not be opened")
            report = {
                "event": event,
                "seed": seed,
                "freeze_sha256": binding,
                "test_payloads_opened": 0,
                "checkpoint_sha256": analysis.sha(folder / "checkpoint.pt"),
                "scores_sha256": analysis.sha(folder / "calibration-scores.npz"),
            }
            analysis.write_json(folder / "report.json", report)
            analysis.write_json(
                folder / "progress.json",
                {
                    **report,
                    "completed_units": 575 if (event == EVENTS[-1] and seed == SEEDS[-1]) else 576,
                },
            )
            reports[f"{event}/{seed}"] = report
    analysis.write_json(
        study / "summary.json",
        {
            "schema_version": "league-task-sharing-results-v1",
            "status": "complete-exploratory-task-sharing",
            "test_payloads_opened": 0,
            "freeze_sha256": binding,
            "models": reports,
        },
    )
    monkeypatch.setattr(analysis.np, "load", lambda *a, **k: pytest.fail("Premature predictions"))
    with pytest.raises(ValueError, match="training incomplete"):
        analysis.load_independent(study, control, {}, [])
