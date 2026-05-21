$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'lib/webgamedev-p4.js'
node $scriptPath @args
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
