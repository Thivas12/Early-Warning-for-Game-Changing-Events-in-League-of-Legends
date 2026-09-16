from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import league_ews.pilot_collection as pilot_collection
import league_ews.raw_validation as raw_validation
from league_ews.pilot_collection import (
    collect_selected_pilot_bundles,
    pilot_collection_preflight,
    validate_frozen_pilot_selection,
)
from league_ews.raw_validation import validate_raw_collection
from league_ews.riot import RiotAPIError, canonical_riot_json
from league_ews.selection import select_pilot_matches
from tests.test_raw_validation import _bundle
from tests.test_selection import (
    FRAME,
    PATCHES,
    PLAN,
    _patch_small_selection,
    _small_cells,
    _write_complete_discovery,
)


class FullDetailFetcher:
    def __init__(self) -> None:
        self.calls = 0

    def get_match_for_screening(self, match_id: str) -> dict[str, object]:
        patch = PATCHES[self.calls % len(PATCHES)]
        self.calls += 1
        return _bundle(match_id, f"{patch}.1")[0]


class TimelineFetcher:
    def __init__(self, *, fail: bool = False, wrong_identity: bool = False) -> None:
        self.fail = fail
        self.wrong_identity = wrong_identity
        self.calls: list[str] = []

    def get_timeline(self, match_id: str) -> dict[str, object]:
        if self.fail:
            raise AssertionError("a completed or recovered collection contacted Riot")
        self.calls.append(match_id)
        identity = "EUW1_999999999" if self.wrong_identity else match_id
        return _bundle(identity)[1]


def _prepare_frozen_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    discovery = tmp_path / "discovery"
    selection = tmp_path / "selection"
    _write_complete_discovery(discovery)
    _patch_small_selection(monkeypatch, discovery)
    monkeypatch.setattr(pilot_collection, "sampling_cells", lambda frame: _small_cells())
    manifest = select_pilot_matches(
        FRAME,
        PLAN,
        discovery,
        output_root=selection,
        regional_fetchers={
            "europe": FullDetailFetcher(),
            "americas": FullDetailFetcher(),
        },
        screened_at=datetime(2026, 9, 15, 14, tzinfo=UTC),
    )
    assert manifest["complete"] is True
    assert manifest["selected_match_ids"] == 12
    return discovery, selection


def _fetchers(**kwargs: Any) -> dict[str, TimelineFetcher]:
    return {
        "europe": TimelineFetcher(**kwargs),
        "americas": TimelineFetcher(**kwargs),
    }


def _collect(
    discovery: Path,
    selection: Path,
    raw: Path,
    fetchers: dict[str, TimelineFetcher],
    *,
    max_new_requests: int | None = None,
) -> dict[str, object]:
    return collect_selected_pilot_bundles(
        FRAME,
        PLAN,
        discovery,
        selection,
        output_root=raw,
        regional_fetchers=fetchers,
        collected_at=datetime(2026, 9, 15, 16, tzinfo=UTC),
        max_new_requests=max_new_requests,
    )


def test_frozen_selection_validation_is_exact_and_identifier_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovery, selection = _prepare_frozen_selection(tmp_path, monkeypatch)

    report = validate_frozen_pilot_selection(FRAME, PLAN, discovery, selection)

    assert report["passed"] is True
    assert report["summary"] == {
        "selected_match_ids": 12,
        "registered_cells": 12,
        "identifiers_in_summary": False,
    }
    assert "EUW1_" not in json.dumps(report)
    assert "NA1_" not in json.dumps(report)

    selected_pool = json.loads((selection / "selected-pool.json").read_text(encoding="utf-8"))
    selected_id = selected_pool["cells"][0]["selected"][0]["match_id"]
    screen_path = selection / "details" / "europe" / f"{selected_id}.json"
    screen_path.write_text(screen_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    rejected = validate_frozen_pilot_selection(FRAME, PLAN, discovery, selection)
    assert rejected["passed"] is False
    assert "EUW1_" not in json.dumps(rejected)


def test_selected_collection_is_bounded_resumable_and_no_refetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovery, selection = _prepare_frozen_selection(tmp_path, monkeypatch)
    raw = tmp_path / "raw"
    first_fetchers = _fetchers()
    progress: list[str] = []

    partial = collect_selected_pilot_bundles(
        FRAME,
        PLAN,
        discovery,
        selection,
        output_root=raw,
        regional_fetchers=first_fetchers,
        collected_at=datetime(2026, 9, 15, 16, tzinfo=UTC),
        max_new_requests=3,
        progress=progress.append,
    )

    assert partial["complete"] is False
    assert partial["available_bundles"] == 3
    assert partial["new_timeline_requests"] == 3
    assert sum(len(fetcher.calls) for fetcher in first_fetchers.values()) == 3
    assert "EUW1_" not in json.dumps(partial)
    assert "NA1_" not in json.dumps(partial)

    second_fetchers = _fetchers()
    complete = _collect(discovery, selection, raw, second_fetchers)
    assert complete["complete"] is True
    assert complete["available_bundles"] == 12
    assert complete["new_timeline_requests"] == 9
    assert sum(len(fetcher.calls) for fetcher in second_fetchers.values()) == 9
    assert len(list((raw / "matches").glob("*.json"))) == 12
    assert len(list((raw / "timelines").glob("*.json"))) == 12

    resumed = _collect(discovery, selection, raw, _fetchers(fail=True))
    assert resumed["complete"] is True
    assert resumed["new_timeline_requests"] == 0
    manifest = json.loads((raw / "collection-manifest.json").read_text(encoding="utf-8"))
    assert manifest["requested"] == 12
    assert len(manifest["skipped_existing"]) == 12
    assert manifest["collected"] == []


def test_selected_collection_recovers_one_timeline_only_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovery, selection = _prepare_frozen_selection(tmp_path, monkeypatch)
    raw = tmp_path / "raw"
    _collect(discovery, selection, raw, _fetchers(), max_new_requests=11)
    pool = json.loads((selection / "selected-pool.json").read_text(encoding="utf-8"))
    last_id = pool["cells"][-1]["selected"][-1]["match_id"]
    timeline = _bundle(last_id)[1]
    timeline_path = raw / "timelines" / f"{last_id}.json"
    timeline_path.write_bytes(canonical_riot_json(timeline))
    (raw / "collection-manifest.json.partial").write_text("interrupted", encoding="utf-8")

    recovered = _collect(discovery, selection, raw, _fetchers(fail=True))

    assert recovered["complete"] is True
    assert recovered["recovered_unpaired_bundles"] == 1
    assert recovered["new_timeline_requests"] == 0
    assert not list(raw.rglob("*.partial"))


def test_selected_collection_recovers_manifest_binding_commit_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovery, selection = _prepare_frozen_selection(tmp_path, monkeypatch)
    raw = tmp_path / "raw"
    _collect(discovery, selection, raw, _fetchers(), max_new_requests=1)
    original_atomic_write = pilot_collection._atomic_write

    def interrupt_binding(path: Path, content: bytes) -> None:
        if path.name == "selection-binding.json":
            raise OSError("simulated interruption")
        original_atomic_write(path, content)

    with monkeypatch.context() as interrupted:
        interrupted.setattr(pilot_collection, "_atomic_write", interrupt_binding)
        with pytest.raises(OSError, match="simulated interruption"):
            _collect(discovery, selection, raw, _fetchers(), max_new_requests=1)

    assert (raw / "collection-checkpoint.pending").is_file()
    resumed = _collect(discovery, selection, raw, _fetchers(), max_new_requests=1)
    assert resumed["available_bundles"] == 3
    assert not (raw / "collection-checkpoint.pending").exists()


def test_selected_collection_rejects_gaps_tampering_and_unsafe_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovery, selection = _prepare_frozen_selection(tmp_path, monkeypatch)
    raw = tmp_path / "raw"
    _collect(discovery, selection, raw, _fetchers(), max_new_requests=2)
    pool = json.loads((selection / "selected-pool.json").read_text(encoding="utf-8"))
    first_id = pool["cells"][0]["selected"][0]["match_id"]
    (raw / "matches" / f"{first_id}.json").unlink()
    (raw / "timelines" / f"{first_id}.json").unlink()
    with pytest.raises(ValueError, match="contiguous selected prefix"):
        _collect(discovery, selection, raw, _fetchers())

    clean = tmp_path / "clean"
    _collect(discovery, selection, clean, _fetchers(), max_new_requests=1)
    clean_match = next((clean / "matches").glob("*.json"))
    clean_match.write_text(clean_match.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from its selection"):
        _collect(discovery, selection, clean, _fetchers())

    timeline_clean = tmp_path / "timeline-clean"
    _collect(discovery, selection, timeline_clean, _fetchers(), max_new_requests=1)
    timeline_path = next((timeline_clean / "timelines").glob("*.json"))
    timeline_path.write_text(timeline_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="changed after checkpointing"):
        _collect(discovery, selection, timeline_clean, _fetchers())

    with pytest.raises(ValueError, match="positive"):
        _collect(discovery, selection, tmp_path / "unused", _fetchers(), max_new_requests=0)
    with pytest.raises(ValueError, match="separate directory"):
        _collect(discovery, selection, selection, _fetchers())
    with pytest.raises(ValueError, match="separate directory"):
        _collect(discovery, selection, selection / "raw", _fetchers())
    with pytest.raises(ValueError, match="timezone-aware"):
        collect_selected_pilot_bundles(
            FRAME,
            PLAN,
            discovery,
            selection,
            output_root=tmp_path / "naive",
            regional_fetchers=_fetchers(),
            collected_at=datetime(2026, 9, 15),
        )


def test_selected_collection_rejects_bad_timeline_and_missing_route(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovery, selection = _prepare_frozen_selection(tmp_path, monkeypatch)
    with pytest.raises(RiotAPIError, match="identity or required metadata"):
        _collect(discovery, selection, tmp_path / "bad", _fetchers(wrong_identity=True))

    class FailingTimelineFetcher:
        def get_timeline(self, match_id: str) -> dict[str, object]:
            raise RiotAPIError(f"private upstream path contained {match_id}")

    with pytest.raises(RiotAPIError, match="no replacement was made") as failure:
        collect_selected_pilot_bundles(
            FRAME,
            PLAN,
            discovery,
            selection,
            output_root=tmp_path / "api-failure",
            regional_fetchers={
                "europe": FailingTimelineFetcher(),
                "americas": FailingTimelineFetcher(),
            },
        )
    assert "EUW1_" not in str(failure.value)
    assert "NA1_" not in str(failure.value)
    with pytest.raises(ValueError, match="clients do not cover"):
        _collect(discovery, selection, tmp_path / "missing", {})


def test_raw_validation_requires_and_accepts_exact_pilot_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovery, selection = _prepare_frozen_selection(tmp_path, monkeypatch)
    raw = tmp_path / "raw"
    _collect(discovery, selection, raw, _fetchers())

    def small_coverage(frame, counts, *, stage):
        assert stage == "pilot"
        assert len(counts) == 12
        assert set(counts.values()) == {1}
        return {
            "stage": "pilot",
            "passed": True,
            "expected_cells": 12,
            "represented_cells": 12,
            "unexpected_cells": 0,
            "target_matches": 12,
            "observed_in_frame_matches": 12,
            "exact_cell_targets_met": True,
        }

    monkeypatch.setattr(raw_validation, "sampling_coverage", small_coverage)
    report = validate_raw_collection(
        raw,
        min_routes=2,
        min_patches=6,
        sampling_frame=FRAME,
        sampling_stage="pilot",
        discovery_plan=PLAN,
        discovery_root=discovery,
        selection_root=selection,
        checked_at=datetime(2026, 9, 16, tzinfo=UTC),
    )

    assert report["passed"] is True
    assert report["pilot_selection"]["status"] == "passed"
    assert "pilot-selection-binding" not in {
        check["check_id"] for check in report["checks"] if check["passed"] is False
    }
    assert "EUW1_" not in json.dumps(report)

    binding_path = raw / "selection-binding.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["collection_manifest_sha256"] = "0" * 64
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    rejected = validate_raw_collection(
        raw,
        min_routes=2,
        min_patches=6,
        sampling_frame=FRAME,
        sampling_stage="pilot",
        discovery_plan=PLAN,
        discovery_root=discovery,
        selection_root=selection,
        checked_at=datetime(2026, 9, 16, tzinfo=UTC),
    )
    assert rejected["passed"] is False
    assert rejected["pilot_selection"]["status"] == "failed"

    with pytest.raises(ValueError, match="requires discovery_plan"):
        validate_raw_collection(
            raw,
            sampling_frame=FRAME,
            sampling_stage="pilot",
            discovery_plan=PLAN,
        )
    with pytest.raises(ValueError, match="sampling frame"):
        validate_raw_collection(
            raw,
            discovery_plan=PLAN,
            discovery_root=discovery,
            selection_root=selection,
        )


def test_collection_preflight_combines_authority_and_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovery, selection = _prepare_frozen_selection(tmp_path, monkeypatch)
    monkeypatch.setattr(
        pilot_collection,
        "pilot_selection_preflight",
        lambda *args, **kwargs: {"passed": True},
    )

    report = pilot_collection_preflight(
        tmp_path / "authority.yaml",
        FRAME,
        PLAN,
        discovery,
        selection,
    )

    assert report["passed"] is True
    assert report["authority"]["passed"] is True
    assert report["selection"]["passed"] is True
