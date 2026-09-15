from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import league_ews.selection as selection
from league_ews.sampling import (
    SamplingCell,
    load_registered_sampling_frame,
    order_candidate_match_ids,
    sampling_cells,
)
from league_ews.selection import select_pilot_matches, validate_candidate_pool

ROOT = Path(__file__).parents[1]
FRAME = ROOT / "configs" / "rifthazard-sampling-frame.yaml"
PLAN = ROOT / "configs" / "rifthazard-discovery-plan.yaml"
PATCHES = tuple(f"16.{minor}" for minor in range(12, 18))


def _canonical(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write_complete_discovery(root: Path) -> None:
    frame, frame_sha256 = load_registered_sampling_frame(FRAME)
    plan_content = PLAN.read_bytes()
    plan_sha256 = hashlib.sha256(plan_content).hexdigest()
    snapshot_sha256 = "a" * 64
    cells = []
    summaries = []
    for cell_index, cell in enumerate(sampling_cells(frame)):
        minimum = cell.pilot_target * 2
        identifiers = tuple(
            f"{cell.platform_id}_{cell_index * 100_000 + index + 1}" for index in range(minimum)
        )
        ordered = order_candidate_match_ids(frame, identifiers)
        record = {
            "regional_route": cell.regional_route,
            "platform_id": cell.platform_id,
            "game_version_patch": cell.game_version_patch,
            "minimum_candidates": minimum,
            "candidate_count": len(ordered),
            "minimum_met": True,
            "match_ids": list(ordered),
        }
        cells.append(record)
        summaries.append({key: value for key, value in record.items() if key != "match_ids"})

    pool = {
        "schema_version": "riot-candidate-pool-v1",
        "frame_id": frame.frame_id,
        "frame_sha256": frame_sha256,
        "plan_id": "rifthazard-pilot-discovery-2026-09-15",
        "plan_sha256": plan_sha256,
        "snapshot_sha256": snapshot_sha256,
        "complete": True,
        "globally_deduplicated": True,
        "cells": cells,
        "contains_match_identifiers": True,
        "redistribution": "not-authorized",
    }
    pool_content = _canonical(pool)
    manifest = {
        "schema_version": "riot-candidate-discovery-manifest-v1",
        "completed_at": "2026-09-15T12:00:00+00:00",
        "complete": True,
        "frame_id": frame.frame_id,
        "frame_sha256": frame_sha256,
        "plan_id": "rifthazard-pilot-discovery-2026-09-15",
        "plan_sha256": plan_sha256,
        "ladder_snapshot_sha256": snapshot_sha256,
        "candidate_pool_sha256": hashlib.sha256(pool_content).hexdigest(),
        "resolution_cache_sha256": "b" * 64,
        "history_cache_sha256": "c" * 64,
        "players_processed_per_platform": 64,
        "balanced_waves_completed": 2,
        "resolution_files": 128,
        "history_page_files": 768,
        "candidate_match_ids": sum(cell["candidate_count"] for cell in cells),
        "candidate_windows": summaries,
        "contains_player_identifiers_in_private_files": True,
        "identifiers_in_summary": False,
        "redistribution": "not-authorized",
    }
    root.mkdir(parents=True)
    (root / "candidate-pool.json").write_bytes(pool_content)
    (root / "discovery-manifest.json").write_bytes(_canonical(manifest))


def _detail(match_id: str, platform_id: str, patch: str, **overrides: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "platformId": platform_id,
        "queueId": 420,
        "mapId": 11,
        "gameMode": "CLASSIC",
        "gameType": "MATCHED_GAME",
        "participants": [{} for _ in range(10)],
        "gameVersion": f"{patch}.1",
        "gameCreation": 1_789_000_000_000,
    }
    info.update(overrides)
    return {
        "metadata": {
            "matchId": match_id,
            "participants": [f"private-{index}" for index in range(10)],
        },
        "info": info,
    }


class SequencedFetcher:
    def __init__(
        self,
        platform_id: str,
        *,
        first_not_found: bool = False,
        first_wrong_queue: bool = False,
        fail: bool = False,
    ) -> None:
        self.platform_id = platform_id
        self.first_not_found = first_not_found
        self.first_wrong_queue = first_wrong_queue
        self.fail = fail
        self.calls = 0
        self.valid_calls = 0

    def get_match_for_screening(self, match_id: str) -> dict[str, Any] | None:
        if self.fail:
            raise AssertionError("completed resume unexpectedly contacted Riot")
        self.calls += 1
        if self.first_not_found and self.calls == 1:
            return None
        if self.first_wrong_queue and self.calls == 1:
            return _detail(match_id, self.platform_id, PATCHES[0], queueId=430)
        patch = PATCHES[self.valid_calls % len(PATCHES)]
        self.valid_calls += 1
        return _detail(match_id, self.platform_id, patch)


def _small_cells() -> tuple[SamplingCell, ...]:
    frame, _ = load_registered_sampling_frame(FRAME)
    return tuple(replace(cell, pilot_target=1) for cell in sampling_cells(frame))


def _patch_small_selection(monkeypatch: pytest.MonkeyPatch, discovery: Path) -> None:
    bound = selection._load_bound_candidate_pool(FRAME, PLAN, discovery)
    monkeypatch.setattr(selection, "_load_bound_candidate_pool", lambda *args: bound)
    monkeypatch.setattr(selection, "sampling_cells", lambda frame: _small_cells())


def test_candidate_pool_validation_is_checksum_bound_and_identifier_free(tmp_path) -> None:
    discovery = tmp_path / "discovery"
    _write_complete_discovery(discovery)

    report = validate_candidate_pool(FRAME, PLAN, discovery)

    assert report["passed"] is True
    assert report["summary"] == {
        "candidate_match_ids": 10_000,
        "registered_cells": 12,
        "identifiers_in_summary": False,
    }
    assert "EUW1_" not in json.dumps(report)

    with (discovery / "candidate-pool.json").open("ab") as stream:
        stream.write(b" ")
    rejected = validate_candidate_pool(FRAME, PLAN, discovery)
    assert rejected["passed"] is False
    assert "EUW1_" not in json.dumps(rejected)


def test_pilot_selection_is_resumable_exact_and_privacy_minimal(tmp_path, monkeypatch) -> None:
    discovery = tmp_path / "discovery"
    output = tmp_path / "selection"
    _write_complete_discovery(discovery)
    _patch_small_selection(monkeypatch, discovery)
    progress: list[str] = []
    fetchers = {
        "europe": SequencedFetcher("EUW1", first_not_found=True),
        "americas": SequencedFetcher("NA1", first_wrong_queue=True),
    }

    manifest = select_pilot_matches(
        FRAME,
        PLAN,
        discovery,
        output_root=output,
        regional_fetchers=fetchers,
        screened_at=datetime(2026, 9, 15, 14, tzinfo=UTC),
        progress=progress.append,
    )

    assert manifest["complete"] is True
    assert manifest["selected_match_ids"] == 12
    assert manifest["rejected_screened"] == 2
    assert manifest["rejection_reasons"] == {"not-found": 1, "queue": 1}
    assert manifest["identifiers_in_summary"] is False
    assert "EUW1_" not in json.dumps(manifest)
    assert progress[-1].endswith("complete cells 12/12")
    selected_pool = json.loads((output / "selected-pool.json").read_text(encoding="utf-8"))
    assert selected_pool["selected_match_ids"] == 12
    assert selected_pool["contains_player_identifiers"] is False
    assert len((output / "selected-match-ids" / "europe.txt").read_text().splitlines()) == 6
    assert len((output / "selected-match-ids" / "americas.txt").read_text().splitlines()) == 6
    assert not list(output.rglob("*.partial"))

    resumed = select_pilot_matches(
        FRAME,
        PLAN,
        discovery,
        output_root=output,
        regional_fetchers={
            "europe": SequencedFetcher("EUW1", fail=True),
            "americas": SequencedFetcher("NA1", fail=True),
        },
        screened_at=datetime(2026, 9, 15, 15, tzinfo=UTC),
    )
    assert resumed["complete"] is True
    assert resumed["new_requests"] == 0
    assert resumed["selected_pool_sha256"] == manifest["selected_pool_sha256"]


def test_pilot_selection_supports_bounded_runs_and_rejects_cache_gaps(
    tmp_path,
    monkeypatch,
) -> None:
    discovery = tmp_path / "discovery"
    output = tmp_path / "selection"
    _write_complete_discovery(discovery)
    _patch_small_selection(monkeypatch, discovery)
    fetchers = {
        "europe": SequencedFetcher("EUW1"),
        "americas": SequencedFetcher("NA1"),
    }

    partial = select_pilot_matches(
        FRAME,
        PLAN,
        discovery,
        output_root=output,
        regional_fetchers=fetchers,
        max_new_requests=3,
    )
    assert partial["complete"] is False
    assert partial["new_requests"] == 3
    assert not (output / "selected-pool.json").exists()

    bound = selection._load_bound_candidate_pool(FRAME, PLAN, discovery)
    first = bound.ordered_candidates[0]
    (output / "details" / first.regional_route / f"{first.match_id}.json").unlink()
    with pytest.raises(ValueError, match="contiguous deterministic prefix"):
        select_pilot_matches(
            FRAME,
            PLAN,
            discovery,
            output_root=output,
            regional_fetchers=fetchers,
        )


def test_pilot_selection_rejects_unsafe_runtime_inputs(tmp_path, monkeypatch) -> None:
    discovery = tmp_path / "discovery"
    _write_complete_discovery(discovery)
    _patch_small_selection(monkeypatch, discovery)
    fetchers = {
        "europe": SequencedFetcher("EUW1"),
        "americas": SequencedFetcher("NA1"),
    }
    with pytest.raises(ValueError, match="positive"):
        select_pilot_matches(
            FRAME,
            PLAN,
            discovery,
            output_root=tmp_path / "output",
            regional_fetchers=fetchers,
            max_new_requests=0,
        )
    with pytest.raises(ValueError, match="separate output roots"):
        select_pilot_matches(
            FRAME,
            PLAN,
            discovery,
            output_root=discovery,
            regional_fetchers=fetchers,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        select_pilot_matches(
            FRAME,
            PLAN,
            discovery,
            output_root=tmp_path / "output",
            regional_fetchers=fetchers,
            screened_at=datetime(2026, 9, 15),
        )


def test_detail_identity_mismatch_is_not_cached(tmp_path, monkeypatch) -> None:
    discovery = tmp_path / "discovery"
    output = tmp_path / "selection"
    _write_complete_discovery(discovery)
    _patch_small_selection(monkeypatch, discovery)

    class MismatchFetcher(SequencedFetcher):
        def get_match_for_screening(self, match_id: str) -> dict[str, Any]:
            return _detail("EUW1_999999999", self.platform_id, PATCHES[0])

    with pytest.raises(ValueError, match="identity"):
        select_pilot_matches(
            FRAME,
            PLAN,
            discovery,
            output_root=output,
            regional_fetchers={
                "europe": MismatchFetcher("EUW1"),
                "americas": MismatchFetcher("NA1"),
            },
        )
    assert not list((output / "details").rglob("*.json"))
