# RiftHazard calibration results — 2026-09-26

These aggregate results were supplied from the private registered-final run.
The source files remain under `data/private/` in the researcher's checkout;
this report contains no match or player identifiers or model files. The
registered split checksum is
`265a10f2ae7dc9ad6a956e11a52562b1091c08c5c57e3d0721db18578dd89770`.
The final raw collection manifest checksum is
`7e07a1cddcd05377a6af881fc0540853687cfc4afd9d0a49dde793405a7e4bc1`.
The B3 implementation is in commit `4f58ee2`, the paired bootstrap in
`88bab56`, and the alert-policy implementation in `8c89e86`. The CLI uses
the locked `uv.lock` environment (Python 3.12), B3 random seed `20260915`,
and the bootstrap seed `20260915`. B3 inputs are the causal tabular feature
set in `src/league_ews/tabular_baseline.py`; labels use the exact-future-events
policy in `src/league_ews/labels.py`. Exact per-target model and report hashes
are retained in the ignored private outputs. The public values below are
rounded transcriptions of the supplied command output; those private outputs
remain the source of truth.
Patches 16.12–16.15 supplied 24,000 training matches, patch 16.16 supplied
6,000 calibration matches, and the 6,000 matches from patch 16.17 remain
unread by the calibration commands.

## Row-level discrimination on calibration

| Control | Macro average precision across 12 event/horizon targets |
|---|---:|
| B0 prevalence | 0.06531 |
| B1 match clock | 0.11133 |
| B2 observed event history | 0.23985 |
| B3 causal tabular gradient boosting | 0.37594 |
| B4 eight-frame GRU, ten-seed mean | 0.32382 |

The paired B3 minus B2 macro AP gain was **0.13609**. Resampling all 6,000
complete calibration matches 1,000 times with identical draws for both methods
gave a percentile 95% interval of **0.13061–0.14182**. All 12 target-specific
paired intervals were above zero. These intervals estimate uncertainty within
this calibration sample. Repeated appearances of players across matches and
future-patch drift are not captured by this match-level resampling.

The ten prespecified B4 seeds all completed three training epochs on the
24,000 training matches. On the same 6,000-match calibration partition, their
macro AP mean was **0.32382**, sample standard deviation **0.00701**, and
range **0.31349–0.33485**. The B4 mean trails B3 by **0.05212** absolute macro
AP. All ten seed results remain in the ignored private summary; no seed was
selected from calibration performance. The per-target values below are rounded
transcriptions supplied from the private reports, not fresh measurements in
this public checkout.

| Target | B3 AP | B4 mean AP | B4 − B3 |
|---|---:|---:|---:|
| Baron 10 s | 0.2367 | 0.1320 | −0.1047 |
| Baron 20 s | 0.3712 | 0.2365 | −0.1347 |
| Baron 30 s | 0.3985 | 0.2801 | −0.1184 |
| Baron 60 s | 0.4512 | 0.3716 | −0.0796 |
| Dragon 10 s | 0.3110 | 0.2515 | −0.0595 |
| Dragon 20 s | 0.4925 | 0.4256 | −0.0669 |
| Dragon 30 s | 0.5885 | 0.5393 | −0.0492 |
| Dragon 60 s | 0.7507 | 0.7242 | −0.0265 |
| Teamfight 10 s | 0.1286 | 0.1233 | −0.0053 |
| Teamfight 20 s | 0.1867 | 0.1920 | +0.0053 |
| Teamfight 30 s | 0.2313 | 0.2403 | +0.0091 |
| Teamfight 60 s | 0.3645 | 0.3695 | +0.0050 |

B4 trails B3 on every Baron and Dragon target. The small Teamfight gains at
20–60 seconds have no paired uncertainty interval yet and do not establish an
improvement. B4 remains a secondary control; the registered H1 comparison is
the graph model M1 against B3.

## Event-level 60-second alert policy on calibration

The fixed policy selected one threshold per event from a 101-point logarithmic
grid by maximum event F1, then fewer false alerts, then higher threshold. It
suppresses repeated alerts through 60 seconds and pairs each alert to at most
one strictly future event onset within 60 seconds. It is a calibration-selected
operating point, so the numbers below may be optimistic.

| Event | Threshold | Precision | Event recall | Event F1 | False alerts/game | Median lead (s) |
|---|---:|---:|---:|---:|---:|---:|
| Baron | 0.199526 | 0.36610 | 0.68667 | 0.47758 | 1.28767 | 25.634 |
| Dragon | 0.354813 | 0.65539 | 0.77891 | 0.71183 | 1.55200 | 27.4295 |
| Teamfight proxy | 0.199526 | 0.29704 | 0.75086 | 0.42568 | 11.85267 | 28.3425 |

The registered H5 coaching-utility gate requires at least two event types to
reach event recall ≥0.50, precision ≥0.50, median lead ≥20 seconds and no more
than one false alert per game. **None of these three B3 calibration operating
points meets the complete gate.** Baron and teamfight precision fall below
0.50; all three exceed the false-alert budget. This is a negative result for
the selected B3 policy, not a final test result for B3 or a result for the
proposed graph model. No product utility claim follows from it.

## M1 graph-hazard model on calibration

The ten registered M1 seeds completed three epochs each. Their mean macro AP
over the twelve event/horizon targets was **0.49112** (sample SD **0.00622**,
range **0.47963–0.49952**), compared with **0.37594** for B3. The descriptive
mean delta is **+0.11518** absolute. No seed was selected from calibration;
the future-patch paired interval needed for H1 has not been calculated.

The same fixed 60-second alert-policy rule selected an operating point for
each M1 seed and event on the 6,000 calibration matches. The ten-seed means
below are rounded transcriptions of the private, checksum-bound audit; B3 is
the earlier calibration operating point on those same matches. These are
calibration-selected results, not future-patch estimates.

| Event | Method | Precision | Recall | Event F1 | False alerts/game |
|---|---|---:|---:|---:|---:|
| Baron | B3 | 0.36610 | 0.68667 | 0.47758 | 1.28767 |
| Baron | M1 mean | 0.48761 | 0.51085 | 0.49852 | 0.58347 |
| Dragon | B3 | 0.65539 | 0.77891 | 0.71183 | 1.55200 |
| Dragon | M1 mean | 0.55153 | 0.63018 | 0.58807 | 1.94413 |
| Teamfight proxy | B3 | 0.29704 | 0.75086 | 0.42568 | 11.85267 |
| Teamfight proxy | M1 mean | 0.32815 | 0.67829 | 0.44203 | 9.27712 |

M1 gives a modestly higher event F1 and fewer false alerts for Baron and
teamfight, but lower recall for both. For Dragon it has lower precision,
recall and F1, with more false alerts. Teamfight still produces over nine
false alerts per game on average. These results do not establish H5, and the
test patch 16.17 remains unread. The registered ablations come before its
one-time evaluation.

Model and alert-policy decisions must remain on the training and calibration
patches until the one-time future-patch evaluation is frozen.
