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
evidence; the analysis command does not select a cutoff automatically.

## Frozen decision

The checksum-bound pilot report contained 5,000 matches across all 12 cells.
The 180-second candidate excluded all 90 matches carrying Riot's early-surrender
flag and no other matches, retaining 4,910 (98.2%). Every higher positive
candidate excluded additional matches without removing another early-surrender
case. The final population rule is therefore:

```text
retain if info.gameDuration >= 180 seconds
```

`configs/rifthazard-duration-rule.yaml` freezes this choice and binds it to the
original frame plus private analysis SHA-256
`3cab09e4f305bb67b089e28a35276cee1fe67add9584baef6552d78b7a12c9c5`.
Validate the public rule and local private report together with:

```bash
make validate-duration-rule
```

## Freeze boundary

The original pre-pilot sampling frame remains immutable because discovery,
selection and raw collection are already bound to its SHA-256 digest. The
separate duration supplement references that frame and the exact private
analysis report. Final-stage validation requires both and enforces the inclusive
180-second boundary on every final match.

The cutoff was not chosen from event prevalence, labels, model scores or model
performance. It cannot be revised after final collection begins.
