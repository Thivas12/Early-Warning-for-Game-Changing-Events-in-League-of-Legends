# Useful-lead supervision by task-sharing control

The original LeagueEWS report proposes temporal buildup and shared learning.
History controls now support additional past non-timing state for short-lead
Baron and teamfight warnings, while longer-lead Dragon can deteriorate.
The joint-versus-independent comparison and PCGrad controls used cumulative
labels. They cannot establish how sharing behaves after the useful-lead target
repair, which improved both the hybrid and TCN. This study fills that gap.

Run exactly nine independent event fits: three events by the original three
seeds. Use the completed independent backend unchanged, preserving the full
LeagueEWS initialization and dropout consumption while only the selected event
supervises the encoder. Replace only its evaluated30/60labels with useful next
10–30/20–60targets. Keep cumulative10/20auxiliaries and every training setting,
normalizer, batch, optimizer and per-event weight. Each fit uses576checkpointed
shard updates; total5184. No tuning or early stopping. This matches capacity
per event, not total compute: independent prediction uses three encoders.

Compare with the completed timely joint model and the two cumulative-label
controls. Primary: joint minus independent macro10–30recall at the equally
weighted mean of four prespecified matched-early budgets. Secondary: paired
target-by-sharing interaction, individual events/regions/seeds,20–60window,
all five previous policies, every budget and warning burden components.
Use the same2000paired whole-match region-stratified bootstrap draws and fixed
seeds. Rows, seeds and operating points are not independent matches. Report
all interval and seed signs, including losses. No best-head mixture is selected.

The plan defines descriptive support, event point non-harm, burden and regional
consistency rules. These do not authorize practical promotion: the completed
joint model's regional budget failures remain. The analysis is adaptive and
conditional on models and early policies, not fresh confirmation or novelty.
Sharing effects cannot separately identify gradient interference, loss scaling,
optimization or representation competition. Related established multitask
methods are recorded in the preceding task-sharing literature review.

Freeze this protocol and training code before the CUDA canary. Resume its exact
checkpoint in one locked worker. All nine fits must finish before scoring; a
missing committed-analysis release returns safely with zero new scores. Issue
the hash-bound release only after evaluator, analysis and source dependencies
are tested and committed. Freeze all234early policy heads before later replay.
Reproduce all216old heads across five policies exactly; independently replay
both common budget-one policies on all3000later matches for each of18new heads.
Additional fixed-sample checks cover every selected component threshold.

Use only the unchanged League development ZIP. All earlier checkpoints and
sources stay frozen. Patch16.17 stays sealed. Preserve the original registered
LeagueEWS-minus-GRU result and all failed gates. Publish aggregate evidence and
code only, excluding private score arrays and model binaries.
