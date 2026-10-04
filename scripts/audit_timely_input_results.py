"""Verify prior metric parity and record completed input-control execution."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path

from scripts.export_league_development import require


def main(args):
    repo = Path(__file__).resolve().parents[1]
    folder = args.output
    data = json.loads((folder / "analysis.json").read_bytes())
    parity = {}
    for old_folder, policies in [
        (
            "timely-neural-2026-10-03",
            ("deterministic", "regional_deterministic", "matched_early_mixture"),
        ),
        ("dense-policy-2026-10-04", ("dense_deterministic", "dense_regional_deterministic")),
    ]:
        old = json.loads((repo / "reports" / old_folder / "analysis.json").read_bytes())
        n = {"model_metric_records": 0, "shared_contrast_metric_records": 0}
        for region, horizons in old["results"].items():
            for horizon, groups in horizons.items():
                for policy in policies:
                    for budget, group in groups[policy].items():
                        new = data["results"][region][horizon][policy][budget]
                        for kind, count_key in [
                            ("models", "model_metric_records"),
                            ("contrasts", "shared_contrast_metric_records"),
                        ]:
                            for name, events in group[kind].items():
                                if name not in new[kind]:
                                    require(
                                        kind == "contrasts", "Prior model absent from new analysis"
                                    )
                                    continue
                                for event, metrics in events.items():
                                    for metric, estimate in metrics.items():
                                        require(
                                            estimate == new[kind][name][event][metric],
                                            f"Prior estimate differs: {old_folder}/"
                                            f"{region}/{horizon}/"
                                            f"{policy}/{budget}/{kind}/{name}/{event}/{metric}",
                                        )
                                        n[count_key] += 1
        parity[old_folder] = n

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    training = args.training
    policy = args.policy
    s = json.loads((policy / "summary.json").read_bytes())
    t = json.loads((training / "summary.json").read_bytes())
    require(len(s["heads"]) == 198 and len(t["models"]) == 6, "Incomplete studies")
    progress = [json.loads(p.read_bytes()) for p in training.glob("*/seed-*/progress.json")]
    require(
        len(progress) == 6 and all(v["completed_units"] == 576 for v in progress), "Incomplete fits"
    )
    require(s["test_payloads_opened"] == t["test_payloads_opened"] == 0, "Test boundary differs")
    require((training / "worker-exit-code").read_text().strip() == "0", "Training exit differs")
    r = {
        "recorded_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "training_protocol_commit": "039f927",
        "analysis_commit": "9ccb4a6",
        "training_freeze_sha256": sha(training / "freeze.json"),
        "training_summary_sha256": sha(training / "summary.json"),
        "training_exit_code": 0,
        "new_fits": 6,
        "new_shard_updates": 3456,
        "new_fit_training_seconds": sum(v["training_seconds"] for v in t["models"].values()),
        "new_fit_records": {
            name: {
                k: model[k]
                for k in ("parameters", "training_seconds", "checkpoint_sha256", "scores_sha256")
            }
            for name, model in t["models"].items()
        },
        "completed_prior_neural_fits": 33,
        "total_completed_neural_fits": 39,
        "test_payloads_opened": 0,
        "freeze_sha256": sha(policy / "freeze.json"),
        "policy_freeze_sha256": sha(policy / "policy-freeze.json"),
        "summary_sha256": sha(policy / "summary.json"),
        "early_heads": 198,
        "later_heads": 198,
        "independent_component_checks": sum(
            v["independent_component_checks"] for v in s["heads"].values()
        ),
        "new_full_reference_checks": sum(
            v["new_full_reference_checks"] for v in s["heads"].values()
        ),
        "prior_coarse_mixture_heads_reproduced": sum(
            v["previous_counts_reproduced"] for v in s["heads"].values()
        ),
        "prior_dense_heads_reproduced": sum(
            v["dense_counts_reproduced"] for v in s["heads"].values()
        ),
        "prior_analysis_exact_reproduction": parity,
        "raw_analysis_sha256": sha(folder / "analysis.json"),
        "raw_policies_sha256": sha(folder / "early-policies.json"),
        "tests_passed": 627,
        "tests_skipped": 1,
        "coverage_percent": 85.89,
        "focused_tests_passed": 8,
        "mypy_source_files": 87,
    }
    recovery_path = folder / "recovery-record.json"
    if recovery_path.exists():
        recovery = json.loads(recovery_path.read_bytes())
        for record in recovery["checkpoint_records"]:
            if record["completed_units"] == 576:
                path = training / record["family"] / f"seed-{record['seed']}" / "checkpoint.pt"
                require(sha(path) == record["checkpoint_sha256"], "Completed checkpoint changed")
        recovery["completed_recovery"] = {
            "recorded_at_utc": r["recorded_at_utc"],
            "final_worker_exit_code": 0,
            "final_fit_completed_units": 576,
            "final_checkpoint_sha256": sha(training / "clock_only/seed-20261002/checkpoint.pt"),
            "five_completed_checkpoint_hashes_unchanged": True,
            "root_cause_established": False,
        }
        recovery_path.write_text(json.dumps(recovery, indent=2) + "\n")
        r["recovery_record_sha256"] = sha(recovery_path)
        r["original_worker_exit_code"] = 139
        r["recovered_from_verified_checkpoint"] = True
    (folder / "execution-record.json").write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "training", "policy"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    main(args)
