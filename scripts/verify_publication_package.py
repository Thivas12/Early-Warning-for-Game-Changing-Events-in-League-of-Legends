"""Independently verify public aggregate claims, timing summaries and PDF bindings."""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run():
    root = Path(__file__).resolve().parents[1]
    output = root / "reports/publication-package-2026-10-07"
    evidence = json.loads((output / "evidence.json").read_bytes())
    sources = {}
    for relative, expected in evidence["source_sha256"].items():
        path = root / relative
        require(sha(path) == expected, "Scientific source hash changed")
        sources[relative] = json.loads(path.read_bytes())
    require(len(evidence["effects"]) == 8, "Wrong effect inventory")
    for record in evidence["effects"]:
        original = sources[record["source"]]
        for key in record["json_pointer"].strip("/").split("/"):
            original = original[key]
        require(record["recall_difference_pp"] == 100 * original["mean"], "Estimate changed")
        require(record["ci95_pp"] == [100 * x for x in original["ci95"]], "Interval changed")
        require(record["seeds_pp"] == [100 * x for x in original["seeds"]], "Seeds changed")
    runtime = json.loads((output / "runtime.json").read_bytes())
    require(runtime["status"] == "complete-system-microbenchmark", "Incomplete runtime")
    require(
        runtime["test_payloads_opened"] == runtime["new_outcome_evaluations"] == 0,
        "Benchmark crossed outcome boundary",
    )
    require("TF32 disabled" in runtime["precision"], "Precision correction missing")
    expected = {
        (a, s, d, b)
        for a in ("leagueews", "tcn")
        for s in (20260930, 20261001, 20261002)
        for d in ("cpu", "cuda")
        for b in (1, 128)
    }
    observed = set()
    for record in runtime["records"]:
        key = tuple(record[k] for k in ("architecture", "seed", "device", "batch"))
        require(key not in observed, "Duplicate runtime cell")
        observed.add(key)
        samples = record["samples_ms"]
        require(len(samples) == record["calls"] == 100, "Incomplete timing samples")
        require(all(math.isfinite(x) and x > 0 for x in samples), "Invalid timing")
        median = statistics.median(samples)
        p95 = statistics.quantiles(samples, n=20, method="inclusive")[18]
        for left, right in (
            (median, record["median_ms"]),
            (p95, record["p95_ms"]),
            (1000 * record["batch"] / median, record["windows_per_second_at_median"]),
        ):
            require(math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12), "Wrong summary")
    require(observed == expected, "Incomplete architecture/seed/device/batch inventory")
    for relative, expected_hash in runtime["sources"].items():
        require(sha(root / relative) == expected_hash, "Frozen runtime source changed")
    documents = json.loads((output / "document-checks.json").read_bytes())
    for record in documents:
        require(sha(root / record["path"]) == record["sha256"], "PDF changed after check")
        require(record["pages"] in (2, 7), "Unexpected document pagination")
    checked_links = 0
    for relative in (
        "docs/leagueews-case-study.md",
        "docs/leagueews-confirmation-protocol.md",
        "reports/publication-package-2026-10-07/reproduce.md",
        "paper/leagueews-2026-10/README.md",
    ):
        path = root / relative
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if target.startswith("https://"):
                continue
            require((path.parent / target.split("#")[0]).is_file(), "Broken local publication link")
            checked_links += 1
    result = {
        "status": "passed-public-artifact-verification",
        "exact_source_effects": 8,
        "runtime_cells": 24,
        "timing_samples": 2400,
        "documents": 2,
        "local_links": checked_links,
        "new_outcome_evaluations": 0,
        "scope": "Source extraction, independent timing arithmetic, inventory and hashes",
    }
    (output / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    run()
