# League-only scope correction: 30 September 2026

**Access update, 1 October 2026:** the user supplied the compact three-event
development ZIP. All 60 shards and 879,998 observed rows passed validation;
train/calibration data are now available here. Nine real three-event tree fits
are reported in [the tree results](../reports/league-three-event-results-2026-10-01.md).
The [neural study and history ablation](../reports/neural-continuation-2026-10-01/research-report.md)
also completed on the PC GPU. Test payloads remain absent from the export.
The restoration instructions below are historical;
do not request another export merely because those paragraphs describe the
previous access limitation.

The research objective is early warning of Baron, Dragon and teamfight events in
**League of Legends**. The user explicitly rejected the substitution of Dota
experiments. Availability of a different game's replays is not authorization to
change the research question.

## Evidence that belongs to this project

| Evidence | What it supports | Limit |
|---|---|---|
| [League coordination screen](../reports/coordination-screen-real-2026-09-29.md) | Current geometry and observed history help the tested Dragon warning models; engineered coordination adds only +0.168 percentage points, with its interval crossing zero | Exploratory calibration; conditional intervals; no demonstrated novel coordination signal |
| [League timing-objective screen](../reports/timely-objective-real-2026-09-30.md) | Training on the useful 20–60-second interval changes recall and late-warning burden | Primary regional budget gate failed; no methodological novelty established |
| [Scheduled-policy implementation](cooldown-aware-warning-research.md) | An implemented candidate and checks of its mathematical mechanism | No verified real League result is available here; existing loss mathematics is not claimed as new |

The two real League reports come from user-executed WSL runs. This workspace has
their aggregate summaries; it has not refitted those private models. The uploaded
coordination summary identifies freeze
`29930b83632e79a527e856595cfbf1f3e4ee99fa55824448009c55ca86dedd8f`, and the timing
summary identifies freeze
`43fdb8283a5cc95791d419d01035cbb4d4aaa57b266d3cf0425be9c38d398f18`.

Recorded development data: 24,000 training matches with 704,967 genuine observed
rows, and 6,000 calibration matches with 175,031 observed rows. Train patches are
16.12–16.15; calibration is 16.16. The 6,000 patch-16.17 test payloads stay sealed.
The later calibration half has already been examined, so it is not a fresh test.

## Preserve the actual target and information boundary

`src/league_ews/labels.py` derives Dragon and Baron times from
`ELITE_MONSTER_KILL` records. These identify objective kills/completions, not the
first attack on the objective. The teamfight target keeps its registered
kill-episode definition. The Dota first-damage target is not imported into this
project. A pre-attack League claim would need separately obtained and validated
League labels and observations.

Use genuine observation times and past observations only. Do not create apparent
10-second observations by interpolation from later frames. The old leaked MSc
scores remain excluded from research evidence. Future experiments must distinguish
extra decision opportunities from extra observed information, and must count late
and false alerts under their declared budgets.

## Out-of-scope historical work

The [Dota archive index](archived-dota-work.md) preserves the separate studies,
including the 48 objective-training fits. They establish neither effectiveness
nor ineffectiveness of a League model. They are not League training runs,
League baselines, a League data expansion, or League novelty evidence.

Their frozen source files and reports are retained without changing their hashes.
They are removed from the active research status. No further Dota work is authorized
by the standing request to improve this League project.

## Concrete next step

Restore access to the existing audited League development cache. The standalone
`scripts/export_league_development.py` checks the saved League freeze, summary,
split hash, exact train/calibration shard membership and every shard checksum.
The source freeze is pinned to the reviewed coordination run above. It checks
numeric array headers and shapes without loading NumPy or unpickling objects.
It exports those numeric shards and selected development metadata into a ZIP.
It does not open processed match payloads, test shards, API credentials, model
pickles or player identifiers. Test membership is omitted from the exported split.

The exporter uses the Python standard library and does not need a GPU or new
training. It leaves source data and experiment freezes unchanged. Its checks
establish consistency with the saved source binding; the received arrays must
still be validated before any new fit. If the cache is missing, it reports the
missing League prerequisite instead of substituting another dataset.

Run from the user's existing repository:

```bash
cd /home/thivas/work/ai-portfolio/league-ews-audit
git fetch origin fix/league-only-research-scope
git show origin/fix/league-only-research-scope:scripts/export_league_development.py > /tmp/export_league_development.py
python3 /tmp/export_league_development.py --repo .
```

The output is `data/private/league-development-export-v1/development.zip`.
Upload that ZIP to continue the experiments here. The script prints its size and
SHA-256; it never overwrites an existing output. Public match identifiers and
route/patch metadata are included for whole-match comparisons, but player
identifiers and test membership are not. No new League experiment should be
reported as run until the actual data are available and a League-specific
comparison has been fixed. This access step is not itself a novelty result.

Validation of this correction: 13 focused export-contract tests passed using
tiny synthetic fixtures. These cover excluded test payloads, metadata filtering,
checksum and membership failures, nonnumeric arrays, symbolic links, preservation
of sources and cleanup after an interrupted write. They are software checks,
not training runs or evidence for the research hypothesis.
