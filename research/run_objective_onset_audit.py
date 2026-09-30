"""Run the observational label audit on one or more Gem replay JSON exports."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.objective_onset import audit_match


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    records = []
    seen: set[str] = set()
    for path in args.inputs:
        raw = path.read_bytes()
        result = audit_match(json.loads(raw))
        if result["match_id"] in seen:
            raise ValueError("Duplicate match: cannot count duplicate exports as replication")
        seen.add(result["match_id"])
        records.append({"input_sha256": hashlib.sha256(raw).hexdigest(), "audit": result})
    report = {
        "schema": "objective-onset-audit-v1",
        "status": "exploratory_measurement_audit_not_forecasting_validation",
        "source_revision": args.source_revision,
        "source_hashes": {
            name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
            for name in ("research/objective_onset.py", "research/run_objective_onset_audit.py")
        },
        "independent_matches": len(records),
        "reports": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    for record in records:
        audit = record["audit"]
        scenario = audit["scenarios"][1]
        print(
            f"Match {audit['match_id']}: {len(scenario['episodes'])} damage episodes; "
            f"{audit['terminal_events']} kills"
        )
        for metric in scenario["metrics"]:
            if metric["delivery_delay_nominal_seconds"] == 0:
                print(
                    {
                        "minimum_lead": metric["minimum_lead_nominal_seconds"],
                        "completion_recall": metric["completion"]["recall"],
                        "onset_recall": metric["damage_onset"]["recall"],
                        "unmatched_completion_alarms": metric["completion"]["unmatched_alarms"],
                    }
                )


if __name__ == "__main__":
    main()
