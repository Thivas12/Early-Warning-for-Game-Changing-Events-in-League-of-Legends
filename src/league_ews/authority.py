"""Fail-closed authorization preflight for private Riot research collection."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

AUTHORITY_SCHEMA_VERSION = "riot-collection-authority-v1"
PREFLIGHT_SCHEMA_VERSION = "riot-collection-preflight-v1"
GENERAL_POLICY_URL = "https://developer.riotgames.com/policies/general"
LOL_POLICY_URL = "https://developer.riotgames.com/docs/lol"
REQUIRED_POLICY_URLS = frozenset({GENERAL_POLICY_URL, LOL_POLICY_URL})
REQUIRED_ENDPOINTS = frozenset({"match-v5.match", "match-v5.timeline"})
MAX_POLICY_AGE_DAYS = 30
SECRET_PATTERN = re.compile(r"RGAPI-[A-Za-z0-9_-]+", re.IGNORECASE)
SENSITIVE_KEYS = frozenset(
    {"api_key", "riot_api_key", "password", "secret", "token", "access_token"}
)

Region = Literal["americas", "asia", "europe", "sea"]


class AuthorityRecord(BaseModel):
    """Private attestation required before the collector can be invoked."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["riot-collection-authority-v1"]
    recorded_on: date
    policy_reviewed_on: date
    policy_urls: tuple[str, ...] = Field(min_length=2)
    purpose: Literal["non-commercial-research"]
    player_facing: bool
    credential_tier: Literal["personal", "production"]
    portal_status: Literal["pending", "registered-and-audited", "approved", "acknowledged"]
    regions: tuple[Region, ...] = Field(min_length=1)
    endpoints: tuple[Literal["match-v5.match", "match-v5.timeline"], ...] = Field(min_length=2)
    raw_storage: Literal["private"]
    raw_retention_days: int = Field(gt=0, le=90)
    raw_redistribution: Literal["prohibited"]
    derived_redistribution: Literal["not-authorized"]
    identifiers_in_public_artifacts: Literal[False]
    ethics_status: Literal["not-required", "approved", "pending"]
    authorization_confirmed: bool


@dataclass(frozen=True)
class AuthorityCheck:
    check_id: str
    passed: bool
    message: str


def _safe_validation_error(error: ValidationError) -> str:
    issues = []
    for item in error.errors(include_input=False, include_context=False):
        location = ".".join(str(part) for part in item["loc"]) or "record"
        issues.append(f"{location}: {item['type']}")
    return "; ".join(issues)


def _contains_sensitive_key(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in SENSITIVE_KEYS:
                return True
            if _contains_sensitive_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _load_record(path: Path) -> AuthorityRecord:
    rendered = path.read_text(encoding="utf-8")
    if SECRET_PATTERN.search(rendered):
        raise ValueError("authority record contains a Riot credential")
    payload = yaml.safe_load(rendered)
    if not isinstance(payload, Mapping):
        raise ValueError("authority record must contain a mapping")
    if _contains_sensitive_key(payload):
        raise ValueError("authority record contains a secret-bearing field")
    return AuthorityRecord.model_validate(payload)


def _check(check_id: str, passed: bool, success: str, failure: str) -> AuthorityCheck:
    return AuthorityCheck(
        check_id=check_id,
        passed=passed,
        message=success if passed else failure,
    )


def collection_preflight(
    record_path: str | Path,
    *,
    requested_region: str,
    environment: Mapping[str, str] | None = None,
    as_of: date | None = None,
) -> dict[str, object]:
    """Evaluate collection authority without contacting Riot or exposing credentials."""

    if requested_region not in {"americas", "asia", "europe", "sea"}:
        raise ValueError(f"Unsupported regional route: {requested_region}")

    record_file = Path(record_path)
    checked_on = as_of or datetime.now(UTC).date()
    checks: list[AuthorityCheck] = []
    try:
        record = _load_record(record_file)
    except (OSError, ValueError, yaml.YAMLError, ValidationError) as error:
        if isinstance(error, ValidationError):
            reason = _safe_validation_error(error)
        elif isinstance(error, yaml.YAMLError):
            reason = "authority record contains invalid YAML"
        elif isinstance(error, OSError):
            reason = "authority record is missing or unreadable"
        else:
            reason = str(error)
        checks.append(
            AuthorityCheck(
                check_id="record-schema",
                passed=False,
                message=f"Private authority record rejected: {reason}",
            )
        )
        return {
            "schema_version": PREFLIGHT_SCHEMA_VERSION,
            "checked_on": checked_on.isoformat(),
            "requested_region": requested_region,
            "passed": False,
            "record": None,
            "checks": [asdict(item) for item in checks],
        }

    checks.append(
        AuthorityCheck(
            check_id="record-schema",
            passed=True,
            message=f"Authority record conforms to {AUTHORITY_SCHEMA_VERSION}",
        )
    )

    record_date_valid = record.policy_reviewed_on <= record.recorded_on <= checked_on
    checks.append(
        _check(
            "record-date",
            record_date_valid,
            "Authority record date is consistent with its policy review",
            "Authority record must follow its policy review and cannot be future-dated",
        )
    )

    policy_age = (checked_on - record.policy_reviewed_on).days
    checks.append(
        _check(
            "policy-review-date",
            0 <= policy_age <= MAX_POLICY_AGE_DAYS,
            f"Policy review is {policy_age} days old",
            "Policy review must not be future-dated or older than 30 days",
        )
    )
    checks.append(
        _check(
            "policy-sources",
            REQUIRED_POLICY_URLS.issubset(record.policy_urls),
            "Required Riot policy pages were recorded",
            "Both the Riot general and League policy URLs must be reviewed",
        )
    )

    portal_allowed = record.portal_status in {
        "registered-and-audited",
        "approved",
        "acknowledged",
    }
    checks.append(
        _check(
            "portal-scope",
            portal_allowed,
            "Product registration and audit are confirmed",
            "Riot product registration and audit must be confirmed before collection",
        )
    )
    checks.append(
        _check(
            "credential-scope",
            record.credential_tier == "personal"
            or record.portal_status in {"approved", "acknowledged"},
            "Credential tier is consistent with the declared portal status",
            "A production credential requires Approved or Acknowledged portal status",
        )
    )
    checks.append(
        _check(
            "region-scope",
            requested_region in record.regions,
            f"Regional route {requested_region} is explicitly authorized",
            f"Regional route {requested_region} is absent from the authority record",
        )
    )
    checks.append(
        _check(
            "endpoint-scope",
            REQUIRED_ENDPOINTS.issubset(record.endpoints),
            "Match detail and timeline endpoints are explicitly scoped",
            "Both Match-V5 detail and timeline endpoints must be scoped",
        )
    )
    checks.append(
        _check(
            "ethics-status",
            record.ethics_status in {"not-required", "approved"},
            f"Ethics status is {record.ethics_status}",
            "Collection is blocked while ethics status is pending",
        )
    )
    checks.append(
        _check(
            "authorization-attestation",
            record.authorization_confirmed,
            "The researcher explicitly confirmed collection authority",
            "The researcher has not confirmed collection authority",
        )
    )

    configured_environment = os.environ if environment is None else environment
    key_configured = bool(configured_environment.get("RIOT_API_KEY", "").strip())
    checks.append(
        _check(
            "runtime-credential",
            key_configured,
            "RIOT_API_KEY is configured in the runtime environment",
            "RIOT_API_KEY is not configured in the runtime environment",
        )
    )

    passed = all(item.passed for item in checks)
    safe_record = {
        "schema_version": record.schema_version,
        "recorded_on": record.recorded_on.isoformat(),
        "policy_reviewed_on": record.policy_reviewed_on.isoformat(),
        "purpose": record.purpose,
        "player_facing": record.player_facing,
        "credential_tier": record.credential_tier,
        "portal_status": record.portal_status,
        "regions": list(record.regions),
        "endpoints": list(record.endpoints),
        "raw_storage": record.raw_storage,
        "raw_retention_days": record.raw_retention_days,
        "raw_redistribution": record.raw_redistribution,
        "derived_redistribution": record.derived_redistribution,
        "identifiers_in_public_artifacts": record.identifiers_in_public_artifacts,
        "ethics_status": record.ethics_status,
    }
    return {
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "checked_on": checked_on.isoformat(),
        "requested_region": requested_region,
        "passed": passed,
        "record": safe_record,
        "checks": [asdict(item) for item in checks],
    }
