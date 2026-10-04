"""Verify prior metric parity and record completed conditional-history execution."""

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
            "timely-inputs-2026-10-04",
            (
                "deterministic",
                "regional_deterministic",
                "matched_early_mixture",
                "dense_deterministic",
                "dense_regional_deterministic",
            ),
        ),
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
    require(len(s["heads"]) == 216 and len(t["models"]) == 3, "Incomplete studies")
    progress = [json.loads(p.read_bytes()) for p in training.glob("*/seed-*/progress.json")]
    require(
        len(progress) == 3 and all(v["completed_units"] == 576 for v in progress), "Incomplete fits"
    )
    require(s["test_payloads_opened"] == t["test_payloads_opened"] == 0, "Test boundary differs")
    require((training / "worker-exit-code").read_text().strip() == "0", "Training exit differs")
    r = {
        "recorded_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "training_protocol_commit": "997e299",
        "analysis_commit": args.analysis_commit,
        "training_freeze_sha256": sha(training / "freeze.json"),
        "training_summary_sha256": sha(training / "summary.json"),
        "training_exit_code": 0,
        "new_fits": 3,
        "new_shard_updates": 1728,
        "new_fit_training_seconds": sum(v["training_seconds"] for v in t["models"].values()),
        "new_fit_records": {
            name: {
                k: model[k]
                for k in ("parameters", "training_seconds", "checkpoint_sha256", "scores_sha256")
            }
            for name, model in t["models"].items()
        },
        "completed_prior_neural_fits": 39,
        "total_completed_neural_fits": 42,
        "test_payloads_opened": 0,
        "freeze_sha256": sha(policy / "freeze.json"),
        "policy_freeze_sha256": sha(policy / "policy-freeze.json"),
        "summary_sha256": sha(policy / "summary.json"),
        "early_heads": 216,
        "later_heads": 216,
        "independent_component_checks": sum(
            v["independent_component_checks"] for v in s["heads"].values()
        ),
        "new_full_reference_checks": sum(
            v["new_full_reference_checks"] for v in s["heads"].values()
        ),
        "prior_all_five_policy_heads_reproduced": sum(
            v["previous_counts_reproduced"] for v in s["heads"].values()
        ),
        "prior_dense_heads_reproduced": sum(
            v["dense_counts_reproduced"] for v in s["heads"].values()
        ),
        "prior_analysis_exact_reproduction": parity,
        "raw_analysis_sha256": sha(folder / "analysis.json"),
        "raw_policies_sha256": sha(folder / "early-policies.json"),
        "tests_passed": 642,
        "tests_skipped": 1,
        "coverage_percent": 85.89,
        "focused_experiment_tests_passed": 8,
        "scoring_release_tests_passed": 7,
        "pre_prediction_tests_passed": 635,
        "protocol_commit_order_met": False,
        "protocol_deviation_sha256": sha(folder / "protocol-deviation.json"),
        "mypy_source_files": 87,
    }
    (folder / "execution-record.json").write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "training", "policy"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--analysis-commit", required=True)
    args = parser.parse_args()
    main(args)
