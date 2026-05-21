---
name: compile-spine-package
description: Manually compile separated PNG layers or PSD-export manifests into a validated Spine 4.3 proof package using deterministic scripts. Use when the user explicitly asks to build, compile, regenerate, or create shared_symbols output.
disable-model-invocation: true
argument-hint: "[layer-folder-or-manifest] [family]"
---

# Compile Spine Package

Use this manual workflow only when the user wants a package built or regenerated. Do not freehand Spine JSON.

## Inputs Required

- Layer folder containing transparent PNG parts, or a documented PSD export manifest plus PNG layers.
- Recipe family, or enough layer evidence to classify with `scripts/classify_family.py`.
- Document width and height from the PSD/artboard.
- Optional controls JSON matching `assets/recipe_controls_schema.json`.

If any required input is missing, ask one concise question before compiling.

## Default Command

```powershell
python scripts/build_spine_package.py `
  --layer-dir <folder-of-png-layers> `
  --family <recipe-family> `
  --rank <N> `
  --doc-width <width> `
  --doc-height <height> `
  --controls <controls.json> `
  --out-dir <output-dir> `
  --build-preview `
  --spine-editor-zip
```

Omit `--controls` when there is no controls file. Add `--create-spine-project --spine-cli "C:\Program Files\Spine\Spine.com"` only when the user wants native `.spine` creation on a machine with Spine CLI available.

## Opt-In Feature Flags

Use only when explicitly requested or backed by a reviewed plan:

- `--enable-sequences`
- `--mesh-plan <mesh_plan.json>`
- `--auto-mesh-plan`
- `--auto-bind-weights`
- `--skin-plan <skin_plan.json>`
- `--enable-ik`
- `--enable-transform-constraints`
- `--enable-clipping <plan.json>`
- `--enable-events <plan.json>`
- `--enable-physics`
- `--composite-expressions`
- `--render-qa-frames`

Automatic mesh plans and auto weights remain review-required proof artifacts, not final production rigging.

## Required Outputs

- `shared_symbols.json`
- `shared_symbols.atlas`
- `shared_symbols.png`
- `validation_report.json`
- `preview.html` when `--build-preview` is used
- `spine_editor_handoff.zip` when `--spine-editor-zip` is used

## Blocking Conditions

Stop and report blockers when:

- The family is unsupported or review-gated.
- Source paths point at protected source-art destinations.
- Validation fails.
- Atlas page or attachment references are missing.
- The user requests hand-authored final Spine JSON.
- The user asks for production export, final weight painting, or final art approval.

## Final Report

Report the command run, output directory, validation status, preview/handoff artifacts, and any remaining review requirements. Reference `references/compilers.md`, `references/intake.md`, and `references/validation.md` for deeper details.
