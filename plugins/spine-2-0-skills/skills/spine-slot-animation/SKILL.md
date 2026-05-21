---
name: spine-slot-animation
description: Route slot-game Spine 4.3 animation work to deterministic compile, diagnose, validate, handoff, rig-review, or visual remediation workflows. Use for slot symbols, PSD or PNG layers, shared_symbols packages, Spine Player errors, H5G recipe families, or bounded notes like more bouncy and less flashy.
when_to_use: Use as the default entrypoint for H5G slot animation requests, especially when the user mentions HP LP MP JP WD SC BO SF WYS symbols, Spine 4.3.04, spine-player, PSD-to-Spine, shared_symbols.json, shared_symbols.atlas, preview failures, or rigging readiness.
---

# Spine Slot Animation

This is the router skill for the progressive Spine plugin fork. It chooses the workflow and points Claude to the smallest required reference or helper skill.

## Core Rule

```text
AI proposes context, classification, recipe choice, layer-role mapping, and bounded controls. Deterministic tooling owns JSON generation, atlas packing, preview generation, and validation.
```

Never freehand `shared_symbols.json`, atlas metadata, raw timeline keys, or native `.spine` project files. Route changes through controls JSON, plans, compiler scripts, validators, and preview evidence.

## Defaults

- Target Spine Editor `4.3.04` and Spine Player `4.3.1` unless a project explicitly pins another supported 4.x line.
- Import JSON with the same editor version recorded in `shared_symbols.json` `skeleton.spine`; use the resulting `.spine` project as the bridge to newer editors.
- Default output uses array-form 4.x skins, root bone `root`, FPS 24, straight alpha atlas pages, normal slot blend mode, and no unreviewed advanced features.
- `v10_linear` and 3.8 output are legacy proof paths only. The portable builder rejects them.

## Route The Request

| User intent | Use | Required references |
|---|---|---|
| Natural-language revision note | Emit bounded controls only | `references/controls.md`, `assets/recipe_controls_schema.json` |
| PNG or PSD-export layers to package | Invoke `/spine-2-0-skills:compile-spine-package` | `references/compilers.md`, `references/intake.md` |
| Broken preview, import, or runtime issue | Invoke `/spine-2-0-skills:diagnose-spine-package` | `references/pitfalls.md`, `references/spine_43_contract.md` |
| Is this package ready? | Invoke `/spine-2-0-skills:validate-spine-package` | `references/validation.md`, `assets/eval_coverage_report.json` |
| Send to Chris / create `.spine` | Invoke `/spine-2-0-skills:package-spine-handoff` | `references/spine_cli.md`, `references/compilers.md` |
| Autonomous rigging, meshes, weights, avatars | Invoke `/spine-2-0-skills:review-spine-rigging` | `references/rig_proposal.md`, `references/autonomous_rigging_research.md` |
| Preview looks wrong | Use visual remediation | `references/visual_remediation.md`, `scripts/visual_remediation_loop.py` |

Ask one short clarifying question only when the input path, workflow, or family is genuinely ambiguous.

## Recipe Families

Supported routing families: `hp_symbol`, `mp_symbol`, `lp_symbol`, `wild_symbol`, `scatter_symbol`, `bonus_symbol`, `bo_special_symbol`, `jackpot_symbol`, `special_feature_symbol`, `value_symbol`, `winframe_explode`, `meter`, `transition`, `celebration`, and `avatar`.

Review-gated families: `blocker_or_bonus_symbol`, `non_symbol_or_unknown`.

Classify from filename/layer prefix, role map, and composition. Never classify by visual style alone. Use `scripts/classify_family.py` and `references/families.md` when unsure.

## Bounded Revision Output

For notes such as "more bouncy", "less flashy", "slower idle", or "stronger land", output one JSON object matching `assets/recipe_controls_schema.json`. No prose, no markdown fence, no raw Spine JSON, no keyframes.

```json
{
  "recipe_type": "hp_symbol",
  "bounce_strength": 1.0,
  "land_duration_scale": 1.0,
  "idle_duration_scale": 1.0,
  "glow_intensity": 1.0,
  "sparkle_intensity": 1.0,
  "premium_intensity": 1.0,
  "motion_strength": 1.0,
  "feature_active_intensity": 1.0
}
```

Omit unchanged fields. Keep values moderate unless the user asks for a strong change.

## Non-Negotiables

- Do not write to source-art directories or Perforce.
- Do not silently open or copy PSD/PSB files outside the documented intake workflow.
- Do not claim production-ready mesh, IK, deform, clipping, events, physics, export, or final art approval from a proof package.
- Do not hide mesh tearing, missing attachments, wrong z-order, deform needs, linked mesh needs, or path-constraint needs behind cosmetic controls.
- Do not make Chris depend on the full H5G research workspace. Prefer portable scripts, G-drive report pack evidence, or bundled snapshots as documented.

## Capability Truth

Before saying the system "can rig" or "fully understands" a case, read `references/capability_status.md` and `assets/compiler_evidence_index.json`. The system is a deterministic proof and review pipeline, not a fully autonomous production rigger.

Preserved capability anchors:

- Mesh automation includes `--auto-mesh-plan` and topology-aware `--auto-bind-weights`, but generated plans/weights remain review-required.
- Autonomous rigging is report-only proposal support; it cannot approve production topology, final weights, `.skel` export, or final art.
- H5G corpus guidance uses `scripts/resolve_h5g_corpus_bakeoff.py`, the read-only `G:/artSource/_spineResources/H5G_Corpus_Bakeoff` report pack, or bundled advisory snapshots.
- Spine CLI import/info support writes `spine_project_report.json`; export, clean, pack, unpack, advanced flags, license activation, Perforce, and source-art writes remain policy-gated or unsupported.

## Additional Resources

- `references/progressive_skill_capability_crosswalk.md` maps old monolithic sections to this hub-and-spoke fork.
- `references/validation.md` defines readiness gates.
- `references/boundaries.md` defines refusal and safety boundaries.
- `references/spine_43_contract.md` defines the current JSON/import contract.
- `SPINE_43_READINESS_AUDIT.md` records the 4.3 readiness audit inherited from the source plugin.
