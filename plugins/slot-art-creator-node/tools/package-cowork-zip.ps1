param(
    [string]$OutputDir = (Join-Path $PSScriptRoot "..\dist")
)

$ErrorActionPreference = 'Stop'

$PluginRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ManifestPath = Join-Path $PluginRoot ".claude-plugin\plugin.json"
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Plugin manifest not found: $ManifestPath"
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
if (-not $Manifest.name) {
    throw "Plugin manifest must include a name."
}

$StageRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("cowork-plugin-" + [guid]::NewGuid().ToString("N"))
$Stage = Join-Path $StageRoot $Manifest.name
$ZipPath = Join-Path (Resolve-Path (New-Item -ItemType Directory -Force -Path $OutputDir)).Path "$($Manifest.name)-cowork-upload.zip"

$Items = @(
    ".claude-plugin",
    "skills",
    "agents",
    "hooks",
    "nb2-mcp-server",
    "shared",
    "package.json",
    "README.md",
    "setup-keys.js"
)

$ExcludedDirs = @(
    "node_modules",
    "dist",
    "generated",
    "logs",
    ".git",
    ".cache",
    "cache",
    "caches",
    "__pycache__"
)
$ExcludedFiles = @(
    ".env",
    ".env.*",
    "*.log",
    "npm-debug.log*",
    "yarn-debug.log*",
    "yarn-error.log*",
    "pnpm-debug.log*",
    "*.pem",
    "*credentials*",
    "id_rsa*",
    "id_ed25519*"
)

function Remove-ExcludedContent {
    param([string]$Root)

    Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory |
        Where-Object { $ExcludedDirs -contains $_.Name } |
        Sort-Object FullName -Descending |
        Remove-Item -Recurse -Force

    Get-ChildItem -LiteralPath $Root -Recurse -Force -File |
        Where-Object {
            $Name = $_.Name
            $ExcludedFiles | Where-Object { $Name -like $_ }
        } |
        Remove-Item -Force
}

function Invoke-ClaudePluginValidate {
    $Claude = Get-Command claude -ErrorAction SilentlyContinue
    if (-not $Claude) {
        Write-Warning "Claude CLI not found; skipping optional 'claude plugin validate'."
        return
    }

    Write-Host "Running optional Claude CLI validation..."
    & $Claude.Source plugin validate $PluginRoot
    if ($LASTEXITCODE -ne 0) {
        throw "'claude plugin validate' failed."
    }
    Write-Host "Claude CLI validation passed."
}

try {
    Invoke-ClaudePluginValidate
    New-Item -ItemType Directory -Force -Path $Stage | Out-Null

    foreach ($Item in $Items) {
        $Source = Join-Path $PluginRoot $Item
        if (Test-Path -LiteralPath $Source) {
            Copy-Item -LiteralPath $Source -Destination $Stage -Recurse -Force
        }
    }
    Remove-ExcludedContent -Root $Stage

    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Zip = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
    try {
        $Files = Get-ChildItem -LiteralPath $Stage -Recurse -Force -File
        foreach ($File in $Files) {
            $RelativePath = [System.IO.Path]::GetRelativePath($Stage, $File.FullName)
            $EntryName = $RelativePath.Replace([System.IO.Path]::DirectorySeparatorChar, '/')
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($Zip, $File.FullName, $EntryName) | Out-Null
        }
    } finally {
        $Zip.Dispose()
    }

    $SizeBytes = (Get-Item -LiteralPath $ZipPath).Length
    $SizeMb = [math]::Round($SizeBytes / 1MB, 2)
    if ($SizeBytes -gt 50MB) {
        throw "Cowork ZIP is $SizeMb MB, above the documented 50 MB organization upload limit."
    }

    Write-Host ""
    Write-Host "Cowork upload ZIP created:"
    Write-Host "  $ZipPath"
    Write-Host "  Size: $SizeMb MB"
    Write-Host ""
    Write-Host "Install in Claude Desktop > Cowork > Customize > Browse plugins > upload custom plugin file."
    Write-Host "For organization distribution, upload this ZIP in Organization settings > Plugins."
} finally {
    if (Test-Path -LiteralPath $StageRoot) {
        Remove-Item -LiteralPath $StageRoot -Recurse -Force
    }
}
