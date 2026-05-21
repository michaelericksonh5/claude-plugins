$ErrorActionPreference = 'Stop'

$ConfigDir = Join-Path $env:USERPROFILE '.h5g-slot-art-creator'
$EnvPath = Join-Path $ConfigDir '.env'

function Read-SlotEnvFile {
    $Values = [ordered]@{}
    if (Test-Path -LiteralPath $EnvPath) {
        foreach ($Line in Get-Content -LiteralPath $EnvPath) {
            $Trimmed = $Line.Trim()
            if (-not $Trimmed -or $Trimmed.StartsWith('#')) { continue }
            $Index = $Trimmed.IndexOf('=')
            if ($Index -lt 1) { continue }
            $Values[$Trimmed.Substring(0, $Index).Trim()] = $Trimmed.Substring($Index + 1).Trim()
        }
    }
    return $Values
}

function Write-SlotEnvFile {
    param([hashtable]$Values)

    New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
    $Lines = @(
        '# slot-art-creator-node API keys',
        '# Written by setup-keys.ps1',
        '# Do not paste these values into chat.'
    )

    foreach ($Name in @(
        'GEMINI_API_KEY',
        'FAL_KEY',
        'OPENAI_API_KEY',
        'HTTPS_PROXY',
        'HTTP_PROXY',
        'NO_PROXY',
        'NODE_EXTRA_CA_CERTS',
        'SSL_CERT_FILE'
    )) {
        if ($Values.ContainsKey($Name) -and $Values[$Name]) {
            $Lines += "$Name=$($Values[$Name])"
        }
    }

    Set-Content -LiteralPath $EnvPath -Value $Lines -Encoding ASCII
}

function Read-HiddenText {
    param([string]$Prompt)

    $Secure = Read-Host $Prompt -AsSecureString
    $Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
    }
}

function Set-SlotKey {
    param(
        [hashtable]$Values,
        [string]$Name,
        [string]$Label,
        [string]$Url
    )

    Write-Host ''
    Write-Host $Label
    Write-Host "Get a key: $Url"
    Write-Host 'Paste the key below. Input is hidden. Leave blank to skip.'
    $Value = Read-HiddenText $Name
    if ($Value) {
        $Values[$Name] = $Value.Trim()
        Write-Host "$Name saved."
    } else {
        Write-Host "$Name skipped."
    }
}

Write-Host ''
Write-Host 'slot-art-creator-node - API key setup'
Write-Host '======================================'
Write-Host ''
Write-Host "Keys will be saved to: $EnvPath"
Write-Host 'Input is hidden and never goes through Claude chat.'
Write-Host ''
Write-Host '[1] Gemini only'
Write-Host '[2] fal.ai only'
Write-Host '[3] OpenAI only'
Write-Host '[4] NB2 keys (Gemini + fal.ai)'
Write-Host '[5] All keys'
$Choice = Read-Host 'Choice [1]'
if (-not $Choice) { $Choice = '1' }

$Values = Read-SlotEnvFile

switch ($Choice) {
    '5' {
        Set-SlotKey $Values 'GEMINI_API_KEY' 'Google Gemini / NB2' 'https://aistudio.google.com/apikey'
        Set-SlotKey $Values 'FAL_KEY' 'fal.ai / NB2 fallback' 'https://fal.ai/dashboard'
        Set-SlotKey $Values 'OPENAI_API_KEY' 'OpenAI / gpt-image-2 (optional)' 'https://platform.openai.com/api-keys'
    }
    '4' {
        Set-SlotKey $Values 'GEMINI_API_KEY' 'Google Gemini / NB2' 'https://aistudio.google.com/apikey'
        Set-SlotKey $Values 'FAL_KEY' 'fal.ai / NB2 fallback' 'https://fal.ai/dashboard'
    }
    '3' {
        Set-SlotKey $Values 'OPENAI_API_KEY' 'OpenAI / gpt-image-2 (optional)' 'https://platform.openai.com/api-keys'
    }
    '2' {
        Set-SlotKey $Values 'FAL_KEY' 'fal.ai / NB2 fallback' 'https://fal.ai/dashboard'
    }
    default {
        Set-SlotKey $Values 'GEMINI_API_KEY' 'Google Gemini / NB2' 'https://aistudio.google.com/apikey'
    }
}

Write-SlotEnvFile $Values

Write-Host ''
Write-Host "Setup complete. Saved keys to: $EnvPath"
Write-Host 'Restart Claude Desktop / reload Claude Code so the MCP server sees the new keys.'
