# What was wrong, what was missing, and what this study can resolve

The original hypothesis concerns temporal buildup and shared learning for
Baron, Dragon and teamfights. It comes from page 21 of the preserved MSc report;
see the [notebook review](../../docs/notebook-continuation.md). Keeping the hybrid
architecture while improving a score is not enough to establish that hypothesis.

## Corrected validity problems

The notebook's overlapping windows and jitter copies were split after global
normalization. Matches and overlapping histories could enter both sides. The
continuation splits by match and patch first, fits normalization on training
only, and uses actual historical observations with masks and ages. End-of-match
statistics are excluded. Chronological alerts replace hindsight peak selection;
matching, useful lead, one-to-one event credit and cooldown are explicit. The
original report's saved row AUCs are preserved as historical outputs, not valid
estimates of this continuation's warning performance.

The continuation then had two consequential missing controls. First, its
cumulative output targets rewarded some events that were already too close for
a useful warning. The [target intervention](../timely-neural-2026-10-03/research-report.md)
changed the evaluated heads to useful next-event windows while fixing the
training recipe. Both LeagueEWS and TCN improved, particularly longer-lead
Dragon. This supports objective alignment; it does not establish a new hybrid
architecture. Shorter auxiliary heads retain their old cumulative labels.

Second, a coarse threshold grid left models at different warning costs. The
[threshold-resolution control](../dense-policy-2026-10-04/research-report.md)
recovered a deterministic target gain. Matching expected early cost does not
match later cost, and neither approach removes regional failures. The original
registered LeagueEWS-minus-GRU comparison and its failed regional gate remain
unchanged. The additional policies are explicitly separate exploratory controls.

## Missing mechanism control addressed here

The earlier full-history versus current-only comparison used cumulative labels.
It could not establish that historical state remains valuable under useful-lead
supervision. This study retrains the identical input intervention with the
corrected targets, and evaluates the paired difference in history effects across
both target definitions. The full, timely LeagueEWS model is a completed frozen
control, not a new selected fit.

A timing-only model tests a second alternative explanation: objective counts,
observed clock, time-since-objective and their trajectories may explain much of
the recall. The new model keeps the same architecture, initialization and update
budget, but retains only the prespecified timing inputs and corresponding masks.
Comparing full versus timing-only measures the value of the excluded information
under this fixed recipe. It does not identify which excluded feature causes a
gain. The current-only intervention still contains historical summaries in its
current frame and retains observation ages; timing-only still has a history.

## Regional exposure check using already published aggregates

The [descriptive exposure record](prior-exposure-diagnostic.json) reuses the
completed objective audit and dense-policy analysis; it selects no new policy.
Americas has 44,120 observed frames in the early half and 44,157 later, only
0.084% more, with 1,500 distinct matches in each half. Its Baron opportunity fraction changes
from 33.27% to 32.68%, while full timely LeagueEWS's mean dense budget-one burden
is 1.0313 warnings per match across seeds. Europe's observed-frame count falls
1.03%; its corresponding Baron burden is 0.9364.

The near-equal Americas frame exposure does not support explaining its overrun
simply as substantially more observed frames per match. It does not rule out
changes in match composition, conditional risks or score distributions. Aggregate
ratios cannot identify the cause of drift or turn a mean training/calibration
constraint into a later regional risk guarantee. All failed gates remain failed.

## What remains unresolved regardless of the result

- The two input contrasts are not a factorial decomposition. Full-minus-current
  removes past timing and non-timing state together; full-minus-clock removes
  current and past non-timing state together. Even two positive contrasts cannot
  prove that the history gain comes from past non-timing state. That requires an
  additional control retaining genuine timer history and all current state while
  replacing only past non-timing values and missingness with their current values.
  This limitation was recorded before the new calibration predictions existed.
- Equal parameter counts do not guarantee equal effective capacity or equally
  good optimization after input removal. A weak reduced-input model is not an
  information-theoretic proof that timing cannot predict an event.
- These controls do not isolate temporal order, cross-attention, or causal game
  actions. The TCN control has fewer parameters and a different compute cost.
- Joint versus independent heads and PCGrad were studied under cumulative labels.
  Their task-dependent tradeoffs are recorded; sharing under useful-lead targets
  remains a separate question. This study cannot claim to solve task interference.
- Objective labels mean Baron/Dragon completions, not engagement onset. Genuine
  timeline frames constrain available warning opportunities. Held-forward values
  cannot create additional measured observations.
- The same calibration population informed successive studies. Conditional
  whole-match intervals omit refitting, policy-selection and adaptive-search
  uncertainty. They also do not establish independence of matches sharing players.
  Seed replication is not a new population or fresh external validation.
- Full timely LeagueEWS already fails regional hard-one budgets. Passing an input
  diagnostic cannot rescind those failures. Later results cannot be used to select
  a lower budget and then describe that budget as a fresh confirmatory success.

The committed plan fixes all six fits, their checkpoint/scoring gate, all 198
policy heads, the primary contrast, event/regional/seed analyses and descriptive
rules before observing new calibration predictions. All negative results are
retained. No result from this development-only study, by itself, licenses a
breakthrough or novelty claim. Patch 16.17 stays sealed.
