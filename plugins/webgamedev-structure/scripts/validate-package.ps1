$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'lib/validate-package.js'
node $scriptPath
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
