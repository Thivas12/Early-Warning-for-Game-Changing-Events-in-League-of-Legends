# Run the original LeagueEWS continuation on the PC's GPU

**Latest completed follow-up, 4 October 2026:** the [conditional history study](../reports/clock-history-2026-10-04/research-report.md) completed three further fits and all 216 policy heads. Past non-timing state adds +.533 recall points [.374, .696] beyond genuine timer history and current state at 10–30 seconds, with all seed and regional macro effects positive and lower aggregate burden. Longer-lead Dragon declines; regional budget gates remain failed. The analysis hash record preceded scoring, but Git approval delayed its commit until afterward; [the deviation and enforced future release procedure](../reports/clock-history-2026-10-04/scoring-release-repair.md) are explicit. Preserve all 42 completed neural fits. No worker needs restarting, no breakthrough is claimed, and patch 16.17 stays sealed.

**Useful-lead input controls completed, 4 October 2026:** six additional LeagueEWS fits and all 198 policy heads finished. A native crash in the final seed was recovered from a verified checkpoint; the resumed worker exited zero and all five previously completed checkpoints were unchanged. The [report](../reports/timely-inputs-2026-10-04/research-report.md) supports a short-lead history benefit, with longer-lead and regional limitations. Use the [pinned reproduction record](../reports/timely-inputs-2026-10-04/reproduce.md); preserve all 39 completed neural fits. This study's GPU worker is finished. Patch 16.17 remains sealed.

The uploaded development ZIP is validated and usable. No further collection,
export or upload is required. This runner reads that exact ZIP directly.

**Completed, 1 October 2026:** CUDA was verified on the RTX 4060 Laptop GPU.
All twelve fits, 6,912 shard updates and twelve gated evaluations finished with
exit code 0. The [results](../reports/neural-continuation-2026-10-01/research-report.md)
and [status verification](../reports/neural-continuation-2026-10-01/status-verification.json)
record the actual execution. The launch instructions below describe the original
run; inspect its existing output before using them. For recovery, use the
[pinned source and environment](../reports/neural-continuation-2026-10-01/reproduce.md).

**Follow-up completed, 2 October 2026:** nine independent event encoders finished
5,184 updates and nine gated evaluations with exit code 0. Their
[results and interpretation](../reports/task-sharing-2026-10-02/research-report.md)
and [separate frozen runner](../reports/task-sharing-2026-10-02/reproduce.md)
preserve this original experiment. Patch 16.17 remains sealed.

**Further follow-up, analysed 3 October 2026:** all three PCGrad fits completed
1,728 shard updates and gated evaluation, exit code 0. The
[results](../reports/gradient-conflict-2026-10-02/research-report.md) fail the
frozen practical screen: additional mean primary recall carries more warning
burden, does not recover Baron and is not positive in every seed. Preserve its
[separate frozen outputs and runner](../reports/gradient-conflict-2026-10-02/reproduce.md).
There is no running training worker to duplicate or completed fit to restart.

**CPU follow-up completed, 3 October 2026:** the separately frozen
[warning-efficiency analysis](../reports/warning-efficiency-2026-10-03/research-report.md)
reused all completed scores. Its 126 early heads and 126 later heads are complete;
no new training is needed to reproduce it. PCGrad fails the new diagnostic screen.
Use the [separate replay instructions](../reports/warning-efficiency-2026-10-03/reproduce.md)
and preserve all original GPU experiment files and checkpoints.

**Timely-target control completed, 4 October 2026:** six new LeagueEWS/TCN fits
finished 3,456 updates, followed by all 162 gated policy heads. The
[results](../reports/timely-neural-2026-10-03/research-report.md) find consistent
objective-alignment gains, particularly secondary Dragon, but fail the frozen
practical screen. The [separate runner](../reports/timely-neural-2026-10-03/reproduce.md)
preserves all prior studies. No GPU worker remains active. Patch 16.17 is sealed.

**Threshold-resolution control completed, 4 October 2026:** all 72 early and
72 later heads finished with no new training. The [results](../reports/dense-policy-2026-10-04/research-report.md)
recover a deterministic useful-lead target gain, but warning-cost and regional
gates remain unresolved. Preserve the [separate replay](../reports/dense-policy-2026-10-04/reproduce.md)
and every earlier experiment. No worker is active.

## Model and fixed experiment

The original LeagueEWS descendant is unchanged: residual TCN with squeeze-excitation,
two bidirectional GRUs, cross-attention, self-attention, temporal pooling,
shared dense layers and three event heads. Its implementation is
`src/league_ews/notebook_ews.py`, reviewed against the MSc notebook in
[the source review](notebook-continuation.md).

| Setting | Fixed value |
|---|---|
| Families | LeagueEWS, GRU, TCN, current-frame MLP |
| Seeds | 20260930, 20261001, 20261002 |
| Training population | 24,000 matches; 704,967 observed rows; patches 16.12–16.15 |
| Calibration | 6,000 matches; 175,031 rows; patch 16.16 |
| History | Eight real observed frames; 27 values, 27 missingness flags and age |
| Targets | Baron, Dragon and teamfight, each at 10/20/30/60 seconds |
| Training | 12 epochs; batch 256; AdamW, learning rate 0.0001, weight decay 0.0001 |
| Loss | Original event weights 1 / 2 / 2.5; unchanged twelve binary outputs |
| Device | CUDA by default; unavailable CUDA causes an explicit error |
| Checkpoint | Every 500-match training shard, including model, optimizer and RNG |
| Evaluation | All 12 fits finish before fitted-model calibration scoring begins |

This is an alternate input runner for the already specified experiment, not an
additional model family or a changed loss. Do not launch it alongside an already
running complete `notebook-continuation` study. The new outputs are separate from
the earlier runner's checkpoints, so existing results are preserved.

The compact reader reconstructs the same B4 histories, fits normalization only
on training current frames in original shard order, and uses the original backend
and batch-order seeds. It has software checks for bit-identical inputs and model
predictions, exact checkpoint continuation, target separation, training-only
normalization and the calibration scoring gate. Package/CUDA version and device differences can change
numerical results; cross-device bit-identical training is not promised.

## Start in WSL

These commands create a separate code checkout and use the existing environment
and ZIP. They do not switch the existing audit checkout or reinstall PyTorch.

```bash
cd /home/thivas/work/ai-portfolio/league-ews-audit
git fetch origin research/league-real-three-event-screen
git worktree add --detach ../league-ews-gpu origin/research/league-real-three-event-screen
cd ../league-ews-gpu
export LEAGUE_PYTHON=../league-ews-audit/.venv/bin/python
export LEAGUE_ARCHIVE=../league-ews-audit/data/private/league-three-event-export-v1/development.zip
make compact-notebook-canary DEVICE=cuda && make start-compact-notebook DEVICE=cuda
```

Create the worktree once. The canary prints the actual GPU name, torch/CUDA build,
trains one real shard and checkpoints it. The background worker resumes there
and survives closing the terminal. A duplicate worker for this output is rejected.
If CUDA is unavailable, copy the error; the runner will not quietly train on CPU.

Progress, including after opening a new terminal:

```bash
cd /home/thivas/work/ai-portfolio/league-ews-gpu
make compact-notebook-status LEAGUE_PYTHON=../league-ews-audit/.venv/bin/python
```

There are 6,912 shard updates: 48 shards × 12 epochs × 12 fits. Calibration report
count stays zero during training by design. The canary reports real shard time;
no whole-study duration is promised before observing the hardware's performance.

Results are written under `league-ews-gpu/data/private/compact-notebook-v1/`.
When complete, upload `summary.json` from that folder. Each fit also preserves
its checkpoint, progress, row predictions, match counts and report. To resume
after interruption, set the same two variables and rerun the start target.
The freeze rejects changed source, data, device or runtime rather than mixing runs.

## Research interpretation

Primary neural contrast remains LeagueEWS minus GRU in macro 10–30-second timely
recall. All three events and regional false-plus-late warning budgets are reported.
The available calibration data have already been examined: these are development
results. Patch-16.17 payloads are absent from the ZIP and are not requested.

The new tree results provide necessary controls but do not test neural task
sharing. A positive hybrid result still needs the separately specified mechanism
ablations and a frozen confirmatory evaluation before a novelty claim.
