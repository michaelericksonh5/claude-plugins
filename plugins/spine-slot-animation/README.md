# Spine Slot Animation

Claude skill and portable compiler pipeline for generating validated Spine 4.3 proof packages for slot-game symbols, UI/system elements, and avatar state rigs.

The core rule is:

```text
AI proposes context. Deterministic tooling compiles. Validators and previews prove or reject.
```

This plugin is useful for:

- Turning notes such as "more bouncy", "less flashy", "slower idle", or "stronger land" into bounded animation controls.
- Compiling separated transparent PNG layers into `shared_symbols.json`, `shared_symbols.atlas`, and `shared_symbols.png`.
- Routing art into the documented H5G recipe families: HP/MP/LP symbols, wild, scatter, bonus, jackpot, special feature, value, winframes, meters, transitions, celebrations, and avatars.
- Validating Spine JSON structure, atlas references, animation loop/settle endpoints, optional mesh/skin/physics plans, and production-export approval gates.
- Producing report-only rig proposals that preserve confidence, review reasons, region/mesh decisions, and autonomous-rigger acceptance gates.
- Comparing mesh/weight fixtures against Chris-approved Spine exports and validating avatar runtime ownership contracts before stronger autonomous-rigger claims.
- Creating a visual remediation packet so Claude or an animator can inspect previews, record issues, generate bounded fixes, and recompile instead of stopping at pass/fail.
- Using H5G corpus/bakeoff evidence from the full local research workspace, the read-only G-drive consolidated report pack at `G:/artSource/_spineResources/H5G_Corpus_Bakeoff`, or the bundled advisory snapshot.
- Generating `preview.html` and running a browser-backed Spine Player runtime probe for representative packages.
- Creating native `.spine` projects through Spine's official CLI import path when approved, while treating broader CLI export/clean/pack/unpack commands as gated reference knowledge.

It is not a push-button replacement for a Spine animator or rigger. Production export, final weight painting, deform timelines, linked meshes, broad background/UI ambience, persistent avatar runtime state, Perforce submission, and final art approval remain gated.

For H5G corpus/bakeoff guidance, see `references/h5g_corpus_bakeoff_usage.md`, `assets/h5g_corpus_evidence_snapshot.json`, `references/h5g_corpus_distilled_knowledge.md`, and `assets/h5g_corpus_distilled_evidence.json`. The resolver can detect the full research workspace, the read-only G-drive report pack (`H5G_CORPUS_BAKEOFF_CONSOLIDATED_REPORT.md` + index), or a bundled advisory snapshot when neither external source is available. For autonomous-rigging research and claim boundaries, see `references/autonomous_rigging_research.md`, `references/rig_proposal.md`, and `assets/autonomous_rigging_evidence_index.json`. The proposal helper is report-only and does not emit production Spine output.

For the official Spine CLI command families and the plugin's support boundaries, see `references/spine_cli.md`. Production export remains gated.

## Claude Plugin Structure

```text
Claude_Spine_Generator/
  .claude-plugin/plugin.json
  README.md
  skills/spine-slot-animation/SKILL.md
  assets/
  evals/
  references/
  scripts/
  tests/
```

`skills/spine-slot-animation/SKILL.md` is the natural-language entrypoint. `.claude-plugin/plugin.json` exposes it as a Claude plugin skill.

## Natural-Language Triggers

The skill is designed to trigger when a user mentions:

- "animate this slot symbol"
- "rig these layers"
- "make this symbol more bouncy"
- "less flashy"
- "faster idle"
- "stronger land"
- "Spine 4.3"
- "Spine Player blank canvas"
- `shared_symbols.json`
- `shared_symbols.atlas`
- HP/LP/MP/JP/WD/SC/BO/SF/WYS symbol naming
- PSD-to-Spine or Photoshop layer export workflows

The skill should not freehand final Spine JSON in chat. It should classify the asset, choose a recipe, map layer roles, emit bounded controls if needed, and run deterministic compiler scripts.

## Quick Start

From this repository root:

```powershell
python scripts/build_spine_package.py `
  --layer-dir <folder-of-png-layers> `
  --family hp_symbol `
  --rank 3 `
  --doc-width 178 `
  --doc-height 178 `
  --out-dir <output-dir> `
  --build-preview `
  --spine-editor-zip `
  --create-spine-project `
  --spine-cli "C:\Program Files\Spine\Spine.com"
```

Omit `--create-spine-project` when Spine is not installed on the current machine. The handoff ZIP still includes `CREATE_SPINE_PROJECT.ps1`, which Chris can run locally with his Spine install.

The output directory receives:

- `shared_symbols.json`
- `shared_symbols.atlas`
- `shared_symbols.png`
- `validation_report.json`
- optional `preview.html`
- optional `spine_editor_handoff.zip`
- optional native `.spine` project when `--create-spine-project` is used on a machine with Spine CLI

Send the ZIP, not a hand-picked set of loose files, to a Spine animator. The ZIP refuses to build unless `shared_symbols.json`, `shared_symbols.atlas`, and `shared_symbols.png` are all present.

Spine does not import the ZIP directly. Chris should unzip it and run `CREATE_SPINE_PROJECT.ps1` to create the native `.spine` project through Spine's official CLI. The script imports with the version recorded in `shared_symbols.json` `skeleton.spine`; it does not paper over mismatches by changing the version string. Manual **File -> Import Data...** works only when Chris opens the same Spine version recorded in the JSON, then sets Spine's **Images** path to the included `editor_images/` folder if images show as missing. The atlas files stay in the bundle for runtime/game preview validation.

For representative runtime proof:

```powershell
python scripts/build_runtime_acceptance_fixtures.py
npx -p playwright node scripts/runtime_acceptance_probe.mjs --packages-root generated/runtime_acceptance/packages
```

For a non-compiling rig review proposal:

```powershell
python scripts/generate_rig_proposal.py `
  --family hp_symbol `
  --layer-interpretation <interpreted_layers.json> `
  --out generated/rig_proposals/<asset>.rig_proposal.json
```

For autonomous-rigger promotion gates:

```powershell
python scripts/compare_mesh_weight_parity.py `
  --approved <chris-approved-export.json> `
  --candidate <candidate-shared-symbols.json> `
  --out generated/mesh_weight_parity/<fixture>.json

python scripts/validate_avatar_runtime_contract.py `
  --contract <avatar-runtime-contract.json> `
  --out generated/avatar_runtime_contracts/<avatar>.json
```

For preview-driven remediation:

```powershell
python scripts/visual_remediation_loop.py `
  --package-dir <compiled-package-dir> `
  --out-dir generated/visual_reviews/<asset> `
  --render-frames
```

Claude or the animator inspects `preview.html` and the packet, writes `visual_review.json`, then runs:

```powershell
python scripts/visual_remediation_loop.py `
  --review generated/visual_reviews/<asset>/visual_review.json `
  --out-dir generated/visual_reviews/<asset>
```

Safe visual findings become `visual_remediation.controls.json` for recompile. Rig, mesh, z-order, missing-asset, deform, linked-mesh, and path-constraint issues block until the underlying compiler/art problem is fixed.

Generated proof outputs go under `generated/`, which is ignored by git.

## Validation Gates

A package should not be called ready unless these pass:

- `validation_report.json` has `status: "ok"`.
- `loop_validation_status` is `ok` for loop/settle endpoint checks.
- Atlas references resolve to packed regions.
- Optional feature plans pass their policy validators.
- `preview.html` loads in the Spine Web Player.
- `spine_editor_handoff.zip` exists for artist handoff and contains `shared_symbols.json`, `shared_symbols.atlas`, `shared_symbols.png`, unpacked `editor_images/`, `CREATE_SPINE_PROJECT.ps1`, `README_FOR_SPINE_EDITOR.md`, and `audit_manifest.json`.
- For production export review, `production_export_gate_report.json` is clean and the gate ran the browser runtime probe.

Native `.spine` creation is separate from production export. It invokes Spine CLI only when explicitly requested and never writes to Perforce or source art.

Weighted mesh automation is opt-in and review-required. Use `--report-mesh-candidates` to write `mesh_candidate_report.json` without changing output, `--auto-mesh-plan` to generate a conservative draft `auto_mesh_plan.json`, and `--auto-bind-weights` to emit first-pass weighted vertices. Reviewed `--mesh-plan` files override automatic drafts, and generated weights are not Spine Auto parity or final weight painting.

## Dependencies

The Python scripts use the standard library plus Pillow for image handling. Some scripts auto-install Pillow if missing. Browser runtime proof uses Node.js plus Playwright through `npx -p playwright`.

Recommended environment:

- Python 3.10+
- Node.js 20+
- PowerShell 7 on Windows
- Internet access for `npx -p playwright` and Spine Player CDN preview

## GitHub / Marketplace Notes

This repository is structured as a standalone Claude plugin repo. To publish through the H5G marketplace, add it to `michaelericksonh5/claude-plugins/.claude-plugin/marketplace.json` as a GitHub-sourced plugin:

```json
{
  "name": "spine-slot-animation",
  "description": "Generate validated Spine 4.3 proof packages for slot-game symbols, UI/system elements, and avatar state rigs.",
  "version": "0.1.4",
  "source": {
    "source": "github",
    "repo": "michaelericksonh5/Claude_Spine_Generator"
  },
  "category": "creative",
  "tags": ["spine", "slot-machine", "animation", "game-art", "validation"]
}
```

Before publishing, run:

```powershell
python scripts/run_local_evals.py
python scripts/build_runtime_acceptance_fixtures.py
npx -p playwright node scripts/runtime_acceptance_probe.mjs --packages-root generated/runtime_acceptance/packages
claude plugin validate .
```

## Current Status

The current local suite covers the promoted feature gates and loop validation. The browser runtime proof covers representative HP symbol, avatar state, and winframe packages. See:

- `references/capability_status.md`
- `references/validation.md`
- `references/spine_cli.md`
- `references/h5g_corpus_bakeoff_usage.md`
- `references/h5g_corpus_distilled_knowledge.md`
- `references/visual_remediation.md`
- `references/autonomous_rigging_research.md`
- `references/rig_proposal.md`
- `loop.md`
- `assets/eval_coverage_report.json`
