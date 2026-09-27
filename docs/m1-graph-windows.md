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
