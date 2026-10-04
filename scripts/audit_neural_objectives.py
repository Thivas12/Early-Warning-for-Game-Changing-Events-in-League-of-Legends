"""Quantify target misalignment and real-frame opportunities on League development."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from league_ews.constants import EVENTS
from league_ews.coordination_experiment import sha, write_json
from league_ews.m1_alert_diagnostics import _chronological_halves
from scripts.league_compact_data import EXPECTED_ARCHIVE, load_partition, validate_archive
from scripts.timely_neural_targets import fitted_targets, next_event_delays


def aggregate(data, rows, indices):
    selected = np.concatenate([np.arange(*data["match_offsets"][i : i + 2]) for i in indices])
    gaps = np.concatenate(
        [np.diff(data["times_ms"][slice(*data["match_offsets"][i : i + 2])]) for i in indices]
    )
    result = {
        "matches": len(indices),
        "observations": len(selected),
        "gap_ms_quantiles": np.percentile(gaps, [0, 25, 50, 75, 100]).tolist(),
        "exact_60s_gap_fraction": float((gaps == 60000).mean()),
        "events": {},
    }
    aligned = fitted_targets(data)
    for e, event in enumerate(EVENTS):
        delay = next_event_delays(data, event)
        result["events"][event] = {}
        for c, h in ((2, 30), (3, 60)):
            total = opportunities = 0
            for i in indices:
                a, b = data["match_offsets"][i : i + 2]
                left, right = data[f"{event}_offsets"][i : i + 2]
                times = data["times_ms"][a:b]
                events = data[f"{event}_ms"][left:right]
                total += len(events)
                opportunities += int(
                    np.any(
                        (times[:, None] >= events - h * 1000)
                        & (times[:, None] <= events - h * 1000 // 3),
                        axis=0,
                    ).sum()
                )
            cumulative = int(data["targets"][selected, e * 4 + c].sum())
            useful = int(aligned[selected, e * 4 + c].sum())
            late = int(((delay[selected] > 0) & (delay[selected] < h * 1000 // 3)).sum())
            if cumulative != useful + late:
                raise ValueError("Positive target decomposition differs")
            result["events"][event][str(h)] = {
                "event_count": total,
                "frame_opportunities": opportunities,
                "frame_only_recall_ceiling": opportunities / total,
                "cumulative_positive_rows": cumulative,
                "useful_next_event_positive_rows": useful,
                "late_only_positive_rows": late,
                "late_fraction_of_cumulative_positives": late / cumulative,
            }
    return result


def main(archive, output):
    repo = Path(__file__).resolve().parents[1]
    validation = validate_archive(archive, repo)
    result = {
        "schema_version": "league-neural-objective-audit-v1",
        "archive_sha256": EXPECTED_ARCHIVE,
        "source_sha256": {
            str(p): sha(p) for p in (Path(__file__), repo / "scripts/timely_neural_targets.py")
        },
        "scope": "Descriptive audited development data; no fitted-model evaluation or test access",
        "test_payloads_opened": 0,
        "validation": validation,
        "partitions": {},
    }
    for part in ("train", "calibration"):
        data, rows = load_partition(archive, part)
        groups = (
            {"train": list(range(len(rows)))}
            if part == "train"
            else dict(zip(("early", "later"), _chronological_halves(rows), strict=True))
        )
        for name, idx in groups.items():
            result["partitions"][name] = {
                r: aggregate(
                    data, rows, [i for i in idx if r == "overall" or rows[i]["regional_route"] == r]
                )
                for r in ("overall", "europe", "americas")
            }
    write_json(output, result)
    for event, stats in result["partitions"]["train"]["overall"]["events"].items():
        print(event, stats)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.archive, args.output)
