"""Useful-lead independent targets, exact checkpoints and committed-analysis gating."""

import json

import numpy as np
import pytest

from scripts import run_timely_sharing as runner
from scripts.run_compact_notebook import sequences
from scripts.task_sharing_backend import IndependentEventBackend
from scripts.timely_neural_targets import fitted_targets
from tests import test_timely_neural as base_fixture
from tests.test_compact_research import archive, norm, sample
from tests.test_task_sharing import same


def test_checkpoint_resume_exact_and_recovers_progress_after_interrupted_write(tmp_path):
    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    resumed, direct = tmp_path / "resumed", tmp_path / "direct"
    for _ in range(2):
        runner.train_fit(path, manifest, norm(), resumed, "fixture", "dragon", 9, "cpu", 1)
    runner.train_fit(path, manifest, norm(), direct, "fixture", "dragon", 9, "cpu", 2)
    backend = IndependentEventBackend(9, event="dragon")
    a = backend.torch.load(resumed / "dragon/seed-9/checkpoint.pt", weights_only=True)
    b = backend.torch.load(direct / "dragon/seed-9/checkpoint.pt", weights_only=True)
    same(backend.torch, a["backend"], b["backend"])
    assert a["completed_units"] == b["completed_units"] == 2
    assert a["last_loss"] == b["last_loss"]
    with pytest.raises(ValueError, match="checkpoint mismatch"):
        runner.train_fit(path, manifest, norm(), resumed, "different", "dragon", 9, "cpu", 1)


@pytest.mark.parametrize("event", runner.EVENTS)
def test_scoring_saves_only_trained_event_horizons(tmp_path, monkeypatch, event):
    import torch

    data = sample()
    path, entry = archive(tmp_path, data)
    manifest = {"shards": [{}] * 48 + [{**entry, "partition": "calibration"}]}
    expected, expected_mask, _ = sequences(data, norm())
    scores = np.tile(np.arange(1, 13, dtype=np.float32) / 20, (len(expected), 1))

    class Backend:
        def __init__(self, *args, **kwargs):
            self.torch = torch
            self.version = str(torch.__version__)
            self.columns = slice(runner.EVENTS.index(event) * 4, runner.EVENTS.index(event) * 4 + 4)

        def load_state_dict(self, state):
            pass

        def predict_shard(self, x, mask):
            np.testing.assert_array_equal(x, expected)
            np.testing.assert_array_equal(mask, expected_mask)
            return scores[:, self.columns]

    p = tmp_path / "output" / event / "seed-9"
    p.mkdir(parents=True)
    torch.save(
        {
            "freeze_sha256": "fixture",
            "completed_units": 576,
            "backend": {},
            "parameters": 10,
            "active_parameters": 8,
            "event": event,
            "seed": 9,
            "device": "cpu",
            "torch_version": str(torch.__version__),
            "training_seconds": 1.0,
        },
        p / "checkpoint.pt",
    )
    monkeypatch.setattr(runner, "IndependentEventBackend", Backend)
    report = runner.score_fit(
        path, manifest, norm(), tmp_path / "output", "fixture", event, 9, "cpu", data, []
    )
    assert "warnings" not in report and "row_metrics" not in report
    with np.load(p / "calibration-scores.npz") as z:
        np.testing.assert_array_equal(z["targets"], data["targets"][:, Backend().columns])
        np.testing.assert_array_equal(
            z["fitted_targets"], fitted_targets(data)[:, Backend().columns]
        )
        np.testing.assert_array_equal(z["match_offsets"], data["match_offsets"])
        np.testing.assert_array_equal(z["probabilities"], scores[:, Backend().columns])


def fixture_run(tmp_path, monkeypatch):
    monkeypatch.setattr(base_fixture, "runner", runner)
    args = base_fixture.fixture_run(tmp_path, monkeypatch)
    plan = json.loads(args.plan.read_bytes())
    plan["analysis_sources"] = ["fixture.py"]
    args.plan.write_text(json.dumps(plan))
    monkeypatch.setattr(runner, "verify_prior_controls", lambda *_: {})
    return args


def test_all_nine_fits_and_committed_release_required_before_scoring(tmp_path, monkeypatch):
    args = fixture_run(tmp_path, monkeypatch)
    trained = []

    def train(*a):
        trained.append((a[5], a[6]))
        return 576, len(trained) != 9

    monkeypatch.setattr(runner, "train_fit", train)
    monkeypatch.setattr(runner, "load_partition", lambda *_: pytest.fail("Premature scoring"))
    assert runner.run(args)["status"] == "paused-resume-same-command"
    assert len(trained) == 9
    monkeypatch.setattr(runner, "train_fit", lambda *_: (0, True))
    assert runner.run(args) == {"status": "awaiting-committed-analysis-release", "new_scores": 0}
    (args.output / "analysis-release.json").write_text("{}")

    def invalid(*_):
        raise ValueError("Uncommitted analysis")

    monkeypatch.setattr(runner, "verify_scoring_release", invalid)
    with pytest.raises(ValueError, match="Uncommitted"):
        runner.run(args)
    released = []
    monkeypatch.setattr(runner, "verify_scoring_release", lambda *a: released.append(a))

    def calibration(*_):
        assert len(released) == 1
        return {}, []

    monkeypatch.setattr(runner, "load_partition", calibration)
    scored = []

    def score(*a):
        assert len(released) == 1
        scored.append((a[5], a[6]))
        return {"fixture": True}

    monkeypatch.setattr(runner, "score_fit", score)
    assert runner.run(args)["status"] == "complete-exploratory-timely-sharing-predictions"
    assert len(scored) == 9


def test_training_uses_useful_targets_and_preserves_nonfinite_checkpoint(tmp_path, monkeypatch):
    data = sample()
    path, entry = archive(tmp_path, data)
    manifest = {"shards": [entry] * 48}
    original = IndependentEventBackend.train_shard
    calls = []

    def checked(self, x, mask, targets, **kwargs):
        np.testing.assert_array_equal(targets, fitted_targets(data))
        calls.append(targets.copy())
        return original(self, x, mask, targets, **kwargs)

    monkeypatch.setattr(IndependentEventBackend, "train_shard", checked)
    output = tmp_path / "study"
    runner.train_fit(path, manifest, norm(), output, "fixture", "dragon", 9, "cpu", 1)
    assert len(calls) == 1
    checkpoint = output / "dragon/seed-9/checkpoint.pt"
    before = runner.sha(checkpoint)

    def invalid(self, *args, **kwargs):
        with self.torch.no_grad():
            next(self.model.parameters()).fill_(float("nan"))
        return 0.0, 18

    monkeypatch.setattr(IndependentEventBackend, "train_shard", invalid)
    with pytest.raises(ValueError, match="Nonfinite parameters"):
        runner.train_fit(path, manifest, norm(), output, "fixture", "dragon", 9, "cpu", 1)
    assert runner.sha(checkpoint) == before
