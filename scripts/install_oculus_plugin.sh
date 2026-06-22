#!/usr/bin/env bash
set -euo pipefail

# Installs the Oculus Hermes plugin into the active Oculus profile home
# so it can be enabled with: hermes -p oculus plugins enable oculus

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/hermes/plugin/oculus"

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

if [ ! -d "$SRC_DIR" ]; then
  echo "Missing plugin dir: $SRC_DIR" >&2
  exit 1
fi

DST_HOME="$(resolve_oculus_home)"
DST_DIR="$DST_HOME/plugins/oculus"

mkdir -p "$DST_HOME/plugins"
rm -rf "$DST_DIR"
cp -R "$SRC_DIR" "$DST_DIR"

echo "Installed Hermes plugin to: $DST_DIR"

echo "Note: ./scripts/install_agent_pack.sh will also enable the plugin + set OCULUS_WORKDIR automatically (when Hermes is installed)."
echo "Manual enable (if needed):"
echo "  hermes -p oculus plugins enable oculus"
echo "Manual env (if needed):"
echo "  hermes -p oculus config env-path"
echo "  OCULUS_WORKDIR=$REPO_ROOT"
echo "If tools don't appear in-session: /tools -> enable 'oculus'"