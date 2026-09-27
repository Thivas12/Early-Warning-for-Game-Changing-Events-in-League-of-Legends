"""Freeze the M1 graph inputs before any private graph shard is written."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from league_ews.graph import ObjectiveRules
from league_ews.timeline import Position

EXPECTED_PLAN: dict[str, Any] = {
    "schema_version": "league-ews-m1-graph-plan-v1",
    "freeze_stage": "before-private-graph-staging",
    "applicable_patches": ["16.12", "16.13", "16.14", "16.15", "16.16"],
    "history_steps": 8,
    "nodes": ["participant", "objective"],
    "edges": ["same-team", "proximity", "assistance", "near-baron", "near-dragon"],
    "proximity_radius_units": 2500,
    "objective_rules": {
        "baron_position": [5007, 10471],
        "dragon_position": [9866, 4414],
        "baron_spawn_seconds": 1200,
        "dragon_spawn_seconds": 300,
    },
    "source_notes": {
        "baron_spawn": "riot-patch-26.1-regular-summoners-rift",
        "dragon_spawn": "fixed-300-second-engineering-prior",
        "positions": "approximate-anchors-from-existing-graph-test",
        "sensitivity": "ablate-objective-nodes-and-proximity",
    },
    "test_patch": "16.17",
    "test_status": "sealed",
}


def load_graph_plan(path: str | Path) -> tuple[str, ObjectiveRules, float]:
    """Require the exact predeclared input contract and return its checksum."""

    content = Path(path).read_bytes()
    if yaml.safe_load(content) != EXPECTED_PLAN:
        raise ValueError("M1 graph plan differs from the frozen input contract")
    details = EXPECTED_PLAN["objective_rules"]
    baron_x, baron_y = details["baron_position"]
    dragon_x, dragon_y = details["dragon_position"]
    rules = ObjectiveRules(
        baron_position=Position(x=baron_x, y=baron_y),
        dragon_position=Position(x=dragon_x, y=dragon_y),
        baron_spawn_seconds=details["baron_spawn_seconds"],
        dragon_spawn_seconds=details["dragon_spawn_seconds"],
    )
    return (
        hashlib.sha256(content).hexdigest(),
        rules,
        float(EXPECTED_PLAN["proximity_radius_units"]),
    )


def freeze_graph_plan(
    plan_path: str | Path,
    split_path: str | Path,
    processed_root: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    """Bind the plan to an audited split and processing manifest without payload reads."""

    plan_sha, _, _ = load_graph_plan(plan_path)
    split_bytes = Path(split_path).read_bytes()
    split = json.loads(split_bytes)
    if split.get("schema_version") != "league-ews-final-split-v1" or split.get("summary", {}).get(
        "counts"
    ) != {"train": 24000, "calibration": 6000, "test": 6000}:
        raise ValueError("M1 requires the complete frozen final split")
    processing_bytes = (Path(processed_root) / "processing-manifest.json").read_bytes()
    if split.get("processing_manifest_sha256") != hashlib.sha256(processing_bytes).hexdigest():
        raise ValueError("M1 split is not bound to the processed manifest")
    record: dict[str, object] = {
        "schema_version": "league-ews-m1-graph-freeze-v1",
        "plan_sha256": plan_sha,
        "split_sha256": hashlib.sha256(split_bytes).hexdigest(),
        "processing_manifest_sha256": hashlib.sha256(processing_bytes).hexdigest(),
        "train_matches": 24000,
        "calibration_matches": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    content = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()
    target = Path(output_path)
    if target.exists():
        if target.read_bytes() != content:
            raise ValueError("Existing M1 graph freeze differs from bound inputs")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".partial")
        partial.write_bytes(content)
        partial.replace(target)
    return record
