"""Implementation fixtures: event isolation, paired RNG, exact resume and scoring gate."""

from copy import deepcopy

import numpy as np
import pytest

from league_ews.notebook_ews import NotebookEWSBackend, right_pad_sequences
from scripts import run_task_sharing as runner
from scripts.run_compact_notebook import sequences
from scripts.task_sharing_backend import IndependentEventBackend
from tests.test_compact_research import archive, norm, sample


def same(torch, left, right):
    if torch.is_tensor(left):
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            same(torch, left[key], right[key])
    elif isinstance(left, list):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            same(torch, a, b)
    else:
        assert left == right


@pytest.mark.parametrize("event", runner.EVENTS)
def test_identical_initial_model_selected_logits_dropout_rng_and_capacity(event):
    x, mask, _ = sequences(sample(), norm())
    joint = NotebookEWSBackend(17)
    initial = deepcopy(joint.state_dict())
    packed, lengths = right_pad_sequences(x, mask)
    logits = joint.model(joint.torch.from_numpy(packed), joint.torch.from_numpy(lengths))
    rng = joint.torch.get_rng_state().clone()
    independent = IndependentEventBackend(17, event=event)
    same(joint.torch, initial["model"], independent.model.state_dict())
    other_logits = independent.model(
        joint.torch.from_numpy(packed), joint.torch.from_numpy(lengths)
    )
    assert joint.torch.equal(logits, other_logits)
    assert joint.torch.equal(rng, joint.torch.get_rng_state())
    assert sum(p.numel() for p in independent.model.parameters()) == 1751647
    assert sum(p.numel() for p in independent.model.parameters() if p.requires_grad) == 1749591
    np.testing.assert_array_equal(
        independent.predict_shard(x, mask), joint.predict_shard(x, mask)[:, independent.columns]
    )


@pytest.mark.parametrize("event", runner.EVENTS)
def test_only_selected_event_labels_affect_training_with_original_loss_weight(event):
    x, mask, y = sequences(sample(), norm())
    a = IndependentEventBackend(29, event=event)
    initial = deepcopy(a.model.state_dict())
    packed, lengths = right_pad_sequences(x, mask)
    order = np.random.default_rng(31).permutation(len(x))
    logits = a.model(a.torch.from_numpy(packed[order]), a.torch.from_numpy(lengths[order]))
    expected = (
        a.loss_weight
        * a.torch.nn.functional.binary_cross_entropy_with_logits(
            logits[:, a.columns], a.torch.tensor(y[order, a.columns], dtype=a.torch.float32)
        ).item()
    )
    a = IndependentEventBackend(29, event=event)
    loss, rows = a.train_shard(x, mask, y, seed=31)
    final = deepcopy(a.state_dict())
    assert rows == len(x)
    assert loss == pytest.approx(expected, abs=1e-6)
    b = IndependentEventBackend(29, event=event)
    changed = np.full(y.shape, np.nan)
    changed[:, b.columns] = y[:, b.columns]
    other_loss, _ = b.train_shard(x, mask, changed, seed=31)
    assert loss == other_loss
    same(a.torch, final, b.state_dict())
    for i in range(3):
        name = f"heads.{i}.weight"
        assert a.torch.equal(initial[name], final["model"][name]) == (i != a.event_index)
    assert any(
        not a.torch.equal(value, final["model"][name])
        for name, value in initial.items()
        if not name.startswith("heads.")
    )


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


def test_invalid_event_and_selected_labels_rejected():
    with pytest.raises(ValueError, match="Unknown League event"):
        IndependentEventBackend(1, event="invalid")
    x, mask, y = sequences(sample(), norm())
    model = IndependentEventBackend(1, event="baron")
    with pytest.raises(ValueError, match="four binary"):
        model.train_shard(x, mask, np.full(y.shape, np.nan), seed=1)


@pytest.mark.parametrize("complete_fits", [0, 8])
def test_all_nine_fits_required_before_calibration(tmp_path, monkeypatch, complete_fits):
    import json
    import zipfile
    from types import SimpleNamespace

    import torch

    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    with zipfile.ZipFile(path, "a") as z:
        z.writestr("manifest.json", json.dumps(manifest))
    control = tmp_path / "control"
    control.mkdir()

    runner.write_json(
        control / "freeze.json",
        {
            "source_sha256": {},
            "runtime": {
                "device": "cpu",
                "torch": str(torch.__version__),
                "cuda_build": torch.version.cuda,
                "gpu_name": None,
            },
        },
    )
    runner.write_json(control / "normalizer.json", runner.fit_normalizer(path, manifest))
    reports = {}
    for family in runner.PLAN["families"]:
        for seed in runner.SEEDS:
            p = control / family / f"seed-{seed}"
            p.mkdir(parents=True)
            (p / "checkpoint.pt").write_bytes(b"fixture")
            (p / "calibration-scores.npz").write_bytes(b"fixture")
            runner.write_json(p / "progress.json", {"completed_units": 576})
            runner.write_json(
                p / "report.json",
                {
                    "checkpoint_sha256": runner.sha(p / "checkpoint.pt"),
                    "scores_sha256": runner.sha(p / "calibration-scores.npz"),
                },
            )
            reports[f"{family}/{seed}"] = json.loads((p / "report.json").read_bytes())
    runner.write_json(
        control / "summary.json",
        {
            "status": "complete-exploratory-architecture-screen",
            "freeze_sha256": runner.sha(control / "freeze.json"),
            "test_payloads_opened": 0,
            "models": reports,
        },
    )
    plan = tmp_path / "plan.json"
    runner.write_json(
        plan,
        {
            "events": list(runner.EVENTS),
            "original_plan": runner.PLAN,
            "seeds": list(runner.SEEDS),
            "control_summary_sha256": runner.sha(control / "summary.json"),
            "control_freeze_sha256": runner.sha(control / "freeze.json"),
        },
    )
    monkeypatch.setattr(runner, "validate_archive", lambda *a: {"status": "fixture"})
    monkeypatch.setattr(runner, "load_partition", lambda *a: pytest.fail("Premature calibration"))
    args = SimpleNamespace(
        plan=plan,
        control=control,
        control_source=control,
        archive=path,
        output=tmp_path / "output",
        device="cpu",
        max_new_shards=1,
        preflight=False,
    )
    calls = []

    def train(*a):
        calls.append((a[5], a[6]))
        return (0, True) if len(calls) <= complete_fits else (1, False)

    monkeypatch.setattr(runner, "train_fit", train)
    result = runner.run(args)
    assert len(calls) == complete_fits + 1
    assert result == {"status": "paused-resume-same-command", "new_shards": 1}


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

    calls = []

    def policy(cal, rows, probabilities, event, horizon):
        column = runner.EVENTS.index(event) * 4 + (2 if horizon == 30 else 3)
        np.testing.assert_array_equal(probabilities, scores[:, column])
        calls.append((event, horizon))
        return {}, np.zeros((1, 6), dtype=int)

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
    monkeypatch.setattr(runner, "_chronological_halves", lambda *a: ([0], [1]))
    monkeypatch.setattr(runner, "policy_report", policy)
    report = runner.score_fit(
        path, manifest, norm(), tmp_path / "output", "fixture", event, 9, "cpu", data, []
    )
    assert len(calls) == 2
    assert len(report["row_metrics"]) == 4
    with np.load(p / "calibration-scores.npz") as z:
        np.testing.assert_array_equal(z["targets"], data["targets"][:, Backend().columns])
        np.testing.assert_array_equal(z["match_offsets"], data["match_offsets"])
        np.testing.assert_array_equal(z["probabilities"], scores[:, Backend().columns])
