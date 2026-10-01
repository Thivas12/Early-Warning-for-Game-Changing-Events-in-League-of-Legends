# League neural continuation analysis

This analysis preserves the registered LeagueEWS versus GRU comparison and
examines what the four model families can establish about early warnings for
Baron, Dragon and teamfight events. All results use League development data.
Patch 16.17 remains sealed.

## Source review

The original model notebooks contain identical code. Re-extracting their saved
evidence reproduces the recorded source review exactly; the extraction is saved
in `notebook-evidence.json`. The original final report was read directly,
including its architecture and training description on pages 13–14, results on
page 16, intended offline use on page 20, and mechanism claims on page 21.

The original pipeline normalized before splitting and randomly divided
overlapping windows after augmentation. Its generator also attached final player
statistics to earlier timestamps. The saved AUCs therefore do not establish
generalization. Their event tables average the 10, 20 and 30 second horizons.
The continuation is a documented descendant of that architecture with audited
features, match-disjoint splits and real observed frames.

The report attributes gains to temporal buildup and shared learning. Comparing
LeagueEWS, GRU, TCN and a current-frame MLP alone cannot identify task transfer:
all four use shared supervision. Their parameter counts also differ, so an
architecture contrast is not a controlled attribution to cross-attention.

Existing tree results provide context, not additional neural fits. Extra lagged
frames gave a macro timely-recall difference of −0.0197 percentage points, with
a conditional 95% interval of [−0.2763, +0.2305]. Training history trees on the
useful interval gave +0.4753 points [0.1850, 0.7913], while increasing teamfight
warning burden. That adaptive result supports testing target alignment as an
established control; it establishes no new method.

## Population and endpoints

The frozen study trains four families at seeds 20260930, 20261001 and 20261002,
using 24,000 matches and 704,967 observed rows from patches 16.12–16.15.
Each fit uses 12 epochs, the original event weights, and the fixed optimizer.

Calibration contains 6,000 matches on patch 16.16. Threshold selection uses the
earlier 1,500 matches in each route, and evaluation uses the later 1,500 in each
route, for 3,000 evaluation matches. This population has already been examined
and remains exploratory. Baron and Dragon labels identify kills or completions,
not the start of an engagement.

The primary contrast is LeagueEWS minus GRU in macro timely event recall with
10–30 seconds of lead, a 60 second cooldown, and at most one false-plus-late
warning per match for each event in each route. Every seed and regional failure
is reported. The registered screen requires a positive difference in every seed
and both models meeting every primary regional budget. It is not a significance
test or confirmation of superiority.

Secondary analyses include all family comparisons, individual events, regional
results, the 20–60 second lead endpoint, and the original row metrics at
10/20/30/60 seconds. No later-calibration threshold adjustment is made.

## Paired uncertainty and seed variation

`scripts/analyse_neural_screen.py` checks completed training, summary provenance,
checkpoint hashes, prediction hashes, aligned targets and offsets, and matching
per-match event counts. It also checks that the recomputed primary point
estimates equal the original runner's summary.

There are 2,000 whole-match bootstrap draws with seed 20261001, stratified by
route. A draw samples the same matches across all families, seeds and events.
Recall is total timely events divided by total events, then averaged equally
across event types for the macro endpoint. False-plus-late burden is the number
of alerts minus timely credits, divided by matches. False and late components
are reported separately. The macro burden is a per-event average, not a combined
three-event attention budget.

The mean across seeds describes average performance of three fixed fits; it is
not an ensemble and does not create 9,000 independent matches. Conditional 95%
percentile intervals capture variation among evaluation matches with models and
thresholds held fixed. Per-seed estimates, ranges and sample standard deviations
describe training variation separately. These intervals do not cover refitting,
threshold-selection uncertainty, adaptation or future patches. Secondary
intervals are unadjusted.

## Mechanism limits

A sequence model versus snapshot changes both information and architecture.
A same-architecture retraining intervention can remove past state information
while retaining parameters, tensor shapes, valid lengths and age channels. It
tests the incremental value of past observed values and missingness beyond the
current summaries and timing information. It does not remove all historical
information from cumulative current features, or isolate temporal order alone.

Shared versus independent event encoders would be required to identify task
sharing. The current study and a history ablation cannot establish that effect.
Any focused follow-up will receive a separate plan and source/runtime freeze
after the original runner completes its gated calibration evaluation.
