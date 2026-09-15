"""Input/output helpers with deterministic provenance."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from league_ews.constants import LEGACY_LABEL_COLUMNS, TIME_COLUMN


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest without loading a large dataset into memory."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_legacy_csv(
    path: str | Path,
    *,
    nrows: int | None = None,
    usecols: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Load the legacy CSV with compact, deterministic dtypes."""

    selected = tuple(usecols) if usecols is not None else None
    frame = pd.read_csv(path, nrows=nrows, usecols=selected, low_memory=False)
    if TIME_COLUMN in frame:
        frame[TIME_COLUMN] = pd.to_numeric(frame[TIME_COLUMN], downcast="integer")
    for column in LEGACY_LABEL_COLUMNS:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], downcast="integer")
    float_columns = frame.select_dtypes(include=["float64"]).columns
    if len(float_columns):
        frame[float_columns] = frame[float_columns].astype("float32")
    return frame
