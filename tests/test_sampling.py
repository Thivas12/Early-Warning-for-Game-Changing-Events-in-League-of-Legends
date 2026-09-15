from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from league_ews.cli import main
from league_ews.sampling import (
    candidate_rank_sha256,
    load_sampling_frame,
    order_candidate_match_ids,
    sampling_coverage,
    validate_sampling_frame,
)

ROOT = Path(__file__).parents[1]
FRAME_PATH = ROOT / "configs" / "rifthazard-sampling-frame.yaml"


def _write_mutated_frame(tmp_path: Path, mutate) -> Path:
    payload = yaml.safe_load(FRAME_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    mutate(payload)
    output = tmp_path / "frame.yaml"
    output.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output


def _failed_checks(report: dict[str, object]) -> set[str]:
    checks = report["checks"]
    assert isinstance(checks, list)
    return {
        str(check["check_id"])
        for check in checks
        if isinstance(check, dict) and check["passed"] is False
    }


def test_registered_sampling_frame_is_valid_and_exactly_allocated() -> None:
    report = validate_sampling_frame(FRAME_PATH)

    assert report["passed"] is True
    assert report["schema_version"] == "league-ews-sampling-frame-validation-v1"
    assert len(str(report["frame_sha256"])) == 64
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["regional_routes"] == ["europe", "americas"]
    assert summary["platform_ids"] == ["EUW1", "NA1"]
    assert summary["game_version_patches"] == [
        "16.12",
        "16.13",
        "16.14",
        "16.15",
        "16.16",
        "16.17",
    ]
    assert summary["route_patch_cells"] == 12
    assert summary["pilot_target_matches"] == 5_000
    assert summary["final_target_matches"] == 36_000
    cells = summary["cells"]
    assert isinstance(cells, list)
    assert [cell["pilot_target"] for cell in cells] == [417] * 8 + [416] * 4
    assert {cell["final_target"] for cell in cells} == {3_000}


def test_sampling_frame_cli_prints_validated_contract(capsys) -> None:
    exit_code = main(["validate-sampling-frame", "--frame", str(FRAME_PATH)])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["passed"] is True


def test_sampling_frame_fails_closed_for_missing_or_invalid_input(tmp_path) -> None:
    missing = validate_sampling_frame(tmp_path / "missing.yaml")
    assert missing["passed"] is False
    assert _failed_checks(missing) == {"frame-schema"}

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("frame_id: [not-valid\n", encoding="utf-8")
    report = validate_sampling_frame(invalid)
    assert report["passed"] is False
    assert "not-valid" not in json.dumps(report)


def test_sampling_frame_rejects_route_or_patch_drift(tmp_path) -> None:
    route_drift = _write_mutated_frame(
        tmp_path,
        lambda payload: payload["route_platforms"][1].update(platform_id="BR1"),
    )
    assert _failed_checks(validate_sampling_frame(route_drift)) == {"route-platforms"}

    def drift_patch(payload: dict[str, object]) -> None:
        patches = payload["patches"]
        assert isinstance(patches, list)
        assert isinstance(patches[2], dict)
        patches[2]["game_version_patch"] = "16.99"

    patch_drift = _write_mutated_frame(tmp_path, drift_patch)
    assert _failed_checks(validate_sampling_frame(patch_drift)) == {
        "future-patch-split",
        "patch-series",
    }


def test_sampling_frame_rejects_premature_duration_cutoff(tmp_path) -> None:
    frame = _write_mutated_frame(
        tmp_path,
        lambda payload: payload["duration"].update(pilot_minimum_seconds=300),
    )

    report = validate_sampling_frame(frame)

    assert report["passed"] is False
    assert _failed_checks(report) == {"frame-schema"}


def test_sampling_frame_rejects_seed_source_and_window_drift(tmp_path) -> None:
    seed_drift = _write_mutated_frame(
        tmp_path,
        lambda payload: payload["selection"].update(random_seed=99),
    )
    assert _failed_checks(validate_sampling_frame(seed_drift)) == {"selection-controls"}

    source_drift = _write_mutated_frame(
        tmp_path,
        lambda payload: payload["sources"].update(
            queue_ids="https://developer.riotgames.com/unregistered-source"
        ),
    )
    assert _failed_checks(validate_sampling_frame(source_drift)) == {"official-sources"}

    def drift_window(payload: dict[str, object]) -> None:
        patches = payload["patches"]
        assert isinstance(patches, list)
        assert isinstance(patches[0], dict)
        patches[0]["released_on"] = "2026-06-09"

    window_drift = _write_mutated_frame(tmp_path, drift_window)
    assert _failed_checks(validate_sampling_frame(window_drift)) == {"patch-series"}


def test_sampling_coverage_requires_every_exact_cell_target() -> None:
    frame = load_sampling_frame(FRAME_PATH)
    report = validate_sampling_frame(FRAME_PATH)
    summary = report["summary"]
    assert isinstance(summary, dict)
    cells = summary["cells"]
    assert isinstance(cells, list)
    observed = {
        (
            str(cell["regional_route"]),
            str(cell["platform_id"]),
            str(cell["game_version_patch"]),
        ): int(cell["pilot_target"])
        for cell in cells
    }

    complete = sampling_coverage(frame, observed, stage="pilot")
    assert complete["passed"] is True
    assert complete["target_matches"] == 5_000
    assert complete["represented_cells"] == 12

    first_cell = next(iter(observed))
    observed[first_cell] -= 1
    incomplete = sampling_coverage(frame, observed, stage="pilot")
    assert incomplete["passed"] is False
    assert incomplete["observed_in_frame_matches"] == 4_999


def test_sampling_coverage_rejects_unregistered_cells() -> None:
    frame = load_sampling_frame(FRAME_PATH)
    observed = {("europe", "EUW1", "16.12"): 417, ("asia", "KR", "16.12"): 1}

    report = sampling_coverage(frame, observed, stage="pilot")

    assert report["passed"] is False
    assert report["unexpected_cells"] == 1

    with pytest.raises(ValueError, match="cannot be negative"):
        sampling_coverage(frame, {("europe", "EUW1", "16.12"): -1}, stage="pilot")

    with pytest.raises(ValueError, match="Unsupported sampling stage"):
        sampling_coverage(frame, {}, stage="invalid")  # type: ignore[arg-type]


def test_candidate_order_is_seeded_deduplicated_and_outcome_blind() -> None:
    frame = load_sampling_frame(FRAME_PATH)

    ordered = order_candidate_match_ids(
        frame,
        ("EUW1_2", "NA1_3", "EUW1_10", "EUW1_2", ""),
    )

    assert ordered == ("NA1_3", "EUW1_10", "EUW1_2")
    assert candidate_rank_sha256(frame, "EUW1_10") == (
        "53ca4b14eb988234df7ffaa8386e6c5970ad21dd3f433160e770b9622a2071a0"
    )


def test_candidate_order_rejects_malformed_identifiers() -> None:
    frame = load_sampling_frame(FRAME_PATH)

    with pytest.raises(ValueError, match="malformed match ID"):
        order_candidate_match_ids(frame, ("../../private",))
