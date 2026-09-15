from __future__ import annotations

import json
from datetime import UTC, datetime

from league_ews.cli import main
from league_ews.raw_validation import validate_raw_collection
from league_ews.riot import collect_match_bundles


def _bundle(
    match_id: str = "EUW1_1", game_version: str = "16.18.1"
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
                            "timestamp": 55_000,
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
    def __init__(self, game_version: str = "16.18.1") -> None:
        self.game_version = game_version

    def get_match(self, match_id: str) -> dict[str, object]:
        return _bundle(match_id, self.game_version)[0]

    def get_timeline(self, match_id: str) -> dict[str, object]:
        return _bundle(match_id, self.game_version)[1]


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


def test_raw_validation_accepts_integral_pilot_and_summarizes_events(tmp_path) -> None:
    _collect(tmp_path)

    report = validate_raw_collection(
        tmp_path,
        min_routes=1,
        min_patches=1,
        checked_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    assert report["passed"] is True
    assert report["g2_complete"] is False
    assert report["manual_event_spot_check"] == "pending"
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
    assert "private-puuid" not in json.dumps(report)


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
    assert _failed_checks(report) == {"manifest-schema"}


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
