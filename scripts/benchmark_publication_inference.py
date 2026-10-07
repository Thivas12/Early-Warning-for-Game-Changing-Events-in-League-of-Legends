"""Measure saved LeagueEWS/TCN inference using training inputs, without outcome scoring."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import subprocess
import time
import zipfile
from pathlib import Path

import numpy as np

from league_ews.coordination_experiment import sha, write_json
from league_ews.notebook_ews import NotebookEWSBackend, right_pad_sequences
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE
from scripts.run_compact_notebook import read_shard, sequences

SEEDS = (20260930, 20261001, 20261002)
SPEC = {
    "leagueews": ("league-timely-optimization-v1", "equal_sum", 1751647),
    "tcn": ("league-matched-optimization-v1", "equal_tcn", 557087),
}
PROTOCOL = "reports/publication-package-2026-10-07/runtime-protocol.md"


def describe(samples, batch):
    values = np.asarray(samples, dtype=np.float64)
    require(values.shape == (100,) and bool(np.isfinite(values).all()), "Invalid timings")
    require(bool((values > 0).all()), "Nonpositive timings")
    return {
        "calls": len(values),
        "median_ms": float(np.median(values)),
        "p95_ms": float(np.quantile(values, 0.95)),
        "windows_per_second_at_median": float(batch * 1000 / np.median(values)),
        "samples_ms": values.tolist(),
    }


def run(args):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch

    repo = Path(__file__).resolve().parents[1]
    require(torch.cuda.is_available(), "CUDA required; do not silently substitute CPU")
    require(not args.output.exists(), "Output exists; preserve this benchmark run")
    source_paths = [
        "scripts/benchmark_publication_inference.py",
        PROTOCOL,
        "src/league_ews/notebook_ews.py",
        "scripts/run_compact_notebook.py",
        "scripts/export_league_three_events.py",
        "src/league_ews/b4_normalizer.py",
    ]
    source_hashes = {}
    for relative in source_paths:
        frozen = subprocess.run(
            ["git", "show", f"{args.commit}:{relative}"],
            cwd=repo,
            check=True,
            capture_output=True,
        ).stdout
        require(frozen == (repo / relative).read_bytes(), "Benchmark source differs from commit")
        source_hashes[relative] = hashlib.sha256(frozen).hexdigest()
    archive_path = args.data_root / "league-three-event-export-v1/development.zip"
    require(sha(archive_path) == EXPECTED_ARCHIVE, "Wrong development archive")
    normalizer_path = args.data_root / "league-timely-optimization-v1/normalizer.json"
    normalizer = json.loads(normalizer_path.read_bytes())
    require(normalizer["fit_partitions"] == ["train"], "Normalizer not training-only")
    require(
        normalizer
        == json.loads(
            (args.data_root / "league-matched-optimization-v1/normalizer.json").read_bytes()
        ),
        "Model normalizers differ",
    )
    with zipfile.ZipFile(archive_path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        entry = manifest["shards"][0]
        require(entry["partition"] == "train", "Benchmark must use training only")
        inputs, mask, _ = sequences(read_shard(archive, entry), normalizer)
    chosen = np.linspace(0, len(inputs) - 1, 128, dtype=np.int64)
    packed, lengths = right_pad_sequences(inputs[chosen], mask[chosen])
    require(packed.shape == (128, 8, 55), "Unexpected model input shape")
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    records = []
    release = {
        "schema_version": "league-publication-runtime-v1",
        "commit": args.commit,
        "sources": source_hashes,
        "archive_sha256": EXPECTED_ARCHIVE,
        "training_shard_sha256": entry["sha256"],
        "normalizer_sha256": sha(normalizer_path),
        "input_sha256": hashlib.sha256(packed.tobytes() + lengths.tobytes()).hexdigest(),
        "input_shape": list(packed.shape),
        "history_lengths": np.bincount(lengths, minlength=9).tolist(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": str(torch.__version__),
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "cpu_threads": 2,
        "interop_threads": 1,
        "precision": "float32; no autocast; deterministic algorithms",
        "timed_scope": "resident-input forward plus sigmoid, synchronized host wall time",
        "excluded": "loading, feature building, transfers, NumPy output and alert policy",
        "calibration_payloads_opened": 0,
        "test_payloads_opened": 0,
        "new_fits": 0,
        "new_outcome_evaluations": 0,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "limitations": [
            "One laptop, uncontrolled power/thermal state and background GPU use",
            "Repeated timings are not independent deployment workloads or accuracy estimates",
            "No serving, network, policy or end-to-end latency claim",
        ],
    }
    args.output.mkdir(parents=True)
    write_json(args.output / "release.json", release)
    for seed_index, seed in enumerate(SEEDS):
        order = ("leagueews", "tcn") if seed_index % 2 == 0 else ("tcn", "leagueews")
        for architecture in order:
            study, family, parameter_count = SPEC[architecture]
            folder = args.data_root / study / family / f"seed-{seed}"
            report = json.loads((folder / "report.json").read_bytes())
            checkpoint = folder / "checkpoint.pt"
            checksum = sha(checkpoint)
            require(checksum == report["checkpoint_sha256"], "Checkpoint/report mismatch")
            state = torch.load(checkpoint, map_location="cpu", weights_only=True)
            require(
                state["family"] == family
                and state["seed"] == seed
                and state["completed_units"] == 576
                and state["freeze_sha256"] == sha(args.data_root / study / "freeze.json"),
                "Incomplete or incorrectly bound checkpoint",
            )
            reference = None
            for device in ("cpu", "cuda"):
                backend = NotebookEWSBackend(seed, device, family=architecture)
                backend.model.load_state_dict(state["backend"]["model"], strict=True)
                require(
                    sum(p.numel() for p in backend.model.parameters()) == parameter_count,
                    "Unexpected model capacity",
                )
                # Optimizer state is irrelevant to inference and is not loaded.
                del backend.optimizer
                backend.model.eval()
                with torch.inference_mode():
                    x = torch.from_numpy(packed).to(device)
                    n = torch.from_numpy(lengths)
                    prediction = torch.sigmoid(backend.model(x, n)).cpu().numpy()
                    require(bool(np.isfinite(prediction).all()), "Nonfinite prediction")
                    if reference is None:
                        reference = prediction
                    else:
                        require(
                            bool(np.allclose(reference, prediction, rtol=1e-4, atol=1e-5)),
                            "CPU/CUDA output parity failed",
                        )
                    for batch in (1, 128):
                        for _ in range(20):
                            torch.sigmoid(backend.model(x[:batch], n[:batch]))
                        if device == "cuda":
                            torch.cuda.synchronize()
                            torch.cuda.reset_peak_memory_stats()
                        durations = []
                        for i in range(100):
                            start = i % 128 if batch == 1 else 0
                            if device == "cuda":
                                torch.cuda.synchronize()
                            began = time.perf_counter_ns()
                            torch.sigmoid(
                                backend.model(x[start : start + batch], n[start : start + batch])
                            )
                            if device == "cuda":
                                torch.cuda.synchronize()
                            durations.append((time.perf_counter_ns() - began) / 1e6)
                        records.append(
                            {
                                "architecture": architecture,
                                "seed": seed,
                                "device": device,
                                "batch": batch,
                                "parameters": parameter_count,
                                "checkpoint_sha256": checksum,
                                "peak_cuda_allocated_bytes": (
                                    torch.cuda.max_memory_allocated() if device == "cuda" else None
                                ),
                                **describe(durations, batch),
                            }
                        )
                        write_json(args.output / "progress.json", {"records": records})
                        print(
                            architecture, seed, device, batch, records[-1]["median_ms"], flush=True
                        )
                del x, n, backend
                gc.collect()
                torch.cuda.empty_cache()
            del state
    require(len(records) == 24, "Incomplete benchmark")
    write_json(
        args.output / "runtime.json",
        {
            **release,
            "status": "complete-system-microbenchmark",
            "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cpu_cuda_parity": "all six saved fits passed rtol=1e-4, atol=1e-5",
            "records": records,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    run(parser.parse_args())
