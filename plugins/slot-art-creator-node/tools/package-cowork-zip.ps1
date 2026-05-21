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
    "setup-keys.js",
    "setup-keys.bat",
    "setup-keys.ps1",
    "setup-keys.sh",
    ".env.example"
)

$ExcludedDirs = @(
    "node_modules",
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
    "*.zip",
    "*.7z",
    "*.tar",
    "*.tgz",
    "*.tar.gz",
    "*.rar",
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

$ArchivePatterns = @("*.zip", "*.7z", "*.tar", "*.tgz", "*.tar.gz", "*.rar")

function Assert-FreshMcpBundle {
    $McpRoot = Join-Path $PluginRoot "nb2-mcp-server"
    $Bundle = Join-Path $McpRoot "dist\index.mjs"
    if (-not (Test-Path -LiteralPath $Bundle)) {
        throw "MCP bundle missing: $Bundle. Run: cd nb2-mcp-server; npm ci; npm run build"
    }

    $BundleTime = (Get-Item -LiteralPath $Bundle).LastWriteTimeUtc
    $SourceFiles = Get-ChildItem -LiteralPath $McpRoot -Recurse -Force -File |
        Where-Object {
            $_.FullName -notlike "*\node_modules\*" -and
            $_.FullName -notlike "*\dist\*" -and
            ($_.Extension -in @(".js", ".json") -or $_.Name -eq "package-lock.json")
        }
    $NewestSource = $SourceFiles | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if ($NewestSource -and $NewestSource.LastWriteTimeUtc -gt $BundleTime) {
        throw "MCP bundle is stale: $Bundle is older than $($NewestSource.FullName). Run: cd nb2-mcp-server; npm run build"
    }
}

function Remove-ExcludedContent {
    param([string]$Root)

    Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory |
        Where-Object { $ExcludedDirs -contains $_.Name } |
        Sort-Object FullName -Descending |
        Remove-Item -Recurse -Force

    Get-ChildItem -LiteralPath $Root -Recurse -Force -File |
        Where-Object {
            $Name = $_.Name
            if ($Name -eq ".env.example") { return $false }
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

function Assert-NoNestedArchives {
    param([string]$ZipPath)

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        $ArchiveEntries = @(
            $Zip.Entries |
                Where-Object {
                    $Name = $_.FullName
                    $ArchivePatterns | Where-Object { $Name -like $_ }
                }
        )
        if ($ArchiveEntries.Count -gt 0) {
            $Names = ($ArchiveEntries | Select-Object -ExpandProperty FullName) -join ", "
            throw "Nested archive files are not allowed in plugin payloads: $Names"
        }
    } finally {
        $Zip.Dispose()
    }
}

try {
    Assert-FreshMcpBundle
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
    Assert-NoNestedArchives -ZipPath $ZipPath

    Write-Host ""
    Write-Host "Legacy/admin Cowork upload ZIP created:"
    Write-Host "  $ZipPath"
    Write-Host "  Size: $SizeMb MB"
    Write-Host ""
    Write-Host "Use this only if GitHub-synced marketplaces are blocked by org policy."
    Write-Host "Generated archives stay under ignored dist/ and are excluded from plugin payloads."
} finally {
    if (Test-Path -LiteralPath $StageRoot) {
        Remove-Item -LiteralPath $StageRoot -Recurse -Force
    }
}
