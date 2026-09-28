"""Alert opportunity is measured from real frames with frozen alert matching."""

import unittest

from league_ews.alert_policy import MatchRisk
from league_ews.cli import build_parser
from league_ews.m1_alert_diagnostics import _chronological_halves, diagnose_alerts


class AlertOpportunityTests(unittest.TestCase):
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


def test_alert_opportunity_strict_future_observation_and_cooldown():
    AlertOpportunityTests().test_strict_future_observation_and_cooldown()


def test_alert_opportunity_at_frame_is_not_anticipated():
    AlertOpportunityTests().test_onset_at_frame_is_not_anticipated_by_that_frame()


def test_alert_opportunity_cli_has_no_test_or_raw_dependency():
    AlertOpportunityTests().test_no_test_or_raw_dependency_in_cli()


def test_alert_opportunity_temporal_halves_reject_changed_order():
    AlertOpportunityTests().test_balanced_temporal_halves_reject_changed_order()
