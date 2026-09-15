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
