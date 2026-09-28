# Rare-event research path after the frozen M1 experiment

This is a prospective analysis and follow-on experiment plan, written while
the registered M1 ablations are running. It does **not** change their training
configuration, model checkpoints, final split, alert thresholds or sealed test
patch. The final test is still released once, after the existing M1 protocol
and operating decisions are frozen. Added comparisons are separately labeled
exploratory unless a new protocol is frozen before their own training.

## Three different sources of difficulty

1. **Sparse events:** most genuine prediction frames are negative, especially
   for Baron at 10 seconds. Measure positive rows per event, horizon, patch,
   route and partition; do not infer them from the number of event onsets.
2. **Sparse observations:** a real Match-V5 frame is commonly about a minute
   from the preceding one. The event-opportunity measure counts events with a
   strictly earlier genuine frame within each horizon. No reweighting method
   can create an observation that the API did not supply.
3. **Patch and within-match shift:** event rates and available features can
   differ by game time, patch, route and missing-position status. Balance the
   *match* sampling frame, but report the actual row and event distributions.

The local atlas (`make render-research-eda`) now computes these prevalence and
coverage diagnostics on train and calibration only. Its JSON summary is
ignored along with the HTML report. It is descriptive, not a hyperparameter
search over test labels or evidence that the graph is causal.

## Priority and comparison rules

| Priority | Proposed check | Evaluation | Decision boundary |
|---|---|---|---|
| 1 | Run `make audit-raw-field-coverage` for raw `totalGold`, `xp`, `level`, minion and position presence by train/calibration cell, and compare against normalized defaults. | Checksum-bound source-side counts; no test outcomes. | A nontrivial default rate requires a documented missingness sensitivity analysis before claiming those channels are measured. |
| 2 | Finish all six frozen ablations across ten seeds, including objective nodes, relations, independent heads and native timing. | Paired, whole-match calibration comparisons; all seeds reported. | A strong overall M1 AP alone does not establish which mechanism matters. |
| 3 | Describe 12 target prevalences and opportunity, calibration by event/horizon, event-time slices, and false alerts by match and game time. | Train/calibration diagnostics; report denominators and uncertainty across matches. | Choose a follow-on intervention for a measured failure, not for an appealing chart. |
| 4 | Only if warranted, freeze a separate imbalance sensitivity study before fitting. Compare original at-risk BCE with focal BCE (`gamma=2`) and a modest, train-derived positive weight (`min(5, sqrt(negative/positive))`) per event/bin. Keep architecture, seeds, shards and training budget equal. | Evaluate all variants on the original, unresampled calibration distribution: macro AP, per-target AP, Brier/calibration, event F1, recall, lead time and false alerts per game. Recalibrate thresholds on calibration only. | Weighting or focal loss wins only if its practical benefit is credible **and** risk calibration and alert burden remain acceptable. Do not add a weighted candidate to the original H1 claim after seeing its calibration result. |
| 5 | Study later-patch transfer, player overlap, teamfight proxy sensitivity and fair route slices. | Run the already registered final evaluation once after freezes; further variants require a separately dated protocol and a new untouched cohort. | Report negative results and uncertainty rather than selecting a favorable seed or slice. |

The suggested weight formula is a **proposal**, not an implemented or
preregistered treatment. Its exact application needs care: the event/bin
denominator must use only at-risk training bins, and no selection can use
calibration labels to compute training weights. Avoid synthetic timeline
interpolation and SMOTE on highly dependent frames. Report calibration and
alert burden because improving minority recall can make warnings unusable.

## Method claim

The original M1 uses event-specific conditional hazards with an at-risk mask;
it does not use class weights, focal loss or oversampling. The research
contribution under test is the complete causal, native-cadence graph and
coherent multi-horizon evaluation, **not** a newly invented imbalance loss.
Calibration results suggest promise, but a method claim depends on ablation
evidence and the sealed future-patch test. Operational coaching requires the
registered H5 criteria; row-level discrimination alone is insufficient.

## Primary research behind the comparisons

- Lin et al., [Focal Loss for Dense Object Detection](https://openaccess.thecvf.com/content_iccv_2017/html/Lin_Focal_Loss_for_ICCV_2017_paper.html), ICCV 2017. Focal loss downweights easy negatives; its effects in this event task are unknown until tested.
- Gensheimer and Narasimhan, [A Scalable Discrete-Time Survival Model for Neural Networks](https://peerj.com/articles/6257/), PeerJ 2019. Conditional discrete hazards motivate a likelihood with explicit at-risk bins.
- van den Goorbergh et al., [The harm of class imbalance corrections for risk prediction models](https://academic.oup.com/jamia/article/29/9/1525/6605096), JAMIA 2022. In their setting, resampling harmed probability calibration; this is a warning to check, not a result transferable automatically to League data.
- Menon et al., [Long-tail learning via logit adjustment](https://research.google/pubs/long-tail-learning-via-logit-adjustment/), ICLR 2021. Logit adjustment is another established baseline, not a new invention; its multiclass setting does not transfer directly to our independent hazard bins.
