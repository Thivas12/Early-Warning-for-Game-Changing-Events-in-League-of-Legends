from __future__ import annotations

import subprocess

from league_ews.provenance import source_provenance


def test_source_provenance_reads_clean_repository(tmp_path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "test"], cwd=tmp_path, check=True)

    result = source_provenance(tmp_path)

    assert len(result["git_commit"]) == 40
    assert result["tracked_files_dirty"] is False


def test_source_provenance_handles_non_repository(tmp_path) -> None:
    result = source_provenance(tmp_path)
    assert result == {"git_commit": None, "tracked_files_dirty": True}
