# LeagueEWS publication closeout

**Review date: 8 October 2026.** The completed development study is ready to be
reviewed as an exploratory paper and technical portfolio. Submission readiness
and fresh-patch generalization remain separate, unfinished claims.

## Completed in this editorial revision

- A focused manuscript with explicit contributions, related-work boundaries,
  data and endpoint definitions, absolute baseline results, controlled effects,
  runtime measurements, limitations and references.
- A short repository landing page and a five-minute technical review route.
- A separate versioned manuscript PDF; the original 7 October package and all
  its checksum-bound results remain unchanged.
- Public verification of the existing evidence and source-linked tables in the
  revision. No new model fit, policy search or outcome evaluation was performed.

## Three remaining submission gates

| Gate | Concrete completion artifact | Current status |
|---|---|---|
| Confirmation and claim scope | An executable, checksum-bound release of the [four-claim confirmation protocol](leagueews-confirmation-protocol.md), followed by its one-time complete report if fresh-patch claims are pursued | The design exists; exact private checkpoint/policy bindings and the release gate are unfinished. Patch 16.17 remains sealed. An exploratory-only submission must explicitly retain this limitation. |
| Closest League literature | A full-text comparison with Vardakis et al. (2026), recording labels, horizons, splits, baselines, metrics and overlap | Publisher abstract verified; full text could not be retrieved on 8 October. Do not infer unreported methods or claim priority from the abstract. |
| Author and venue review | Owner-verified claims, authorship/AI disclosure, data and artifact access statement, and a venue-formatted manuscript | Human review and venue selection are pending. Acceptance and recruiter response cannot be established by repository checks. |

The [7 October decision](publication-decision-2026-10-07.md) remains in force:
incremental development sweeps have stopped. Neither a small favorable interval
nor an internal software gate is a reason to reopen them. No task in this
editorial revision releases held-out payloads or changes that decision.

## Claim-to-evidence map

| Claim suitable for the current paper | Public evidence | Boundary |
|---|---|---|
| Past non-timing state adds short-lead information under the tested recipe | [History report](../reports/clock-history-2026-10-04/research-report.md) | Explored calibration; not a causal mechanism or uniform event benefit |
| Useful-lead supervision improves longer-lead recall in both hybrid and TCN | [Target report](../reports/timely-neural-2026-10-03/research-report.md) | Policy dependent; trades late against false warnings |
| Joint training can hurt longer-lead performance | [Sharing report](../reports/timely-sharing-2026-10-05/research-report.md) | Independent encoders use more resources; task weights also matter |
| The hybrid has a small matched-recipe advantage over TCN | [Matched controls](../reports/matched-optimization-2026-10-06/research-report.md) | Unequal capacity and tuning; regional consistency unresolved |
| Conservative selection removed observed overruns at a recall cost | [Policy report](../reports/warning-risk-2026-10-07/research-report.md) | Not a certified adaptive-search risk guarantee |
| CPU/GPU model cost depends on batch size | [Runtime protocol](../reports/publication-package-2026-10-07/runtime-protocol-v2.md) and [timings](../reports/publication-package-2026-10-07/runtime.json) | One laptop, resident inputs, no preprocessing or serving overhead |

## Literature access record

Primary records checked on 8 October 2026: Yang et al., arXiv:2012.09424;
Yèche et al., PMLR 248; Yu et al., arXiv:2001.06782; Angelopoulos et al.,
arXiv:2110.01052; and Vardakis et al., DOI:10.1016/j.entcom.2026.101091.
The first four provide accessible primary records. The Vardakis publisher
record identifies imminent player-death prediction in League with a Temporal
Fusion Transformer. Direct full-text access returned HTTP 403; the institutional
listing did not yield a retrievable full text. The paper therefore marks its
detailed methodological comparison as unresolved.

References and direct primary links are in the
[revised manuscript](leagueews-paper-revised.md). This is a focused comparison
with the closest identified work, not a claim of an exhaustive systematic review.
