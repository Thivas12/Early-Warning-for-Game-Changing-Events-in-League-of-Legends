"""Train the nine loss-weight and projection controls before committed-analysis release."""

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

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.notebook_experiment import EPOCHS, PLAN, SEEDS
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, load_partition, validate_archive
from scripts.run_compact_notebook import fit_normalizer, read_shard, sequences
from scripts.scoring_release import verify as verify_scoring_release
from scripts.timely_neural_targets import fitted_targets
from scripts.timely_optimization_backend import NEW_VARIANTS, VARIANTS, TimelyOptimizationBackend

FAMILIES = NEW_VARIANTS


def train_fit(archive_path, manifest, normalizer, output, binding, family, seed, device, budget=0):
    backend = TimelyOptimizationBackend(seed, device, variant=family)
    folder = output / family / f"seed-{seed}"
    folder.mkdir(parents=True, exist_ok=True)
    checkpoint = folder / "checkpoint.pt"
    completed, seconds = 0, 0.0
    if checkpoint.exists():
        state = backend.torch.load(checkpoint, map_location="cpu", weights_only=True)
        require(
            state["freeze_sha256"] == binding
            and state["family"] == family
            and state["variant_specification"] == VARIANTS[family]
            and state["seed"] == seed
            and state["device"] == device
            and state["torch_version"] == backend.version
            and type(state["completed_units"]) is int
            and 0 <= state["completed_units"] <= 48 * EPOCHS,
            "Timely optimization checkpoint mismatch",
        )
        backend.load_state_dict(state["backend"])
        completed, seconds = state["completed_units"], state["training_seconds"]
        write_json(folder / "progress.json", {k: v for k, v in state.items() if k != "backend"})
    else:
        require(
            not (folder / "progress.json").exists() and not (folder / "report.json").exists(),
            "Missing checkpoint for existing fit; preserve artifacts",
        )
    finish = min(48 * EPOCHS, completed + budget) if budget else 48 * EPOCHS
    with zipfile.ZipFile(archive_path) as archive:
        for unit in range(completed, finish):
            epoch, index = divmod(unit, 48)
            entry = manifest["shards"][index]
            require(entry["partition"] == "train", "Training must use train only")
            started = time.perf_counter()
            data = read_shard(archive, entry)
            x, mask, _ = sequences(data, normalizer)
            target = fitted_targets(data)
            loss, rows = backend.train_shard(x, mask, target, seed=seed + epoch * 10000 + index)
            require(np.isfinite(loss), "Nonfinite loss; retaining preceding checkpoint")
            require(
                all(bool(backend.torch.isfinite(p).all()) for p in backend.model.parameters()),
                "Nonfinite parameters; retaining preceding checkpoint",
            )
            elapsed = time.perf_counter() - started
            seconds += elapsed
            state = {
                "freeze_sha256": binding,
                "family": family,
                "variant_specification": VARIANTS[family],
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
                f"{family} timely seed {seed}: epoch {epoch + 1}/12 "
                f"shard {index + 1}/48 loss {loss:.6f} {elapsed:.2f}s",
                flush=True,
            )
    return finish - completed, finish == 48 * EPOCHS


def score_fit(archive_path, manifest, normalizer, output, binding, family, seed, device, cal, rows):
    """Save predictions only; policy selection/evaluation has a separate global gate."""
    folder = output / family / f"seed-{seed}"
    backend = TimelyOptimizationBackend(seed, device, variant=family)
    state = backend.torch.load(folder / "checkpoint.pt", map_location="cpu", weights_only=True)
    require(
        state["freeze_sha256"] == binding
        and state["completed_units"] == 576
        and state["family"] == family
        and state["variant_specification"] == VARIANTS[family]
        and state["seed"] == seed
        and state["device"] == device
        and state["torch_version"] == backend.version,
        "Incomplete or mismatched fit",
    )
    backend.load_state_dict(state["backend"])
    probabilities, truths, fitted, offsets = [], [], [], [0]
    with zipfile.ZipFile(archive_path) as archive:
        for entry in manifest["shards"][48:]:
            require(entry["partition"] == "calibration", "Invalid calibration membership")
            data = read_shard(archive, entry)
            x, mask, target = sequences(data, normalizer)
            probabilities.append(backend.predict_shard(x, mask))
            truths.append(target)
            fitted.append(fitted_targets(data))
            offsets.extend((data["match_offsets"][1:] + offsets[-1]).tolist())
    scores, truth, fitted = (
        np.concatenate(probabilities),
        np.concatenate(truths),
        np.concatenate(fitted),
    )
    require(
        scores.shape == truth.shape
        and np.isfinite(scores).all()
        and ((scores >= 0) & (scores <= 1)).all(),
        "Invalid probabilities",
    )
    require(
        np.array_equal(truth, cal["targets"])
        and np.array_equal(offsets, cal["match_offsets"])
        and np.array_equal(fitted, fitted_targets(cal)),
        "Calibration alignment differs",
    )
    score_path = folder / "calibration-scores.npz"
    with score_path.with_suffix(".partial").open("wb") as stream:
        np.savez_compressed(
            stream,
            probabilities=scores,
            targets=truth,
            fitted_targets=fitted,
            match_offsets=cal["match_offsets"],
        )
    score_path.with_suffix(".partial").replace(score_path)
    report = {
        "family": family,
        "variant_specification": VARIANTS[family],
        "seed": seed,
        "freeze_sha256": binding,
        "checkpoint_sha256": sha(folder / "checkpoint.pt"),
        "scores_sha256": sha(score_path),
        "parameters": state["parameters"],
        "training_seconds": state["training_seconds"],
        "target_semantics": (
            "10/20 cumulative auxiliaries; next-event 10-30/20-60 useful-lead heads"
        ),
        "policy_evaluation": "not performed; requires separate all-early-policy gate",
        "test_payloads_opened": 0,
    }
    write_json(folder / "report.json", report)
    print(f"Saved predictions for timely {family}, seed {seed}", flush=True)
    return report


def verify_control(control, plan, repo):
    require(
        sha(control / "freeze.json") == plan["timely_freeze_sha256"]
        and sha(control / "summary.json") == plan["timely_summary_sha256"],
        "Useful-lead control changed",
    )
    frozen = json.loads((control / "freeze.json").read_bytes())
    summary = json.loads((control / "summary.json").read_bytes())
    require(
        summary["status"] == "complete-exploratory-timely-neural-predictions"
        and summary["freeze_sha256"] == plan["timely_freeze_sha256"]
        and summary["test_payloads_opened"] == 0
        and frozen["archive_sha256"] == EXPECTED_ARCHIVE
        and set(summary["models"]) == {f"{f}/{s}" for f in ("leagueews", "tcn") for s in SEEDS},
        "Incomplete useful-lead control",
    )
    require(
        all(sha(repo / p) == v for p, v in frozen["source_sha256"].items()),
        "Control source changed",
    )
    require(sha(control / "normalizer.json") == frozen["normalizer_sha256"], "Normalizer changed")
    for identity, report in summary["models"].items():
        family, seed = identity.split("/")
        folder = control / family / f"seed-{seed}"
        progress = json.loads((folder / "progress.json").read_bytes())
        require(
            report == json.loads((folder / "report.json").read_bytes())
            and report["family"] == progress["family"] == family
            and report["seed"] == progress["seed"] == int(seed)
            and report["freeze_sha256"] == progress["freeze_sha256"] == summary["freeze_sha256"]
            and progress["completed_units"] == 576
            and report["checkpoint_sha256"] == sha(folder / "checkpoint.pt")
            and report["scores_sha256"] == sha(folder / "calibration-scores.npz"),
            "Control checkpoint or scores changed",
        )
    return frozen


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    require(
        plan["events"] == list(EVENTS)
        and plan["families"] == list(FAMILIES)
        and plan["seeds"] == list(SEEDS)
        and plan["original_plan"] == PLAN
        and plan["variants"] == json.loads(json.dumps(VARIANTS)),
        "Factorial training plan differs",
    )
    original = verify_control(args.control, plan, repo)
    backend = TimelyOptimizationBackend(SEEDS[0], args.device, variant=FAMILIES[0])
    runtime = {
        "device": args.device,
        "torch": backend.version,
        "cuda_build": backend.torch.version.cuda,
        "gpu_name": backend.torch.cuda.get_device_name() if args.device == "cuda" else None,
    }
    require(runtime == original["runtime"], "Runtime differs from useful-lead control")
    del backend
    validation = validate_archive(args.archive, repo)
    with zipfile.ZipFile(args.archive) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    normalizer = fit_normalizer(args.archive, manifest)
    require(
        normalizer == json.loads((args.control / "normalizer.json").read_bytes()),
        "Training-only normalizer differs",
    )
    sources = {
        **original["source_sha256"],
        **{
            name: sha(repo / name)
            for name in (
                "scripts/timely_optimization_backend.py",
                "scripts/pcgrad_backend.py",
                "scripts/run_timely_optimization.py",
                "scripts/run_timely_optimization.sh",
                "scripts/scoring_release.py",
            )
        },
    }
    frozen = {
        "schema_version": "league-timely-optimization-freeze-v1",
        "plan": plan,
        "plan_sha256": sha(args.plan),
        "archive_sha256": EXPECTED_ARCHIVE,
        "runtime": runtime,
        "python": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name) for name in ("numpy", "scikit-learn", "pydantic")
        },
        "source_sha256": sources,
        "normalizer_sha256": sha(args.control / "normalizer.json"),
        "control_freeze_sha256": sha(args.control / "freeze.json"),
        "control_summary_sha256": sha(args.control / "summary.json"),
    }
    path = args.output / "freeze.json"
    if path.exists():
        require(json.loads(path.read_bytes()) == frozen, "Freeze differs; preserve existing study")
    else:
        write_json(path, frozen)
    binding = sha(path)
    write_json(args.output / "validation.json", validation)
    write_json(args.output / "normalizer.json", normalizer)
    print(json.dumps({"freeze_sha256": binding, **runtime}), flush=True)
    if args.preflight:
        return {"status": "ready", "freeze_sha256": binding}
    used = 0
    for family in FAMILIES:
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
    if not (args.output / "analysis-release.json").exists():
        return {"status": "awaiting-committed-analysis-release", "new_scores": 0}
    verify_scoring_release(repo, args.output, args.plan, plan["analysis_sources"])
    cal, rows = load_partition(args.archive, "calibration")
    reports = {}
    for family in FAMILIES:
        for seed in SEEDS:
            folder = args.output / family / f"seed-{seed}"
            path = folder / "report.json"
            if path.exists():
                report = json.loads(path.read_bytes())
                require(
                    report["freeze_sha256"] == binding
                    and report["family"] == family
                    and report["seed"] == seed
                    and report["checkpoint_sha256"] == sha(folder / "checkpoint.pt")
                    and report["scores_sha256"] == sha(folder / "calibration-scores.npz"),
                    "Existing scored fit changed",
                )
            else:
                report = score_fit(
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
            reports[f"{family}/{seed}"] = report
    summary = {
        "schema_version": "league-timely-optimization-predictions-v1",
        "status": "complete-exploratory-timely-optimization-predictions",
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
        with (args.control / "experiment.lock").open("rb") as control_lock:
            fcntl.flock(control_lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
            print(json.dumps(run(args), indent=2))
