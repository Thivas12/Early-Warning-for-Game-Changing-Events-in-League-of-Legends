"""Render the complete third-screen record without hiding unsuccessful controls."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd


def main() -> None:
    root = Path("reports")
    results = json.loads((root / "command-anticipation-results-2026-09-30.json").read_text())
    quality = json.loads((root / "command-anticipation-quality-2026-09-30.json").read_text())
    verification = json.loads((root / "command-stream-verification-2026-09-30.json").read_text())
    secondary = json.loads((root / "command-first-contact-2026-09-30.json").read_text())
    accepted = [r for r in quality["matches"] if r["status"] == "accepted"]
    fresh = [r for r in accepted if r["split"] == "evaluation"]
    excluded = Counter(
        r["reason"].split(":")[0] for r in quality["matches"] if r["status"] != "accepted"
    )
    meta = pd.read_parquet(
        "data/external/betty/matches.parquet", columns=["match_id", "league_name"]
    )
    names = dict(zip(meta.match_id.astype(str), meta.league_name, strict=True))
    leagues = Counter(names[str(r["match_id"])] for r in fresh)
    lines = [
        "# Command-stream anticipation: completed third public-data screen",
        "",
        f"**Advancement gate: {'PASS' if results['screen_advances'] else 'FAIL'}. "
        "No breakthrough or state-of-the-art claim.**",
        "",
        "This experiment tests whether recorded movement destinations improve prediction of",
        "Roshan damage onsets beyond observed positions and command frequency. It was",
        "declared after two unsuccessful feature studies. The earlier results remain intact.",
        "",
        "## Data actually used",
        "",
        "Exactly 250 new matches were selected before download, disjoint from all 500",
        f"previously selected matches and ten schema-development matches. {len(fresh)} fresh",
        "matches passed the unchanged base checks and new command checks. Development",
        f"retained {sum(r['split'] == 'train' for r in accepted)} training and",
        f"{sum(r['split'] == 'calibration' for r in accepted)} calibration matches.",
        "",
        "Across this experiment's retained development and evaluation data: "
        f"{sum(r['hero_rows'] for r in accepted):,}",
        f"hero-state rows, {sum(r['command_rows'] for r in accepted):,} live-game command rows,",
        f"and {sum(r['decision_rows'] for r in accepted):,} decision rows. These are repeated",
        "observations within matches, not independent samples. The original development",
        "matches are reused and must not be counted again as new data.",
        "",
        f"Fresh evaluation: {results['fresh_targets']} quiet-gap onsets and",
        f"{results['fresh_decision_rows']:,} decisions. Quality exclusions: {dict(excluded)}.",
        "",
        f"Retained evaluation league counts: {dict(leagues)}. Source PROFESSIONAL labels",
        "do not establish elite-tournament or independent-team generalization.",
        "",
        "## Frozen comparison",
        "",
        "The lead window is 20-60 seconds, cooldown 60 seconds, and each unmatched",
        "alarm counts toward the one-per-match budget. All thresholds are selected on",
        "calibration only. One fixed seed is used; previous seed repetitions produced",
        "identical policies. Both selection and model weights were frozen before scoring.",
        f"Calibration selected **{results['selected_comparator']}** as the comparator.",
        f"Original control calibration reproduced: {results['original_controls_reproduced']}.",
        "",
        "| Model | Inputs | Calibration hits | Fresh onset hits | Recall | "
        "Unmatched/match | Hits with 5s delivery delay |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results["models"]:
        s, c = r["onset"], r["calibration"]
        lines.append(
            f"| {r['name']} | {r['features']} | {c['hits']}/{c['targets']} | "
            f"{s['hits']}/{s['targets']} | {s['recall']:.2%} | {s['unmatched_per_match']:.3f} | "
            f"{r['onset_with_5s_delivery_delay']['hits']} |"
        )
    lines += ["", "Primary candidate: **command_destination**. Paired recall differences:", ""]
    for c in results["comparisons"]:
        m, d = c["match_interval"], c["day_interval"]
        lines.append(
            f"- Versus {c['comparator']}: {100 * m['recall_difference']:+.2f} percentage points; "
            f"match-bootstrap 95% [{100 * m['percentile_95'][0]:+.2f}, "
            f"{100 * m['percentile_95'][1]:+.2f}], calendar-day "
            f"[{100 * d['percentile_95'][0]:+.2f}, {100 * d['percentile_95'][1]:+.2f}] "
            f"({d['units']} days). Pass: {c['passes']}."
        )
    strongest = max(results["models"][:5], key=lambda r: r["onset"]["hits"])
    lines += [
        "",
        f"The strongest fresh-test baseline by hits was {strongest['name']} "
        f"with {strongest['onset']['hits']} hits.",
        "That descriptive observation does not replace the calibration-selected comparator.",
        "The intervals are exploratory percentile bootstraps, not a multiple-experiment",
        "error guarantee. Day clusters do not establish independence between teams.",
        "",
        "## First engagement versus re-engagement",
        "",
        "This secondary check was declared before fitting. It counts only the first",
        "positive damage in each Roshan life, resetting after a Roshan death. All alarms",
        "and thresholds stay fixed; there is no recalibration to this stricter target.",
        "",
        "| Model | First-contact hits | Recall | Unmatched/match |",
        "|---|---:|---:|---:|",
    ]
    for r in secondary["models"]:
        s = r["first_damage_per_life"]
        lines.append(
            f"| {r['name']} | {s['hits']}/{s['targets']} | "
            f"{s['recall']:.2%} | {s['unmatched_per_match']:.3f} |"
        )
    coord = verification["coordinate_check"]
    lines += [
        "",
        "## Raw-source validation and interpretation",
        "",
        f"All {verification['commands']:,} commands in training replay 7616388415 exactly match",
        "independently decoded raw protobuf fields and ticks. The canonical column",
        "issuer_player_id is actually the raw message entindex; it is used only as an",
        "anonymous issuing-entity key. Selected units are missing from the derivative,",
        "so these commands cannot safely be joined to hero slots or called hero intentions.",
        "",
        f"Among {coord['16384']['rows']:,} single-selected-hero movement checks, applying +16384",
        f"to XY gives median subsequent-position distance {coord['16384']['median_distance']:.1f}",
        f"units and {coord['16384']['within_50_units']:,} matches within 50 units. Without the",
        f"conversion, median distance is {coord['0']['median_distance']:.1f} and none are within",
        "50 units. Subsequent positions are used only for this coordinate diagnostic,",
        "never as forecast inputs. This validates one replay, not every source field.",
        "",
        "Only prior commands and the currently observed objective position enter features.",
        "The rotated-destination control retains timing, issuer, command rates and model",
        "capacity while corrupting map location. It is a diagnostic, not a causal test.",
        "Commands may involve heroes, couriers, illusions or other selected units; an",
        "order need not execute. Visibility and real-time delivery were not established.",
        "",
        "## Novelty assessment",
        "",
        "This is a controlled feature experiment with an established tree learner. It",
        "does not establish a new learning algorithm. Intent-related proxies already",
        "appear in [Tot et al.'s camera-based fight prediction](https://ieee-cog.org/2021/assets/papers/paper_101.pdf).",
        "[Yang et al.](https://arxiv.org/abs/2012.09424) already study multi-event prediction",
        "with rich MOBA state features and attribution. [T-Foresight](https://www.sciencedirect.com/science/article/pii/S2468502X25000440)",
        "studies trajectory-based strategy interpretation; only its abstract was accessible",
        "here. These sources preclude claiming that forecasting player plans in MOBAs is",
        "new merely because this experiment uses a different input stream.",
        "",
        "Even a passing screen would need independent replication, stronger external",
        "baselines, sensor-availability validation, and broader tournament coverage.",
        "No result here evaluates League of Legends or opens its private final test.",
        "",
        "## Reproduction and evidence",
        "",
        "Complete the original precontact protocol to reconstruct training/calibration",
        "arrays. Use the pinned dependencies in research/command-requirements.txt.",
        "The canonical dataset is pinned to 29aca0551be317948d0a181e9630c9a583fadc32.",
        "Raw verification also needs Gem e276f3ea5e77b5b8652a68ef7687b5c494592853 on PYTHONPATH",
        "and the archived training replay from the preceding raw-verification step.",
        "",
        "```bash",
        "python -m research.acquire_command_anticipation --plan-only",
        "python -m research.acquire_command_anticipation",
        "python -m research.verify_command_stream",
        "python -m research.command_features",
        "# In a fresh reproduction checkout, preserve the published freeze first:",
        "mv reports/command-anticipation-freeze-2026-09-30.json "
        "reports/command-anticipation-freeze-published.json",
        "python -m research.run_command_anticipation fit",
        "python -m research.run_command_anticipation score",
        "python -m research.audit_command_first_contact",
        "python -m research.summarize_command_anticipation",
        "```",
        "",
        "Fit intentionally refuses to overwrite frozen artifacts. To reproduce, use a",
        "separate checkout/output workspace and preserve the published evidence files.",
        "The cohort, acquisition hashes, exclusions, per-match alarms, frozen thresholds,",
        "paired intervals and raw validation are in adjacent command-*.json files.",
        "The downloaded replays, Parquet data and model binary are not committed.",
    ]
    (root / "command-anticipation-research-2026-09-30.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
