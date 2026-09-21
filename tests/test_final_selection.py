from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

import league_ews.final_selection as final_selection
from league_ews.final_discovery import (
    FinalCandidatePool,
    FinalCandidatePoolCell,
    FinalCandidateWindowSummary,
    FinalDiscoveryContext,
    FinalDiscoveryManifest,
    load_registered_final_discovery_plan,
)
from league_ews.final_selection import (
    BoundFinalCandidatePool,
    final_selection_preflight,
    load_registered_final_selection_plan,
    select_final_matches,
    validate_final_selection_plan,
    validate_frozen_final_selection,
)
from league_ews.pilot_collection import FrozenPilotSelection, FrozenSelectedMatch
from league_ews.sampling import (
    SamplingCell,
    load_registered_sampling_frame,
    order_candidate_match_ids,
    sampling_cells,
)
from league_ews.selection import CandidateReference

ROOT = Path(__file__).parents[1]
FRAME = ROOT / "configs" / "rifthazard-sampling-frame.yaml"
DISCOVERY_PLAN = ROOT / "configs" / "rifthazard-final-discovery-plan.yaml"
SELECTION_PLAN = ROOT / "configs" / "rifthazard-final-selection-plan.yaml"
DURATION_RULE = ROOT / "configs" / "rifthazard-duration-rule.yaml"


def _small_cells() -> tuple[SamplingCell, ...]:
    frame, _ = load_registered_sampling_frame(FRAME)
    return tuple(replace(cell, final_target=1) for cell in sampling_cells(frame))


def _pilot_match(match_id: str, route: str, platform: str) -> FrozenSelectedMatch:
    return FrozenSelectedMatch(
        match_id=match_id,
        regional_route=route,  # type: ignore[arg-type]
        platform_id=platform,
        game_version_patch="16.12",
        candidate_rank_sha256="1" * 64,
        screen_record_sha256="2" * 64,
        match_payload_sha256="3" * 64,
        game_version="16.12.1",
        game_creation_ms=1,
        screen_record_path=Path("private.json"),
    )


def _bound() -> tuple[BoundFinalCandidatePool, dict[str, str]]:
    frame, frame_sha256 = load_registered_sampling_frame(FRAME)
    discovery_plan, discovery_plan_sha256 = load_registered_final_discovery_plan(
        DISCOVERY_PLAN,
        frame=frame,
        frame_sha256=frame_sha256,
    )
    selection_plan, selection_plan_sha256 = load_registered_final_selection_plan(
        SELECTION_PLAN,
        FRAME,
        DISCOVERY_PLAN,
        DURATION_RULE,
    )
    pilot = FrozenPilotSelection(
        frame=frame,
        frame_sha256=frame_sha256,
        plan_id=discovery_plan.pilot_selection.discovery_plan_id,
        plan_sha256=discovery_plan.pilot_selection.discovery_plan_sha256,
        discovery_manifest_sha256=(discovery_plan.pilot_selection.discovery_manifest_sha256),
        candidate_pool_sha256=discovery_plan.pilot_selection.candidate_pool_sha256,
        selected_pool_sha256=discovery_plan.pilot_selection.selected_pool_sha256,
        selected_matches=(
            _pilot_match("EUW1_99000001", "europe", "EUW1"),
            _pilot_match("NA1_99000002", "americas", "NA1"),
        ),
    )
    context = FinalDiscoveryContext(
        frame,
        frame_sha256,
        discovery_plan,
        discovery_plan_sha256,
        pilot,
    )

    pool_cells: list[FinalCandidatePoolCell] = []
    summaries: list[FinalCandidateWindowSummary] = []
    references: list[CandidateReference] = []
    patches_by_id: dict[str, str] = {}
    for cell_index, cell in enumerate(sampling_cells(frame)):
        identifiers = tuple(
            f"{cell.platform_id}_{cell_index * 100_000 + index + 1}" for index in range(10)
        )
        ordered = order_candidate_match_ids(frame, identifiers)
        pool_cells.append(
            FinalCandidatePoolCell(
                regional_route=cell.regional_route,
                platform_id=cell.platform_id,
                game_version_patch=cell.game_version_patch,
                minimum_candidates=6,
                candidate_count=len(ordered),
                excluded_pilot_matches_discovered=0,
                minimum_met=True,
                match_ids=ordered,
            )
        )
        summaries.append(
            FinalCandidateWindowSummary(
                regional_route=cell.regional_route,
                platform_id=cell.platform_id,
                game_version_patch=cell.game_version_patch,
                minimum_candidates=6,
                candidate_count=len(ordered),
                excluded_pilot_matches_discovered=0,
                minimum_met=True,
            )
        )
        for match_id in ordered:
            references.append(CandidateReference(match_id, cell.regional_route, cell.platform_id))
            patches_by_id[match_id] = cell.game_version_patch

    by_id = {reference.match_id: reference for reference in references}
    ordered_ids = order_candidate_match_ids(frame, tuple(by_id))
    candidate_pool_sha256 = "4" * 64
    manifest_sha256 = "5" * 64
    pool = FinalCandidatePool(
        schema_version="riot-final-candidate-pool-v1",
        stage="final",
        frame_id=frame.frame_id,
        frame_sha256=frame_sha256,
        plan_id=discovery_plan.plan_id,
        plan_sha256=discovery_plan_sha256,
        duration_rule_sha256=discovery_plan.duration_rule.rule_sha256,
        pilot_selected_pool_sha256=pilot.selected_pool_sha256,
        snapshot_sha256="6" * 64,
        complete=True,
        globally_deduplicated=True,
        excluded_pilot_match_ids_discovered=0,
        cells=tuple(pool_cells),
        contains_match_identifiers=True,
        contains_player_identifiers=False,
        redistribution="not-authorized",
    )
    manifest = FinalDiscoveryManifest(
        schema_version="riot-final-candidate-discovery-manifest-v1",
        completed_at=datetime(2026, 9, 21, tzinfo=UTC),
        complete=True,
        frame_id=frame.frame_id,
        frame_sha256=frame_sha256,
        plan_id=discovery_plan.plan_id,
        plan_sha256=discovery_plan_sha256,
        duration_rule_sha256=discovery_plan.duration_rule.rule_sha256,
        duration_analysis_sha256=discovery_plan.duration_rule.analysis_sha256,
        pilot_selected_pool_sha256=pilot.selected_pool_sha256,
        ladder_snapshot_sha256="6" * 64,
        candidate_pool_sha256=candidate_pool_sha256,
        resolution_cache_sha256="7" * 64,
        history_cache_sha256="8" * 64,
        players_processed_per_platform=32,
        balanced_waves_completed=1,
        resolution_files=64,
        history_page_files=384,
        candidate_match_ids=len(references),
        excluded_pilot_match_ids_discovered=0,
        candidate_windows=tuple(summaries),
        contains_player_identifiers_in_private_files=True,
        identifiers_in_summary=False,
        redistribution="not-authorized",
    )
    return (
        BoundFinalCandidatePool(
            frame=frame,
            frame_sha256=frame_sha256,
            selection_plan=selection_plan,
            selection_plan_sha256=selection_plan_sha256,
            final_discovery_context=context,
            discovery_manifest=manifest,
            discovery_manifest_sha256=manifest_sha256,
            candidate_pool=pool,
            candidate_pool_sha256=candidate_pool_sha256,
            pilot=pilot,
            ordered_candidates=tuple(by_id[match_id] for match_id in ordered_ids),
        ),
        patches_by_id,
    )


def _detail(
    match_id: str,
    platform_id: str,
    patch: str,
    *,
    duration: int = 180,
) -> dict[str, Any]:
    return {
        "metadata": {
            "matchId": match_id,
            "participants": [f"private-puuid-{index}" for index in range(10)],
        },
        "info": {
            "platformId": platform_id,
            "queueId": 420,
            "mapId": 11,
            "gameMode": "CLASSIC",
            "gameType": "MATCHED_GAME",
            "participants": [{"win": index < 5} for index in range(10)],
            "gameVersion": f"{patch}.1",
            "gameCreation": 1_789_000_000_000,
            "gameDuration": duration,
            "teams": [{"win": True}, {"win": False}],
        },
    }


class FinalDetailFetcher:
    def __init__(
        self,
        platform_id: str,
        patches_by_id: dict[str, str],
        *,
        short_match_id: str | None = None,
        fail: bool = False,
    ) -> None:
        self.platform_id = platform_id
        self.patches_by_id = patches_by_id
        self.short_match_id = short_match_id
        self.fail = fail
        self.calls = 0

    def get_match_for_screening(self, match_id: str) -> dict[str, Any]:
        if self.fail:
            raise AssertionError("completed final selection contacted Riot")
        self.calls += 1
        duration = 179 if match_id == self.short_match_id else 180
        return _detail(
            match_id,
            self.platform_id,
            self.patches_by_id[match_id],
            duration=duration,
        )


def _patch_small_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[BoundFinalCandidatePool, dict[str, str]]:
    bound, patches_by_id = _bound()
    monkeypatch.setattr(final_selection, "_load_bound_final_candidates", lambda *args: bound)
    monkeypatch.setattr(final_selection, "sampling_cells", lambda frame: _small_cells())
    monkeypatch.setattr(final_selection, "REGISTERED_FINAL_TARGET", 12)
    monkeypatch.setattr(final_selection, "REGISTERED_MATCHES_PER_CELL", 1)
    return bound, patches_by_id


def _call_select(
    output: Path,
    fetchers: dict[str, FinalDetailFetcher],
    **kwargs: Any,
) -> dict[str, object]:
    return select_final_matches(
        FRAME,
        SELECTION_PLAN,
        DISCOVERY_PLAN,
        DURATION_RULE,
        Path("duration-analysis.json"),
        Path("pilot-plan.yaml"),
        Path("pilot-discovery"),
        Path("pilot-selection"),
        Path("final-discovery"),
        output_root=output,
        regional_fetchers=fetchers,
        **kwargs,
    )


def test_registered_final_selection_plan_is_frozen() -> None:
    report = validate_final_selection_plan(
        SELECTION_PLAN,
        FRAME,
        DISCOVERY_PLAN,
        DURATION_RULE,
    )

    assert report["passed"] is True
    assert report["plan_id"] == "rifthazard-final-selection-2026-09-21"
    assert report["summary"] == {
        "candidate_match_ids": 110_838,
        "registered_cells": 12,
        "matches_per_cell": 3_000,
        "target_matches": 36_000,
        "final_minimum_seconds": 180,
        "pilot_match_ids_excluded": 5_000,
        "identifiers_in_summary": False,
    }


def test_final_selection_plan_rejects_discovery_inventory_drift(tmp_path) -> None:
    payload = yaml.safe_load(SELECTION_PLAN.read_text(encoding="utf-8"))
    payload["final_discovery"]["candidate_match_ids"] = 110_837
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = validate_final_selection_plan(path, FRAME, DISCOVERY_PLAN, DURATION_RULE)

    assert report["passed"] is False
    failed = {check["check_id"] for check in report["checks"] if not check["passed"]}
    assert failed == {"final-discovery-binding"}


def test_final_selection_preflight_fails_closed_before_authority(tmp_path) -> None:
    report = final_selection_preflight(
        tmp_path / "authority.yaml",
        FRAME,
        SELECTION_PLAN,
        DISCOVERY_PLAN,
        DURATION_RULE,
        tmp_path / "duration-analysis.json",
        tmp_path / "pilot-plan.yaml",
        tmp_path / "pilot-discovery",
        tmp_path / "pilot-selection",
        tmp_path / "final-discovery",
    )

    assert report["passed"] is False
    assert report["authority"] is None
    assert report["bindings"]["passed"] is False
    assert "EUW1_" not in json.dumps(report)


def test_final_selection_is_exact_duration_bound_private_and_resumable(
    tmp_path,
    monkeypatch,
) -> None:
    bound, patches_by_id = _patch_small_selection(monkeypatch)
    output = tmp_path / "final-selection"
    first = bound.ordered_candidates[0]
    progress: list[str] = []
    fetchers = {
        "europe": FinalDetailFetcher("EUW1", patches_by_id, short_match_id=first.match_id),
        "americas": FinalDetailFetcher("NA1", patches_by_id, short_match_id=first.match_id),
    }

    manifest = _call_select(
        output,
        fetchers,
        screened_at=datetime(2026, 9, 21, 12, tzinfo=UTC),
        progress=progress.append,
    )

    assert manifest["complete"] is True
    assert manifest["selected_match_ids"] == 12
    assert manifest["rejected_screened"] == 1
    assert manifest["rejection_reasons"] == {"duration-minimum": 1}
    assert manifest["identifiers_in_summary"] is False
    assert "EUW1_" not in json.dumps(manifest)
    assert progress[-1].endswith("complete cells 12/12")
    selected_pool = json.loads((output / "selected-pool.json").read_text(encoding="utf-8"))
    assert selected_pool["selected_match_ids"] == 12
    assert selected_pool["duration_eligibility"] == "info.gameDuration>=180-v1"
    assert selected_pool["contains_player_identifiers"] is False
    assert len((output / "selected-match-ids" / "europe.txt").read_text().splitlines()) == 6
    assert len((output / "selected-match-ids" / "americas.txt").read_text().splitlines()) == 6
    short_record = json.loads(
        (output / "details" / first.regional_route / f"{first.match_id}.json").read_text(
            encoding="utf-8"
        )
    )
    assert short_record["payload"]["info"]["gameDuration"] == 179
    assert not list(output.rglob("*.partial"))

    resumed = _call_select(
        output,
        {
            "europe": FinalDetailFetcher("EUW1", patches_by_id, fail=True),
            "americas": FinalDetailFetcher("NA1", patches_by_id, fail=True),
        },
        screened_at=datetime(2026, 9, 21, 13, tzinfo=UTC),
    )
    assert resumed["complete"] is True
    assert resumed["new_requests"] == 0
    assert resumed["selected_pool_sha256"] == manifest["selected_pool_sha256"]

    report = validate_frozen_final_selection(
        FRAME,
        SELECTION_PLAN,
        DISCOVERY_PLAN,
        DURATION_RULE,
        Path("duration-analysis.json"),
        Path("pilot-plan.yaml"),
        Path("pilot-discovery"),
        Path("pilot-selection"),
        Path("final-discovery"),
        output,
    )
    assert report["passed"] is True
    assert report["summary"] == {
        "selected_match_ids": 12,
        "registered_cells": 12,
        "matches_per_cell": 1,
        "identifiers_in_summary": False,
    }


def test_final_selection_supports_bounded_runs_and_rejects_cache_gaps(
    tmp_path,
    monkeypatch,
) -> None:
    bound, patches_by_id = _patch_small_selection(monkeypatch)
    output = tmp_path / "final-selection"
    fetchers = {
        "europe": FinalDetailFetcher("EUW1", patches_by_id),
        "americas": FinalDetailFetcher("NA1", patches_by_id),
    }
    partial = _call_select(output, fetchers, max_new_requests=3)
    assert partial["complete"] is False
    assert partial["new_requests"] == 3
    assert not (output / "selected-pool.json").exists()

    first = bound.ordered_candidates[0]
    (output / "details" / first.regional_route / f"{first.match_id}.json").unlink()
    with pytest.raises(ValueError, match="contiguous deterministic prefix"):
        _call_select(output, fetchers)


def test_final_selection_rejects_unsafe_runtime_inputs(tmp_path, monkeypatch) -> None:
    _, patches_by_id = _patch_small_selection(monkeypatch)
    fetchers = {
        "europe": FinalDetailFetcher("EUW1", patches_by_id),
        "americas": FinalDetailFetcher("NA1", patches_by_id),
    }
    with pytest.raises(ValueError, match="positive"):
        _call_select(tmp_path / "output", fetchers, max_new_requests=0)
    with pytest.raises(ValueError, match="separate from input data"):
        _call_select(Path("final-discovery"), fetchers)
    with pytest.raises(ValueError, match="timezone-aware"):
        _call_select(
            tmp_path / "output",
            fetchers,
            screened_at=datetime(2026, 9, 21),
        )


def test_final_selection_validation_detects_selected_pool_tampering(
    tmp_path,
    monkeypatch,
) -> None:
    _, patches_by_id = _patch_small_selection(monkeypatch)
    output = tmp_path / "final-selection"
    _call_select(
        output,
        {
            "europe": FinalDetailFetcher("EUW1", patches_by_id),
            "americas": FinalDetailFetcher("NA1", patches_by_id),
        },
    )
    with (output / "selected-pool.json").open("ab") as stream:
        stream.write(b" ")

    report = validate_frozen_final_selection(
        FRAME,
        SELECTION_PLAN,
        DISCOVERY_PLAN,
        DURATION_RULE,
        Path("duration-analysis.json"),
        Path("pilot-plan.yaml"),
        Path("pilot-discovery"),
        Path("pilot-selection"),
        Path("final-discovery"),
        output,
    )
    assert report["passed"] is False
    assert report["summary"] is None
    assert "EUW1_" not in json.dumps(report)
