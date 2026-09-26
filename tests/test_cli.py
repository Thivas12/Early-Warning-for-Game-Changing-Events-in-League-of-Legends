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


def test_discovery_plan_cli_passes_offline(tmp_path) -> None:
    output = tmp_path / "discovery-plan.json"

    exit_code = main(
        [
            "validate-discovery-plan",
            "--plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True


def test_discovery_preflight_cli_fails_without_private_record(tmp_path) -> None:
    output = tmp_path / "discovery-preflight.json"

    exit_code = main(
        [
            "preflight-discovery",
            "--authority-record",
            str(tmp_path / "missing.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 2
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_discover_cli_repeats_gate_before_client_creation(tmp_path, monkeypatch, capsys) -> None:
    def forbidden_client(*args: object, **kwargs: object) -> None:
        raise AssertionError("Riot clients must not be created before discovery preflight")

    monkeypatch.setattr("league_ews.cli.RiotPlatformClient.from_environment", forbidden_client)
    monkeypatch.setattr("league_ews.cli.RiotMatchClient.from_environment", forbidden_client)

    exit_code = main(
        [
            "discover-candidates",
            "--authority-record",
            str(tmp_path / "missing.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--output",
            str(tmp_path / "discovery"),
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["passed"] is False


def test_discover_cli_builds_all_clients_after_preflight(tmp_path, monkeypatch, capsys) -> None:
    events: list[str] = []

    monkeypatch.setattr(
        "league_ews.cli.candidate_discovery_preflight",
        lambda *args, **kwargs: {"passed": True},
    )

    class FakeClient:
        def __init__(self, name: str) -> None:
            self.name = name

        def __enter__(self):
            events.append(f"enter:{self.name}")
            return self

        def __exit__(self, *args: object) -> None:
            events.append(f"exit:{self.name}")

    class FakePlatformClient:
        @classmethod
        def from_environment(cls, *, platform_id: str, pace):
            assert callable(pace)
            return FakeClient(platform_id)

    class FakeMatchClient:
        @classmethod
        def from_environment(cls, *, regional_route: str, pace):
            assert callable(pace)
            return FakeClient(regional_route)

    def fake_discover(
        frame,
        plan,
        *,
        output_root,
        platform_fetchers,
        regional_fetchers,
        progress,
    ) -> dict[str, object]:
        events.append("discover")
        assert set(platform_fetchers) == {"EUW1", "NA1"}
        assert set(regional_fetchers) == {"europe", "americas"}
        assert output_root == tmp_path / "discovery"
        progress("safe progress")
        return {"complete": True, "candidate_match_ids": 10_000}

    monkeypatch.setattr("league_ews.cli.RiotPlatformClient", FakePlatformClient)
    monkeypatch.setattr("league_ews.cli.RiotMatchClient", FakeMatchClient)
    monkeypatch.setattr("league_ews.cli.discover_candidate_pool", fake_discover)

    exit_code = main(
        [
            "discover-candidates",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--output",
            str(tmp_path / "discovery"),
            "--request-interval",
            "0",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["complete"] is True
    assert "safe progress" in captured.err
    assert events[:4] == ["enter:EUW1", "enter:NA1", "enter:europe", "enter:americas"]
    assert events[4] == "discover"


def test_candidate_pool_validation_cli_writes_safe_report(tmp_path, monkeypatch) -> None:
    output = tmp_path / "candidate-pool-validation.json"

    def fake_validation(frame, plan, discovery_root):
        assert discovery_root == tmp_path / "discovery"
        return {"passed": True, "summary": {"candidate_match_ids": 24_976}}

    monkeypatch.setattr("league_ews.cli.validate_candidate_pool", fake_validation)
    exit_code = main(
        [
            "validate-candidate-pool",
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--discovery-root",
            str(tmp_path / "discovery"),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True


def test_final_discovery_plan_validation_cli_writes_report(tmp_path) -> None:
    output = tmp_path / "final-plan.json"

    exit_code = main(
        [
            "validate-final-discovery-plan",
            "--plan",
            "configs/rifthazard-final-discovery-plan.yaml",
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--output",
            str(output),
        ]
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["passed"] is True
    assert report["summary"]["pilot_match_ids_excluded"] == 5_000


def test_final_discover_cli_repeats_gate_before_client_creation(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        "league_ews.cli.final_candidate_discovery_preflight",
        lambda *args, **kwargs: {"passed": False},
    )

    def forbidden_client(*args: object, **kwargs: object) -> None:
        raise AssertionError("Riot clients must not be created before final preflight")

    monkeypatch.setattr("league_ews.cli.RiotPlatformClient.from_environment", forbidden_client)
    monkeypatch.setattr("league_ews.cli.RiotMatchClient.from_environment", forbidden_client)
    exit_code = main(
        [
            "discover-final-candidates",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--final-discovery-plan",
            "configs/rifthazard-final-discovery-plan.yaml",
            "--duration-rule",
            "configs/rifthazard-duration-rule.yaml",
            "--duration-analysis",
            str(tmp_path / "duration.json"),
            "--pilot-discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--pilot-discovery-root",
            str(tmp_path / "pilot-discovery"),
            "--pilot-selection-root",
            str(tmp_path / "pilot-selection"),
            "--output",
            str(tmp_path / "final-discovery"),
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["passed"] is False


def test_final_discovery_preflight_cli_writes_private_report(
    tmp_path,
    monkeypatch,
) -> None:
    output = tmp_path / "preflight.json"
    monkeypatch.setattr(
        "league_ews.cli.final_candidate_discovery_preflight",
        lambda *args: {"passed": True, "bindings": {"pilot_match_ids_excluded": 5_000}},
    )

    exit_code = main(
        [
            "preflight-final-discovery",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--final-discovery-plan",
            "configs/rifthazard-final-discovery-plan.yaml",
            "--duration-rule",
            "configs/rifthazard-duration-rule.yaml",
            "--duration-analysis",
            str(tmp_path / "duration.json"),
            "--pilot-discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--pilot-discovery-root",
            str(tmp_path / "pilot-discovery"),
            "--pilot-selection-root",
            str(tmp_path / "pilot-selection"),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True


def test_final_discover_cli_builds_all_clients_after_preflight(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        "league_ews.cli.final_candidate_discovery_preflight",
        lambda *args, **kwargs: {"passed": True},
    )

    class FakeClient:
        def __init__(self, name: str) -> None:
            self.name = name

        def __enter__(self):
            events.append(f"enter:{self.name}")
            return self

        def __exit__(self, *args: object) -> None:
            events.append(f"exit:{self.name}")

    class FakePlatformClient:
        @classmethod
        def from_environment(cls, *, platform_id: str, pace):
            assert callable(pace)
            return FakeClient(platform_id)

    class FakeMatchClient:
        @classmethod
        def from_environment(cls, *, regional_route: str, pace):
            assert callable(pace)
            return FakeClient(regional_route)

    def fake_discover(*args, output_root, platform_fetchers, regional_fetchers, progress):
        events.append("discover")
        assert len(args) == 7
        assert output_root == tmp_path / "final-discovery"
        assert set(platform_fetchers) == {"EUW1", "NA1"}
        assert set(regional_fetchers) == {"europe", "americas"}
        progress("safe final progress")
        return {"complete": True, "candidate_match_ids": 72_000}

    monkeypatch.setattr("league_ews.cli.RiotPlatformClient", FakePlatformClient)
    monkeypatch.setattr("league_ews.cli.RiotMatchClient", FakeMatchClient)
    monkeypatch.setattr("league_ews.cli.discover_final_candidate_pool", fake_discover)

    exit_code = main(
        [
            "discover-final-candidates",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--final-discovery-plan",
            "configs/rifthazard-final-discovery-plan.yaml",
            "--duration-rule",
            "configs/rifthazard-duration-rule.yaml",
            "--duration-analysis",
            str(tmp_path / "duration.json"),
            "--pilot-discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--pilot-discovery-root",
            str(tmp_path / "pilot-discovery"),
            "--pilot-selection-root",
            str(tmp_path / "pilot-selection"),
            "--output",
            str(tmp_path / "final-discovery"),
            "--request-interval",
            "0",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["complete"] is True
    assert "safe final progress" in captured.err
    assert events[:4] == ["enter:EUW1", "enter:NA1", "enter:europe", "enter:americas"]


def test_final_candidate_pool_validation_cli_writes_safe_report(
    tmp_path,
    monkeypatch,
) -> None:
    output = tmp_path / "final-validation.json"
    monkeypatch.setattr(
        "league_ews.cli.validate_final_candidate_pool",
        lambda *args: {"passed": True, "summary": {"candidate_match_ids": 72_000}},
    )

    exit_code = main(
        [
            "validate-final-candidate-pool",
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--final-discovery-plan",
            "configs/rifthazard-final-discovery-plan.yaml",
            "--duration-rule",
            "configs/rifthazard-duration-rule.yaml",
            "--duration-analysis",
            str(tmp_path / "duration.json"),
            "--pilot-discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--pilot-discovery-root",
            str(tmp_path / "pilot-discovery"),
            "--pilot-selection-root",
            str(tmp_path / "pilot-selection"),
            "--final-discovery-root",
            str(tmp_path / "final-discovery"),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True


def _final_selection_args(tmp_path) -> list[str]:
    return [
        "--sampling-frame",
        "configs/rifthazard-sampling-frame.yaml",
        "--final-selection-plan",
        "configs/rifthazard-final-selection-plan.yaml",
        "--final-discovery-plan",
        "configs/rifthazard-final-discovery-plan.yaml",
        "--duration-rule",
        "configs/rifthazard-duration-rule.yaml",
        "--duration-analysis",
        str(tmp_path / "duration.json"),
        "--pilot-discovery-plan",
        "configs/rifthazard-discovery-plan.yaml",
        "--pilot-discovery-root",
        str(tmp_path / "pilot-discovery"),
        "--pilot-selection-root",
        str(tmp_path / "pilot-selection"),
        "--final-discovery-root",
        str(tmp_path / "final-discovery"),
    ]


def test_final_selection_plan_validation_cli_writes_report(tmp_path) -> None:
    output = tmp_path / "final-selection-plan.json"
    exit_code = main(
        [
            "validate-final-selection-plan",
            "--plan",
            "configs/rifthazard-final-selection-plan.yaml",
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--final-discovery-plan",
            "configs/rifthazard-final-discovery-plan.yaml",
            "--duration-rule",
            "configs/rifthazard-duration-rule.yaml",
            "--output",
            str(output),
        ]
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["passed"] is True
    assert report["summary"]["target_matches"] == 36_000


def test_final_selection_preflight_cli_writes_private_report(tmp_path, monkeypatch) -> None:
    output = tmp_path / "final-selection-preflight.json"
    monkeypatch.setattr(
        "league_ews.cli.final_selection_preflight",
        lambda *args: {"passed": True, "bindings": {"target_matches": 36_000}},
    )
    exit_code = main(
        [
            "preflight-final-selection",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            *_final_selection_args(tmp_path),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True


def test_select_final_repeats_gate_before_client_creation(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        "league_ews.cli.final_selection_preflight",
        lambda *args, **kwargs: {"passed": False},
    )

    def forbidden_client(*args: object, **kwargs: object) -> None:
        raise AssertionError("Riot clients must not be created before final selection preflight")

    monkeypatch.setattr("league_ews.cli.RiotMatchClient.from_environment", forbidden_client)
    exit_code = main(
        [
            "select-final",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            *_final_selection_args(tmp_path),
            "--output",
            str(tmp_path / "final-selection"),
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["passed"] is False


def test_select_final_builds_regional_clients_after_preflight(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        "league_ews.cli.final_selection_preflight",
        lambda *args, **kwargs: {"passed": True},
    )

    class FakeClient:
        def __init__(self, route: str) -> None:
            self.route = route

        @classmethod
        def from_environment(cls, *, regional_route: str, pace):
            assert callable(pace)
            events.append(f"create:{regional_route}")
            return cls(regional_route)

        def __enter__(self):
            events.append(f"enter:{self.route}")
            return self

        def __exit__(self, *args: object) -> None:
            events.append(f"exit:{self.route}")

    def fake_select(
        *args,
        output_root,
        regional_fetchers,
        max_new_requests,
        progress,
    ):
        events.append("select")
        assert len(args) == 9
        assert output_root == tmp_path / "final-selection"
        assert set(regional_fetchers) == {"europe", "americas"}
        assert max_new_requests == 250
        progress("safe final selection progress")
        return {"complete": True, "selected_match_ids": 36_000}

    monkeypatch.setattr("league_ews.cli.RiotMatchClient", FakeClient)
    monkeypatch.setattr("league_ews.cli.select_final_matches", fake_select)
    exit_code = main(
        [
            "select-final",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            *_final_selection_args(tmp_path),
            "--output",
            str(tmp_path / "final-selection"),
            "--request-interval",
            "0",
            "--max-new-requests",
            "250",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["selected_match_ids"] == 36_000
    assert "safe final selection progress" in captured.err
    assert events[:4] == [
        "create:europe",
        "enter:europe",
        "create:americas",
        "enter:americas",
    ]
    assert events[4] == "select"


def test_validate_frozen_final_selection_cli_writes_report(
    tmp_path,
    monkeypatch,
) -> None:
    output = tmp_path / "final-selection-validation.json"
    monkeypatch.setattr(
        "league_ews.cli.validate_frozen_final_selection",
        lambda *args: {"passed": True, "summary": {"selected_match_ids": 36_000}},
    )
    exit_code = main(
        [
            "validate-final-selection",
            *_final_selection_args(tmp_path),
            "--final-selection-root",
            str(tmp_path / "final-selection"),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True


def test_pilot_selection_preflight_cli_fails_closed(tmp_path) -> None:
    output = tmp_path / "selection-preflight.json"
    exit_code = main(
        [
            "preflight-pilot-selection",
            "--authority-record",
            str(tmp_path / "missing-authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--discovery-root",
            str(tmp_path / "missing-discovery"),
            "--output",
            str(output),
        ]
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 2
    assert report["passed"] is False
    assert report["authority"]["passed"] is False
    assert report["candidate_pool"]["passed"] is False


def test_select_pilot_repeats_gate_before_client_creation(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "league_ews.cli.pilot_selection_preflight",
        lambda *args, **kwargs: {"passed": False},
    )

    def forbidden_client(*args: object, **kwargs: object) -> None:
        raise AssertionError("Riot clients must not be created before selection preflight")

    monkeypatch.setattr("league_ews.cli.RiotMatchClient.from_environment", forbidden_client)
    exit_code = main(
        [
            "select-pilot",
            "--authority-record",
            str(tmp_path / "missing.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--discovery-root",
            str(tmp_path / "discovery"),
            "--output",
            str(tmp_path / "selection"),
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["passed"] is False


def test_select_pilot_builds_regional_clients_after_preflight(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        "league_ews.cli.pilot_selection_preflight",
        lambda *args, **kwargs: {"passed": True},
    )

    class FakeClient:
        def __init__(self, route: str) -> None:
            self.route = route

        @classmethod
        def from_environment(cls, *, regional_route: str, pace):
            assert callable(pace)
            events.append(f"create:{regional_route}")
            return cls(regional_route)

        def __enter__(self):
            events.append(f"enter:{self.route}")
            return self

        def __exit__(self, *args: object) -> None:
            events.append(f"exit:{self.route}")

    def fake_select(
        frame,
        plan,
        discovery_root,
        *,
        output_root,
        regional_fetchers,
        max_new_requests,
        progress,
    ):
        events.append("select")
        assert set(regional_fetchers) == {"europe", "americas"}
        assert max_new_requests == 100
        progress("safe progress")
        return {"complete": True, "selected_match_ids": 5_000}

    monkeypatch.setattr("league_ews.cli.RiotMatchClient", FakeClient)
    monkeypatch.setattr("league_ews.cli.select_pilot_matches", fake_select)
    exit_code = main(
        [
            "select-pilot",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--discovery-root",
            str(tmp_path / "discovery"),
            "--output",
            str(tmp_path / "selection"),
            "--request-interval",
            "0",
            "--max-new-requests",
            "100",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["selected_match_ids"] == 5_000
    assert "safe progress" in captured.err
    assert events[:4] == [
        "create:europe",
        "enter:europe",
        "create:americas",
        "enter:americas",
    ]
    assert events[4] == "select"


def test_validate_frozen_pilot_selection_cli_writes_report(
    tmp_path,
    monkeypatch,
) -> None:
    output = tmp_path / "validation.json"
    monkeypatch.setattr(
        "league_ews.cli.validate_frozen_pilot_selection",
        lambda *args: {"passed": True, "summary": {"selected_match_ids": 5_000}},
    )

    exit_code = main(
        [
            "validate-pilot-selection",
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
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
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True


def test_pilot_collection_preflight_cli_writes_failure(
    tmp_path,
    monkeypatch,
) -> None:
    output = tmp_path / "preflight.json"
    monkeypatch.setattr(
        "league_ews.cli.pilot_collection_preflight",
        lambda *args: {"passed": False},
    )

    exit_code = main(
        [
            "preflight-pilot-collection",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
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

    assert exit_code == 2
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_collect_selected_pilot_gates_before_client_creation(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        "league_ews.cli.pilot_collection_preflight",
        lambda *args: {"passed": False},
    )

    def forbidden_client(*args: object, **kwargs: object) -> None:
        raise AssertionError("Riot clients must not be created before pilot preflight")

    monkeypatch.setattr("league_ews.cli.RiotMatchClient.from_environment", forbidden_client)
    exit_code = main(
        [
            "collect-selected-pilot",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--discovery-root",
            str(tmp_path / "discovery"),
            "--selection-root",
            str(tmp_path / "selection"),
            "--output",
            str(tmp_path / "raw"),
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["passed"] is False


def test_collect_selected_pilot_builds_clients_after_preflight(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        "league_ews.cli.pilot_collection_preflight",
        lambda *args: {"passed": True},
    )

    class FakeClient:
        def __init__(self, route: str) -> None:
            self.route = route

        @classmethod
        def from_environment(cls, *, regional_route: str, pace):
            assert callable(pace)
            events.append(f"create:{regional_route}")
            return cls(regional_route)

        def __enter__(self):
            events.append(f"enter:{self.route}")
            return self

        def __exit__(self, *args: object) -> None:
            events.append(f"exit:{self.route}")

    def fake_collect(
        frame,
        plan,
        discovery_root,
        selection_root,
        *,
        output_root,
        regional_fetchers,
        max_new_requests,
        progress,
    ):
        events.append("collect")
        assert set(regional_fetchers) == {"europe", "americas"}
        assert discovery_root == tmp_path / "discovery"
        assert selection_root == tmp_path / "selection"
        assert output_root == tmp_path / "raw"
        assert max_new_requests == 7
        progress("safe progress")
        return {
            "complete": True,
            "available_bundles": 5_000,
            "identifiers_in_summary": False,
        }

    monkeypatch.setattr("league_ews.cli.RiotMatchClient", FakeClient)
    monkeypatch.setattr("league_ews.cli.collect_selected_pilot_bundles", fake_collect)
    exit_code = main(
        [
            "collect-selected-pilot",
            "--authority-record",
            str(tmp_path / "authority.yaml"),
            "--sampling-frame",
            "configs/rifthazard-sampling-frame.yaml",
            "--discovery-plan",
            "configs/rifthazard-discovery-plan.yaml",
            "--discovery-root",
            str(tmp_path / "discovery"),
            "--selection-root",
            str(tmp_path / "selection"),
            "--output",
            str(tmp_path / "raw"),
            "--request-interval",
            "0",
            "--max-new-requests",
            "7",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["available_bundles"] == 5_000
    assert "safe progress" in captured.err
    assert events[:4] == [
        "create:europe",
        "enter:europe",
        "create:americas",
        "enter:americas",
    ]
    assert events[4] == "collect"


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

    def fake_validation(
        raw,
        *,
        min_routes: int,
        min_patches: int,
        sampling_frame,
        sampling_stage,
        discovery_plan,
        discovery_root,
        selection_root,
        duration_rule,
        duration_analysis,
        final_selection_plan,
        final_discovery_plan,
        pilot_discovery_plan,
        pilot_discovery_root,
        pilot_selection_root,
        final_discovery_root,
        final_selection_root,
    ) -> dict[str, object]:
        events.append("validate")
        assert raw == tmp_path / "raw"
        assert min_routes == 1
        assert min_patches == 1
        assert sampling_frame is None
        assert sampling_stage is None
        assert discovery_plan is None
        assert discovery_root is None
        assert selection_root is None
        assert duration_rule is None
        assert duration_analysis is None
        assert final_selection_plan is None
        assert final_discovery_plan is None
        assert pilot_discovery_plan is None
        assert pilot_discovery_root is None
        assert pilot_selection_root is None
        assert final_discovery_root is None
        assert final_selection_root is None
        return {"passed": True}

    def fake_processing(raw, *, output_root, max_new_matches) -> dict[str, object]:
        events.append("process")
        assert raw == tmp_path / "raw"
        assert output_root == tmp_path / "processed"
        assert max_new_matches is None
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
