# Marketplace Publishing

Do not publish until local validation passes.

## Validate

```powershell
claude plugin validate .
```

## Package

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
```

This creates `dist/token-saver.zip`. The package must not include nested `.zip` or `.plugin` files.

## Verify Package Contents

```powershell
$zipPath = ".\dist\token-saver.zip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zipPath))
try {
  $nested = @($zip.Entries | Where-Object { $_.FullName -match '\.(zip|plugin)$' })
  if ($nested.Count -gt 0) { throw "Nested archives found: $($nested.FullName -join ', ')" }
} finally {
  $zip.Dispose()
}
```

## Version Bump

Before publishing a new release, update `.claude-plugin/plugin.json` and any marketplace entry to the same version.

## Marketplace Repository Steps

1. Copy this plugin folder to `claude-plugins/plugins/token-saver`.
2. Do not copy `dist/`, `.zip`, or `.plugin` artifacts.
3. Add or update the marketplace entry for `token-saver`.
4. Run `claude plugin validate .\plugins\token-saver` in the marketplace clone.
5. Scan `plugins/token-saver` for `.zip` and `.plugin` files and remove any artifacts before publishing.

This project intentionally uses Node.js helpers plus PowerShell and shell wrappers. It does not require a package manager or Python.
