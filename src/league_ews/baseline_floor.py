"""Training-patch prevalence, clock and strictly observed event-history controls."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.constants import EVENTS, RIFTHAZARD_HORIZONS_SECONDS
from league_ews.final_split import freeze_final_split
from league_ews.metrics import probabilistic_metrics
from league_ews.raw_validation import ProcessingManifest
from league_ews.timeline import NormalizedTimeline

LABELS = tuple(
    f"y_{event}_{horizon}" for event in EVENTS for horizon in RIFTHAZARD_HORIZONS_SECONDS
)
PSEUDOCOUNT = 20
CLOCK_BIN_MS = 60_000
MAX_CLOCK_BIN = 60
RECENT_KILL_MS = 120_000


def _history_bucket(event: str, timestamp_ms: int, last: int | None, recent_kills: int) -> int:
    if event == "teamfight":
        return min(recent_kills, 3)
    if last is None:
        return 0
    elapsed = timestamp_ms - last
    return 1 if elapsed < 120_000 else 2 if elapsed < 300_000 else 3


def _rows(
    payload: Mapping[str, Any], match_id: str
) -> Iterator[tuple[int, dict[str, int], dict[str, int]]]:
    """Yield only causal controls; target values are kept separate from controls."""

    if payload.get("schema_version") != "league-ews-processed-match-v1":
        raise ValueError("Unsupported processed match schema")
    timeline = NormalizedTimeline.model_validate(payload["timeline"])
    labels = payload["labels"]
    if timeline.match_id != match_id or not isinstance(labels, list):
        raise ValueError("Processed match identity or labels differ")
    if len(timeline.observations) != len(labels):
        raise ValueError("Processed observation and label counts differ")
    last_objective: dict[str, int | None] = {"baron": None, "dragon": None}
    kills: deque[int] = deque()
    for observation, label_row in zip(timeline.observations, labels, strict=True):
        timestamp = observation.timestamp_ms
        for event in sorted(observation.events, key=lambda item: item.timestamp_ms):
            if event.timestamp_ms > timestamp:
                continue
            if event.event_type == "CHAMPION_KILL":
                kills.append(event.timestamp_ms)
            elif event.event_type == "ELITE_MONSTER_KILL":
                if event.monster_type == "BARON_NASHOR":
                    last_objective["baron"] = event.timestamp_ms
                elif event.monster_type == "DRAGON":
                    last_objective["dragon"] = event.timestamp_ms
        while kills and kills[0] < timestamp - RECENT_KILL_MS:
            kills.popleft()
        if not isinstance(label_row, dict) or label_row.get("timestamp_ms") != timestamp:
            raise ValueError("Processed label timestamp differs from observation")
        targets = {name: label_row.get(name) for name in LABELS}
        if any(type(value) is not int or value not in (0, 1) for value in targets.values()):
            raise ValueError("Processed labels must be binary integers")
        history = {
            event: _history_bucket(event, timestamp, last_objective.get(event), len(kills))
            for event in EVENTS
        }
        yield min(timestamp // CLOCK_BIN_MS, MAX_CLOCK_BIN), cast(dict[str, int], targets), history


def _read_match(root: Path, match_id: str, expected_sha: str) -> Mapping[str, Any]:
    content = (root / "matches" / f"{match_id}.json").read_bytes()
    if hashlib.sha256(content).hexdigest() != expected_sha:
        raise ValueError("Processed match checksum differs from audited manifest")
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("Processed match must be an object")
    return payload


def _estimate(positives: int, total: int, prior: float) -> float:
    return (positives + PSEUDOCOUNT * prior) / (total + PSEUDOCOUNT)


def _probabilities(
    model: Mapping[str, Any], label: str, clock: int, history: int
) -> tuple[float, float, float]:
    prevalence = float(model["prevalence"][label])
    clock_counts = model["clock_counts"].get(f"{label}|{clock}", [0, 0])
    clock_prob = _estimate(clock_counts[0], clock_counts[1], prevalence)
    history_counts = model["history_counts"].get(f"{label}|{clock}|{history}", [0, 0])
    history_prob = _estimate(history_counts[0], history_counts[1], clock_prob)
    return prevalence, clock_prob, history_prob


def fit_baseline_floor(
    processed_root: str | Path,
    partitions: Mapping[str, list[dict[str, object]]],
    processing_manifest: ProcessingManifest,
) -> tuple[dict[str, object], dict[str, object]]:
    """Fit B0-B2 on train only and evaluate calibration only; never open test files."""

    root = Path(processed_root)
    by_id = {record.match_id: record for record in processing_manifest.matches}
    if len(by_id) != len(processing_manifest.matches):
        raise ValueError("Processing manifest repeats a match")
    if not set(partitions) == {"train", "calibration", "test"}:
        raise ValueError("Expected train, calibration and test partitions")
    seen: set[str] = set()
    for entries in partitions.values():
        for entry in entries:
            match_id = str(entry["match_id"])
            if match_id in seen or match_id not in by_id:
                raise ValueError(
                    "Split membership is duplicated or absent from processing manifest"
                )
            seen.add(match_id)
    if seen != set(by_id):
        raise ValueError("Split does not cover exactly the processed inventory")
    positive: Counter[str] = Counter()
    total: Counter[str] = Counter()
    clock_positive: Counter[str] = Counter()
    clock_total: Counter[str] = Counter()
    history_positive: Counter[str] = Counter()
    history_total: Counter[str] = Counter()
    train_rows = 0
    for index, entry in enumerate(partitions["train"], start=1):
        match_id = str(entry["match_id"])
        payload = _read_match(root, match_id, by_id[match_id].sha256)
        for clock, targets, history in _rows(payload, match_id):
            train_rows += 1
            for label, value in targets.items():
                event = label.split("_", 2)[1]
                clock_key = f"{label}|{clock}"
                history_key = f"{clock_key}|{history[event]}"
                positive[label] += value
                total[label] += 1
                clock_positive[clock_key] += value
                clock_total[clock_key] += 1
                history_positive[history_key] += value
                history_total[history_key] += 1
        if index % 1000 == 0:
            print(f"Trained {index}/{len(partitions['train'])} matches", flush=True)
    if not train_rows:
        raise ValueError("Training partition contains no observations")
    model: dict[str, object] = {
        "schema_version": "league-ews-baseline-floor-v1",
        "labels": LABELS,
        "clock_bin_ms": CLOCK_BIN_MS,
        "max_clock_bin": MAX_CLOCK_BIN,
        "recent_kill_ms": RECENT_KILL_MS,
        "pseudocount": PSEUDOCOUNT,
        "prevalence": {label: positive[label] / total[label] for label in LABELS},
        "clock_counts": {key: [clock_positive[key], count] for key, count in clock_total.items()},
        "history_counts": {
            key: [history_positive[key], count] for key, count in history_total.items()
        },
        "train_matches": len(partitions["train"]),
        "train_observations": train_rows,
    }
    truth: dict[str, list[int]] = {label: [] for label in LABELS}
    scores: dict[str, dict[str, list[float]]] = {
        name: {label: [] for label in LABELS} for name in ("B0", "B1", "B2")
    }
    calibration_rows = 0
    for index, entry in enumerate(partitions["calibration"], start=1):
        match_id = str(entry["match_id"])
        payload = _read_match(root, match_id, by_id[match_id].sha256)
        for clock, targets, history in _rows(payload, match_id):
            calibration_rows += 1
            for label, value in targets.items():
                event = label.split("_", 2)[1]
                truth[label].append(value)
                for name, probability in zip(
                    ("B0", "B1", "B2"),
                    _probabilities(model, label, clock, history[event]),
                    strict=True,
                ):
                    scores[name][label].append(probability)
        if index % 1000 == 0:
            print(
                f"Scored {index}/{len(partitions['calibration'])} calibration matches",
                flush=True,
            )
    if not calibration_rows:
        raise ValueError("Calibration partition contains no observations")
    metrics: dict[str, dict[str, dict[str, float | None]]] = {}
    macro: dict[str, float] = {}
    for name, by_label in scores.items():
        metrics[name] = {
            label: probabilistic_metrics(
                np.asarray(truth[label], dtype=np.int8),
                np.asarray(values, dtype=np.float64),
            )
            for label, values in by_label.items()
        }
        macro[name] = float(
            np.mean([float(value["average_precision"] or 0.0) for value in metrics[name].values()])
        )
    report: dict[str, object] = {
        "schema_version": "league-ews-baseline-floor-calibration-v1",
        "train_matches": len(partitions["train"]),
        "train_observations": train_rows,
        "calibration_matches": len(partitions["calibration"]),
        "calibration_observations": calibration_rows,
        "test_matches_unread": len(partitions["test"]),
        "macro_average_precision": macro,
        "metrics": metrics,
        "identifiers_in_report": False,
    }
    return model, report


def run_final_baseline_floor(
    raw_root: str | Path,
    processed_root: str | Path,
    frame_path: str | Path,
    g2_report: str | Path,
    processed_audit: str | Path,
    split_path: str | Path,
    output_root: str | Path,
) -> dict[str, object]:
    """Check split provenance, then save B0-B2 training and calibration evidence."""

    split_bytes = Path(split_path).read_bytes()
    frozen = freeze_final_split(raw_root, processed_root, frame_path, g2_report, processed_audit)
    if json.loads(split_bytes) != frozen:
        raise ValueError("Private split differs from the audited registered partitions")
    content = (Path(processed_root) / "processing-manifest.json").read_bytes()
    processing = ProcessingManifest.model_validate_json(content)
    partitions = frozen["partitions"]
    if not isinstance(partitions, dict):
        raise ValueError("Split partitions must be an object")
    model, report = fit_baseline_floor(processed_root, partitions, processing)
    model["split_sha256"] = hashlib.sha256(split_bytes).hexdigest()
    model["processing_manifest_sha256"] = hashlib.sha256(content).hexdigest()
    model_bytes = (json.dumps(model, sort_keys=True, separators=(",", ":")) + "\n").encode()
    report["model_sha256"] = hashlib.sha256(model_bytes).hexdigest()
    report["split_sha256"] = model["split_sha256"]
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    for path, data in (
        (output / "model.json", model_bytes),
        (
            output / "calibration-report.json",
            (json.dumps(report, sort_keys=True, indent=2) + "\n").encode(),
        ),
    ):
        if path.exists():
            if path.read_bytes() != data:
                raise ValueError("Existing baseline artifact differs; refusing to overwrite")
        else:
            partial = path.with_suffix(path.suffix + ".partial")
            partial.write_bytes(data)
            partial.replace(path)
    return {
        key: report[key]
        for key in (
            "schema_version",
            "train_matches",
            "calibration_matches",
            "test_matches_unread",
            "macro_average_precision",
            "model_sha256",
            "split_sha256",
            "identifiers_in_report",
        )
    }
