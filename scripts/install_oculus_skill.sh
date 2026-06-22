#!/usr/bin/env bash
set -euo pipefail

# Installs the Oculus skill into the active Oculus profile home so /agent oculus
# launches with native context.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/hermes/skills/oculus/SKILL.md"

resolve_oculus_home() {
  local fallback="${HERMES_HOME:-$HOME/.hermes}"

  if command -v hermes >/dev/null 2>&1; then
    hermes profile create oculus >/dev/null 2>&1 || true

    local profile_config
    profile_config="$(hermes -p oculus config path 2>/dev/null | tail -n 1 || true)"
    if [ -n "$profile_config" ]; then
      printf '%s\n' "${profile_config%/config.yaml}"
      return
    fi
  fi

  printf '%s\n' "$fallback"
}

if [ ! -f "$SRC" ]; then
  echo "Missing skill source: $SRC" >&2
  exit 1
fi

DST_HOME="$(resolve_oculus_home)"
DST_DIR="$DST_HOME/skills/oculus"
DST="$DST_DIR/SKILL.md"

mkdir -p "$DST_DIR"
cp "$SRC" "$DST"

echo "Installed Hermes skill: $DST"
