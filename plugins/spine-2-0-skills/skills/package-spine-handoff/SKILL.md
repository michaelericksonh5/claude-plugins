---
name: package-spine-handoff
description: Manually package a validated Spine 4.3 proof package for animator handoff, including handoff ZIP creation and optional native .spine project import through official Spine CLI.
disable-model-invocation: true
argument-hint: "[package-dir]"
---

# Package Spine Handoff

Use this manual workflow when the user wants to send a package to Chris or create a native `.spine` project.

## Required Package Files

- `shared_symbols.json`
- `shared_symbols.atlas`
- `shared_symbols.png`
- `validation_report.json` with `status: "ok"`

## Handoff ZIP

Preferred handoff artifact:

```powershell
python scripts/package_spine_editor_handoff.py --package-dir <package-dir>
```

Or build it through the compiler with `--spine-editor-zip`.

The ZIP must contain JSON, atlas, PNG, unpacked `editor_images/`, `CREATE_SPINE_PROJECT.ps1`, README, and audit manifest. Send the ZIP; do not hand-pick loose files.

## Native `.spine` Project

Only create native `.spine` through official Spine CLI import:

```powershell
python scripts/create_spine_project.py `
  --package-dir <package-dir> `
  --spine-cli "C:\Program Files\Spine\Spine.com"
```

The script reads `shared_symbols.json` `skeleton.spine` and rejects import-version mismatches. Do not hand-write or reverse-engineer `.spine` files.

## Blocking Conditions

Stop when Spine CLI is unavailable, validation is not clean, required files are missing, the requested CLI version does not match `skeleton.spine`, or the user asks for production export automation.

## Final Report

Report the ZIP path, native `.spine` path if created, CLI command/report path, import-version used, and what Chris still needs to review.

Reference `references/spine_cli.md`, `references/compilers.md`, and `references/boundaries.md`.
