$ErrorActionPreference = 'Stop'

$pluginRoot = Split-Path -Parent $PSScriptRoot
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  throw 'Node.js is required. Install Node.js 20 LTS or newer, then rerun this installer.'
}

node (Join-Path $pluginRoot 'scripts\lib\install.js') windows
if ($LASTEXITCODE -ne 0) {
  throw "token-saver installer failed with exit code $LASTEXITCODE"
}
