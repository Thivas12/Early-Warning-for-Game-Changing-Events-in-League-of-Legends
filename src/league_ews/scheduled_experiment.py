"""Exploratory sparse-observation policy study. Never opens test payloads."""

from __future__ import annotations

import argparse
import fcntl
import importlib.metadata
import json
import time
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.scheduled_model import MODELS, Settings, fit, predict, runtime
from league_ews.scheduled_policy import (
    Decisions,
    action_probabilities,
    decision_trace,
    marginal_counts,
    select_policy,
    summary,
)
from league_ews.timely_experiment import freeze as source_freeze
from league_ews.timely_experiment import load_partition
from league_ews.timely_policy import compare_counts

DEFAULT_SETTINGS = Settings()

PLAN: dict[str, Any] = {
    "status": "exploratory-method-candidate-not-confirmatory-or-SOTA",
    "hypothesis": "exact cooldown credit improves warning utility beyond pointwise training",
    "train": "all-24000-matches;fixed-8-epochs;no-calibration-gradient-updates",
    "actions": "absolute-10-second-clock;latest-real-frame-only;age<60s;no-hidden-event-feedback",
    "stop": "last-recorded-observation-boundary;terminal-stop-assumption-required-for-deployment",
    "target": "next-strictly-future-Dragon-at-20-to-60-seconds;late-and-false-both-cost",
    "cooldown_ms": 60000,
    "policy": "independent-Bernoulli-when-available;no-other-dependence-on-sampled-action-history",
    "policy_selection": (
        "randomized-or-deterministic-and-49-logit-offsets-plus-off;earlier-calibration-only"
    ),
    "tuning_budget": 0.9,
    "tuning_budget_scope": "each-route-mean;fixed-margin-not-a-probabilistic-guarantee",
    "evaluation_budget": 1.0,
    "primary": "history-refractory-minus-history-bce;paired-by-seed-and-match",
    "required_controls": ["history-pmf", "history-utility", "clock-bce"],
    "frame_ablation": "history-refractory-frame",
    "bootstrap": "paired-route-stratified-whole-matches;average-fitted-seed-counts;conditional",
    "test_access": "prohibited;6000-patch-16.17-payloads-sealed",
    "unsupported_claims": [
        "new-renewal-mathematics",
        "causal-game-intervention",
        "new-player-observations",
        "groundbreaking",
        "state-of-the-art",
        "independent-confirmation-on-16.16",
    ],
}


def freeze(
    source: Path,
    processed: Path,
    split: Path,
    audit: Path,
    output: Path,
    settings: Settings,
    seeds: tuple[int, ...],
    device: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if source.resolve() == output.resolve() or source.resolve() in output.resolve().parents:
        raise ValueError("Use a separate output outside the source experiment")
    # Reuse audited source binding WITHOUT altering any original module or artifact.
    inherited, membership = source_freeze(
        source, processed, split, audit, output / "source-binding"
    )
    package = Path(__file__).parent
    torch, chosen = runtime(device)
    frozen = {
        "schema_version": "league-ews-scheduled-policy-freeze-v1",
        "plan": PLAN,
        "settings": asdict(settings),
        "seeds": list(seeds),
        "models": list(MODELS),
        "source_binding_sha256": sha(output / "source-binding" / "freeze.json"),
        "source_shards": inherited["shards"],
        "code_sha256": {
            p.name: sha(p)
            for p in [
                package / "scheduled_policy.py",
                package / "scheduled_model.py",
                package / "scheduled_experiment.py",
            ]
        },
        "environment": {
            "device": chosen,
            "torch": str(torch.__version__),
            "cuda": torch.version.cuda,
            "numpy": np.__version__,
            "sklearn": importlib.metadata.version("scikit-learn"),
        },
    }
    path = output / "freeze.json"
    if path.exists() and json.loads(path.read_bytes()) != frozen:
        raise ValueError("Scheduled policy freeze differs; use a new output directory")
    if not path.exists():
        write_json(path, frozen)
    return frozen, membership


def evaluate(
    traces: list[Decisions],
    logits: list[np.ndarray],
    early: list[int],
    later: list[int],
    routes: list[str],
) -> tuple[dict[str, Any], np.ndarray]:
    if (
        not early
        or not later
        or set(early) & set(later)
        or sorted([*early, *later]) != list(range(len(traces)))
        or len(routes) != len(traces)
    ):
        raise ValueError("Invalid disjoint tuning/evaluation membership")
    selected, curve = select_policy(
        [traces[i] for i in early],
        [logits[i] for i in early],
        [routes[i] for i in early],
        budget=float(PLAN["tuning_budget"]),
    )
    counts = marginal_counts(
        [traces[i] for i in later],
        [action_probabilities(logits[i], selected["bias"], selected["family"]) for i in later],
    )
    result = summary(counts)
    by_route = {
        r: summary(counts[np.asarray([routes[i] for i in later]) == r]) for r in sorted(set(routes))
    }
    return {
        "selected_policy": selected,
        "tuning_curve": curve,
        "evaluation": result,
        "evaluation_by_route": by_route,
        "all_route_budgets_met": all(r["non_timely_per_match"] <= 1 for r in by_route.values()),
        "count_semantics": "exact policy expectations; deterministic counts if selected",
    }, counts


def completed(folder: Path, binding: str) -> dict[str, Any] | None:
    if not (folder / "report.json").exists():
        return None
    report = json.loads((folder / "report.json").read_bytes())
    if (
        report.get("freeze_sha256") != binding
        or report.get("model_sha256") != sha(folder / "model.pt")
        or report.get("scores_sha256") != sha(folder / "scores.npz")
    ):
        raise ValueError("Completed scheduled model differs from its binding")
    return dict(report)


def run(
    source: Path,
    processed: Path,
    split_path: Path,
    audit: Path,
    output: Path,
    *,
    settings: Settings = DEFAULT_SETTINGS,
    seeds: tuple[int, ...] = (20260930, 20260931, 20260932),
    device: str = "auto",
    max_new_models: int = 0,
) -> dict[str, Any]:
    if (
        not seeds
        or len(set(seeds)) != len(seeds)
        or any(s < 0 for s in seeds)
        or max_new_models < 0
    ):
        raise ValueError("Unique nonnegative seeds and nonnegative model limit required")
    frozen, split = freeze(source, processed, split_path, audit, output, settings, seeds, device)
    binding = sha(output / "freeze.json")
    keys = [(name, seed) for seed in seeds for name in MODELS]
    pending = [
        (name, seed) for name, seed in keys if completed(output / f"{name}-{seed}", binding) is None
    ]
    early, later = _chronological_halves(split["partitions"]["calibration"])
    routes = [row["regional_route"] for row in split["partitions"]["calibration"]]
    if pending:
        inherited = json.loads((output / "source-binding" / "freeze.json").read_bytes())
        train, calibration = (
            load_partition(source, output, p, inherited) for p in ("train", "calibration")
        )
        train_routes = [r["regional_route"] for r in split["partitions"]["train"]]
        if len(train["times"]) != len(train_routes) or len(calibration["times"]) != len(routes):
            raise ValueError("Source match membership differs")
        traces = {
            frame: [
                [
                    decision_trace(t, e, frame_only=frame)
                    for t, e in zip(data["times"], data["events"], strict=True)
                ]
                for data in (train, calibration)
            ]
            for frame in (False, True)
        }
        chosen = frozen["environment"]["device"]
        torch, _ = runtime(chosen)
        print(
            f"Training device: {chosen}; torch={torch.__version__}; "
            f"CUDA build={torch.version.cuda}",
            flush=True,
        )
        for name, seed in pending[:max_new_models] if max_new_models else pending:
            frame = name.endswith("-frame")
            train_traces, cal_traces = traces[frame]
            folder = output / f"{name}-{seed}"
            folder.mkdir(parents=True, exist_ok=True)
            started = time.monotonic()
            payload, training = fit(train, train_traces, train_routes, name, seed, settings, chosen)
            logits = predict(calibration, cal_traces, payload, settings, chosen)
            evaluation, counts = evaluate(cal_traces, logits, early, later, routes)
            torch.save(payload, folder / "model.pt.partial")
            (folder / "model.pt.partial").replace(folder / "model.pt")
            with (folder / "scores.npz.partial").open("wb") as stream:
                np.savez_compressed(
                    stream,
                    logits=np.concatenate(logits),
                    offsets=np.cumsum([0, *[len(s) for s in logits]]),
                    evaluation_counts=counts,
                    evaluation_indices=np.asarray(later),
                )
            (folder / "scores.npz.partial").replace(folder / "scores.npz")
            report = {
                "model": name,
                "seed": seed,
                "freeze_sha256": binding,
                "model_sha256": sha(folder / "model.pt"),
                "scores_sha256": sha(folder / "scores.npz"),
                "seconds": time.monotonic() - started,
                "training": training,
                "observed_rows": {"train": len(train["x"]), "calibration": len(calibration["x"])},
                "decision_ticks": {
                    "train": sum(len(t.times) for t in train_traces),
                    "calibration": sum(len(t.times) for t in cal_traces),
                },
                **evaluation,
            }
            write_json(folder / "report.json", report)
            print(f"Completed {name} seed={seed}: {evaluation['evaluation']}", flush=True)
    if any(completed(output / f"{name}-{seed}", binding) is None for name, seed in keys):
        return {"status": "paused-resume-same-command", "test_matches_unread": 6000}
    reports, averages, individual = {}, {}, {}
    for name in MODELS:
        counts_by_seed = []
        for seed in seeds:
            folder = output / f"{name}-{seed}"
            loaded_report = completed(folder, binding)
            assert loaded_report is not None
            reports[f"{name}-{seed}"] = {
                k: v for k, v in loaded_report.items() if k != "tuning_curve"
            }
            with np.load(folder / "scores.npz", allow_pickle=False) as data:
                counts_by_seed.append(data["evaluation_counts"])
        individual[name] = counts_by_seed
        averages[name] = np.mean(counts_by_seed, axis=0)
    evaluation_routes = [routes[i] for i in later]
    candidate = "history-refractory"
    comparisons = {}
    for control in MODELS:
        if control == candidate:
            continue
        result = compare_counts(averages[candidate], averages[control], evaluation_routes)
        result["paired_seed_recall_gains"] = [
            float((a[:, 2].sum() - b[:, 2].sum()) / a[:, 0].sum()) if a[:, 0].sum() else None
            for a, b in zip(individual[candidate], individual[control], strict=True)
        ]
        result["scope"] = (
            "Conditional paired match uncertainty; fitted seeds/policies fixed; no refitting"
        )
        comparisons[control] = result
    main = comparisons["history-bce"]
    interval = main["percentile_95_intervals"]
    required = ["history-bce", *PLAN["required_controls"]]
    gate = bool(
        len(seeds) >= 3
        and interval is not None
        and interval["timely_recall_difference"][0] > 0
        and main["timely_recall_difference"] >= 0.02
        and all(comparisons[c]["timely_recall_difference"] > 0 for c in required)
        and all(g is not None and g > 0 for g in main["paired_seed_recall_gains"])
        and all(
            reports[f"{n}-{s}"]["all_route_budgets_met"]
            for n in [candidate, *required]
            for s in seeds
        )
    )
    result = {
        "schema_version": "league-ews-scheduled-policy-summary-v1",
        "status": "complete-exploratory-method-screen",
        "freeze_sha256": binding,
        "test_matches_unread": 6000,
        "models": reports,
        "comparisons": comparisons,
        "mean_seed_metrics": {k: summary(v) for k, v in averages.items()},
        "decision": {
            "supports_further_study": gate,
            "minimum_primary_gain": 0.02,
            "scope": "Exploratory only; does not establish novelty or publication quality",
        },
    }
    write_json(output / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/private/coordination-screen-v1"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed/registered-final"))
    parser.add_argument("--split", type=Path, default=Path("data/private/final-split.json"))
    parser.add_argument(
        "--audit", type=Path, default=Path("data/private/final-processed-validation.json")
    )
    parser.add_argument("--output", type=Path, default=Path("data/private/scheduled-policy-v1"))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--seeds", type=int, nargs="+", default=[20260930, 20260931, 20260932])
    parser.add_argument("--batch-matches", type=int, default=32)
    parser.add_argument("--max-new-models", type=int, default=0)
    parser.add_argument("--freeze-only", action="store_true")
    args = parser.parse_args()
    if args.batch_matches < 1 or args.max_new_models < 0:
        parser.error("Positive batch size and nonnegative model limit required")
    # Fail GPU preflight before source scanning or writing a freeze.
    _, chosen = runtime(args.device)
    settings = Settings(batch_matches=args.batch_matches)
    args.output.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        for root, mode in ((args.output, fcntl.LOCK_EX), (args.source, fcntl.LOCK_SH)):
            lock = stack.enter_context((root / "execution.lock").open("a"))
            try:
                fcntl.flock(lock, mode | fcntl.LOCK_NB)
            except BlockingIOError:
                parser.error(f"Another process is using {root}")
        if args.freeze_only:
            freeze(
                args.source,
                args.processed,
                args.split,
                args.audit,
                args.output,
                settings,
                tuple(args.seeds),
                chosen,
            )
            print("Scheduled policy freeze ready", flush=True)
        else:
            result = run(
                args.source,
                args.processed,
                args.split,
                args.audit,
                args.output,
                settings=settings,
                seeds=tuple(args.seeds),
                device=chosen,
                max_new_models=args.max_new_models,
            )
            print(result["status"], flush=True)


if __name__ == "__main__":
    main()
