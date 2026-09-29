# Research reassessment after M1 calibration ablations

**Status:** analysis plan written after observing four graph-removal calibration
results on patch 16.16. It does not retroactively amend the frozen M1 protocol,
the six registered ablations, or their sealed patch 16.17 test. New comparisons
below are exploratory on this cohort. A new model claim needs an independently
registered protocol and a fresh untouched cohort.

## What the present evidence supports

The M1 ten-seed calibration mean macro AP is 0.49112, versus 0.37594 for the
B3 tabular reference. These are 12 observation-level event/horizon tasks. The
M1 60-second Dragon alert policy has event F1 0.58807 and 1.944 false alerts
per game on calibration; B3 has 0.71183 and 1.552 respectively. M1 Teamfight
has 9.277 false alerts per game, which is not a credible low-burden coaching
policy. Thresholds were chosen and assessed on the *same* 6,000 calibration
matches; those alert numbers are selection-biased estimates, not held-out
operating performance. Seed SD measures variation between fits sharing the
same matches. It is not uncertainty for a new patch.

Removing objective nodes raises macro AP by 0.01974 on calibration. It also
changes the graph from 12 to 10 nodes, removes two relation types, and changes
mean-pooling scale. This cannot establish that objective context is harmful.
Removing positions *and* proximity edges lowers macro AP by 0.35198, but does
not separate coordinates, missing-position status, player proximity, and pit
proximity. The two remaining registered ablations (independent horizon heads
and fixed-minute grid) must still be completed and reported, including negative
results. No ablation result licenses selecting the best seed or changing the
original frozen M1 hypothesis.

## Checks before fitting another model

1. Run `make audit-m1-calibration` against the private, checksum-bound original
   and ablation reports. Its small JSON output gives every target's prevalence,
   AP lift over prevalence, Brier skill against the constant-rate forecast, and
   same-seed difference. It lists missing registered variants and never reads
   the test patch. Inspect all 12 targets; macro AP can hide poor Dragon alert
   utility and trivial short-horizon opportunity.
2. Review the existing EDA and raw field coverage by route, patch, game time,
   and position-observed status. The pilot showed roughly 16%, 33%, and 50%
   of event onsets had a genuine observation within 10, 20, and 30 seconds.
   Those are observational ceilings on lead-time event recall, not model
   failures. Quantify the same rates for the final train/calibration partitions.
   Do not synthesize intermediate frames or claim 10-second live updates from
   approximately minute-spaced Match-V5 frames.
3. Check event counting and exposure. Report the number of events with a
   preceding frame within each horizon, all events, positive prediction rows,
   and per-match false-alert distribution (median, p90, p95, maximum). Audit
   lead-time strata and the early/late match phases. A model can raise AP by
   exploiting event clocks while yielding little early warning.

   `make audit-m1-alert-opportunity` replays the **existing** ten M1 policies
   against checksum-bound calibration scores and processed matches. It uses
   only patch 16.16, reads no archived raw bundle, and writes a small
   identifier-free JSON to `reports/local/m1-alert-opportunity.json`. It
   reports actual preceding-frame opportunity at 10/20/30/60 seconds, recall
   among events observable at 60 seconds, false-alert counts per match, and
   lead-time bands. It also chooses a separate threshold from the earlier
   1,500 calibration matches in each route and evaluates that operating point
   on the later 1,500 in each route. These later-half numbers are a descriptive
   within-patch sensitivity check, because this analysis was designed after
   seeing the aggregate calibration outcomes; they are not confirmatory
   future-patch performance. The existing thresholds and reports are never
   changed. Compare their same-sample metrics with these later-half estimates,
   and explicitly report deterioration rather than optimizing a new threshold
   against the later half.
4. Audit normalized missing fields against source-side presence. A default
   value must not be presented as a measured value. Inspect actual availability
   and timing of positions before attributing the large spatial ablation gap
   to tactical movement.

## Separately registered follow-on experiment

The candidate research question is whether *observable, recent relative
position and objective availability* improves useful early warnings at a
fixed alert budget across patches. It is a falsifiable question, not a novelty
claim. Preregister the exact input transforms, architectures, compute budget,
training seeds, model selection and thresholds before any new fit.

| Comparison | Single change | Why it is needed |
|---|---|---|
| Coordinate-only removal | Mask participant x/y, preserve their observed bit and all edges | Separate coordinate content from graph relations. |
| Proximity-only removal | Keep coordinates, remove player and pit proximity relations | Isolate edge information. |
| Missingness-only removal | Keep measured coordinates and relations, mask observed-position bit | Detect a missingness shortcut. |
| Objective-anchor control | Retain 12 nodes and pooling denominator; replace the two anchor features/edges with masked nodes | Separate objective information from node-count and pooling effects. |
| Simple spatial tabular baseline | Use only causally observed time, objective clocks, and team-relative distances; equal training data | Check whether the GNN adds value over a transparent spatial model. |

Do not add the best-performing control to the already registered M1 test claim.
The objective-clock baseline is particularly important: fixed spawn bits and
positions could make AP look better without representing player interactions.
Any interpolation must be excluded from the prediction-input path. A learned
continuous-time point-process model is an optional, separately budgeted
comparator; irregular event timing alone does not make it better.

**Primary operating endpoint for the follow-on:** event recall and precision
at a prespecified false-alert budget per game, with one-to-one onset matching,
60-second horizon, 60-second cooldown, and the event-opportunity denominator
shown alongside recall over all events. Report Baron, Dragon and Teamfight
separately. Gate a model only if it improves the prespecified event utility
without worsening false-alert burden or probability calibration. Macro AP,
each horizon's AP lift, Brier skill, and lead-time distribution are secondary;
never substitute them for a failed operating gate. Define the numerical budget
and decision rule before collecting the next cohort, based on the product use
case and the observed train/calibration burden, not on test scores.

**Uncertainty and multiplicity:** paired match-level bootstrap within route
and patch for each model comparison, resampling entire matches and preserving
all their frames and event onsets. Use a fixed public seed and at least 1,000
replicates; report interval estimates, denominators, and route/patch slices.
Ten training seeds are repeated fits, not ten independent datasets. Specify a
primary event and endpoint or control the family of multiple comparisons in
the separate protocol. Estimate threshold utility on data separate from that
used to choose the threshold. On the current cohort, same-calibration scores
remain descriptive regardless of bootstrap precision.

**Generalization:** keep original patch 16.17 sealed until the original six
ablations, original M1/B3 policy, and analysis code are frozen for its single
registered release. Publication must include that result even if unfavorable.
Any model invented after inspecting patch 16.16 needs a *new* later-patch
untouched cohort, with fresh source authority and sampling plan. Monitor
player overlap and repeat the uncertainty analysis at the player cluster level
if linkage is lawfully retained; report what cannot be measured if it is not.

## Research basis and limits

Yèche et al., [Temporal Label Smoothing for Early Event Prediction](https://proceedings.mlr.press/v202/yeche23a.html),
ICML 2023, study event recall at low false-alarm rates and temporal prediction
structure. Their results motivate evaluating warning burden, not importing
their performance into League. Yanagisawa,
[Proper Scoring Rules for Survival Analysis](https://proceedings.mlr.press/v202/yanagisawa23a.html),
ICML 2023, motivates checking probability quality in addition to ranking.
Cai and Ye,
[Understanding the Limits of Deep Tabular Methods with Temporal Shift](https://proceedings.mlr.press/v267/cai25j.html),
ICML 2025, discuss the impact of temporal shift and splitting choices;
their setting does not establish this project's future-patch performance.
The [technical alarm evaluation framework](https://pmc.ncbi.nlm.nih.gov/articles/PMC8414372/)
motivates separating timeliness and burden from row-level ranking; its clinical
setting is not evidence of game-specific utility.
These are established research directions. The contribution, if any, has to
survive the concrete controls and a new untouched cohort.
