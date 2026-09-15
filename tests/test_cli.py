from __future__ import annotations

import json

import pytest

from league_ews.cli import main
from tests.helpers import synthetic_legacy_frame


def test_audit_cli_writes_report_and_strict_exit(tmp_path) -> None:
    csv_path = tmp_path / "legacy.csv"
    output = tmp_path / "reports" / "audit.json"
    synthetic_legacy_frame(matches=3).to_csv(csv_path, index=False)

    exit_code = main(["audit", "--csv", str(csv_path), "--output", str(output), "--strict"])

    report = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["passed"] is True
    assert len(report["dataset_sha256"]) == 64


def test_audit_cli_can_print_json(tmp_path, capsys) -> None:
    csv_path = tmp_path / "legacy.csv"
    synthetic_legacy_frame(matches=3).to_csv(csv_path, index=False)

    assert main(["audit", "--csv", str(csv_path), "--nrows", "5"]) == 0
    assert json.loads(capsys.readouterr().out)["rows"] == 5


def test_benchmark_cli_normalises_output_directory(tmp_path, capsys) -> None:
    csv_path = tmp_path / "legacy.csv"
    output = tmp_path / "result"
    synthetic_legacy_frame().to_csv(csv_path, index=False)

    exit_code = main(
        [
            "benchmark",
            "--csv",
            str(csv_path),
            "--output",
            str(output),
            "--baselines",
            "time",
            "--max-iter",
            "2",
            "--threshold-candidates",
            "3",
        ]
    )

    assert exit_code == 0
    assert (output / "benchmark.json").is_file()
    assert "Wrote" in capsys.readouterr().out


def test_benchmark_cli_rejects_unknown_baseline(tmp_path) -> None:
    csv_path = tmp_path / "legacy.csv"
    synthetic_legacy_frame(matches=3).to_csv(csv_path, index=False)
    with pytest.raises(ValueError, match="Unknown baselines"):
        main(
            [
                "benchmark",
                "--csv",
                str(csv_path),
                "--output",
                str(tmp_path / "result.json"),
                "--baselines",
                "oracle",
            ]
        )


def test_split_diagnostic_cli_writes_json(tmp_path) -> None:
    csv_path = tmp_path / "legacy.csv"
    output = tmp_path / "diagnostic.json"
    synthetic_legacy_frame(matches=5, timestamps=50).to_csv(csv_path, index=False)

    assert (
        main(
            [
                "diagnose-split",
                "--csv",
                str(csv_path),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_collect_fails_authority_gate_before_client_creation(tmp_path, monkeypatch, capsys) -> None:
    def forbidden_client_creation(*args: object, **kwargs: object) -> None:
        raise AssertionError("the Riot client must not be constructed")

    monkeypatch.setattr(
        "league_ews.cli.RiotMatchClient.from_environment",
        forbidden_client_creation,
    )
    match_ids = tmp_path / "matches.txt"
    match_ids.write_text("EUW1_123\n", encoding="utf-8")

    exit_code = main(
        [
            "collect",
            "--authority-record",
            str(tmp_path / "missing-authority.yaml"),
            "--match-ids",
            str(match_ids),
            "--region",
            "europe",
        ]
    )

    assert exit_code == 2
    report = json.loads(capsys.readouterr().out)
    assert report["passed"] is False
    assert report["checks"][0]["check_id"] == "record-schema"


def test_preflight_cli_writes_failure_report(tmp_path) -> None:
    output = tmp_path / "preflight.json"

    exit_code = main(
        [
            "preflight-collection",
            "--record",
            str(tmp_path / "missing-authority.yaml"),
            "--region",
            "europe",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 2
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_collect_proceeds_after_successful_gate(tmp_path, monkeypatch, capsys) -> None:
    events: list[str] = []

    def fake_preflight(record, *, requested_region: str) -> dict[str, object]:
        events.append("preflight")
        assert record == tmp_path / "authority.yaml"
        assert requested_region == "europe"
        return {"passed": True}

    class FakeClient:
        @classmethod
        def from_environment(cls, *, regional_route: str):
            events.append("client")
            assert regional_route == "europe"
            return cls()

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_collect(match_ids, *, regional_route, output_root, fetcher, overwrite):
        events.append("collect")
        assert list(match_ids) == ["EUW1_123"]
        assert regional_route == "europe"
        assert output_root == tmp_path / "raw"
        assert isinstance(fetcher, FakeClient)
        assert overwrite is False
        return {"collected": [], "skipped_existing": []}

    monkeypatch.setattr("league_ews.cli.collection_preflight", fake_preflight)
    monkeypatch.setattr("league_ews.cli.RiotMatchClient", FakeClient)
    monkeypatch.setattr("league_ews.cli.collect_match_bundles", fake_collect)
    match_ids = tmp_path / "matches.txt"
    match_ids.write_text("EUW1_123\n", encoding="utf-8")

    exit_code = main(
        [
            "collect",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--match-ids",
            str(match_ids),
            "--output",
            str(tmp_path / "raw"),
            "--region",
            "europe",
        ]
    )

    assert exit_code == 0
    assert events == ["preflight", "client", "collect"]
    assert "Collected 0" in capsys.readouterr().out


def test_validate_raw_cli_writes_failure_report(tmp_path) -> None:
    output = tmp_path / "raw-validation.json"

    exit_code = main(
        [
            "validate-raw",
            "--raw",
            str(tmp_path / "missing"),
            "--output",
            str(output),
            "--min-routes",
            "1",
            "--min-patches",
            "1",
        ]
    )

    assert exit_code == 2
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_process_fails_raw_gate_before_writing_outputs(tmp_path, monkeypatch, capsys) -> None:
    def forbidden_processing(*args: object, **kwargs: object) -> None:
        raise AssertionError("processing must not start")

    monkeypatch.setattr("league_ews.cli.process_raw_collection", forbidden_processing)

    exit_code = main(
        [
            "process",
            "--raw",
            str(tmp_path / "missing"),
            "--output",
            str(tmp_path / "processed"),
            "--min-routes",
            "1",
            "--min-patches",
            "1",
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["passed"] is False
    assert not (tmp_path / "processed").exists()


def test_process_runs_only_after_successful_raw_gate(tmp_path, monkeypatch, capsys) -> None:
    events: list[str] = []

    def fake_validation(raw, *, min_routes: int, min_patches: int) -> dict[str, object]:
        events.append("validate")
        assert raw == tmp_path / "raw"
        assert min_routes == 1
        assert min_patches == 1
        return {"passed": True}

    def fake_processing(raw, *, output_root) -> dict[str, object]:
        events.append("process")
        assert raw == tmp_path / "raw"
        assert output_root == tmp_path / "processed"
        return {"matches": []}

    monkeypatch.setattr("league_ews.cli.validate_raw_collection", fake_validation)
    monkeypatch.setattr("league_ews.cli.process_raw_collection", fake_processing)

    exit_code = main(
        [
            "process",
            "--raw",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "processed"),
            "--min-routes",
            "1",
            "--min-patches",
            "1",
        ]
    )

    assert exit_code == 0
    assert events == ["validate", "process"]
    assert "Processed 0" in capsys.readouterr().out
