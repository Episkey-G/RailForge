#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
RAILFORGE_BIN="$CODEX_ROOT/bin/railforge"
if [[ ! -x "$RAILFORGE_BIN" && -x "$CODEX_ROOT/bin/railforge.exe" ]]; then
  RAILFORGE_BIN="$CODEX_ROOT/bin/railforge.exe"
fi
PYTHON_BIN="${RAILFORGE_PYTHON_BIN:-}"

if [[ -x "$RAILFORGE_BIN" ]]; then
  if [[ " $* " == *" --workspace "* ]]; then
    exec "$RAILFORGE_BIN" spec-init "$@"
  fi

  exec "$RAILFORGE_BIN" spec-init --workspace "$PWD" "$@"
fi

if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python not found. Install RailForge binary or set RAILFORGE_PYTHON_BIN." >&2
    exit 1
  fi
fi

if [[ " $* " == *" --workspace "* ]]; then
  exec "$PYTHON_BIN" -m railforge spec-init "$@"
fi

exec "$PYTHON_BIN" -m railforge spec-init --workspace "$PWD" "$@"
