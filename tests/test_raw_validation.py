from __future__ import annotations

import json
from datetime import UTC, datetime

from league_ews.cli import main
from league_ews.processing import process_raw_collection
from league_ews.raw_validation import create_event_spot_check_record, validate_raw_collection
from league_ews.riot import collect_match_bundles


def _bundle(
    match_id: str = "EUW1_1",
    game_version: str = "16.18.1",
    event_timestamp_ms: int = 55_000,
) -> tuple[dict[str, object], dict[str, object]]:
    detail = {
        "metadata": {"matchId": match_id, "participants": ["private-puuid"] * 10},
        "info": {
            "gameVersion": game_version,
            "gameCreation": 123,
            "platformId": match_id.split("_", maxsplit=1)[0],
            "participants": [
                {"participantId": participant, "teamId": 100 if participant <= 5 else 200}
                for participant in range(1, 11)
            ],
        },
    }

    def participant_frames() -> dict[str, object]:
        return {
            str(participant): {
                "totalGold": 500,
                "xp": 0,
                "level": 1,
                "minionsKilled": 0,
                "jungleMinionsKilled": 0,
                "position": {"x": participant, "y": participant},
            }
            for participant in range(1, 11)
        }

    timeline = {
        "metadata": {"matchId": match_id, "participants": ["private-puuid"] * 10},
        "info": {
            "frames": [
                {"timestamp": 0, "participantFrames": participant_frames(), "events": []},
                {
                    "timestamp": 60_000,
                    "participantFrames": participant_frames(),
                    "events": [
                        {
                            "timestamp": event_timestamp_ms,
                            "type": "ELITE_MONSTER_KILL",
                            "monsterType": "DRAGON",
                            "killerTeamId": 100,
                        }
                    ],
                },
            ]
        },
    }
    return detail, timeline


class FakeFetcher:
    def __init__(
        self,
        game_version: str = "16.18.1",
        event_timestamp_ms: int = 55_000,
    ) -> None:
        self.game_version = game_version
        self.event_timestamp_ms = event_timestamp_ms

    def get_match(self, match_id: str) -> dict[str, object]:
        return _bundle(match_id, self.game_version, self.event_timestamp_ms)[0]

    def get_timeline(self, match_id: str) -> dict[str, object]:
        return _bundle(match_id, self.game_version, self.event_timestamp_ms)[1]


def _collect(root) -> None:
    collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=root,
        fetcher=FakeFetcher(),
        collected_at=datetime(2026, 9, 15, tzinfo=UTC),
    )


def _failed_checks(report: dict[str, object]) -> set[str]:
    checks = report["checks"]
    assert isinstance(checks, list)
    return {
        str(check["check_id"])
        for check in checks
        if isinstance(check, dict) and check["passed"] is False
    }


def _write_spot_check(root, processed, output, *match_ids: str) -> None:
    process_raw_collection(root, output_root=processed)
    record = create_event_spot_check_record(
        root,
        processed,
        tuple(match_ids),
        objective_events_match_source=True,
        teamfight_episodes_match_source=True,
        strict_future_labels_match_processed=True,
        reviewed_at=datetime(2026, 9, 15, tzinfo=UTC),
    )
    output.write_text(json.dumps(record), encoding="utf-8")


def test_raw_validation_accepts_integral_pilot_and_summarizes_events(tmp_path) -> None:
    _collect(tmp_path)

    report = validate_raw_collection(
        tmp_path,
        min_routes=1,
        min_patches=1,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    assert report["passed"] is True
    assert report["automated_passed"] is True
    assert report["schema_version"] == "riot-raw-validation-v3"
    assert report["g2_complete"] is False
    spot_check = report["manual_event_spot_check"]
    assert isinstance(spot_check, dict)
    assert spot_check["status"] == "pending"
    assert len(str(report["manifest_sha256"])) == 64
    assert report["coverage_requirements"] == {
        "min_regional_routes": 1,
        "min_patches": 1,
    }
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["manifest_bundles"] == 1
    assert summary["valid_bundles"] == 1
    assert summary["events"] == {"baron": 0, "dragon": 1, "teamfight": 0}
    assert summary["observation_cadence_ms"] == {
        "interval_count": 1,
        "minimum": 60_000,
        "median": 60_000,
        "maximum": 60_000,
    }
    labelability = summary["event_labelability"]
    assert isinstance(labelability, dict)
    assert labelability["dragon"] == {
        "total_events": 1,
        "by_horizon_seconds": {
            "10": {"labelable_events": 0, "fraction": 0.0},
            "20": {"labelable_events": 0, "fraction": 0.0},
            "30": {"labelable_events": 0, "fraction": 0.0},
            "60": {"labelable_events": 1, "fraction": 1.0},
        },
    }
    assert labelability["baron"]["by_horizon_seconds"]["60"]["fraction"] is None
    assert "private-puuid" not in json.dumps(report)


def test_checksum_bound_manual_spot_check_passes_without_exposing_match_id(
    tmp_path,
) -> None:
    _collect(tmp_path)
    processed = tmp_path / "processed"
    record_path = tmp_path / "private-event-spot-check.json"
    _write_spot_check(tmp_path, processed, record_path, "EUW1_1")

    report = validate_raw_collection(
        tmp_path,
        min_routes=1,
        min_patches=1,
        event_spot_check=record_path,
        processed_root=processed,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    spot_check = report["manual_event_spot_check"]
    assert isinstance(spot_check, dict)
    assert spot_check["status"] == "passed"
    assert spot_check["sampled_bundles"] == 1
    assert spot_check["covered_route_patch_cells"] == 1
    assert spot_check["required_route_patch_cells"] == 1
    assert report["g2_complete"] is False
    rendered = json.dumps(report)
    assert "EUW1_1" not in rendered
    assert "private-puuid" not in rendered


def test_manual_spot_check_fails_after_manifest_changes(tmp_path) -> None:
    _collect(tmp_path)
    processed = tmp_path / "processed"
    record_path = tmp_path / "private-event-spot-check.json"
    _write_spot_check(tmp_path, processed, record_path, "EUW1_1")
    collect_match_bundles(
        ["EUW1_2"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=FakeFetcher(),
        collected_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    report = validate_raw_collection(
        tmp_path,
        min_routes=1,
        min_patches=1,
        event_spot_check=record_path,
        processed_root=processed,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    assert report["automated_passed"] is True
    assert report["passed"] is False
    spot_check = report["manual_event_spot_check"]
    assert isinstance(spot_check, dict)
    assert spot_check["status"] == "failed"
    failed = {check["check_id"] for check in spot_check["checks"] if check["passed"] is False}
    assert failed == {"manifest-binding", "processing-inventory"}


def test_manual_spot_check_detects_processed_file_tampering(tmp_path) -> None:
    _collect(tmp_path)
    processed = tmp_path / "processed"
    record_path = tmp_path / "private-event-spot-check.json"
    _write_spot_check(tmp_path, processed, record_path, "EUW1_1")
    processed_match = processed / "matches" / "EUW1_1.json"
    processed_match.write_text(
        processed_match.read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )

    report = validate_raw_collection(
        tmp_path,
        min_routes=1,
        min_patches=1,
        event_spot_check=record_path,
        processed_root=processed,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    assert report["automated_passed"] is True
    assert report["passed"] is False
    spot_check = report["manual_event_spot_check"]
    assert isinstance(spot_check, dict)
    failed = {check["check_id"] for check in spot_check["checks"] if check["passed"] is False}
    assert failed == {"processed-sample-checksums"}


def test_manual_spot_check_must_cover_every_observed_route_patch_cell(tmp_path) -> None:
    collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=FakeFetcher("16.18.1"),
        collected_at=datetime(2026, 9, 15, tzinfo=UTC),
    )
    collect_match_bundles(
        ["NA1_2"],
        regional_route="americas",
        output_root=tmp_path,
        fetcher=FakeFetcher("16.19.1"),
        collected_at=datetime(2026, 9, 15, tzinfo=UTC),
    )
    processed = tmp_path / "processed"
    record_path = tmp_path / "private-event-spot-check.json"
    _write_spot_check(tmp_path, processed, record_path, "EUW1_1")

    report = validate_raw_collection(
        tmp_path,
        min_routes=2,
        min_patches=2,
        event_spot_check=record_path,
        processed_root=processed,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    spot_check = report["manual_event_spot_check"]
    assert isinstance(spot_check, dict)
    assert spot_check["status"] == "failed"
    assert report["passed"] is False
    assert spot_check["covered_route_patch_cells"] == 1
    assert spot_check["required_route_patch_cells"] == 2


def test_event_labelability_requires_a_strictly_prior_observation(tmp_path) -> None:
    collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=FakeFetcher(event_timestamp_ms=60_000),
        collected_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    report = validate_raw_collection(
        tmp_path,
        min_routes=1,
        min_patches=1,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    summary = report["summary"]
    assert isinstance(summary, dict)
    labelability = summary["event_labelability"]
    assert isinstance(labelability, dict)
    dragon = labelability["dragon"]
    assert dragon["by_horizon_seconds"]["10"]["labelable_events"] == 0
    assert dragon["by_horizon_seconds"]["60"]["labelable_events"] == 1


def test_raw_validation_detects_checksum_tampering(tmp_path) -> None:
    _collect(tmp_path)
    timeline_path = tmp_path / "timelines" / "EUW1_1.json"
    timeline_path.write_text(
        timeline_path.read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )

    report = validate_raw_collection(
        tmp_path,
        min_routes=1,
        min_patches=1,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    assert report["passed"] is False
    assert _failed_checks(report) == {
        "checksums",
        "patch-coverage",
        "route-coverage",
    }
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["valid_bundles"] == 0


def test_raw_validation_counts_cumulative_routes_and_patches(tmp_path) -> None:
    collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=FakeFetcher("16.18.1"),
    )
    collect_match_bundles(
        ["NA1_2"],
        regional_route="americas",
        output_root=tmp_path,
        fetcher=FakeFetcher("16.19.1"),
    )

    report = validate_raw_collection(
        tmp_path,
        min_routes=2,
        min_patches=2,
        checked_at=datetime.now(UTC),
    )

    assert report["passed"] is True
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["regional_routes"] == {"americas": 1, "europe": 1}
    assert summary["patches"] == {"16.18": 1, "16.19": 1}


def test_raw_validation_enforces_preregistered_coverage(tmp_path) -> None:
    _collect(tmp_path)

    report = validate_raw_collection(
        tmp_path,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    assert _failed_checks(report) == {"route-coverage", "patch-coverage"}


def test_raw_validation_fails_closed_for_missing_manifest(tmp_path) -> None:
    report = validate_raw_collection(
        tmp_path,
        min_routes=1,
        min_patches=1,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    assert report["passed"] is False
    assert report["automated_passed"] is False
    assert _failed_checks(report) == {"manifest-schema"}
    assert report["summary"]["observation_cadence_ms"] == {
        "interval_count": 0,
        "minimum": None,
        "median": None,
        "maximum": None,
    }


def test_record_event_spot_check_cli_writes_private_evidence(tmp_path, capsys) -> None:
    _collect(tmp_path)
    processed = tmp_path / "processed"
    process_raw_collection(tmp_path, output_root=processed)
    output = tmp_path / "event-spot-check.json"

    exit_code = main(
        [
            "record-event-spot-check",
            "--raw",
            str(tmp_path),
            "--processed",
            str(processed),
            "--match-id",
            "EUW1_1",
            "--output",
            str(output),
            "--confirm-objective-events",
            "--confirm-teamfight-episodes",
            "--confirm-future-labels",
        ]
    )

    assert exit_code == 0
    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["schema_version"] == "riot-event-spot-check-v1"
    assert record["samples"][0]["match_id"] == "EUW1_1"
    assert len(record["samples"][0]["processed_sha256"]) == 64
    assert "EUW1_1" not in capsys.readouterr().out


def test_validated_raw_bundle_processes_end_to_end(tmp_path) -> None:
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    _collect(raw)

    exit_code = main(
        [
            "process",
            "--raw",
            str(raw),
            "--output",
            str(processed),
            "--min-routes",
            "1",
            "--min-patches",
            "1",
        ]
    )

    assert exit_code == 0
    assert (processed / "matches" / "EUW1_1.json").is_file()
    manifest = json.loads((processed / "processing-manifest.json").read_text(encoding="utf-8"))
    assert manifest["contains_player_identifiers"] is False
