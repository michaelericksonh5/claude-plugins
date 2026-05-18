$ErrorActionPreference = 'Continue'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$candidates = @(
  (Join-Path (Split-Path -Parent $scriptDir) 'scripts\lib\hook.js'),
  (Join-Path (Split-Path -Parent $scriptDir) 'token-saver\lib\hook.js')
)
$helper = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

try {
  $inputText = [Console]::In.ReadToEnd()
  $inputText | node $helper
} catch {
  Write-Output "token-saver hook warning: could not summarize output ($($_.Exception.Message))"
}

exit 0
