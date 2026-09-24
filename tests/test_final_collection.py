from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import league_ews.final_collection as final_collection
from league_ews.final_collection import (
    collect_selected_final_bundles,
    final_collection_preflight,
)
from league_ews.final_selection import FrozenFinalSelectedMatch, FrozenFinalSelection
from league_ews.riot import canonical_riot_json
from tests.test_raw_validation import _bundle


class TimelineFetcher:
    def __init__(self, timelines: dict[str, dict[str, object]], *, fail: bool = False) -> None:
        self.timelines = timelines
        self.fail = fail
        self.calls: list[str] = []

    def get_timeline(self, match_id: str) -> dict[str, object]:
        if self.fail:
            raise AssertionError("completed collection contacted Riot")
        self.calls.append(match_id)
        return self.timelines[match_id]


def _frozen(
    tmp_path: Path,
) -> tuple[FrozenFinalSelection, dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    match_ids = ("EUW1_100", "NA1_200")
    matches: dict[str, dict[str, object]] = {}
    timelines: dict[str, dict[str, object]] = {}
    entries: list[FrozenFinalSelectedMatch] = []
    for index, match_id in enumerate(match_ids):
        match, timeline = _bundle(match_id, "16.12.1")
        info = match["info"]
        assert isinstance(info, dict)
        matches[match_id] = match
        timelines[match_id] = timeline
        entries.append(
            FrozenFinalSelectedMatch(
                match_id=match_id,
                regional_route="europe" if index == 0 else "americas",
                platform_id=match_id.split("_", maxsplit=1)[0],
                game_version_patch="16.12",
                candidate_rank_sha256=f"{index + 1:064x}",
                screen_record_sha256=f"{index + 3:064x}",
                match_payload_sha256=hashlib.sha256(canonical_riot_json(match)).hexdigest(),
                game_version="16.12.1",
                game_creation_ms=int(info["gameCreation"]),
                game_duration_seconds=int(info["gameDuration"]),
                screen_record_path=tmp_path / f"screen-{index}.json",
            )
        )
    frozen = FrozenFinalSelection(
        frame=SimpleNamespace(frame_id="frame", route_platforms=()),  # type: ignore[arg-type]
        frame_sha256="1" * 64,
        selection_plan_id="selection-plan",
        selection_plan_sha256="2" * 64,
        final_discovery_plan_sha256="3" * 64,
        final_discovery_manifest_sha256="4" * 64,
        candidate_pool_sha256="5" * 64,
        duration_rule_sha256="6" * 64,
        pilot_selected_pool_sha256="7" * 64,
        selected_pool_sha256="8" * 64,
        selected_matches=tuple(entries),
    )
    return frozen, matches, timelines


def _collect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    max_new_requests: int | None = None,
    fail: bool = False,
) -> tuple[dict[str, object], TimelineFetcher]:
    frozen, matches, timelines = _frozen(tmp_path)
    monkeypatch.setattr(final_collection, "load_frozen_final_selection", lambda *a, **k: frozen)
    monkeypatch.setattr(
        final_collection,
        "_load_cached_match",
        lambda frozen_selection, entry: (
            canonical_riot_json(matches[entry.match_id]),
            matches[entry.match_id],
        ),
    )
    fetcher = TimelineFetcher(timelines, fail=fail)
    binding = collect_selected_final_bundles(
        tmp_path / "frame.yaml",
        tmp_path / "selection-plan.yaml",
        tmp_path / "discovery-plan.yaml",
        tmp_path / "duration-rule.yaml",
        tmp_path / "duration-analysis.json",
        tmp_path / "pilot-plan.yaml",
        tmp_path / "pilot-discovery",
        tmp_path / "pilot-selection",
        tmp_path / "final-discovery",
        tmp_path / "final-selection",
        output_root=tmp_path / "raw-final",
        regional_fetchers={"europe": fetcher, "americas": fetcher},
        collected_at=datetime(2026, 9, 24, tzinfo=UTC),
        max_new_requests=max_new_requests,
    )
    return binding, fetcher


def test_final_collection_is_bounded_resumable_and_reuses_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    partial, first = _collect(tmp_path, monkeypatch, max_new_requests=1)
    assert partial["complete"] is False
    assert partial["available_bundles"] == 1
    assert first.calls == ["EUW1_100"]

    complete, second = _collect(tmp_path, monkeypatch)
    assert complete["schema_version"] == "riot-final-collection-binding-v1"
    assert complete["complete"] is True
    assert complete["available_bundles"] == 2
    assert second.calls == ["NA1_200"]
    assert "EUW1_" not in json.dumps(complete)
    assert "NA1_" not in json.dumps(complete)

    resumed, third = _collect(tmp_path, monkeypatch, fail=True)
    assert resumed["complete"] is True
    assert resumed["new_timeline_requests"] == 0
    assert third.calls == []
    assert not list((tmp_path / "raw-final").rglob("*.partial"))


def test_final_collection_rejects_nonpositive_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frozen, _, _ = _frozen(tmp_path)
    monkeypatch.setattr(final_collection, "load_frozen_final_selection", lambda *a, **k: frozen)
    with pytest.raises(ValueError, match="positive"):
        collect_selected_final_bundles(
            tmp_path / "frame",
            tmp_path / "selection-plan",
            tmp_path / "discovery-plan",
            tmp_path / "duration-rule",
            tmp_path / "duration-analysis",
            tmp_path / "pilot-plan",
            tmp_path / "pilot-discovery",
            tmp_path / "pilot-selection",
            tmp_path / "final-discovery",
            tmp_path / "final-selection",
            output_root=tmp_path / "raw-final",
            regional_fetchers={},
            max_new_requests=0,
        )


def test_final_collection_preflight_requires_selection_and_timeline_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frozen, _, _ = _frozen(tmp_path)
    monkeypatch.setattr(
        final_collection,
        "validate_frozen_final_selection",
        lambda *a, **k: {"passed": True},
    )
    monkeypatch.setattr(final_collection, "load_frozen_final_selection", lambda *a, **k: frozen)
    observed: dict[str, Any] = {}

    def fake_authority(*args: Any, **kwargs: Any) -> dict[str, object]:
        observed.update(kwargs)
        return {"passed": True}

    monkeypatch.setattr(final_collection, "collection_preflight", fake_authority)
    report = final_collection_preflight(
        tmp_path / "authority",
        tmp_path / "frame",
        tmp_path / "selection-plan",
        tmp_path / "discovery-plan",
        tmp_path / "duration-rule",
        tmp_path / "duration-analysis",
        tmp_path / "pilot-plan",
        tmp_path / "pilot-discovery",
        tmp_path / "pilot-selection",
        tmp_path / "final-discovery",
        tmp_path / "final-selection",
    )
    assert report["passed"] is True
    assert observed["required_endpoints"] == ("match-v5.timeline",)
