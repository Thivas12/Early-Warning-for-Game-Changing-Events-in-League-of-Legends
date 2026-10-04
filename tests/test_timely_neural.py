"""Target, feature isolation, exact resume and scoring-gate implementation checks."""

import json
import zipfile
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.notebook_ews import NotebookEWSBackend
from scripts import run_timely_neural as runner
from scripts.audit_neural_results import reference_counts
from scripts.run_compact_notebook import sequences
from scripts.run_three_event_timing import timely_targets
from scripts.timely_neural_targets import fitted_targets, next_event_delays
from tests.test_compact_research import archive, norm, sample


def test_target_boundaries_and_next_event_credit_are_exact():
    times = np.zeros(11, dtype=np.int64)
    delays = np.array([0, 9999, 10000, 19999, 20000, 30000, 30001, 60000, 60001, 5000, 70000])
    event_lists = [np.array([v], dtype=np.int64) for v in delays]
    event_lists[9] = np.array([5000, 20000])  # Later timely event cannot rescue earlier late event.
    offsets = np.r_[0, np.cumsum([len(v) for v in event_lists])]
    data = {
        "times_ms": times,
        "match_offsets": np.arange(12),
        "targets": np.zeros((11, 12), dtype=np.int8),
    }
    data["targets"][:, ::4] = 1  # Auxiliary preservation, regardless of fixture labels.
    for event in runner.EVENTS:
        data[event + "_ms"] = np.concatenate(event_lists)
        data[event + "_offsets"] = offsets
    y = fitted_targets(data)
    for e, _event in enumerate(runner.EVENTS):
        for c, h in ((2, 30), (3, 60)):
            expected = [
                reference_counts(np.array([0]), events, np.array([1.0]), 0.5, h)[2]
                for events in event_lists
            ]
            np.testing.assert_array_equal(y[:, 4 * e + c], expected)
        np.testing.assert_array_equal(
            y[:, 4 * e : 4 * e + 2], data["targets"][:, 4 * e : 4 * e + 2]
        )
    assert y[9, 2] == 0  # Any-event-in-window formulation would incorrectly give 1.
    assert next_event_delays(data, "baron")[0] == np.iinfo(np.int64).max


def test_fitted_targets_match_existing_tree_control_and_do_not_change_features():
    data = sample()
    original = deepcopy(data)
    x, mask, _ = sequences(data, norm())
    y = fitted_targets(data)
    for e, event in enumerate(runner.EVENTS):
        np.testing.assert_array_equal(y[:, 4 * e + 2], timely_targets(data, event))
    for k in data:
        np.testing.assert_array_equal(data[k], original[k])
    changed = deepcopy(data)
    changed["targets"] = y
    revised, other, _ = sequences(changed, norm())
    np.testing.assert_array_equal(revised, x)
    np.testing.assert_array_equal(other, mask)
    changed["dragon_ms"][:] += 10000
    revised, _, _ = sequences(changed, norm())
    np.testing.assert_array_equal(revised, x)


def test_exact_resume_and_missing_checkpoint_rejected(tmp_path):
    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    resumed, direct = tmp_path / "resumed", tmp_path / "direct"
    for _ in range(2):
        runner.train_fit(path, manifest, norm(), resumed, "fixture", "tcn", 9, "cpu", 1)
    runner.train_fit(path, manifest, norm(), direct, "fixture", "tcn", 9, "cpu", 2)
    backend = NotebookEWSBackend(9, family="tcn")
    a = backend.torch.load(resumed / "tcn/seed-9/checkpoint.pt", weights_only=True)
    b = backend.torch.load(direct / "tcn/seed-9/checkpoint.pt", weights_only=True)

    def same(x, y):
        if backend.torch.is_tensor(x):
            assert backend.torch.equal(x, y)
        elif isinstance(x, dict):
            assert x.keys() == y.keys()
            for k in x:
                same(x[k], y[k])
        elif isinstance(x, list):
            for p, q in zip(x, y, strict=True):
                same(p, q)
        else:
            assert x == y

    same(a["backend"], b["backend"])
    assert a["last_loss"] == b["last_loss"]
    assert a["completed_units"] == b["completed_units"] == 2
    with pytest.raises(ValueError, match="checkpoint mismatch"):
        runner.train_fit(path, manifest, norm(), resumed, "different", "tcn", 9, "cpu", 1)
    (resumed / "tcn/seed-9/checkpoint.pt").unlink()
    with pytest.raises(ValueError, match="Missing checkpoint"):
        runner.train_fit(path, manifest, norm(), resumed, "fixture", "tcn", 9, "cpu", 1)


def fixture_run(tmp_path, monkeypatch):
    import torch

    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    with zipfile.ZipFile(path, "a") as z:
        z.writestr("manifest.json", json.dumps(manifest))
    control = tmp_path / "control"
    control.mkdir()
    summary = {
        "status": "complete-exploratory-architecture-screen",
        "test_payloads_opened": 0,
        "models": {},
    }
    frozen = {
        "source_sha256": {},
        "runtime": {
            "device": "cpu",
            "torch": str(torch.__version__),
            "cuda_build": torch.version.cuda,
            "gpu_name": None,
        },
    }
    runner.write_json(control / "freeze.json", frozen)
    summary["freeze_sha256"] = runner.sha(control / "freeze.json")
    runner.write_json(control / "normalizer.json", runner.fit_normalizer(path, manifest))
    for family in runner.PLAN["families"]:
        for seed in runner.SEEDS:
            p = control / family / f"seed-{seed}"
            p.mkdir(parents=True)
            (p / "checkpoint.pt").write_bytes(b"fixture")
            (p / "calibration-scores.npz").write_bytes(b"fixture")
            runner.write_json(p / "progress.json", {"completed_units": 576})
            r = {
                "checkpoint_sha256": runner.sha(p / "checkpoint.pt"),
                "scores_sha256": runner.sha(p / "calibration-scores.npz"),
            }
            runner.write_json(p / "report.json", r)
            summary["models"][f"{family}/{seed}"] = r
    runner.write_json(control / "summary.json", summary)
    plan = tmp_path / "plan.json"
    runner.write_json(
        plan,
        {
            "families": list(runner.FAMILIES),
            "events": list(runner.EVENTS),
            "seeds": list(runner.SEEDS),
            "original_plan": runner.PLAN,
            "control_summary_sha256": runner.sha(control / "summary.json"),
            "control_freeze_sha256": runner.sha(control / "freeze.json"),
        },
    )
    monkeypatch.setattr(runner, "validate_archive", lambda *_: {"fixture": True})
    return SimpleNamespace(
        archive=path,
        control=control,
        control_source=tmp_path,
        output=tmp_path / "output",
        plan=plan,
        device="cpu",
        max_new_shards=0,
        preflight=False,
    )


def test_all_six_fits_must_complete_before_predictions(tmp_path, monkeypatch):
    args = fixture_run(tmp_path, monkeypatch)
    trained = []

    def train(*a):
        trained.append((a[5], a[6]))
        return 576, len(trained) != 6

    monkeypatch.setattr(runner, "train_fit", train)
    monkeypatch.setattr(
        runner, "load_partition", lambda *_: pytest.fail("Premature calibration scoring")
    )
    result = runner.run(args)
    assert result["status"] == "paused-resume-same-command" and len(trained) == 6
    assert not (args.output / "summary.json").exists()
    trained.clear()

    def complete(*a):
        trained.append((a[5], a[6]))
        return 0, True

    monkeypatch.setattr(runner, "train_fit", complete)

    def calibration(*a):
        assert len(trained) == 6
        return {}, []

    monkeypatch.setattr(runner, "load_partition", calibration)
    scored = []

    def score(*a):
        assert len(trained) == 6
        scored.append((a[5], a[6]))
        return {"fixture": True}

    monkeypatch.setattr(runner, "score_fit", score)
    assert runner.run(args)["status"] == "complete-exploratory-timely-neural-predictions"
    assert len(scored) == 6


def test_prediction_scoring_saves_both_target_definitions_without_evaluation(tmp_path, monkeypatch):
    import torch

    data = sample()
    path, entry = archive(tmp_path, data)
    manifest = {"shards": [{}] * 48 + [{**entry, "partition": "calibration"}]}
    expected, mask, _ = sequences(data, norm())
    scores = np.full((18, 12), 0.25, dtype=np.float32)

    class Backend:
        def __init__(self, *args, **kwargs):
            self.torch, self.version = torch, str(torch.__version__)

        def load_state_dict(self, state):
            pass

        def predict_shard(self, x, m):
            np.testing.assert_array_equal(x, expected)
            np.testing.assert_array_equal(m, mask)
            return scores

    monkeypatch.setattr(runner, "NotebookEWSBackend", Backend)
    folder = tmp_path / "output/tcn/seed-9"
    folder.mkdir(parents=True)
    torch.save(
        {
            "freeze_sha256": "fixture",
            "completed_units": 576,
            "family": "tcn",
            "seed": 9,
            "device": "cpu",
            "torch_version": str(torch.__version__),
            "backend": {},
            "parameters": 1,
            "training_seconds": 1,
        },
        folder / "checkpoint.pt",
    )
    report = runner.score_fit(
        path, manifest, norm(), tmp_path / "output", "fixture", "tcn", 9, "cpu", data, []
    )
    assert "warnings" not in report and "row_metrics" not in report
    with np.load(folder / "calibration-scores.npz", allow_pickle=False) as saved:
        np.testing.assert_array_equal(saved["fitted_targets"], fitted_targets(data))
        np.testing.assert_array_equal(saved["targets"], data["targets"])
        np.testing.assert_array_equal(saved["probabilities"], scores)


def test_nonfinite_update_preserves_last_valid_checkpoint(tmp_path, monkeypatch):
    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    output = tmp_path / "study"
    runner.train_fit(path, manifest, norm(), output, "fixture", "tcn", 9, "cpu", 1)
    checkpoint = output / "tcn/seed-9/checkpoint.pt"
    digest = runner.sha(checkpoint)

    def invalid(self, inputs, *args, **kwargs):
        with self.torch.no_grad():
            next(self.model.parameters()).fill_(float("nan"))
        return 0.0, len(inputs)

    monkeypatch.setattr(runner.NotebookEWSBackend, "train_shard", invalid)
    with pytest.raises(ValueError, match="Nonfinite parameters"):
        runner.train_fit(path, manifest, norm(), output, "fixture", "tcn", 9, "cpu", 1)
    assert runner.sha(checkpoint) == digest
    assert json.loads((checkpoint.parent / "progress.json").read_text())["completed_units"] == 1
