"""Resumable, CPU-only Dragon coordination screen; test payloads are never opened."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits  # type: ignore[import-untyped]

from league_ews.alert_policy import MatchRisk
from league_ews.baseline_floor import _read_match
from league_ews.coordination_features import FEATURE_NAMES, VARIANT_WIDTHS, coordination_matrix
from league_ews.coordination_policy import paired_intervals, replay, select_budget_policy
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.metrics import probabilistic_metrics
from league_ews.raw_validation import ProcessingManifest
from league_ews.timeline import NormalizedTimeline

SEED = 20260929
SHARD_MATCHES = 100
PLAN: dict[str, Any] = {
    "schema_version": "league-ews-coordination-screen-plan-v1",
    "status": "exploratory-after-calibration-review-not-a-test-preregistration",
    "target": "dragon-within-60-seconds-in-actual-match",
    "variants": VARIANT_WIDTHS,
    "features": list(FEATURE_NAMES),
    "history": "two-previous-observed-frames-max-age-180-seconds",
    "pit_anchors": "same-approximate-anchors-as-frozen-M1-not-rule-enforcement",
    "selection_fit_patches": ["16.12", "16.13", "16.14"],
    "selection_validation_patch": "16.15",
    "selection_metric": "average_precision;ties-fewer-leaves",
    "final_fit_patches": ["16.12", "16.13", "16.14", "16.15"],
    "max_leaf_nodes_grid": [7, 15, 31],
    "max_iter": 100,
    "learning_rate": 0.08,
    "min_samples_leaf": 100,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "seed": SEED,
    "class_weight": None,
    "missing_values": "constant-zero-with-training-fitted-missing-indicators-keep-empty-features",
    "calibration": "earlier-1500-per-route-policy-tuning;later-1500-per-route-evaluation",
    "policy": "maximize-timely-20-to-60-second-recall-at-one-false-alert-per-match",
    "cooldown": "allow-at-least-60-seconds-apart",
    "late_alerts": "matched-under-20-seconds-reported-separately-not-counted-as-false",
    "primary_contrast": "coordination-minus-history",
    "secondary_contrasts": ["history-minus-snapshot", "snapshot-minus-b3"],
    "bootstrap": "2000-paired-whole-match-route-stratified-conditional-draws",
    "test_access": "prohibited",
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def bind_inputs(
    processed: Path, split_path: Path, audit_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate all membership metadata, without opening any match payload."""
    split = json.loads(split_path.read_bytes())
    audit = json.loads(audit_path.read_bytes())
    manifest_path = processed / "processing-manifest.json"
    inventory = ProcessingManifest.model_validate_json(manifest_path.read_bytes())
    records = {record.match_id: record for record in inventory.matches}
    partitions = split.get("partitions", {})
    counts = {"train": 24000, "calibration": 6000, "test": 6000}
    if (
        split.get("schema_version") != "league-ews-final-split-v1"
        or split.get("processing_manifest_sha256") != sha(manifest_path)
        or split.get("processed_audit_sha256") != sha(audit_path)
        or audit.get("schema_version") != "league-ews-processed-validation-v1"
        or audit.get("passed") is not True
        or audit.get("processing_manifest_sha256") != sha(manifest_path)
        or audit.get("raw_manifest_sha256") != split.get("raw_manifest_sha256")
        or audit.get("summary", {}).get("validated_matches") != 36000
        or audit.get("summary", {}).get("contains_player_identifiers") is not False
        or {name: len(rows) for name, rows in partitions.items()} != counts
        or len(records) != 36000
        or len(inventory.matches) != 36000
    ):
        raise ValueError("Coordination inputs differ from the frozen audited cohort")
    seen: set[str] = set()
    for partition, entries in partitions.items():
        expected_patches = (
            PLAN["final_fit_patches"]
            if partition == "train"
            else ["16.16" if partition == "calibration" else "16.17"]
        )
        cells: Counter[tuple[str, str]] = Counter()
        previous = (-1, "")
        for row in entries:
            match_id = row["match_id"]
            patch, route = row["game_version_patch"], row["regional_route"]
            order = (row["game_creation_ms"], match_id)
            if (
                match_id in seen
                or match_id not in records
                or order < previous
                or patch not in expected_patches
                or route not in ("europe", "americas")
                or ".".join(records[match_id].game_version.split(".")[:2]) != patch
                or not match_id.startswith("EUW1_" if route == "europe" else "NA1_")
            ):
                raise ValueError("Invalid split membership, route, patch or chronological order")
            seen.add(match_id)
            previous = order
            cells[(route, patch)] += 1
        if cells != Counter(
            {(route, patch): 3000 for route in ("europe", "americas") for patch in expected_patches}
        ):
            raise ValueError("Unexpected route/patch cell counts")
    if seen != set(records):
        raise ValueError("Split does not cover processed inventory")
    _chronological_halves(partitions["calibration"])
    return split, records


def freeze(processed: Path, split_path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    split, records = bind_inputs(processed, split_path, audit_path)
    package = Path(__file__).parent
    source_files = (
        "coordination_features.py",
        "coordination_policy.py",
        "coordination_experiment.py",
        "tabular_baseline.py",
        "timeline.py",
        "metrics.py",
        "baseline_floor.py",
        "m1_alert_diagnostics.py",
        "alert_policy.py",
        "raw_validation.py",
        "constants.py",
    )
    result = {
        "schema_version": "league-ews-coordination-screen-freeze-v1",
        "plan": PLAN,
        "split_sha256": sha(split_path),
        "processed_audit_sha256": sha(audit_path),
        "processing_manifest_sha256": sha(processed / "processing-manifest.json"),
        "code_sha256": {name: sha(package / name) for name in source_files},
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "scikit-learn", "pydantic", "joblib")
        },
        "test_matches_unread": 6000,
        "feature_storage_bytes": sum(
            records[row["match_id"]].observations
            for name in ("train", "calibration")
            for row in split["partitions"][name]
        )
        * len(FEATURE_NAMES)
        * 4,
    }
    path = output / "freeze.json"
    if path.exists():
        if json.loads(path.read_bytes()) != result:
            raise ValueError(
                "Existing screen freeze differs; use a new experiment output directory"
            )
    else:
        write_json(path, result)
    return result


def stage(
    processed: Path, split: dict[str, Any], records: dict[str, Any], output: Path, max_new: int = 0
) -> bool:
    """Checkpoint every 100 matches. A killed shard is safely rebuilt on resume."""
    binding = sha(output / "freeze.json")
    new = 0
    for partition in ("train", "calibration"):
        entries = split["partitions"][partition]
        for start in range(0, len(entries), SHARD_MATCHES):
            target = output / "shards" / f"{partition}.{start:05d}.npz"
            meta = target.with_suffix(".json")
            if meta.exists():
                stored = json.loads(meta.read_bytes())
                if (
                    stored.get("freeze_sha256") != binding
                    or not target.exists()
                    or stored.get("sha256") != sha(target)
                ):
                    raise ValueError("Staged coordination shard differs from its binding")
                continue
            if max_new and new >= max_new:
                return False
            features, labels, stamps, event_times = [], [], [], []
            offsets, event_offsets = [0], [0]
            for row in entries[start : start + SHARD_MATCHES]:
                match_id = row["match_id"]
                payload = _read_match(processed, match_id, records[match_id].sha256)
                timeline = NormalizedTimeline.model_validate(payload["timeline"])
                if (
                    timeline.match_id != match_id
                    or timeline.game_creation_ms != row["game_creation_ms"]
                    or timeline.game_version != records[match_id].game_version
                    or len(timeline.observations) != records[match_id].observations
                ):
                    raise ValueError("Processed timeline metadata differs from split/manifest")
                matrix = coordination_matrix(timeline)
                times = np.array(
                    [obs.timestamp_ms for obs in timeline.observations], dtype=np.int64
                )
                onsets = np.asarray(payload["event_index"]["dragon_ms"], dtype=np.int64)
                if np.any(np.diff(onsets) <= 0) or (
                    len(onsets) and (onsets[0] < 0 or onsets[-1] > times[-1])
                ):
                    raise ValueError("Invalid Dragon event chronology")
                truth = (
                    np.searchsorted(onsets, times + 60_000, side="right")
                    - np.searchsorted(onsets, times, side="right")
                    > 0
                ).astype(np.int8)
                actual = payload["labels"]
                if len(actual) != len(times) or any(
                    item.get("timestamp_ms") != int(t)
                    or type(item.get("y_dragon_60")) is not int
                    or item["y_dragon_60"] != int(y)
                    for item, t, y in zip(actual, times, truth, strict=True)
                ):
                    raise ValueError("Dragon targets differ from exact future event times")
                features.append(matrix)
                labels.append(truth)
                stamps.append(times)
                event_times.append(onsets)
                offsets.append(offsets[-1] + len(times))
                event_offsets.append(event_offsets[-1] + len(onsets))
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".partial")
            with temporary.open("wb") as stream:
                np.savez_compressed(
                    stream,
                    x=np.concatenate(features),
                    y=np.concatenate(labels),
                    times=np.concatenate(stamps),
                    events=np.concatenate(event_times),
                    offsets=np.asarray(offsets),
                    event_offsets=np.asarray(event_offsets),
                )
            temporary.replace(target)
            write_json(
                meta,
                {
                    "freeze_sha256": binding,
                    "sha256": sha(target),
                    "rows": offsets[-1],
                    "matches": len(features),
                },
            )
            new += 1
            print(f"Staged {partition}: {start + len(features)}/{len(entries)} matches", flush=True)
    return True


def load_partition(output: Path, partition: str) -> dict[str, Any]:
    """Assemble a disk-backed matrix; match arrays stay small and preserve order."""
    paths = sorted((output / "shards").glob(f"{partition}.*.npz"))
    if not paths:
        raise ValueError("No staged partition")
    metadata = [json.loads(path.with_suffix(".json").read_bytes()) for path in paths]
    rows = sum(item["rows"] for item in metadata)
    matrix_path = output / f"{partition}.features.npy"
    x = np.lib.format.open_memmap(
        matrix_path, mode="w+", dtype=np.float32, shape=(rows, len(FEATURE_NAMES))
    )
    y = np.empty(rows, dtype=np.int8)
    times, events, offsets = [], [], [0]
    for path, meta in zip(paths, metadata, strict=True):
        if meta["freeze_sha256"] != sha(output / "freeze.json") or meta["sha256"] != sha(path):
            raise ValueError("Feature shard checksum differs")
        with np.load(path, allow_pickle=False) as data:
            start, end = offsets[-1], offsets[-1] + len(data["x"])
            x[start:end], y[start:end] = data["x"], data["y"]
            for index, (left, right) in enumerate(
                zip(data["offsets"][:-1], data["offsets"][1:], strict=True)
            ):
                times.append(tuple(int(v) for v in data["times"][left:right]))
                eleft, eright = data["event_offsets"][index : index + 2]
                events.append(tuple(int(v) for v in data["events"][eleft:eright]))
                offsets.append(start + int(right))
    x.flush()
    return {"x": x, "y": y, "times": times, "events": events, "offsets": np.asarray(offsets)}


def fit_predict(
    train: dict[str, Any],
    calibration: dict[str, Any],
    development_rows: np.ndarray,
    variant: str,
    *,
    leaf_grid: tuple[int, ...] = (7, 15, 31),
    iterations: int = 100,
    min_leaf: int = 100,
) -> tuple[Any, np.ndarray, list[dict[str, Any]]]:
    """Select capacity on a whole later training patch, then refit all training matches."""
    width = VARIANT_WIDTHS[variant]
    x, y = train["x"][:, :width], train["y"]
    if (
        development_rows.shape != y.shape
        or development_rows.dtype != np.bool_
        or any(len(np.unique(y[mask])) != 2 for mask in (development_rows, ~development_rows))
    ):
        raise ValueError(
            "Selection fit and validation need both classes and disjoint row membership"
        )
    results: list[dict[str, Any]] = []
    for leaves in leaf_grid:
        model = make_pipeline(
            SimpleImputer(
                strategy="constant", fill_value=0, add_indicator=True, keep_empty_features=True
            ),
            HistGradientBoostingClassifier(
                loss="log_loss",
                max_leaf_nodes=leaves,
                max_iter=iterations,
                learning_rate=0.08,
                min_samples_leaf=min_leaf,
                l2_regularization=1.0,
                early_stopping=False,
                random_state=SEED,
            ),
        )
        model.fit(x[~development_rows], y[~development_rows])
        scores = model.predict_proba(x[development_rows])[:, 1]
        results.append(
            {"max_leaf_nodes": leaves, **probabilistic_metrics(y[development_rows], scores)}
        )
    best = max(results, key=lambda row: (row["average_precision"], -row["max_leaf_nodes"]))
    model = make_pipeline(
        SimpleImputer(
            strategy="constant", fill_value=0, add_indicator=True, keep_empty_features=True
        ),
        HistGradientBoostingClassifier(
            loss="log_loss",
            max_leaf_nodes=best["max_leaf_nodes"],
            max_iter=iterations,
            learning_rate=0.08,
            min_samples_leaf=min_leaf,
            l2_regularization=1.0,
            early_stopping=False,
            random_state=SEED,
        ),
    )
    model.fit(x, y)
    return model, np.asarray(model.predict_proba(calibration["x"][:, :width])[:, 1]), results


def evaluate_scores(
    calibration: dict[str, Any], scores: np.ndarray, early: list[int], later: list[int]
) -> tuple[dict[str, Any], np.ndarray]:
    if (
        scores.shape != calibration["y"].shape
        or not np.isfinite(scores).all()
        or np.any((scores < 0) | (scores > 1))
    ):
        raise ValueError("Invalid calibration scores")
    if set(early) & set(later) or sorted([*early, *later]) != list(
        range(len(calibration["times"]))
    ):
        raise ValueError("Policy tuning and evaluation must partition whole matches")
    offsets = calibration["offsets"]
    matches = [
        MatchRisk(times, events, tuple(float(v) for v in scores[offsets[i] : offsets[i + 1]]))
        for i, (times, events) in enumerate(
            zip(calibration["times"], calibration["events"], strict=True)
        )
    ]
    threshold, curve = select_budget_policy([matches[i] for i in early])
    evaluation, counts = replay([matches[i] for i in later], threshold)
    selected_rows = np.concatenate([np.arange(offsets[i], offsets[i + 1]) for i in later])
    return {
        "threshold": threshold,
        "tuning_curve": curve,
        "evaluation": evaluation,
        "evaluation_budget_met": evaluation["false_alerts_per_game"] <= 1.0,
        "evaluation_row_metrics": probabilistic_metrics(
            calibration["y"][selected_rows], scores[selected_rows]
        ),
    }, counts


def run(
    processed: Path,
    split_path: Path,
    audit_path: Path,
    output: Path,
    *,
    max_new_shards: int = 0,
    max_new_models: int = 1,
) -> dict[str, Any]:
    freeze(processed, split_path, audit_path, output)
    split, records = bind_inputs(processed, split_path, audit_path)
    if not stage(processed, split, records, output, max_new_shards):
        return {"status": "staging-paused-resume-same-command", "test_matches_unread": 6000}
    binding = sha(output / "freeze.json")
    pending = []
    for variant in VARIANT_WIDTHS:
        folder = output / variant
        report_file = folder / "report.json"
        if report_file.exists():
            report = json.loads(report_file.read_bytes())
            if (
                report.get("freeze_sha256") != binding
                or report.get("model_sha256") != sha(folder / "model.joblib")
                or report.get("scores_sha256") != sha(folder / "scores.npz")
            ):
                raise ValueError("Completed model artifact differs from its binding")
        else:
            pending.append(variant)
    if pending:
        train, calibration = (load_partition(output, name) for name in ("train", "calibration"))
        development = np.repeat(
            [row["game_version_patch"] == "16.15" for row in split["partitions"]["train"]],
            np.diff(train["offsets"]),
        )
        early, later = _chronological_halves(split["partitions"]["calibration"])
        for variant in pending[:max_new_models] if max_new_models else pending:
            print(f"Fitting {variant}; selecting on patch 16.15 only", flush=True)
            start = time.monotonic()
            model, scores, selection = fit_predict(train, calibration, development, variant)
            evaluation, counts = evaluate_scores(calibration, scores, early, later)
            folder = output / variant
            folder.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, folder / "model.joblib.partial")
            (folder / "model.joblib.partial").replace(folder / "model.joblib")
            with (folder / "scores.npz.partial").open("wb") as stream:
                np.savez_compressed(
                    stream,
                    probabilities=scores,
                    targets=calibration["y"],
                    match_offsets=calibration["offsets"],
                    evaluation_counts=counts,
                )
            (folder / "scores.npz.partial").replace(folder / "scores.npz")
            write_json(
                folder / "report.json",
                {
                    "variant": variant,
                    "feature_count": VARIANT_WIDTHS[variant],
                    "freeze_sha256": binding,
                    "model_sha256": sha(folder / "model.joblib"),
                    "scores_sha256": sha(folder / "scores.npz"),
                    "selection": selection,
                    "selected_max_leaf_nodes": model.named_steps[
                        "histgradientboostingclassifier"
                    ].max_leaf_nodes,
                    "fit_and_evaluation_seconds": time.monotonic() - start,
                    "test_matches_unread": 6000,
                    **evaluation,
                },
            )
    complete = all((output / variant / "report.json").exists() for variant in VARIANT_WIDTHS)
    if not complete:
        return {"status": "models-paused-resume-same-command", "test_matches_unread": 6000}
    _, later = _chronological_halves(split["partitions"]["calibration"])
    routes = [split["partitions"]["calibration"][i]["regional_route"] for i in later]
    reports, counts_by_variant = {}, {}
    for variant in VARIANT_WIDTHS:
        report = json.loads((output / variant / "report.json").read_bytes())
        reports[variant] = {key: value for key, value in report.items() if key != "tuning_curve"}
        with np.load(output / variant / "scores.npz", allow_pickle=False) as scores:
            counts_by_variant[variant] = scores["evaluation_counts"]
    summary = {
        "schema_version": "league-ews-coordination-screen-summary-v1",
        "status": "complete-exploratory-calibration-screen",
        "freeze_sha256": binding,
        "new_private_model_results": True,
        "test_matches_unread": 6000,
        "models": reports,
        "paired_comparisons": {
            f"{candidate}-minus-{control}": paired_intervals(
                counts_by_variant[candidate], counts_by_variant[control], routes
            )
            for candidate, control in (
                ("coordination", "history"),
                ("history", "snapshot"),
                ("snapshot", "b3"),
            )
        },
        "interpretation": (
            "Tests these engineered representations, not absence of all possible "
            "coordination signal; all comparisons exploratory after calibration review"
        ),
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", type=Path, default=Path("data/processed/registered-final"))
    parser.add_argument("--split", type=Path, default=Path("data/private/final-split.json"))
    parser.add_argument(
        "--processed-audit", type=Path, default=Path("data/private/final-processed-validation.json")
    )
    parser.add_argument("--output", type=Path, default=Path("data/private/coordination-screen-v1"))
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument(
        "--max-new-shards", type=int, default=0, help="0 stages all remaining shards"
    )
    parser.add_argument("--max-new-models", type=int, default=1, help="0 fits all remaining models")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if args.max_new_shards < 0 or args.max_new_models < 0 or args.threads < 1:
        parser.error("Shard/model limits must be nonnegative; threads must be positive")
    required = (args.processed / "processing-manifest.json", args.split, args.processed_audit)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        parser.error("Required private inputs are not available: " + ", ".join(missing))
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "execution.lock").open("w") as lock, threadpool_limits(limits=args.threads):
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Another coordination command is using this output directory")
        result = (
            freeze(args.processed, args.split, args.processed_audit, args.output)
            if args.freeze_only
            else run(
                args.processed,
                args.split,
                args.processed_audit,
                args.output,
                max_new_shards=args.max_new_shards,
                max_new_models=args.max_new_models,
            )
        )
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
