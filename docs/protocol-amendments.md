# Registered protocol amendments

This file records changes made after `docs/research-plan.md` was frozen. An
amendment states when it occurred, what evidence was available and whether it
changes a hypothesis, outcome or decision rule.

## 2026-09-15 — align processed horizons with the registered protocol

**Stage:** after one operational Match-V5 canary; before the research pilot,
model fitting, threshold selection or outcome analysis.

The frozen research plan and `configs/rifthazard-v2.yaml` both specify 10, 20,
30 and 60-second horizons. The processing default accidentally contained only
10, 20 and 30 seconds. Research-v2 processing is corrected to emit all four
registered horizons. The legacy audit remains fixed to the 10, 20 and 30-second
columns that exist in the historical dataset.

This is an implementation-conformance correction. It does not change a
hypothesis, primary outcome, split rule, event definition or pass criterion.
No model result was available or inspected when the correction was made.

## 2026-09-15 — record native-cadence label opportunities

**Stage:** after the operational canary; before the research pilot, model
fitting, threshold selection or outcome analysis.

Raw validation now reports within-match snapshot intervals and, for every
registered event/horizon pair, the fraction of events that have at least one
genuine strictly prior observation within the forecast horizon. This is a
descriptive opportunity diagnostic, not a model-performance measure or data
quality threshold. It does not interpolate, forward-fill or otherwise create
additional observations.

This addition makes the registered native-versus-fixed-cadence ablation and
short-horizon feasibility limits auditable. It does not change a hypothesis,
outcome, event definition, horizon or pass criterion. No model result was
available or inspected when the diagnostic was added.
