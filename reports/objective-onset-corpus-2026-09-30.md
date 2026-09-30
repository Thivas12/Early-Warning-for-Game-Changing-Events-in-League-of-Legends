# Completed objective-onset audit — 30 September 2026

**A reactive contact detector earns substantial objective-completion credit.
That credit does not establish anticipation of the attack it detected.** This
is a real-replay measurement finding and a reason to change the next research
question, not a new forecasting model or a breakthrough claim.

## Executed study

We attempted all nine matches in Gem's pinned replay-fixture manifest. Seven
passed raw-file SHA256, complete-parse, game-clock, and OpenDota terminal-event
checks. One download timed out twice. One archived OpenDota reference lacked
parsed objective data, preventing the required check. Both failures are
preserved in the acquisition ledger. No exclusion used model performance.

The seven accepted games contain **1,004,359 combat-log records**, but only
**seven independent matches**. They contain 21 Roshan kills. With a ten-second
quiet-gap definition there are 41 damage episodes: 21 end in a kill and 20
close after a quiet period without a kill. None is right-censored at this gap.
“Non-terminal damage episode” does not prove an abandoned strategic intention.
One accepted match contains no Roshan contact and remains in the denominator.

No model was fitted. The baseline emits at the first positive objective damage
after a quiet gap and observes a 60-second cooldown. Its inputs cannot include
future kills. Identical alarms are scored against completion and contact onset
with one-to-one event matching. Leads below use **pause-corrected game time**.

## Primary descriptive results

Ten-second quiet gap, immediate observer-log delivery, 30 total alarms:

| Lead window | Completion recall | Completion unmatched alarms/match | Contact-onset recall | Onset unmatched alarms/match |
|---|---:|---:|---:|---:|
| 5–60 seconds | 18/21 = **85.7%** | 12/7 = **1.71** | 6/41 = **14.6%** | 24/7 = **3.43** |
| 20–60 seconds | 10/21 = **47.6%** | 20/7 = **2.86** | 6/41 = **14.6%** | 24/7 = **3.43** |

The six onset hits precede **later re-engagements**. A detector cannot anticipate
the very first damage that triggers its own alarm. Its nonzero onset score is
reported rather than suppressed. At the existing one-unmatched-alert-per-match
gate, this detector fails under both target definitions and both lead windows.
It is not a competitive model result at that operating point.

The stricter 20-second minimum reduces the amount of completion credit, but
does not eliminate it. The difference between the two recall columns is not a
causal decomposition of model skill: their event denominators are different.

## Boundary sensitivity

Immediate delivery, 20–60-second lead window:

| Quiet gap | Damage episodes | Alarms | Completion hits / 21 | Onset hits / episodes |
|---|---:|---:|---:|---:|
| 5 seconds | 48 | 31 | 11/21 | 7/48 |
| 10 seconds | 41 | 30 | 10/21 | 6/41 |
| 20 seconds | 33 | 29 | 10/21 | 3/33 |
| 30 seconds | 30 | 29 | 10/21 | 1/30 |

Short quiet gaps split repeated contacts into more events. A research claim
about tactical initiation therefore needs validated event boundaries and this
sensitivity analysis. The machine-readable report also contains one- and
five-second delivery-delay controls. No gap or delay was selected to maximize
the headline result.

## Per-match accountability

Primary gap; onset hits below use a 20–60-second lead:

| Match | Damage episodes | Kills | Alarms | Completion hits at 5s / 20s | Onset hits |
|---|---:|---:|---:|---:|---:|
| 8822520406 | 1 | 1 | 1 | 1 / 1 | 0 |
| 8822593932 | 9 | 3 | 5 | 2 / 1 | 2 |
| 8855242704 | 7 | 5 | 7 | 5 / 1 | 0 |
| 8856501050 | 12 | 7 | 10 | 7 / 4 | 1 |
| 8860187335 | 9 | 3 | 4 | 1 / 1 | 3 |
| 8868259993 | 0 | 0 | 0 | 0 / 0 | 0 |
| 8974053011 | 3 | 2 | 3 | 2 / 2 | 0 |

The earlier one-match export pilot is kept separately in
`objective-onset-pilot-2026-09-30.json`. It lacks a pause clock, uses nominal
replay-tick time, and is excluded from the table and all seven-match totals.

## Research decision

Proceed with **pre-contact objective engagement forecasting that retains
non-terminal episodes**, using independently validated labels and a strong
reactive re-engagement baseline. First-contact labels are observable; strategic
intent and actionability are not established by this audit.

The proposed method comparison, closest literature, data requirements, and
five-percentage-point advancement gate are in
[`objective-onset-research.md`](../docs/objective-onset-research.md).

This is Dota feasibility evidence from a small, nonrandom parser-test corpus.
It neither establishes a population effect nor transfers numerically to
League. No confidence interval or significance claim is manufactured from the
million correlated log records. We have not shown that any published model's
entire performance comes from contact detection, or that the existing League
system uses the same information. Completion prediction can still be useful
for a broadcast or during an ongoing attack.

The missing League measurement is objective damage onset and reliable episode
closure. The normalized 36,000-match collection and its aggregate JSON reports
do not provide those labels. Filling minute gaps with invented state cannot
supply them. The next substantial result needs dense League telemetry or
validated replay annotations, followed by an unseen-patch model comparison.

## Reproduction and verification

- Nine focused scientific tests passed, including 250 randomized comparisons
  of event matching against exhaustive assignment, detector prefix consistency,
  future-death independence, non-terminal episodes, censoring, source validation,
  and incidental credit for a later re-engagement.
- Changed Python files pass Ruff; whitespace and credential-pattern checks pass.
- Replaying the committed compact numerical evidence produced a byte-identical
  corpus report. Source and raw-file hashes are recorded.
- The extractor received a formatting-only edit during acquisition. Its saved
  compiled code and final source were verified to have identical executable
  bytecode, constants, names, and argument structure; both provenance hashes
  are retained in the evidence ledger.
- No full-suite rerun, GPU training, real League experiment, or final-test access
  was performed in this study.

Fast offline reproduction from the committed facts, with Python 3.12 and no
third-party packages:

```bash
PYTHONPATH=. python -m research.compile_objective_onset \
  --evidence reports/objective-onset-corpus-2026-09-30-evidence.json \
  --output-prefix /tmp/objective-onset-reproduced
```

[`Raw numerical report`](objective-onset-corpus-2026-09-30.json) ·
[`Compact evidence and acquisition ledger`](objective-onset-corpus-2026-09-30-evidence.json)

Upstream source: [Gem](https://github.com/whanyu1212/gem-dota/tree/e276f3ea5e77b5b8652a68ef7687b5c494592853),
commit `e276f3ea5e77b5b8652a68ef7687b5c494592853`. The compact evidence contains
derived numeric contacts and timing/provenance facts, not raw replays or copied
parser code.
