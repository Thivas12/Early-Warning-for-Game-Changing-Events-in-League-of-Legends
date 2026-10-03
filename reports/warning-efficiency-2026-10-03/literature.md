# Targeted warning-policy literature check — 3 October 2026

This checks the rationale and limits of the operating-point diagnostic. It is
not an exhaustive League novelty search. All empirical findings in this study
use the audited League archive exclusively.

- Provost and Fawcett, *Robust Classification for Imprecise Environments*
  ([author manuscript](https://arxiv.org/abs/cs/0009007), 2000 manuscript;
  Machine Learning, 2001). The full manuscript's Theorem 7 constructs points
  between classifiers by randomized selection, and its constrained ROC analysis
  shows why the preferred classifier can depend on the operating requirement.
  Convex combinations and operating-point sensitivity are established ideas.
  Here a component is an entire match policy, preserving temporal cooldown and
  event credit. Its cost axis is false-plus-late warnings per match, not ordinary
  binary-classification false-positive rate. The paper does not establish our
  later-calibration budget, chronological generalization or policy optimality.
- Bilen et al., *A Framework for the Robust Evaluation of Sound Event Detection*
  ([author manuscript](https://arxiv.org/abs/1910.08440), ICASSP 2020).
  Its abstract describes event evaluation using operating-point curves and a
  summary score instead of a single threshold score. This supports looking at
  multiple fixed budgets as established evaluation practice. We do not implement
  its sound-detection metric or use its empirical results as League evidence.
- Angelopoulos et al., *Learn then Test: Calibrating Predictive Algorithms to
  Achieve Risk Control* ([author manuscript](https://arxiv.org/abs/2110.01052),
  revision 2022). Its abstract describes finite-sample risk guarantees obtained
  through a multiple-testing formulation. Our empirical early-cost matching is
  not that procedure and offers no such guarantee. Chronological drift and
  repeated development inspection remain limitations.

The last two entries were checked at abstract level; no unexamined full-text
claims are attributed to them. There are no direct quotations here. A favourable
League curve would be an exploratory model comparison, not a new convex-hull
method or a first event-warning metric.
