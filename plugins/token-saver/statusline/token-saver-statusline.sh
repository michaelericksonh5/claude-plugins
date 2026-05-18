#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
helper="$script_dir/../scripts/lib/statusline.js"

if [ ! -f "$helper" ]; then
  helper="$script_dir/token-saver/lib/statusline.js"
fi

if [ ! -f "$helper" ]; then
  helper="$(dirname "$script_dir")/scripts/lib/statusline.js"
fi

if ! command -v node >/dev/null 2>&1; then
  printf '%s\n' 'model: unknown | effort: auto | ctx: n/a | cache read: 0'
  exit 0
fi

node "$helper" || printf '%s\n' 'model: unknown | effort: auto | ctx: n/a | cache read: 0'
