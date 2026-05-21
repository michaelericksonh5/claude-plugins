$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$doctor = Join-Path $scriptDir 'lib\doctor.js'
node $doctor @args
