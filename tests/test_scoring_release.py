"""Prevent unattended scoring while analysis-commit approval is pending."""

import json
import subprocess

import pytest

from scripts import run_clock_history_released as gated
from scripts import scoring_release as release
from tests.test_clock_history import fixture_run


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


@pytest.fixture
def committed(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "analysis.py").write_text("# fixed analysis\n")
    plan = repo / "plan.json"
    plan.write_text("{}\n")
    git(repo, "add", "analysis.py", "plan.json")
    git(repo, "commit", "-qm", "Fixture analysis")
    commit = git(repo, "rev-parse", "HEAD")
    study = tmp_path / "study"
    study.mkdir()
    (study / "freeze.json").write_text('{"training": "fixture"}\n')
    return repo, study, plan, commit, ["analysis.py"]


def test_committed_release_verifies_and_cannot_be_overwritten(committed):
    repo, study, plan, _commit, paths = committed
    with pytest.raises(ValueError, match="Awaiting"):
        release.verify(repo, study, plan, paths)
    result = release.issue(*committed)
    assert result == release.verify(repo, study, plan, paths)
    with pytest.raises(FileExistsError):
        release.issue(*committed)
    with pytest.raises(ValueError, match="binding differs"):
        release.verify(repo, study, plan, [])


@pytest.mark.parametrize("changed", ["analysis.py", "plan.json", "freeze.json"])
def test_release_rejects_source_plan_or_training_changes(committed, changed):
    repo, study, plan, _commit, paths = committed
    release.issue(*committed)
    path = (study if changed == "freeze.json" else repo) / changed
    path.write_text(path.read_text() + "changed\n")
    with pytest.raises(ValueError, match="differs"):
        release.verify(repo, study, plan, paths)


def test_release_cannot_be_backfilled_after_scoring(committed):
    _, study, _, _, _ = committed
    p = study / "clock_history/seed-1"
    p.mkdir(parents=True)
    (p / "calibration-scores.partial").write_bytes(b"partial")
    with pytest.raises(ValueError, match="Scoring already started"):
        release.issue(*committed)
    assert not (study / "analysis-release.json").exists()


def test_release_rejects_uncommitted_analysis(committed):
    repo, study, _, _, _ = committed
    (repo / "analysis.py").write_text("# uncommitted change\n")
    with pytest.raises(ValueError, match="committed bytes"):
        release.issue(*committed)
    assert not (study / "analysis-release.json").exists()


def test_last_update_stops_before_scoring_and_missing_release_preserves_checkpoint(
    tmp_path, monkeypatch
):
    args = fixture_run(tmp_path, monkeypatch)
    trained = []

    def train(*a):
        p = args.output / a[5] / f"seed-{a[6]}"
        p.mkdir(parents=True, exist_ok=True)
        (p / "checkpoint.pt").write_bytes(b"preserved fixture")
        (p / "progress.json").write_text(json.dumps({"completed_units": 576}))
        trained.append(a[6])
        return 576, True

    monkeypatch.setattr(gated.original, "train_fit", train)
    monkeypatch.setattr(
        gated.original, "load_partition", lambda *_: pytest.fail("Premature calibration scoring")
    )
    assert gated.run(args)["status"] == "paused-resume-same-command"
    assert len(trained) == 3
    checkpoints = {p: p.read_bytes() for p in args.output.glob("*/seed-*/checkpoint.pt")}
    assert gated.run(args) == {"status": "awaiting-committed-analysis-release", "new_scores": 0}
    assert {p: p.read_bytes() for p in checkpoints} == checkpoints
    # An invalid release must fail before entering the original runner.
    (args.output / "analysis-release.json").write_text("{}")
    monkeypatch.setattr(gated, "__file__", str(tmp_path / "scripts/run.py"))
    with pytest.raises(KeyError):
        gated.run(args)
    assert len(trained) == 3
