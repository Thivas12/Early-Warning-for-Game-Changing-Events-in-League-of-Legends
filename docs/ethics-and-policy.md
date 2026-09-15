# Ethics, privacy and Riot policy boundary

This document is an engineering constraint, not legal advice. Policy must be
rechecked before every public dataset, model or product release.

Policy snapshot reviewed on **2026-09-15**:

- [Riot Developer General Policies](https://developer.riotgames.com/policies/general)
- [League of Legends Developer API Policy](https://developer.riotgames.com/docs/lol)

The repository treats 30 days as the maximum age of a policy review before a
new private collection. This is a project safety rule, not a Riot-stated
interval.

Riot's [General Policies](https://developer.riotgames.com/policies/general)
require products to be registered and audited, prohibit betting and unfair
advantages, require a free tier for monetized products, and require paid
content to be transformative. The current
[League policy](https://developer.riotgames.com/docs/lol) prohibits
game-session-specific information previously unknown to the player and apps
that dictate decisions. It also says API keys must not be included in code.

Consequences for this project:

1. Research collection uses supported endpoints, HTTPS and environment-injected
   credentials.
2. The historical embedded key is treated as compromised and must be revoked.
3. Raw player identifiers are not published; account mappings are not needed
   for the modeling task.
4. The first legitimate product concept is post-match coaching. A live feature
   requires explicit Riot approval and a demonstrated information boundary.
5. Warnings describe uncertainty and offer alternatives; they never command a
   player.
6. No betting, token, blockchain, hidden-MMR or opponent-deanonymization use is
   permitted.
7. Research and product data licences remain separate. CC BY-NC legacy data
   cannot silently become a subscription asset.

## Human-subject and harm review

Although match telemetry is exposed through an API, large-scale behavioral
analysis can still create privacy and profiling risks. Before collection, the
researcher should obtain institutional ethics guidance where applicable,
minimize data, set a retention period and document whether consent or a waiver
is required. Public examples must not make a player discoverable.

## Executable collection gate

`league-ews preflight-collection` and `league-ews preflight-discovery` check a
private, ignored authority record before any API request. They require an
up-to-date policy review, a non-commercial research purpose, explicit endpoint
and regional scope,
private raw storage, a retention period of at most 90 days, no redistribution,
resolved ethics status, confirmed Riot product registration/audit and a
runtime-injected key. Discovery additionally binds the exact sampling frame and
stopping-plan checksums and requires all seven registered endpoints across
europe and americas. A production credential additionally requires an Approved
or Acknowledged portal status. Both network commands repeat their applicable
check and stop before constructing an API client when it fails.

The preflight confirms that evidence was recorded; it does not grant legal or
institutional approval. The committed example is deliberately non-operational.

## Release checklist

- current policy reviewed and dated;
- Riot registration/status recorded privately;
- dataset and model licences verified;
- security scan and identifier scan pass;
- intended-use and prohibited-use language included;
- legal boilerplate visible in any player-facing interface;
- rollback, deletion and incident contacts defined.
