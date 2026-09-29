"""Freeze an exploratory hybrid only after checksum-bound spatial auditing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from league_ews.m1_training import _bound_inputs
from league_ews.m1_training_plan import SEEDS
from league_ews.m2_backend import MODES

PLAN_SHA256 = "90ce5d4e430292cf4b1f804dea3a11a10ea1c7237fb1760c5961dcb839878f5e"


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _checked_inputs(
    staging_root: Path,
    normalizer_path: Path,
    training_plan_path: Path,
    hazards_path: Path,
    training_freeze_path: Path,
    audit_path: Path,
    plan_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    manifest, normalizer, m1_binding = _bound_inputs(
        staging_root, normalizer_path, training_plan_path, hazards_path, training_freeze_path
    )
    audit = json.loads(audit_path.read_bytes())
    plan = yaml.safe_load(plan_path.read_bytes())
    if (
        audit.get("schema_version") != "league-ews-m2-preprocessing-audit-v1"
        or audit.get("staging_manifest_sha256")
        != _sha((staging_root / "staging-manifest.json").read_bytes())
        or audit.get("training_freeze_sha256") != m1_binding
        or audit.get("split_sha256") != manifest["split_sha256"]
        or audit.get("test_matches_unread") != 6000
        or audit.get("identifiers_in_report") is not False
        or audit.get("partitions", {}).get("train", {}).get("matches") != 24000
        or audit.get("partitions", {}).get("calibration", {}).get("matches") != 6000
        or not isinstance(plan, dict)
        or _sha(plan_path.read_bytes()) != PLAN_SHA256
        or plan.get("schema_version") != "league-ews-m2-hybrid-plan-v1"
        or plan.get("freeze_stage") != "after-spatial-audit-before-hybrid-training"
        or plan.get("model", {}).get("modes") != list(MODES)
        or plan.get("training", {}).get("seeds") != SEEDS
        or plan.get("training", {}).get("epochs") != 3
        or plan.get("training", {}).get("loss") != "mean-bce-with-logits-over-at-risk-bins"
        or plan.get("test", {}).get("access") != "prohibited-for-m2"
    ):
        raise ValueError("M2 hybrid plan or spatial audit differs from the frozen input boundary")
    return manifest, normalizer, m1_binding


def freeze_m2_hybrid(
    staging_root: str | Path,
    normalizer_path: str | Path,
    training_plan_path: str | Path,
    hazards_path: str | Path,
    training_freeze_path: str | Path,
    audit_path: str | Path,
    plan_path: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    root = Path(staging_root)
    normalizer = Path(normalizer_path)
    training_plan = Path(training_plan_path)
    hazards = Path(hazards_path)
    training_freeze = Path(training_freeze_path)
    audit = Path(audit_path)
    plan = Path(plan_path)
    manifest, _, m1_binding = _checked_inputs(
        root, normalizer, training_plan, hazards, training_freeze, audit, plan
    )
    report = {
        "schema_version": "league-ews-m2-hybrid-freeze-v1",
        "staging_manifest_sha256": _sha((root / "staging-manifest.json").read_bytes()),
        "normalizer_sha256": _sha(normalizer.read_bytes()),
        "m1_training_freeze_sha256": m1_binding,
        "spatial_audit_sha256": _sha(audit.read_bytes()),
        "plan_sha256": _sha(plan.read_bytes()),
        "split_sha256": manifest["split_sha256"],
        "modes": list(MODES),
        "seeds": SEEDS,
        "train_matches": 24000,
        "calibration_matches_unread": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    content = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    target = Path(output)
    if target.exists() and target.read_bytes() != content:
        raise ValueError("Existing M2 hybrid freeze differs from checked inputs")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        partial = target.with_suffix(target.suffix + ".partial")
        partial.write_bytes(content)
        partial.replace(target)
    return report
