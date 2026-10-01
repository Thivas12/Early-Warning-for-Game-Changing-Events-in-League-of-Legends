"""Train a fixed architecture with current state repeated at historical positions.

The existing neural study is read only. Valid history lengths and frame ages stay
unchanged; values and missingness at valid positions become the current frame.
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

from league_ews.baseline_floor import LABELS
from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.metrics import probabilistic_metrics
from league_ews.notebook_ews import NotebookEWSBackend
from league_ews.notebook_experiment import EPOCHS, PLAN, SEEDS
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, load_partition, validate_archive
from scripts.run_compact_notebook import fit_normalizer, read_shard, sequences
from scripts.run_three_event_trees import policy_report


def current_only(inputs: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Remove past state while keeping age, valid length, padding and current state."""
    require(inputs.ndim == 3 and inputs.shape[2] == 55, "Expected 55 input channels")
    require(mask.shape == inputs.shape[:2] and mask.dtype == np.bool_, "Invalid mask")
    require(np.all(mask[:, -1]), "Current frame must be the last valid position")
    require(np.all(np.diff(mask.astype(int), axis=1) >= 0), "Expected right-aligned history")
    result = inputs.copy()
    result[..., :54] = np.where(mask[..., None], inputs[:, -1:, :54], result[..., :54])
    return result


def ablated_sequences(data: dict, normalizer: dict) -> tuple:
    x, mask, targets = sequences(data, normalizer)
    return current_only(x, mask), mask, targets


def train_fit(archive_path, manifest, normalizer, output, binding, family, seed, device, budget=0):
    backend = NotebookEWSBackend(seed, device, family=family)
    folder = output / family / f"seed-{seed}"
    folder.mkdir(parents=True, exist_ok=True)
    checkpoint = folder / "checkpoint.pt"
    completed, seconds = 0, 0.0
    if checkpoint.exists():
        state = backend.torch.load(checkpoint, map_location="cpu", weights_only=True)
        require(
            state["freeze_sha256"] == binding
            and state["family"] == family
            and state["seed"] == seed
            and state["device"] == device
            and state["torch_version"] == backend.version
            and 0 <= state["completed_units"] <= 48 * EPOCHS,
            "Ablation checkpoint mismatch",
        )
        backend.load_state_dict(state["backend"])
        completed, seconds = state["completed_units"], state["training_seconds"]
    finish = min(48 * EPOCHS, completed + budget) if budget else 48 * EPOCHS
    with zipfile.ZipFile(archive_path) as archive:
        for unit in range(completed, finish):
            epoch, index = divmod(unit, 48)
            entry = manifest["shards"][index]
            require(entry["partition"] == "train", "Training must use train only")
            started = time.perf_counter()
            x, mask, target = ablated_sequences(read_shard(archive, entry), normalizer)
            loss, rows = backend.train_shard(x, mask, target, seed=seed + epoch * 10000 + index)
            require(np.isfinite(loss), "Nonfinite training loss; retaining preceding checkpoint")
            elapsed = time.perf_counter() - started
            seconds += elapsed
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
                "last_shard_seconds": elapsed,
                "training_seconds": seconds,
            }
            partial = checkpoint.with_suffix(".partial")
            backend.torch.save(state, partial)
            partial.replace(checkpoint)
            write_json(folder / "progress.json", {k: v for k, v in state.items() if k != "backend"})
            print(
                f"{family} current-only seed {seed}: epoch {epoch + 1}/12 "
                f"shard {index + 1}/48 loss {loss:.6f} {elapsed:.2f}s",
                flush=True,
            )
    return finish - completed, finish == 48 * EPOCHS


def score_fit(archive_path, manifest, normalizer, output, binding, family, seed, device, cal, rows):
    folder = output / family / f"seed-{seed}"
    backend = NotebookEWSBackend(seed, device, family=family)
    state = backend.torch.load(folder / "checkpoint.pt", map_location="cpu", weights_only=True)
    require(state["freeze_sha256"] == binding and state["completed_units"] == 576, "Incomplete fit")
    backend.load_state_dict(state["backend"])
    probabilities, truths, offsets = [], [], [0]
    with zipfile.ZipFile(archive_path) as archive:
        for entry in manifest["shards"][48:]:
            require(entry["partition"] == "calibration", "Invalid calibration membership")
            data = read_shard(archive, entry)
            x, mask, target = ablated_sequences(data, normalizer)
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
    with score_path.with_suffix(".partial").open("wb") as f:
        np.savez_compressed(
            f,
            probabilities=scores,
            targets=truth,
            match_offsets=cal["match_offsets"],
            **{f"counts_{k}": v for k, v in counts.items()},
        )
    score_path.with_suffix(".partial").replace(score_path)
    report = {
        "family": family,
        "seed": seed,
        "freeze_sha256": binding,
        "checkpoint_sha256": sha(folder / "checkpoint.pt"),
        "scores_sha256": sha(score_path),
        "parameters": state["parameters"],
        "training_seconds": state["training_seconds"],
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
    print(f"Scored current-only {family}, seed {seed}", flush=True)
    return report


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    family = plan["family"]
    require(family in ("leagueews", "gru", "tcn"), "Need a temporal encoder")
    require(plan["original_plan"] == PLAN, "Original training plan changed")
    require(plan["seeds"] == list(SEEDS), "All three seeds required")
    require(
        sha(args.control / "summary.json") == plan["control_summary_sha256"],
        "Control summary changed",
    )
    require(
        sha(args.control / "freeze.json") == plan["control_freeze_sha256"], "Control freeze changed"
    )
    original_freeze = json.loads((args.control / "freeze.json").read_bytes())
    for name, digest in original_freeze["source_sha256"].items():
        require(sha(repo / name) == digest, f"Original implementation changed: {name}")
    for f in PLAN["families"]:
        for seed in SEEDS:
            p = args.control / f / f"seed-{seed}"
            require(
                json.loads((p / "progress.json").read_bytes())["completed_units"] == 576,
                "Control training unfinished",
            )
            report = json.loads((p / "report.json").read_bytes())
            require(
                report["checkpoint_sha256"] == sha(p / "checkpoint.pt")
                and report["scores_sha256"] == sha(p / "calibration-scores.npz"),
                "Control artifacts changed",
            )
    backend = NotebookEWSBackend(SEEDS[0], args.device, family=family)
    runtime = {
        "device": args.device,
        "torch": backend.version,
        "cuda_build": backend.torch.version.cuda,
        "gpu_name": backend.torch.cuda.get_device_name() if args.device == "cuda" else None,
    }
    require(runtime == original_freeze["runtime"], "Follow-up runtime differs from control")
    del backend
    validation = validate_archive(args.archive, repo)
    with zipfile.ZipFile(args.archive) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    normalizer = fit_normalizer(args.archive, manifest)
    require(
        normalizer == json.loads((args.control / "normalizer.json").read_bytes()),
        "Normalizer differs",
    )
    frozen = {
        "schema_version": "league-history-ablation-freeze-v1",
        "plan": plan,
        "plan_sha256": sha(args.plan),
        "archive_sha256": EXPECTED_ARCHIVE,
        "runtime": runtime,
        "python": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name) for name in ("numpy", "scikit-learn", "pydantic")
        },
        "source_sha256": {
            **original_freeze["source_sha256"],
            "scripts/run_history_ablation.py": sha(Path(__file__)),
            "scripts/run_history_ablation.sh": sha(Path(__file__).with_suffix(".sh")),
        },
        "normalizer_sha256": sha(args.control / "normalizer.json"),
    }
    freeze_path = args.output / "freeze.json"
    if freeze_path.exists():
        require(json.loads(freeze_path.read_bytes()) == frozen, "Freeze changed; preserve old run")
    else:
        write_json(freeze_path, frozen)
    binding = sha(freeze_path)
    write_json(args.output / "validation.json", validation)
    write_json(args.output / "normalizer.json", normalizer)
    print(json.dumps({"freeze_sha256": binding, **runtime}), flush=True)
    if args.preflight:
        return {"status": "ready", "freeze_sha256": binding}
    used = 0
    for seed in SEEDS:
        consumed, complete = train_fit(
            args.archive,
            manifest,
            normalizer,
            args.output,
            binding,
            family,
            seed,
            args.device,
            args.max_new_shards - used if args.max_new_shards else 0,
        )
        used += consumed
        if not complete or (args.max_new_shards and used >= args.max_new_shards):
            return {"status": "paused-resume-same-command", "new_shards": used}
    # All three retrained models must finish before any fitted-model calibration scoring.
    cal, rows = load_partition(args.archive, "calibration")
    reports = {}
    for seed in SEEDS:
        p = args.output / family / f"seed-{seed}"
        if (p / "report.json").exists():
            r = json.loads((p / "report.json").read_bytes())
            require(
                r["freeze_sha256"] == binding
                and r["checkpoint_sha256"] == sha(p / "checkpoint.pt")
                and r["scores_sha256"] == sha(p / "calibration-scores.npz"),
                "Existing report changed",
            )
        else:
            r = score_fit(
                args.archive,
                manifest,
                normalizer,
                args.output,
                binding,
                family,
                seed,
                args.device,
                cal,
                rows,
            )
        reports[f"{family}/{seed}"] = r
    summary = {
        "schema_version": "league-history-ablation-results-v1",
        "status": "complete-exploratory-history-ablation",
        "freeze_sha256": binding,
        "models": reports,
        "test_payloads_opened": 0,
    }
    write_json(args.output / "summary.json", summary)
    return {"status": summary["status"], "summary": str(args.output / "summary.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("archive", "control", "output", "plan"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--max-new-shards", type=int, default=0)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    require(args.max_new_shards >= 0, "Invalid shard budget")
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "experiment.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Hold a shared lock on the original worker's lock: it must have finished.
        # Opening read-only and acquiring this advisory lock changes no experiment file.
        with (args.control / "experiment.lock").open("rb") as control_lock:
            fcntl.flock(control_lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
            print(json.dumps(run(args), indent=2))
