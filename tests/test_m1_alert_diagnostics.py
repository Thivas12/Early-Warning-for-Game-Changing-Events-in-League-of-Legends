"""Alert opportunity is measured from real frames with frozen alert matching."""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from league_ews.alert_policy import MatchRisk, evaluate_alerts
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.constants import EVENTS
from league_ews.m1_alert_diagnostics import (
    _chronological_halves,
    audit_m1_alert_opportunity,
    diagnose_alerts,
)
from league_ews.m1_training_plan import SEEDS


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path, value):
    path.write_text(json.dumps(value))


def _synthetic_audit(root):
    processed = root / "processed"
    calibration = root / "calibration"
    policy_root = root / "policies"
    for path in (processed, calibration, policy_root):
        path.mkdir()
    processing = processed / "processing-manifest.json"
    processing.write_text("synthetic manifest")
    entries = [
        {
            "match_id": f"EUW1_{index}" if index < 3000 else f"NA1_{index}",
            "game_version_patch": "16.16",
            "regional_route": "europe" if index < 3000 else "americas",
            "game_creation_ms": index % 3000,
        }
        for index in range(6000)
    ]
    split_file = root / "split.json"
    _json(
        split_file,
        {
            "schema_version": "league-ews-final-split-v1",
            "processing_manifest_sha256": _sha(processing),
            "summary": {
                "counts": {"train": 24000, "calibration": 6000, "test": 6000},
                "patches": {"calibration": ["16.16"]},
            },
            "partitions": {"calibration": entries},
        },
    )
    offsets = np.arange(6001, dtype=np.int64)
    truth = np.ones((6000, len(LABELS)), dtype=np.int8)
    probabilities = np.full(truth.shape, 0.9, dtype=np.float32)
    cal_seeds = []
    policy_seeds = []
    single = MatchRisk((0,), (5000,), (0.9,))
    metrics = evaluate_alerts([single] * 6000, 0.5)
    for seed in SEEDS:
        seed_root = calibration / f"seed-{seed}"
        seed_root.mkdir()
        scores = seed_root / "calibration-scores.npz"
        np.savez_compressed(
            scores, probabilities=probabilities, targets=truth, match_offsets=offsets
        )
        cal_seeds.append({"seed": seed, "scores_sha256": _sha(scores)})
    cal_summary = calibration / "ten-seed-summary.json"
    _json(
        cal_summary,
        {
            "schema_version": "league-ews-m1-ten-seed-calibration-v1",
            "split_sha256": _sha(split_file),
            "seed_count": 10,
            "calibration_matches": 6000,
            "identifiers_in_summary": False,
            "test_matches_unread": 6000,
            "selected_seed": None,
            "seed_results": cal_seeds,
        },
    )
    for row in cal_seeds:
        seed = row["seed"]
        policy_path = policy_root / f"policy.seed-{seed}.json"
        _json(
            policy_path,
            {
                "schema_version": "league-ews-m1-alert-policy-v1",
                "seed": seed,
                "split_sha256": _sha(split_file),
                "processing_manifest_sha256": _sha(processing),
                "ten_seed_summary_sha256": _sha(cal_summary),
                "scores_sha256": row["scores_sha256"],
                "events": {
                    event: {"threshold": 0.5, "calibration_event_metrics": metrics}
                    for event in EVENTS
                },
                "selected_seed": None,
                "test_matches_unread": 6000,
                "identifiers_in_report": False,
            },
        )
        policy_seeds.append({"seed": seed, "policy_sha256": _sha(policy_path)})
    _json(
        policy_root / "ten-seed-alert-summary.json",
        {
            "schema_version": "league-ews-m1-ten-seed-alert-summary-v1",
            "split_sha256": _sha(split_file),
            "ten_seed_calibration_sha256": _sha(cal_summary),
            "calibration_matches": 6000,
            "seed_count": 10,
            "identifiers_in_summary": False,
            "selected_seed": None,
            "test_matches_unread": 6000,
            "seed_reports": policy_seeds,
            "events": {
                event: {
                    "events": 6000,
                    "thresholds": [{"seed": seed, "threshold": 0.5} for seed in SEEDS],
                }
                for event in EVENTS
            },
        },
    )
    record = SimpleNamespace(sha256="synthetic", observations=1)
    inventory = SimpleNamespace(
        matches=[SimpleNamespace(match_id=row["match_id"], **vars(record)) for row in entries]
        + [SimpleNamespace(match_id=f"NA1_{index}") for index in range(6000, 36000)]
    )
    payload = {
        "timeline": {"observations": [{"timestamp_ms": 0}]},
        "labels": [{"timestamp_ms": 0, **dict.fromkeys(LABELS, 1)}],
        "event_index": {f"{event}_ms": [5000] for event in EVENTS},
    }
    with (
        patch(
            "league_ews.m1_alert_diagnostics.ProcessingManifest.model_validate_json",
            return_value=inventory,
        ),
        patch("league_ews.m1_alert_diagnostics._read_match", return_value=payload),
        patch("league_ews.m1_alert_diagnostics.select_threshold", return_value=(0.5, {})),
    ):
        output = root / "diagnostic.json"
        result = audit_m1_alert_opportunity(processed, split_file, calibration, policy_root, output)
        assert result["later_half_summary"]["dragon"]["event_recall"]["mean"] == 1.0
        opportunities = result["seed_diagnostics"][0]["events"]["dragon"][
            "opportunities_by_horizon_seconds"
        ]
        assert opportunities["10"] == 6000
        assert result["test_matches_unread"] == 6000
        assert "EUW1_0" not in output.read_text()
        assert audit_m1_alert_opportunity(
            processed, split_file, calibration, policy_root, output
        ) == result
        original_output = output.read_bytes()
        output.write_text("tampered")
        with unittest.TestCase().assertRaisesRegex(ValueError, "Existing alert opportunity"):
            audit_m1_alert_opportunity(processed, split_file, calibration, policy_root, output)
        output.write_bytes(original_output)
        payload["labels"][0][LABELS[0]] = 2
        with unittest.TestCase().assertRaisesRegex(ValueError, "labels must be binary"):
            audit_m1_alert_opportunity(processed, split_file, calibration, policy_root, output)
        payload["labels"][0][LABELS[0]] = 1
        policy_file = policy_root / f"policy.seed-{SEEDS[0]}.json"
        policy_file.write_text("tampered")
        with unittest.TestCase().assertRaisesRegex(ValueError, "checksum differs"):
            audit_m1_alert_opportunity(processed, split_file, calibration, policy_root, output)


class AlertOpportunityTests(unittest.TestCase):
    def test_full_audit_and_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            _synthetic_audit(Path(directory))

    def test_strict_future_observation_and_cooldown(self):
        matches = [
            MatchRisk((0, 60_000, 120_000), (9_000, 80_000, 200_000), (0.9, 0.9, 0.9)),
            MatchRisk((0, 60_000), (60_000,), (0.8, 0.8)),
        ]
        result = diagnose_alerts(matches, 0.5)
        self.assertEqual(
            result["opportunities_by_horizon_seconds"],
            {"10": 1, "20": 2, "30": 2, "60": 3},
        )
        self.assertEqual(result["events"], 4)
        self.assertEqual(result["recall_of_observable_events_60"], 2 / 3)
        self.assertEqual(
            result["matched_lead_seconds"],
            {
                "under_10": 1,
                "over_10_to_30": 0,
                "over_30_to_60": 1,
            },
        )
        self.assertEqual(result["false_alerts_per_game"]["maximum"], 1)
        self.assertEqual(result["games_with_at_least_one_false_alert"], 1)

    def test_onset_at_frame_is_not_anticipated_by_that_frame(self):
        result = diagnose_alerts([MatchRisk((10_000,), (10_000,), (0.8,))], 0.5)
        self.assertEqual(result["opportunities_by_horizon_seconds"]["60"], 0)
        self.assertIsNone(result["recall_of_observable_events_60"])
        self.assertEqual(result["false_alerts_per_game"]["maximum"], 1)

    def test_no_event_or_alert_has_defined_zero_burden(self):
        empty = diagnose_alerts([MatchRisk((), (), ())], 0.5)
        self.assertIsNone(empty["observable_fraction_60"])
        self.assertIsNone(empty["recall_of_observable_events_60"])
        self.assertEqual(empty["false_alerts_per_game"]["maximum"], 0)
        no_hit = diagnose_alerts([MatchRisk((0,), (5000,), (0.1,))], 0.5)
        self.assertEqual(no_hit["recall_of_observable_events_60"], 0.0)
        self.assertEqual(no_hit["games_with_at_least_one_false_alert"], 0)

    def test_no_test_or_raw_dependency_in_cli(self):
        args = build_parser().parse_args(
            [
                "audit-m1-alert-opportunity",
                "--processed",
                "processed",
                "--split",
                "split.json",
                "--calibration-root",
                "calibration",
                "--policy-root",
                "policies",
                "--output",
                "diagnostic.json",
            ]
        )
        self.assertFalse(hasattr(args, "test_root"))
        self.assertFalse(hasattr(args, "raw"))

    def test_cli_prints_only_compact_aggregate(self):
        args = build_parser().parse_args(
            [
                "audit-m1-alert-opportunity",
                "--processed",
                "processed",
                "--split",
                "split.json",
                "--calibration-root",
                "calibration",
                "--policy-root",
                "policies",
                "--output",
                "diagnostic.json",
            ]
        )
        report = {
            "calibration_matches": 6000,
            "seed_count": 10,
            "test_matches_unread": 6000,
            "seed_diagnostics": [
                {
                    "events": {
                        event: {"opportunities_by_horizon_seconds": {"60": 50}} for event in EVENTS
                    }
                }
            ],
            "later_half_summary": {
                event: {
                    metric: {"mean": 0.5}
                    for metric in ("event_f1", "event_recall", "false_alerts_per_game")
                }
                for event in EVENTS
            },
        }
        output = io.StringIO()
        with (
            patch("league_ews.cli.audit_m1_alert_opportunity", return_value=report),
            redirect_stdout(output),
        ):
            self.assertEqual(args.handler(args), 0)
        displayed = json.loads(output.getvalue())
        self.assertEqual(displayed["events"]["dragon"]["later_half_f1_mean"], 0.5)
        self.assertNotIn("seed_diagnostics", displayed)

    def test_balanced_temporal_halves_reject_changed_order(self):
        entries = [
            {"regional_route": route, "game_creation_ms": index}
            for index in range(3000)
            for route in ("europe", "americas")
        ]
        early, later = _chronological_halves(entries)
        self.assertEqual((len(early), len(later)), (3000, 3000))
        self.assertEqual((max(early), min(later)), (2999, 3000))
        entries[2]["game_creation_ms"] = -1
        with self.assertRaises(ValueError):
            _chronological_halves(entries)
        entries[2]["game_creation_ms"] = 1
        entries[0]["regional_route"] = "asia"
        with self.assertRaises(ValueError):
            _chronological_halves(entries)
        with self.assertRaises(ValueError):
            _chronological_halves(entries[1:])


def test_alert_opportunity_strict_future_observation_and_cooldown():
    AlertOpportunityTests().test_strict_future_observation_and_cooldown()


def test_alert_opportunity_at_frame_is_not_anticipated():
    AlertOpportunityTests().test_onset_at_frame_is_not_anticipated_by_that_frame()


def test_alert_opportunity_no_event_or_alert():
    AlertOpportunityTests().test_no_event_or_alert_has_defined_zero_burden()


def test_alert_opportunity_cli_has_no_test_or_raw_dependency():
    AlertOpportunityTests().test_no_test_or_raw_dependency_in_cli()


def test_alert_opportunity_temporal_halves_reject_changed_order():
    AlertOpportunityTests().test_balanced_temporal_halves_reject_changed_order()


def test_alert_opportunity_full_audit_and_mutation():
    AlertOpportunityTests().test_full_audit_and_mutation()


def test_alert_opportunity_cli_compact_summary():
    AlertOpportunityTests().test_cli_prints_only_compact_aggregate()
