"""Checkpoint identity, atomic failure preservation and all-fit scoring release."""

import json
import zipfile
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import run_timely_optimization as runner
from scripts.timely_neural_targets import fitted_targets
from scripts.timely_optimization_backend import TimelyOptimizationBackend
from tests.test_compact_research import archive, norm, sample
from tests.test_task_sharing import same


@pytest.mark.parametrize("family", runner.FAMILIES)
def test_checkpoint_resume_recovers_progress_and_binds_variant(tmp_path, family):
    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    output, direct = tmp_path / "resumed", tmp_path / "direct"
    runner.train_fit(path, manifest, norm(), output, "fixture", family, 9, "cpu", 1)
    folder = output / family / "seed-9"
    (folder / "progress.json").write_text("{}")
    runner.train_fit(path, manifest, norm(), output, "fixture", family, 9, "cpu", 1)
    runner.train_fit(path, manifest, norm(), direct, "fixture", family, 9, "cpu", 2)
    torch = TimelyOptimizationBackend(9, variant=family).torch
    a = torch.load(folder / "checkpoint.pt", weights_only=True)
    b = torch.load(direct / family / "seed-9/checkpoint.pt", weights_only=True)
    same(torch, a["backend"], b["backend"])
    assert a["completed_units"] == b["completed_units"] == 2
    assert json.loads((folder / "progress.json").read_bytes())["completed_units"] == 2
    assert a["last_loss"] == b["last_loss"]
    a["variant_specification"] = runner.VARIANTS["original_sum"]
    torch.save(a, folder / "checkpoint.pt")
    with pytest.raises(ValueError, match="checkpoint mismatch"):
        runner.train_fit(path, manifest, norm(), output, "fixture", family, 9, "cpu", 1)


def test_training_uses_useful_targets_and_preserves_last_finite_checkpoint(tmp_path, monkeypatch):
    data = sample()
    path, entry = archive(tmp_path, data)
    manifest = {"shards": [entry] * 48}
    original = TimelyOptimizationBackend.train_shard
    calls = []

    def checked(self, x, mask, target, **kwargs):
        np.testing.assert_array_equal(target, fitted_targets(data))
        calls.append(True)
        return original(self, x, mask, target, **kwargs)

    monkeypatch.setattr(TimelyOptimizationBackend, "train_shard", checked)
    output = tmp_path / "study"
    runner.train_fit(path, manifest, norm(), output, "fixture", "equal_sum", 9, "cpu", 1)
    checkpoint = output / "equal_sum/seed-9/checkpoint.pt"
    binding = runner.sha(checkpoint)
    assert calls == [True]

    def invalid(self, *args, **kwargs):
        with self.torch.no_grad():
            next(self.model.parameters()).fill_(float("nan"))
        return 0.0, 18

    monkeypatch.setattr(TimelyOptimizationBackend, "train_shard", invalid)
    with pytest.raises(ValueError, match="Nonfinite parameters"):
        runner.train_fit(path, manifest, norm(), output, "fixture", "equal_sum", 9, "cpu", 1)
    assert runner.sha(checkpoint) == binding


def fixture_run(tmp_path, monkeypatch):
    import torch

    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    with zipfile.ZipFile(path, "a") as z:
        z.writestr("manifest.json", json.dumps(manifest))
    control = tmp_path / "control"
    control.mkdir()
    runner.write_json(control / "normalizer.json", runner.fit_normalizer(path, manifest))
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
    runner.write_json(control / "summary.json", {"fixture": True})
    plan = tmp_path / "plan.json"
    runner.write_json(
        plan,
        {
            "events": list(runner.EVENTS),
            "families": list(runner.FAMILIES),
            "seeds": list(runner.SEEDS),
            "original_plan": runner.PLAN,
            "variants": runner.VARIANTS,
            "analysis_sources": ["fixture.py"],
        },
    )
    monkeypatch.setattr(runner, "verify_control", lambda *_: frozen)
    monkeypatch.setattr(runner, "validate_archive", lambda *_: {"fixture": True})
    return SimpleNamespace(
        archive=path,
        control=control,
        plan=plan,
        output=tmp_path / "output",
        device="cpu",
        preflight=False,
        max_new_shards=0,
    )


def test_scores_preserve_both_target_definitions_and_fitted_checkpoint(tmp_path):
    data = sample()
    path, entry = archive(tmp_path, data)
    family = "equal_pcgrad"
    output = tmp_path / "study"
    runner.train_fit(path, {"shards": [entry] * 48}, norm(), output, "fixture", family, 9, "cpu", 1)
    folder = output / family / "seed-9"
    torch = TimelyOptimizationBackend(9, variant=family).torch
    state = torch.load(folder / "checkpoint.pt", weights_only=True)
    # This is only a tiny scoring-interface fixture, not an empirical fitted model.
    state["completed_units"] = 576
    torch.save(state, folder / "checkpoint.pt")
    binding = runner.sha(folder / "checkpoint.pt")
    manifest = {"shards": [{}] * 48 + [{**entry, "partition": "calibration"}]}
    report = runner.score_fit(path, manifest, norm(), output, "fixture", family, 9, "cpu", data, [])
    assert runner.sha(folder / "checkpoint.pt") == report["checkpoint_sha256"] == binding
    assert "warnings" not in report and report["test_payloads_opened"] == 0
    with np.load(folder / "calibration-scores.npz") as z:
        np.testing.assert_array_equal(z["targets"], data["targets"])
        np.testing.assert_array_equal(z["fitted_targets"], fitted_targets(data))
        np.testing.assert_array_equal(z["match_offsets"], data["match_offsets"])
        assert z["probabilities"].shape == data["targets"].shape
        assert np.isfinite(z["probabilities"]).all()


def test_all_nine_fits_and_valid_committed_analysis_required_before_scoring(tmp_path, monkeypatch):
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
    assert runner.run(args)["status"] == "complete-exploratory-timely-optimization-predictions"
    assert len(scored) == 9
