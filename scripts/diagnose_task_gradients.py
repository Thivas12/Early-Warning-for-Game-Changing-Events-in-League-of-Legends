"""Read-only gradient and early-calibration diagnostics for the completed study.

Only aggregate diagnostic output is public. No optimizer step or model save occurs.
Calibration scores are decoded once, then only early match rows enter statistics.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.metrics import probabilistic_metrics
from league_ews.notebook_ews import NotebookEWSBackend, right_pad_sequences
from league_ews.notebook_experiment import SEEDS
from scripts.audit_neural_results import reference_counts
from scripts.export_league_development import require
from scripts.league_compact_data import load_partition, validate_archive
from scripts.run_compact_notebook import read_shard, sequences


def gradient_batches(archive_path, control, device):
    normalizer = json.loads((control / "normalizer.json").read_bytes())
    records, checkpoints = [], {}
    for seed in SEEDS:
        backend = NotebookEWSBackend(seed, device, family="leagueews")
        torch = backend.torch
        checkpoint = control / "leagueews" / f"seed-{seed}" / "checkpoint.pt"
        checkpoints[str(seed)] = sha(checkpoint)
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        require(state["completed_units"] == 576, "Incomplete control")
        backend.load_state_dict(state["backend"])
        backend.model.train()  # Preserve training dropout; diagnose, never step.
        shared = [p for n, p in backend.model.named_parameters() if not n.startswith("heads.")]
        with zipfile.ZipFile(archive_path) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            for index, entry in enumerate(manifest["shards"][:48]):
                require(entry["partition"] == "train", "Gradient data must be train only")
                x, mask, y = sequences(read_shard(archive, entry), normalizer)
                # One independently fixed 256-row batch per shard, common across seeds.
                selection = np.random.default_rng(20261002 + index).choice(len(x), 256, False)
                packed, lengths = right_pad_sequences(x[selection], mask[selection])
                logits = backend.model(
                    torch.from_numpy(packed).to(device), torch.from_numpy(lengths)
                )
                truth = torch.from_numpy(y[selection].astype(np.float32)).to(device)
                loss = (
                    torch.nn.functional.binary_cross_entropy_with_logits(
                        logits, truth, reduction="none"
                    )
                    .reshape(-1, 3, 4)
                    .mean((0, 2))
                )
                gradients = []
                for e, weight in enumerate((1.0, 2.0, 2.5)):
                    g = torch.autograd.grad(weight * loss[e], shared, retain_graph=e < 2)
                    gradients.append(torch.cat([p.flatten() for p in g]))
                matrix = torch.stack(gradients)
                gram = (matrix @ matrix.T).detach().cpu().double().numpy()
                norm = np.sqrt(np.diag(gram))
                cosine = gram / np.outer(norm, norm)
                records.append(
                    {
                        "seed": seed,
                        "shard": index,
                        "rows": len(selection),
                        "weighted_gradient_norm": norm.tolist(),
                        "cosine": cosine.tolist(),
                        "baron_dot_other_over_own_squared": float(gram[0, 1:].sum() / gram[0, 0]),
                        "loss_unweighted": loss.detach().cpu().tolist(),
                    }
                )
            print(f"Gradient diagnostic: seed {seed}, 48 training batches", flush=True)
        require(sha(checkpoint) == checkpoints[str(seed)], "Control checkpoint changed")
    summaries = {}
    for seed in SEEDS:
        subset = [r for r in records if r["seed"] == seed]
        cosine = np.asarray([r["cosine"] for r in subset])
        norms = np.asarray([r["weighted_gradient_norm"] for r in subset])
        interference = np.asarray([r["baron_dot_other_over_own_squared"] for r in subset])
        summaries[str(seed)] = {
            "batches": len(subset),
            "mean_cosine": cosine.mean(0).tolist(),
            "negative_cosine_fraction": (cosine < 0).mean(0).tolist(),
            "median_weighted_gradient_norm": np.median(norms, axis=0).tolist(),
            "baron_other_opposes_fraction": float((interference < 0).mean()),
            "baron_joint_raw_gradient_ascent_fraction": float((interference < -1).mean()),
            "baron_interference_ratio_median": float(np.median(interference)),
        }
    return {"by_seed": summaries, "batches": records, "checkpoint_sha256": checkpoints}


def early_diagnostics(archive, control, independent):
    cal, rows = load_partition(archive, "calibration")
    early, later = _chronological_halves(rows)
    require(len(early) == len(later) == 3000 and not set(early) & set(later), "Bad split")
    indices = np.concatenate([np.arange(*cal["match_offsets"][i : i + 2]) for i in early])
    route = np.concatenate(
        [
            np.repeat(rows[i]["regional_route"], np.diff(cal["match_offsets"][i : i + 2])[0])
            for i in early
        ]
    )
    times = cal["times_ms"][indices]
    strata = {
        "overall": np.ones(len(indices), dtype=bool),
        "europe": route == "europe",
        "americas": route == "americas",
        "before_20m": times < 1200000,
        "20_to_30m": (times >= 1200000) & (times < 1800000),
        "after_30m": times >= 1800000,
    }
    result, bindings = {}, {}
    for seed in SEEDS:
        result[str(seed)] = {}
        for family in ("joint", "independent"):
            result[str(seed)][family] = {}
            for e, event in enumerate(EVENTS):
                folder = control / "leagueews" if family == "joint" else independent / event
                folder = folder / f"seed-{seed}"
                report = json.loads((folder / "report.json").read_bytes())
                scores_path = folder / "calibration-scores.npz"
                require(sha(scores_path) == report["scores_sha256"], "Scores changed")
                bindings[f"{family}/{event}/{seed}"] = report["scores_sha256"]
                columns = slice(4 * e, 4 * e + 4) if family == "joint" else slice(0, 4)
                with np.load(scores_path, allow_pickle=False) as saved:
                    probabilities = saved["probabilities"][:, columns]
                early_scores = probabilities[indices]
                labels = cal["targets"][indices, 4 * e : 4 * e + 4]
                per_horizon = {}
                for horizon, col, lower in ((30, 2, 0), (60, 3, 1)):
                    # Labels at the lower boundary are cumulative; exact boundary
                    # ties are counted in 'late' here. Event replay uses the exact
                    # registered inclusive timely boundaries independently below.
                    lead_masks = {
                        "at_most_lower_bound": labels[:, lower] == 1,
                        "above_lower_through_horizon": (labels[:, col] == 1)
                        & (labels[:, lower] == 0),
                        "no_event_within_horizon": labels[:, col] == 0,
                    }
                    row_metrics = {}
                    for name, selection in strata.items():
                        row_metrics[name] = {
                            "rows": int(selection.sum()),
                            **probabilistic_metrics(
                                labels[selection, col], early_scores[selection, col]
                            ),
                            "score_by_next_event_interval": {
                                lead: {
                                    "rows": int((selection & mask).sum()),
                                    "mean_score": float(early_scores[selection & mask, col].mean())
                                    if (selection & mask).any()
                                    else None,
                                }
                                for lead, mask in lead_masks.items()
                            },
                        }
                    threshold = report["warnings"][f"{event}_{horizon}"]["threshold"]
                    counts = []
                    for i in early:
                        a, b = cal["match_offsets"][i : i + 2]
                        left, right = cal[f"{event}_offsets"][i : i + 2]
                        counts.append(
                            reference_counts(
                                cal["times_ms"][a:b],
                                cal[f"{event}_ms"][left:right],
                                probabilities[a:b, col],
                                threshold,
                                horizon,
                            )
                        )
                    counts = np.asarray(counts)
                    warning = {}
                    for region in ("overall", "europe", "americas"):
                        selected = np.array(
                            [
                                region == "overall" or rows[i]["regional_route"] == region
                                for i in early
                            ]
                        )
                        totals = counts[selected].sum(0)
                        warning[region] = {
                            "matches": int(selected.sum()),
                            "counts": totals.tolist(),
                            "timely_recall": float(totals[2] / totals[0]),
                            "false_plus_late_per_match": float(
                                (totals[3] - totals[2]) / selected.sum()
                            ),
                        }
                    per_horizon[str(horizon)] = {
                        "row_diagnostics": row_metrics,
                        "early_selected_threshold": threshold,
                        "early_warning": warning,
                    }
                result[str(seed)][family][event] = per_horizon
    return {"matches": 3000, "rows": len(indices), "by_seed": result, "scores_sha256": bindings}


def run(args):
    repo = Path(__file__).resolve().parents[1]
    validation = validate_archive(args.archive, repo)
    backend = NotebookEWSBackend(SEEDS[0], args.device, family="leagueews")
    runtime = {
        "torch": backend.version,
        "cuda_build": backend.torch.version.cuda,
        "device": args.device,
        "gpu": backend.torch.cuda.get_device_name() if args.device == "cuda" else None,
    }
    if args.device == "cuda":
        require(
            float((backend.torch.ones(4, device="cuda") ** 2).sum()) == 4, "CUDA calculation failed"
        )
    del backend
    result = {
        "schema_version": "league-transfer-diagnostics-v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": runtime,
        "source_sha256": sha(Path(__file__)),
        "validation": validation,
        "design": (
            "One fixed 256-row batch from every training shard, final joint checkpoint, "
            "training dropout, no optimizer updates. Same sampled rows for all seeds. "
            "Early calibration only for score and warning statistics."
        ),
        "limits": (
            "Descriptive final-checkpoint gradients, not training trajectories or "
            "causal identification. "
            "Raw gradients ignore Adam preconditioning and curvature. "
            "Row metrics have no IID intervals. "
            "No later calibration informs this diagnosis."
        ),
        "gradients": gradient_batches(args.archive, args.control, args.device),
        "early_calibration": early_diagnostics(args.archive, args.control, args.independent),
        "test_payloads_opened": 0,
    }
    write_json(args.output, result)
    print(
        json.dumps(
            {"output": str(args.output), "gradients": result["gradients"]["by_seed"]}, indent=2
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "control", "independent", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    run(parser.parse_args())
