# Real coordination screen: 29 September 2026

Source: user-executed WSL experiment; this workspace received its aggregate
summary and checked the reported arithmetic. No private model was refitted here.
The source is preserved in `coordination-screen-real-2026-09-29.json`.

- Source SHA-256: `dcff6b77b8edc6806d94e984b35c8640694d604e0b0f1291603a7963f8422f60`.
- Runtime freeze SHA-256: `29930b83632e79a527e856595cfbf1f3e4ee99fa55824448009c55ca86dedd8f`.
- Evaluation: 3,000 matches, 11,329 Dragon onsets.
- Test matches reported unread: 6,000.
- Timely lead: 20-60 seconds, inclusive. All-event recall is primary.
- All comparisons remain exploratory after earlier calibration inspection.

| Model | Timely recall | False alerts/match | Timely precision | AP (within60) |
|---|---:|---:|---:|---:|
| b3 | 37.74% | 0.825 | 44.73% | 0.7519 |
| snapshot | 42.56% | 0.924 | 42.69% | 0.8411 |
| history | 43.05% | 0.939 | 42.77% | 0.8492 |
| coordination | 43.22% | 0.942 | 42.84% | 0.8485 |

## Primary finding

Coordination minus history: **+0.168 percentage points** of timely recall; paired 95% interval **[-0.044, +0.389] points**.
This does not establish an incremental benefit from these movement summaries
at the tested capacities. It does not rule out every learned coordination model.
All selected capacities were the largest tested value (31 leaves).

| Secondary contrast | Recall difference (points) | Paired 95% interval |
|---|---:|---:|
| snapshot-minus-b3 | +4.819 | [+4.279, +5.346] |
| history-minus-snapshot | +0.485 | [+0.213, +0.774] |

These intervals condition on fitted models and tuned policies. They do not
include refit, repeated-player or future-patch uncertainty. Both secondary
gains also increase false alerts; a common budget is not identical realized burden.
No original M1 or legacy-paper scores are substituted as matched baselines.

## Timing and observation limits

Coordination generated 4,896 timely, 3,707 late and
2,826 false alerts. Only 42.84% of alerts were timely.
False plus late burden was 2.178 per match, despite
meeting the mean false-only budget. Late alerts were always separately defined,
not hidden in the count of false alerts; the follow-up changes the primary budget
explicitly rather than reinterpreting this run.

Only 7,555/11,329 events (66.69%)
had an observation in their 20-60-second warning window. This is an upper bound
for policies that alert only at observed frames, not an attainable oracle score.
Cooldown and matching can lower the attainable bound further.
Coordination caught 64.80% of eligible events.
No claim about second-by-second paths or player intent follows from endpoint motion.

## Next experiment

Test whether separating late and timely outcomes during training improves the
useful-warning trade-off. See `docs/timely-objective-screen.md` for the new
four-fit protocol, two explicit budgets and fixed primary contrast. Interval
targets are not claimed as an original algorithm. Test payloads stay sealed.

Reproduce this document:

```bash
uv run --no-sync python scripts/render_coordination_results.py
```
