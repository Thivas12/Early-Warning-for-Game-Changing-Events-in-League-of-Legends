#!/usr/bin/env bash
set -euo pipefail

# Git is already required by the checkout. A missing search binary must not
# turn the credential check into a successful CI step.
check_pattern() {
  local message="$1"
  local pattern="$2"
  shift 2
  local status=0
  git grep -q -I -E "$pattern" -- . "$@" || status=$?
  if (( status == 0 )); then
    echo "$message" >&2
    exit 1
  fi
  if (( status != 1 )); then
    echo 'Credential scan could not inspect the checked-out tree.' >&2
    exit "$status"
  fi
}

check_pattern 'Potential Riot API credential found in the current tree.' \
  'RGAPI-[A-Za-z0-9_-]{20,}' \
  ':(exclude)scripts/check-secrets.sh' ':(exclude)SECURITY.md'

check_pattern 'Potential assigned Riot credential found in the current tree.' \
  '(RIOT_API_KEY|X-Riot-Token)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9_-]{20,}' \
  ':(exclude,glob)**/*.example' ':(exclude,glob)*.example'

echo 'No current-tree Riot credential patterns detected.'
