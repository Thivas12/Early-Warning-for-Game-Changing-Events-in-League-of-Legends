# Timing objective experiment

Status: implementation for a new exploratory experiment, designed after seeing
the 29 September coordination results. No real results from this follow-up exist
yet. This is a diagnostic comparison, not a claimed novel learning algorithm.

## Evidence motivating the change

The [real coordination screen](../reports/coordination-screen-real-2026-09-29.md)
found only +0.168 percentage points of timely recall from movement summaries
beyond history (paired 95% interval -0.044 to +0.389 points). Its coordination
policy issued 4,896 timely, 3,707 late and 2,826 false alerts on 3,000 evaluation
matches. A training target including every event in the next 60 seconds may
reward predictions that are already too late for a 20-second minimum lead.
That is an explanation to test, not a conclusion established by these counts.

## Fixed comparison

Four fresh fits cross two existing feature sets with two binary targets:

| Representation | Within-60 target | Timely target |
|---|---|---|
| Snapshot, 52 features | Next Dragon in (0, 60] seconds | Next Dragon in [20, 60] seconds |
| History, 158 features | Next Dragon in (0, 60] seconds | Next Dragon in [20, 60] seconds |

Time is measured from the observed frame to the next strictly future Dragon.
Exactly 20 and 60 seconds are timely. An event at the frame is not future.
A match that ends without another Dragon contributes known negatives.
Targets use exact event timestamps; features remain the original causal arrays.
No interpolation, invented observations, future match end or future event state
enters the feature matrix. Test payloads are never opened.

All fits use histogram gradient boosting with constant-zero imputation plus
training-fitted missingness indicators; 100 iterations, learning rate 0.08,
minimum leaf size 100, L2 penalty 1, seed 20260929 and no early stopping. Select
7, 15 or 31 leaves using **timely-target AP for both training objectives** on
patch 16.15, after fitting on 16.12–16.14. Break ties toward fewer leaves.
Refit on all 24,000 training matches. Historical model results are not silently
substituted: the common selection metric differs from the original screen.
This controls the selection procedure, but selected capacities may differ.

## Policies, primary contrast and decision

For each fitted model, independently tune two policies on the earlier 1,500
patch-16.16 matches per route. Evaluate on the later 1,500 per route without
retuning. Each selects maximum timely event recall on the same 101 thresholds
from 1e-5 to 1 plus a disabled policy, under a mean burden of at most 1/match:

1. **Primary:** count false **and late** alerts as non-timely burden.
2. **Secondary:** count false alerts only, preserving the previous budget's
   meaning. Late alerts remain separately reported.

Tie-break by less selected burden, then fewer non-timely alerts, then higher
threshold. Allow alerts at least 60 seconds apart and use the existing
chronological one-to-one matching. A mean budget is not a per-match cap.

The **primary contrast** is history/timely minus history/within60 under the
primary policy. The corresponding snapshot contrast and both false-only
contrasts are secondary. Report recall, both burdens, ordinary and timely
precision, opportunity-conditional recall, alert-burden quantiles, and region
slices with the pooled threshold. Lead summaries retain the original meaning:
they include all matched alerts, including late ones.

Report 2,000 route-stratified paired whole-match bootstrap draws for recall,
false burden and non-timely burden. These intervals condition on fitted models
and selected policies. They do not cover retraining, repeated-player dependence
or a population of future patches; multiple exploratory comparisons are not
confirmatory tests. Already-inspected calibration data remains exploratory.

An engineering gate supports further method study if the primary recall gain
is at least **2 percentage points**, its paired interval is above zero, both
models meet the pooled evaluation budget, and the candidate also meets that
budget in each route. This is a newly declared practical screening threshold,
not a replacement claim that the earlier ambitious +10-point goal was achieved.
The gate does not certify novelty or publishability. Failure is retained.

Average precision against the timely target is comparable across objectives.
Brier is reported **only against each model's own target**, so cross-target
Brier values must not be interpreted as comparative calibration. The scores
of a within60 model are not probabilities of the narrower timely event.

The observed fraction of events with a frame in the warning window is an
opportunity upper bound for frame-only alerts, not an attainable oracle score;
cooldown and matching can make the attainable maximum lower. All-event recall
remains primary. Region slices are not cross-region transfer experiments.

## Reproducibility and execution

The completed coordination screen is a prerequisite. Validate its original
source/dependency/data freeze and all train/calibration shard checksums, then
freeze the follow-up protocol and sources before fitting. Rebuild compact
feature matrices in a **separate output directory** from the cached shards;
do not stage raw matches again or overwrite previous models. Completed model
and score hashes are checked on resume. A killed partial fit is restarted.
The CLI locks its output and takes a shared lock on the source experiment so
the earlier writer cannot run concurrently.

```bash
cd /home/thivas/work/ai-portfolio/league-ews-audit
make start-timely-objective
make timely-objective-status
```

`make timely-objective` runs in the foreground; `MAX_NEW_MODELS=1` limits work
to one new fit. `make freeze-timely-objective` validates and freezes only.
No new packages or GPU configuration are required. This cheap controlled
experiment identifies whether changing the objective deserves inclusion in a
subsequent GPU player-history study.

Outputs: `data/private/timely-objective-v1/summary.json`, per-model score arrays,
models, candidate-selection metrics, full tuning curves and reports. Summary
includes actual row counts. The detached worker writes progress per candidate
fit plus an exit code. Source hashes changing after freeze require a fresh
output directory; never edit the freeze to bypass that check.

## Scientific scope and remaining work

Temporal training objectives and event-level alarm policies are established
research: [Temporal Label Smoothing, ICML 2023](https://proceedings.mlr.press/v202/yeche23a.html)
and [Dynamic Survival Analysis for Early Event Prediction, CHIL 2024](https://proceedings.mlr.press/v248/yeche24a.html).
This binary interval target is neither a reproduction of those methods nor an
originality claim. Successful timing results would motivate comparisons with
those approaches under equivalent information and evaluation.

Before a publication claim: freeze an amended joint final evaluation, preserve
the original registered analyses, compare appropriately tuned neural controls
over all assigned seeds, validate endpoint and observation semantics, evaluate
additional unseen patch transitions, examine player dependence where mappings
permit, and provide reproducible aggregate evidence. One sealed patch cannot
support broad patch robustness; a broader ML claim needs external validation.
