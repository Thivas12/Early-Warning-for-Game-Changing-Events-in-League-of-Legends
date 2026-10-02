"""PCGrad mathematics, RNG isolation, exact resume, and calibration gating."""

from copy import deepcopy

import numpy as np
import pytest

from league_ews.notebook_ews import NotebookEWSBackend, right_pad_sequences
from scripts import run_pcgrad as runner
from scripts.pcgrad_backend import PCGradBackend, projected_sum
from scripts.run_compact_notebook import sequences
from tests.test_compact_research import archive, norm, sample
from tests.test_task_sharing import same


@pytest.mark.parametrize("seed", range(5))
def test_gram_projection_matches_literal_paper_algorithm(seed):
    import torch

    rng = np.random.default_rng(seed)
    original = torch.tensor(rng.normal(size=(3, 17)), dtype=torch.float64)
    if seed == 0:
        original[0].zero_()
    orders = [rng.permutation([j for j in range(3) if j != i]) for i in range(3)]
    expected = original.clone()
    for i, order in enumerate(orders):
        for j in order:
            dot = expected[i] @ original[j]
            if dot < 0:
                expected[i] -= dot / (original[j] @ original[j]) * original[j]
    torch.testing.assert_close(
        projected_sum(original, orders), expected.sum(0), rtol=1e-12, atol=1e-12
    )


def test_nonconflicting_gradients_keep_sum_and_antiparallel_cancel():
    import torch

    orders = [[1, 2], [0, 2], [0, 1]]
    g = torch.eye(3)
    torch.testing.assert_close(projected_sum(g, orders), g.sum(0), rtol=0, atol=0)
    g = torch.tensor([[1.0, 0.0], [-1.0, 0.0], [0.0, 0.0]])
    torch.testing.assert_close(projected_sum(g, orders), torch.zeros(2), rtol=0, atol=0)


def test_initialization_forward_and_rng_match_joint_and_every_head_trains():
    x, mask, y = sequences(sample(), norm())
    joint = NotebookEWSBackend(17)
    initial = deepcopy(joint.state_dict())
    packed, lengths = right_pad_sequences(x, mask)
    logits = joint.model(joint.torch.from_numpy(packed), joint.torch.from_numpy(lengths))
    rng = joint.torch.get_rng_state().clone()
    model = PCGradBackend(17)
    same(joint.torch, initial["model"], model.model.state_dict())
    actual = model.model(model.torch.from_numpy(packed), model.torch.from_numpy(lengths))
    assert model.torch.equal(logits, actual)
    assert model.torch.equal(rng, model.torch.get_rng_state())
    model = PCGradBackend(17)
    loss, rows = model.train_shard(x, mask, y, seed=19)
    assert rows == len(x) and np.isfinite(loss)
    final = deepcopy(model.state_dict())
    pcgrad_rng = model.torch.get_rng_state().clone()
    joint = NotebookEWSBackend(17)
    joint.train_shard(x, mask, y, seed=19)
    assert model.torch.equal(pcgrad_rng, model.torch.get_rng_state())
    for event in range(3):
        key = f"heads.{event}.weight"
        assert not model.torch.equal(initial["model"][key], final["model"][key])
        # PCGrad alters shared parameters only; first head update is ordinary AdamW.
        model.torch.testing.assert_close(
            final["model"][key], joint.model.state_dict()[key], atol=1e-7, rtol=1e-6
        )
    assert sum(p.numel() for p in model.model.parameters()) == 1751647


def test_checkpoint_exact_resume_and_progress_recovery(tmp_path):
    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    resumed, direct = tmp_path / "resumed", tmp_path / "direct"
    for _ in range(2):
        runner.train_fit(path, manifest, norm(), resumed, "fixture", "pcgrad", 9, "cpu", 1)
    runner.train_fit(path, manifest, norm(), direct, "fixture", "pcgrad", 9, "cpu", 2)
    model = PCGradBackend(9)
    a = model.torch.load(resumed / "pcgrad/seed-9/checkpoint.pt", weights_only=True)
    b = model.torch.load(direct / "pcgrad/seed-9/checkpoint.pt", weights_only=True)
    same(model.torch, a["backend"], b["backend"])
    assert a["completed_units"] == b["completed_units"] == 2
    assert a["last_loss"] == b["last_loss"]
    with pytest.raises(ValueError, match="checkpoint mismatch"):
        runner.train_fit(path, manifest, norm(), resumed, "different", "pcgrad", 9, "cpu", 1)
    (resumed / "pcgrad/seed-9/progress.json").write_text("{}")
    # Zero training budget in train_fit means all remaining work: use a completed mock
    # state to verify recovery without running more fits.
    a["completed_units"] = 576
    model.torch.save(a, resumed / "pcgrad/seed-9/checkpoint.pt")
    assert runner.train_fit(path, manifest, norm(), resumed, "fixture", "pcgrad", 9, "cpu", 1) == (
        0,
        True,
    )
    import json

    assert (
        json.loads((resumed / "pcgrad/seed-9/progress.json").read_text())["completed_units"] == 576
    )


def test_invalid_targets_rejected():
    x, mask, y = sequences(sample(), norm())
    with pytest.raises(ValueError, match="twelve binary"):
        PCGradBackend(1).train_shard(x, mask, np.full(y.shape, np.nan), seed=1)


@pytest.mark.parametrize("complete_fits", [0, 2])
def test_all_three_fits_required_before_calibration(tmp_path, monkeypatch, complete_fits):
    import json
    import zipfile
    from pathlib import Path
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
            "independent_summary_sha256": runner.sha(control / "summary.json"),
            "diagnostic_file": "reports/gradient-conflict-2026-10-02/diagnostics.json",
            "diagnostic_sha256": runner.sha(
                Path(runner.__file__).resolve().parents[1]
                / "reports/gradient-conflict-2026-10-02/diagnostics.json"
            ),
            "control_freeze_sha256": runner.sha(control / "freeze.json"),
        },
    )
    monkeypatch.setattr(runner, "validate_archive", lambda *a: {"status": "fixture"})
    monkeypatch.setattr(runner, "load_partition", lambda *a: pytest.fail("Premature calibration"))
    args = SimpleNamespace(
        plan=plan,
        control=control,
        independent=control,
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


def test_scoring_saves_all_twelve_horizons(tmp_path, monkeypatch):
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

        def load_state_dict(self, state):
            pass

        def predict_shard(self, x, mask):
            np.testing.assert_array_equal(x, expected)
            np.testing.assert_array_equal(mask, expected_mask)
            return scores

    calls = []

    def policy(cal, rows, probabilities, event, horizon):
        column = runner.EVENTS.index(event) * 4 + (2 if horizon == 30 else 3)
        np.testing.assert_array_equal(probabilities, scores[:, column])
        calls.append((event, horizon))
        return {}, np.zeros((1, 6), dtype=int)

    p = tmp_path / "output" / "pcgrad" / "seed-9"
    p.mkdir(parents=True)
    torch.save(
        {
            "freeze_sha256": "fixture",
            "completed_units": 576,
            "backend": {},
            "parameters": 10,
            "active_parameters": 8,
            "family": "pcgrad",
            "seed": 9,
            "device": "cpu",
            "torch_version": str(torch.__version__),
            "training_seconds": 1.0,
        },
        p / "checkpoint.pt",
    )
    monkeypatch.setattr(runner, "PCGradBackend", Backend)
    monkeypatch.setattr(runner, "_chronological_halves", lambda *a: ([0], [1]))
    monkeypatch.setattr(runner, "policy_report", policy)
    report = runner.score_fit(
        path, manifest, norm(), tmp_path / "output", "fixture", "pcgrad", 9, "cpu", data, []
    )
    assert len(calls) == 6
    assert len(report["row_metrics"]) == 12
    with np.load(p / "calibration-scores.npz") as z:
        np.testing.assert_array_equal(z["targets"], data["targets"])
        np.testing.assert_array_equal(z["match_offsets"], data["match_offsets"])
        np.testing.assert_array_equal(z["probabilities"], scores)
