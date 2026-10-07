# Regional warning-risk continuation

The [matched architecture study](../matched-optimization-2026-10-06/research-report.md)
retains a modest recall gain and repeats regional warning-budget failures.
This policy-only study tests a fixed uncertainty allowance, while measuring
its recall cost and separating it from a causal cap and threshold-order effects.
No model is retrained. No new policy has been replayed on League data yet.

## Fixed scope and estimands

Reuse five completed families: equal-weight useful-lead LeagueEWS, TCN and GRU,
original-weight useful-lead LeagueEWS, and useful-lead independent event
encoders. Keep three original seeds, three events, both evaluated horizons,
both regions, the four original budgets and the existing fine threshold grid.
This gives 90 heads, each with four budgets and two regional constraints.
All other prior results remain frozen and are linked rather than discarded.

Primary architecture endpoint: equal-weight LeagueEWS minus equal-weight TCN
macro 10–30-second timely recall under the new risk-screened policy, averaged
over the four fixed budgets. Retain the previous descriptive architecture,
event point non-harm, no-extra-burden and regional-consistency rules. They do
not replace any original gate. GRU and independent controls are secondary.
Do not rescue a failed primary with the best budget, seed, region or model.

The practical endpoint is whether every regional/event/seed budget-one cell
for equal-weight LeagueEWS has later empirical false-plus-late burden at most
one. Report every nominal-budget failure at all four budgets, not only this
hard-one endpoint. A finite sample satisfying an empirical budget is not a
population-risk guarantee. Report recall, precision, false and late burden,
all seed effects and paired intervals regardless of gate outcomes.

## Four policies distinguish the mechanisms

1. **Uncapped empirical:** reuse the exact earlier fine-grid common-threshold
   policy and later counts. This is the unchanged baseline.
2. **Capped empirical:** stop after four warnings per event per match. Maximize
   early timely hits among all thresholds whose empirical cost is at most the
   budget in each region. This isolates the cap's effect.
3. **Capped empirical sequence:** same cap; visit thresholds from highest to
   lowest and stop at the first failure of either empirical regional budget.
   Select the maximum-hit threshold only from that accepted prefix. This
   isolates the restriction to a fixed threshold order.
4. **Capped KL sequence:** same cap and order, replacing the empirical budget
   check with the fixed bounded-loss test below. This isolates the uncertainty
   allowance relative to policy 3. Silence is always a structural fallback.

All ties use higher early timely hits, then lower early false-plus-late cost,
then the higher threshold. One common threshold is used for both regions.
Cooldown stays 60 seconds. The cap counts emitted warnings, including useful
ones, without looking at future labels, event credit or final match duration.
The first four warnings are retained chronologically; no future top-score
selection is allowed. Four is a fixed design choice, not an empirically tuned
optimum. The cap bounds false-plus-late loss by four for every match, while
permitting more than one useful warning. All events remain in the denominator.
Independent replay must verify this behavior and unchanged opportunity counts.

For each region and threshold let C be summed false-plus-late warnings over
n early matches, a = C/(4n), and b = budget/4. Use p=1 when a>=b; otherwise
p=exp(−n KL(Bernoulli(a) || Bernoulli(b))). This is the Hoeffding KL bound,
without the optional Bentkus improvement. Allocate delta=0.05 across
5 families × 3 seeds × 3 events × 2 horizons × 4 budgets × 2 regions = 720
fixed sequences. Each receives 0.05/720. Stop each common sequence at the
first threshold with either regional p-value above that level. Never skip a
failure, retry another order or adjust delta after seeing results.

## Statistical provenance and limitations

[Learn then Test](https://arxiv.org/pdf/2110.01052), Sections 2.2–2.3, combines
bounded-loss concentration tests with family-wise error control. Its fixed
sequence test stops at the first failed rejection; the order must be chosen
without calibration outcomes. The nominal argument uses IID calibration and
test units and a fixed predictive procedure. We use complete matches as units,
with a union allocation over regional sequences. Choosing the highest-recall
member of an accepted prefix does not require independent threshold tests.
This applies an existing procedure, not a new method.

The original [Conformal Risk Control](https://research.google/pubs/conformal-risk-control/)
result assumes monotone loss. Chronological cooldown and event matching do not
justify that assumption for false-plus-late warnings. The later
[non-monotonic extension](https://arxiv.org/html/2602.20151v1) instead requires
appropriate stability conditions and exchangeability; it does not supply an
automatic guarantee for this adaptive research process. The finite-family
fixed sequence approach makes the selection restriction explicit here.

The League models and study choices were repeatedly adapted to these same
calibration matches. Thus this study **does not claim the nominal risk
guarantee holds for the completed research search**, and an early/later
chronological split does not prove IID behavior. A new patch can shift the
distribution. Even under the theoretical assumptions, controlling population
expected loss does not ensure every realized future regional average or match
is below the budget. Report these distinctions alongside the empirical result.

## Execution and analysis gates

Commit the plan, selector, replay, paired analysis and tests before selecting
new early policies. Bind all five score families, the archive, previous study
summary and source hashes. Finish and hash-freeze all 90 early heads before
replaying any new later policy. Verify the original fine-grid policy counts
exactly. Full independent scalar replay must cover every later match for all
three new budget-one policies and all heads; sample-check every other selected
threshold. Keep every warning cap and count-conservation check active.

Use the original 2,000 region-stratified whole-match bootstrap draws and seed
20261001. All policies/models share paired draws, with fixed training seeds.
Within-model contrasts are policy 2−1, 3−2 and 4−3, plus total 4−1; compute
them inside each draw. Architecture contrasts are retained under every policy.
Do not compare overlapping confidence intervals instead of paired effects.
Publish aggregate counts, by-seed values, interval tables, selected policies,
all gate failures and reproducibility hashes. Report cap activity and whether
silence was selected. Conditional intervals omit adaptive search uncertainty.

No new neural fit, test payload access or retroactive gate change is authorized
by this protocol. Fresh confirmation remains a separate requirement. A recall
loss accompanying better budget control is a tradeoff, not a breakthrough.
