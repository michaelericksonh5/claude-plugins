#!/usr/bin/env sh
set +e

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
helper="$(dirname "$script_dir")/scripts/lib/hook.js"

if [ ! -f "$helper" ]; then
  helper="$(dirname "$script_dir")/token-saver/lib/hook.js"
fi

if ! command -v node >/dev/null 2>&1; then
  printf '%s\n' 'token-saver hook warning: Node.js is required for output summarization.'
  exit 0
fi

node "$helper"
exit 0
