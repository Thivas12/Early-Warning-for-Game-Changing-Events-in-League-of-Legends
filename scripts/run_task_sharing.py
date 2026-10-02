"""Train nine independent event encoders; gate scoring on completion of every fit."""

from __future__ import annotations

import argparse
import ast
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
from league_ews.notebook_experiment import EPOCHS, PLAN, SEEDS
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, load_partition, validate_archive
from scripts.run_compact_notebook import fit_normalizer, read_shard, sequences
from scripts.run_three_event_trees import policy_report
from scripts.task_sharing_backend import IndependentEventBackend


def train_fit(archive_path, manifest, normalizer, output, binding, event, seed, device, budget=0):
    backend = IndependentEventBackend(seed, device, event=event)
    folder = output / event / f"seed-{seed}"
    folder.mkdir(parents=True, exist_ok=True)
    checkpoint = folder / "checkpoint.pt"
    completed, seconds = 0, 0.0
    if checkpoint.exists():
        state = backend.torch.load(checkpoint, map_location="cpu", weights_only=True)
        require(
            state["freeze_sha256"] == binding
            and state["event"] == event
            and state["seed"] == seed
            and state["device"] == device
            and state["torch_version"] == backend.version
            and 0 <= state["completed_units"] <= 48 * EPOCHS,
            "Independent-event checkpoint mismatch",
        )
        backend.load_state_dict(state["backend"])
        completed, seconds = state["completed_units"], state["training_seconds"]
        # A crash can occur after checkpoint replacement but before progress replacement.
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
            x, mask, target = sequences(read_shard(archive, entry), normalizer)
            loss, rows = backend.train_shard(x, mask, target, seed=seed + epoch * 10000 + index)
            require(np.isfinite(loss), "Nonfinite training loss; retaining preceding checkpoint")
            elapsed = time.perf_counter() - started
            seconds += elapsed
            state = {
                "freeze_sha256": binding,
                "event": event,
                "seed": seed,
                "device": device,
                "torch_version": backend.version,
                "completed_units": unit + 1,
                "backend": backend.state_dict(),
                "last_loss": loss,
                "last_rows": rows,
                "parameters": sum(p.numel() for p in backend.model.parameters()),
                "active_parameters": sum(
                    p.numel() for p in backend.model.parameters() if p.requires_grad
                ),
                "last_shard_seconds": elapsed,
                "training_seconds": seconds,
            }
            partial = checkpoint.with_suffix(".partial")
            backend.torch.save(state, partial)
            partial.replace(checkpoint)
            write_json(folder / "progress.json", {k: v for k, v in state.items() if k != "backend"})
            print(
                f"{event} independent seed {seed}: epoch {epoch + 1}/12 "
                f"shard {index + 1}/48 loss {loss:.6f} {elapsed:.2f}s",
                flush=True,
            )
    return finish - completed, finish == 48 * EPOCHS


def score_fit(archive_path, manifest, normalizer, output, binding, event, seed, device, cal, rows):
    folder = output / event / f"seed-{seed}"
    backend = IndependentEventBackend(seed, device, event=event)
    state = backend.torch.load(folder / "checkpoint.pt", map_location="cpu", weights_only=True)
    require(
        state["freeze_sha256"] == binding
        and state["completed_units"] == 576
        and state["event"] == event
        and state["seed"] == seed
        and state["device"] == device
        and state["torch_version"] == backend.version,
        "Incomplete or mismatched fit",
    )
    backend.load_state_dict(state["backend"])
    probabilities, truths, offsets = [], [], [0]
    with zipfile.ZipFile(archive_path) as archive:
        for entry in manifest["shards"][48:]:
            require(entry["partition"] == "calibration", "Invalid calibration membership")
            data = read_shard(archive, entry)
            x, mask, target = sequences(data, normalizer)
            probabilities.append(backend.predict_shard(x, mask))
            truths.append(target[:, backend.columns])
            offsets.extend((data["match_offsets"][1:] + offsets[-1]).tolist())
    scores, truth = np.concatenate(probabilities), np.concatenate(truths)
    require(
        scores.shape == truth.shape
        and np.isfinite(scores).all()
        and ((scores >= 0) & (scores <= 1)).all(),
        "Invalid event probabilities",
    )
    require(
        np.array_equal(truth, cal["targets"][:, backend.columns])
        and np.array_equal(offsets, cal["match_offsets"]),
        "Calibration alignment differs",
    )
    _, later = _chronological_halves(rows)
    selected = np.concatenate([np.arange(offsets[i], offsets[i + 1]) for i in later])
    warnings, counts = {}, {}
    for h, column in ((30, 2), (60, 3)):
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
        "event": event,
        "seed": seed,
        "freeze_sha256": binding,
        "checkpoint_sha256": sha(folder / "checkpoint.pt"),
        "scores_sha256": sha(score_path),
        "parameters": state["parameters"],
        "active_parameters": state["active_parameters"],
        "training_seconds": state["training_seconds"],
        "warnings": warnings,
        "row_metrics": {
            label: probabilistic_metrics(truth[selected, i], scores[selected, i])
            for i, label in enumerate(LABELS[backend.columns])
        },
        "horizon_monotonicity_violations_later": int(
            np.sum(np.any(np.diff(scores[selected], axis=1) < 0, axis=1))
        ),
        "test_payloads_opened": 0,
    }
    write_json(folder / "report.json", report)
    print(f"Scored independent {event}, seed {seed}", flush=True)
    return report


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    require(plan["events"] == list(EVENTS), "All three events required")
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
    control_summary = json.loads((args.control / "summary.json").read_bytes())
    require(
        control_summary["status"] == "complete-exploratory-architecture-screen"
        and control_summary["freeze_sha256"] == sha(args.control / "freeze.json")
        and control_summary["test_payloads_opened"] == 0,
        "Control is not a completed development-only screen",
    )
    # Verify the immutable control checkout, then allow only the explicitly frozen
    # AST-identical formatting repair in the maintained policy-importing script.
    source_digests = {}
    for name, digest in original_freeze["source_sha256"].items():
        require(sha(args.control_source / name) == digest, f"Control source changed: {name}")
        current = sha(repo / name)
        if current != digest:
            require(name == "scripts/run_three_event_trees.py", f"Source changed: {name}")
            require(current == plan["formatted_policy_source_sha256"], "Policy source changed")
            require(
                ast.dump(ast.parse((repo / name).read_text()))
                == ast.dump(ast.parse((args.control_source / name).read_text())),
                "Policy formatting repair changed semantics",
            )
        source_digests[name] = current
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
                and report["scores_sha256"] == sha(p / "calibration-scores.npz")
                and report == control_summary["models"][f"{f}/{seed}"],
                "Control artifacts changed",
            )
    backend = IndependentEventBackend(SEEDS[0], args.device, event=EVENTS[0])
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
        "schema_version": "league-task-sharing-freeze-v1",
        "plan": plan,
        "plan_sha256": sha(args.plan),
        "archive_sha256": EXPECTED_ARCHIVE,
        "runtime": runtime,
        "python": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name) for name in ("numpy", "scikit-learn", "pydantic")
        },
        "source_sha256": {
            **source_digests,
            "scripts/task_sharing_backend.py": sha(repo / "scripts/task_sharing_backend.py"),
            "scripts/run_task_sharing.py": sha(Path(__file__)),
            "scripts/run_task_sharing.sh": sha(Path(__file__).with_suffix(".sh")),
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
    for event in EVENTS:
        for seed in SEEDS:
            consumed, complete = train_fit(
                args.archive,
                manifest,
                normalizer,
                args.output,
                binding,
                event,
                seed,
                args.device,
                args.max_new_shards - used if args.max_new_shards else 0,
            )
            used += consumed
            if not complete or (args.max_new_shards and used >= args.max_new_shards):
                return {"status": "paused-resume-same-command", "new_shards": used}
    # All nine independent models finish before any fitted-model calibration scoring.
    cal, rows = load_partition(args.archive, "calibration")
    reports = {}
    for event in EVENTS:
        for seed in SEEDS:
            p = args.output / event / f"seed-{seed}"
            if (p / "report.json").exists():
                r = json.loads((p / "report.json").read_bytes())
                require(
                    r["freeze_sha256"] == binding
                    and r["event"] == event
                    and r["seed"] == seed
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
                    event,
                    seed,
                    args.device,
                    cal,
                    rows,
                )
            reports[f"{event}/{seed}"] = r
    summary = {
        "schema_version": "league-task-sharing-results-v1",
        "status": "complete-exploratory-task-sharing",
        "freeze_sha256": binding,
        "models": reports,
        "test_payloads_opened": 0,
    }
    write_json(args.output / "summary.json", summary)
    return {"status": summary["status"], "summary": str(args.output / "summary.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("archive", "control", "control-source", "output", "plan"):
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
