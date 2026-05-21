# Wrapper — delegates to setup-keys.mjs
# Keys are written to ~/.claude/settings.json and shared across all
# plugins in the michaelericksonh5-plugins marketplace.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
node "$scriptDir\setup-keys.mjs" @args
