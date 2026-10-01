"""Audit completed neural fits and bootstrap paired whole League matches.

Every draw uses the same matches across events, models and seeds. Seed averages
describe fixed fitted models; they do not turn three fits into three populations.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.notebook_ews import FAMILIES
from league_ews.notebook_experiment import SEEDS
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, EXPECTED_SPLIT

BOOTSTRAP_SEED = 20261001
DRAWS = 2000
METRICS = ("timely_recall", "false_plus_late_per_match", "false_per_match", "late_per_match")


def resample_weights(routes: np.ndarray, draws: int = DRAWS) -> np.ndarray:
    """Stratify whole-match sampling by route; share draws across every contrast."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    groups = [np.flatnonzero(routes == route) for route in sorted(set(routes))]
    result = np.zeros((draws, len(routes)), dtype=np.float64)
    for b in range(draws):
        sampled = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups])
        result[b] = np.bincount(sampled, minlength=len(routes))
    return result


def metrics(counts: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Counts: seed,event,match,6; result: draw,seed,event,metric."""
    sums = np.einsum("bn,senk->bsek", weights, counts, optimize=True)
    size = weights.sum(axis=1)[:, None, None]
    return np.stack(
        (
            sums[..., 2] / sums[..., 0],
            (sums[..., 3] - sums[..., 2]) / size,
            sums[..., 4] / size,
            (sums[..., 1] - sums[..., 2]) / size,
        ),
        axis=-1,
    )


def estimate(point: np.ndarray, draws: np.ndarray) -> dict:
    return {
        metric: {
            "estimate": float(point[i]),
            "conditional_95_interval": np.percentile(draws[:, i], [2.5, 97.5]).tolist(),
        }
        for i, metric in enumerate(METRICS)
    }


def summarise(point: np.ndarray, draws: np.ndarray) -> dict:
    """Point is seed,event,metric. Macro is an unweighted event average."""
    result = {}
    for event, p, b in [
        *((event, point[:, i], draws[:, :, i]) for i, event in enumerate(EVENTS)),
        ("macro", point.mean(axis=1), draws.mean(axis=2)),
    ]:
        result[event] = {
            "by_seed": {str(seed): estimate(p[i], b[:, i]) for i, seed in enumerate(SEEDS)},
            "mean_over_fixed_seeds": estimate(p.mean(axis=0), b.mean(axis=1)),
            "seed_variability": {
                metric: {
                    "min": float(p[:, i].min()),
                    "max": float(p[:, i].max()),
                    "sample_sd": float(p[:, i].std(ddof=1)),
                }
                for i, metric in enumerate(METRICS)
            },
        }
    return result


def load_completed(study: Path, families: tuple[str, ...] = FAMILIES) -> tuple[dict, dict, dict]:
    """Refuse partial studies and verify provenance before reading predictions."""
    summary = json.loads((study / "summary.json").read_bytes())
    binding = sha(study / "freeze.json")
    require(summary["freeze_sha256"] == binding, "Summary freeze mismatch")
    counts, reports, artifacts = {}, {}, {}
    reference_offsets, reference_targets = None, None
    for family in families:
        per_seed = {h: [] for h in (30, 60)}
        reports[family] = {}
        for seed in SEEDS:
            folder = study / family / f"seed-{seed}"
            report = json.loads((folder / "report.json").read_bytes())
            progress = json.loads((folder / "progress.json").read_bytes())
            require(progress["completed_units"] == 576, "Training incomplete")
            require(
                report["family"] == progress["family"] == family
                and report["seed"] == progress["seed"] == seed,
                "Fit identity mismatch",
            )
            require(report["freeze_sha256"] == binding, "Report freeze mismatch")
            require(
                report["checkpoint_sha256"] == sha(folder / "checkpoint.pt"), "Checkpoint changed"
            )
            score_file = folder / "calibration-scores.npz"
            require(report["scores_sha256"] == sha(score_file), "Scores changed")
            require(summary["models"][f"{family}/{seed}"] == report, "Summary report mismatch")
            with np.load(score_file, allow_pickle=False) as z:
                if reference_offsets is None:
                    reference_offsets, reference_targets = z["match_offsets"], z["targets"]
                require(np.array_equal(reference_offsets, z["match_offsets"]), "Offsets differ")
                require(np.array_equal(reference_targets, z["targets"]), "Targets differ")
                require(np.isfinite(z["probabilities"]).all(), "Nonfinite predictions")
                require(
                    ((z["probabilities"] >= 0) & (z["probabilities"] <= 1)).all(),
                    "Invalid probabilities",
                )
                for h in (30, 60):
                    c = np.stack([z[f"counts_{event}_{h}"] for event in EVENTS])
                    require(c.shape == (3, 3000, 6), "Wrong match count")
                    require(
                        np.all(c >= 0)
                        and np.all(c[..., 2] <= c[..., 1])
                        and np.all(c[..., 1] <= c[..., 0])
                        and np.all(c[..., 3] == c[..., 1] + c[..., 4]),
                        "Invalid event/alert count conservation",
                    )
                    for i, event in enumerate(EVENTS):
                        r = report["warnings"][f"{event}_{h}"]["later"]
                        sums = c[i].sum(axis=0)
                        require(
                            int(sums[0]) == r["events"]
                            and int(sums[2]) == r["timely_matched_events"]
                            and int(sums[3]) == r["alerts"],
                            "Counts/report mismatch",
                        )
                    per_seed[h].append(c)
            reports[family][str(seed)] = report
            artifacts[f"{family}/{seed}"] = {
                "report_sha256": sha(folder / "report.json"),
                "checkpoint_sha256": report["checkpoint_sha256"],
                "scores_sha256": report["scores_sha256"],
            }
        counts[family] = {h: np.stack(v) for h, v in per_seed.items()}
    reference = counts[families[0]][30][0, :, :, 0]
    for family in families:
        for h in (30, 60):
            require(np.all(counts[family][h][..., 0] == reference), "Event denominators differ")
    return counts, reports, artifacts


def analyse(counts: dict, routes: np.ndarray, pairs: list[tuple[str, str]]) -> dict:
    result = {}
    for region in ("overall", "europe", "americas"):
        idx = np.arange(len(routes)) if region == "overall" else np.flatnonzero(routes == region)
        weights = resample_weights(routes[idx])
        result[region] = {}
        for h in (30, 60):
            points, boots = {}, {}
            for family, by_horizon in counts.items():
                c = by_horizon[h][:, :, idx]
                points[family] = metrics(c, np.ones((1, len(idx))))[0]
                boots[family] = metrics(c, weights)
            result[region][str(h)] = {
                "families": {f: summarise(points[f], boots[f]) for f in counts},
                "contrasts": {
                    f"{a}_minus_{b}": summarise(points[a] - points[b], boots[a] - boots[b])
                    for a, b in pairs
                },
            }
    return result


def calibration_routes(archive: Path) -> np.ndarray:
    require(sha(archive) == EXPECTED_ARCHIVE, "Development archive changed")
    with zipfile.ZipFile(archive) as z:
        raw = z.read("development-split.json")
    import hashlib

    require(hashlib.sha256(raw).hexdigest() == EXPECTED_SPLIT, "Split changed")
    rows = json.loads(raw)["partitions"]["calibration"]
    _, later = _chronological_halves(rows)
    return np.array([rows[i]["regional_route"] for i in later])


def run(study: Path, archive: Path, output: Path) -> dict:
    counts, reports, artifacts = load_completed(study)
    routes = calibration_routes(archive)
    pairs = [
        ("leagueews", "gru"),
        ("leagueews", "tcn"),
        ("leagueews", "snapshot"),
        ("gru", "snapshot"),
        ("tcn", "snapshot"),
        ("tcn", "gru"),
    ]
    analysis = analyse(counts, routes, pairs)
    original = json.loads((study / "summary.json").read_bytes())
    primary = analysis["overall"]["30"]["contrasts"]["leagueews_minus_gru"]["macro"]
    calculated = [primary["by_seed"][str(s)]["timely_recall"]["estimate"] for s in SEEDS]
    require(
        np.allclose(
            calculated, original["macro_30s_timely_recall_differences_by_seed"], rtol=0, atol=1e-12
        ),
        "Primary result changed",
    )
    log_times = {}
    log_path = study / "worker.log"
    if log_path.exists():
        for family, seed, epoch, shard, seconds in re.findall(
            r"(leagueews|gru|tcn|snapshot) seed (\d+): epoch (\d+)/12, "
            r"shard (\d+)/48, loss [^,]+, ([\d.]+)s",
            log_path.read_text(),
        ):
            log_times.setdefault(f"{family}/{seed}", {})[f"{epoch}/{shard}"] = float(seconds)
    result = {
        "schema_version": "league-neural-paired-analysis-v1",
        "study_freeze_sha256": sha(study / "freeze.json"),
        "study_summary_sha256": sha(study / "summary.json"),
        "analysis_source_sha256": sha(Path(__file__)),
        "archive_sha256": EXPECTED_ARCHIVE,
        "artifacts": artifacts,
        "training_log_seconds": {
            k: {"observed_shards": len(v), "sum_rounded_shard_seconds": sum(v.values())}
            for k, v in log_times.items()
        },
        "training_time_scope": (
            "Rounded logged shard durations; excludes checkpoint writes and calibration; "
            "a canary shard may be absent from the background log"
        ),
        "matched_evaluation_matches": len(routes),
        "bootstrap": {
            "draws": DRAWS,
            "seed": BOOTSTRAP_SEED,
            "unit": "whole-match",
            "strata": "route",
            "paired_across": "all families, seeds and events",
            "interval_scope": (
                "conditional on fitted models and early-half-selected thresholds; no refitting"
            ),
            "seed_mean": (
                "average performance of three fixed fits, "
                "not a prediction ensemble or independent populations"
            ),
            "secondary_intervals": "unadjusted; exploratory",
        },
        "registered_primary": {
            "contrast": "leagueews_minus_gru",
            "endpoint": "macro timely recall at 10-30 seconds",
            "differences_by_seed": calculated,
            "both_models_regional_budgets_by_seed": original[
                "both_models_primary_regional_budgets_met_by_seed"
            ],
            "screen_passed": original["consistent_positive_exploratory_screen"],
        },
        "analysis": analysis,
        "reports": reports,
        "test_payloads_opened": 0,
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "neural-analysis.json", result)
    with (output / "neural-by-seed.csv").open("w", newline="") as stream:
        fields = [
            "family",
            "seed",
            "horizon",
            "region",
            "event",
            "threshold",
            "timely_recall",
            "false_plus_late_per_match",
            "false_per_match",
            "late_per_match",
            "regional_budget_met",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for family, by_seed in reports.items():
            for seed, report in by_seed.items():
                for h in (30, 60):
                    for event in EVENTS:
                        w = report["warnings"][f"{event}_{h}"]
                        for region, m in {"overall": w["later"], **w["by_route"]}.items():
                            writer.writerow(
                                dict(
                                    zip(
                                        fields,
                                        [
                                            family,
                                            seed,
                                            h,
                                            region,
                                            event,
                                            w["threshold"],
                                            m["timely_event_recall"],
                                            m["non_timely_alerts_per_match"],
                                            m["false_alerts_per_match"],
                                            m["late_alerts_per_match"],
                                            w["regional_budget_met"]
                                            if region == "overall"
                                            else m["non_timely_alerts_per_match"] <= 1,
                                        ],
                                        strict=True,
                                    )
                                )
                            )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.study, args.archive, args.output)
    print(json.dumps(result["registered_primary"], indent=2))
