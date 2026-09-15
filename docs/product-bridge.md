# Research-to-product bridge

The product repository is intentionally **not created yet**. It begins only
after a frozen research release clears G6 in `research-plan.md`.

## Safest useful product thesis

A post-match coaching service identifies a small number of high-leverage
moments, explains the observable setup, and offers several review questions.
This is more useful and policy-defensible than a noisy live command engine.

Example output: “Dragon risk rose 40 seconds before the objective as both teams
grouped and vision activity increased. Review your recall timing, lane priority
and contest/trade options.” The player still makes the decision.

## Transfer contract

The product may consume only a signed research release containing:

- feature and input schemas;
- preprocessing code and checksums;
- model weights in a portable format;
- calibration and operating thresholds;
- supported patches/regions and OOD behavior;
- full model/data cards and licence decision;
- latency and cost benchmark;
- rollback version.

No notebook object, raw API key, PUUID or non-commercial dataset crosses the
boundary.

## Legitimate monetization hypothesis

Subject to Riot registration being Approved or Acknowledged:

- free: recent-match review and a limited number of moments;
- paid subscription: deeper longitudinal coaching, comparison to the player's
  own history, exports and team review workspaces;
- optional donations/crowdfunding for research.

The paid value is interpretation, workflow and personalized learning—not resale
of Riot data. Betting, gambling and paid competitive advantage are excluded.

## Near-zero-cost target architecture

- static web UI on Cloudflare Pages;
- one small API/worker only when needed;
- client-side or batch inference where feasible;
- SQLite/DuckDB and object storage before managed databases;
- public GitHub Actions within free allowances;
- strict request, storage and retention budgets;
- no generative-AI call in the critical path unless a user explicitly opts
  into a separately budgeted feature.

Cost target for the closed pilot is $0/month incremental infrastructure. Paid
launch occurs only after measured usage defines a sustainable per-user budget.

## Product discovery before code

Interview at least 12 players across rank bands and 3 coaches. Prototype three
review formats, measure whether users correctly identify the decision point,
and retain only workflows that reduce review time without increasing false
confidence. A provisional name such as “Rift Ahead” requires trademark/domain
screening before use.
