#!/usr/bin/env bash
set -euo pipefail

# Installs the Oculus Hermes skin into the active Oculus profile home.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/hermes/skins/oculus.yaml"

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
  echo "Missing skin file: $SRC" >&2
  exit 1
fi

DST_HOME="$(resolve_oculus_home)"
DST_DIR="$DST_HOME/skins"
DST="$DST_DIR/oculus.yaml"

mkdir -p "$DST_DIR"
cp "$SRC" "$DST"

echo "Installed Hermes skin: $DST"

echo "Optional: activate it"
echo "  hermes config set display.skin oculus"
