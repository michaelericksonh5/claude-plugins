$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$candidates = @(
  (Join-Path $scriptDir '..\scripts\lib\statusline.js'),
  (Join-Path $scriptDir 'token-saver\lib\statusline.js'),
  (Join-Path $PSScriptRoot '..\scripts\lib\statusline.js')
)
$helper = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $helper) {
  $helper = Join-Path (Split-Path -Parent $scriptDir) 'scripts\lib\statusline.js'
}

$inputText = [Console]::In.ReadToEnd()
try {
  $inputText | node $helper
} catch {
  Write-Output 'model: unknown | effort: auto | ctx: n/a | cache read: 0'
}
