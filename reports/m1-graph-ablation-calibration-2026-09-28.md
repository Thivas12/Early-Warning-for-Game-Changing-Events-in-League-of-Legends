# M1 graph removals on calibration

Four registered graph removals have completed ten seeds each on the 6,000-match
patch 16.16 calibration partition. The numbers below are transcribed from the
researcher's checksum-bound CLI summaries on 2026-09-28. Before publication,
compare them with the private `ten-seed-summary.json` for each variant. Patch
16.17 remains unread. The [companion figure](figures/m1-graph-ablation-calibration.svg)
plots the means and observed ten-seed ranges.

| Model | Macro AP mean | Seed SD | Seed range | Difference from M1 |
|---|---:|---:|---:|---:|
| B3 tabular reference | 0.37594 | — | — | — |
| Original M1 | 0.49112 | 0.00622 | 0.47963–0.49952 | Reference |
| Without objective nodes | **0.51086** | 0.00285 | 0.50639–0.51453 | **+0.01974** |
| Without positions or proximity | 0.13914 | 0.00358 | 0.13374–0.14314 | −0.35198 |
| Without interaction edges | 0.46634 | 0.00653 | 0.45381–0.47581 | −0.02478 |
| Without assistance history | 0.46346 | 0.00705 | 0.44933–0.47305 | −0.02766 |

Removing objective nodes improves calibration ranking in every observed seed
range relative to the original M1 range. This challenges the usefulness of the
current fixed objective-anchor nodes in this implementation. The variant also
changes node count, relation count and graph pooling denominator; the comparison
does not isolate a causal effect of objective information alone. Do not select
a best seed or revise the already frozen ablation plan based on this result.

Removing positions **and** three proximity relation types together produces a
large loss of ranking performance. Because those channels are removed in one
registered variant, the result does not separately quantify coordinate and
proximity-edge contributions. Removing all interaction edges or just assistance
edges produces smaller losses. The per-target and event-level alert metrics are
needed to see which events and warning horizons drive these averages.

These are calibration estimates across correlated seeds on one patch, not
independent trials or a future-patch generalization claim. The two other frozen
controls, independent horizon heads and a fixed minute history grid, remain to
be implemented and scored. After their results and alert-burden comparisons,
freeze the final model and operating protocol before the one-time test release.

The compact transcription for the figure is in
[`m1-graph-ablation-calibration-2026-09-28.json`](m1-graph-ablation-calibration-2026-09-28.json).
Regenerate the SVG with `python scripts/render_m1_ablation_figure.py` after
checking the transcription against the private summaries. No raw matches or
player identifiers are required.
