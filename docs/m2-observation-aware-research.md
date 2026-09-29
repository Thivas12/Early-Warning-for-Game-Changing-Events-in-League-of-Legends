# Observation-aware spatial research track

**Status:** exploratory protocol, drafted after seeing M1 calibration results.
It does not replace the six registered M1 ablations, select an M1 seed, or
authorize opening patch 16.17 for this new method. A confirmatory claim needs
a separately frozen design and a newly collected untouched cohort.

## Mechanism before architecture

M1's current participant x/y and observed-position flag, proximity relations,
fixed objective anchors, and minute-spaced observation history enter one graph
encoder. Removing coordinates *and* proximity together reduced mean
calibration macro AP from 0.49112 to 0.13914, but that intervention cannot
separate measured movement from missingness or phase. Removing objective nodes
increased macro AP to 0.51086 while also changing node count and pooling. The
original anchors record fixed map coordinates and an initial spawn flag; they
do **not** encode current objective availability or respawn time.

`make audit-m2-preprocessing` checks the 300 previously staged M1 train and
calibration shards against their immutable checksums. It counts 10/20/30/60 s
positive rows for every exact future label by the number of observed participant
positions (0–10), staged objective spawn flag, partition, and current graph
relation density. It decodes no test match and writes only a small aggregate
JSON file. `make render-m2-preprocessing` creates a local static SVG showing
position coverage and 60-second label rates across no/partial/all coverage.
These conditional rates describe an observation process and game phase; they
cannot identify a causal benefit of position features. Cross-check raw source
presence with `make audit-raw-field-coverage` before treating these as measured
positions. Run it after the GPU
ablation batch or while that batch is idle to avoid disk contention.

`src/league_ews/m2_spatial.py` adds four **exploratory** one-factor transforms
on the existing graph arrays, without writing a second graph corpus:

| Control | Changed input | Held fixed |
|---|---|---|
| Coordinates masked | Participant x/y | Observed bit, all relations, 12 nodes |
| Proximity masked | Player and pit proximity relations | Coordinates, observed bit, 12 nodes |
| Observed bit masked | Participant position-observed channel | Coordinates, relations, 12 nodes |
| Fixed-node anchors masked | Two objective-node feature rows and incident relations | 12-node pooling size, participant channels |

The source graph normalization is fit on training only. `spatial_summary`
derives 24 current/past-only side-channel values: team-specific position
coverage, centroids, nearest opponent and objective distances with explicit
observed bits, spawn flags, relation counts, history length and genuine frame
gap. Absent positions have zero distance **with** a zero observed bit; a zero
distance alone must never be interpreted as a real measurement. This side
channel is candidate input for an observation-aware hybrid. It does not use
future event labels or synthesize 10-second frames.

## Prefit hybrid candidate

The follow-on implementation is in `src/league_ews/m2_backend.py`. Its graph
stream starts from the same M1 architecture, randomly initialized for each
seed. The 24-value side stream has a 32-unit hidden layer. A three-output gate
uses both teams' observed-position counts, whether both team centroids exist,
and the age of the previous real frame. It combines the streams' hazard logits
separately for Baron, Dragon and teamfight. `ungated` uses an equal logit mix;
`spatial-only` removes the graph contribution. The original M1 ten seeds are
the graph-only reference. All variants retain six ordered 10-second hazard
bins and the same at-risk BCE, three epochs, batch size and seeds. The spatial
values use fixed outcome-blind scales based on map and count bounds. No
position imputation, future objective event, oversampling or test input is
introduced.

After the spatial audit, `make freeze-m2-hybrid` binds its bytes, source graph
inventory, M1 normalization, and `configs/rifthazard-m2-hybrid-plan.yaml`.
`make train-m2-seed MODE=gated SEED=20260915 DEVICE=cuda MAX_NEW_SHARDS=1`
is a one-shard canary. Its checkpoint is atomic and resumable across 720
train-only units (three epochs over 240 shards). A partial run exits 2 by
design. The ungated and spatial-only modes are separate, matched controls.
Run one CUDA process at a time, after the already-running M1 ablation batch;
the three modes' checkpoints are small compared with the existing graph
staging and do not create another raw or processed corpus.

After **all ten seeds in one mode** finish,
`make score-m2-calibration MODE=gated SEED=20260915` verifies all ten checkpoints before opening the
calibration shards. It writes checksum-bound probabilities, exact labels and
match offsets plus each target's AP and Brier score. Repeat for all ten seeds
and each mode; this command never reads a test shard. It creates roughly one
compressed score file per seed, so review disk availability before a full
thirty-seed run. After scoring all ten seeds of a mode,
`make audit-m2-utility MODE=gated` verifies probabilities against the
checksum-bound processed labels, recomputes AP/Brier, and fits event thresholds
on the earlier chronological 1,500 matches per route. It replays those frozen
thresholds on the later 1,500 per route, for every seed. Its summary compares
M2 AP with B3 and M1 and later-half alerts with M1, retaining all individual
seed results. The next code stage must compare the bounded loss controls and
gate a fresh-cohort design. Do not run the sealed original test through this
follow-on model.

## Experiment matrix after the diagnostic

1. Refit the four spatial controls above from identical training shards,
   optimizer, epochs, seed list, feature scale, and threshold procedure. Report
   all seeds, every event/horizon AP and Brier score, and Baron/Dragon/
   Teamfight event-level false alerts, lead and recall. The fixed-node anchor
   control helps distinguish anchor content from a changed pooling denominator.
2. Fit a **simple spatial tabular** comparator from the 24 audited side-channel
   features, plus genuine game clock and past objective events if the processed
   fields are checksum-bound and measured before each prediction frame. Compare
   against B3, not only against M1. No future-event-derived time-to-next-spawn
   is a permissible input.
3. Fit a two-stream candidate: relation-aware graph encoder over actual frames
   and a small transparent spatial/clock branch. A learned gate receives
   position coverage and frame age and combines the two streams before
   independent event-specific discrete hazards. The graph-only, side-channel-
   only and ungated fusion controls get the same data and comparable compute.
   Retain event-specific hazards because Baron, Dragon and teamfight can share
   a bin. Estimate scaling on training, and keep an explicit missingness mask.
4. Compare original at-risk BCE with a bounded focal loss and a clipped,
   train-derived positive weight as **separate** controls. Never resample
   individual neighboring frames into a synthetic balanced validation set.
   Evaluate probability calibration and warning burden on the original
   prevalence; minority recall without an alert budget is not a win.
5. Choose thresholds on the earlier chronological half of patch 16.16 and
   diagnose later-half behavior by route, event, game-time phase and coverage.
   This is an exploratory sensitivity check; model family, hyperparameters and
   operating rule must be frozen before a new untouched later-patch cohort.

The **primary endpoint** for a new confirmatory cohort will be one-to-one
onset recall at a prespecified false-alert limit per match for a 60-second
prediction window and 60-second cooldown, with precision and median/p10 lead
time alongside it. Report all-event and 60-second-observable-event denominators,
the false-alert distribution per match, and route/patch slices. Run a paired
match-level bootstrap for the nominated primary comparison and control the
multiple event/model comparisons. A graph with higher macro AP but worse
Dragon or Teamfight warning burden does not satisfy the operating endpoint.

## Research basis

- [GRU-D](https://arxiv.org/abs/1606.01865) motivates carrying a measurement
  mask and elapsed time separately rather than treating missing coordinates as
  real zero positions. It does not prove that League position missingness is
  informative.
- [Temporal Label Smoothing](https://proceedings.mlr.press/v202/yeche23a.html)
  motivates warning evaluation under a low false-alarm rate and timeliness;
  smoothing is a comparator, not permission to fabricate source frames.
- [Focal Loss](https://openaccess.thecvf.com/content_iccv_2017/html/Lin_Focal_Loss_for_ICCV_2017_paper.html)
  suggests downweighting easy negatives; its benefit to this hazard task is an
  empirical question.
- [Class-imbalance corrections in risk prediction](https://academic.oup.com/jamia/article/29/9/1525/6605096)
  show why a recall gain must be checked against probability calibration rather
  than attributed to the loss alone.
- [Proper scoring rules for survival analysis](https://proceedings.mlr.press/v202/yanagisawa23a.html)
  motivate assessing hazard probabilities alongside rankings and alert utility.

The proposed combination is a falsifiable model candidate, not a claimed new
algorithm or a prediction of the future-patch result. All negative outcomes
remain part of the report.
