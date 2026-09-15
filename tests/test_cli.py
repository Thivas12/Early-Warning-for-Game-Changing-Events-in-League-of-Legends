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
