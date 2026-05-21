$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'webgamedev-p4.ps1'
& $scriptPath doctor
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
