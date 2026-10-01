"""Statistical unit checks; fixtures are not empirical League evidence."""

import json

import numpy as np
import pytest

from league_ews.coordination_experiment import sha
from scripts import analyse_neural_screen as analysis
from scripts.analyse_neural_screen import metrics, resample_weights, summarise
from scripts.league_compact_data import EXPECTED_ARCHIVE


def test_bootstrap_preserves_route_sizes_and_resamples_whole_matches():
    routes = np.array(["europe"] * 3 + ["americas"] * 2)
    weights = resample_weights(routes, draws=50)
    np.testing.assert_array_equal(weights[:, :3].sum(1), 3)
    np.testing.assert_array_equal(weights[:, 3:].sum(1), 2)
    assert (weights >= 0).all()
    assert (weights == weights.astype(int)).all()
    assert np.any(weights > 1)


def test_recall_uses_event_totals_not_mean_of_match_recalls():
    counts = np.array([[[[1, 1, 1, 2, 1, 1], [9, 3, 2, 5, 2, 3]]]])
    got = metrics(counts, np.ones((1, 2)))[0, 0, 0]
    np.testing.assert_allclose(got, [0.3, 2.0, 1.5, 0.5])


def test_identical_seeds_do_not_narrow_conditional_interval():
    one = np.array([[[[1, 1, 1, 2, 1, 1], [9, 3, 2, 5, 2, 3]]]])
    counts = np.tile(one, (3, 3, 1, 1))
    draws = metrics(counts, resample_weights(np.array(["europe", "europe"]), 100))
    point = metrics(counts, np.ones((1, 2)))[0]
    result = summarise(point, draws)["macro"]
    assert result["mean_over_fixed_seeds"] == result["by_seed"]["20260930"]
    zeros = summarise(point - point, draws - draws)["macro"]
    assert zeros["mean_over_fixed_seeds"]["timely_recall"]["conditional_95_interval"] == [0, 0]


@pytest.fixture
def completed_study(tmp_path, monkeypatch):
    """Small compressed fixtures satisfy the real loader's fixed match contract."""
    monkeypatch.setattr(analysis, "SEEDS", (20260930,))
    folder = tmp_path / "snapshot/seed-20260930"
    folder.mkdir(parents=True)
    (tmp_path / "freeze.json").write_text(json.dumps({"archive_sha256": EXPECTED_ARCHIVE}))
    binding = sha(tmp_path / "freeze.json")
    (folder / "checkpoint.pt").write_bytes(b"fixture checked only by hash; never deserialized")
    arrays = {
        "match_offsets": np.arange(6001, dtype=np.int64) * 2,
        "targets": np.zeros((12000, 12), dtype=np.int8),
        "probabilities": np.full((12000, 12), 0.2, dtype=np.float32),
    }
    warnings = {}
    for event in ("baron", "dragon", "teamfight"):
        for horizon in (30, 60):
            name = f"{event}_{horizon}"
            arrays[f"counts_{name}"] = np.tile([1, 1, 1, 1, 0, 1], (3000, 1))
            warnings[name] = {
                "later": {
                    "matches": 3000,
                    "events": 3000,
                    "matched_events": 3000,
                    "timely_matched_events": 3000,
                    "alerts": 3000,
                    "timely_opportunities": 3000,
                    "false_alerts_per_match": 0,
                    "late_alerts_per_match": 0,
                    "non_timely_alerts_per_match": 0,
                }
            }
    progress = {
        "family": "snapshot",
        "seed": 20260930,
        "freeze_sha256": binding,
        "completed_units": 576,
    }
    report = {
        "family": "snapshot",
        "seed": 20260930,
        "freeze_sha256": binding,
        "checkpoint_sha256": sha(folder / "checkpoint.pt"),
        "warnings": warnings,
        "test_payloads_opened": 0,
    }

    def save():
        np.savez_compressed(folder / "calibration-scores.npz", **arrays)
        report["scores_sha256"] = sha(folder / "calibration-scores.npz")
        (folder / "report.json").write_text(json.dumps(report))
        (folder / "progress.json").write_text(json.dumps(progress))
        (tmp_path / "summary.json").write_text(
            json.dumps(
                {
                    "freeze_sha256": binding,
                    "status": "complete-exploratory-architecture-screen",
                    "models": {"snapshot/20260930": report},
                    "test_payloads_opened": 0,
                }
            )
        )

    save()
    return tmp_path, arrays, progress, report, save


def test_completed_loader_binds_to_archive_alignment(completed_study):
    root, arrays, _, _, _ = completed_study
    analysis.load_completed(root, ("snapshot",), reference=arrays)
    wrong_targets = arrays["targets"].copy()
    wrong_targets[0, 0] = 1
    with pytest.raises(ValueError, match="Targets differ"):
        analysis.load_completed(root, ("snapshot",), reference={**arrays, "targets": wrong_targets})
    wrong_offsets = arrays["match_offsets"].copy()
    wrong_offsets[1] = 1
    with pytest.raises(ValueError, match="Offsets differ"):
        analysis.load_completed(
            root, ("snapshot",), reference={**arrays, "match_offsets": wrong_offsets}
        )


@pytest.mark.parametrize(
    "failure", ["freeze", "fractional", "shape", "false_burden", "test_access"]
)
def test_completed_loader_rejects_inconsistent_bound_artifacts(completed_study, failure):
    root, arrays, progress, report, save = completed_study
    if failure == "freeze":
        progress["freeze_sha256"] = "wrong-freeze"
    elif failure == "fractional":
        arrays["counts_baron_30"] = arrays["counts_baron_30"].astype(float)
        arrays["counts_baron_30"][:, 5] = 0.5
    elif failure == "shape":
        arrays["probabilities"] = arrays["probabilities"][:-1]
    elif failure == "false_burden":
        report["warnings"]["baron_30"]["later"]["false_alerts_per_match"] = 0.2
    else:
        report["test_payloads_opened"] = 1
    save()  # Rebind hashes: the loader must validate semantics as well as checksums.
    with pytest.raises(ValueError):
        analysis.load_completed(root, ("snapshot",))
