#!/usr/bin/env bash
set -euo pipefail

if rg --hidden --glob '!.git/**' --glob '!scripts/check-secrets.sh' \
  --glob '!SECURITY.md' 'RGAPI-[A-Za-z0-9_-]{20,}' .; then
  echo 'Potential Riot API credential found in the current tree.' >&2
  exit 1
fi

if rg --hidden --glob '!.git/**' --glob '!*.example' \
  '(RIOT_API_KEY|X-Riot-Token)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9_-]{20,}' .; then
  echo 'Potential assigned Riot credential found in the current tree.' >&2
  exit 1
fi

echo 'No current-tree Riot credential patterns detected.'
