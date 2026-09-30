# Development screen: add commands to the full history baseline

Declared after the third experiment's negative fresh result: destination features
caught 11/131 onsets, history 14/131, and the incorrect-location control 0/131.
The command model used current state, not the full history inputs. The remaining
incremental-information question is whether commands improve the full history
baseline. This follow-up is motivated by an observed negative test result; it is
not an independent confirmation or a novel architecture.

Use only the 109 training and 37 calibration matches from the command quality
report. Do not load any prior evaluation features or outcomes into this screen.
Reuse the hash-verified frozen history baseline and refit three augmentations:
history plus command rates, history plus rates and destinations, and history
plus rates and rotated destinations. Use the same 197 history features, 24 rate
features, 45 spatial features, fixed HGBT hyperparameters, seed 17, calibration
threshold search, 20–60-second lead, and 60-second cooldown.

Resource-allocation gate, declared before fitting: the correct-destination
augmentation must catch at least three more calibration onsets than EACH of
history, history+rate, and history+rotated-destination, under <=1 unmatched alarm
per calibration match. Otherwise record the result as insufficient development
evidence and do not spend a new evaluation cohort on this variant. This numerical
gate is a development heuristic, not a statistical significance claim.

If it passes, freeze these exact fitted policies and select 200 new late-period
matches by the lowest SHA256(`command-history-v1:match_id`), excluding every ID
in all three previous selected manifests plus the first ten schema-development
matches. Apply the same quality rules without replacements. Only that new cohort
may test the hypothesis; do not rerun the 145-match evaluation with these models.
Do not pool a later result with the third experiment as if preplanned.

Both positive and negative calibration outcomes must be published. Passing
calibration alone never supports a breakthrough or generalization claim.
