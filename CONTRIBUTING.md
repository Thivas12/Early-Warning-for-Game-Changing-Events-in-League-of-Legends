# Contributing

Research changes are made through pull requests. Each experiment PR must state:

1. the hypothesis fixed before execution;
2. the dataset and split manifest hashes;
3. the primary metric and stopping rule;
4. every attempted configuration, including negative results;
5. the command required to reproduce the result.

Code changes must pass formatting, linting, strict typing, unit tests and the
small-fixture reproducibility check. Do not commit datasets, credentials, raw
player identifiers, generated notebook output or selectively chosen runs.

AI assistance is permitted for planning, coding, review and editing. A human
author remains responsible for every scientific claim and citation. Material
AI use must be recorded in `docs/ai-usage.md`.
