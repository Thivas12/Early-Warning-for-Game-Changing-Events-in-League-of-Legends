from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

import league_ews.final_discovery as final_discovery
from league_ews.final_discovery import (
    FinalDiscoveryContext,
    discover_final_candidate_pool,
    final_candidate_discovery_preflight,
    load_registered_final_discovery_plan,
    validate_final_candidate_pool,
    validate_final_discovery_plan,
)
from league_ews.pilot_collection import FrozenPilotSelection, FrozenSelectedMatch
from league_ews.sampling import SamplingCell, load_registered_sampling_frame, sampling_cells

ROOT = Path(__file__).parents[1]
FRAME = ROOT / "configs" / "rifthazard-sampling-frame.yaml"
PLAN = ROOT / "configs" / "rifthazard-final-discovery-plan.yaml"
PATCHES = tuple(f"16.{minor}" for minor in range(12, 18))


class FakePlatformFetcher:
    def __init__(self, platform_id: str, *, fail: bool = False) -> None:
        self.platform_id = platform_id
        self.fail = fail
        self.ladder_calls: list[str] = []
        self.resolution_calls = 0

    def get_top_league(self, tier: str, *, queue: str = "RANKED_SOLO_5x5") -> dict[str, Any]:
        if self.fail:
            raise AssertionError("completed resume contacted a platform endpoint")
        assert queue == "RANKED_SOLO_5x5"
        self.ladder_calls.append(tier)
        return {
            "entries": [{"summonerId": f"{self.platform_id}-{tier}-{index}"} for index in range(12)]
        }

    def get_summoner_by_id(self, summoner_id: str) -> dict[str, str]:
        if self.fail:
            raise AssertionError("completed resume resolved a player")
        self.resolution_calls += 1
        return {"puuid": f"puuid-{summoner_id}"}


class FakeRegionalFetcher:
    def __init__(self, platform_id: str, pilot_id: str, *, fail: bool = False) -> None:
        self.platform_id = platform_id
        self.pilot_id = pilot_id
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
            raise AssertionError("completed resume contacted Match-V5 history")
        assert end_time > start_time
        assert (queue_id, start, count) == (420, 0, 100)
        self.calls += 1
        identifiers = [self.pilot_id]
        for index in range(5):
            material = f"{puuid}:{start_time}:{index}".encode()
            numeric = int(hashlib.sha256(material).hexdigest()[:15], 16)
            identifiers.append(f"{self.platform_id}_{numeric}")
        return tuple(identifiers)


def _small_cells() -> tuple[SamplingCell, ...]:
    frame, _ = load_registered_sampling_frame(FRAME)
    return tuple(replace(cell, final_target=2) for cell in sampling_cells(frame))


def _frozen_match(match_id: str, route: str, platform: str) -> FrozenSelectedMatch:
    return FrozenSelectedMatch(
        match_id=match_id,
        regional_route=route,  # type: ignore[arg-type]
        platform_id=platform,
        game_version_patch=PATCHES[0],
        candidate_rank_sha256="a" * 64,
        screen_record_sha256="b" * 64,
        match_payload_sha256="c" * 64,
        game_version="16.12.1",
        game_creation_ms=1,
        screen_record_path=Path("private.json"),
    )


def _context() -> FinalDiscoveryContext:
    frame, frame_sha256 = load_registered_sampling_frame(FRAME)
    plan, plan_sha256 = load_registered_final_discovery_plan(
        PLAN,
        frame=frame,
        frame_sha256=frame_sha256,
    )
    pilot = FrozenPilotSelection(
        frame=frame,
        frame_sha256=frame_sha256,
        plan_id=plan.pilot_selection.discovery_plan_id,
        plan_sha256=plan.pilot_selection.discovery_plan_sha256,
        discovery_manifest_sha256=plan.pilot_selection.discovery_manifest_sha256,
        candidate_pool_sha256=plan.pilot_selection.candidate_pool_sha256,
        selected_pool_sha256=plan.pilot_selection.selected_pool_sha256,
        selected_matches=(
            _frozen_match("EUW1_999", "europe", "EUW1"),
            _frozen_match("NA1_888", "americas", "NA1"),
        ),
    )
    return FinalDiscoveryContext(frame, frame_sha256, plan, plan_sha256, pilot)


def test_registered_final_discovery_plan_is_frozen() -> None:
    report = validate_final_discovery_plan(PLAN, FRAME)

    assert report["passed"] is True
    assert report["plan_id"] == "rifthazard-final-discovery-2026-09-20"
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["pilot_match_ids_excluded"] == 5_000
    assert summary["max_players_per_platform"] == 512
    cells = summary["minimum_candidates_per_cell"]
    assert isinstance(cells, list)
    assert len(cells) == 12
    assert {cell["minimum_candidates"] for cell in cells} == {6_000}


def test_final_discovery_plan_rejects_duration_checksum_drift(tmp_path) -> None:
    payload = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    payload["duration_rule"]["analysis_sha256"] = "0" * 64
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = validate_final_discovery_plan(path, FRAME)

    assert report["passed"] is False
    failed = {check["check_id"] for check in report["checks"] if not check["passed"]}
    assert failed == {"duration-rule-binding"}


def test_final_preflight_fails_closed_before_authority_check(tmp_path) -> None:
    report = final_candidate_discovery_preflight(
        tmp_path / "authority.yaml",
        FRAME,
        PLAN,
        tmp_path / "duration-rule.yaml",
        tmp_path / "duration-analysis.json",
        tmp_path / "pilot-plan.yaml",
        tmp_path / "pilot-discovery",
        tmp_path / "pilot-selection",
    )

    assert report["passed"] is False
    assert report["authority"] is None
    assert report["bindings"]["passed"] is False
    assert "EUW1_" not in json.dumps(report)


def test_final_candidate_discovery_excludes_pilot_and_resumes(
    tmp_path,
    monkeypatch,
) -> None:
    context = _context()
    output = tmp_path / "final-discovery"
    monkeypatch.setattr(final_discovery, "_load_context", lambda *args: context)
    monkeypatch.setattr(final_discovery, "sampling_cells", lambda frame: _small_cells())

    euw_platform = FakePlatformFetcher("EUW1")
    na_platform = FakePlatformFetcher("NA1")
    europe = FakeRegionalFetcher("EUW1", "EUW1_999")
    americas = FakeRegionalFetcher("NA1", "NA1_888")
    progress: list[str] = []
    manifest = discover_final_candidate_pool(
        FRAME,
        PLAN,
        Path("duration-rule.yaml"),
        Path("duration-analysis.json"),
        Path("pilot-plan.yaml"),
        tmp_path / "pilot-discovery",
        tmp_path / "pilot-selection",
        output_root=output,
        platform_fetchers={"EUW1": euw_platform, "NA1": na_platform},
        regional_fetchers={"europe": europe, "americas": americas},
        discovered_at=datetime(2026, 9, 20, 17, tzinfo=UTC),
        progress=progress.append,
    )

    assert manifest["complete"] is True
    assert manifest["players_processed_per_platform"] == 32
    assert manifest["balanced_waves_completed"] == 1
    assert manifest["resolution_files"] == 64
    assert manifest["history_page_files"] == 384
    assert manifest["candidate_match_ids"] == 1_920
    assert manifest["excluded_pilot_match_ids_discovered"] == 2
    assert "EUW1_" not in json.dumps(manifest)
    assert "puuid-" not in json.dumps(manifest)
    assert progress[-1].endswith("12/12 cells meet the 2x buffer")

    pool_text = (output / "candidate-pool.json").read_text(encoding="utf-8")
    pool = json.loads(pool_text)
    assert pool["contains_player_identifiers"] is False
    candidate_ids = {match_id for cell in pool["cells"] for match_id in cell["match_ids"]}
    assert "EUW1_999" not in candidate_ids
    assert "NA1_888" not in candidate_ids
    assert {cell["minimum_candidates"] for cell in pool["cells"]} == {4}

    validation = validate_final_candidate_pool(
        FRAME,
        PLAN,
        Path("duration-rule.yaml"),
        Path("duration-analysis.json"),
        Path("pilot-plan.yaml"),
        tmp_path / "pilot-discovery",
        tmp_path / "pilot-selection",
        output,
    )
    assert validation["passed"] is True
    assert validation["summary"]["candidate_match_ids"] == 1_920
    assert "EUW1_" not in json.dumps(validation)

    resumed = discover_final_candidate_pool(
        FRAME,
        PLAN,
        Path("duration-rule.yaml"),
        Path("duration-analysis.json"),
        Path("pilot-plan.yaml"),
        tmp_path / "pilot-discovery",
        tmp_path / "pilot-selection",
        output_root=output,
        platform_fetchers={
            "EUW1": FakePlatformFetcher("EUW1", fail=True),
            "NA1": FakePlatformFetcher("NA1", fail=True),
        },
        regional_fetchers={
            "europe": FakeRegionalFetcher("EUW1", "EUW1_999", fail=True),
            "americas": FakeRegionalFetcher("NA1", "NA1_888", fail=True),
        },
        discovered_at=datetime(2026, 9, 20, 18, tzinfo=UTC),
    )
    assert resumed["candidate_pool_sha256"] == manifest["candidate_pool_sha256"]
    assert resumed["complete"] is True

    history = next((output / "histories").rglob("*.json"))
    history.write_bytes(history.read_bytes() + b" ")
    rejected = validate_final_candidate_pool(
        FRAME,
        PLAN,
        Path("duration-rule.yaml"),
        Path("duration-analysis.json"),
        Path("pilot-plan.yaml"),
        tmp_path / "pilot-discovery",
        tmp_path / "pilot-selection",
        output,
    )
    assert rejected["passed"] is False
    assert "EUW1_" not in json.dumps(rejected)


def test_final_discovery_rejects_unsafe_output_and_timestamp(tmp_path, monkeypatch) -> None:
    context = _context()
    monkeypatch.setattr(final_discovery, "_load_context", lambda *args: context)
    fetchers = {
        "EUW1": FakePlatformFetcher("EUW1"),
        "NA1": FakePlatformFetcher("NA1"),
    }
    regional = {
        "europe": FakeRegionalFetcher("EUW1", "EUW1_999"),
        "americas": FakeRegionalFetcher("NA1", "NA1_888"),
    }
    pilot_root = tmp_path / "pilot-discovery"

    with pytest.raises(ValueError, match="timezone-aware"):
        discover_final_candidate_pool(
            FRAME,
            PLAN,
            Path("duration-rule.yaml"),
            Path("duration-analysis.json"),
            Path("pilot-plan.yaml"),
            pilot_root,
            tmp_path / "pilot-selection",
            output_root=tmp_path / "output",
            platform_fetchers=fetchers,
            regional_fetchers=regional,
            discovered_at=datetime(2026, 9, 20),
        )

    with pytest.raises(ValueError, match="separate from pilot"):
        discover_final_candidate_pool(
            FRAME,
            PLAN,
            Path("duration-rule.yaml"),
            Path("duration-analysis.json"),
            Path("pilot-plan.yaml"),
            pilot_root,
            tmp_path / "pilot-selection",
            output_root=pilot_root / "final",
            platform_fetchers=fetchers,
            regional_fetchers=regional,
        )
