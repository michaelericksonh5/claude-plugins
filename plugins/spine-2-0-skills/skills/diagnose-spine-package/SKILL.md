---
name: diagnose-spine-package
description: Manually diagnose broken Spine 4.3 proof packages, blank previews, import-version errors, missing attachments, off-center rigs, or runtime failures without hand-editing JSON.
disable-model-invocation: true
argument-hint: "[package-dir-or-error]"
---

# Diagnose Spine Package

Use this manual workflow for broken preview, import, runtime, or visual behavior reports.

## Evidence To Gather

- Exact error text or screenshot description.
- Package directory path, if available.
- `validation_report.json` and `preview_validation_report.json`, if present.
- `shared_symbols.json` `skeleton.spine` value.
- Whether the failure occurs in Spine Player, Spine Editor import, or native `.spine` creation.

## Diagnosis Order

1. Read `references/pitfalls.md` for symptom mapping.
2. Check `references/spine_43_contract.md` for current JSON/import rules.
3. Run compiler validation or inspect existing validation reports.
4. Confirm `skeleton.spine` matches the CLI/editor import version.
5. Check atlas page filename, attachment paths, skins array shape, rotate `value`, slot `rgba`, and two-color `rgba2` plus setup `dark`.
6. If the issue is visual rather than structural, route to `references/visual_remediation.md` and `scripts/visual_remediation_loop.py`.

## Common Fix Routes

- Blank canvas: regenerate through the current 4.3 builder if legacy field shapes are present.
- Version mismatch: regenerate for the target version or import with the JSON version first; do not edit `skeleton.spine` alone.
- Missing images in Spine Editor: use the handoff ZIP `editor_images/` path and `CREATE_SPINE_PROJECT.ps1`.
- Off-center or scattered rig: inspect document dimensions, parent-local bone placement, and animation delta keys.
- Wrong expression visible at rest: fix overlay polarity in setup color and attachment timelines.

## Blocking Conditions

Do not claim a fix until the relevant compiler/validator path is identified. Do not patch final JSON by hand. Do not claim Spine Editor import proof unless Spine CLI import has actually succeeded.

## Final Report

Lead with the likely root cause, then list evidence, exact fix path, commands to run, and remaining proof needed.
