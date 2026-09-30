#!/usr/bin/env python3
"""Recover saved MSc evidence without executing a notebook, contacting Riot or fitting a model."""

import ast
import hashlib
import json
import re
from pathlib import Path


def source(cell):
    return "".join(cell.get("source", []))


def outputs(cell):
    return "\n".join(
        "".join(out.get("text", out.get("data", {}).get("text/plain", [])))
        for out in cell.get("outputs", [])
    )


def recover(repo):
    legacy = repo / "legacy/msc-v1"
    paths = [*sorted(legacy.glob("*.ipynb")), legacy / "LOL Final Report.pdf"]
    hashes = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    canonical = json.loads((legacy / "EWS_model_building.ipynb").read_bytes())
    alternate = json.loads((legacy / "EWS - model building.ipynb").read_bytes())

    def code_hash(notebook):
        code = "\n".join(source(c) for c in notebook["cells"] if c["cell_type"] == "code")
        return hashlib.sha256(code.encode()).hexdigest()

    require_same = code_hash(canonical) == code_hash(alternate)
    if not require_same:
        raise ValueError("Notebook versions no longer contain identical modeling code")
    tables = {}
    for name, index in (("random_forest", 17), ("mlp", 38), ("leagueews", 71)):
        cell = canonical["cells"][index]
        if 'groupby("event")' not in source(cell):
            raise ValueError("Saved metric aggregation changed; inspect before reporting")
        rows = re.findall(
            r"^\s*\d+\s+(Baron|Dragon|Teamfight)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*$",
            outputs(cell),
            re.M,
        )
        if len(rows) != 3:
            raise ValueError("Could not recover the complete saved metric table")
        tables[name] = {
            event.lower(): dict(
                zip(("roc_auc", "precision_at_0_5", "brier"), map(float, values), strict=True)
            )
            for event, *values in rows
        }
    # Parse the stored best-hyperparameter literal; never evaluate executable code.
    tuning = outputs(canonical["cells"][63])
    best = ast.literal_eval(re.search(r"Best hyperparameters found:\s*(\{[^\n]+\})", tuning)[1])
    eda = json.loads((legacy / "EWS_Exploratory_data_analysis.ipynb").read_bytes())
    shape = ast.literal_eval(outputs(eda["cells"][13]).strip())
    sequence_output = outputs(canonical["cells"][8])
    raw_shape = ast.literal_eval(re.search(r"Raw sequences:\s*(\([^\n]+?\))", sequence_output)[1])
    augmented_shape = ast.literal_eval(
        re.search(r"Augmented sequences:\s*(\([^\n]+?\))", sequence_output)[1]
    )
    partition_output = outputs(canonical["cells"][11])
    counts = {
        name: int(re.search(rf"{prefix}:\s*\((\d+),", partition_output)[1])
        for name, prefix in (("train", "Train"), ("validation", "Val"), ("test", "Test"))
    }
    return {
        "schema_version": "league-ews-msc-source-review-v1",
        "source_sha256": hashes,
        "model_code_identical_across_notebook_versions": require_same,
        "model_code_sha256": code_hash(canonical),
        "saved_dataset_shape": list(shape),
        "saved_raw_sequence_shape": list(raw_shape),
        "saved_augmented_sequence_shape": list(augmented_shape),
        "saved_partition_sequences": counts,
        "saved_best_hyperparameters": best,
        "saved_metrics_mean_over_horizons_10_20_30": tables,
        "metric_scope": "Recorded notebook outputs; not new fits or valid generalization estimates",
        "new_real_data_fits": 0,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = recover(root)
    output = root / "reports/notebook-source-review-2026-09-30.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Recovered original evidence: {output}")
