"""Run the unchanged runtime protocol with explicit IEEE float32 convolution math."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from league_ews.coordination_experiment import write_json
from scripts import benchmark_publication_inference as base
from scripts.export_league_development import require


def run(args):
    repo = Path(__file__).resolve().parents[1]
    relative = str(Path(__file__).resolve().relative_to(repo))
    committed = subprocess.run(
        ["git", "show", f"{args.commit}:{relative}"], cwd=repo, check=True, capture_output=True
    ).stdout
    require(committed == Path(__file__).read_bytes(), "Uncommitted benchmark wrapper")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch

    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_float32_matmul_precision("highest")
    base.PROTOCOL = "reports/publication-package-2026-10-07/runtime-protocol-v2.md"
    base.run(args)
    path = args.output / "runtime.json"
    result = json.loads(path.read_bytes())
    result["sources"][relative] = hashlib.sha256(committed).hexdigest()
    result["precision"] = "IEEE float32; matmul and cuDNN TF32 disabled; no autocast"
    result["prior_aborted_run"] = "league-publication-runtime-v1; CPU/CUDA parity; preserved"
    write_json(path, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    run(parser.parse_args())
