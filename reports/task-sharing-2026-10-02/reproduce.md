# Reproduce the League task sharing study

The frozen comparison trains nine independent event encoders against the three
completed joint LeagueEWS controls. It tests the original report's shared learning
explanation on the existing development cohort. [The plan](plan.json) records the
intervention and interpretation rules before fitting. The earlier registered
LeagueEWS versus GRU comparison remains unchanged.

## Fixed training implementation

Training is frozen at commit `5c66ffe` on `research/league-task-sharing-20261002`.
The private freeze is
`ae2f54e1006b09153acfd08e383752c1ebe996112b665fc6a005bfc3ee286bbe`.
Resume using the same files and CUDA environment. Analysis and documentation may
be added subsequently without editing the frozen training dependencies.

Each independent fit retains the complete original initialization and forward
path. The two unused heads are frozen; only the selected event's four horizons
contribute gradients. Their original weights are 1.0, 2.0 and 2.5 for Baron,
Dragon and teamfight. They are not renormalized. Retaining the inert heads also
retains Baron's dropout RNG consumption during Dragon and teamfight training.
Only the selected event's predictions are published into the private score file.

Each fit has 1,749,591 trainable parameters and 1,751,647 allocated parameters.
The independent system uses three encoders, versus one joint encoder. This
matches encoder capacity per task, not total compute or model storage. All fits
use 12 epochs, 48 shards per epoch, the original three seeds, and the original
batch and optimizer settings. There is no early stopping or model selection.

The runner verifies the preserved GPU checkout against every original source
hash. The sole maintained-source difference permitted is the pinned formatting
repair in `scripts/run_three_event_trees.py`; its AST must equal the preserved
source. Exporter, backend, input, normalization and warning-policy sources remain
byte-identical. The original experiment files and environments are not rewritten.

## Local execution

The development ZIP and checkpoints are private and excluded from Git. These
commands refer to the verified local paths. Start a runner only after checking
host processes, GPU use and output locks. The shell wrapper and Python runner
both acquire exclusive locks. The original completed experiment is held under
a read-only shared lock. Use a monitored foreground session.

```bash
cd /home/thivas/work/ai-portfolio/league-ews-audit/tmp/league-ews-task-sharing-20261002
bash scripts/run_task_sharing.sh \
  /home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  /home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-three-event-export-v1/development.zip \
  /home/thivas/work/ai-portfolio/league-ews-gpu/data/private/compact-notebook-v1 \
  /home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-task-sharing-v1 \
  reports/task-sharing-2026-10-02/plan.json \
  /home/thivas/work/ai-portfolio/league-ews-gpu
```

An interruption resumes the same checkpoint, including optimizer and CPU/CUDA
RNG state. Checkpoints are replaced atomically after each shard. The runner
repairs a lagging progress record from its bound checkpoint after an interrupted
write. It rejects changed source, plan, archive, runtime or control artifacts.
All nine fits must finish before scoring any new fitted model. Calibration
validation during archive checking is distinct from fitted-model evaluation.

## Analysis after completion

```bash
PYTHONPATH=.:src /home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  -m scripts.analyse_task_sharing \
  --study /home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-task-sharing-v1 \
  --control /home/thivas/work/ai-portfolio/league-ews-gpu/data/private/compact-notebook-v1 \
  --archive /home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-three-event-export-v1/development.zip \
  --output reports/task-sharing-2026-10-02
PYTHONPATH=.:src /home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  -m scripts.render_task_sharing \
  --input reports/task-sharing-2026-10-02/analysis.json \
  --output reports/task-sharing-2026-10-02/tables.md
```

Analysis verifies exact selected-event labels and match offsets, all nine fit
bindings, and independent warning replays on all 6,000 calibration matches. The
early 3,000 select thresholds; the later 3,000 evaluate them. It verifies regional
counts and budgets before bootstrapping. There are 2,000 whole-match draws within
region, paired across every event, model and seed. Intervals condition on the
fitted models and thresholds; seed means do not triple the match sample size.
The already inspected calibration cohort makes this exploratory development.

Only aggregate reports, logs, code, protocols and artifact hashes belong in the
results branch. Patch 16.17 is excluded from the archive and remains sealed.
