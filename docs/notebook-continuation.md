# Continue from the original LeagueEWS project

**Update, 3 October 2026:** the three separately frozen PCGrad fits and gated
evaluation completed. The [mechanism report](../reports/gradient-conflict-2026-10-02/research-report.md)
records a mean primary macro gain with more warning burden, a negative seed,
unrecovered Baron recall and a Europe Dragon budget failure. At longer lead,
Baron improves while Dragon and teamfights decline. The practical screen fails;
this established optimization method does not resolve the sharing tradeoff.
Use its [pinned reproduction record](../reports/gradient-conflict-2026-10-02/reproduce.md).
All original freezes remain unchanged, and patch 16.17 remains sealed.

**Update, 2 October 2026:** the nine independent event fits also completed.
[Joint versus independent results](../reports/task-sharing-2026-10-02/research-report.md)
show higher Dragon recall and lower Baron recall under joint training, with
failed regional budgets. The shared-learning explanation is task-dependent;
no breakthrough is established. Use the study's
[separate reproduction record](../reports/task-sharing-2026-10-02/reproduce.md).

**Update, 1 October 2026:** the validated development ZIP supported nine tree
controls, all twelve neural fits and three history-ablation fits. The
[completed neural report](../reports/neural-continuation-2026-10-01/research-report.md)
records higher recall than GRU, no clear advantage over TCN, and failed regional
warning-budget gates. The earlier access and implementation status below is
historical. Use the [pinned reproduction instructions](../reports/neural-continuation-2026-10-01/reproduce.md)
to preserve the completed experiments; no new upload is required.

The starting point is Keerthivasan Kannan's **LeagueEWS**, described in the
55-page final report and implemented in the original model-building notebooks.
The research question covers **Baron, Dragon and teamfights**. The original
architecture and its hypotheses must be evaluated directly before replacing
them with an unrelated model family or narrowing the entire project to Dragon.

## What the original project actually did

Reviewed sources are under `legacy/msc-v1`: `LOL Final Report.pdf`,
`LOL Data Gen - Final.ipynb`, both EDA versions, and both model-building versions.
The two model notebooks have identical code despite different markdown/images.
Cell numbers below are zero-based in `EWS_model_building.ipynb`.
All source hashes and recovered saved tables are recorded in
[the machine-readable review](../reports/notebook-source-review-2026-09-30.json).

| Component | Original implementation and evidence |
|---|---|
| Collection | Riot EUW ranked queue 420; ladder-seeded match and timeline collection; generator cells 2–11 |
| Saved dataset | 484,255 rows and 86 columns in EDA cell 13; these are the artifacts currently in this repository |
| Features | Economy, XP, CS, combat, vision, timers, objective proximity and team spread; 75 selected columns plus within-match first differences make 150 model inputs; model cell 5 |
| Sequences | 40 rows per window, stride 5; 74,728 base windows; two reflected jitter copies give 224,184 windows; model cell 8 |
| Task | Three events, each with next-10/20/30-second binary labels; sequence target is the final row's nine-label vector |
| Controls | Nine independent random forests and a last-frame MLP |
| LeagueEWS | Residual dilated TCN with squeeze-excitation; two stacked BiGRUs; TCN-to-GRU and representation-to-input cross-attention; self-attention; learned temporal pooling; shared dense layers; three event heads |
| Selected architecture | TCN widths 80/160/160, dilations 1/2/4; two 160-unit-per-direction BiGRUs; four attention heads with key dimension 64; 128-wide fused sequence; shared 512/256 dense layers; dropout 0.5; model cells 60/63/64 |
| Training | AdamW, five six-epoch tuning trials, up to 30 final epochs, event loss weights 1/2/2.5; report pages 13–14 and model cells 63/68 |
| Intended use | Offline coaching/research, explicitly stated in the report's ethics section, page 20 |

The report's most important hypothesis is on page 21: **temporal buildup and
shared learning across events explain the hybrid's gains**. The component list
alone does not establish that explanation. It needs sequence controls and,
separately, matched single-task versus shared-task comparisons.

## Saved results, without changing their meaning

These are the **recorded notebook outputs**, not freshly reproduced estimates:

| Model | Baron AUC | Dragon AUC | Teamfight AUC |
|---|---:|---:|---:|
| Random forest | 0.975212 | 0.916203 | 0.698452 |
| Last-frame MLP | 0.972985 | 0.733707 | 0.741425 |
| LeagueEWS | 0.986737 | 0.949880 | 0.922940 |

Cells 17, 38 and 71 compute the **arithmetic mean over 10/20/30-second
horizons**. The ROC plots separately display 30-second curves. Calling the
table a 30-second-only result conflates different outputs.

The final report's page-16 MLP Dragon row says precision 0.20 and Brier 0.16.
The saved notebook instead gives 0.388889 and 0.047362. The report's abstract
also says approximately 8,000 sequences, while its methodology and notebook
record 74,728 before augmentation. These discrepancies are recorded here;
the historical report and notebook files remain unchanged.

Re-extract the saved evidence without running any notebook or fitting a model:

```bash
python3 scripts/recover_notebook_evidence.py
```

## Corrections that matter to the original hypothesis

1. **Split first, then build windows.** The original notebook standardizes all
   rows, creates overlapping windows, makes jitter copies, then randomly splits
   those copies. Training and evaluation therefore share matches and overlapping
   histories. The existing [legacy audit](legacy-audit.md) quantifies this.
2. **Separate past observations from final match outcomes.** Generator cell 23
   joins end-of-match player statistics onto every timestamp. The model's broad
   numeric-column selection admits them. The continuation uses the audited
   current/past feature allowlist and training-only normalization.
3. **Keep the meaning of cadence.** The generator holds frame values forward on
   a 10-second grid; those rows are not independent 10-second measurements.
   Forty such rows span 390 seconds. The continuation uses eight genuine frames,
   usually about 420 seconds of history, with explicit frame age and missingness.
   This is a documented adaptation, not identical input sampling.
4. **Repair the clustering interpretation.** Generator `cluster_density` is the
   sum of x/y ranges, averaged over teams. Larger values mean greater spread.
   EDA cell 51 maps the highest quantile to “All-In Cluster” and the lowest to
   “Spread Out”, reversing the variable's meaning. Its resulting verbal claim
   cannot support the direction of a coordination effect without reanalysis.
5. **Replay alerts chronologically.** `pick_warnings` in cells 30/55 chooses the
   largest score in a cluster, then the largest peaks across the entire match.
   Future scores can replace an earlier warning. Those are retrospective
   visualization choices, not an executable online alarm policy. The new policy
   acts when a score arrives, obeys cooldown, and credits each event once.
6. **Test the actual augmentation claim.** `jitter_seq` copies every window, not
   only positive windows, and retains the same labels after shifts. Uniform
   tripling does not alter class prevalence. This study removes that augmentation.

The BiGRU itself is **not automatically leakage**: a backward pass over a window
containing only observations available by the prediction cutoff is permissible.
It would become leakage if later match observations entered that window. Tests
check that changing a future observation cannot change an earlier prediction.

## Implemented continuation

`src/league_ews/notebook_ews.py` retains the original hybrid's main components
and selected widths. It implements these four fixed families:

| Family | Input/encoder | Trainable parameters |
|---|---|---:|
| Snapshot | Current frame only, MLP and common output heads | 207,628 |
| GRU | Two 160-unit bidirectional GRUs and temporal pooling | 912,717 |
| TCN | Three residual squeeze-excitation TCN blocks and temporal pooling | 557,087 |
| LeagueEWS | Original two-stream TCN/BiGRU cross-attention design | 1,751,647 |

All four share the same audited input channels, event heads, event loss weights,
training matches, batches, optimizer and update budget. These are **matched-data
controls, not equal-parameter or equal-compute controls**. Beating GRU would not
by itself attribute a gain specifically to cross-attention.

The changes from the notebook are explicit: PyTorch instead of Keras; masked
histories; per-token LayerNorm instead of BatchNorm; masked squeeze-excitation
and pooling; PyTorch elementwise input dropout rather than Keras GRU dropout
semantics; 55 audited channels instead of the old 150; an additional 60-second
output per event; fixed 12 epochs with constant learning rate 1e-4 instead of
tuning/early stopping/cosine scheduling; no separate dense-kernel L2 term beyond
AdamW weight decay. This is a **descendant and controlled continuation**, not a
bit-for-bit reproduction of the saved Keras model.

The executable plan is `PLAN` in `src/league_ews/notebook_experiment.py`:

- Four families × three fixed seeds = 12 planned fits, 12 epochs each.
- Reuse `data/private/b4-sequences` and its training-only normalizer. No new raw
  collection and no full-dataset export are needed for a WSL run.
- Keep all three events and report 10/20/30/60-second row metrics separately.
- Primary contrast: LeagueEWS minus the two-layer GRU in macro timely recall
  across the three events, at 10–30 seconds of lead. Sixty-second diagnostics
  use 20–60 seconds of lead. Cooldown stays 60 seconds in both policies.
- Select each threshold on the earlier 1,500 calibration matches per route,
  with at most one false-plus-late alarm per match in **each** route. Evaluate
  the fixed threshold on the later halves and report regional budget failures.
- Save each completed training shard. Resume exactly from model, optimizer and
  RNG state. Freeze all implementation files, source artifacts, input bindings,
  runtime and device. Score calibration only after all planned fits complete.
- Keep patch-16.17 payloads sealed. The already inspected calibration population
  makes this exploratory. Paired intervals are conditional on fitted models
  and policies; secondary intervals are not multiplicity-adjusted.

The summary reports whether the primary difference is positive in every seed
while **both** models meet every primary regional budget. That is a development
screen, not proof of superiority, publication readiness or a breakthrough.
Shared versus single-task transfer is still untested by these four families.
Capacity controls and a genuinely fresh evaluation would be required before
attributing gains to a new mechanism.

The [discovery gates](league-discovery-gates.md) specify the next mechanism
comparisons and the closest prior work. Its compact three-event exporter can
make the existing development data available in another workspace without a
new collection or a pre-staged B4 cache. These additions do not change this
12-fit experiment or establish an empirical discovery.

## Run with the user's existing WSL data

```bash
cd /home/thivas/work/ai-portfolio/league-ews-audit
git fetch origin research/leagueews-notebook-continuation
git switch research/leagueews-notebook-continuation
make notebook-continuation-canary DEVICE=cuda
make start-notebook-continuation DEVICE=cuda
make notebook-continuation-status
```

The canary trains LeagueEWS on one real training shard and checkpoints it; the full worker
resumes from there. It survives closing the terminal. Re-running the start
target resumes completed work and rejects a duplicate worker. The program
fails explicitly if CUDA or the audited source cache is unavailable.
Preflight verifies source files before the background worker starts.

If the already collected B4 cache was never staged, reuse the existing commands
`make stage-b4-sequences-all` and `make fit-b4-normalizer` before the canary.
Do not rerun API collection. Do not use another game's data. The output is
`data/private/notebook-ews-v1/summary.json` after training and calibration finish.

## Verification at initial implementation

Twenty-one tests passed on CPU: 14 new continuation checks and seven existing
sequence/normalization checks. They check training of all three heads in
every family, padding invariance, future-observation isolation, exact optimizer
resume, snapshot/history separation, warning boundaries, one-to-one credit,
cooldown, regional budgets, calibration-read isolation and the resume-before-
calibration gate, plus full scoring-path event/horizon and match alignment.
The training fixtures are synthetic implementation checks. CUDA execution and
the full repository CI suite have not been verified in this workspace.
Focused Ruff checks, strict type checks on the three new modules, shell syntax
and `git diff --check` also pass.

**No new real-data League fit has run in this workspace.** It has the original
notebooks/report and saved aggregate summaries, but not the private WSL cache.
The continuation is implemented for that existing cache; none of the software
checks is counted as an empirical research result.
