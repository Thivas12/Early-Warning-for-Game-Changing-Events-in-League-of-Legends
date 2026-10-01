"""Run the existing LeagueEWS CUDA plan directly from the compact development ZIP.

Keeps the original four families, three seeds, twelve epochs, batch order, losses
and optimizer. Separate output and freeze: never overwrite a WSL study checkpoint.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.metadata
import json
import platform
import time
import zipfile
from pathlib import Path

import numpy as np

from league_ews.b4_normalizer import apply_b4_normalizer
from league_ews.baseline_floor import LABELS
from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.metrics import probabilistic_metrics
from league_ews.notebook_ews import FAMILIES, NotebookEWSBackend
from league_ews.notebook_experiment import EPOCHS, PLAN, SEEDS
from league_ews.tabular_baseline import FEATURES
from league_ews.timely_policy import compare_counts
from scripts.export_league_development import require
from scripts.export_league_three_events import rebuild_histories
from scripts.league_compact_data import (
    EXPECTED_ARCHIVE,
    load_array_bytes,
    load_partition,
    validate_archive,
)
from scripts.league_compact_data import (
    sha as digest,
)
from scripts.run_three_event_trees import policy_report


def read_shard(archive: zipfile.ZipFile, entry: dict) -> dict[str, np.ndarray]:
    content = archive.read(entry["file"])
    require(digest(content) == entry["sha256"], "Compact shard changed")
    return load_array_bytes(content)


def fit_normalizer(archive_path: Path, manifest: dict) -> dict:
    """Same training-current-frame moments and shard order as the existing B4 path."""
    width = len(FEATURES)
    counts = np.zeros(width, dtype=np.int64)
    mean = np.zeros(width, dtype=np.float64)
    m2 = np.zeros(width, dtype=np.float64)
    rows = 0
    with zipfile.ZipFile(archive_path) as archive:
        for entry in manifest["shards"]:
            if entry["partition"] != "train":
                continue
            data = read_shard(archive, entry)
            values = data["values"].astype(np.float64)
            rows += len(values)
            for column in range(width):
                present = values[~data["missing"][:, column], column]
                n = len(present)
                if n:
                    average = float(present.mean())
                    variance = float(np.sum((present - average) ** 2))
                    total = int(counts[column]) + n
                    delta = average - mean[column]
                    m2[column] += variance + delta * delta * int(counts[column]) * n / total
                    mean[column] += delta * n / total
                    counts[column] = total
    scale = np.sqrt(np.divide(m2, counts, out=np.zeros_like(m2), where=counts > 0))
    constant = (counts == 0) | (scale == 0)
    mean[constant], scale[constant] = 0, 1
    return {
        "schema_version": "league-ews-b4-normalizer-v1",
        "features": list(FEATURES),
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "present_counts": counts.tolist(),
        "training_observations": rows,
        "source_archive_sha256": EXPECTED_ARCHIVE,
        "fit_partitions": ["train"],
    }


def sequences(data: dict[str, np.ndarray], normalizer: dict):
    windows, masks = [], []
    for a, b in zip(data["match_offsets"][:-1], data["match_offsets"][1:], strict=True):
        x, mask = rebuild_histories({k: data[k][a:b] for k in ("values", "missing", "times_ms")})
        windows.append(x)
        masks.append(mask)
    x, mask = np.concatenate(windows), np.concatenate(masks)
    return apply_b4_normalizer(x, mask, normalizer), mask, data["targets"]


def train_fit(archive_path, manifest, normalizer, output, binding, family, seed, device, budget):
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
            "Checkpoint does not match the compact LeagueEWS freeze",
        )
        backend.load_state_dict(state["backend"])
        completed = state["completed_units"]
    finish = total if budget == 0 else min(total, completed + budget)
    with zipfile.ZipFile(archive_path) as archive:
        for unit in range(completed, finish):
            epoch, index = divmod(unit, 48)
            entry = manifest["shards"][index]
            require(entry["partition"] == "train", "Training cannot read calibration")
            started = time.perf_counter()
            x, mask, target = sequences(read_shard(archive, entry), normalizer)
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
                "last_shard_seconds": time.perf_counter() - started,
            }
            partial = checkpoint.with_suffix(".partial")
            backend.torch.save(state, partial)
            partial.replace(checkpoint)
            progress = {k: v for k, v in state.items() if k != "backend"}
            write_json(folder / "progress.json", progress)
            print(
                f"{family} seed {seed}: epoch {epoch + 1}/{EPOCHS}, "
                f"shard {index + 1}/48, loss {loss:.6f}, "
                f"{progress['last_shard_seconds']:.1f}s",
                flush=True,
            )
    return finish - completed, finish == total


def score_fit(archive_path, manifest, normalizer, output, binding, family, seed, device, cal, rows):
    folder = output / family / f"seed-{seed}"
    checkpoint = folder / "checkpoint.pt"
    backend = NotebookEWSBackend(seed, device, family=family)
    state = backend.torch.load(checkpoint, map_location="cpu", weights_only=True)
    require(
        state["freeze_sha256"] == binding and state["completed_units"] == 48 * EPOCHS,
        "Incomplete fit",
    )
    backend.load_state_dict(state["backend"])
    probabilities, truths, offsets = [], [], [0]
    with zipfile.ZipFile(archive_path) as archive:
        for entry in manifest["shards"][48:]:
            require(entry["partition"] == "calibration", "Invalid calibration membership")
            data = read_shard(archive, entry)
            x, mask, target = sequences(data, normalizer)
            probabilities.append(backend.predict_shard(x, mask))
            truths.append(target)
            offsets.extend((data["match_offsets"][1:] + offsets[-1]).tolist())
    scores, truth = np.concatenate(probabilities), np.concatenate(truths)
    require(
        np.array_equal(truth, cal["targets"]) and np.array_equal(offsets, cal["match_offsets"]),
        "Calibration alignment differs",
    )
    _, later = _chronological_halves(rows)
    selected = np.concatenate([np.arange(offsets[i], offsets[i + 1]) for i in later])
    warnings, counts = {}, {}
    for e, event in enumerate(EVENTS):
        for h, column in ((30, e * 4 + 2), (60, e * 4 + 3)):
            key = f"{event}_{h}"
            warnings[key], counts[key] = policy_report(cal, rows, scores[:, column], event, h)
    score_path = folder / "calibration-scores.npz"
    temporary = score_path.with_suffix(".partial")
    with temporary.open("wb") as f:
        np.savez_compressed(
            f,
            probabilities=scores,
            targets=truth,
            match_offsets=cal["match_offsets"],
            **{f"counts_{k}": v for k, v in counts.items()},
        )
    temporary.replace(score_path)
    report = {
        "family": family,
        "seed": seed,
        "freeze_sha256": binding,
        "checkpoint_sha256": sha(checkpoint),
        "scores_sha256": sha(score_path),
        "parameters": state["parameters"],
        "warnings": warnings,
        "row_metrics": {
            label: probabilistic_metrics(truth[selected, i], scores[selected, i])
            for i, label in enumerate(LABELS)
        },
        "horizon_monotonicity_violations_later": int(
            np.sum(np.any(np.diff(scores[selected].reshape(-1, 3, 4), axis=2) < 0, axis=2))
        ),
        "test_payloads_opened": 0,
    }
    write_json(folder / "report.json", report)
    print(f"Scored {family}, seed {seed}", flush=True)
    return report


def run(archive_path, output, repo, device, max_new_shards, preflight=False):
    require(max_new_shards >= 0, "Invalid shard budget")
    # Fail before lengthy validation if CUDA is unavailable; never substitute CPU.
    backend = NotebookEWSBackend(SEEDS[0], device, family="snapshot")
    runtime = {
        "device": device,
        "torch": backend.version,
        "cuda_build": backend.torch.version.cuda,
        "gpu_name": backend.torch.cuda.get_device_name() if device == "cuda" else None,
    }
    print(json.dumps(runtime), flush=True)
    del backend
    validation = validate_archive(archive_path, repo)
    with zipfile.ZipFile(archive_path) as z:
        manifest = json.loads(z.read("manifest.json"))
    output.mkdir(parents=True, exist_ok=True)
    source_files = [
        *sorted((repo / "src/league_ews").glob("*.py")),
        *(
            repo / "scripts" / name
            for name in (
                "run_compact_notebook.py",
                "league_compact_data.py",
                "run_three_event_trees.py",
                "export_league_three_events.py",
                "export_league_development.py",
            )
        ),
    ]
    frozen = {
        "schema_version": "league-ews-compact-notebook-freeze-v1",
        "original_plan": PLAN,
        "archive_sha256": EXPECTED_ARCHIVE,
        "runtime": runtime,
        "python": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name) for name in ("numpy", "scikit-learn", "pydantic")
        },
        "source_sha256": {str(p.relative_to(repo)): sha(p) for p in source_files},
        "adaptation": (
            "Compact input and checkpoint paths only; original training algorithm and policy"
        ),
        "test_payloads_present": 0,
    }
    freeze_path = output / "freeze.json"
    if freeze_path.exists():
        require(
            json.loads(freeze_path.read_bytes()) == frozen,
            "Freeze changed; preserve old run and use a new output",
        )
    else:
        write_json(freeze_path, frozen)
    binding = sha(freeze_path)
    normalizer = fit_normalizer(archive_path, manifest)
    norm_path = output / "normalizer.json"
    if norm_path.exists():
        require(json.loads(norm_path.read_bytes()) == normalizer, "Normalizer changed")
    else:
        write_json(norm_path, normalizer)
    write_json(output / "validation.json", validation)
    if preflight:
        return {
            "status": "ready",
            **runtime,
            "fits": 12,
            "epochs": EPOCHS,
            "training_rows": normalizer["training_observations"],
            "test_payloads_present": 0,
        }
    used = 0
    for family in FAMILIES:
        for seed in SEEDS:
            consumed, complete = train_fit(
                archive_path,
                manifest,
                normalizer,
                output,
                binding,
                family,
                seed,
                device,
                max_new_shards - used if max_new_shards else 0,
            )
            used += consumed
            if not complete or (max_new_shards and used >= max_new_shards):
                return {
                    "status": "paused-resume-same-command",
                    "new_training_shards": used,
                    "calibration_scored": False,
                }
    # No fitted-model calibration evaluation until the entire planned training grid completes.
    cal, rows = load_partition(archive_path, "calibration")
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
                    "Existing report changed",
                )
            else:
                report = score_fit(
                    archive_path,
                    manifest,
                    normalizer,
                    output,
                    binding,
                    family,
                    seed,
                    device,
                    cal,
                    rows,
                )
            reports[f"{family}/{seed}"] = report
    _, later = _chronological_halves(rows)
    routes = [rows[i]["regional_route"] for i in later]
    comparisons, macro, budgets = {}, [], []
    for seed in SEEDS:
        with (
            np.load(
                output / "leagueews" / f"seed-{seed}" / "calibration-scores.npz", allow_pickle=False
            ) as candidate,
            np.load(
                output / "gru" / f"seed-{seed}" / "calibration-scores.npz", allow_pickle=False
            ) as control,
        ):
            comparison = {
                f"{event}_{h}": compare_counts(
                    candidate[f"counts_{event}_{h}"], control[f"counts_{event}_{h}"], routes
                )
                for event in EVENTS
                for h in (30, 60)
            }
        comparisons[str(seed)] = comparison
        macro.append(
            float(np.mean([comparison[f"{e}_30"]["timely_recall_difference"] for e in EVENTS]))
        )
        budgets.append(
            all(
                reports[f"{f}/{seed}"]["warnings"][f"{e}_30"]["regional_budget_met"]
                for f in ("leagueews", "gru")
                for e in EVENTS
            )
        )
    result = {
        "schema_version": "league-ews-compact-notebook-summary-v1",
        "status": "complete-exploratory-architecture-screen",
        "freeze_sha256": binding,
        "models": reports,
        "leagueews_minus_gru": comparisons,
        "macro_30s_timely_recall_differences_by_seed": macro,
        "both_models_primary_regional_budgets_met_by_seed": budgets,
        "consistent_positive_exploratory_screen": all(v > 0 for v in macro) and all(budgets),
        "test_payloads_opened": 0,
        "interpretation": (
            "Not novelty or confirmation; calibration already reviewed; "
            "intervals conditional on fits/policies"
        ),
    }
    write_json(output / "summary.json", result)
    return {"status": result["status"], "summary": str(output / "summary.json")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/private/compact-notebook-v1"))
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--max-new-shards", type=int, default=1)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "experiment.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "A compact LeagueEWS worker is already running.\n")
        try:
            result = run(
                args.archive.resolve(),
                args.output.resolve(),
                Path.cwd(),
                args.device,
                args.max_new_shards,
                args.preflight,
            )
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            parser.exit(1, f"Compact LeagueEWS stopped: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
