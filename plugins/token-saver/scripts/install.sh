#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
plugin_root=$(dirname "$script_dir")

if ! command -v node >/dev/null 2>&1; then
  printf '%s\n' 'Node.js is required. Install Node.js 20 LTS or newer, then rerun this installer.' >&2
  exit 1
fi

node "$plugin_root/scripts/lib/install.js" unix
