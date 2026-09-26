# B4 temporal baseline: causal input contract

This is the next baseline after the registered B3 calibration and event-level
alert evaluation. The final test patch 16.17 stays unread while the model and
operating policy are built and frozen on earlier patches.

`src/league_ews/b4_sequence.py` constructs one sequence per genuine timeline
observation. Each sequence contains the current frame and at most seven earlier
frames **from the same match**. It never interpolates missing minutes, reaches
into a different match, or reads a frame later than the prediction timestamp.
Short histories are left-padded and carry an explicit history mask. Every real
frame has its actual age in minutes relative to the prediction time. The 27
causal B3 feature values occupy separate channels from 27 missingness bits;
missing numeric values are set to zero in the value channel. The 12 strict
future labels are returned in a separate array, not among the model inputs.

The window function deliberately returns unscaled values. A later trainer must
fit feature scaling and any model selection on patches 16.12–16.15 only, using
a grouped inner training split where needed. It may score and set thresholds
on patch 16.16. Ten fixed seeds are required by the registered neural
experiment protocol, with all seeds reported. The 16.17 patch remains reserved
for a single evaluation after the model and policy are locked. B4 remains a
secondary sequence control; the registered H1 comparison is M1 against B3.

This chunk establishes and tests the causal window contract. It does not fit
a neural model or create a private artifact, and needs no Riot credential.
