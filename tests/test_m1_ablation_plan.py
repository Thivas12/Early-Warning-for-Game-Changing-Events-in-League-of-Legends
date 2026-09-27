"""The registered variants bind to M1's frozen train/calibration evidence."""

import hashlib
import json
from pathlib import Path

import pytest

from league_ews.cli import build_parser
from league_ews.m1_ablation_plan import VARIANTS, freeze_m1_ablations
from league_ews.m1_training_plan import SEEDS

ROOT = Path(__file__).resolve().parents[1]
ABLATIONS = ROOT / "configs" / "rifthazard-m1-ablation-plan.yaml"
TRAINING = ROOT / "configs" / "rifthazard-m1-training-plan.yaml"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    return path


def _sources(tmp_path: Path) -> tuple[Path, Path, Path]:
    frozen = _write(
        tmp_path / "training-freeze.json",
        {
            "schema_version": "league-ews-m1-training-freeze-v1",
            "training_plan_sha256": _sha(TRAINING.read_bytes()),
            "split_sha256": "a" * 64,
            "seeds": SEEDS,
            "train_matches": 24000,
            "calibration_matches_unread": 6000,
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        },
    )
    calibration = _write(
        tmp_path / "calibration.json",
        {
            "schema_version": "league-ews-m1-ten-seed-calibration-v1",
            "freeze_sha256": _sha(frozen.read_bytes()),
            "split_sha256": "a" * 64,
            "seed_count": 10,
            "seed_results": [{"seed": seed} for seed in SEEDS],
            "selected_seed": None,
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        },
    )
    alerts = _write(
        tmp_path / "alert.json",
        {
            "schema_version": "league-ews-m1-ten-seed-alert-summary-v1",
            "ten_seed_calibration_sha256": _sha(calibration.read_bytes()),
            "split_sha256": "a" * 64,
            "seed_count": 10,
            "seed_reports": [{"seed": seed} for seed in SEEDS],
            "selected_seed": None,
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        },
    )
    return frozen, calibration, alerts


def test_freeze_binds_all_variants_and_private_calibration(tmp_path: Path) -> None:
    frozen, calibration, alerts = _sources(tmp_path)
    output = tmp_path / "ablation-freeze.json"
    report = freeze_m1_ablations(ABLATIONS, TRAINING, frozen, calibration, alerts, output)
    assert report["variants"] == list(VARIANTS)
    assert report["test_matches_unread"] == 6000
    assert report["alert_summary_sha256"] == _sha(alerts.read_bytes())
    assert freeze_m1_ablations(ABLATIONS, TRAINING, frozen, calibration, alerts, output) == report
    output.write_text("altered")
    with pytest.raises(ValueError, match="Existing"):
        freeze_m1_ablations(ABLATIONS, TRAINING, frozen, calibration, alerts, output)


@pytest.mark.parametrize("source", ["frozen", "calibration", "alerts"])
def test_tampered_binding_fails_closed(tmp_path: Path, source: str) -> None:
    frozen, calibration, alerts = _sources(tmp_path)
    chosen = {"frozen": frozen, "calibration": calibration, "alerts": alerts}[source]
    payload = json.loads(chosen.read_text())
    payload["split_sha256"] = "b" * 64
    _write(chosen, payload)
    with pytest.raises(ValueError, match="ablation freeze"):
        freeze_m1_ablations(
            ABLATIONS, TRAINING, frozen, calibration, alerts, tmp_path / "output.json"
        )


def test_changed_plan_and_seed_selection_fail_closed(tmp_path: Path) -> None:
    frozen, calibration, alerts = _sources(tmp_path)
    altered = tmp_path / "altered.yaml"
    altered.write_text(
        ABLATIONS.read_text().replace("graph_pool_denominator: 10", "graph_pool_denominator: 12")
    )
    with pytest.raises(ValueError, match="ablation plan"):
        freeze_m1_ablations(
            altered, TRAINING, frozen, calibration, alerts, tmp_path / "output.json"
        )
    data = json.loads(alerts.read_text())
    data["selected_seed"] = SEEDS[0]
    _write(alerts, data)
    with pytest.raises(ValueError, match="ablation freeze"):
        freeze_m1_ablations(
            ABLATIONS, TRAINING, frozen, calibration, alerts, tmp_path / "output.json"
        )


def test_cli_exposes_freeze_with_explicit_private_inputs() -> None:
    args = build_parser().parse_args(
        [
            "freeze-m1-ablations",
            "--ablation-plan",
            str(ABLATIONS),
            "--training-plan",
            str(TRAINING),
            "--training-freeze",
            "private/training.json",
            "--calibration-summary",
            "private/calibration.json",
            "--alert-summary",
            "private/alerts.json",
            "--output",
            "private/freeze.json",
        ]
    )
    assert args.output == Path("private/freeze.json")
