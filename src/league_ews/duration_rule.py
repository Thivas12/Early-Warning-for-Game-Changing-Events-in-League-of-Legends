"""Validation for the checksum-bound post-pilot minimum-duration rule."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.sampling import SamplingFrame, load_registered_sampling_frame

DURATION_ANALYSIS_SCHEMA_VERSION = "league-ews-pilot-duration-analysis-v1"
DURATION_RULE_SCHEMA_VERSION = "league-ews-duration-rule-v1"
DURATION_RULE_VALIDATION_SCHEMA_VERSION = "league-ews-duration-rule-validation-v1"
CANDIDATE_MINIMUM_SECONDS = (0, 180, 300, 600, 900, 1_200)

REGISTERED_DURATION_RULE_ID = "rifthazard-duration-2026-09-20"
REGISTERED_DURATION_FREEZE_DATE = date(2026, 9, 20)
REGISTERED_FRAME_ID = "rifthazard-2026-09-15"
REGISTERED_FRAME_SHA256 = "2355ec26182aa6862e8a110ff94f0ab402e9a4e77c0a52a0a5c81f1892033f6b"
REGISTERED_DURATION_ANALYSIS_SHA256 = (
    "3cab09e4f305bb67b089e28a35276cee1fe67add9584baef6552d78b7a12c9c5"
)
REGISTERED_FINAL_MINIMUM_SECONDS = 180
REGISTERED_PILOT_MATCHES = 5_000
REGISTERED_REPRESENTED_CELLS = 12
REGISTERED_EARLY_SURRENDER_MATCHES = 90
REGISTERED_EXCLUDED_MATCHES = 90
REGISTERED_RETAINED_MATCHES = 4_910

DECISION_FIELDS = (
    "info.gameDuration",
    "info.participants.gameEndedInEarlySurrender",
    "info.participants.gameEndedInSurrender",
)
MATCH_ID_PATTERN = re.compile(r"^(?:EUW1|NA1)_[0-9]+$")
IDENTIFIER_KEYS = frozenset(
    {
        "match_id",
        "matchId",
        "puuid",
        "summoner_id",
        "summonerId",
        "summoner_name",
        "summonerName",
        "riot_id_game_name",
        "riotIdGameName",
        "riot_id_tagline",
        "riotIdTagline",
        "account_id",
        "accountId",
    }
)


class DurationFrameBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    frame_id: Literal["rifthazard-2026-09-15"]
    frame_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DurationAnalysisBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["league-ews-pilot-duration-analysis-v1"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    matches: int = Field(gt=0)
    represented_cells: int = Field(gt=0)
    identifiers_in_summary: Literal[False]


class DurationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    early_surrender_matches: int = Field(ge=0)
    excluded_matches: int = Field(ge=0)
    excluded_early_surrender_matches: int = Field(ge=0)
    excluded_other_matches: int = Field(ge=0)
    retained_matches: int = Field(ge=0)


class DurationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    duration_field: Literal["info.gameDuration"]
    comparison: Literal["greater-than-or-equal"]
    final_minimum_seconds: int = Field(gt=0)
    candidate_minimum_seconds: tuple[int, ...] = Field(min_length=1)
    selection_rule: Literal[
        "lowest-candidate-excluding-all-early-surrenders-and-no-other-matches-v1"
    ]
    evidence: DurationEvidence


class DurationControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pilot_excluded_from_final_claims: Literal[True]
    pilot_match_ids_excluded_from_final: Literal[True]
    chosen_before_final_collection: Literal[True]
    immutable_after_final_collection_starts: Literal[True]
    event_labels_used: Literal[False]
    model_outputs_used: Literal[False]
    winner_used: Literal[False]


class DurationRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["league-ews-duration-rule-v1"]
    rule_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    frozen_on: date
    status: Literal["frozen-after-registered-pilot-before-final-collection"]
    frame: DurationFrameBinding
    pilot_analysis: DurationAnalysisBinding
    decision: DurationDecision
    controls: DurationControls


@dataclass(frozen=True)
class DurationRuleCheck:
    check_id: str
    passed: bool
    message: str


def _check(check_id: str, passed: bool, success: str, failure: str) -> DurationRuleCheck:
    return DurationRuleCheck(
        check_id=check_id,
        passed=passed,
        message=success if passed else failure,
    )


def _safe_validation_error(error: ValidationError) -> str:
    issues = []
    for item in error.errors(include_input=False, include_context=False):
        location = ".".join(str(part) for part in item["loc"]) or "rule"
        issues.append(f"{location}: {item['type']}")
    return "; ".join(issues)


def _load_rule_bytes(path: Path) -> tuple[bytes, DurationRule]:
    content = path.read_bytes()
    payload = yaml.safe_load(content)
    if not isinstance(payload, Mapping):
        raise ValueError("duration rule must contain a mapping")
    return content, DurationRule.model_validate(payload)


def load_duration_rule(path: str | Path) -> DurationRule:
    """Load a strictly validated duration-rule document."""

    try:
        _, rule = _load_rule_bytes(Path(path))
    except ValidationError as error:
        raise ValueError(
            f"duration rule schema rejected: {_safe_validation_error(error)}"
        ) from error
    except yaml.YAMLError as error:
        raise ValueError("duration rule contains invalid YAML") from error
    except OSError as error:
        raise ValueError("duration rule is missing or unreadable") from error
    return rule


def _contract_checks(
    rule: DurationRule,
    frame: SamplingFrame,
    frame_sha256: str,
) -> list[DurationRuleCheck]:
    evidence = rule.decision.evidence
    return [
        DurationRuleCheck(
            check_id="rule-schema",
            passed=True,
            message=f"Duration rule conforms to {DURATION_RULE_SCHEMA_VERSION}",
        ),
        _check(
            "freeze-stage",
            rule.rule_id == REGISTERED_DURATION_RULE_ID
            and rule.frozen_on == REGISTERED_DURATION_FREEZE_DATE
            and rule.frozen_on > frame.frozen_on,
            "The rule was frozen after the registered pilot and before final collection",
            "Duration-rule identity or freeze date differs from the registered amendment",
        ),
        _check(
            "frame-binding",
            rule.frame.frame_id == frame.frame_id == REGISTERED_FRAME_ID
            and rule.frame.frame_sha256 == frame_sha256 == REGISTERED_FRAME_SHA256,
            "The rule is bound to the immutable pre-pilot sampling frame",
            "Duration rule does not match the registered sampling-frame checksum",
        ),
        _check(
            "analysis-binding",
            rule.pilot_analysis.schema_version == DURATION_ANALYSIS_SCHEMA_VERSION
            and rule.pilot_analysis.sha256 == REGISTERED_DURATION_ANALYSIS_SHA256
            and rule.pilot_analysis.matches == REGISTERED_PILOT_MATCHES
            and rule.pilot_analysis.represented_cells == REGISTERED_REPRESENTED_CELLS
            and not rule.pilot_analysis.identifiers_in_summary,
            "The rule declares the exact identifier-free 5,000-match pilot analysis",
            "Pilot-analysis identity or registered inventory differs from the freeze",
        ),
        _check(
            "decision-rule",
            rule.decision.final_minimum_seconds == REGISTERED_FINAL_MINIMUM_SECONDS
            and rule.decision.candidate_minimum_seconds == CANDIDATE_MINIMUM_SECONDS,
            "The final rule retains matches with gameDuration >= 180 seconds",
            "The duration cutoff or predeclared candidate grid differs from the freeze",
        ),
        _check(
            "decision-evidence",
            evidence.early_surrender_matches == REGISTERED_EARLY_SURRENDER_MATCHES
            and evidence.excluded_matches == REGISTERED_EXCLUDED_MATCHES
            and evidence.excluded_early_surrender_matches == REGISTERED_EARLY_SURRENDER_MATCHES
            and evidence.excluded_other_matches == 0
            and evidence.retained_matches == REGISTERED_RETAINED_MATCHES
            and evidence.excluded_matches + evidence.retained_matches == REGISTERED_PILOT_MATCHES,
            "The lowest clean candidate excludes all early surrenders and no other matches",
            "Recorded pilot evidence does not support the frozen 180-second decision",
        ),
        _check(
            "anti-selection-controls",
            rule.controls.event_labels_used is False
            and rule.controls.model_outputs_used is False
            and rule.controls.winner_used is False
            and rule.controls.pilot_excluded_from_final_claims
            and rule.controls.pilot_match_ids_excluded_from_final
            and rule.controls.chosen_before_final_collection
            and rule.controls.immutable_after_final_collection_starts,
            "The rule is outcome-blind, pilot-isolated and immutable for final collection",
            "One or more post-pilot anti-selection controls are not confirmed",
        ),
    ]


def _json_object(content: bytes) -> Mapping[str, Any]:
    payload = json.loads(content)
    if not isinstance(payload, Mapping):
        raise ValueError("duration analysis must contain a JSON object")
    return payload


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _contains_identifier(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in IDENTIFIER_KEYS or _contains_identifier(item) for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_identifier(item) for item in value)
    return isinstance(value, str) and MATCH_ID_PATTERN.fullmatch(value) is not None


def _analysis_checks(
    rule: DurationRule,
    analysis_content: bytes,
) -> list[DurationRuleCheck]:
    analysis_sha256 = hashlib.sha256(analysis_content).hexdigest()
    try:
        report = _json_object(analysis_content)
    except (json.JSONDecodeError, ValueError):
        return [
            DurationRuleCheck(
                check_id="analysis-schema",
                passed=False,
                message="Private duration analysis is not a valid JSON object",
            )
        ]

    bindings = _mapping(report.get("bindings"))
    input_policy = _mapping(report.get("input_policy"))
    duration = _mapping(report.get("duration"))
    candidate_rows = report.get("candidate_minimums")
    candidates: dict[int, Mapping[str, Any]] = {}
    candidate_inventory_valid = isinstance(candidate_rows, list)
    if isinstance(candidate_rows, list):
        for row in candidate_rows:
            if not isinstance(row, Mapping) or not isinstance(row.get("minimum_seconds"), int):
                candidate_inventory_valid = False
                continue
            minimum = int(row["minimum_seconds"])
            if minimum in candidates:
                candidate_inventory_valid = False
            candidates[minimum] = row
    selected = candidates.get(rule.decision.final_minimum_seconds, {})
    evidence = rule.decision.evidence

    return [
        _check(
            "analysis-checksum",
            analysis_sha256 == rule.pilot_analysis.sha256,
            "Private duration-analysis bytes match the frozen SHA-256",
            "Private duration-analysis checksum differs from the frozen rule",
        ),
        _check(
            "analysis-schema",
            report.get("schema_version") == rule.pilot_analysis.schema_version,
            "Private duration analysis has the registered schema",
            "Private duration-analysis schema differs from the frozen rule",
        ),
        _check(
            "analysis-frame-binding",
            report.get("frame_id") == rule.frame.frame_id
            and bindings.get("frame_sha256") == rule.frame.frame_sha256,
            "Private duration analysis is bound to the registered sampling frame",
            "Private duration analysis is bound to a different sampling frame",
        ),
        _check(
            "analysis-inventory",
            duration.get("matches") == rule.pilot_analysis.matches
            and report.get("represented_cells") == rule.pilot_analysis.represented_cells,
            "Private duration analysis covers all 5,000 matches and 12 cells",
            "Private duration-analysis inventory differs from the frozen pilot",
        ),
        _check(
            "analysis-input-policy",
            tuple(input_policy.get("fields_used", ())) == DECISION_FIELDS
            and input_policy.get("event_labels_used") is False
            and input_policy.get("model_outputs_used") is False
            and input_policy.get("winner_used") is False,
            "Only duration and surrender metadata informed the rule",
            "Private duration analysis used an unregistered decision input",
        ),
        _check(
            "analysis-identifiers",
            report.get("identifiers_in_summary") is False and not _contains_identifier(report),
            "Private duration analysis contains no match or player identifiers",
            "Private duration analysis contains identifier-like content",
        ),
        _check(
            "analysis-candidate-grid",
            candidate_inventory_valid
            and tuple(candidates) == rule.decision.candidate_minimum_seconds,
            "Private duration analysis contains the complete predeclared candidate grid",
            "Private duration-analysis candidate grid is incomplete or changed",
        ),
        _check(
            "analysis-decision-evidence",
            duration.get("early_surrender_matches") == evidence.early_surrender_matches
            and selected.get("excluded_matches") == evidence.excluded_matches
            and selected.get("excluded_early_surrender_matches")
            == evidence.excluded_early_surrender_matches
            and selected.get("excluded_other_matches") == evidence.excluded_other_matches
            and selected.get("retained_matches") == evidence.retained_matches,
            "Private report exactly supports the frozen 180-second rule",
            "Private duration evidence differs from the committed rule",
        ),
    ]


def validate_duration_rule(
    rule_path: str | Path,
    sampling_frame: str | Path,
    analysis_path: str | Path | None,
) -> dict[str, object]:
    """Validate the public rule and its private, identifier-free pilot evidence."""

    try:
        rule_content, rule = _load_rule_bytes(Path(rule_path))
    except (OSError, ValueError, yaml.YAMLError, ValidationError) as error:
        if isinstance(error, ValidationError):
            reason = _safe_validation_error(error)
        elif isinstance(error, yaml.YAMLError):
            reason = "invalid YAML"
        elif isinstance(error, OSError):
            reason = "missing or unreadable file"
        else:
            reason = str(error)
        check = DurationRuleCheck(
            check_id="rule-schema",
            passed=False,
            message=f"Duration rule rejected: {reason}",
        )
        return {
            "schema_version": DURATION_RULE_VALIDATION_SCHEMA_VERSION,
            "rule_id": None,
            "rule_sha256": None,
            "analysis_sha256": None,
            "passed": False,
            "checks": [asdict(check)],
            "summary": None,
        }

    try:
        frame, frame_sha256 = load_registered_sampling_frame(sampling_frame)
        checks = _contract_checks(rule, frame, frame_sha256)
    except ValueError:
        checks = [
            DurationRuleCheck(
                check_id="sampling-frame",
                passed=False,
                message="Registered sampling frame is missing, invalid or changed",
            )
        ]

    analysis_sha256: str | None = None
    if analysis_path is None:
        checks.append(
            DurationRuleCheck(
                check_id="analysis-file",
                passed=False,
                message="Private pilot duration analysis was not supplied",
            )
        )
    else:
        try:
            analysis_content = Path(analysis_path).read_bytes()
        except OSError:
            checks.append(
                DurationRuleCheck(
                    check_id="analysis-file",
                    passed=False,
                    message="Private pilot duration analysis is missing or unreadable",
                )
            )
        else:
            analysis_sha256 = hashlib.sha256(analysis_content).hexdigest()
            checks.extend(_analysis_checks(rule, analysis_content))

    return {
        "schema_version": DURATION_RULE_VALIDATION_SCHEMA_VERSION,
        "rule_id": rule.rule_id,
        "rule_sha256": hashlib.sha256(rule_content).hexdigest(),
        "analysis_sha256": analysis_sha256,
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
        "summary": {
            "frame_id": rule.frame.frame_id,
            "final_minimum_seconds": rule.decision.final_minimum_seconds,
            "eligibility_expression": "info.gameDuration >= 180",
            "pilot_matches": rule.pilot_analysis.matches,
            "excluded_matches": rule.decision.evidence.excluded_matches,
            "retained_matches": rule.decision.evidence.retained_matches,
            "identifiers_in_summary": False,
        },
    }


def load_registered_duration_rule(
    rule_path: str | Path,
    sampling_frame: str | Path,
    analysis_path: str | Path,
) -> tuple[DurationRule, str]:
    """Load one duration rule only when its public and private bindings pass."""

    report = validate_duration_rule(rule_path, sampling_frame, analysis_path)
    if not report["passed"]:
        raise ValueError("duration rule fails the registered post-pilot contract")
    content, rule = _load_rule_bytes(Path(rule_path))
    return rule, hashlib.sha256(content).hexdigest()
