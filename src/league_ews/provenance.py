"""Source provenance that degrades safely outside a Git checkout."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(arguments: list[str], root: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def source_provenance(root: str | Path | None = None) -> dict[str, object]:
    """Return the source commit and tracked-dirty state when Git is available."""

    source_root = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    revision = _git(["rev-parse", "HEAD"], source_root)
    status = _git(["status", "--porcelain", "--untracked-files=no"], source_root)
    commit = revision.stdout.strip() if revision is not None and revision.returncode == 0 else None
    dirty = status is None or status.returncode != 0 or bool(status.stdout.strip())
    return {"git_commit": commit, "tracked_files_dirty": dirty}
