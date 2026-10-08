# Publication package reproduction

This package adds presentation artifacts and one saved-model systems benchmark.
It performs no new predictive-method fit or outcome evaluation. The scientific
source remains the completed, exploratory League studies. Test payloads are
unopened. The original audit manuscript at `paper/main.tex` is preserved.

## Read the work

- [Project brief, two pages](leagueews-project-brief.pdf)
- [Research-engineering case study](../../docs/leagueews-case-study.md)
- [Working paper, seven pages](../../paper/leagueews-2026-10/leagueews-working-paper.pdf)
- [Paper source](../../docs/leagueews-paper-draft.md)
- [Exact figure estimates and source hashes](evidence.json)
- [Complete runtime measurements](runtime.json)
- [Confirmation design and remaining execution gate](../../docs/leagueews-confirmation-protocol.md)

The paper PDF renders the linked source and adds a systems appendix. Figure
estimates are extracted by exact JSON pointers from four completed analysis
files; no hand-entered point estimates or intervals drive those figures.
The matched hybrid–TCN lower interval endpoint is 0.130489355 percentage points;
this package rounds it directly to 0.130 at three decimals, correcting the
earlier narrative's double rounding to 0.131. Frozen study outputs are unchanged.
Both PNG and vector PDF/SVG versions are supplied. All 24 runtime cells and
2,400 measured call durations are retained. Timings are hardware-specific,
exclude input preparation/transfers/serving and carry no predictive accuracy claim.

## Rebuild documents without private data

Use Python 3.12 with NumPy 2.5.3, Matplotlib 3.11.2, ReportLab 4.4.10 and
pypdf 6.5.0. In this workspace, document-only dependencies live in isolated
temporary directories; the CUDA environment and project lock were not changed.

```bash
PYTHONPATH=/tmp/league-publication-tools:/tmp/league-warning-plot-tools:.:src \
MPLCONFIGDIR=/tmp/league-warning-mpl \
/home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  -m scripts.build_publication_package \
  --runtime reports/publication-package-2026-10-07/runtime.json
```

Portable equivalent, in an isolated Python environment:

```bash
python -m pip install numpy==2.5.3 matplotlib==3.11.2 reportlab==4.4.10 pypdf==6.5.0
python -m scripts.build_publication_package \
  --runtime reports/publication-package-2026-10-07/runtime.json
```

The public aggregate runtime JSON suffices to rebuild the documents. Rebuilding
may change PDF metadata and hashes; the estimates must remain identical. The
builder verifies complete benchmark status, all 24 cells, zero held-out reads,
PDF text extraction and a two-page brief. `document-checks.json` records the
generated page counts and hashes. These are artifact checks, not research tests.

Verify the source estimates, all timing arithmetic, complete cell inventory,
frozen runtime-source hashes, document hashes and local links without private
data or optional libraries:

```bash
python3 -m scripts.verify_publication_package
```

The verifier uses Python's standard-library statistics independently of the
NumPy timing summary implementation. Its result is `verification.json`.
All nine PDF pages were rendered and visually inspected; a split appendix
table and overlapping figure annotations were corrected before the final build.
The final appendix was inspected again after those corrections.

## Reproduce runtime with the private saved models

The original benchmark protocol and runner were committed at `cd616f4`.
That run stopped at CPU/CUDA parity after two CPU cells. It remains in
`data/private/league-publication-runtime-v1`; it is not silently overwritten.
The [precision amendment](runtime-protocol-v2.md) and wrapper were committed
at `84b9929` before the complete amended run. The output names reject overwrite.

```bash
PYTHONPATH=.:src python -m scripts.benchmark_publication_inference_v2 \
  --data-root /path/to/original/data/private \
  --output /path/to/a/new/runtime-output \
  --commit 84b9929
```

The script requires the saved training-only normalizer, the checksum-bound
compact development ZIP and all six complete saved checkpoints. It reads
one training shard, never calibration or test payloads. It verifies checkpoint
digests, training-freeze binding, parameter counts, committed source bytes and
CPU/CUDA output agreement. CUDA is required and there is no silent CPU fallback.
Default corpus, model and study artifacts are never overwritten.

## Verification boundaries

The prior predictive suite passed 740 tests with one skip; its final CI passed
on `4786728c80103c29675ff88934a92898759260c6`. That count describes the completed
policy study, not additional test coverage for this document build. New scripts
receive focused Ruff checks and direct artifact/benchmark verification. The
package records visual inspection separately. No unit-test count is treated
as an empirical replication, and no publication acceptance is claimed.
