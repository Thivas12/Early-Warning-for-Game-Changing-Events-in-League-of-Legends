"""Four matched target/representation fits, with source-bound cache reuse and no test access."""

from __future__ import annotations

import argparse
import fcntl
import json
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits  # type: ignore[import-untyped]

from league_ews.alert_policy import MatchRisk
from league_ews.coordination_experiment import SHARD_MATCHES, sha, write_json
from league_ews.coordination_experiment import freeze as source_freeze
from league_ews.coordination_features import FEATURE_NAMES, VARIANT_WIDTHS
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.metrics import probabilistic_metrics
from league_ews.timely_policy import (
    BURDENS,
    compare_counts,
    interval_targets,
    select_policies,
    summarize,
)

VARIANTS = ("snapshot", "history")
OBJECTIVES = ("within60", "timely20_60")
MODELS = tuple(f"{variant}-{objective}" for variant in VARIANTS for objective in OBJECTIVES)
PLAN: dict[str, Any] = {
    "schema_version": "league-ews-timely-objective-plan-v1",
    "status": "exploratory-follow-up-after-inspecting-coordination-calibration-results",
    "variants": list(VARIANTS),
    "objectives": list(OBJECTIVES),
    "target": "next-strictly-future-dragon:within60=(0,60];timely=[20,60];late=(0,20)",
    "features": "unchanged-causal-coordination-screen-prefixes",
    "selection_fit_patches": ["16.12", "16.13", "16.14"],
    "selection_validation_patch": "16.15",
    "selection_metric": "timely20_60-average-precision-for-BOTH-objectives;ties-fewer-leaves",
    "final_fit_patches": ["16.12", "16.13", "16.14", "16.15"],
    "max_leaf_nodes_grid": [7, 15, 31],
    "max_iter": 100,
    "learning_rate": 0.08,
    "min_samples_leaf": 100,
    "l2_regularization": 1.0,
    "seed": 20260929,
    "early_stopping": False,
    "class_weight": None,
    "calibration": "earlier-1500-per-route-tuning;later-1500-per-route-exploratory-evaluation",
    "primary_policy": "maximize-timely-recall-at-mean-false-plus-late-alerts<=1-per-match",
    "secondary_policy": "maximize-timely-recall-at-mean-false-alerts<=1-per-match",
    "threshold_grid": "101-logspace-1e-5-to-1-plus-disabled;60-second-cooldown",
    "primary_contrast": "history-timely20_60-minus-history-within60:non_timely",
    "minimum_useful_gain": 0.02,
    "minimum_useful_gain_scope": "new-exploratory-engineering-gate-not-the-earlier-10pp-ambition",
    "bootstrap": "2000-paired-route-stratified-whole-match-draws;conditional-on-fits-and-policies",
    "test_access": "prohibited;all-6000-16.17-payloads-remain-sealed",
}


def freeze(
    source: Path, processed: Path, split_path: Path, audit: Path, output: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    if source.resolve() == output.resolve() or source.resolve() in output.resolve().parents:
        raise ValueError("Use a separate output directory outside the source experiment")
    if not (source / "freeze.json").is_file() or not (source / "summary.json").is_file():
        raise ValueError("Complete the coordination screen before the timely experiment")
    original = source_freeze(processed, split_path, audit, source)
    source_binding = sha(source / "freeze.json")
    summary = json.loads((source / "summary.json").read_bytes())
    if (
        summary.get("status") != "complete-exploratory-calibration-screen"
        or summary.get("freeze_sha256") != source_binding
        or summary.get("test_matches_unread") != 6000
        or set(summary.get("models", {})) != set(VARIANT_WIDTHS)
    ):
        raise ValueError("Source coordination summary differs from its binding")
    split = json.loads(split_path.read_bytes())
    shards = {}
    for partition in ("train", "calibration"):
        entries = split["partitions"][partition]
        expected = [f"{partition}.{i:05d}.npz" for i in range(0, len(entries), SHARD_MATCHES)]
        if sorted(p.name for p in (source / "shards").glob(f"{partition}.*.npz")) != expected:
            raise ValueError("Source shard inventory is incomplete or unexpected")
        for index, name in enumerate(expected):
            path = source / "shards" / name
            metadata = json.loads(path.with_suffix(".json").read_bytes())
            if (
                metadata.get("freeze_sha256") != source_binding
                or metadata.get("sha256") != sha(path)
                or metadata.get("matches")
                != len(entries[index * SHARD_MATCHES : (index + 1) * SHARD_MATCHES])
                or not isinstance(metadata.get("rows"), int)
                or metadata["rows"] < metadata["matches"]
            ):
                raise ValueError("Source shard differs from its binding")
            shards[name] = metadata
    package = Path(__file__).parent
    result = {
        "schema_version": "league-ews-timely-objective-freeze-v1",
        "plan": PLAN,
        "source_freeze_sha256": source_binding,
        "source_summary_sha256": sha(source / "summary.json"),
        "source_freeze": original,
        "shards": shards,
        "code_sha256": {
            name: sha(package / name) for name in ("timely_experiment.py", "timely_policy.py")
        },
    }
    target = output / "freeze.json"
    if target.exists():
        if json.loads(target.read_bytes()) != result:
            raise ValueError("Timely freeze differs; use a new output directory")
    else:
        write_json(target, result)
    return result, split


def load_partition(
    source: Path, output: Path, partition: str, frozen: dict[str, Any]
) -> dict[str, Any]:
    """Reconstruct only train/calibration in the NEW output; never mutate source matrices."""
    if partition not in ("train", "calibration"):
        raise ValueError("Test partition access is prohibited")
    shards = [
        (name, meta)
        for name, meta in sorted(frozen["shards"].items())
        if name.startswith(partition + ".")
    ]
    rows = sum(meta["rows"] for _, meta in shards)
    if not rows:
        raise ValueError("No staged partition")
    x = np.lib.format.open_memmap(
        output / f"{partition}.features.npy",
        mode="w+",
        dtype=np.float32,
        shape=(rows, VARIANT_WIDTHS["history"]),
    )
    times, events, offsets = [], [], [0]
    targets: dict[str, list[np.ndarray]] = {name: [] for name in (*OBJECTIVES, "late0_20")}
    for name, meta in shards:
        path = source / "shards" / name
        if sha(path) != meta["sha256"]:
            raise ValueError("Source shard checksum differs")
        with np.load(path, allow_pickle=False) as data:
            if (
                data["x"].shape != (meta["rows"], len(FEATURE_NAMES))
                or data["y"].shape != (meta["rows"],)
                or data["times"].shape != (meta["rows"],)
                or data["offsets"].shape != (meta["matches"] + 1,)
                or data["event_offsets"].shape != (meta["matches"] + 1,)
                or data["offsets"][0] != 0
                or data["offsets"][-1] != meta["rows"]
                or data["event_offsets"][0] != 0
                or data["event_offsets"][-1] != len(data["events"])
                or np.any(np.diff(data["offsets"]) <= 0)
                or np.any(np.diff(data["event_offsets"]) < 0)
            ):
                raise ValueError("Invalid source shard arrays")
            start = offsets[-1]
            x[start : start + meta["rows"]] = data["x"][:, : VARIANT_WIDTHS["history"]]
            for i, (left, right) in enumerate(
                zip(data["offsets"][:-1], data["offsets"][1:], strict=True)
            ):
                stamps = tuple(int(v) for v in data["times"][left:right])
                eleft, eright = data["event_offsets"][i : i + 2]
                onsets = tuple(int(v) for v in data["events"][eleft:eright])
                labels = interval_targets(stamps, onsets)
                if not np.array_equal(labels["within60"], data["y"][left:right]):
                    raise ValueError("Cached original targets differ from exact event times")
                for key, value in labels.items():
                    targets[key].append(value)
                times.append(stamps)
                events.append(onsets)
                offsets.append(start + int(right))
    x.flush()
    print(f"Loaded {partition}: {len(times):,} matches; {rows:,} rows", flush=True)
    return {
        "x": x,
        "targets": {k: np.concatenate(v) for k, v in targets.items()},
        "times": times,
        "events": events,
        "offsets": np.asarray(offsets),
    }


def fit_predict(
    train: dict[str, Any],
    calibration: dict[str, Any],
    development: np.ndarray,
    variant: str,
    objective: str,
    *,
    leaf_grid: tuple[int, ...] = (7, 15, 31),
    iterations: int = 100,
    min_leaf: int = 100,
) -> tuple[Any, np.ndarray, list[dict[str, Any]]]:
    if variant not in VARIANTS or objective not in OBJECTIVES:
        raise ValueError("Unknown representation or objective")
    x, y = train["x"][:, : VARIANT_WIDTHS[variant]], train["targets"][objective]
    timely = train["targets"]["timely20_60"]
    if (
        development.shape != y.shape
        or development.dtype != np.bool_
        or any(
            len(np.unique(v[mask])) != 2
            for v in (y, timely)
            for mask in (development, ~development)
        )
    ):
        raise ValueError("Both classes required on selection fit and validation partitions")

    def make_model(leaves: int) -> Any:
        return make_pipeline(
            SimpleImputer(
                strategy="constant", fill_value=0, add_indicator=True, keep_empty_features=True
            ),
            HistGradientBoostingClassifier(
                loss="log_loss",
                max_leaf_nodes=leaves,
                max_iter=iterations,
                learning_rate=PLAN["learning_rate"],
                min_samples_leaf=min_leaf,
                l2_regularization=PLAN["l2_regularization"],
                early_stopping=False,
                random_state=PLAN["seed"],
            ),
        )

    selection: list[dict[str, Any]] = []
    for leaves in leaf_grid:
        print(f"  Selecting {variant}/{objective}: {leaves} leaves", flush=True)
        model = make_model(leaves)
        model.fit(x[~development], y[~development])
        scores = np.asarray(model.predict_proba(x[development])[:, 1])
        selection.append(
            {
                "max_leaf_nodes": leaves,
                "timely_average_precision": probabilistic_metrics(timely[development], scores)[
                    "average_precision"
                ],
                "own_target_metrics": probabilistic_metrics(y[development], scores),
            }
        )
    best = max(selection, key=lambda r: (r["timely_average_precision"], -r["max_leaf_nodes"]))
    print(f"  Refitting {variant}/{objective}: {best['max_leaf_nodes']} leaves", flush=True)
    model = make_model(best["max_leaf_nodes"])
    model.fit(x, y)
    scores = np.asarray(model.predict_proba(calibration["x"][:, : VARIANT_WIDTHS[variant]])[:, 1])
    return model, scores, selection


def evaluate(
    data: dict[str, Any],
    scores: np.ndarray,
    early: list[int],
    later: list[int],
    routes: list[str],
    objective: str,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    if (
        objective not in OBJECTIVES
        or scores.shape != data["targets"][objective].shape
        or not np.isfinite(scores).all()
        or np.any((scores < 0) | (scores > 1))
        or len(routes) != len(data["times"])
        or not early
        or not later
        or set(early) & set(later)
        or sorted([*early, *later]) != list(range(len(routes)))
    ):
        raise ValueError("Invalid scores or disjoint evaluation partition")
    offsets = data["offsets"]
    matches = [
        MatchRisk(t, e, tuple(float(v) for v in scores[offsets[i] : offsets[i + 1]]))
        for i, (t, e) in enumerate(zip(data["times"], data["events"], strict=True))
    ]
    selected, curve = select_policies([matches[i] for i in early])
    policies, counts = {}, {}
    for burden in BURDENS:
        threshold = selected[burden]["threshold"]
        summary, counts[burden] = summarize([matches[i] for i in later], threshold)
        policies[burden] = {
            "threshold": threshold,
            "tuning": selected[burden],
            "evaluation": summary,
            "evaluation_budget_met": summary[f"{burden}_alerts_per_game"] <= 1,
            "evaluation_by_route": {
                route: summarize([matches[i] for i in later if routes[i] == route], threshold)[0]
                for route in sorted({routes[i] for i in later})
            },
        }
    rows = np.concatenate([np.arange(offsets[i], offsets[i + 1]) for i in later])
    return {
        "policies": policies,
        "tuning_curve": curve,
        "own_target_row_metrics": probabilistic_metrics(
            data["targets"][objective][rows], scores[rows]
        ),
        "timely_ranking_average_precision": probabilistic_metrics(
            data["targets"]["timely20_60"][rows], scores[rows]
        )["average_precision"],
        "row_metric_scope": "Own-target Brier only; cross-target Brier is not comparable",
    }, counts


def run(
    source: Path,
    processed: Path,
    split_path: Path,
    audit: Path,
    output: Path,
    *,
    max_new_models: int = 0,
) -> dict[str, Any]:
    frozen, split = freeze(source, processed, split_path, audit, output)
    binding = sha(output / "freeze.json")
    pending = []
    for name in MODELS:
        folder = output / name
        if (folder / "report.json").exists():
            report = json.loads((folder / "report.json").read_bytes())
            if (
                report.get("freeze_sha256") != binding
                or report.get("model_sha256") != sha(folder / "model.joblib")
                or report.get("scores_sha256") != sha(folder / "scores.npz")
            ):
                raise ValueError("Completed timely model differs from its binding")
        else:
            pending.append(name)
    early, later = _chronological_halves(split["partitions"]["calibration"])
    routes = [row["regional_route"] for row in split["partitions"]["calibration"]]
    if pending:
        train, calibration = (
            load_partition(source, output, p, frozen) for p in ("train", "calibration")
        )
        if len(train["times"]) != len(split["partitions"]["train"]) or len(
            calibration["times"]
        ) != len(routes):
            raise ValueError("Staged matches differ from split membership")
        development = np.repeat(
            [r["game_version_patch"] == "16.15" for r in split["partitions"]["train"]],
            np.diff(train["offsets"]),
        )
        for name in pending[:max_new_models] if max_new_models else pending:
            variant, objective = name.split("-", 1)
            print(f"Fitting {name}", flush=True)
            start = time.monotonic()
            model, scores, selection = fit_predict(
                train, calibration, development, variant, objective
            )
            evaluation, counts = evaluate(calibration, scores, early, later, routes, objective)
            folder = output / name
            folder.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, folder / "model.joblib.partial")
            (folder / "model.joblib.partial").replace(folder / "model.joblib")
            with (folder / "scores.npz.partial").open("wb") as stream:
                np.savez_compressed(
                    stream,
                    probabilities=scores,
                    targets=calibration["targets"][objective],
                    match_offsets=calibration["offsets"],
                    counts_false=counts["false"],
                    counts_non_timely=counts["non_timely"],
                )
            (folder / "scores.npz.partial").replace(folder / "scores.npz")
            write_json(
                folder / "report.json",
                {
                    "name": name,
                    "variant": variant,
                    "objective": objective,
                    "feature_count": VARIANT_WIDTHS[variant],
                    "freeze_sha256": binding,
                    "model_sha256": sha(folder / "model.joblib"),
                    "scores_sha256": sha(folder / "scores.npz"),
                    "selected_max_leaf_nodes": model.named_steps[
                        "histgradientboostingclassifier"
                    ].max_leaf_nodes,
                    "selection": selection,
                    "fit_and_evaluation_seconds": time.monotonic() - start,
                    "rows": {"train": len(train["x"]), "calibration": len(calibration["x"])},
                    **evaluation,
                },
            )
            print(f"Completed {name}", flush=True)
    if any(not (output / name / "report.json").exists() for name in MODELS):
        return {"status": "models-paused-resume-same-command", "test_matches_unread": 6000}
    reports, counts_by_model = {}, {}
    for name in MODELS:
        report = json.loads((output / name / "report.json").read_bytes())
        reports[name] = {k: v for k, v in report.items() if k != "tuning_curve"}
        with np.load(output / name / "scores.npz", allow_pickle=False) as data:
            counts_by_model[name] = {k: data[f"counts_{k}"] for k in BURDENS}
    comparisons = {}
    for variant in VARIANTS:
        candidate, control = f"{variant}-timely20_60", f"{variant}-within60"
        for burden in BURDENS:
            key = f"{candidate}-minus-{control}:{burden}"
            comparison = compare_counts(
                counts_by_model[candidate][burden],
                counts_by_model[control][burden],
                [routes[i] for i in later],
            )
            candidate_policy = reports[candidate]["policies"][burden]
            control_policy = reports[control]["policies"][burden]
            comparison["both_evaluation_budgets_met"] = (
                candidate_policy["evaluation_budget_met"]
                and control_policy["evaluation_budget_met"]
            )
            comparison["candidate_budget_met_by_route"] = {
                route: values[f"{burden}_alerts_per_game"] <= 1
                for route, values in candidate_policy["evaluation_by_route"].items()
            }
            comparisons[key] = comparison
    primary = comparisons[PLAN["primary_contrast"]]
    interval = primary["percentile_95_intervals"]
    gate = {
        "primary_contrast": PLAN["primary_contrast"],
        "minimum_useful_recall_gain": PLAN["minimum_useful_gain"],
        "supports_further_method_study": bool(
            primary["both_evaluation_budgets_met"]
            and all(primary["candidate_budget_met_by_route"].values())
            and primary["timely_recall_difference"] >= PLAN["minimum_useful_gain"]
            and interval is not None
            and interval["timely_recall_difference"][0] > 0
        ),
        "scope": "Exploratory engineering gate; does not establish novelty or test performance",
    }
    result = {
        "schema_version": "league-ews-timely-objective-summary-v1",
        "status": "complete-exploratory-timely-objective-screen",
        "freeze_sha256": binding,
        "source_summary_sha256": frozen["source_summary_sha256"],
        "new_private_model_results": True,
        "test_matches_unread": 6000,
        "models": reports,
        "paired_comparisons": comparisons,
        "decision": gate,
    }
    write_json(output / "summary.json", result)
    print("Summary ready: True", flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/private/coordination-screen-v1"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed/registered-final"))
    parser.add_argument("--split", type=Path, default=Path("data/private/final-split.json"))
    parser.add_argument(
        "--audit", type=Path, default=Path("data/private/final-processed-validation.json")
    )
    parser.add_argument("--output", type=Path, default=Path("data/private/timely-objective-v1"))
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--max-new-models", type=int, default=0)
    parser.add_argument("--freeze-only", action="store_true")
    args = parser.parse_args()
    if args.threads < 1 or args.max_new_models < 0:
        parser.error("Threads must be positive; model limit must be nonnegative")
    if not (args.source / "summary.json").is_file():
        parser.error("Complete the coordination screen first")
    args.output.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack, threadpool_limits(limits=args.threads):
        for root, mode in ((args.output, fcntl.LOCK_EX), (args.source, fcntl.LOCK_SH)):
            lock = stack.enter_context((root / "execution.lock").open("a"))
            try:
                fcntl.flock(lock, mode | fcntl.LOCK_NB)
            except BlockingIOError:
                parser.error(f"Another command is using {root}; wait for it to finish")
        if args.freeze_only:
            freeze(args.source, args.processed, args.split, args.audit, args.output)
            print("Timely objective freeze ready", flush=True)
        else:
            result = run(
                args.source,
                args.processed,
                args.split,
                args.audit,
                args.output,
                max_new_models=args.max_new_models,
            )
            print(result["status"], flush=True)


if __name__ == "__main__":
    main()
