# Related work and novelty boundary

This is a living evidence map, not a claim that the search is exhaustive. The
final manuscript requires a second-author literature review and forward/backward
citation search before submission.

| Work | Setting | Contribution relevant here | What remains open |
|---|---|---|---|
| [Yang et al., 2022](https://arxiv.org/abs/2012.09424) | Honor of Kings | Predicts four important MOBA events and evaluates gradient-based attribution. | Does not establish League-specific, future-patch, calibrated alert utility. It also means “attention/event prediction” alone is not novel. |
| [Vardakis et al., 2026](https://doi.org/10.1016/j.entcom.2026.101091) | Commercial MOBA telemetry | Recent in-game event-prediction study. | Full text must be compared before freezing novelty claims; bibliographic discovery alone is insufficient. |
| [Caldeira et al., 2025](https://arxiv.org/abs/2506.02706) | League of Legends | Uses interaction/graph measures to study collective intelligence and match outcome. | Outcome prediction and aggregate graph measures differ from short-horizon event hazards. Graphs in League are therefore not novel by themselves. |
| [Chitayat et al., 2023](https://arxiv.org/abs/2305.18477) | Dota 2 | Uses game-design parameters for patch-agnostic analytics. | Does not study calibrated multi-event warnings, but establishes that patch robustness must be a baseline rather than an afterthought. |
| [Rossi et al., 2020](https://arxiv.org/abs/2006.10637) | General dynamic graphs | Temporal Graph Networks represent changing interactions as timed events. | Supplies a model family, not a domain contribution or evaluation protocol. |

## Defensible contribution target

The contribution is the combination of:

1. a causal, patch-indexed League event benchmark with exact timestamps;
2. coherent discrete hazards for several competing/recurrent strategic events;
3. a dynamic player–objective interaction representation;
4. future-patch and player-component evaluation;
5. calibration, alert burden, lead time and selective-abstention analysis; and
6. a public negative-results path if complex models do not beat schedule and
   history priors.

Each element has precedents. Novelty must come from the research question,
dataset/evaluation rigor and demonstrated empirical findings—not architecture
branding.

## Search strings for the submission review

- `(MOBA OR "League of Legends") AND (event prediction OR forecasting)`
- `(esports OR MOBA) AND (temporal graph OR point process OR survival)`
- `(game analytics) AND (patch drift OR temporal generalization)`
- `(early warning) AND (event-level evaluation OR alert fatigue)`
- citation graph around Yang 2022, Vardakis 2026 and Caldeira 2025

Databases to search: ACM Digital Library, IEEE Xplore, Scopus/Web of Science,
Google Scholar and arXiv. Search date, query and inclusion decision must be
recorded in the paper appendix.
