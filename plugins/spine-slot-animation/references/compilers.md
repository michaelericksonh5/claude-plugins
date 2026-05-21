# Compilers

Two compilers exist because two input shapes exist. Pick by what the user has in hand.

## Proof compiler vs layered rig compiler

| Compiler | Input | Output shape |
|---|---|---|
| **Proof compiler** | Single body PNG + recipe key | Single-bone, single-slot, single-attachment skeleton with family-typical animations |
| **Layered rig compiler** | Separated per-layer PNGs + optional rig layout | Multi-bone, multi-slot, multi-attachment skeleton; one bone per layer; layered animations composed across all parts |

Pick the **proof compiler** for:

- LP letters / numerics (single-layer body).
- JP badges (star/badge body + optional sheen).
- Value symbols (body + optional value text overlay).
- Single-image wilds, scatters, meters, transitions, celebrations, avatars.
- Anywhere the symbol ships as one body image with optional decorative slots (glow, sparkle, frame, glass).

Pick the **layered rig compiler** for:

- Character HP symbols with separated expression layers (head, eyes-blink, mouth-laugh, hands, arms, hat).
- BO/special symbols with separated feature layers.
- Anywhere multi-bone parent/child relationships and shared-timeline composition matter.

If unsure, look at the source-layer count. A folder with one body PNG (plus a few decorative layers) is proof. A folder with 8+ named-part PNGs is layered.

## Proof compiler — H5G reference

### Compile a base proof

```powershell
uv run python research/hp_symbol_proof_compiler.py `
  research/generated/proof_layers `
  research/generated/proof_hp_symbol_default `
  --force
```

### Compile with controls

```powershell
uv run python research/hp_symbol_proof_compiler.py `
  research/generated/proof_layers `
  research/generated/proof_hp_symbol_more_bouncy `
  --controls research/examples/more_bouncy.controls.json `
  --force
```

### Compile other proof recipes

```powershell
uv run python research/hp_symbol_proof_compiler.py `
  <input_dir> <output_dir> --recipe-type <recipe_key> --force
```

`<recipe_key>` must be one of the 15 supported recipe types (see `references/families.md`).

### What the proof compiler emits

- `shared_symbols.json` — Spine 3.8 v10_linear skeleton. This is legacy proof output, not the current default.
- `shared_symbols.atlas` — atlas metadata.
- `shared_symbols.png` — packed atlas page.
- `validation_report.json` — recipe type, recipe support, export profile, applied controls, V10-linear check, no-op controls, idle-loop validation.
- `preview_validation_report.json` — preview shape and readiness.
- `preview.html` — Spine Web Player preview.

### Proof compiler input contract

Required layer:

- `symbol_body.png`

Optional layers:

- `symbol_shadow.png`
- `symbol_highlight.png`
- `glow.png`
- `sparkle.png`
- `back_frame.png`
- `front_frame.png`
- `glass.png`

The compiler reads only PNG layers supplied in the input folder.

## Layered rig compiler — H5G reference

### Compile a layered rig

```powershell
uv run python research/layered_rig_compiler.py `
  <input_dir> <output_dir> `
  --force
```

The input may include `rig_layout.json` and `rig_adjustments.json`. If no layout exists, the compiler writes `generated_rig_layout.json` in the output folder for manual editing.

### Optional flags

```text
--layout LAYOUT             Path to a rig_layout.json overriding the default
--adjustments ADJUSTMENTS   Path to rig_adjustments.json
--advanced-policy POLICY    Optional advanced Spine policy JSON for validation
```

### What the layered rig compiler emits

- `shared_symbols.json` — 4.x skeleton with multi-bone hierarchy and composed `idle` / `breathe` / `land` / `win` timelines.
- `shared_symbols.atlas` — atlas metadata.
- `shared_symbols.png` — packed atlas page.
- `validation_report.json` — referenced PNGs exist, atlas regions cover every attachment, draw order = z-order, advanced-feature absence (no mesh / IK / deform / clipping / events unless explicitly opt-in).
- `preview.html` + per-animation APNG (`preview_motion_idle.apng`, `preview_motion_win.apng`, `preview_motion_land.apng`, `preview_motion_breathe.apng`).
- `generated_rig_layout.json` (if no layout was supplied).

### Applying controls

The proof compiler accepts a controls JSON via `--controls`. The layered rig compiler reads its `rig_layout.json` and `rig_adjustments.json` for transform/z-order iteration; bounded animator controls (in the schema described in `references/controls.md`) attach to the proof workflow but the layered compiler bakes the recipe-specific amplitudes from the motion profile by default.

When the user provides a controls JSON for a layered character rig, route to the proof workflow for the matching recipe, or extend the layered compiler with a controls hook. Don't try to retro-apply controls in chat by hand-editing the rig_layout.

## Batch orchestration

## Evidence index

Before promoting new compiler behavior, rebuild and consult `assets/compiler_evidence_index.json`:

```powershell
python scripts/build_compiler_evidence_index.py
```

The index is generated only from existing H5G research outputs under the local Claude Spine `research/` tree. It records family contracts, coverage, bakeoff gaps, advanced gates, UI/system evidence, contextual layer evidence, compendium summaries, and exact motion-profile availability. Treat missing required sources or malformed required files as blockers; optional missing sources are recorded as warnings.

### Compile all Photoshop2Spine exports under a folder

```powershell
uv run python research/compile_photoshop2spine_exports.py `
  <exports_root> <output_root>
```

Runs intake + compile + preview per symbol in `<intake_root>`. Outputs at `<output_root>/<symbol>/compiled/`.

### Local proof UI

The H5G project has a local web UI for proof package generation with role-map / source-layer manifest selectors:

```powershell
uv run python app/local_proof_ui.py
```

It can translate a revision note into controls JSON via Claude Code CLI before compiling:

```powershell
uv run python app/local_proof_ui.py --mock-claude --dry-run-note "make it more bouncy but less flashy"
```

The UI writes Claude-generated controls to `generated_controls.json` in the run folder and validates that file with the compiler controls loader before compiling.

## Preview generation

```powershell
uv run python research/spine_preview_generator.py <package_dir>
```

The preview uses the matching Spine Web Player line with local package assets.

### If browser local fetches are blocked

Serve the output folder:

```powershell
Set-Location <package_dir>
python -m http.server 8000
```

Then open `http://localhost:8000/preview.html`. Or, for a batch overview:

```powershell
uv run python -m http.server 8780 --bind 127.0.0.1 --directory <batch_root>
```

Open `http://127.0.0.1:8780/<symbol>/compiled/preview.html` or `http://127.0.0.1:8780/index.html`.

## Packaging for handoff

Create a review-only folder and zip:

```powershell
uv run python research/package_h5g_export.py <package_dir>
```

The packager copies Spine assets, preview HTML, validation reports, optional UI-generated controls JSON, a source layer manifest, and `audit_manifest.json`. It is NOT production deployment and does NOT write to Perforce, `G:\artSource`, or production paths.

For Spine Editor import:

```powershell
uv run python research/package_for_spine_editor.py <batch_root>
$pkgDir = "<batch_root>\spine_editor_packages"
Compress-Archive -Path "$pkgDir\*.zip", "$pkgDir\_summary.json" `
  -DestinationPath "<batch_root>\h5g_symbols_for_<recipient>.zip" -Force
```

Per-symbol ZIPs + combined batch ZIP that the art team imports into the current approved Spine Editor.

## Choosing a profile

The proof compiler emits Spine 3.8 v10_linear by default; the portable builder targets current 4.3 by default. To stay consistent:

| Goal | Compiler | Profile |
|---|---|---|
| New 4.3-targeted layered character rig | Portable builder | Spine 4.3.04 (default) |
| New 4.3-targeted single-body symbol | Portable builder single-layer input | Spine 4.3.04 |
| Legacy proof package for an existing v10_linear pipeline | Proof | `v10_linear` |
| Quick proof scaffold to test recipe controls | Proof | `v10_linear` |

For new work, prefer the portable 4.3 path. The v10_linear profile is a fallback, not a target. See `references/spine_43_contract.md` for the current default and `references/spine_42_contract.md#38-fallback-profile-v10_linear` for legacy migration notes.

## After compile — required next steps

1. Read `validation_report.json`. If it reports a failure, fix and recompile before moving on.
2. Read `preview_validation_report.json`. Same rule.
3. For current 4.x packages, run the compatibility/import-version gates. See `references/validation.md`.
4. Open `preview.html` or the APNGs and visually confirm the rig is recognizable.

Only after all three pass should you describe the package as ready.

For Phase 10 production export review, run the report-only export gate after those checks:

```powershell
python scripts/production_export_gate.py `
  --package-dir <output> `
  --production-export-profile <profile.json>
```

Or ask the portable builder to check the gate after a build:

```powershell
python scripts/build_spine_package.py ... `
  --production-export-profile <profile.json> `
  --check-production-export-gate
```

The gate writes `production_export_gate_report.json` and never invokes Spine CLI, creates `.skel`, activates a license, writes to Perforce, or writes to source art. A passing gate is `ready_for_manual_export` only.

For the official Spine CLI command families and this plugin's automation boundaries, see `references/spine_cli.md`. In short: native `.spine` creation may use the official import/info path, while export, clean, pack/unpack, advanced flags, and any production write remain policy-gated.

## Spine Editor handoff

For animator review, generate the handoff ZIP:

```powershell
python scripts/build_spine_package.py `
  --layer-dir <png_folder> `
  --family hp_symbol --rank 1 `
  --doc-width 178 --doc-height 178 `
  --out-dir <output_dir> `
  --build-preview `
  --spine-editor-zip `
  --create-spine-project `
  --spine-cli "C:\Program Files\Spine\Spine.com"
```

When the machine has Spine installed, `--create-spine-project` invokes Spine's official CLI and writes a native `.spine` file plus `spine_project_report.json`. If the machine does not have Spine installed, send `<output_dir>/spine_editor_handoff.zip`; it includes `CREATE_SPINE_PROJECT.ps1` so Chris can unzip it and create the `.spine` file locally with his Spine CLI. Do not manually collect a subset of loose files. The ZIP also keeps `shared_symbols.atlas` and `shared_symbols.png` together for runtime preview/game validation and includes import instructions plus an audit manifest.

## Native `.spine` project generation

Do not hand-author `.spine` files. Spine's project format is owned by the Spine Editor. The documented automation path is to run Spine's CLI import:

```powershell
Spine -u <shared_symbols.json skeleton.spine> -i <compiled_package_dir>\shared_symbols.json -o <output_project.spine> -r <skeleton_name>
```

The plugin wrapper for that command is:

```powershell
python scripts/create_spine_project.py <compiled_package_dir> `
  --spine-cli "C:\Program Files\Spine\Spine.com" `
  --output-project <output_project.spine>
```

It:

- Finds `Spine.com` from `--spine-cli`, `SPINE_CLI`, PATH, or common install folders.
- Uses the `skeleton.spine` value from `shared_symbols.json` by default.
- Refuses a mismatched `--spine-version`; Spine's official import path requires JSON data to be imported with the same editor version that wrote the data.
- Imports the generated JSON to a `.spine` output under an allowed path.
- Probes the resulting project with `Spine -i <output_project.spine>`.
- Writes `spine_project_report.json`.

This is the only automated Spine CLI path in the plugin. The broader CLI surface is documented in `references/spine_cli.md`, but production export remains gated.

Remaining promotion work:

- Run the command on a machine with a real licensed Spine install and add captured acceptance evidence.
- Verify whether image paths resolve automatically or still need the README's manual Images-path step.
- Re-export JSON from the generated `.spine` and compare bones, slots, skins, attachments, animations, and mesh data against the compiler output.

## When the compiler complains

If the compiler reports a missing layer, an invalid recipe key, or an out-of-range control value, the user's input violates the contract somewhere. Don't try to massage the input to make it compile. Surface the error verbatim, identify which part of the contract was violated (point to `references/families.md` for required layers, `references/controls.md` for control ranges), and ask the user to fix at the source.

The compiler is the source of truth. The skill's job is to keep the user's inputs inside its contract.
