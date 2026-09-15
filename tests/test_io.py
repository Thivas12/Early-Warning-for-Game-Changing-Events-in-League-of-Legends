from __future__ import annotations

import hashlib

import pandas as pd

from league_ews.io import load_legacy_csv, sha256_file


def test_sha256_file_streams_known_content(tmp_path) -> None:
    path = tmp_path / "sample.bin"
    path.write_bytes(b"league-ews")
    assert sha256_file(path, chunk_size=3) == hashlib.sha256(b"league-ews").hexdigest()


def test_legacy_loader_compacts_supported_types(tmp_path) -> None:
    path = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "match_id": ["m1", "m1"],
            "t": [0, 10],
            "gold_diff": [1.5, 2.5],
            "y_baron_10": [0, 1],
            "ignored": [4.0, 5.0],
        }
    ).to_csv(path, index=False)

    frame = load_legacy_csv(
        path,
        nrows=1,
        usecols=("match_id", "t", "gold_diff", "y_baron_10"),
    )

    assert frame.columns.tolist() == ["match_id", "t", "gold_diff", "y_baron_10"]
    assert len(frame) == 1
    assert str(frame["gold_diff"].dtype) == "float32"
    assert frame["t"].dtype.itemsize < 8
    assert frame["y_baron_10"].dtype.itemsize < 8
