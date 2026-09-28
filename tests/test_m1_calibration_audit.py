"""Check that diagnostic comparisons are paired and checksum-bound."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.m1_calibration_audit import audit_m1_calibration
from league_ews.m1_training_plan import SEEDS


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_experiment(root, *, variant=None, original_hash=None):
    root.mkdir(parents=True)
    seeds = []
    for seed in SEEDS:
        folder = root / f"seed-{seed}"
        folder.mkdir()
        scores = folder / "calibration-scores.npz"
        scores.write_bytes(f"private score for {seed}".encode())
        ap = 0.6 if variant else 0.5
        report = {
            "schema_version": (
                "league-ews-m1-graph-ablation-calibration-v1"
                if variant
                else "league-ews-m1-calibration-v1"
            ),
            "seed": seed,
            "scores_sha256": _sha(scores),
            "checkpoint_sha256": str(seed),
            "targets": list(LABELS),
            "calibration_matches": 6000,
            "calibration_observations": 12,
            "test_matches_unread": 6000,
            "identifiers_in_report": False,
            "metrics": {
                label: {"average_precision": ap, "brier": 0.12, "prevalence": 0.2}
                for label in LABELS
            },
            "macro_average_precision": ap,
        }
        if variant:
            report["variant"] = variant
        path = folder / "calibration-report.json"
        path.write_text(json.dumps(report))
        seeds.append(
            {
                "seed": seed,
                "report_sha256": _sha(path),
                "scores_sha256": _sha(scores),
                "checkpoint_sha256": str(seed),
            }
        )
    summary = {
        "schema_version": (
            "league-ews-m1-graph-ablation-ten-seed-summary-v1"
            if variant
            else "league-ews-m1-ten-seed-calibration-v1"
        ),
        "seed_count": 10,
        "calibration_matches": 6000,
        "calibration_observations": 12,
        "test_matches_unread": 6000,
        "selected_seed": None,
        "identifiers_in_summary": False,
        "split_sha256": "split",
        "seed_results": seeds,
        "per_target_average_precision": {
            label: {"mean": 0.6 if variant else 0.5} for label in LABELS
        },
    }
    if variant:
        summary.update(
            {
                "variant": variant,
                "original_m1_summary_sha256": original_hash,
                "training_freeze_sha256": "freeze",
            }
        )
    else:
        summary["freeze_sha256"] = "freeze"
    path = root / "ten-seed-summary.json"
    path.write_text(json.dumps(summary))
    return path


def _test_audit_paired_targets_missing_variants_and_no_test(tmp_path):
    original = tmp_path / "original"
    original_path = _make_experiment(original)
    root = tmp_path / "variants"
    variant = "no-objective-nodes"
    _make_experiment(root / variant, variant=variant, original_hash=_sha(original_path))
    output = tmp_path / "audit.json"
    result = audit_m1_calibration(original, root, output)
    target = result["comparisons"][variant]["per_target"][LABELS[0]]
    assert abs(target["paired_ap_delta_mean"] - 0.1) < 1e-12
    assert target["positive_delta_seeds"] == 10
    assert abs(target["m1_ap_lift_over_prevalence"] - 2.5) < 1e-12
    assert result["comparisons"][variant]["positive_delta_seeds"] == 10
    assert len(result["missing_variants"]) == 5
    assert result["test_matches_unread"] == 6000
    assert audit_m1_calibration(original, root, output) == result


def _test_audit_rejects_mutation_and_incompatible_split(tmp_path):
    original = tmp_path / "original"
    original_path = _make_experiment(original)
    variant = "no-objective-nodes"
    root = tmp_path / "variants"
    variant_path = _make_experiment(
        root / variant, variant=variant, original_hash=_sha(original_path)
    )
    summary = json.loads(variant_path.read_text())
    summary["split_sha256"] = "other"
    variant_path.write_text(json.dumps(summary))
    try:
        audit_m1_calibration(original, root, tmp_path / "audit.json")
    except ValueError as exc:
        assert "not bound" in str(exc)
    else:
        raise AssertionError("incompatible split was accepted")
    summary["split_sha256"] = "split"
    variant_path.write_text(json.dumps(summary))
    score = root / variant / f"seed-{SEEDS[0]}" / "calibration-scores.npz"
    score.write_bytes(score.read_bytes() + b"changed")
    try:
        audit_m1_calibration(original, root, tmp_path / "audit.json")
    except ValueError as exc:
        assert "checksum differs" in str(exc)
    else:
        raise AssertionError("mutated scores were accepted")


def test_audit_cli_has_no_test_path():
    args = build_parser().parse_args(
        [
            "audit-m1-calibration",
            "--original-root",
            "original",
            "--ablation-root",
            "variants",
            "--output",
            "diagnostic.json",
        ]
    )
    assert args.original_root.name == "original"
    assert not hasattr(args, "test_root")


class AuditTests(unittest.TestCase):
    def test_pairs_and_incomplete_inventory(self):
        with tempfile.TemporaryDirectory() as root:
            _test_audit_paired_targets_missing_variants_and_no_test(Path(root))

    def test_rejects_modified_inputs(self):
        with tempfile.TemporaryDirectory() as root:
            _test_audit_rejects_mutation_and_incompatible_split(Path(root))

    def test_parser_has_no_test_path(self):
        test_audit_cli_has_no_test_path()
