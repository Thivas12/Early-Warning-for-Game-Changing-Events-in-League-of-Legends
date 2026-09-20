from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from league_ews.cli import main
from league_ews.duration import _duration_seconds, analyze_pilot_duration

FRAME_PATH = Path("configs/rifthazard-sampling-frame.yaml")


def _write_pilot(tmp_path: Path) -> tuple[Path, Path]:
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    (raw / "matches").mkdir(parents=True)
    processed.mkdir()

    specifications = (
        ("EUW1_1", 200, True, False),
        ("EUW1_2", 700, False, True),
        ("EUW1_3", 1_300, False, False),
    )
    available = []
    for match_id, duration, early_surrender, surrender in specifications:
        payload = {
            "metadata": {"matchId": match_id},
            "info": {
                "gameDuration": duration,
                "participants": [
                    {
                        "gameEndedInEarlySurrender": early_surrender,
                        "gameEndedInSurrender": surrender,
                    }
                    for _ in range(10)
                ],
            },
        }
        content = json.dumps(payload, sort_keys=True).encode()
        (raw / "matches" / f"{match_id}.json").write_bytes(content)
        available.append(
            {
                "match_id": match_id,
                "regional_route": "europe",
                "game_version": "16.12.1",
                "game_creation_ms": 1,
                "match_sha256": hashlib.sha256(content).hexdigest(),
                "timeline_sha256": "a" * 64,
            }
        )

    raw_manifest = {
        "schema_version": "riot-raw-collection-v2",
        "collected_at": "2026-09-20T00:00:00Z",
        "requested": 3,
        "collected": available,
        "skipped_existing": [],
        "available": available,
        "contains_raw_player_identifiers": True,
        "redistribution": "not-authorized-by-this-manifest",
    }
    raw_manifest_content = (json.dumps(raw_manifest, sort_keys=True) + "\n").encode()
    (raw / "collection-manifest.json").write_bytes(raw_manifest_content)

    frame_content = FRAME_PATH.read_bytes()
    binding = {
        "schema_version": "riot-pilot-collection-binding-v1",
        "recorded_at": "2026-09-20T00:00:00Z",
        "complete": True,
        "frame_id": "rifthazard-2026-09-15",
        "frame_sha256": hashlib.sha256(frame_content).hexdigest(),
        "plan_id": "test-plan",
        "plan_sha256": "b" * 64,
        "discovery_manifest_sha256": "c" * 64,
        "candidate_pool_sha256": "d" * 64,
        "selected_pool_sha256": "e" * 64,
        "collection_manifest_sha256": hashlib.sha256(raw_manifest_content).hexdigest(),
        "expected_selected_match_ids": 3,
        "available_bundles": 3,
        "new_timeline_requests": 3,
        "recovered_unpaired_bundles": 0,
        "identifiers_in_summary": False,
        "redistribution": "not-authorized",
    }
    (raw / "selection-binding.json").write_text(
        json.dumps(binding),
        encoding="utf-8",
    )

    processing_manifest = {
        "schema_version": "league-ews-processing-manifest-v1",
        "normalizer": "riot-match-v5-normalized-v1",
        "label_policy": "exact-future-events-v1",
        "matches": [
            {
                "match_id": match_id,
                "game_version": "16.12.1",
                "observations": 2,
                "baron_events": 0,
                "dragon_events": 0,
                "teamfight_events": 0,
                "sha256": "f" * 64,
            }
            for match_id, *_ in specifications
        ],
        "contains_player_identifiers": False,
    }
    (processed / "processing-manifest.json").write_text(
        json.dumps(processing_manifest),
        encoding="utf-8",
    )
    return raw, processed


def test_duration_analysis_is_checksum_bound_and_identifier_free(tmp_path) -> None:
    raw, processed = _write_pilot(tmp_path)

    report = analyze_pilot_duration(raw, processed, FRAME_PATH)

    assert report["schema_version"] == "league-ews-pilot-duration-analysis-v1"
    assert report["duration"] == {
        "matches": 3,
        "minimum_seconds": 200,
        "mean_seconds": 733.333,
        "percentiles_seconds": {
            "p01": 200,
            "p05": 200,
            "p10": 200,
            "p25": 200,
            "p50": 700,
            "p75": 1_300,
            "p90": 1_300,
            "p95": 1_300,
            "p99": 1_300,
        },
        "maximum_seconds": 1_300,
        "early_surrender_matches": 1,
        "surrender_matches": 1,
        "early_surrender_flag_complete_matches": 3,
        "surrender_flag_complete_matches": 3,
    }
    thresholds = {row["minimum_seconds"]: row for row in report["candidate_minimums"]}
    assert thresholds[300]["excluded_matches"] == 1
    assert thresholds[300]["excluded_early_surrender_matches"] == 1
    assert thresholds[900]["excluded_matches"] == 2
    assert thresholds[900]["excluded_other_matches"] == 1
    assert report["represented_cells"] == 1
    assert report["identifiers_in_summary"] is False
    assert "EUW1_1" not in json.dumps(report)


def test_duration_analysis_rejects_inventory_drift(tmp_path) -> None:
    raw, processed = _write_pilot(tmp_path)
    manifest_path = processed / "processing-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["matches"].pop()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="inventories"):
        analyze_pilot_duration(raw, processed, FRAME_PATH)


@pytest.mark.parametrize("value", [None, True, 0, -1, 1.5, float("inf")])
def test_duration_seconds_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValueError, match="gameDuration"):
        _duration_seconds({"gameDuration": value})


def test_duration_cli_writes_report_after_registered_validation(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    output = tmp_path / "duration.json"
    monkeypatch.setattr(
        "league_ews.cli.validate_raw_collection",
        lambda *args, **kwargs: {"passed": True},
    )
    monkeypatch.setattr(
        "league_ews.cli.analyze_pilot_duration",
        lambda *args, **kwargs: {"schema_version": "test", "identifiers_in_summary": False},
    )

    exit_code = main(
        [
            "analyze-pilot-duration",
            "--raw",
            str(tmp_path / "raw"),
            "--processed",
            str(tmp_path / "processed"),
            "--sampling-frame",
            str(FRAME_PATH),
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--discovery-root",
            str(tmp_path / "discovery"),
            "--selection-root",
            str(tmp_path / "selection"),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == "test"
    assert "checksum-bound" in capsys.readouterr().out


def test_duration_cli_stops_on_failed_registered_validation(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        "league_ews.cli.validate_raw_collection",
        lambda *args, **kwargs: {"passed": False, "checks": []},
    )

    exit_code = main(
        [
            "analyze-pilot-duration",
            "--raw",
            str(tmp_path / "raw"),
            "--processed",
            str(tmp_path / "processed"),
            "--sampling-frame",
            str(FRAME_PATH),
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--discovery-root",
            str(tmp_path / "discovery"),
            "--selection-root",
            str(tmp_path / "selection"),
            "--output",
            str(tmp_path / "duration.json"),
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["passed"] is False
