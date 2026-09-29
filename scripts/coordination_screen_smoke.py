"""Executable synthetic controls. These are not League model-performance results."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from league_ews.coordination_experiment import evaluate_scores, fit_predict
from league_ews.coordination_features import VARIANT_WIDTHS, coordination_matrix
from league_ews.timeline import NormalizedTimeline


def timeline(signal: bool = False, match_id: str = "EUW1_1") -> NormalizedTimeline:
    """Identical snapshot sets; only identity-linked past displacements differ."""
    frames = []
    for time in (480_000, 540_000, 600_000, 660_000):
        participants = []
        for index in range(10):
            location = (index + 1) % 5 if signal and time == 540_000 and index < 5 else index % 5
            participants.append(
                {
                    "participant_id": index + 1,
                    "team_id": 100 if index < 5 else 200,
                    "total_gold": 2000,
                    "xp": 2000,
                    "level": 5,
                    "lane_minions": 30,
                    "jungle_minions": 0,
                    "position": {"x": 4000 + location * 700, "y": 4000 + (index // 5) * 4000},
                }
            )
        frames.append({"timestamp_ms": time, "participants": participants, "events": []})
    return NormalizedTimeline.model_validate(
        {
            "match_id": match_id,
            "platform_id": "EUW1",
            "game_version": "16.12.1",
            "game_creation_ms": 1,
            "observations": frames,
        }
    )


def synthetic_arrays(matches: int = 80) -> dict:
    negative, positive = (coordination_matrix(timeline(flag))[2] for flag in (False, True))
    labels = np.arange(matches) % 2
    return {
        "x": np.stack([positive if y else negative for y in labels]),
        "y": labels.astype(np.int8),
        "times": [(600_000,)] * matches,
        "events": [(630_000,) if y else () for y in labels],
        "offsets": np.arange(matches + 1, dtype=np.int64),
    }


def main() -> None:
    train, calibration = synthetic_arrays(80), synthetic_arrays(40)
    development = np.arange(80) >= 60
    early, later = list(range(20)), list(range(20, 40))
    results = {}
    with threadpool_limits(limits=1):
        for variant in VARIANT_WIDTHS:
            _, scores, _ = fit_predict(
                train,
                calibration,
                development,
                variant,
                leaf_grid=(3, 7),
                iterations=25,
                min_leaf=5,
            )
            report, _ = evaluate_scores(calibration, scores, early, later)
            results[variant] = {
                "row_metrics": report["evaluation_row_metrics"],
                "warning_metrics": report["evaluation"],
            }
        train["x"][:] = train["x"][0]
        calibration["x"][:] = calibration["x"][0]
        _, scores, _ = fit_predict(
            train,
            calibration,
            development,
            "coordination",
            leaf_grid=(3, 7),
            iterations=25,
            min_leaf=5,
        )
        null, _ = evaluate_scores(calibration, scores, early, later)
    result = {
        "schema_version": "league-ews-coordination-synthetic-controls-v1",
        "synthetic": True,
        "new_private_model_results": False,
        "construction": (
            "Snapshot/history aggregates identical; synthetic target depends on "
            "identity-linked past movement; one forecast per match"
        ),
        "fit_matches": 60,
        "selection_matches": 20,
        "threshold_tuning_matches": 20,
        "evaluation_matches": 20,
        "positive_control": results,
        "signal_removed_control": null["evaluation_row_metrics"],
        "interpretation": (
            "Checks that the pipeline can detect an injected signal and loses that "
            "advantage when removed; says nothing about effect size in real League matches"
        ),
    }
    path = (
        Path(__file__).resolve().parents[1]
        / "reports/coordination-screen-synthetic-controls-2026-09-29.json"
    )
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
