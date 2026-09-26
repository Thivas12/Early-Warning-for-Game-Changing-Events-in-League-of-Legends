"""Bounded causal tabular baseline on the frozen training and calibration patches."""

from __future__ import annotations

import hashlib
import json
import math
from collections import deque
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, cast

import joblib  # type: ignore[import-untyped]
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from league_ews.baseline_floor import LABELS, _read_match
from league_ews.final_split import freeze_final_split
from league_ews.metrics import probabilistic_metrics
from league_ews.raw_validation import ProcessingManifest
from league_ews.timeline import NormalizedTimeline

FEATURES = (
    "clock_minutes",
    "gold_blue",
    "gold_red",
    "gold_diff",
    "xp_blue",
    "xp_red",
    "xp_diff",
    "level_blue",
    "level_red",
    "level_diff",
    "lane_cs_blue",
    "lane_cs_red",
    "lane_cs_diff",
    "jungle_cs_blue",
    "jungle_cs_red",
    "jungle_cs_diff",
    "recent_kills_blue",
    "recent_kills_red",
    "dragons_blue",
    "dragons_red",
    "barons_blue",
    "barons_red",
    "minutes_since_dragon",
    "minutes_since_baron",
    "blue_spread",
    "red_spread",
    "centroid_distance",
)
SEED = 20260915
MAX_ITER = 100


def _team_summary(participants: list[Any], team_id: int) -> tuple[float, ...]:
    team = [participant for participant in participants if participant.team_id == team_id]
    if len(team) != 5:
        raise ValueError("Each observation must have five participants per team")
    return (
        sum(person.total_gold for person in team),
        sum(person.xp for person in team),
        sum(person.level for person in team) / 5,
        sum(person.lane_minions for person in team),
        sum(person.jungle_minions for person in team),
    )


def _position_summary(participants: list[Any]) -> tuple[float, float, float]:
    positions = {
        team: [
            (person.position.x, person.position.y)
            for person in participants
            if person.team_id == team and person.position is not None
        ]
        for team in (100, 200)
    }
    if any(len(positions[team]) != 5 for team in (100, 200)):
        return math.nan, math.nan, math.nan
    centroids = {
        team: (sum(x for x, _ in points) / 5, sum(y for _, y in points) / 5)
        for team, points in positions.items()
    }
    spread = {
        team: sum(math.dist(point, centroids[team]) for point in points) / 5
        for team, points in positions.items()
    }
    return spread[100], spread[200], math.dist(centroids[100], centroids[200])


def _rows(
    payload: Mapping[str, Any], match_id: str, label: str
) -> Iterator[tuple[list[float], int]]:
    if payload.get("schema_version") != "league-ews-processed-match-v1":
        raise ValueError("Unsupported processed match schema")
    timeline = NormalizedTimeline.model_validate(payload["timeline"])
    labels = payload["labels"]
    if timeline.match_id != match_id or not isinstance(labels, list):
        raise ValueError("Processed match identity or labels differ")
    if len(timeline.observations) != len(labels):
        raise ValueError("Processed observation and label counts differ")
    last_objective: dict[str, int | None] = {"dragon": None, "baron": None}
    objective_counts = {"dragon": {100: 0, 200: 0}, "baron": {100: 0, 200: 0}}
    kills: deque[tuple[int, int | None]] = deque()
    for observation, target in zip(timeline.observations, labels, strict=True):
        timestamp = observation.timestamp_ms
        for event in sorted(observation.events, key=lambda item: item.timestamp_ms):
            if event.timestamp_ms > timestamp:
                continue
            if event.event_type == "CHAMPION_KILL":
                kills.append((event.timestamp_ms, event.killer_team_id))
            elif event.event_type == "ELITE_MONSTER_KILL":
                event_name = {"DRAGON": "dragon", "BARON_NASHOR": "baron"}.get(
                    event.monster_type or ""
                )
                if event_name is not None:
                    last_objective[event_name] = event.timestamp_ms
                    if event.killer_team_id in (100, 200):
                        objective_counts[event_name][event.killer_team_id] += 1
        while kills and kills[0][0] < timestamp - 120_000:
            kills.popleft()
        if not isinstance(target, dict) or target.get("timestamp_ms") != timestamp:
            raise ValueError("Processed label timestamp differs from observation")
        y = target.get(label)
        if type(y) is not int or y not in (0, 1):
            raise ValueError("Processed target must be a binary integer")
        participants = list(observation.participants)
        blue = _team_summary(participants, 100)
        red = _team_summary(participants, 200)
        spreads = _position_summary(participants)
        since = []
        for name in ("dragon", "baron"):
            last = last_objective[name]
            since.append((timestamp - last) / 60_000 if last is not None else math.nan)
        vector = [
            timestamp / 60_000,
            blue[0],
            red[0],
            blue[0] - red[0],
            blue[1],
            red[1],
            blue[1] - red[1],
            blue[2],
            red[2],
            blue[2] - red[2],
            blue[3],
            red[3],
            blue[3] - red[3],
            blue[4],
            red[4],
            blue[4] - red[4],
            sum(team == 100 for _, team in kills),
            sum(team == 200 for _, team in kills),
            objective_counts["dragon"][100],
            objective_counts["dragon"][200],
            objective_counts["baron"][100],
            objective_counts["baron"][200],
            *since,
            *spreads,
        ]
        yield vector, y


def _matrix(
    root: Path,
    entries: list[dict[str, object]],
    by_id: Mapping[str, Any],
    label: str,
    partition: str,
) -> tuple[np.ndarray, np.ndarray]:
    n_rows = sum(by_id[str(entry["match_id"])].observations for entry in entries)
    matrix = np.empty((n_rows, len(FEATURES)), dtype=np.float32)
    targets = np.empty(n_rows, dtype=np.int8)
    offset = 0
    for index, entry in enumerate(entries, start=1):
        match_id = str(entry["match_id"])
        if match_id not in by_id:
            raise ValueError("Split match is absent from processing manifest")
        expected = by_id[match_id]
        rows = list(_rows(_read_match(root, match_id, expected.sha256), match_id, label))
        if len(rows) != expected.observations:
            raise ValueError("Processed observation count differs from manifest")
        next_offset = offset + len(rows)
        matrix[offset:next_offset] = [vector for vector, _ in rows]
        targets[offset:next_offset] = [target for _, target in rows]
        offset = next_offset
        if index % 1000 == 0:
            print(f"B3 {partition}: {index}/{len(entries)} matches", flush=True)
    if offset != n_rows or n_rows == 0:
        raise ValueError("Unexpected empty or incomplete tabular matrix")
    return matrix, targets


def _bound_floor(root: Path, split_sha: str) -> str:
    model_bytes = (root / "model.json").read_bytes()
    model_sha = hashlib.sha256(model_bytes).hexdigest()
    model = json.loads(model_bytes)
    report = json.loads((root / "calibration-report.json").read_bytes())
    if not (
        model.get("schema_version") == "league-ews-baseline-floor-v1"
        and model.get("split_sha256") == split_sha
        and report.get("schema_version") == "league-ews-baseline-floor-calibration-v1"
        and report.get("model_sha256") == model_sha
        and report.get("split_sha256") == split_sha
        and report.get("train_matches") == 24000
        and report.get("calibration_matches") == 6000
        and report.get("test_matches_unread") == 6000
    ):
        raise ValueError("B0-B2 artifacts do not bind to the frozen split")
    return model_sha


def run_final_tabular(
    raw_root: str | Path,
    processed_root: str | Path,
    frame_path: str | Path,
    g2_report: str | Path,
    processed_audit: str | Path,
    split_path: str | Path,
    floor_root: str | Path,
    output_root: str | Path,
    label: str,
) -> dict[str, object]:
    """Fit one fixed B3 target and score calibration; test files remain unopened."""

    if label not in LABELS:
        raise ValueError("Unsupported event/horizon target")
    split_bytes = Path(split_path).read_bytes()
    frozen = freeze_final_split(raw_root, processed_root, frame_path, g2_report, processed_audit)
    if json.loads(split_bytes) != frozen:
        raise ValueError("Private split differs from the audited registered partitions")
    split_sha = hashlib.sha256(split_bytes).hexdigest()
    floor_sha = _bound_floor(Path(floor_root), split_sha)
    content = (Path(processed_root) / "processing-manifest.json").read_bytes()
    processing_sha = hashlib.sha256(content).hexdigest()
    processing = ProcessingManifest.model_validate_json(content)
    by_id = {record.match_id: record for record in processing.matches}
    if len(by_id) != len(processing.matches):
        raise ValueError("Processing manifest repeats a match")
    partitions = cast(dict[str, list[dict[str, object]]], frozen["partitions"])
    train, calibration, test = (partitions[name] for name in ("train", "calibration", "test"))
    if (
        len(train) != 24000
        or len(calibration) != 6000
        or len(test) != 6000
        or {str(entry["match_id"]) for group in partitions.values() for entry in group}
        != set(by_id)
    ):
        raise ValueError("Frozen split differs from processed inventory")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / f"report.{label}.json"
    model_path = root / f"model.{label}.joblib"
    if report_path.exists() or model_path.exists():
        if not report_path.exists() or not model_path.exists():
            raise ValueError("Incomplete existing B3 artifacts require inspection")
        stored_report = json.loads(report_path.read_bytes())
        if not (
            stored_report.get("split_sha256") == split_sha
            and stored_report.get("processing_manifest_sha256") == processing_sha
            and stored_report.get("floor_model_sha256") == floor_sha
            and stored_report.get("label") == label
            and stored_report.get("model_sha256")
            == hashlib.sha256(model_path.read_bytes()).hexdigest()
        ):
            raise ValueError("Existing B3 artifact differs from audited inputs")
        return cast(dict[str, object], stored_report)
    x_train, y_train = _matrix(Path(processed_root), train, by_id, label, "train")
    x_cal, y_cal = _matrix(Path(processed_root), calibration, by_id, label, "calibration")
    if set(np.unique(y_train)) != {0, 1}:
        raise ValueError("Training target lacks both classes")
    classifier = HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=0.08,
        max_iter=MAX_ITER,
        max_leaf_nodes=15,
        min_samples_leaf=100,
        l2_regularization=1.0,
        random_state=SEED,
    )
    classifier.fit(x_train, y_train)
    probabilities = classifier.predict_proba(x_cal)[:, 1]
    metrics = probabilistic_metrics(y_cal, probabilities)
    temporary = model_path.with_suffix(model_path.suffix + ".partial")
    joblib.dump(classifier, temporary)
    model_sha = hashlib.sha256(temporary.read_bytes()).hexdigest()
    report: dict[str, object] = {
        "schema_version": "league-ews-final-tabular-calibration-v1",
        "label": label,
        "feature_names": list(FEATURES),
        "estimator": "HistGradientBoostingClassifier",
        "hyperparameters": {
            "learning_rate": 0.08,
            "max_iter": MAX_ITER,
            "max_leaf_nodes": 15,
            "min_samples_leaf": 100,
            "l2_regularization": 1.0,
            "random_state": SEED,
            "class_weight": None,
        },
        "train_matches": len(train),
        "train_observations": len(y_train),
        "calibration_matches": len(calibration),
        "calibration_observations": len(y_cal),
        "test_matches_unread": len(test),
        "metrics": metrics,
        "split_sha256": split_sha,
        "floor_model_sha256": floor_sha,
        "processing_manifest_sha256": processing_sha,
        "model_sha256": model_sha,
        "identifiers_in_report": False,
    }
    temporary.replace(model_path)
    report_temp = report_path.with_suffix(report_path.suffix + ".partial")
    report_temp.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    report_temp.replace(report_path)
    return report


def summarize_final_tabular(root: str | Path, floor_root: str | Path) -> dict[str, object]:
    """Report a calibration-only B3 macro AP after all 12 targets are complete."""

    base = Path(root)
    floor = json.loads((Path(floor_root) / "calibration-report.json").read_bytes())
    reports = [json.loads((base / f"report.{label}.json").read_bytes()) for label in LABELS]
    split_sha = floor.get("split_sha256")
    floor_sha = floor.get("model_sha256")
    for label, report in zip(LABELS, reports, strict=True):
        model_path = base / f"model.{label}.joblib"
        if not (
            report.get("schema_version") == "league-ews-final-tabular-calibration-v1"
            and report.get("label") == label
            and report.get("split_sha256") == split_sha
            and report.get("floor_model_sha256") == floor_sha
            and report.get("model_sha256") == hashlib.sha256(model_path.read_bytes()).hexdigest()
            and report.get("test_matches_unread") == 6000
        ):
            raise ValueError("B3 target report is missing or differs from frozen inputs")
    b3_ap = float(np.mean([report["metrics"]["average_precision"] for report in reports]))
    return {
        "schema_version": "league-ews-final-tabular-summary-v1",
        "targets": len(LABELS),
        "calibration_macro_average_precision": {
            "B0": floor["macro_average_precision"]["B0"],
            "B1": floor["macro_average_precision"]["B1"],
            "B2": floor["macro_average_precision"]["B2"],
            "B3": b3_ap,
        },
        "test_matches_unread": 6000,
        "split_sha256": split_sha,
        "identifiers_in_summary": False,
    }
