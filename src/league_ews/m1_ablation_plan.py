"""Bind the registered M1 ablation implementation before fitting variants."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from league_ews.graph import FEATURE_NAMES
from league_ews.m1_graph_window import EDGE_TYPES
from league_ews.m1_training_plan import EXPECTED_PLAN, SEEDS

VARIANTS = tuple(EXPECTED_PLAN["registered_m1_ablations"])
EXPECTED_ABLATIONS: dict[str, Any] = {
    "schema_version": "league-ews-m1-ablation-plan-v1",
    "freeze_stage": "after-m1-calibration-before-ablation-fitting",
    "reference": "frozen-m1-ten-seed-calibration-and-alert-policies",
    "common": {
        "seeds": SEEDS,
        "train_patches": ["16.12", "16.13", "16.14", "16.15"],
        "calibration_patch": "16.16",
        "test_patch": "16.17",
        "test_release": "once-after-all-model-and-policy-freezes",
        "same_shard_order_epochs_optimizer_and_threshold_rule_as_m1": True,
        "no_calibration_seed_selection": True,
    },
    "variants": {
        "no-positions-or-proximity": {
            "source": "frozen-m1-graph-shards",
            "remove_participant_features": [
                "x_scaled",
                "y_scaled",
                "position_observed_or_initial_spawn_elapsed",
            ],
            "remove_objective_features": ["x_scaled", "y_scaled"],
            "preserve_objective_spawn_clock_bit": True,
            "remove_relations": ["proximity", "near-baron", "near-dragon"],
            "retain_node_count": 12,
        },
        "no-interaction-edges": {
            "source": "frozen-m1-graph-shards",
            "remove_relations": list(EDGE_TYPES),
            "retain_all_node_features": True,
            "retain_node_count": 12,
        },
        "no-objective-nodes": {
            "source": "frozen-m1-graph-shards",
            "retain_nodes": "first-ten-participants",
            "graph_pool_denominator": 10,
            "retain_participant_features": True,
            "retain_participant_relations": list(EDGE_TYPES[:3]),
        },
        "no-assistance-history": {
            "source": "frozen-m1-graph-shards",
            "remove_relations": ["assistance"],
            "retain_all_node_features": True,
            "retain_node_count": 12,
        },
        "independent-horizon-heads": {
            "source": "frozen-m1-graph-shards",
            "encoder": "identical-to-m1",
            "output": "twelve-independent-sigmoid-logits",
            "targets": "stored-exact-future-labels",
            "loss": "mean-bce-over-twelve-labels",
            "monotonicity_constraint": "none",
        },
        "fixed-minute-grid": {
            "source": "audited-processed-train-and-calibration-only",
            "prediction_rows": "genuine-observations-unchanged",
            "anchors": "current-real-timestamp-minus-k-times-60000-ms-for-k-0-through-7",
            "history_selection": "latest-genuine-observation-at-or-before-each-anchor",
            "repeated-observation": "deduplicate-and-left-pad",
            "unavailable-history": "left-pad",
            "targets": "same-genuine-observation-future-labels",
            "encoder": "identical-to-m1",
        },
    },
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def freeze_m1_ablations(
    ablation_plan_path: str | Path,
    m1_training_plan_path: str | Path,
    m1_training_freeze_path: str | Path,
    calibration_summary_path: str | Path,
    alert_summary_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Freeze variant choices without opening private matches or the test patch."""

    plan_bytes = Path(ablation_plan_path).read_bytes()
    training_plan_bytes = Path(m1_training_plan_path).read_bytes()
    freeze_bytes = Path(m1_training_freeze_path).read_bytes()
    calibration_bytes = Path(calibration_summary_path).read_bytes()
    alert_bytes = Path(alert_summary_path).read_bytes()
    frozen = json.loads(freeze_bytes)
    calibration = json.loads(calibration_bytes)
    alerts = json.loads(alert_bytes)
    if (
        yaml.safe_load(plan_bytes) != EXPECTED_ABLATIONS
        or tuple(EXPECTED_ABLATIONS["variants"]) != VARIANTS
        or any(
            name not in FEATURE_NAMES
            for name in (
                *EXPECTED_ABLATIONS["variants"]["no-positions-or-proximity"][
                    "remove_participant_features"
                ],
                *EXPECTED_ABLATIONS["variants"]["no-positions-or-proximity"][
                    "remove_objective_features"
                ],
            )
        )
    ):
        raise ValueError("M1 ablation plan differs from registered variants or graph channels")
    if yaml.safe_load(training_plan_bytes) != EXPECTED_PLAN:
        raise ValueError("M1 ablations require the frozen original training plan")
    if (
        not isinstance(frozen, dict)
        or frozen.get("schema_version") != "league-ews-m1-training-freeze-v1"
        or frozen.get("training_plan_sha256") != _sha(training_plan_bytes)
        or frozen.get("seeds") != SEEDS
        or frozen.get("train_matches") != 24000
        or frozen.get("calibration_matches_unread") != 6000
        or frozen.get("test_matches_unread") != 6000
        or frozen.get("identifiers_in_summary") is not False
        or not isinstance(calibration, dict)
        or calibration.get("schema_version") != "league-ews-m1-ten-seed-calibration-v1"
        or calibration.get("freeze_sha256") != _sha(freeze_bytes)
        or calibration.get("split_sha256") != frozen.get("split_sha256")
        or calibration.get("seed_count") != len(SEEDS)
        or [x.get("seed") for x in calibration.get("seed_results", [])] != SEEDS
        or calibration.get("selected_seed") is not None
        or calibration.get("test_matches_unread") != 6000
        or calibration.get("identifiers_in_summary") is not False
        or not isinstance(alerts, dict)
        or alerts.get("schema_version") != "league-ews-m1-ten-seed-alert-summary-v1"
        or alerts.get("ten_seed_calibration_sha256") != _sha(calibration_bytes)
        or alerts.get("split_sha256") != frozen.get("split_sha256")
        or alerts.get("seed_count") != len(SEEDS)
        or [x.get("seed") for x in alerts.get("seed_reports", [])] != SEEDS
        or alerts.get("selected_seed") is not None
        or alerts.get("test_matches_unread") != 6000
        or alerts.get("identifiers_in_summary") is not False
    ):
        raise ValueError("M1 ablation freeze differs from original training and calibration")
    result: dict[str, Any] = {
        "schema_version": "league-ews-m1-ablation-freeze-v1",
        "ablation_plan_sha256": _sha(plan_bytes),
        "training_freeze_sha256": _sha(freeze_bytes),
        "calibration_summary_sha256": _sha(calibration_bytes),
        "alert_summary_sha256": _sha(alert_bytes),
        "split_sha256": frozen["split_sha256"],
        "variants": list(VARIANTS),
        "seeds": SEEDS,
        "train_matches": 24000,
        "calibration_matches": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    path = Path(output_path)
    content = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError("Existing M1 ablation freeze differs from bound inputs")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(path.suffix + ".partial")
        partial.write_bytes(content)
        partial.replace(path)
    return result
