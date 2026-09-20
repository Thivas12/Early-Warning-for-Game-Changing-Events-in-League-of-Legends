# Registered-pilot duration analysis

The registered sampling frame deliberately left the final minimum-duration
rule unset until the full 5,000-match pilot could be inspected. The pilot is
excluded from final claims and may be used only for infrastructure checks and
this duration/remake decision.

Run the checksum-bound analysis with:

```bash
make analyze-pilot-duration
```

The command first repeats the exact registered-pilot raw validation, including
the sampling-frame, discovery, frozen-selection and processed-inventory gates.
It then writes `data/private/pilot-duration-analysis.json`. The report is
ignored by Git and contains no match IDs or player identifiers.

## Permitted inputs

The calculation reads only these Match-V5 detail fields:

- `info.gameDuration`;
- `info.participants[].gameEndedInEarlySurrender`;
- `info.participants[].gameEndedInSurrender`.

It does not read timeline events, extracted event labels, winners, model
features, predictions or downstream performance. The processing manifest is
used only to establish exact inventory identity and bind its checksum.

The report gives nearest-rank duration percentiles and descriptive retention
counts for candidate minimums of 0, 180, 300, 600, 900 and 1,200 seconds,
overall and within each registered route-patch cell. These rows are decision
evidence, not an automatically selected cutoff.

## Freeze boundary

After reviewing the identifier-free report, exactly one minimum-duration rule
must be recorded in a checksum-bound post-pilot supplement before any final
candidate detail or timeline is collected. The original pre-pilot sampling
frame remains immutable because discovery, selection and raw collection are
already bound to its SHA-256 digest. The supplement must reference that frame,
the duration-analysis report and its input manifest checksums.

No cutoff may be chosen from event prevalence, labels, model scores or model
performance. Once frozen, the rule cannot be revised after final collection
begins.
