"""Read-only replay of completed neural warnings against development timestamps.

This audit emits aggregate evidence only. It never trains a model, changes a
threshold, or reads a test partition. The reference replay deliberately builds
the alert list first and credits events separately from the production policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from league_ews.notebook_experiment import SEEDS
from scripts.analyse_neural_screen import calibration_routes, load_completed
from scripts.export_league_development import require
from scripts.league_compact_data import EXPECTED_ARCHIVE, EXPECTED_SPLIT, load_partition


def reference_counts(times, events, scores, threshold, horizon):
    """Return events, hits, timely hits, alerts, false alerts and opportunities."""
    require(horizon in (30, 60), "Invalid horizon")
    require(len(times) == len(scores), "Prediction length differs")
    require(
        threshold is None or (np.isfinite(threshold) and 0 < threshold <= 1),
        "Invalid threshold",
    )
    alerts = []
    if threshold is not None:
        for timestamp, score in zip(times, scores, strict=True):
            if float(score) >= threshold and (not alerts or timestamp - alerts[-1] >= 60_000):
                alerts.append(int(timestamp))
    credited = set()
    timely = 0
    for alert in alerts:
        candidates = [
            int(event)
            for event in events
            if event not in credited and alert < event <= alert + horizon * 1000
        ]
        if candidates:
            event = min(candidates)
            credited.add(event)
            timely += event - alert >= horizon * 1000 // 3
    opportunities = sum(
        bool(np.any((times >= event - horizon * 1000) & (times <= event - horizon * 1000 // 3)))
        for event in events
    )
    return [
        len(events),
        len(credited),
        timely,
        len(alerts),
        len(alerts) - len(credited),
        opportunities,
    ]


def check_report(counts, report):
    events, hits, timely, alerts, false, opportunities = counts.sum(axis=0)
    n = len(counts)
    expected = {
        "matches": n,
        "events": events,
        "matched_events": hits,
        "timely_matched_events": timely,
        "alerts": alerts,
        "timely_opportunities": opportunities,
        "event_recall": hits / events if events else None,
        "timely_event_recall": timely / events if events else None,
        "timely_precision": timely / alerts if alerts else None,
        "false_alerts_per_match": false / n,
        "late_alerts_per_match": (hits - timely) / n,
        "non_timely_alerts_per_match": (alerts - timely) / n,
    }
    for key, value in expected.items():
        require(
            report[key] is None
            if value is None
            else report[key] is not None and np.isclose(report[key], value, rtol=0, atol=1e-12),
            f"Replayed report differs: {key}",
        )


def run(studies: list[Path], archive: Path, output: Path) -> dict:
    calibration_routes(archive)  # Verify exact archive and development split hashes first.
    cal, rows = load_partition(archive, "calibration")
    early, later = _chronological_halves(rows)
    routes = np.asarray([row["regional_route"] for row in rows])
    identities = [row["match_id"] for row in rows]
    require(len(identities) == len(set(identities)) == 6000, "Calibration match identities differ")
    require(not set(early) & set(later) and len(early) == len(later) == 3000, "Halves overlap")
    studies_out = []
    for study in studies:
        summary = json.loads((study / "summary.json").read_bytes())
        families = tuple(sorted({key.split("/")[0] for key in summary["models"]}))
        _, reports, artifacts = load_completed(study, families, reference=cal)
        fits = {}
        for family in families:
            for seed in SEEDS:
                key = f"{family}/{seed}"
                score_path = study / family / f"seed-{seed}" / "calibration-scores.npz"
                with np.load(score_path, allow_pickle=False) as saved:
                    probabilities = saved["probabilities"]
                    policies = {}
                    for e, event in enumerate(EVENTS):
                        for horizon, column in ((30, e * 4 + 2), (60, e * 4 + 3)):
                            name = f"{event}_{horizon}"
                            report = reports[family][str(seed)]["warnings"][name]
                            threshold = report["threshold"]
                            counts = []
                            for i in range(len(rows)):
                                a, b = cal["match_offsets"][i : i + 2]
                                left, right = cal[f"{event}_offsets"][i : i + 2]
                                counts.append(
                                    reference_counts(
                                        cal["times_ms"][a:b],
                                        cal[f"{event}_ms"][left:right],
                                        probabilities[a:b, column],
                                        threshold,
                                        horizon,
                                    )
                                )
                            counts = np.asarray(counts, dtype=np.int64)
                            require(
                                np.array_equal(counts[later], saved[f"counts_{name}"]),
                                f"Replayed match counts differ: {key}/{name}",
                            )
                            check_report(counts[later], report["later"])
                            early_burdens = {}
                            late_budgets = []
                            for route in ("europe", "americas"):
                                early_idx = [i for i in early if routes[i] == route]
                                late_idx = [i for i in later if routes[i] == route]
                                early_counts = counts[early_idx]
                                burden = float((early_counts[:, 3] - early_counts[:, 2]).mean())
                                require(burden <= 1, "Selected threshold violates early budget")
                                early_burdens[route] = burden
                                check_report(counts[late_idx], report["by_route"][route])
                                late_counts = counts[late_idx]
                                late_budgets.append(
                                    float((late_counts[:, 3] - late_counts[:, 2]).mean()) <= 1
                                )
                            require(
                                all(late_budgets) == report["regional_budget_met"],
                                "Regional budget flag differs",
                            )
                            policies[name] = {
                                "threshold": threshold,
                                "early_false_plus_late_per_match": early_burdens,
                                "later_counts_and_regional_reports_match": True,
                                "later_regional_budgets_met": all(late_budgets),
                            }
                fits[key] = {"artifacts": artifacts[key], "policies": policies}
                print(f"Verified {study.name}: {key}, six policies on 6,000 matches", flush=True)
        studies_out.append({"summary_sha256": sha(study / "summary.json"), "fits": fits})
    result = {
        "schema_version": "league-neural-independent-replay-audit-v1",
        "archive_sha256": EXPECTED_ARCHIVE,
        "development_split_sha256": EXPECTED_SPLIT,
        "audit_source_sha256": sha(Path(__file__)),
        "ordered_calibration_match_ids_sha256": hashlib.sha256(
            json.dumps(identities, separators=(",", ":")).encode()
        ).hexdigest(),
        "calibration_matches": 6000,
        "evaluation_matches": 3000,
        "studies": studies_out,
        "thresholds_changed": False,
        "threshold_selection_repeated": False,
        "test_payloads_opened": 0,
    }
    write_json(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, action="append", required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.study, args.archive, args.output)
