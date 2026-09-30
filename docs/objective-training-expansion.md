# Pre-fit data-scale follow-up

Declared before any scores from the objective-training screen. The existing
109-match training set has only 76 onsets. In parallel with the small-data loss
comparison, acquire 600 additional training candidates and 150 additional
calibration candidates to test whether conclusions survive a larger event count.
This is training/development acquisition, not evaluation reuse.

Exclude all 750 IDs in the three previous selection manifests and the first ten
schema-development IDs. Training candidates must start before 1756021999, the
beginning of the original calibration period. Calibration candidates must start
at or after that time and before 1760390736, the original evaluation period.
Select the 600/150 lowest SHA256(`objective-expansion-v1:split:match_id`) within
each time range, freeze the manifest before acquisition, and apply the existing
strict snapshot/clock/identity/combat-versus-HP checks without replacements.
No command stream is needed because this comparison uses only history features.

Pool retained additions with the original 109 training and 37 calibration
matches. Keep all previously evaluated matches excluded from both pools.
Use the same seven neural losses, network, training schedule, seeds and threshold
search as the small-data protocol; recompute preprocessing, prevalence and the
weighted-BCE weight from the larger training set only. Refit the same HGBT
history baseline on the pooled training set, then calibrate on the pooled
development set. This declares both data sizes before viewing any loss scores.

For the larger pool, advance only if each seed's cooldown-utility policy has at
least 25% calibration event recall, at least ten percentage points more recall
than the best non-primary neural arm or pooled HGBT baseline, and <=1 unmatched
alarm/match. Require at least 200 retained training and 60 retained calibration
matches; otherwise report an insufficient-data outcome. No change of gate based
on observed scores. Calibration remains development evidence. Any advancing
candidate needs a separately frozen, disjoint new evaluation cohort.
