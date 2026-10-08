# AI-assisted development record

AI assistance is allowed, but it is not evidence and is not an author.

## Recorded use for research/v2 scaffold

OpenAI Codex was used on 2026-09-15 to:

- inventory and critique the repository;
- trace data-generation and model-splitting code;
- propose the falsifiable research design;
- implement typed modules, tests, CLI workflows and CI configuration;
- execute the legacy audit and leakage-safe baselines;
- discover candidate literature and draft documentation/manuscript text.

The generated numeric claims in the repository come from committed executable
code and identified data hashes, not from language-model recollection. Web
sources were opened directly before policy and related-work summaries were
written.

## Material use in the LeagueEWS continuation and publication package

From 30 September through 7 October 2026, OpenAI Codex assisted with the
three-event notebook continuation, controlled follow-up experiments, checkpoint
and replay auditing, literature checks, analysis and report writing. On
7 October it synthesized the completed evidence, drafted the manuscript and
recruiter-facing case study, generated source-linked figures/PDFs, specified
the bounded confirmation design and implemented the saved-model CPU/GPU runtime
measurement. It diagnosed the cuDNN TF32 parity failure and preserved both the
aborted first run and the committed precision correction.

Affected publication files include `docs/leagueews-paper-draft.md`,
`docs/leagueews-case-study.md`, `docs/leagueews-confirmation-protocol.md`,
`scripts/build_publication_package.py`, the two publication benchmark runners,
`paper/leagueews-2026-10/` and `reports/publication-package-2026-10-07/`.
Reported empirical figures come from identified execution artifacts, not model
recollection. Human verification for submission has not been represented as
complete. The résumé bullets are drafts for the owner's verification, not a
claim of unaided implementation or accepted publication.

## Human accountability before submission

Before submission, a human author must:

- inspect every code change and rerun every result;
- verify citations against full texts;
- confirm data rights and ethics requirements;
- decide and defend all scientific claims;
- disclose AI use according to the target venue's current policy.

Future material AI use should append the date, tool/model if known, purpose,
affected files and human verification outcome to this document or the relevant
pull request.
