#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper for the Hermes-native install path.
# Preferred install method:
#   hermes profile install <repo> --alias

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v hermes >/dev/null 2>&1; then
  echo "Hermes is not installed. Install Hermes first, then run: hermes profile install $REPO_ROOT --alias" >&2
  exit 1
fi

exec hermes profile install "$REPO_ROOT" --alias -y
