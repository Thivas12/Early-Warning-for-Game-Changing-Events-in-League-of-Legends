"""Reproduce secondary calculations and explicitly synthetic methodological probes.

No private matches, fitted models, or sealed test payloads are opened. The
calibration values are existing public transcriptions, not newly scored models.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from league_ews.alert_policy import MatchRisk, evaluate_alerts
from league_ews.graph import ObjectiveRules, build_interaction_graph
from league_ews.labels import _combat_episode_starts
from league_ews.m3_followup import confirmed_followup_masks
from league_ews.tabular_baseline import FEATURES, _rows
from league_ews.timeline import (
    NormalizedTimeline,
    Observation,
    ParticipantState,
    Position,
    TimelineEvent,
)

ROOT = Path(__file__).resolve().parents[1]


def recurrence_probe() -> dict[str, object]:
    """Change only a known past objective kill, holding observed states fixed."""
    participants = tuple(
        ParticipantState(
            participant_id=i,
            team_id=100 if i <= 5 else 200,
            total_gold=2000,
            xp=1800,
            level=5,
            lane_minions=30,
            jungle_minions=5,
            position=Position(x=1000 * i, y=1000 * i),
        )
        for i in range(1, 11)
    )
    kill = TimelineEvent(
        timestamp_ms=540_000,
        event_type="ELITE_MONSTER_KILL",
        monster_type="DRAGON",
        killer_team_id=100,
    )
    without = Observation(timestamp_ms=600_000, participants=participants, events=())
    with_kill = without.model_copy(update={"events": (kill,)})
    rules = ObjectiveRules(Position(x=5000, y=10000), Position(x=10000, y=5000), 1200, 300)
    graphs = [build_interaction_graph(obs, objective_rules=rules) for obs in (without, with_kill)]
    vectors = []
    for obs in (without, with_kill):
        timeline = NormalizedTimeline(
            match_id="SYNTHETIC_RECURRENCE",
            platform_id="EUW1",
            game_version="16.16.1",
            game_creation_ms=1,
            observations=(obs,),
        )
        payload = {
            "schema_version": "league-ews-processed-match-v1",
            "timeline": timeline.model_dump(),
            "labels": [{"timestamp_ms": 600_000, "y_dragon_60": 0}],
        }
        vectors.append(next(_rows(payload, timeline.match_id, "y_dragon_60"))[0])
    changes = []
    for name, left, right in zip(FEATURES, vectors[0], vectors[1], strict=True):
        if not np.isclose(left, right, equal_nan=True):
            changes.append(
                {
                    "feature": name,
                    "without_past_kill": None if np.isnan(left) else left,
                    "with_past_kill": None if np.isnan(right) else right,
                }
            )
    return {
        "synthetic": True,
        "graph_node_features_equal": bool(
            np.array_equal(graphs[0].node_features, graphs[1].node_features)
        ),
        "graph_edges_equal": bool(np.array_equal(graphs[0].edge_index, graphs[1].edge_index)),
        "graph_relations_equal": graphs[0].edge_types == graphs[1].edge_types,
        "b3_changed_features": changes,
        "interpretation": "explicit objective recurrence is omitted from M1 graph construction",
    }


def partial_bin_probe() -> dict[str, object]:
    """Show discretization error under independent within-bin censoring."""
    n = 200_000
    rng = np.random.default_rng(20260929)
    rate = -np.log(0.9) / 10
    event_time = rng.exponential(1 / rate, size=n)
    followup = rng.choice([5.0, 10.0], size=n)
    event_observed = event_time <= followup
    included_by_binary_mask = event_observed | (followup == 10)
    mask_estimate = event_observed.sum() / included_by_binary_mask.sum()
    exposure_rate = event_observed.sum() / np.minimum(event_time, followup).sum()
    p5 = -np.expm1(-rate * 5)
    analytic_mask = (0.5 * p5 + 0.5 * 0.1) / (0.5 * p5 + 0.5)
    return {
        "synthetic": True,
        "n": n,
        "seed": 20260929,
        "true_risk_10_seconds": 0.1,
        "analytic_binary_mask_optimum": float(analytic_mask),
        "simulated_binary_mask_optimum": float(mask_estimate),
        "constant_rate_likelihood_risk": float(-np.expm1(-exposure_rate * 10)),
        "assumptions": (
            "Exponential event time; independent equal mixture of 5s/10s follow-up; 10s bin"
        ),
        "interpretation": (
            "Binary masking is a discretized approximation, not an exact continuous-time likelihood"
        ),
    }


def main() -> None:
    source = ROOT / "reports/m1-graph-ablation-calibration-2026-09-28.json"
    data = json.loads(source.read_text())
    m1, b3 = data["m1"]["mean"], data["b3"]
    variants = data["variants"]
    retained = (variants["no-interaction-edges"]["mean"] - b3) / (m1 - b3)
    opportunity = {
        "baron": [1080, 2149, 3262, 6494],
        "dragon": [3772, 7501, 11324, 22713],
        "teamfight": [6508, 13501, 20077, 39998],
    }
    # Predict at 180s, with verified complete match termination at 200s.
    times = np.array([180_000, 200_000], dtype=np.int64)
    targets = np.zeros((2, 3, 6), dtype=np.float32)
    _, known = confirmed_followup_masks(times, targets, game_duration_ms=200_000)
    policy_fixture = MatchRisk(
        (300_000, 360_000, 420_000), (330_000, 390_000, 450_000), (0.9, 0.9, 0.9)
    )
    kills = [
        TimelineEvent(
            timestamp_ms=300_000 + i * 9000,
            event_type="CHAMPION_KILL",
            position=Position(x=1000 if i % 2 else 14000, y=1000 if i % 2 else 14000),
        )
        for i in range(11)
    ]
    event_rate, end_rate, horizon = 0.01, 0.02, 60
    report = {
        "schema_version": "league-ews-research-findings-v1",
        "evidence_date": "2026-09-29",
        "new_private_model_results": False,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_note": data["source"],
        "existing_calibration_secondary_analysis": {
            "m1_minus_b3_macro_ap": m1 - b3,
            "m1_relative_ap_gain_percent": 100 * (m1 - b3) / b3,
            "ap_gap_remaining_without_edges_percent": 100 * retained,
            "objective_removal_gain": variants["no-objective-nodes"]["mean"] - m1,
            "combined_spatial_removal_drop": m1 - variants["no-positions-or-proximity"]["mean"],
            "dragon_f1_delta_from_rounded_report": 0.58807 - 0.71183,
            "dragon_false_alert_increase_percent_from_rounded_report": 100 * (1.94413 / 1.552 - 1),
            "opportunity_counts_10_20_30_60": opportunity,
            "opportunity_fraction_relative_to_60s": {
                k: [x / v[-1] for x in v] for k, v in opportunity.items()
            },
            "warning": (
                "Descriptive arithmetic on calibration transcriptions, "
                "not causal attribution or fresh uncertainty estimates"
            ),
        },
        "synthetic_probes": {
            "objective_recurrence": recurrence_probe(),
            "terminal_outcome": {
                "synthetic": True,
                "assumption": (
                    "Prediction at 180s; complete match and event ascertainment "
                    "through verified termination at 200s; no future event"
                ),
                "correct_actual_match_labels_at_10_20_30_60": [0, 0, 0, 0],
                "boundary_mask_marks_known": known[0, 0].tolist(),
                "interpretation": (
                    "Boundary coverage does not identify which labels are genuinely unknown"
                ),
            },
            "partial_bin_likelihood": partial_bin_probe(),
            "competing_terminal_event": {
                "synthetic": True,
                "event_rate_per_second": event_rate,
                "match_end_rate_per_second": end_rate,
                "horizon_seconds": horizon,
                "risk_ignoring_terminal_competitor": float(-np.expm1(-event_rate * horizon)),
                "actual_cumulative_incidence": float(
                    event_rate
                    / (event_rate + end_rate)
                    * -np.expm1(-(event_rate + end_rate) * horizon)
                ),
            },
            "cooldown_boundary": {
                "synthetic": True,
                "current_strictly_more_than_60s": evaluate_alerts([policy_fixture], 0.5),
                "at_least_60s_manual_oracle": {
                    "alerts": 3,
                    "matched_events": 3,
                    "event_recall": 1.0,
                    "false_alerts": 0,
                },
                "interpretation": (
                    "Exactly 60s spacing is suppressed by current <= comparison; "
                    "this is a convention sensitivity, not a measured LoL effect"
                ),
            },
            "combat_episode": {
                "synthetic": True,
                "kill_count": len(kills),
                "span_seconds": 90,
                "alternating_distant_positions": True,
                "onsets_ms": list(_combat_episode_starts(kills, min_kills=3, max_gap_seconds=10)),
                "interpretation": (
                    "Temporal chaining does not enforce spatially coherent fights "
                    "or a maximum total duration"
                ),
            },
        },
    }
    output = ROOT / "reports/research-findings-2026-09-29.json"
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
