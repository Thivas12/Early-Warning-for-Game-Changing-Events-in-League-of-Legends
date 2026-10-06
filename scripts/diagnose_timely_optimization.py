"""Training-only local update diagnostics; never replace a fitted checkpoint.

Each virtual AdamW step starts from the same saved useful-lead model, optimizer
and RNG state. Observed loss changes reuse the same dropout masks. These local
measurements do not predict the outcome of training an alternative optimizer.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from league_ews.coordination_experiment import sha
from league_ews.notebook_ews import right_pad_sequences
from league_ews.notebook_experiment import SEEDS
from scripts.export_league_development import require
from scripts.league_compact_data import validate_archive
from scripts.run_compact_notebook import read_shard, sequences
from scripts.timely_neural_targets import fitted_targets
from scripts.timely_optimization_backend import VARIANTS, TimelyOptimizationBackend, backward


def local_step(backend, state, x, mask, target, *, projection_seed):
    """Mutate only a temporary backend; restore the source state before every probe."""
    backend.load_state_dict(copy.deepcopy(state))
    backend.model.train()
    backend.optimizer.zero_grad(set_to_none=True)
    torch = backend.torch
    packed, lengths = right_pad_sequences(x, mask)
    inputs = torch.from_numpy(packed).to(backend.device)
    lengths = torch.from_numpy(lengths)
    truth = torch.from_numpy(target.astype(np.float32)).to(backend.device)
    cpu_rng = torch.get_rng_state()
    cuda_rng = torch.cuda.get_rng_state_all() if backend.device == "cuda" else []
    parameters = list(backend.model.parameters())
    named = list(backend.model.named_parameters())
    shared = [i for i, (name, _) in enumerate(named) if not name.startswith("heads.")]
    before_parameters = [p.detach().clone() for p in parameters]
    logits = backend.model(inputs, lengths)
    columns = torch.nn.functional.binary_cross_entropy_with_logits(logits, truth, reduction="none")
    losses = columns.reshape(-1, 3, 4).mean((0, 2))
    gradients = [torch.autograd.grad(losses[e], parameters, retain_graph=True) for e in range(3)]
    shared_matrix = torch.stack(
        [torch.cat([gradient[i].flatten() for i in shared]) for gradient in gradients]
    )
    weighted = shared_matrix * shared_matrix.new_tensor(backend.weights)[:, None]
    gram = (weighted.double() @ weighted.double().T).detach().cpu().numpy()
    norms = np.sqrt(np.maximum(np.diag(gram), 0))
    cosine = gram / np.maximum(np.outer(norms, norms), 1e-30)
    raw_descent = gram.sum(axis=1) / np.maximum(np.diag(gram), 1e-30)
    before_loss = losses.detach().cpu().double().numpy()
    backward(backend, losses, np.random.default_rng([projection_seed, 20261002]))
    backend.optimizer.step()
    require(all(bool(torch.isfinite(p).all()) for p in parameters), "Nonfinite virtual update")
    deltas = [p.detach() - before for p, before in zip(parameters, before_parameters, strict=True)]
    actual_first_order = [
        float(sum((g.double() * d.double()).sum() for g, d in zip(gs, deltas, strict=True)))
        for gs in gradients
    ]
    shared_first_order = [
        float(sum((gs[i].double() * deltas[i].double()).sum() for i in shared)) for gs in gradients
    ]
    torch.set_rng_state(cpu_rng)
    if backend.device == "cuda":
        torch.cuda.set_rng_state_all(cuda_rng)
    with torch.no_grad():
        after_logits = backend.model(inputs, lengths)
        after = (
            torch.nn.functional.binary_cross_entropy_with_logits(
                after_logits, truth, reduction="none"
            )
            .reshape(-1, 3, 4)
            .mean((0, 2))
            .cpu()
            .double()
            .numpy()
        )
    return {
        "weighted_shared_gradient_norm": norms.tolist(),
        "shared_cosine": cosine.tolist(),
        "joint_raw_descent_dot_over_own_squared": raw_descent.tolist(),
        "unweighted_loss_before": before_loss.tolist(),
        "unweighted_loss_after": after.tolist(),
        "observed_loss_change_same_dropout": (after - before_loss).tolist(),
        "adamw_full_first_order_change": actual_first_order,
        "adamw_shared_first_order_change": shared_first_order,
        "parameter_update_norm": float(torch.sqrt(sum(d.double().square().sum() for d in deltas))),
    }


def run(args):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(args.plan.read_bytes())
    require(
        plan["variants"] == {k: {**v, "weights": list(v["weights"])} for k, v in VARIANTS.items()},
        "Diagnostic variants changed",
    )
    require(not args.output.exists(), "Preserve the existing diagnostic")
    require(
        sha(args.control / "freeze.json") == plan["control_freeze_sha256"], "Control freeze changed"
    )
    require(
        sha(args.control / "summary.json") == plan["control_summary_sha256"],
        "Control summary changed",
    )
    frozen = json.loads((args.control / "freeze.json").read_bytes())
    require(
        all(sha(repo / name) == digest for name, digest in frozen["source_sha256"].items()),
        "Control source changed",
    )
    summary = json.loads((args.control / "summary.json").read_bytes())
    require(
        summary["test_payloads_opened"] == 0 and len(summary["models"]) == 6,
        "Incomplete timely controls",
    )
    validation = validate_archive(args.archive, repo)
    normalizer = json.loads((args.control / "normalizer.json").read_bytes())
    require(
        sha(args.control / "normalizer.json") == frozen["normalizer_sha256"], "Normalizer changed"
    )
    records, checkpoints = [], {}
    for seed in SEEDS:
        backend = TimelyOptimizationBackend(seed, args.device, variant="original_sum")
        runtime = {
            "device": args.device,
            "torch": backend.version,
            "cuda_build": backend.torch.version.cuda,
            "gpu_name": backend.torch.cuda.get_device_name() if args.device == "cuda" else None,
        }
        require(runtime == frozen["runtime"], "Runtime changed")
        checkpoint = args.control / "leagueews" / f"seed-{seed}" / "checkpoint.pt"
        binding = sha(checkpoint)
        checkpoints[str(seed)] = binding
        require(
            summary["models"][f"leagueews/{seed}"]["checkpoint_sha256"] == binding,
            "Checkpoint changed",
        )
        saved = backend.torch.load(checkpoint, map_location="cpu", weights_only=True)
        require(
            saved["completed_units"] == 576
            and saved["freeze_sha256"] == plan["control_freeze_sha256"],
            "Incomplete checkpoint",
        )
        with zipfile.ZipFile(args.archive) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            for index, entry in enumerate(manifest["shards"][:48]):
                require(entry["partition"] == "train", "Diagnostic data must be training only")
                data = read_shard(archive, entry)
                x, mask, _ = sequences(data, normalizer)
                y = fitted_targets(data)
                selection = np.random.default_rng(plan["batch_seed"] + index).choice(
                    len(x), 256, False
                )
                for variant, specification in VARIANTS.items():
                    backend.variant = variant
                    backend.weights = specification["weights"]
                    backend.aggregation = specification["aggregation"]
                    values = local_step(
                        backend,
                        saved["backend"],
                        x[selection],
                        mask[selection],
                        y[selection],
                        projection_seed=plan["batch_seed"] + index,
                    )
                    records.append(
                        {"seed": seed, "shard": index, "variant": variant, "rows": 256, **values}
                    )
                if (index + 1) % 12 == 0:
                    print(f"Diagnosed seed {seed}: {index + 1}/48 training batches", flush=True)
        require(sha(checkpoint) == binding, "Source checkpoint changed")
        del backend
    aggregates = {}
    for seed in SEEDS:
        aggregates[str(seed)] = {}
        for variant in VARIANTS:
            selected = [v for v in records if v["seed"] == seed and v["variant"] == variant]
            record = {"batches": len(selected)}
            for field in (
                "adamw_full_first_order_change",
                "adamw_shared_first_order_change",
                "observed_loss_change_same_dropout",
            ):
                values = np.asarray([v[field] for v in selected])
                record[field] = {
                    "median": np.median(values, 0).tolist(),
                    "ascent_fraction": (values > 0).mean(0).tolist(),
                }
            cosine = np.asarray([v["shared_cosine"] for v in selected])
            raw = np.asarray([v["joint_raw_descent_dot_over_own_squared"] for v in selected])
            record["mean_shared_cosine"] = cosine.mean(0).tolist()
            record["negative_shared_cosine_fraction"] = (cosine < 0).mean(0).tolist()
            record["raw_sum_ascent_fraction"] = (raw < 0).mean(0).tolist()
            record["median_weighted_shared_gradient_norm"] = np.median(
                [v["weighted_shared_gradient_norm"] for v in selected], 0
            ).tolist()
            aggregates[str(seed)][variant] = record
    result = {
        "schema_version": "league-timely-optimization-diagnostic-v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "plan": plan,
        "plan_sha256": sha(args.plan),
        "runtime": runtime,
        "source_sha256": {name: sha(repo / name) for name in plan["sources"]},
        "checkpoint_sha256": checkpoints,
        "validation": validation,
        "by_seed": aggregates,
        "batches": records,
        "calibration_statistics_computed": False,
        "test_payloads_opened": 0,
        "new_fitted_models": 0,
        "source_checkpoints_modified": False,
        "limits": (
            "Local final-checkpoint probes use the original optimizer moments and identical "
            "dropout within each comparison. A virtual step includes AdamW preconditioning, "
            "stored momentum and weight decay; it does not identify training-trajectory effects "
            "or predict held-out warning performance. Batch rows are dependent and no IID "
            "uncertainty is claimed."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "by_seed": aggregates}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "control", "plan", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    with (args.control / "experiment.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        run(args)
