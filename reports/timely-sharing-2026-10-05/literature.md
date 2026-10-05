# What this comparison can add to existing work

Targeted primary-source review on 5 October 2026, while the frozen nine-fit
study trains. This is a novelty check, not an exhaustive systematic review.
No external dataset or additional empirical fit is introduced.

| Prior work checked | Relevance and boundary |
|---|---|
| [Prediction of MOBA game events based on In-Game Data, 2026](https://www.sciencedirect.com/science/article/pii/S1875952126000133) | The publisher abstract describes League player-death forecasting with a Temporal Fusion Transformer, a five-second horizon and ten seconds of history, using fewer than 200 professional matches. Temporal neural event forecasting in League is already established. Its reported F1 is not comparable with our three-event timely recall at constrained warning burden. Only the publisher abstract was reviewed; this is not a replication or a full-method comparison. |
| [Dynamic Survival Analysis for Early Event Prediction, 2024](https://arxiv.org/html/2403.12818v1) | Sections 3.1–3.3 model the next recurrent event through episodes, truncate survival likelihood to the prediction horizon and use localized hazard information in alarm policies with silencing. Our minimum-lead binary labels are not that survival model. Aligning supervision with alarm timing is already a methodological topic; the distinction does not establish novelty. |
| [Gradient Surgery for Multi-Task Learning, NeurIPS 2020](https://proceedings.neurips.cc/paper/2020/hash/3fe78a8acf5fda99de95303940a2420c-Abstract.html) | The proceedings abstract describes gradient interference and a gradient-projection intervention. Applying that intervention is reuse of an established method. Our completed PCGrad control remains a mixed/negative result. |
| [Conflict-Averse Gradient Descent for Multi-task learning, NeurIPS 2021](https://proceedings.neurips.cc/paper/2021/hash/9d27fdf2477ffbff837d73ef7ae23db9-Abstract.html) | The proceedings abstract explicitly addresses average-loss optimization harming individual tasks, using their worst local improvement to regularize the trajectory. A future task-protection claim would require relevant established controls. |
| [Clinical Risk Prediction with Temporal Probabilistic Asymmetric Multi-Task Learning, AAAI 2021](https://ojs.aaai.org/index.php/AAAI/article/view/17097) | The proceedings abstract distinguishes improved task averages from individual-task harm and models time-dependent asymmetric transfer using feature uncertainty. Temporal/asymmetric sharing alone is not a new concept. No non-League performance is used as evidence for League. |

The current study's intended contribution is narrower: measure whether replacing
cumulative targets with useful-lead targets changes the sharing effect in the
same LeagueEWS descendant. It completes an explicit two-by-two control on the
same matches, fixed seeds and policies. The paired interaction can reveal a
dependency between two implementation choices. It cannot establish a new
multitask algorithm, identify the optimizer mechanism, or validate deployment.

Searches for League event prediction, teamfight prediction and multitask
prediction did not establish whether an identical three-event comparison has
already been published. Search non-detection is not evidence of priority. A
small favorable interval on repeatedly inspected calibration would not resolve
that question. Any claim must retain the regional warning failures, observation
cadence, resource imbalance and conditional uncertainty documented in the audit.
Patch 16.17 remains outside this review and study.
