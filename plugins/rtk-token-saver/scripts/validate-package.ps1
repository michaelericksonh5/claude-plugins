$ErrorActionPreference = 'Stop'

$pluginRoot = Split-Path -Parent $PSScriptRoot

Push-Location $pluginRoot
try {
  claude plugin validate .
  if ($LASTEXITCODE -ne 0) {
    throw "claude plugin validate failed with exit code $LASTEXITCODE"
  }
  Write-Output 'Plugin validation passed.'

  node (Join-Path $pluginRoot 'scripts\lib\validate-package.js')
  if ($LASTEXITCODE -ne 0) {
    throw "package validation failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}
