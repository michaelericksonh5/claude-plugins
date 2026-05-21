#!/usr/bin/env bash
# Wrapper — delegates to setup-keys.mjs
# Keys are written to ~/.claude/settings.json and shared across all
# plugins in the michaelericksonh5-plugins marketplace.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
node "$SCRIPT_DIR/setup-keys.mjs" "$@"
