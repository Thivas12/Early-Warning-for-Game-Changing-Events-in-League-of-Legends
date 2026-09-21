from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from league_ews.discovery import (
    candidate_discovery_preflight,
    discover_candidate_pool,
    validate_discovery_plan,
)

ROOT = Path(__file__).parents[1]
FRAME = ROOT / "configs" / "rifthazard-sampling-frame.yaml"
PLAN = ROOT / "configs" / "rifthazard-discovery-plan.yaml"


def _authority(*, schema_version: str = "riot-collection-authority-v2") -> dict[str, object]:
    endpoints = [
        "league-v4.challenger",
        "league-v4.grandmaster",
        "league-v4.master",
        "summoner-v4.by-summoner-id",
        "match-v5.ids-by-puuid",
        "match-v5.match",
        "match-v5.timeline",
    ]
    if schema_version == "riot-collection-authority-v1":
        endpoints = ["match-v5.match", "match-v5.timeline"]
    return {
        "schema_version": schema_version,
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
        "regions": ["europe", "americas"],
        "endpoints": endpoints,
        "raw_storage": "private",
        "raw_retention_days": 30,
        "raw_redistribution": "prohibited",
        "derived_redistribution": "not-authorized",
        "identifiers_in_public_artifacts": False,
        "ethics_status": "not-required",
        "authorization_confirmed": True,
    }


class FakePlatformFetcher:
    def __init__(self, platform_id: str, *, fail: bool = False) -> None:
        self.platform_id = platform_id
        self.fail = fail
        self.ladder_calls: list[str] = []
        self.resolution_calls = 0

    def get_top_league(self, tier: str, *, queue: str = "RANKED_SOLO_5x5") -> dict[str, Any]:
        if self.fail:
            raise AssertionError("resume unexpectedly contacted a platform endpoint")
        assert queue == "RANKED_SOLO_5x5"
        self.ladder_calls.append(tier)
        return {
            "entries": [{"summonerId": f"{self.platform_id}-{tier}-{index}"} for index in range(12)]
        }

    def get_summoner_by_id(self, summoner_id: str) -> dict[str, str]:
        if self.fail:
            raise AssertionError("resume unexpectedly resolved a player")
        self.resolution_calls += 1
        return {"puuid": f"puuid-{summoner_id}"}


class FakeRegionalFetcher:
    def __init__(
        self,
        platform_id: str,
        *,
        foreign_platform_id: str | None = None,
        malformed_match_id: bool = False,
        fail: bool = False,
    ) -> None:
        self.platform_id = platform_id
        self.foreign_platform_id = foreign_platform_id
        self.malformed_match_id = malformed_match_id
        self.fail = fail
        self.calls = 0

    def get_match_ids_by_puuid(
        self,
        puuid: str,
        *,
        start_time: int,
        end_time: int,
        queue_id: int,
        start: int = 0,
        count: int = 100,
    ) -> tuple[str, ...]:
        if self.fail:
            raise AssertionError("resume unexpectedly contacted Match-V5 history")
        assert end_time > start_time
        assert (queue_id, start, count) == (420, 0, 100)
        self.calls += 1
        identifiers = []
        for index in range(30):
            material = f"{puuid}:{start_time}:{index}".encode()
            numeric = int(hashlib.sha256(material).hexdigest()[:15], 16)
            identifiers.append(f"{self.platform_id}_{numeric}")
        if self.foreign_platform_id is not None:
            material = f"foreign:{puuid}:{start_time}".encode()
            numeric = int(hashlib.sha256(material).hexdigest()[:15], 16)
            identifiers.append(f"{self.foreign_platform_id}_{numeric}")
        if self.malformed_match_id:
            identifiers.append("not-a-match-id")
        return tuple(identifiers)


def test_registered_discovery_plan_is_frame_bound() -> None:
    report = validate_discovery_plan(PLAN, FRAME)

    assert report["passed"] is True
    assert report["sampling_frame_sha256"] == (
        "2355ec26182aa6862e8a110ff94f0ab402e9a4e77c0a52a0a5c81f1892033f6b"
    )
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["history_requests_per_wave"] == 384
    cells = summary["minimum_candidates_per_cell"]
    assert isinstance(cells, list)
    assert {cell["minimum_candidates"] for cell in cells} == {832, 834}


def test_discovery_plan_rejects_frame_checksum_drift(tmp_path) -> None:
    payload = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    payload["sampling_frame"]["sha256"] = "0" * 64
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = validate_discovery_plan(path, FRAME)

    assert report["passed"] is False
    checks = report["checks"]
    assert isinstance(checks, list)
    assert {check["check_id"] for check in checks if not check["passed"]} == {
        "sampling-frame-binding"
    }


def test_discovery_preflight_requires_v2_scope(tmp_path) -> None:
    record = tmp_path / "authority.yaml"
    record.write_text(yaml.safe_dump(_authority()), encoding="utf-8")

    passed = candidate_discovery_preflight(
        record,
        FRAME,
        PLAN,
        environment={"RIOT_API_KEY": "configured-not-returned"},
        as_of=date(2026, 9, 15),
    )
    assert passed["passed"] is True
    assert "configured-not-returned" not in json.dumps(passed)

    record.write_text(
        yaml.safe_dump(_authority(schema_version="riot-collection-authority-v1")),
        encoding="utf-8",
    )
    failed = candidate_discovery_preflight(
        record,
        FRAME,
        PLAN,
        environment={"RIOT_API_KEY": "configured"},
        as_of=date(2026, 9, 15),
    )
    assert failed["passed"] is False
    authority = failed["authority"]
    assert isinstance(authority, dict)
    checks = authority["checks"]
    assert isinstance(checks, list)
    assert {check["check_id"] for check in checks if not check["passed"]} == {"endpoint-scope"}


def test_candidate_discovery_is_balanced_private_and_resumable(tmp_path) -> None:
    euw_platform = FakePlatformFetcher("EUW1")
    na_platform = FakePlatformFetcher("NA1")
    europe = FakeRegionalFetcher("EUW1", foreign_platform_id="NA1")
    americas = FakeRegionalFetcher("NA1", foreign_platform_id="EUW1")
    progress: list[str] = []

    manifest = discover_candidate_pool(
        FRAME,
        PLAN,
        output_root=tmp_path,
        platform_fetchers={"EUW1": euw_platform, "NA1": na_platform},
        regional_fetchers={"europe": europe, "americas": americas},
        discovered_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
        progress=progress.append,
    )

    assert manifest["complete"] is True
    assert manifest["players_processed_per_platform"] == 32
    assert manifest["balanced_waves_completed"] == 1
    assert manifest["resolution_files"] == 64
    assert manifest["history_page_files"] == 384
    assert manifest["candidate_match_ids"] == 11_520
    assert euw_platform.ladder_calls == ["CHALLENGER", "GRANDMASTER", "MASTER"]
    assert na_platform.ladder_calls == ["CHALLENGER", "GRANDMASTER", "MASTER"]
    assert euw_platform.resolution_calls == na_platform.resolution_calls == 32
    assert europe.calls == americas.calls == 192
    assert progress[-1].endswith("12/12 candidate windows meet their buffer")
    assert "EUW1_" not in json.dumps(manifest)
    assert "puuid-" not in json.dumps(manifest)
    assert (tmp_path / "ladder-snapshot.json").is_file()
    assert (tmp_path / "candidate-pool.json").is_file()
    assert (tmp_path / "discovery-manifest.json").is_file()
    assert not list(tmp_path.rglob("*.partial"))
    for platform_id in ("EUW1", "NA1"):
        for path in (tmp_path / "histories" / platform_id).rglob("*.json"):
            history = json.loads(path.read_text(encoding="utf-8"))
            assert all(match_id.startswith(f"{platform_id}_") for match_id in history["match_ids"])

    resumed = discover_candidate_pool(
        FRAME,
        PLAN,
        output_root=tmp_path,
        platform_fetchers={
            "EUW1": FakePlatformFetcher("EUW1", fail=True),
            "NA1": FakePlatformFetcher("NA1", fail=True),
        },
        regional_fetchers={
            "europe": FakeRegionalFetcher("EUW1", fail=True),
            "americas": FakeRegionalFetcher("NA1", fail=True),
        },
        discovered_at=datetime(2026, 9, 15, 13, tzinfo=UTC),
    )
    assert resumed["candidate_pool_sha256"] == manifest["candidate_pool_sha256"]
    assert resumed["complete"] is True

    resolution = next((tmp_path / "resolutions" / "EUW1").glob("*.json"))
    (resolution.parent / f"{'0' * 64}.json").write_bytes(resolution.read_bytes())
    with pytest.raises(ValueError, match="cache inventory"):
        discover_candidate_pool(
            FRAME,
            PLAN,
            output_root=tmp_path,
            platform_fetchers={
                "EUW1": FakePlatformFetcher("EUW1", fail=True),
                "NA1": FakePlatformFetcher("NA1", fail=True),
            },
            regional_fetchers={
                "europe": FakeRegionalFetcher("EUW1", fail=True),
                "americas": FakeRegionalFetcher("NA1", fail=True),
            },
        )


def test_discovery_rejects_partial_state_and_naive_timestamp(tmp_path) -> None:
    platform_fetchers = {
        "EUW1": FakePlatformFetcher("EUW1"),
        "NA1": FakePlatformFetcher("NA1"),
    }
    regional_fetchers = {
        "europe": FakeRegionalFetcher("EUW1"),
        "americas": FakeRegionalFetcher("NA1"),
    }
    with pytest.raises(ValueError, match="timezone-aware"):
        discover_candidate_pool(
            FRAME,
            PLAN,
            output_root=tmp_path,
            platform_fetchers=platform_fetchers,
            regional_fetchers=regional_fetchers,
            discovered_at=datetime(2026, 9, 15),
        )

    partial = tmp_path / "state.json.partial"
    partial.write_text("partial", encoding="utf-8")
    with pytest.raises(ValueError, match="partial"):
        discover_candidate_pool(
            FRAME,
            PLAN,
            output_root=tmp_path,
            platform_fetchers=platform_fetchers,
            regional_fetchers=regional_fetchers,
        )


def test_discovery_rejects_malformed_history_match_id(tmp_path) -> None:
    with pytest.raises(ValueError, match="malformed match ID"):
        discover_candidate_pool(
            FRAME,
            PLAN,
            output_root=tmp_path,
            platform_fetchers={
                "EUW1": FakePlatformFetcher("EUW1"),
                "NA1": FakePlatformFetcher("NA1"),
            },
            regional_fetchers={
                "europe": FakeRegionalFetcher("EUW1", malformed_match_id=True),
                "americas": FakeRegionalFetcher("NA1"),
            },
            discovered_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
        )
