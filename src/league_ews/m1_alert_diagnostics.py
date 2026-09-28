"""Checksum-bound, descriptive alert opportunity audit on calibration only."""

from __future__ import annotations

import hashlib
import json
from bisect import bisect_left
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.alert_policy import (
    COOLDOWN_MS,
    HORIZON_MS,
    MatchRisk,
    evaluate_alerts,
    select_threshold,
)
from league_ews.baseline_floor import LABELS, _read_match
from league_ews.constants import EVENTS
from league_ews.m1_training_plan import SEEDS
from league_ews.raw_validation import ProcessingManifest

HORIZONS_MS = (10_000, 20_000, 30_000, 60_000)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _distribution(values: list[int]) -> dict[str, float | int]:
    data = np.asarray(values)
    return {
        "median": float(np.median(data)),
        "p90": float(np.percentile(data, 90)),
        "p95": float(np.percentile(data, 95)),
        "maximum": int(np.max(data)),
    }


def diagnose_alerts(matches: list[MatchRisk], threshold: float) -> dict[str, Any]:
    """Replay the frozen matching rule and count observable event opportunities.

    An onset is observable at a horizon only when a strictly preceding actual
    prediction frame falls inside that horizon. This is a descriptive ceiling
    for this observation schedule, not an estimate of a live system's recall.
    """

    expected = evaluate_alerts(matches, threshold)
    opportunity = {str(h // 1000): 0 for h in HORIZONS_MS}
    false_by_game: list[int] = []
    leads: list[int] = []
    for match in matches:
        times, onsets = match.times_ms, match.events_ms
        for onset in onsets:
            index = bisect_left(times, onset) - 1
            if index >= 0:
                delta = onset - times[index]
                for horizon in HORIZONS_MS:
                    opportunity[str(horizon // 1000)] += delta <= horizon
        last_alert = -COOLDOWN_MS - 1
        first_unmatched = 0
        false = 0
        for time, risk in zip(times, match.risks, strict=True):
            if risk < threshold or time - last_alert <= COOLDOWN_MS:
                continue
            last_alert = time
            while first_unmatched < len(onsets) and onsets[first_unmatched] <= time:
                first_unmatched += 1
            if first_unmatched < len(onsets) and onsets[first_unmatched] - time <= HORIZON_MS:
                leads.append(onsets[first_unmatched] - time)
                first_unmatched += 1
            else:
                false += 1
        false_by_game.append(false)
    if (
        sum(false_by_game) != expected["false_alerts"]
        or len(leads) != expected["matched_events"]
        or len(leads) > opportunity["60"]
    ):
        raise ValueError("Opportunity replay differs from the frozen alert matcher")
    observed = opportunity["60"]
    return {
        "events": expected["events"],
        "opportunities_by_horizon_seconds": opportunity,
        "observable_fraction_60": observed / expected["events"] if expected["events"] else None,
        "recall_of_observable_events_60": len(leads) / observed if observed else None,
        "false_alerts_per_game": _distribution(false_by_game),
        "games_with_at_least_one_false_alert": sum(value > 0 for value in false_by_game),
        "games_with_at_least_five_false_alerts": sum(value >= 5 for value in false_by_game),
        "matched_lead_seconds": {
            "under_10": sum(value <= 10_000 for value in leads),
            "over_10_to_30": sum(10_000 < value <= 30_000 for value in leads),
            "over_30_to_60": sum(30_000 < value <= 60_000 for value in leads),
        },
    }


def _chronological_halves(entries: list[dict[str, Any]]) -> tuple[list[int], list[int]]:
    """Choose the earlier and later 1,500 matches in each route."""

    route_counts = {"europe": 0, "americas": 0}
    last_creation = dict.fromkeys(route_counts, -1)
    early: list[int] = []
    later: list[int] = []
    for index, row in enumerate(entries):
        route = row["regional_route"]
        if route not in route_counts or row["game_creation_ms"] < last_creation[route]:
            raise ValueError("Calibration route or chronological order differs from frozen split")
        last_creation[route] = row["game_creation_ms"]
        (early if route_counts[route] < 1500 else later).append(index)
        route_counts[route] += 1
    if route_counts != {"europe": 3000, "americas": 3000}:
        raise ValueError("Alert audit cannot create balanced chronological calibration halves")
    return early, later


def audit_m1_alert_opportunity(
    processed_root: str | Path,
    split_path: str | Path,
    calibration_root: str | Path,
    policy_root: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    """Audit existing M1 policies without refitting, selecting, or opening test files."""

    processed = Path(processed_root)
    calibration = Path(calibration_root)
    policies = Path(policy_root)
    split_file = Path(split_path)
    calibration_summary_file = calibration / "ten-seed-summary.json"
    policy_summary_file = policies / "ten-seed-alert-summary.json"
    split = json.loads(split_file.read_bytes())
    cal_summary = json.loads(calibration_summary_file.read_bytes())
    policy_summary = json.loads(policy_summary_file.read_bytes())
    processing_file = processed / "processing-manifest.json"
    processing_sha = _sha(processing_file)
    inventory = ProcessingManifest.model_validate_json(processing_file.read_bytes())
    entries = split["partitions"]["calibration"]
    if (
        split.get("schema_version") != "league-ews-final-split-v1"
        or split.get("processing_manifest_sha256") != processing_sha
        or split.get("summary", {}).get("counts")
        != {"train": 24000, "calibration": 6000, "test": 6000}
        or split["summary"]["patches"]["calibration"] != ["16.16"]
        or len(entries) != 6000
        or len(inventory.matches) != 36000
        or cal_summary.get("schema_version") != "league-ews-m1-ten-seed-calibration-v1"
        or cal_summary.get("split_sha256") != _sha(split_file)
        or cal_summary.get("calibration_matches") != 6000
        or cal_summary.get("seed_count") != len(SEEDS)
        or cal_summary.get("identifiers_in_summary") is not False
        or policy_summary.get("schema_version") != "league-ews-m1-ten-seed-alert-summary-v1"
        or policy_summary.get("split_sha256") != _sha(split_file)
        or policy_summary.get("ten_seed_calibration_sha256") != _sha(calibration_summary_file)
        or policy_summary.get("calibration_matches") != 6000
        or policy_summary.get("seed_count") != len(SEEDS)
        or policy_summary.get("identifiers_in_summary") is not False
        or cal_summary.get("test_matches_unread") != 6000
        or policy_summary.get("test_matches_unread") != 6000
        or cal_summary.get("selected_seed") is not None
        or policy_summary.get("selected_seed") is not None
        or [row["seed"] for row in cal_summary["seed_results"]] != SEEDS
        or [row["seed"] for row in policy_summary["seed_reports"]] != SEEDS
    ):
        raise ValueError("Alert audit inputs differ from the frozen calibration inventory")
    by_id = {row.match_id: row for row in inventory.matches}
    if len(by_id) != 36000 or len({row["match_id"] for row in entries}) != 6000:
        raise ValueError("Alert audit match inventory is duplicated")
    early, later = _chronological_halves(entries)
    times: list[tuple[int, ...]] = []
    onsets: dict[str, list[tuple[int, ...]]] = {event: [] for event in EVENTS}
    truth_rows: list[list[int]] = []
    offsets = [0]
    for row in entries:
        match_id = row["match_id"]
        if row["game_version_patch"] != "16.16" or match_id not in by_id:
            raise ValueError("Alert audit calibration match differs from the frozen split")
        payload = _read_match(processed, match_id, by_id[match_id].sha256)
        observations = payload["timeline"]["observations"]
        labels = payload["labels"]
        stamps = tuple(int(item["timestamp_ms"]) for item in observations)
        if (
            len(stamps) != by_id[match_id].observations
            or len(labels) != len(stamps)
            or any(b <= a for a, b in pairwise(stamps))
            or any(item["timestamp_ms"] != stamp for item, stamp in zip(labels, stamps))
        ):
            raise ValueError("Alert audit observation inventory differs from processed match")
        times.append(stamps)
        truth_rows.extend([[item[label] for label in LABELS] for item in labels])
        offsets.append(offsets[-1] + len(stamps))
        for event in EVENTS:
            onsets[event].append(tuple(payload["event_index"][f"{event}_ms"]))
    truth = np.asarray(truth_rows, dtype=np.int8)
    expected_offsets = np.asarray(offsets, dtype=np.int64)
    if not np.isin(truth, (0, 1)).all():
        raise ValueError("Alert audit labels must be binary")

    seed_diagnostics: list[dict[str, Any]] = []
    for cal_seed, policy_seed in zip(
        cal_summary["seed_results"], policy_summary["seed_reports"], strict=True
    ):
        seed = cal_seed["seed"]
        score_file = calibration / f"seed-{seed}" / "calibration-scores.npz"
        policy_file = policies / f"policy.seed-{seed}.json"
        if (
            _sha(score_file) != cal_seed["scores_sha256"]
            or _sha(policy_file) != policy_seed["policy_sha256"]
        ):
            raise ValueError("Alert audit score or policy checksum differs from summary")
        policy = json.loads(policy_file.read_bytes())
        if (
            policy.get("schema_version") != "league-ews-m1-alert-policy-v1"
            or policy.get("seed") != seed
            or policy.get("scores_sha256") != cal_seed["scores_sha256"]
            or policy.get("split_sha256") != _sha(split_file)
            or policy.get("processing_manifest_sha256") != processing_sha
            or policy.get("ten_seed_summary_sha256") != _sha(calibration_summary_file)
            or policy.get("test_matches_unread") != 6000
            or policy.get("selected_seed") is not None
            or policy.get("identifiers_in_report") is not False
            or set(policy.get("events", {})) != set(EVENTS)
        ):
            raise ValueError("Alert audit policy differs from frozen calibration")
        with np.load(score_file, allow_pickle=False) as saved:
            if set(saved.files) != {"probabilities", "targets", "match_offsets"}:
                raise ValueError("Alert audit score inventory differs")
            probabilities = saved["probabilities"]
            targets = saved["targets"]
            match_offsets = saved["match_offsets"]
        if (
            probabilities.shape != truth.shape
            or not np.array_equal(targets, truth)
            or not np.array_equal(match_offsets, expected_offsets)
            or not np.isfinite(probabilities).all()
            or np.any((probabilities < 0) | (probabilities > 1))
        ):
            raise ValueError("Alert audit scores or labels differ from frozen processed files")
        diagnostics: dict[str, Any] = {}
        for event_index, event in enumerate(EVENTS):
            policy_event = policy["events"][event]
            matches = [
                MatchRisk(
                    times[index],
                    onsets[event][index],
                    tuple(float(value) for value in probabilities[start:end, event_index * 4 + 3]),
                )
                for index, (start, end) in enumerate(pairwise(offsets))
            ]
            threshold = float(policy_event["threshold"])
            metrics = evaluate_alerts(matches, threshold)
            if metrics != policy_event["calibration_event_metrics"]:
                raise ValueError("Alert audit replay differs from frozen policy metrics")
            summarized = policy_summary["events"][event]
            if (
                summarized["thresholds"][SEEDS.index(seed)]
                != {"seed": seed, "threshold": threshold}
                or metrics["events"] != summarized["events"]
            ):
                raise ValueError("Alert audit operating point differs from ten-seed summary")
            diagnostics[event] = diagnose_alerts(matches, threshold)
            diagnostics[event]["full_calibration_policy_metrics"] = metrics
            diagnostics[event]["full_calibration_threshold"] = threshold
            early_threshold, _ = select_threshold([matches[index] for index in early])
            later_matches = [matches[index] for index in later]
            diagnostics[event]["later_half_operating_point"] = {
                "threshold_selected_on_early_half": early_threshold,
                "early_matches": len(early),
                "later_matches": len(later),
                "metrics": evaluate_alerts(later_matches, early_threshold),
            }
        seed_diagnostics.append({"seed": seed, "events": diagnostics})
    later_half_summary: dict[str, Any] = {}
    for event in EVENTS:
        later_half_summary[event] = {}
        for metric in ("precision", "event_recall", "event_f1", "false_alerts_per_game"):
            values = [
                float(row["events"][event]["later_half_operating_point"]["metrics"][metric])
                for row in seed_diagnostics
            ]
            later_half_summary[event][metric] = {
                "mean": float(np.mean(values)),
                "sample_standard_deviation": float(np.std(values, ddof=1)),
            }
    result: dict[str, Any] = {
        "schema_version": "league-ews-m1-alert-opportunity-diagnostic-v1",
        "split_sha256": _sha(split_file),
        "processing_manifest_sha256": processing_sha,
        "calibration_summary_sha256": _sha(calibration_summary_file),
        "policy_summary_sha256": _sha(policy_summary_file),
        "calibration_matches": len(entries),
        "seed_count": len(SEEDS),
        "seed_diagnostics": seed_diagnostics,
        "later_half_summary": later_half_summary,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
        "interpretation": (
            "Full calibration policy diagnostics reuse threshold-selection matches. "
            "The later-half operating point uses thresholds selected on earlier "
            "matches within each route; this remains exploratory on one patch."
        ),
    }
    destination = Path(output)
    content = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if destination.exists():
        if destination.read_bytes() != content:
            raise ValueError("Existing alert opportunity audit differs from audited inputs")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".partial")
        temporary.write_bytes(content)
        temporary.replace(destination)
    return result
