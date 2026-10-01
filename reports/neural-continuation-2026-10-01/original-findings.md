# Results of the four family League study

All twelve CUDA fits and their gated calibration evaluations completed with
worker exit code 0. **LeagueEWS improves on GRU at the primary endpoint, but the
registered development screen fails its regional warning-budget requirement.**
LeagueEWS and the smaller TCN have nearly identical average primary recall.

## Useful warning recall

These are percentages of distinct events warned about with 10–30 seconds of
lead, averaged over the three fixed seeds. Burden is false-plus-late warnings
per match, averaged over events and seeds; it is not a combined attention budget.

| Family | Baron recall | Dragon recall | Teamfight recall | Macro recall | Mean burden |
|---|---:|---:|---:|---:|---:|
| LeagueEWS | 20.878% | 13.176% | 3.082% | 12.379% | 0.865 |
| GRU | 12.085% | 8.977% | 2.204% | 7.755% | 0.785 |
| TCN | 20.734% | 13.532% | 2.834% | 12.367% | 0.864 |
| Snapshot | 18.636% | 11.743% | 2.590% | 10.990% | 0.845 |

The registered LeagueEWS-minus-GRU differences are **+4.932, +3.379 and +5.559
percentage points** at seeds 20260930, 20261001 and 20261002. Their fixed-seed
mean is **+4.623 points**, conditional paired 95% interval **[+4.223, +5.064]**.
However, Americas Baron burden in seed 20261001 is **1.0113** for LeagueEWS and
**1.0120** for GRU, exceeding the limit of one. The original screen is therefore
false; the thresholds and decision rule have not been relaxed after evaluation.

LeagueEWS's macro recall ranges from 12.156% to 12.773% across seeds, with sample
standard deviation 0.343 percentage points. GRU ranges from 6.597% to 8.827%,
with standard deviation 1.118 points. TCN ranges from 11.972% to 12.604%, and
snapshot from 10.702% to 11.258%. Seed variation is distinct from the conditional
match-sampling intervals; three seeds do not triple the number of matches.

LeagueEWS emits 0.050 fewer false but 0.130 more late warnings per match per event
than GRU, for a net **+0.080** false-plus-late burden. Its recall gain is not an
equal-realized-burden comparison.

## Controls and regions

LeagueEWS minus TCN is **+0.012 points [−0.156, +0.178]**. The individual seed
differences are +0.802, −0.318 and −0.448 points. This does not demonstrate an
advantage for the hybrid's extra components. LeagueEWS has 1,751,647 parameters
and TCN 557,087; the comparison matches data and update budget, not capacity or
compute.

LeagueEWS exceeds snapshot by **+1.389 points [+1.135, +1.637]**. TCN exceeds
snapshot by +1.377 points [+1.115, +1.627]. GRU trails snapshot by **−3.234 points
[−3.645, −2.847]**, so beating GRU alone is an insufficient architecture claim.

All primary regional failures concern Baron in the Americas: the two failures
above, all three TCN seeds (1.0200, 1.0260, 1.0040), and snapshot seed 20260930
(1.0320). There are no Europe primary budget failures. Mean LeagueEWS Baron
recall is 21.201% in Europe and 20.560% in the Americas, with burdens 0.9038 and
0.9920. A seed average below one does not erase a failing seed.

The [complete tables](tables.md) include every event, family, region and seed,
paired contrasts, and budget failures. [Machine-readable results](neural-analysis.json)
also retain the separate false and late burdens, all 12 row metrics per fit,
thresholds and provenance checks. [The CSV](neural-by-seed.csv) has one row per
family, seed, horizon, region and event.

## The longer lead endpoint reverses the primary ranking

At 20–60 seconds, LeagueEWS minus GRU macro recall is **−0.843 points
[−1.358, −0.307]**, negative in all three seeds. Dragon drives this reversal:
LeagueEWS recall is 9.645%, versus GRU's 18.130%, a difference of **−8.486 points
[−9.164, −7.809]**. Baron and teamfight improve, so this is not uniform harm.

The Dragon row classifier's average precision is nevertheless about 0.763 for
LeagueEWS, versus 0.557–0.596 for GRU. LeagueEWS's selected policies produce more
late Dragon warnings. Better within-horizon classification thus does not imply
better useful warning timing. These observations do not, by themselves, identify
a causal explanation for the reversal.

## What the experiment establishes

The four-family comparison does not isolate history from architecture or
capacity. All four models use shared event supervision, so it cannot identify
positive or negative task transfer. It also does not isolate cross-attention
from the other hybrid components. A near-zero hybrid-versus-TCN difference is
evidence against promoting the added hybrid complexity on this endpoint.

The selected follow-up is the protocol's retrained history ablation of LeagueEWS,
with the same parameters and training recipe. Its [frozen plan](history-ablation-plan.json)
tests whether past observed values and missingness contribute beyond current
state summaries and retained timing information. It was selected after these
development results and is explicitly adaptive and exploratory.

All intervals use 2,000 paired whole-match bootstrap draws within regions and
are conditional on fitted models and selected thresholds. They do not include
refitting, adaptive search or future-patch uncertainty. Secondary intervals are
unadjusted. See [methods and source review](methods.md). Patch 16.17 remains
unopened. Neither a breakthrough nor methodological novelty is established.
