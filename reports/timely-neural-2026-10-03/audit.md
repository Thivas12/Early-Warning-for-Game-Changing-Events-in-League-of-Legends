# Audit of mistakes and missing controls — 3 October 2026

The largest verified omission was **testing sharing and PCGrad before adding the
known useful-lead training control to the neural comparison**. The October 1
three-event tree report explicitly recommended that control. Preserving the
original cumulative-target experiment was necessary; treating it as sufficient
for subsequent mechanism work was not. Its numerical results remain evidence
about that fixed recipe. They cannot settle what a target-aligned neural model
would do. This follow-up corrects that experimental omission.

The audit also identifies limits that a successful fit will not erase:

| Issue | Evidence and correction |
|---|---|
| Training positives reward warnings counted as late | On the 24,000 training matches, 32.06% of Baron, 33.21% of Dragon and 33.18% of teamfight within-30 positives concern a next event less than ten seconds ahead. For within-60, the fractions below twenty seconds are 32.41%, 32.74% and 34.87%. Replace only the evaluated neural heads with next-event useful-lead targets; preserve all other training choices. |
| A label for any event in the useful interval can disagree with alert credit | The evaluator credits the earliest future event. A closer late event prevents a second later event from rescuing the warning. The new targets use the next strictly future event, not subtraction of nested binary labels or any-event-in-interval logic. Tests match an independent replay at the boundaries and with multiple future events. |
| The warning-efficiency diagnostic changed two policy properties together | The earlier report disclosed that its exact-cost mixture also selected thresholds per region. Add a regional deterministic control, making common-threshold → regional-threshold → regional-mixture changes inspectable. Do not attribute the entire change to cost matching. |
| Exact early budget equality is not later equality or a risk guarantee | The previous mixture hits the early boundary by design; later sampling and chronological drift produce many overruns. Keep the earlier failed gate unchanged. Report later cost with paired uncertainty and every violation; do not declare equivalence from an interval crossing zero or silently lower the required budget. |
| Observation cadence limits the task, but cannot excuse weak discrimination | Only 33.0–33.8% of training events have a real frame in the 10–30-second interval. The bound is 66.0–67.6% at 20–60 seconds, before cooldown/credit restrictions. No forward-filled or invented observations are added. Low teamfight recall remains far below this ceiling. |
| Architecture and transfer explanations were not fully identified | LeagueEWS has more parameters than TCN/GRU; independent encoders use more total compute. The history ablation removes past values while retaining current summaries, ages and valid lengths. Positive differences cannot establish a novel architecture, exact causal transfer mechanism, or which past channel matters. The new study tests supervision in two existing families and its interaction with family. |
| Repeated calibration inspection cannot become confirmation | The same patch has informed multiple follow-ups. Every new result remains adaptive exploratory evidence; seed repetition and narrower conditional intervals do not create fresh matches. Patch 16.17 stays sealed. |
| Stopping after the negative screen left the next justified control undone | The previous turn ended after publishing the warning-efficiency diagnostic. This continuation carries the omitted control through fitting, gated evaluation and interpretation rather than ending at another proposal. |

No arithmetic, replay or match-pairing bug has been found in the completed
warning-efficiency study. Its original count vectors and bootstrap estimates
reproduced exactly, and its conclusion was appropriately negative. Negative
results are not implementation failures to erase. The present corrections are
new, explicitly labelled comparisons; frozen prior studies remain unchanged.

The descriptive [objective audit](objective-audit.json) uses only the validated
League development archive, independently verifies the cumulative-positive
count decomposition, and records both regions and calibration halves. It is
neither a new model result nor a model-selection score. Its source is
`scripts/audit_neural_objectives.py`.

Target localization and warning-policy optimization are established research
ideas. The abstracts of [Yèche et al., CHIL 2024](https://proceedings.mlr.press/v248/yeche24a.html)
and [Damera Venkata and Bhattacharyya, NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/hash/c26a8494fe31695db965ae8b7244b7c1-Abstract-Conference.html)
were checked on October 3: they address localized event risk/alarm prioritization
and intervention timing respectively. This label control implements neither
paper and makes no new-method claim. A large engineering improvement would
still require a separate novelty and generalization argument.
