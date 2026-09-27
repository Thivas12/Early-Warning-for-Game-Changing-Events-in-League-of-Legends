# M1 causal graph windows

`build_causal_graph_windows` reads one de-identified processed match and
produces an input row at each genuine Riot timeline frame. The current frame
and up to seven earlier frames from that match are right-aligned; padding has
an explicit history mask. Actual frame ages in minutes preserve irregular
timing. A later frame cannot change an earlier input row.

Every snapshot has ten participant nodes in participant-ID order and two
objective nodes, Baron then Dragon. Its eleven node channels encode role,
team, observed gold, XP, level, minions, position and position/objective
availability. Absent positions have a zero coordinate with an explicit
availability bit. Five directed binary edge channels encode same team,
observed proximity, observed killer-assistant participation, and proximity
to the two objective sites. Killer-assistant edges use only kill events
recorded no later than the snapshot timestamp. The supplied `ObjectiveRules`
contain geometry and spawn times; the M1 staging plan must freeze their
patch-specific values and proximity radius before building private shards.

The twelve registered future labels and three-by-six event-specific hazard
targets are stored in separate return arrays. The builder checks each stored
label against the processed event index and rejects mismatches. The event
index never enters graph inputs. The input tensor is not yet scaled and no
private data, calibration predictions or test-patch data are read by this
pure input-contract implementation. Later staging must bind the frozen
36,000-match split and use only the 24,000 training matches to fit any
normalizer; calibration remains confined to patch 16.16.
