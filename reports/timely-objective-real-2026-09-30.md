# Timely-objective result: useful engineering, insufficient novelty

Source: the user's uploaded summary, preserved verbatim in
`timely-objective-real-2026-09-30.json`. These are exploratory calibration results,
not sealed-test results.

Training: 24,000 matches / 704,967 observed rows. Calibration: 6,000 matches /
175,031 observed rows. The later evaluation half contains 3,000 matches and 11,329
Dragon events. 7,555 events have a real frame in their 20–60-second warning window.
The 66.69% opportunity figure applies to **frame-only actions**, not all policies
using the same information.

| History target, selected budget | Timely recall | False/match | Late/match | Combined/match |
|---|---:|---:|---:|---:|
| Within 60s, false+late budget | 3.04% | .0237 | .8327 | .8563 |
| Timely 20–60s, false+late budget | 36.25% | .7870 | .1937 | .9807 |
| Within 60s, false-only budget | 43.05% | .9393 | 1.2357 | 2.1750 |
| Timely 20–60s, false-only budget | 39.56% | .9183 | .2327 | 1.1510 |

The primary gain is +33.22 percentage points (conditional paired 95% interval
+32.41 to +34.00). It is mostly a warning-objective alignment result against an
ill-suited comparator. It is not evidence of a novel model. The primary gate
failed: NA had 1,505 non-timely alarms across 1,500 matches, exceeding one per match.
EUW had 1,437 / 1,500. Do not silently replace the primary with the passing snapshot
secondary after seeing these outcomes.

Under the false-only policy, timely recall decreased by 3.49 points (interval
−4.00 to −2.97), while late alarms fell by about 81.17%. That is a meaningful
tradeoff, not uniform domination. Metrics with different binary targets, including
Brier scores, must not be compared as though the outcomes were identical.

The prior coordination feature study gained just +0.168 points over history,
with its interval crossing zero. Neither study establishes state of the art.
The new cooldown-policy candidate is specified separately and has no real-data
result yet. This record must not be rewritten after later experiments.
