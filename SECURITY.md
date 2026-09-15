# Security policy

Do not report credentials in a public issue. Use GitHub's private vulnerability
reporting channel when enabled, or contact the repository owner privately.

Riot API credentials must be injected through the environment and must never be
stored in source, notebooks, logs, test fixtures, model metadata or browser
bundles. A key found in history is considered compromised and must be revoked;
deleting the visible line is not sufficient.

Raw identifiers are excluded from published derived data. Research artifacts
must contain pseudonymous match identifiers and no PUUID-to-Riot-ID mapping.
