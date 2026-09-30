"""Resume LeagueEWS and matched controls on the existing audited League cache.

No test-payload path is constructed. Training uses only B4 training shards;
calibration is scored after every planned fit has finished.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.metadata
import json
import sys
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.alert_policy import MatchRisk
from league_ews.b4_calibration import _load_calibration_shard
from league_ews.b4_normalizer import _validated_manifest
from league_ews.b4_training import _shard
from league_ews.baseline_floor import LABELS, _read_match
from league_ews.constants import EVENTS
from league_ews.coordination_experiment import bind_inputs, sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.metrics import probabilistic_metrics
from league_ews.notebook_ews import FAMILIES, MODEL_SPEC, NotebookEWSBackend
from league_ews.notebook_policy import replay, select
from league_ews.timely_policy import compare_counts

JsonMap = dict[str, Any]
CalibrationData = tuple[
    list[tuple[int, ...]], dict[str, list[tuple[int, ...]]], np.ndarray, np.ndarray
]

SEEDS = (20260930, 20261001, 20261002)
EPOCHS = 12
PLAN = {
    "schema_version": "league-ews-notebook-continuation-plan-v1",
    "status": "exploratory-architecture-continuation-not-novelty-or-confirmation",
    "families": list(FAMILIES),
    "seeds": list(SEEDS),
    "epochs": EPOCHS,
    "model": MODEL_SPEC,
    "inputs": "frozen-b4-8-real-frames-27-values-27-missingness-bits-age",
    "targets": list(LABELS),
    "optimizer": "AdamW;lr=0.0001;weight_decay=0.0001;batch=256;constant-lr",
    "model_selection": "fixed-final-epoch;report-every-seed;no-calibration-selection",
    "primary": "LeagueEWS-minus-GRU;macro-timely-recall-10-to-30-seconds",
    "budget": "<=1-false-plus-late-alert-per-match-in-each-route",
    "policy": "early-calibration-route-halves-only;60s-cooldown;chronological-one-to-one",
    "secondary": "per-event-30s-and-60s;all-four-row-horizons;all-controls",
    "test_access": "prohibited",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def freeze(repo: Path, output: Path, device: str) -> tuple[JsonMap, JsonMap, JsonMap, JsonMap]:
    require(
        Path(__file__).resolve().parent == (repo / "src/league_ews").resolve(),
        "Run the module from this checkout so source hashes describe the executing code",
    )
    print("Checking the audited League split and existing sequence-cache checksums...", flush=True)
    split, records = bind_inputs(
        repo / "data/processed/registered-final",
        repo / "data/private/final-split.json",
        repo / "data/private/final-processed-validation.json",
    )
    stage = repo / "data/private/b4-sequences"
    _, manifest = _validated_manifest(stage)
    normalizer_path = stage / "normalizer.json"
    normalizer = json.loads(normalizer_path.read_bytes())
    manifest_hash = sha(stage / "staging-manifest.json")
    split_hash = sha(repo / "data/private/final-split.json")
    require(
        manifest["split_sha256"] == split_hash
        and manifest["processing_manifest_sha256"] == split["processing_manifest_sha256"]
        and normalizer.get("staging_manifest_sha256") == manifest_hash
        and normalizer.get("split_sha256") == split_hash
        and normalizer.get("processing_manifest_sha256") == manifest["processing_manifest_sha256"]
        and normalizer.get("training_observations")
        == sum(e["observations"] for e in manifest["shards"][:48])
        and normalizer.get("train_matches") == 24000
        and normalizer.get("calibration_matches_unread") == 6000
        and normalizer.get("test_matches_unread") == 6000,
        "The source cache, normalizer and audited split differ",
    )
    for partition in ("train", "calibration"):
        require(
            sum(e["observations"] for e in manifest["shards"] if e["partition"] == partition)
            == sum(records[r["match_id"]].observations for r in split["partitions"][partition]),
            "Source observation totals differ from the processed audit",
        )
    source_files = sorted((repo / "src/league_ews").glob("*.py"))
    original_files = sorted((repo / "legacy/msc-v1").glob("*.ipynb"))
    original_files.append(repo / "legacy/msc-v1/LOL Final Report.pdf")
    frozen = {
        "schema_version": "league-ews-notebook-continuation-freeze-v1",
        "plan": PLAN,
        "device": device,
        "python": sys.version,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("torch", "numpy", "scikit-learn", "pydantic")
        },
        "staging_manifest_sha256": manifest_hash,
        "normalizer_sha256": sha(normalizer_path),
        "split_sha256": split_hash,
        "processed_audit_sha256": sha(repo / "data/private/final-processed-validation.json"),
        "processing_manifest_sha256": manifest["processing_manifest_sha256"],
        "source_sha256": {str(p.relative_to(repo)): sha(p) for p in source_files + original_files},
        "test_matches_unread": 6000,
    }
    path = output / "freeze.json"
    if path.exists():
        require(
            json.loads(path.read_bytes()) == frozen,
            "Existing experiment freeze differs; preserve it and use a new output folder",
        )
    else:
        write_json(path, frozen)
    return split, records, manifest, normalizer


def train_fit(
    stage: Path,
    output: Path,
    manifest: JsonMap,
    normalizer: JsonMap,
    binding: str,
    family: str,
    seed: int,
    device: str,
    budget: int,
) -> tuple[int, bool]:
    backend = NotebookEWSBackend(seed, device, family=family)
    folder = output / family / f"seed-{seed}"
    folder.mkdir(parents=True, exist_ok=True)
    checkpoint = folder / "checkpoint.pt"
    total = 48 * EPOCHS
    completed = 0
    if checkpoint.exists():
        state = backend.torch.load(checkpoint, map_location="cpu", weights_only=True)
        require(
            state.get("freeze_sha256") == binding
            and state.get("family") == family
            and state.get("seed") == seed
            and state.get("device") == device
            and state.get("torch_version") == backend.version
            and type(state.get("completed_units")) is int
            and 0 <= state["completed_units"] <= total,
            "Checkpoint does not match this League continuation",
        )
        completed = state["completed_units"]
        backend.load_state_dict(state["backend"])
    finish = total if budget == 0 else min(total, completed + budget)
    for unit in range(completed, finish):
        epoch, index = divmod(unit, 48)
        entry = manifest["shards"][index]
        path = stage / "shards" / entry["file"]
        require(sha(path) == entry["sha256"], "Training shard changed after freeze")
        x, mask, target = _shard(stage, entry, normalizer)
        loss, rows = backend.train_shard(x, mask, target, seed=seed + epoch * 10000 + index)
        state = {
            "freeze_sha256": binding,
            "family": family,
            "seed": seed,
            "device": device,
            "torch_version": backend.version,
            "completed_units": unit + 1,
            "backend": backend.state_dict(),
            "last_loss": loss,
            "last_rows": rows,
            "parameters": sum(p.numel() for p in backend.model.parameters()),
        }
        partial = checkpoint.with_suffix(".partial")
        backend.torch.save(state, partial)
        partial.replace(checkpoint)
        print(
            f"{family} seed {seed}: epoch {epoch + 1}/{EPOCHS}, "
            f"shard {index + 1}/48; loss {loss:.6f}",
            flush=True,
        )
    return finish - completed, finish == total


def calibration_metadata(repo: Path, split: JsonMap, records: JsonMap) -> CalibrationData:
    """Open only the explicit calibration membership, verifying payloads and labels."""
    times, truth, offsets = [], [], [0]
    events: dict[str, list[tuple[int, ...]]] = {event: [] for event in EVENTS}
    for row in split["partitions"]["calibration"]:
        mid = row["match_id"]
        payload = _read_match(repo / "data/processed/registered-final", mid, records[mid].sha256)
        t = tuple(obs["timestamp_ms"] for obs in payload["timeline"]["observations"])
        require(
            len(t) == records[mid].observations and all(b > a for a, b in pairwise(t)),
            "Invalid calibration observations",
        )
        raw_targets = [[r[label] for label in LABELS] for r in payload["labels"]]
        require(
            all(type(value) is int and value in (0, 1) for row in raw_targets for value in row),
            "Calibration targets must be binary integers before conversion",
        )
        y = np.asarray(raw_targets, dtype=np.int8)
        require(
            [r["timestamp_ms"] for r in payload["labels"]] == list(t), "Label timestamps differ"
        )
        for e, event in enumerate(EVENTS):
            ev = tuple(payload["event_index"][f"{event}_ms"])
            require(
                all(b > a for a, b in pairwise(ev)) and all(0 <= v <= t[-1] for v in ev),
                "Invalid event times",
            )
            events[event].append(ev)
            for h, horizon in enumerate((10, 20, 30, 60)):
                exact = (
                    np.searchsorted(ev, np.asarray(t) + horizon * 1000, side="right")
                    - np.searchsorted(ev, t, side="right")
                ) > 0
                require(
                    np.array_equal(y[:, e * 4 + h], exact),
                    "Future labels differ from exact event times",
                )
        times.append(t)
        truth.append(y)
        offsets.append(offsets[-1] + len(t))
    return times, events, np.concatenate(truth), np.asarray(offsets)


def score_fit(
    repo: Path,
    output: Path,
    manifest: JsonMap,
    normalizer: JsonMap,
    binding: str,
    family: str,
    seed: int,
    device: str,
    split: JsonMap,
    metadata: CalibrationData,
) -> JsonMap:
    folder = output / family / f"seed-{seed}"
    backend = NotebookEWSBackend(seed, device, family=family)
    checkpoint = folder / "checkpoint.pt"
    state = backend.torch.load(checkpoint, map_location="cpu", weights_only=True)
    require(
        state["completed_units"] == 48 * EPOCHS and state["freeze_sha256"] == binding,
        "Incomplete fit",
    )
    backend.load_state_dict(state["backend"])
    times, events, exact_truth, expected_offsets = metadata
    probabilities, truths, offsets = [], [], [0]
    stage = repo / "data/private/b4-sequences"
    for entry in manifest["shards"][48:]:
        require(
            entry["partition"] == "calibration"
            and sha(stage / "shards" / entry["file"]) == entry["sha256"],
            "Calibration shard binding differs",
        )
        x, mask, target, ends = _load_calibration_shard(stage, entry, normalizer)
        probabilities.append(backend.predict_shard(x, mask))
        truths.append(target)
        offsets.extend((ends[1:] + offsets[-1]).tolist())
    scores, truth = np.concatenate(probabilities), np.concatenate(truths)
    require(
        np.array_equal(truth, exact_truth) and np.array_equal(offsets, expected_offsets),
        "Calibration scores do not align with audited match labels",
    )
    require(
        bool(np.isfinite(scores).all() and np.all((scores >= 0) & (scores <= 1))),
        "Invalid model probabilities",
    )
    early, later = _chronological_halves(split["partitions"]["calibration"])
    routes = [row["regional_route"] for row in split["partitions"]["calibration"]]
    later_rows = np.concatenate([np.arange(offsets[i], offsets[i + 1]) for i in later])
    policy_reports: JsonMap = {}
    count_arrays: JsonMap = {}
    for e, event in enumerate(EVENTS):
        for horizon, column in ((30, e * 4 + 2), (60, e * 4 + 3)):
            key = f"{event}_{horizon}"
            matches = [
                MatchRisk(
                    times[i],
                    events[event][i],
                    tuple(float(v) for v in scores[offsets[i] : offsets[i + 1], column]),
                )
                for i in range(len(times))
            ]
            threshold = select([matches[i] for i in early], [routes[i] for i in early], horizon)
            overall, counts = replay([matches[i] for i in later], threshold, horizon)
            regional = {
                r: replay([matches[i] for i in later if routes[i] == r], threshold, horizon)[0]
                for r in ("europe", "americas")
            }
            policy_reports[key] = {
                "threshold": threshold,
                "later": overall,
                "by_route": regional,
                "regional_budget_met": all(
                    v["non_timely_alerts_per_match"] <= 1 for v in regional.values()
                ),
            }
            count_arrays[key] = counts
    score_path = folder / "calibration-scores.npz"
    partial = score_path.with_suffix(".partial")
    with partial.open("wb") as stream:
        np.savez_compressed(
            stream,
            probabilities=scores,
            targets=truth,
            match_offsets=np.asarray(offsets),
            **{f"counts_{k}": v for k, v in count_arrays.items()},
        )
    partial.replace(score_path)
    report = {
        "schema_version": "league-ews-notebook-fit-report-v1",
        "family": family,
        "seed": seed,
        "freeze_sha256": binding,
        "checkpoint_sha256": sha(checkpoint),
        "scores_sha256": sha(score_path),
        "parameters": state["parameters"],
        "row_metrics_later_calibration": {
            label: probabilistic_metrics(truth[later_rows, c], scores[later_rows, c])
            for c, label in enumerate(LABELS)
        },
        "horizon_monotonicity_violations_later": int(
            np.sum(np.any(np.diff(scores[later_rows].reshape(-1, 3, 4), axis=2) < 0, axis=2))
        ),
        "warnings": policy_reports,
        "test_matches_unread": 6000,
    }
    write_json(folder / "report.json", report)
    print(f"Completed calibration: {family}, seed {seed}", flush=True)
    return report


def run(
    repo: Path, output: Path, device: str, max_new_shards: int, preflight: bool = False
) -> JsonMap:
    require(max_new_shards >= 0, "Shard budget must be nonnegative")
    # Device preflight before disk-intensive validation. CUDA never silently falls back.
    backend = NotebookEWSBackend(SEEDS[0], device, family="snapshot")
    del backend
    split, records, manifest, normalizer = freeze(repo, output, device)
    binding = sha(output / "freeze.json")
    if preflight:
        return {
            "status": "ready",
            "fits": len(FAMILIES) * len(SEEDS),
            "epochs": EPOCHS,
            "device": device,
            "test_matches_unread": 6000,
        }
    used = 0
    for family in FAMILIES:
        for seed in SEEDS:
            consumed, complete = train_fit(
                repo / "data/private/b4-sequences",
                output,
                manifest,
                normalizer,
                binding,
                family,
                seed,
                device,
                max_new_shards - used if max_new_shards else 0,
            )
            used += consumed
            if not complete or (max_new_shards and used >= max_new_shards):
                return {
                    "status": "training-paused-resume-same-command",
                    "new_shards": used,
                    "test_matches_unread": 6000,
                }
    metadata = calibration_metadata(repo, split, records)
    reports = {}
    for family in FAMILIES:
        for seed in SEEDS:
            folder = output / family / f"seed-{seed}"
            path = folder / "report.json"
            if path.exists():
                report = json.loads(path.read_bytes())
                require(
                    report["freeze_sha256"] == binding
                    and report["checkpoint_sha256"] == sha(folder / "checkpoint.pt")
                    and report["scores_sha256"] == sha(folder / "calibration-scores.npz"),
                    "Existing fit report binding differs",
                )
            else:
                report = score_fit(
                    repo,
                    output,
                    manifest,
                    normalizer,
                    binding,
                    family,
                    seed,
                    device,
                    split,
                    metadata,
                )
            reports[f"{family}/{seed}"] = report
    _, later = _chronological_halves(split["partitions"]["calibration"])
    routes = [split["partitions"]["calibration"][i]["regional_route"] for i in later]
    comparisons = {}
    differences = []
    budget_passes = []
    for seed in SEEDS:
        with (
            np.load(
                output / "leagueews" / f"seed-{seed}" / "calibration-scores.npz", allow_pickle=False
            ) as candidate,
            np.load(
                output / "gru" / f"seed-{seed}" / "calibration-scores.npz", allow_pickle=False
            ) as control,
        ):
            comparisons[str(seed)] = {
                f"{event}_{h}": compare_counts(
                    candidate[f"counts_{event}_{h}"], control[f"counts_{event}_{h}"], routes
                )
                for event in EVENTS
                for h in (30, 60)
            }
        primary = [
            comparisons[str(seed)][f"{event}_30"]["timely_recall_difference"] for event in EVENTS
        ]
        require(
            all(v is not None for v in primary), "Primary macro recall is undefined without events"
        )
        differences.append(float(np.mean(primary)))
        budget_passes.append(
            all(
                reports[f"{family}/{seed}"]["warnings"][f"{event}_30"]["regional_budget_met"]
                for family in ("leagueews", "gru")
                for event in EVENTS
            )
        )
    summary = {
        "schema_version": "league-ews-notebook-continuation-summary-v1",
        "status": "complete-exploratory-development-study",
        "freeze_sha256": binding,
        "models": reports,
        "leagueews_minus_gru": comparisons,
        "macro_30s_timely_recall_differences_by_seed": differences,
        "both_models_primary_regional_budgets_met_by_seed": budget_passes,
        "consistent_positive_exploratory_screen": all(v > 0 for v in differences)
        and all(budget_passes),
        "interpretation": (
            "Architecture screen only; calibration already reviewed; no novelty or confirmatory "
            "claim; intervals conditional on fits/policies and unadjusted for secondary comparisons"
        ),
        "test_matches_unread": 6000,
    }
    write_json(output / "summary.json", summary)
    return {
        "status": summary["status"],
        "summary": str(output / "summary.json"),
        "test_matches_unread": 6000,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--max-new-shards", type=int, default=1, help="0 runs all; default one-shard canary"
    )
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output or repo / "data/private/notebook-ews-v1"
    output.mkdir(parents=True, exist_ok=True)
    with (output / "experiment.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "A notebook-continuation worker is already running.\n")
        try:
            result = run(repo, output, args.device, args.max_new_shards, args.preflight)
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            parser.exit(1, f"LeagueEWS stopped: {error}\nSources and sealed test are unchanged.\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
