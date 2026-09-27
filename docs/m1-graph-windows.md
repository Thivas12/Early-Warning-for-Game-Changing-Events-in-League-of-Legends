# M1 causal graph windows

`build_causal_graph_windows` reads one de-identified processed match and
produces an input row at each genuine Riot timeline frame. The current frame
and up to seven earlier frames from that match are right-aligned; padding has
an explicit history mask. Actual frame ages in minutes preserve irregular
timing. A later frame cannot change an earlier input row.

Every snapshot has ten participant nodes in participant-ID order and two
objective nodes, Baron then Dragon. Its eleven node channels encode role,
team, observed gold, XP, level, minions, position and an observed-position or
initial-spawn-elapsed bit. That objective bit is a clock prior, not a claim
that a monster is currently alive after a kill. Absent participant positions
have zero coordinates with an explicit missingness bit. Five directed binary
edge channels encode same team,
observed proximity, observed killer-assistant participation, and proximity
to the two objective sites. Killer-assistant edges use only kill events
recorded no later than the snapshot timestamp. The supplied `ObjectiveRules`
contain geometry and spawn times; the M1 staging plan freezes their values
and proximity radius for the registered train/calibration patches.

`configs/rifthazard-m1-graph-plan.yaml` fixes the same proposed geometry and
spawn inputs for the five train/calibration patches. Riot's 26.1 notes give
Baron's regular Summoner's Rift spawn as 20 minutes. The 5-minute first-dragon
time and both pit centers are declared engineering priors, with the centers
taken from the existing graph test fixture. They are not claimed as exact Riot
coordinates. The registered objective-node and proximity ablations must test
dependence on these priors.

Run `make freeze-m1-graph` before private staging, then
`make stage-m1-graphs MAX_NEW_SHARDS=1` for a 100-match canary. Each shard is
atomic and checksum-bound; rerunning advances to the next shard, and an
unregistered orphan must match freshly reconstructed arrays before adoption.
The staging command audits the frozen split against raw and processed
manifests, G2 and processed validation, and does not open test-match payloads.

The twelve registered future labels and three-by-six event-specific hazard
targets are stored in separate return arrays. The builder checks each stored
label against the processed event index and rejects mismatches. The event
index never enters graph inputs. The input tensor is not yet scaled and no
private data, calibration predictions or test-patch data are read by this
pure input-contract implementation. Later staging must bind the frozen
36,000-match split and use only the 24,000 training matches to fit any
normalizer; calibration remains confined to patch 16.16.

## Training-only participant scaling

After all 300 train and calibration shards are staged, run `make
fit-m1-normalizer`. It checks the complete ordered inventory and every
checksum, including calibration shard bytes, then decodes only the 240
training shard arrays. One current frame per observation contributes to
the statistics, so repeated history does not change the moments. Only the
ten participant nodes' seven numeric channels (gold, XP, level, lane and
jungle minions, x and y) are fitted. Missing x/y values do not contribute;
the position availability bit, team sign, node roles, objective anchors,
edges, frame ages and padding are never scaled. Zero-variance channels use
an identity transform. The private, immutable normalizer binds its moments
to the staging manifest, graph plan, split, processing manifest and freeze.
The calibration arrays and final test patch remain unread by the fit. No
Riot credential or CUDA runtime is needed.

## Frozen graph-hazard training settings

Run `make freeze-m1-training` after the normalizer is fitted. The command
checks the full staged inventory, binds the normalizer to that exact manifest,
and writes an ignored private freeze containing the graph, split, processing,
training plan and hazard supplement checksums. It does not open calibration
arrays or test matches. The registered primary model has two relation-aware
message layers, an eight-frame 64-unit GRU, and independent six-bin hazards
for Baron, Dragon and teamfight. Training uses three epochs and all ten fixed
seeds; it masks bins after the first event of each type. Calibration may set
alert thresholds and report every seed, but cannot select one seed as the
headline model. The six M1 ablations are also named in the frozen plan.
This step freezes specifications only; the neural trainer follows in a
separate code chunk. It needs no Riot key or PyTorch import.

## Bounded M1 training

`make train-m1-seed SEED=20260915 DEVICE=cuda MAX_NEW_SHARDS=1` trains one
100-match shard for a CUDA canary. The installed PyTorch wheel must expose
CUDA in WSL; `uv run --no-sync` preserves the existing CUDA installation.
The trainer verifies the frozen plan, normalizer, manifest and each requested
training shard checksum. The relation-aware encoder averages observed
neighbors separately for each of five edge types, applies two message layers,
pools twelve nodes per real frame and sends those frames plus their actual
ages through a 64-unit GRU. Three independent six-bin hazard heads train with
binary cross-entropy only while each event type is at risk, through its first
event bin inclusive. Its frozen seed controls deterministic within-shard
shuffling and it checkpoints weights, optimizer and RNG state atomically after
every completed shard. Rerunning advances without replaying completed work.
One seed requires 240 shards × 3 epochs = 720 resumable units. Only one
process should train a seed at a time; a per-seed lock enforces this. The
calibration arrays and final test patch remain unread by training.

## Calibration scoring after ten seeds

`make score-m1-calibration SEED=20260915` requires completed checkpoints
for **all ten** registered seeds before opening any calibration arrays.
For each seed it checks each calibration shard checksum and compares its
hazard targets with the twelve registered labels, then derives 10, 20, 30
and 60-second event probabilities from cumulative conditional hazards.
It writes private, de-identified predictions and a bound report containing
per-target AP, ROC-AUC and Brier score. Existing score files are checked
against the frozen inputs; an interrupted run after writing predictions can
regenerate its report. This stage does not choose a winning seed or read the
final test patch. The ten-seed aggregate and operational alert policies
follow in separate chunks.
