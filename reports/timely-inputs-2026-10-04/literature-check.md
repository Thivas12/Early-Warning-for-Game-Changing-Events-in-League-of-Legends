# Targeted literature recheck, 4 October 2026

This is a limited novelty check, not a systematic review or additional empirical
League evidence. The present input ablations remain fixed regardless of it.

[Vardakis et al., Entertainment Computing 57 (2026), 101091](https://www.sciencedirect.com/science/article/pii/S1875952126000133)
already study imminent player deaths in professional League using a Temporal
Fusion Transformer. The publisher abstract reports a five-second horizon and
ten seconds of history. That task, cadence and event-level endpoint differ from
this study. The abstract was accessible in search; direct article retrieval
returned 403. No claim about their full methods, leakage or split validity is
made. A temporal neural League predictor is not, by itself, new.

[Yèche et al., Dynamic Survival Analysis for Early Event Prediction](https://arxiv.org/html/2403.12818v1)
was inspected beyond its abstract: sections 3.1–3.3 of the March 2024 author
manuscript describe next-event episodes, a truncated hazard likelihood and alarm
prioritization using risk localization. Their silencing rule uses elapsed time
since the last alert, without requiring its outcome to be known. This precedes
our work on useful-lead targets and chronological policies. The present binary
window labels do not implement their hazard model or smoothing method. Our
minimum useful lead also differs from their emphasis on imminent risk, so their
reported healthcare gains cannot predict our League results. The
[CHIL proceedings record](https://proceedings.mlr.press/v248/yeche24a.html)
confirms the later publication; the inspected full text was the earlier version.

The current contribution under investigation is narrower: which observed input
information remains useful for three League events after objective alignment,
under controlled warning costs and matched whole-match comparisons. A positive
input-ablation result is a mechanism diagnostic. It still needs an explanation
that survives strong controls and fresh generalization evidence before a strong
scientific claim; it does not become a new learning method by receiving a name.
