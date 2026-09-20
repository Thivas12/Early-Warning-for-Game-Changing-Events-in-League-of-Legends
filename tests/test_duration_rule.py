from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from league_ews.cli import main
from league_ews.duration_rule import (
    CANDIDATE_MINIMUM_SECONDS,
    DECISION_FIELDS,
    DurationRule,
    _analysis_checks,
    validate_duration_rule,
)

FRAME_PATH = Path("configs/rifthazard-sampling-frame.yaml")
RULE_PATH = Path("configs/rifthazard-duration-rule.yaml")


def _rule() -> DurationRule:
    return DurationRule.model_validate(yaml.safe_load(RULE_PATH.read_text(encoding="utf-8")))


def _analysis_content(rule: DurationRule) -> bytes:
    rows = []
    for minimum in CANDIDATE_MINIMUM_SECONDS:
        selected = minimum == rule.decision.final_minimum_seconds
        rows.append(
            {
                "minimum_seconds": minimum,
                "excluded_matches": 90 if selected else 0,
                "excluded_fraction": 0.018 if selected else 0.0,
                "excluded_early_surrender_matches": 90 if selected else 0,
                "excluded_other_matches": 0,
                "retained_matches": 4_910 if selected else 5_000,
            }
        )
    report = {
        "schema_version": "league-ews-pilot-duration-analysis-v1",
        "frame_id": rule.frame.frame_id,
        "bindings": {"frame_sha256": rule.frame.frame_sha256},
        "input_policy": {
            "fields_used": list(DECISION_FIELDS),
            "event_labels_used": False,
            "model_outputs_used": False,
            "winner_used": False,
        },
        "duration": {"matches": 5_000, "early_surrender_matches": 90},
        "candidate_minimums": rows,
        "represented_cells": 12,
        "identifiers_in_summary": False,
    }
    return (json.dumps(report, sort_keys=True) + "\n").encode()


def _failed(checks: list[object]) -> set[str]:
    return {
        str(check["check_id"])
        for check in checks
        if isinstance(check, dict) and check["passed"] is False
    }


def test_registered_duration_rule_public_contract_is_frozen() -> None:
    report = validate_duration_rule(RULE_PATH, FRAME_PATH, None)

    assert report["passed"] is False
    assert _failed(report["checks"]) == {"analysis-file"}
    assert report["summary"] == {
        "frame_id": "rifthazard-2026-09-15",
        "final_minimum_seconds": 180,
        "eligibility_expression": "info.gameDuration >= 180",
        "pilot_matches": 5_000,
        "excluded_matches": 90,
        "retained_matches": 4_910,
        "identifiers_in_summary": False,
    }


def test_private_analysis_must_exactly_support_rule() -> None:
    rule = _rule()
    content = _analysis_content(rule)
    bound_rule = rule.model_copy(
        update={
            "pilot_analysis": rule.pilot_analysis.model_copy(
                update={"sha256": hashlib.sha256(content).hexdigest()}
            )
        }
    )

    checks = _analysis_checks(bound_rule, content)

    assert all(check.passed for check in checks)


@pytest.mark.parametrize("identifier_key", ["match_id", "matchId", "puuid", "summonerId"])
def test_private_analysis_rejects_identifier_content(identifier_key: str) -> None:
    rule = _rule()
    payload = json.loads(_analysis_content(rule))
    payload[identifier_key] = "EUW1_123"
    content = (json.dumps(payload, sort_keys=True) + "\n").encode()
    bound_rule = rule.model_copy(
        update={
            "pilot_analysis": rule.pilot_analysis.model_copy(
                update={"sha256": hashlib.sha256(content).hexdigest()}
            )
        }
    )

    checks = _analysis_checks(bound_rule, content)

    failed = {check.check_id for check in checks if not check.passed}
    assert failed == {"analysis-identifiers"}


def test_duration_rule_cli_writes_private_validation(tmp_path, monkeypatch) -> None:
    output = tmp_path / "validation.json"
    monkeypatch.setattr(
        "league_ews.cli.validate_duration_rule",
        lambda *args: {"passed": True, "rule_id": "test"},
    )

    exit_code = main(
        [
            "validate-duration-rule",
            "--rule",
            str(RULE_PATH),
            "--sampling-frame",
            str(FRAME_PATH),
            "--analysis",
            str(tmp_path / "analysis.json"),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["rule_id"] == "test"
