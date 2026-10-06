# Matched optimization for the original sequence controls

The completed [weighting study](../timely-optimization-2026-10-05/research-report.md)
supports a primary recall gain from equal event weights within LeagueEWS.
Its favorable comparison against useful-lead TCN still changes both architecture
and loss weighting. Useful-lead GRU controls have not yet been fitted. The next
study closes those specific gaps before any revised architecture claim.

The [fixed plan](plan.json) adds nine fits: equal-weight TCN, original-weight
GRU and equal-weight GRU, each using the original three seeds. Existing
original/equal-weight LeagueEWS and original-weight TCN are reused unchanged.
All cells use useful-lead evaluated heads, the same cumulative auxiliary heads,
observations, normalizer, optimizer and twelve-epoch schedule. PCGrad is absent
from every new fit. Original within-architecture initializations and batch/RNG
streams are preserved; weights are either (1, 2, 2.5) or (11/6, 11/6, 11/6).

The primary comparison is equal-weight LeagueEWS minus equal-weight TCN macro
10–30-second recall, equally averaged over the four fixed matched-early budgets.
The GRU comparison, longer lead and architecture-by-weighting interactions are
secondary and cannot replace a failed primary result. Each interaction is
computed within every paired whole-match bootstrap draw. All prior estimates,
all events, both regions, all seeds, policies and budgets must be retained.

The architecture sizes remain those of the original notebook continuation:
LeagueEWS 1,751,647 parameters, TCN 557,087 and GRU 912,717. Matching loss weights
does not equalize capacity or computation, isolate an individual encoder layer,
or establish optimally tuned baselines. Report those limits and measured costs.

The descriptive rules require a positive primary conditional interval and
every seed positive, no negative aggregate event point estimate, no-extra-burden
upper bound at most zero, and supported regional macro effects with every seed
positive. Secondary GRU support is evaluated separately. Event point non-harm
is not a noninferiority test. Every event/region budget failure is reported.

Before fitting, commit the plan and verified runner. Start with a one-shard
CUDA canary and resume that checkpoint in one locked worker. Complete all nine
fits before scoring; require a hash-bound committed-analysis release. Freeze
all 342 early policy heads before later replay, including exact reproduction
of all 288 previous heads. Verify new heads with independent replay on every
later match for both common budget-one policies, then compute the frozen paired
analysis. Preserve the original study freezes and checkpoints throughout.

This is adaptive exploratory development on already inspected calibration.
Matching optimization tests one confound; it does not establish novelty or
fresh generalization. Existing budget failures remain failed, and patch 16.17
stays sealed. No new architecture, hyperparameter search or method name is
introduced by this control study.
