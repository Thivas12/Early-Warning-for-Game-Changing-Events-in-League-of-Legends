from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def _yaml(relative: str) -> dict[str, object]:
    payload = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _json(relative: str) -> dict[str, object]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_committed_reports_share_the_declared_dataset_identity() -> None:
    manifest = _yaml("data/manifests/legacy-v5.yaml")
    file_record = manifest["file"]
    assert isinstance(file_record, dict)
    digest = file_record["sha256"]

    audit = _json("reports/legacy-audit.json")
    split = _json("reports/legacy-split-contamination.json")
    baseline = _json("reports/legacy-baselines.json")
    diagnostic = _json("reports/legacy-postmatch-leak.json")
    assert audit["dataset_sha256"] == digest
    assert split["dataset_sha256"] == digest
    for report in (baseline, diagnostic):
        dataset = report["dataset"]
        assert isinstance(dataset, dict)
        assert dataset["sha256"] == digest


def test_experiment_registry_points_to_existing_artifacts() -> None:
    registry = _yaml("experiments/registry.yaml")
    experiments = registry["experiments"]
    assert isinstance(experiments, list)
    identifiers = set()
    for experiment in experiments:
        assert isinstance(experiment, dict)
        identifiers.add(experiment["id"])
        assert (ROOT / str(experiment["artifact"])).is_file()
    assert identifiers == {"A001", "A002", "B001", "B002", "M001"}


def test_current_legacy_notebooks_contain_no_riot_token() -> None:
    token = re.compile(r"RGAPI-[A-Za-z0-9_-]{20,}")
    for notebook in (ROOT / "legacy" / "msc-v1").glob("*.ipynb"):
        assert token.search(notebook.read_text(encoding="utf-8")) is None


def test_authority_example_is_safe_and_fail_closed() -> None:
    record = _yaml("configs/riot-authority.example.yaml")
    assert record["schema_version"] == "riot-collection-authority-v2"
    assert record["regions"] == ["europe", "americas"]
    assert len(record["endpoints"]) == 7
    assert record["authorization_confirmed"] is False
    assert record["ethics_status"] == "pending"
    assert "data/private/" in (ROOT / ".gitignore").read_text(encoding="utf-8")


def test_duration_rule_contains_only_private_evidence_binding() -> None:
    rule = _yaml("configs/rifthazard-duration-rule.yaml")
    decision = rule["decision"]
    analysis = rule["pilot_analysis"]
    assert isinstance(decision, dict)
    assert isinstance(analysis, dict)
    assert decision["final_minimum_seconds"] == 180
    assert len(str(analysis["sha256"])) == 64
    assert analysis["identifiers_in_summary"] is False


def test_final_discovery_plan_is_pilot_isolated_and_outcome_blind() -> None:
    plan = _yaml("configs/rifthazard-final-discovery-plan.yaml")
    stopping = plan["stopping"]
    pilot = plan["pilot_selection"]
    duration = plan["duration_rule"]
    assert isinstance(stopping, dict)
    assert isinstance(pilot, dict)
    assert isinstance(duration, dict)
    assert stopping["stage"] == "final"
    assert stopping["candidate_multiplier_per_cell"] == 2
    assert stopping["exclude_pilot_match_ids_before_stop"] is True
    assert stopping["inspect_match_details_before_stop"] is False
    assert stopping["inspect_labels_before_stop"] is False
    assert pilot["selected_match_ids"] == 5_000
    assert duration["final_minimum_seconds"] == 180


def test_final_selection_plan_is_exact_duration_bound_and_outcome_blind() -> None:
    plan = _yaml("configs/rifthazard-final-selection-plan.yaml")
    discovery = plan["final_discovery"]
    selection = plan["selection"]
    controls = plan["controls"]
    duration = plan["duration_rule"]
    pilot = plan["pilot_selection"]
    assert isinstance(discovery, dict)
    assert isinstance(selection, dict)
    assert isinstance(controls, dict)
    assert isinstance(duration, dict)
    assert isinstance(pilot, dict)
    assert discovery["candidate_match_ids"] == 110_838
    assert discovery["balanced_waves_completed"] == 9
    assert len(discovery["cells"]) == 12
    assert selection["target_matches"] == 36_000
    assert selection["matches_per_cell"] == 3_000
    assert selection["candidate_order"] == "seeded-sha256-global-prefix-v1"
    assert duration["final_minimum_seconds"] == 180
    assert pilot["selected_match_ids"] == 5_000
    assert pilot["exclude_from_final"] is True
    assert all(value is False for key, value in controls.items() if key.startswith("inspect_"))
    assert (ROOT / "docs" / "final-selection.md").is_file()
