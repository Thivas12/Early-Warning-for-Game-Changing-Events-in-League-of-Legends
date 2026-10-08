# Editorial and portfolio revision · 8 October 2026

This version builds on commit `8d3a903db3c1da3af87e5c07c58cf53b7d9a90eb`.
It changes research presentation, not the completed empirical record.

- [Revised paper PDF](../../paper/leagueews-2026-10/leagueews-reviewed-paper.pdf)
- [Manuscript source](../../docs/leagueews-paper-revised.md)
- [Technical review route](../../docs/recruiter-walkthrough.md)
- [Submission closeout](../../docs/submission-readiness.md)
- [Exact baseline records](absolute-baselines.json)
- [Revision verification](verification.json)

The 26 files in the original publication manifest remain byte-identical. The
earlier manuscript, figures, runtime data, public verifier and original PDFs
are retained. The old landing page is preserved as
[research history](../../RESEARCH_HISTORY.md).

The revised manuscript adds explicit contributions and a prior-work comparison,
a cohort table, endpoint definitions, absolute baseline recall and burden,
an in-body evidence figure, a runtime table and formal references. All new
baseline table entries are copied from frozen JSON pointers and rounded only
for display. No new training, threshold search or outcome scoring occurred.

## Reproduce the editorial artifact

The original public verifier uses only the Python standard library:

```bash
python scripts/verify_publication_package.py
```

To render the new PDF, use the document-only dependencies from the
[original reproduction guide](../publication-package-2026-10-07/reproduce.md),
or an isolated environment with NumPy, Matplotlib, ReportLab and pypdf installed:

```bash
python scripts/build_publication_review.py
```

The builder checks the original 26-file manifest, 20 exact baseline values,
four displayed baseline rows, eight displayed runtime medians, and local
document-link targets. It then writes a separate PDF and verification record.
It never calls the old builder's mutation routines or opens private payloads.

Document rendering is not empirical reproduction. The saved figures and
conditional intervals retain the same limitations as the original studies.
Publication still requires the author and literature review described in the
closeout document; fresh-patch claims also require the frozen confirmation run.
