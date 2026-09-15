from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from league_ews.authority import DISCOVERY_ENDPOINTS, collection_preflight


def _record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": "riot-collection-authority-v1",
        "recorded_on": "2026-09-15",
        "policy_reviewed_on": "2026-09-15",
        "policy_urls": [
            "https://developer.riotgames.com/policies/general",
            "https://developer.riotgames.com/docs/lol",
        ],
        "purpose": "non-commercial-research",
        "player_facing": False,
        "credential_tier": "personal",
        "portal_status": "registered-and-audited",
        "regions": ["europe"],
        "endpoints": ["match-v5.match", "match-v5.timeline"],
        "raw_storage": "private",
        "raw_retention_days": 30,
        "raw_redistribution": "prohibited",
        "derived_redistribution": "not-authorized",
        "identifiers_in_public_artifacts": False,
        "ethics_status": "not-required",
        "authorization_confirmed": True,
    }
    record.update(overrides)
    return record


def _write_record(path: Path, **overrides: object) -> None:
    path.write_text(yaml.safe_dump(_record(**overrides)), encoding="utf-8")


def _failed_checks(report: dict[str, object]) -> set[str]:
    checks = report["checks"]
    assert isinstance(checks, list)
    return {
        str(item["check_id"])
        for item in checks
        if isinstance(item, dict) and item["passed"] is False
    }


def test_preflight_passes_for_scoped_private_research(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(path)

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured-but-never-returned"},
        as_of=date(2026, 9, 15),
    )

    assert report["passed"] is True
    rendered = json.dumps(report)
    assert "configured-but-never-returned" not in rendered
    assert "authorization_confirmed" not in rendered


def test_preflight_fails_without_runtime_key(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(path)

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={},
        as_of=date(2026, 9, 15),
    )

    assert report["passed"] is False
    assert _failed_checks(report) == {"runtime-credential"}


def test_preflight_rejects_stale_policy_and_pending_ethics(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(path, policy_reviewed_on="2026-07-01", ethics_status="pending")

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    assert _failed_checks(report) == {"policy-review-date", "ethics-status"}


def test_collection_requires_registered_and_audited_product(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(path, portal_status="pending")

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    assert "portal-scope" in _failed_checks(report)


def test_production_key_requires_accepted_portal_status(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(
        path,
        credential_tier="production",
        portal_status="registered-and-audited",
    )

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    assert _failed_checks(report) == {"credential-scope"}


def test_preflight_rejects_inconsistent_record_date(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(path, recorded_on="2026-09-14")

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    assert _failed_checks(report) == {"record-date"}


def test_preflight_rejects_region_and_endpoint_scope_mismatch(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(path, regions=["asia"], endpoints=["match-v5.match", "match-v5.match"])

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    assert _failed_checks(report) == {"region-scope", "endpoint-scope"}


def test_preflight_rejects_embedded_credentials_without_echoing_them(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    secret = "".join(("RG", "API-", "do-not-return-this-value"))
    path.write_text(yaml.safe_dump({**_record(), "notes": secret}), encoding="utf-8")

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    rendered = json.dumps(report)
    assert report["passed"] is False
    assert secret not in rendered
    assert "credential" in rendered


def test_preflight_fails_closed_for_missing_or_invalid_record(tmp_path) -> None:
    missing = collection_preflight(
        tmp_path / "missing.yaml",
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )
    assert missing["passed"] is False

    invalid_path = tmp_path / "invalid.yaml"
    invalid_path.write_text("schema_version: wrong\n", encoding="utf-8")
    invalid = collection_preflight(
        invalid_path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )
    assert invalid["passed"] is False
    assert "wrong" not in json.dumps(invalid)


def test_invalid_yaml_is_rejected_without_echoing_source(tmp_path) -> None:
    path = tmp_path / "invalid.yaml"
    sensitive_source = "private-value-that-must-not-be-returned"
    path.write_text(f"purpose: [{sensitive_source}\n", encoding="utf-8")

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    rendered = json.dumps(report)
    assert report["passed"] is False
    assert sensitive_source not in rendered
    assert "invalid YAML" in rendered


def test_v2_preflight_requires_all_discovery_routes_and_endpoints(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(
        path,
        schema_version="riot-collection-authority-v2",
        regions=["europe", "americas"],
        endpoints=sorted(DISCOVERY_ENDPOINTS),
    )

    report = collection_preflight(
        path,
        requested_regions=("europe", "americas"),
        required_endpoints=DISCOVERY_ENDPOINTS,
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    assert report["passed"] is True
    assert report["requested_region"] is None
    assert report["requested_regions"] == ["europe", "americas"]


def test_v1_record_cannot_claim_discovery_endpoints(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(path, endpoints=sorted(DISCOVERY_ENDPOINTS))

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    assert report["passed"] is False
    assert _failed_checks(report) == {"record-schema"}


def test_v2_record_rejects_duplicate_scope(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(
        path,
        schema_version="riot-collection-authority-v2",
        regions=["europe", "europe"],
    )

    report = collection_preflight(
        path,
        requested_region="europe",
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )

    assert report["passed"] is False
    assert _failed_checks(report) == {"record-schema"}


def test_preflight_rejects_ambiguous_or_unknown_requested_scope(tmp_path) -> None:
    path = tmp_path / "authority.yaml"
    _write_record(path)

    with pytest.raises(ValueError, match="either"):
        collection_preflight(
            path,
            requested_region="europe",
            requested_regions=("europe",),
        )
    with pytest.raises(ValueError, match="endpoint"):
        collection_preflight(
            path,
            requested_region="europe",
            required_endpoints=("unknown-v1.endpoint",),
        )
