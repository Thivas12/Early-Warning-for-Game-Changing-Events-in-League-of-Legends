"""A mean gain cannot conceal task harm, seed disagreement or budget failure."""

from copy import deepcopy

import pytest

from scripts.analyse_pcgrad import EVENTS, SEEDS, diagnostic_rules
from tests.test_task_sharing_analysis import positive_analysis


def fixture_analysis():
    result = positive_analysis()
    for section in result.values():
        data = section["30"]
        data["families"]["pcgrad"] = deepcopy(data["families"]["leagueews"])
        template = data["contrasts"]["leagueews_minus_independent"]
        for family in ("leagueews", "independent", "tcn"):
            data["contrasts"][f"pcgrad_minus_{family}"] = deepcopy(template)
    return result


@pytest.mark.parametrize("event", EVENTS)
def test_harm_to_any_event_blocks_screen(event):
    data = fixture_analysis()
    assert diagnostic_rules(data)["practical_screen"]
    data["overall"]["30"]["contrasts"]["pcgrad_minus_leagueews"][event]["mean_over_fixed_seeds"][
        "timely_recall"
    ]["estimate"] = -0.001
    assert not diagnostic_rules(data)["no_mean_task_harm"]
    assert not diagnostic_rules(data)["practical_screen"]


def test_regional_budget_failure_cannot_hide_in_average():
    data = fixture_analysis()
    data["americas"]["30"]["families"]["pcgrad"]["baron"]["by_seed"][str(SEEDS[-1])][
        "false_plus_late_per_match"
    ]["estimate"] = 1.001
    rules = diagnostic_rules(data)
    assert rules["baron_recovery"] and rules["macro_gain"]
    assert not rules["all_pcgrad_primary_regional_budgets"]
    assert not rules["practical_screen"]


@pytest.mark.parametrize("event,rule", [("baron", "baron_recovery"), ("macro", "macro_gain")])
def test_seed_disagreement_or_interval_crossing_zero_blocks_gain(event, rule):
    data = fixture_analysis()
    value = data["overall"]["30"]["contrasts"]["pcgrad_minus_leagueews"][event]
    value["by_seed"][str(SEEDS[0])]["timely_recall"]["estimate"] = -0.001
    assert not diagnostic_rules(data)[rule]
    value["by_seed"][str(SEEDS[0])]["timely_recall"]["estimate"] = 0.02
    value["mean_over_fixed_seeds"]["timely_recall"]["conditional_95_interval"][0] = -0.001
    assert not diagnostic_rules(data)[rule]


@pytest.mark.parametrize("family", ["independent", "tcn"])
def test_both_strong_controls_required(family):
    data = fixture_analysis()
    data["overall"]["30"]["contrasts"][f"pcgrad_minus_{family}"]["macro"]["mean_over_fixed_seeds"][
        "timely_recall"
    ]["conditional_95_interval"][0] = -0.001
    assert not diagnostic_rules(data)["strong_control_gain"]
    assert not diagnostic_rules(data)["practical_screen"]


def test_loader_checks_every_fit_before_opening_predictions(tmp_path, monkeypatch):
    from pathlib import Path

    from scripts import analyse_pcgrad as analysis

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
                "independent_summary_sha256": analysis.sha(control / "summary.json"),
                "diagnostic_file": "reports/gradient-conflict-2026-10-02/diagnostics.json",
                "diagnostic_sha256": analysis.sha(
                    Path(analysis.__file__).resolve().parents[1]
                    / "reports/gradient-conflict-2026-10-02/diagnostics.json"
                ),
                "control_freeze_sha256": analysis.sha(control / "freeze.json"),
            },
            "source_sha256": {},
        },
    )
    binding = analysis.sha(study / "freeze.json")
    reports = {}
    for event in ("pcgrad",):
        for seed in SEEDS:
            folder = study / event / f"seed-{seed}"
            folder.mkdir(parents=True)
            (folder / "checkpoint.pt").write_bytes(b"fixture checkpoint")
            (folder / "calibration-scores.npz").write_bytes(b"must not be opened")
            report = {
                "family": event,
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
                    "completed_units": 575 if (seed == SEEDS[-1]) else 576,
                },
            )
            reports[f"{event}/{seed}"] = report
    analysis.write_json(
        study / "summary.json",
        {
            "schema_version": "league-pcgrad-results-v1",
            "status": "complete-exploratory-pcgrad",
            "test_payloads_opened": 0,
            "freeze_sha256": binding,
            "models": reports,
        },
    )
    monkeypatch.setattr(analysis.np, "load", lambda *a, **k: pytest.fail("Premature predictions"))
    with pytest.raises(ValueError, match="completion"):
        analysis.load_pcgrad(study, control, control, {}, [])
