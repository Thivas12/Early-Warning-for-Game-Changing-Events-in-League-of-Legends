"""Freeze per-seed M1 event thresholds on the registered calibration patch."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.alert_policy import COOLDOWN_MS, HORIZON_MS, THRESHOLDS, MatchRisk, select_threshold
from league_ews.baseline_floor import LABELS, _read_match
from league_ews.constants import EVENTS
from league_ews.m1_summary import summarize_m1_calibration
from league_ews.m1_training_plan import SEEDS
from league_ews.raw_validation import ProcessingManifest

CAL_MATCHES = 6000
PROCESSED_MATCHES = 36000


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def select_m1_alert_policy(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    hazard_path: str | Path,
    freeze_path: str | Path,
    training_root: str | Path,
    calibration_root: str | Path,
    floor_root: str | Path,
    tabular_root: str | Path,
    processed_root: str | Path,
    split_path: str | Path,
    output_root: str | Path,
    *,
    seed: int,
) -> dict[str, Any]:
    """Use B3's fixed event rule for every seed, with no seed selection."""

    if seed not in SEEDS:
        raise ValueError("M1 alert seed is absent from the frozen experiment")
    summary = summarize_m1_calibration(
        staging_root,
        normalizer_path,
        plan_path,
        hazard_path,
        freeze_path,
        training_root,
        calibration_root,
        floor_root,
        tabular_root,
    )
    summary_path = Path(calibration_root) / "ten-seed-summary.json"
    summary_sha = _sha(summary_path.read_bytes())
    staging_bytes = (Path(staging_root) / "staging-manifest.json").read_bytes()
    if _sha(staging_bytes) != summary["staging_manifest_sha256"]:
        raise ValueError("M1 alert staging differs from audited ten-seed summary")
    staging = json.loads(staging_bytes)
    processed = Path(processed_root)
    processing_bytes = (processed / "processing-manifest.json").read_bytes()
    if _sha(processing_bytes) != staging["processing_manifest_sha256"]:
        raise ValueError("M1 alert processing manifest differs from graph staging")
    inventory = ProcessingManifest.model_validate_json(processing_bytes)
    if len(inventory.matches) != PROCESSED_MATCHES:
        raise ValueError("M1 alert requires the complete processed inventory")
    by_id = {record.match_id: record for record in inventory.matches}
    split_bytes = Path(split_path).read_bytes()
    if _sha(split_bytes) != summary["split_sha256"]:
        raise ValueError("M1 alert split differs from frozen calibration")
    split = json.loads(split_bytes)
    entries = cast(list[dict[str, Any]], split["partitions"]["calibration"])
    if (
        len(entries) != CAL_MATCHES
        or split.get("processing_manifest_sha256") != _sha(processing_bytes)
        or len({entry["match_id"] for entry in entries}) != CAL_MATCHES
    ):
        raise ValueError("M1 alert calibration inventory is invalid")

    seed_result = next(result for result in summary["seed_results"] if result["seed"] == seed)
    score_file = Path(calibration_root) / f"seed-{seed}" / "calibration-scores.npz"
    with np.load(score_file, allow_pickle=False) as saved:
        scores = saved["probabilities"]
        truth = saved["targets"]
        offsets = saved["match_offsets"]
    if offsets.shape != (CAL_MATCHES + 1,) or int(offsets[-1]) != len(scores):
        raise ValueError("M1 alert score offsets differ from calibration inventory")

    times_by_match: list[tuple[int, ...]] = []
    events_by_type: dict[str, list[tuple[int, ...]]] = {event: [] for event in EVENTS}
    for index, entry in enumerate(entries):
        match_id = str(entry["match_id"])
        payload = _read_match(processed, match_id, by_id[match_id].sha256)
        observations = payload["timeline"]["observations"]
        labels = payload["labels"]
        start, end = int(offsets[index]), int(offsets[index + 1])
        if len(observations) != len(labels) or len(labels) != end - start:
            raise ValueError("M1 alert observation inventory differs from saved scores")
        expected = np.asarray([[row[label] for label in LABELS] for row in labels], dtype=np.int8)
        if not np.array_equal(expected, truth[start:end]):
            raise ValueError("M1 alert labels differ from audited processed matches")
        times = tuple(int(row["timestamp_ms"]) for row in observations)
        if any(row["timestamp_ms"] != time for row, time in zip(labels, times, strict=True)):
            raise ValueError("M1 alert label times differ from prediction times")
        times_by_match.append(times)
        for event in EVENTS:
            events_by_type[event].append(tuple(payload["event_index"][f"{event}_ms"]))
        if (index + 1) % 1000 == 0:
            print(f"M1 alert seed {seed}: checked {index + 1}/{CAL_MATCHES} matches", flush=True)

    policies: dict[str, Any] = {}
    for event_index, event in enumerate(EVENTS):
        column = event_index * 4 + 3
        matches = [
            MatchRisk(
                times_by_match[index],
                events_by_type[event][index],
                tuple(
                    float(value) for value in scores[offsets[index] : offsets[index + 1], column]
                ),
            )
            for index in range(CAL_MATCHES)
        ]
        threshold, metrics = select_threshold(matches)
        policies[event] = {"threshold": threshold, "calibration_event_metrics": metrics}

    policy: dict[str, Any] = {
        "schema_version": "league-ews-m1-alert-policy-v1",
        "seed": seed,
        "split_sha256": summary["split_sha256"],
        "processing_manifest_sha256": _sha(processing_bytes),
        "ten_seed_summary_sha256": summary_sha,
        "checkpoint_sha256": seed_result["checkpoint_sha256"],
        "scores_sha256": seed_result["scores_sha256"],
        "threshold_grid": list(THRESHOLDS),
        "horizon_seconds": HORIZON_MS // 1000,
        "cooldown_seconds": COOLDOWN_MS // 1000,
        "criterion": "max-event-f1-then-min-false-alerts-then-max-threshold",
        "calibration_matches": CAL_MATCHES,
        "events": policies,
        "selected_seed": None,
        "test_matches_unread": 6000,
        "identifiers_in_report": False,
    }
    output = Path(output_root) / f"policy.seed-{seed}.json"
    content = (json.dumps(policy, sort_keys=True, indent=2) + "\n").encode()
    if output.exists():
        if output.read_bytes() != content:
            raise ValueError("Existing M1 alert policy differs from frozen inputs")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        partial = output.with_suffix(".json.partial")
        partial.write_bytes(content)
        partial.replace(output)
    return policy
