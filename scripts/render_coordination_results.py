"""Render the user-supplied real aggregate summary, with reproducible arithmetic."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def render(source: Path) -> str:
    raw = source.read_bytes()
    report = json.loads(raw)
    if report["status"] != "complete-exploratory-calibration-screen":
        raise ValueError("Expected a completed real coordination screen")
    models = report["models"]
    for model in models.values():
        e = model["evaluation"]
        if (
            model["freeze_sha256"] != report["freeze_sha256"]
            or abs(e["timely_event_recall"] * e["events"] - e["timely_matched_events"]) > 1e-6
            or abs(e["false_alerts_per_game"] * e["matches"] - (e["alerts"] - e["matched_events"]))
            > 1e-6
        ):
            raise ValueError("Inconsistent aggregate counts or freeze")
    e = models["coordination"]["evaluation"]
    primary = report["paired_comparisons"]["coordination-minus-history"]
    lo, hi = primary["percentile_95_intervals"]["timely_recall_difference"]
    lines = [
        "# Real coordination screen: 29 September 2026",
        "",
        "Source: user-executed WSL experiment; this workspace received its aggregate",
        "summary and checked the reported arithmetic. No private model was refitted here.",
        "The source is preserved in `coordination-screen-real-2026-09-29.json`.",
        "",
        f"- Source SHA-256: `{hashlib.sha256(raw).hexdigest()}`.",
        f"- Runtime freeze SHA-256: `{report['freeze_sha256']}`.",
        f"- Evaluation: {e['matches']:,} matches, {e['events']:,} Dragon onsets.",
        f"- Test matches reported unread: {report['test_matches_unread']:,}.",
        "- Timely lead: 20-60 seconds, inclusive. All-event recall is primary.",
        "- All comparisons remain exploratory after earlier calibration inspection.",
        "",
        "| Model | Timely recall | False alerts/match | Timely precision | AP (within60) |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ("b3", "snapshot", "history", "coordination"):
        m = models[name]
        v = m["evaluation"]
        lines.append(
            f"| {name} | {v['timely_event_recall']:.2%} | "
            f"{v['false_alerts_per_game']:.3f} | {v['timely_precision']:.2%} | "
            f"{m['evaluation_row_metrics']['average_precision']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Primary finding",
            "",
            f"Coordination minus history: **{100 * primary['timely_recall_difference']:+.3f} "
            f"percentage points** of timely recall; paired 95% interval "
            f"**[{100 * lo:+.3f}, {100 * hi:+.3f}] points**.",
            "This does not establish an incremental benefit from these movement summaries",
            "at the tested capacities. It does not rule out every learned coordination model.",
            "All selected capacities were the largest tested value (31 leaves).",
            "",
            "| Secondary contrast | Recall difference (points) | Paired 95% interval |",
            "|---|---:|---:|",
        ]
    )
    for name in ("snapshot-minus-b3", "history-minus-snapshot"):
        c = report["paired_comparisons"][name]
        a, b = c["percentile_95_intervals"]["timely_recall_difference"]
        lines.append(
            f"| {name} | {100 * c['timely_recall_difference']:+.3f} | "
            f"[{100 * a:+.3f}, {100 * b:+.3f}] |"
        )
    late = e["matched_events"] - e["timely_matched_events"]
    false = e["alerts"] - e["matched_events"]
    opportunities = e["timely_opportunities"]
    lines.extend(
        [
            "",
            "These intervals condition on fitted models and tuned policies. They do not",
            "include refit, repeated-player or future-patch uncertainty. Both secondary",
            "gains also increase false alerts; a common budget is not identical realized burden.",
            "No original M1 or legacy-paper scores are substituted as matched baselines.",
            "",
            "## Timing and observation limits",
            "",
            f"Coordination generated {e['timely_matched_events']:,} timely, {late:,} late and",
            f"{false:,} false alerts. Only {e['timely_precision']:.2%} of alerts were timely.",
            f"False plus late burden was {(false + late) / e['matches']:.3f} per match, despite",
            "meeting the mean false-only budget. Late alerts were always separately defined,",
            "not hidden in the count of false alerts; the follow-up changes the primary budget",
            "explicitly rather than reinterpreting this run.",
            "",
            f"Only {opportunities:,}/{e['events']:,} events ({opportunities / e['events']:.2%})",
            "had an observation in their 20-60-second warning window. This is an upper bound",
            "for policies that alert only at observed frames, not an attainable oracle score.",
            "Cooldown and matching can lower the attainable bound further.",
            f"Coordination caught {e['opportunity_conditional_timely_recall']:.2%} "
            "of eligible events.",
            "No claim about second-by-second paths or player intent follows from endpoint motion.",
            "",
            "## Next experiment",
            "",
            "Test whether separating late and timely outcomes during training improves the",
            "useful-warning trade-off. See `docs/timely-objective-screen.md` for the new",
            "four-fit protocol, two explicit budgets and fixed primary contrast. Interval",
            "targets are not claimed as an original algorithm. Test payloads stay sealed.",
            "",
            "Reproduce this document:",
            "",
            "```bash",
            "uv run --no-sync python scripts/render_coordination_results.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=Path("reports/coordination-screen-real-2026-09-29.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("reports/coordination-screen-real-2026-09-29.md")
    )
    args = parser.parse_args()
    args.output.write_text(render(args.source))


if __name__ == "__main__":
    main()
