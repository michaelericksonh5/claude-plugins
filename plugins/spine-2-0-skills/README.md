# Spine 2.0 Skills

Progressive-disclosure Spine 4.3 skill suite of `spine-slot-animation` for generating and reviewing validated Spine 4.3 proof packages for slot-game symbols, UI/system elements, and avatar state rigs.

Spine 2.0 Skills preserves the deterministic compiler/runtime layer from `spine-slot-animation` v0.1.4 and restructures only the Claude skill layer:

```text
AI proposes context. Deterministic tooling compiles. Validators and previews prove or reject.
```

## What Changed

The original plugin used one large skill. This fork keeps one auto-invoked router skill and adds manual helper skills for high-friction workflows:

| Skill | Invocation | Purpose |
|---|---|---|
| `spine-slot-animation` | Automatic or manual | Router/orchestrator for slot Spine work |
| `compile-spine-package` | Manual only | Build or regenerate 4.3 proof packages |
| `diagnose-spine-package` | Manual only | Diagnose preview, import, or runtime failures |
| `validate-spine-package` | Manual only | Run readiness gates and runtime proof checks |
| `package-spine-handoff` | Manual only | Create handoff ZIPs and optional `.spine` projects |
| `review-spine-rigging` | Manual only | Review rigging, mesh, weight, avatar, and production-boundary evidence |

Manual helpers use `disable-model-invocation: true` so Claude does not accidentally trigger side-effect workflows.

## Plugin Structure

```text
Claude_Spine_Generator_Progressive/
  .claude-plugin/plugin.json
  skills/
    spine-slot-animation/SKILL.md
    compile-spine-package/SKILL.md
    diagnose-spine-package/SKILL.md
    validate-spine-package/SKILL.md
    package-spine-handoff/SKILL.md
    review-spine-rigging/SKILL.md
  assets/
  evals/
  references/
  scripts/
  tests/
```

## Current Defaults

- Spine Editor target: `4.3.04`
- Spine Player target: `4.3.1`
- Portable builder: `scripts/build_spine_package.py`
- Handoff path: `spine_editor_handoff.zip` plus `CREATE_SPINE_PROJECT.ps1`
- Native `.spine`: official Spine CLI import only

Do not fix import errors by changing `skeleton.spine` alone. Import with the same editor version recorded in the JSON, then use the `.spine` project as the bridge.

## Quick Compile

```powershell
python scripts/build_spine_package.py `
  --layer-dir <folder-of-png-layers> `
  --family hp_symbol `
  --rank 3 `
  --doc-width 178 `
  --doc-height 178 `
  --out-dir <output-dir> `
  --build-preview `
  --spine-editor-zip
```

Add `--create-spine-project --spine-cli "C:\Program Files\Spine\Spine.com"` only when Spine CLI is installed and native `.spine` creation is explicitly requested.

## Validation

Before calling a package ready, check:

- `validation_report.json` status is `ok`.
- Loop/settle validation is clean.
- Preview validation and/or browser runtime proof is clean when claimed.
- JSON `skeleton.spine` matches the CLI/editor import version.
- Handoff ZIP contains JSON, atlas, PNG, `editor_images/`, `CREATE_SPINE_PROJECT.ps1`, README, and audit manifest.

Run local regression coverage:

```powershell
python scripts/run_local_evals.py
claude plugin validate .
```

Runtime proof, when required:

```powershell
python scripts/build_runtime_acceptance_fixtures.py
npx -p playwright node scripts/runtime_acceptance_probe.mjs --packages-root generated/runtime_acceptance/packages
```

## Capability Boundaries

This is not a push-button replacement for a Spine animator/rigger. Production export, final weight painting, deform timelines, linked meshes, broad background/UI ambience, persistent avatar runtime state, Perforce submission, and final art approval remain gated.

See `references/progressive_skill_capability_crosswalk.md`, `references/capability_status.md`, and `SPINE_43_READINESS_AUDIT.md`.

## Marketplace Entry

Publish as a separate plugin, not a replacement for the original:

```json
{
  "name": "spine-2-0-skills",
  "description": "Progressive Claude skill fork for validated Spine 4.3 slot-animation proof packages with manual compile, diagnose, validate, handoff, and rig-review workflows.",
  "version": "2.0.1",
  "source": {
    "source": "github",
    "repo": "michaelericksonh5/Claude_Spine_Generator_Progressive"
  },
  "category": "creative",
  "tags": ["spine", "slot-machine", "animation", "game-art", "validation", "claude-skills"]
}
```
