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

The paired B3 minus B2 macro AP gain was **0.13609**. Resampling all 6,000
complete calibration matches 1,000 times with identical draws for both methods
gave a percentile 95% interval of **0.13061–0.14182**. All 12 target-specific
paired intervals were above zero. These intervals estimate uncertainty within
this calibration sample. Repeated appearances of players across matches and
future-patch drift are not captured by this match-level resampling.

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

The next modeling stage is B4 temporal sequence context, followed by the
registered graph and hazard ablations. Model and alert-policy decisions must
remain on the training and calibration patches until the one-time future-patch
evaluation is frozen.
