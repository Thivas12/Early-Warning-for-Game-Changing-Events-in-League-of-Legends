"""Render the two completed experimental waves, including exclusions and failures."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def read(name):
    return json.loads(Path(f"reports/{name}-2026-09-30.json").read_text())


def table(report):
    lines = [
        "| Policy | Onset hits | Onset recall | Unmatched alerts / match | Kill recall |",
        "|---|---:|---:|---:|---:|",
    ]
    for model in report["models"]:
        if model["seed"] != 17:
            continue
        onset, kill = model["onset"], model["completion"]
        lines.append(
            f"| {model['name']} | {onset['hits']}/{onset['targets']} | "
            f"{onset['recall']:.1%} | {onset['unmatched_per_match']:.3f} | {kill['recall']:.1%} |"
        )
    reactive = report["reactive"]
    onset = reactive.get("onset", reactive.get("onsets"))
    kill = reactive.get("completion", reactive.get("kills"))
    lines.append(
        f"| reactive first-damage detector | {onset['hits']}/{onset['targets']} | "
        f"{onset['recall']:.1%} | {onset['unmatched_per_match']:.3f} | {kill['recall']:.1%} |"
    )
    return "\n".join(lines)


def main():
    initial = read("precontact-pilot")
    fresh = read("precontact-invariance")
    q1, q2 = read("precontact-quality"), read("precontact-replication-quality")
    verification = read("precontact-independent-parser")
    credit = read("precontact-completion-credit")
    fresh_credit = next(c for c in credit["cohorts"] if c["name"] == "fresh")
    primary_credit = next(c for c in fresh_credit["sensitivities"] if c["quiet_gap_seconds"] == 10)
    accepted = [m for q in (q1, q2) for m in q["matches"] if m["status"] == "accepted"]
    reasons = Counter(
        m["reason"].split(":")[0]
        for q in (q1, q2)
        for m in q["matches"]
        if m["status"] != "accepted"
    )
    a = initial["comparisons"][0]
    b = fresh["comparisons"][0]

    def ci(result, key):
        lo, hi = result[key]["percentile_95"]
        return f"[{lo * 100:+.2f}, {hi * 100:+.2f}] percentage points"

    source_matches = len(q1["matches"]) + len(q2["matches"])
    lines = [
        "# Pre-contact objective forecasting: two completed experimental waves",
        "",
        "**Status: exploratory research. No breakthrough or new algorithm is established.**",
        "",
        f"Audited {source_matches} disjoint public Dota matches. "
        f"Retained {len(accepted)} after source checks, "
        f"with {sum(m['hero_rows'] for m in accepted):,} hero-state rows and "
        f"{sum(m['decision_rows'] for m in accepted):,} five-second decision rows. "
        "Hero rows are repeated observations, not independent samples.",
        "",
        "## Design and order of work",
        "",
        "The first wave selected 300 matches by a fixed hash, then split them chronologically "
        "180/60/60 before validation. Quality checks retained 110 training, 37 calibration, "
        "and 26 evaluation matches. Model capacity and alert rules were fixed before fitting. "
        "All five comparisons used the same feature archive and capacity.",
        "",
        "After reading that negative result, the follow-up removed absolute map coordinates and "
        "player/team ordering. Its current-state and motion variants were declared before new "
        "evaluation scores. Exactly 200 disjoint later-period matches were selected. Training and "
        f"calibration remained unchanged; {fresh['split_matches']['fresh_evaluation']} "
        "new matches passed validation. "
        "The original holdout was never added to training or calibration.",
        "",
        "The target is observable damage onset after a death or a gap strictly longer than ten "
        "seconds. It includes non-terminal attempts. It is not strategic intent or irreversible "
        "commitment. Decisions begin at minute five, require 20-60 seconds of lead, use a "
        "60-second cooldown, and receive one-to-one credit. Every unmatched alert counts. "
        "The empirical alert budget is at most one unmatched alert per match. The thresholds "
        "are chosen using calibration only. Observation scope is an omniscient replay observer.",
        "",
        "## First wave: negative result",
        "",
        table(initial),
        "",
        "Coordination minus individual history: "
        f"{a['match_bootstrap']['recall_difference'] * 100:+.2f} "
        f"percentage points; match-bootstrap 95% interval {ci(a, 'match_bootstrap')}; "
        f"calendar-day interval {ci(a, 'day_bootstrap')}. "
        f"Advancement gate: **{initial['advancement_gate_all_seeds']}**.",
        "",
        "The clock baseline outperformed the proposed full coordination representation. "
        "The one additional hit over individual history does not demonstrate a gain. "
        "The reactive detector's high completion recall and zero onset recall use the same "
        "alarm stream but different target denominators; subtracting those recalls is not a "
        "causal decomposition of model skill.",
        "",
        "## Fresh-cohort follow-up",
        "",
        table(fresh),
        "",
        f"The comparator selected on calibration was **{b['calibration_selected_comparator']}**. "
        "Invariant motion minus that comparator: "
        f"{b['match_bootstrap']['recall_difference'] * 100:+.2f} "
        f"percentage points; match-bootstrap 95% interval {ci(b, 'match_bootstrap')}; "
        f"calendar-day interval {ci(b, 'day_bootstrap')}. "
        f"Advancement gate: **{fresh['advancement_gate_all_seeds']}**.",
        "",
        "Three fixed seeds (17, 29, 43) were run. Full-feature histogram boosting is deterministic "
        "here; identical repeats are not independent replications. The scientific replication "
        "is the disjoint match cohort. Complete per-seed and per-match results, including the "
        "fixed five-second delivery-delay sensitivity, are in the JSON reports. Original "
        "model refits must reproduce their first-wave calibration thresholds and counts exactly.",
        "",
        "## Same-encounter completion check",
        "",
        "A post-hoc descriptive check restricts both labels to the same completed encounters. "
        f"On the fresh cohort the reactive detector caught {primary_credit['completion_hits']} "
        f"of {primary_credit['completed_encounters']} kills, but anticipated only "
        f"{primary_credit['same_encounter_onset_hits']} of those same encounters' damage onsets. "
        f"Of its credited kill warnings, {primary_credit['completion_hits_at_or_after_own_onset']} "
        "arrived at or after the corresponding encounter had already started. "
        "This rules out different target populations as the sole explanation of the score gap. "
        "Incidental warnings of subsequent re-engagements retain their legitimate credit. "
        "This is a descriptive mechanism check, not a separately registered discovery test.",
        "",
        "| Quiet gap | Same completed encounters | Kill hits | Onset hits | "
        "Credited kill warnings at/after onset |",
        "|---|---:|---:|---:|---:|",
        *[
            f"| {s['quiet_gap_seconds']} s | {s['completed_encounters']} | "
            f"{s['completion_hits']} | {s['same_encounter_onset_hits']} | "
            f"{s['completion_hits_at_or_after_own_onset']} |"
            for s in fresh_credit["sensitivities"]
        ],
        "",
        "## Data quality and provenance",
        "",
        "The older public export's `game_time`, and the canonical combat table's `game_time_sec`, "
        "track elapsed replay ticks. They cannot be directly compared with pause-adjusted "
        "snapshot times. Some canonical snapshot clocks also advance during pauses and then "
        "jump backward. This pilot excludes unresolved pauses; it never silently repairs them.",
        "",
        "The schema-development match also has team labels contradicted by pregame combat "
        "identities. The adapter derives team membership exclusively from pre-horn records and "
        "requires five heroes per team. Gold and net-worth fields are omitted because their "
        "hero attribution was not independently verified. Every labeled onset must agree with "
        "entity HP loss, and every observed HP loss must have nearby combat damage.",
        "",
        "| Exclusion reason | Matches |",
        "|---|---:|",
    ]
    lines.extend(f"| {reason} | {count} |" for reason, count in reasons.most_common())
    lines.extend(
        [
            "",
            f"A separate Gem parse of archived training match {verification['match_id']} "
            f"matched all {verification['gem_contact_rows']} target damage/death records exactly. "
            f"Maximum clock discrepancy across {verification['clock_rows']} samples was "
            f"{verification['clock_max_absolute_error_seconds']:.6f} seconds. "
            "One independent parse is a useful check, not certification of every field or match.",
            "",
            "## Interpretation and limits",
            "",
            "The tree models and engineered geometry are established methods. This work does "
            "not establish algorithmic novelty, state of the art, or a breakthrough. The "
            "measurement result is that objective-completion recall can substantially reward "
            "a detector triggered by damage already underway. Whether this supports a "
            "novel benchmark contribution still needs a closer comparison with existing event "
            "anticipation evaluations.",
            "",
            "The metadata calls the source PROFESSIONAL, but 176 of the first 300 selected "
            "matches belong to Destiny League. Repeated teams and players may create dependence "
            "beyond calendar-day blocks. Excluding pauses and parse inconsistencies changes "
            "the sampled population. The match count and event count are modest, calibration "
            "is adaptive, and these are exploratory intervals rather than multiplicity-corrected "
            "discovery guarantees. Neither observer inputs nor Dota results establish usable "
            "player-visible warnings or League of Legends performance. The private League "
            "test remains untouched.",
            "",
            "No more samples are added after inspecting the second wave. A further method "
            "revision requires a new declared experiment and fresh evaluation. Useful next "
            "work is authoritative pause reconstruction and broader league/team coverage, "
            "followed by matched temporal-model and visibility-restricted comparisons; it is "
            "not relabeling these baseline features as a new algorithm.",
            "",
            "## Artifacts and reproduction",
            "",
            "- [First protocol](../docs/precontact-pilot-protocol.md) and "
            "[follow-up declaration](../docs/precontact-invariance-followup.md).",
            "- [First results](precontact-pilot-2026-09-30.json) and "
            "[fresh results](precontact-invariance-2026-09-30.json).",
            "- [First quality ledger](precontact-quality-2026-09-30.json) and "
            "[fresh quality ledger](precontact-replication-quality-2026-09-30.json).",
            "- [Independent parser check](precontact-independent-parser-2026-09-30.json).",
            "- [Same-encounter completion check](precontact-completion-credit-2026-09-30.json).",
            "- Acquisition manifests pin the public dataset revision, selected match IDs, "
            "split membership, and source file hashes.",
            "- The scientific timing, prefix-access, team-attribution, alert-budget, and "
            "invariance tests pass. Raw replays and feature caches are not committed.",
            "",
        ]
    )
    Path("reports/precontact-research-2026-09-30.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
