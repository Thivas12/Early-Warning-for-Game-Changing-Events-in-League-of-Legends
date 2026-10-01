# Completed study: maintenance and research verification

The reported recall gains and regional warning-budget failures reproduce.
This review repairs publication tooling and strengthens the analysis checks;
it changes no fitted model, threshold, split, endpoint or archived result.
Patch 16.17 remains sealed. No additional empirical training fit was launched.

## Repairs

- Reformatted the inherited tree script without changing its parsed Python AST.
  The original GPU and history-ablation source checkouts remain byte-for-byte
  bound to their freezes. Only the separate maintenance checkout has the fix.
- Updated the locked `urllib3` dependency from 2.7.0 to 2.8.0, retaining every
  other package. The [upstream release notes](https://urllib3.readthedocs.io/en/stable/changelog.html)
  identify fixes for proxy TLS configuration, unbounded chunk-line buffering
  and Deflate streaming. The [uv locking documentation](https://docs.astral.sh/uv/concepts/projects/sync/)
  describes the targeted update used here.
- Bound both studies' calibration offsets and target arrays to the same exact
  development archive. Previously, the history analysis compared event totals
  across studies and array alignment within each study, which was insufficient
  to independently establish the cross-study row alignment.
- Added checks for completed status, progress-freeze identity, prediction shape,
  integer event counts, count/report agreement and recorded test-access flags.
  Thirteen new regression checks cover these contracts and replay boundaries.
- Updated the README and continuation documents to describe the completed fits,
  failed development screens and remaining task-sharing question. Recovery
  instructions now pin the original source commits explicitly.

## Independent empirical audit

The [read-only replay](replay-audit.json) checks all 15 completed fits, each with
three events and two horizons: **90 policies on the same 6,000 calibration
matches**, of which 3,000 are evaluation matches. These repeated evaluations do
not increase the independent match population.

The audit builds each chronological warning list from saved probabilities and
the 60-second cooldown, then separately assigns one-to-one future event credit
from the archive's exact event times. It preserves the 10–30- and 20–60-second
useful lead boundaries and excludes events simultaneous with a warning.
Every saved evaluation match-count array agrees exactly. Overall and regional
recall, false warnings, late warnings, opportunities and budget flags agree.
Every chosen threshold meets the earlier-calibration regional budgets; the
reported later-calibration failures remain. Threshold selection was not rerun
and no threshold was changed.

Recomputing both paired analyses with the stronger archive checks reproduced
all numerical results and artifact bindings exactly. Only the analysis-source
hashes differ. The [verification record](verification.json) binds the old and new
outputs and confirms all 92 original and 94 follow-up source hashes in their
preserved execution checkouts. The archived result JSONs remain unchanged.

## Validation and reproduction

`make check` passed in a new CPU environment installed from the updated lockfile:
292 Python files formatted, lint passed, strict typing passed for 87 source
files, and **544 tests passed with one optional dependency skip**. Combined
statement/branch coverage is **85.89%**, above the unchanged 85% requirement.
The credential scan, shell syntax and diff whitespace checks also passed.
These tests are implementation checks, not new League training results.

An initial type-check process exited with a segmentation fault, and an initial
pytest collection reported an AST-rewrite error. Both passed in isolated checks
and in the subsequent complete `make check`; the cause was not established.
No source check was disabled to obtain the passing run.

The [dependency audit](dependency-audit.json) found no known advisories in the
packages it could assess. It skipped the local project and the CPU-specific
PyTorch build identifier. A [separate upstream-version query](torch-upstream-audit.json)
found no advisories for PyTorch 2.14.0; this is advisory coverage of the upstream
version, not independent certification of the CPU binary. The original CUDA
environment was not modified.

From the maintenance checkout, using its own environment:

```bash
uv sync --frozen --all-groups --extra b4
UV_NO_SYNC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 make check
uv run --no-sync pip-audit
bash scripts/check-secrets.sh

PYTHONPATH=.:src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  -m scripts.audit_neural_results \
  --study /home/thivas/work/ai-portfolio/league-ews-gpu/data/private/compact-notebook-v1 \
  --study /home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-history-ablation-v1 \
  --archive /home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-three-event-export-v1/development.zip \
  --output reports/local/replayed-neural-audit.json
```

The paired-analysis commands are in the [original reproduction guide](../neural-continuation-2026-10-01/reproduce.md).
They can also run read-only from the maintenance checkout with its Python and a
new output directory. Resuming either training study requires its pinned
execution checkout and original CUDA environment, not this maintenance version.

## Interpretation retained

LeagueEWS exceeds GRU on the registered 10–30-second recall endpoint, but the
regional budget gate fails. Its mean difference from TCN remains indistinguishable
from zero under the reported conditional interval. At 20–60 seconds it trails
GRU. Additional history helps mainly Baron; neither that result nor these repairs
establish task transfer, architectural novelty or future-patch generalization.

The next specified mechanism comparison remains joint versus independent event
encoders. Warning-policy changes would require a separate frozen study; tuning
thresholds on the already scored later calibration matches cannot repair the
registered screen. The original negative findings are retained in full.
