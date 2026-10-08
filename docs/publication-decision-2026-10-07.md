# Publication decision: end incremental calibration search

Decision dated 7 October 2026, using completed evidence through commit
`4786728c80103c29675ff88934a92898759260c6`.

**A breakthrough has not been demonstrated. The current evidence supports an
exploratory empirical paper, not a new-method or broad-superiority paper.**
The next Hoeffding–Bentkus/empirical-Bernstein comparison is not being launched.
Changing an established concentration bound cannot by itself identify a new
predictive mechanism, resolve architecture confounding, or provide untouched
confirmation. No source, policy, fit, result or failed gate is rewritten.

The [paper draft](leagueews-paper-draft.md) brings the completed experiments
together around one question: which proposed explanations for LeagueEWS survive
controlled evaluation? Its answer is differentiated: useful target alignment
and some past state help, uniform beneficial sharing does not, and the hybrid's
remaining TCN advantage is small and recipe-dependent. This is a scientific
result worth assessing on its merits. It is not evidence that a venue will
accept the paper, and it does not fulfill the requested breakthrough.

## Claims and decisions

| Proposed claim | Evidence that matters | Decision |
|---|---|---|
| The original high AUC proves generalization | Overlapping within-match windows, pre-split scaling and end-of-match features contaminate the original evaluation | Exclude from empirical support; preserve as the motivation for the audit |
| The hybrid is broadly superior to strong temporal controls | Original LeagueEWS–TCN difference +0.012 points [−0.156, +0.178]; latest loss-matched comparison +0.242 [0.130, 0.354], with regional uncertainty and unmatched capacity | Reject broad superiority and component attribution; report both comparisons |
| Past non-timing state adds useful information under the fixed recipe | Conditional history contrast +0.533 points [0.374, 0.696] at short lead, all macro seed signs and both regional intervals positive; aggregate burden falls | Retain this narrow exploratory representation finding; disclose the timing deviation and mixed longer-lead results |
| Sharing benefits all three events | Useful-lead joint–independent difference −0.061 [−0.219, +0.099] short lead and −0.664 [−0.925, −0.397] longer lead, with substantial Baron harm | Reject uniform sharing benefit; retain task-dependent effects under the tested recipes |
| PCGrad resolves negative transfer | Its primary benefit is unclear at matched early cost and after equal weighting | Reject; do not rename or repackage the established optimizer as a discovery |
| Better warning-budget compliance establishes better prediction | Capped KL selection has 0/720 observed nominal violations, while LeagueEWS loses 1.818 short-lead and 3.114 longer-lead recall points | Retain the measured operating tradeoff; reject frontier improvement and adaptive-search certification |
| All internal gates must pass before any paper can be written | Some gates target a particular mechanism, practical promotion or strict burden superiority | Incorrect: preserve their outcomes, but restrict the relevant claims rather than declaring all negative results unpublishable |
| The current data prove a publication-quality breakthrough | No untouched confirmation of the adaptive candidate; no distinct established methodological advance | Unsupported |

Recall differences are percentage points. The listed intervals are pointwise,
conditional, paired whole-match bootstrap intervals; they exclude adaptive
search and refitting uncertainty. The table combines separately specified
contrasts and operating policies, not interchangeable estimates of one effect.

## What the internal gates actually mean

An upper confidence limit above zero for additional burden does not prove that
burden increased. Similarly, an interval spanning zero does not establish
equivalence, and a regional interval spanning zero does not establish a
regional reversal. These distinctions must survive the paper's wording.

A method can meet a practical burden limit while having uncertain burden
superiority over another method. Requiring statistically lower burden is a
stronger claim than meeting the same allowed budget. Neither criterion should
be substituted for the other after examining results. Previous registered
screen outcomes remain exactly as reported.

Publication quality also requires a meaningful question, correct methods,
honest uncertainty and a contribution relative to prior work. It is not
equivalent to passing every exploratory screen. Conversely, passing software
tests or all observed regional budget cells does not establish novelty.

## Stop rules for this continuation

Do not launch another model, loss, threshold, bound or seed sweep solely because
the latest comparison is small or a gate failed. Do not repeatedly consume a
holdout until a positive result appears. Do not introduce a new acronym for the
same components. No further development experiment is selected by this memo.

For the existing empirical paper, the remaining decisive work is a single
frozen confirmation of a bounded set of claims, not another development search.
Before that evaluation, one executable protocol must bind the exact saved
models and policies, endpoints, complete comparison family, multiplicity
handling and one-time reporting rule. It must distinguish a directional
scientific hypothesis from practical superiority: a minimum worthwhile effect
or noninferiority margin needs an external use-case justification, not a value
chosen to fit these results. A negative confirmation must remain the paper's
result. It must not trigger automatic retuning on that patch.

The existing development ZIP excludes patch-16.17 payloads. The current local
workspace also has original processed-data directories and split metadata;
therefore a blanket claim that the user's held-out data are unavailable is not
justified. Their payload availability and integrity have not been established
in this synthesis. No held-out payload was opened. This memo does not change
the sealed-test boundary or constitute an executable release protocol.

The draft is explicitly a development-study manuscript until that work is
complete. A full comparison with the closest 2026 League paper also remains
limited by full-text access. These are concrete unresolved limitations, not
reasons to generate an unlimited list of additional experiments.

## Evidence and literature audit

The accompanying [source index](../reports/publication-synthesis-2026-10-07/sources.json)
binds the completed reports and manuscript dependencies by SHA-256. It records
provenance, not independent reanalysis. The draft carries local source links
next to each empirical claim, preserves original negative outcomes, identifies
all policy changes and contains no new empirical score.

A targeted primary-source check on 7 October 2026 used these queries:

- `"League of Legends" "early warning" event prediction Baron Dragon teamfight`
- `"Prediction of MOBA game events based on In-Game Data"`
- `"Dynamic Survival Analysis for Early Event Prediction"`
- `"Learn then Test" calibrating predictive algorithms risk control 2110.01052`

The publisher's indexed abstract for [Vardakis et al.](https://www.sciencedirect.com/science/article/pii/S1875952126000133)
describes imminent League player-death prediction using a Temporal Fusion
Transformer. Direct full-text retrieval returned HTTP 403; its split quality
and detailed baselines have not been assessed. The [Yang et al. author abstract](https://arxiv.org/abs/2012.09424)
already establishes multi-event MOBA prediction. The [Yèche et al. proceedings abstract](https://proceedings.mlr.press/v248/yeche24a.html)
establishes event-level alarm prioritization using localized temporal risk.
The [version-pinned Learn then Test manuscript](https://arxiv.org/pdf/2110.01052v5)
supplies risk testing and fixed-sequence methodology, with the IID calibration
requirement stated in Section 1.1. A tighter bound from that literature would
be an implementation choice, not a novel LeagueEWS contribution. This targeted
check is not an exhaustive systematic review.
