# Progressive Skill Capability Crosswalk

This document maps the original `spine-slot-animation` monolithic skill to the progressive hub-and-spoke fork. It exists to prevent capability loss while keeping each `SKILL.md` concise.

## Source Skill

Source plugin: `spine-slot-animation` v0.1.4
Fork plugin: `spine-2-0-skills` v2.0.1

The deterministic runtime layer is intentionally unchanged:

- `scripts/`
- `assets/`
- `references/`
- `evals/`
- `tests/`

Only the skill routing layer is split.

## Workflow Mapping

| Original monolith area | Progressive location | Notes |
|---|---|---|
| Frontmatter triggers | `skills/spine-slot-animation/SKILL.md` | Shorter description plus `when_to_use`; helper skills are manual-only. |
| Core rule | `skills/spine-slot-animation/SKILL.md` | Preserved verbatim in intent: AI proposes; deterministic tools compile and validate. |
| Defaults | `skills/spine-slot-animation/SKILL.md` | Spine Editor `4.3.04`, Spine Player `4.3.1`, array skins, root bone, straight alpha atlas. |
| 15 recipe families | `skills/spine-slot-animation/SKILL.md`; details in `references/families.md` | Router keeps family list and classifier direction. |
| Workflow A: revision notes | `skills/spine-slot-animation/SKILL.md` | Bounded controls stay in the hub because this is low-side-effect JSON output. |
| Workflow B: PNGs to first package | `skills/compile-spine-package/SKILL.md` | Uses `scripts/build_spine_package.py`; preserves `--build-preview` and `--spine-editor-zip`. |
| Workflow C: PSD intake | `skills/compile-spine-package/SKILL.md`; details in `references/intake.md` | PSDs still require documented manifest/layer export before compile. |
| Workflow D: diagnose/fix | `skills/diagnose-spine-package/SKILL.md` | Uses `references/pitfalls.md`, `references/spine_43_contract.md`, and validation reports. |
| Workflow E: autonomous rigging review | `skills/review-spine-rigging/SKILL.md` | Report-only rig proposals remain non-compiling and review-required. |
| Workflow F: visual remediation | `skills/spine-slot-animation/SKILL.md`; details in `references/visual_remediation.md` | Router directs to `scripts/visual_remediation_loop.py`; structural findings still block. |
| Non-negotiables | `skills/spine-slot-animation/SKILL.md`; helper blocking sections; `references/boundaries.md` | No source-art writes, no Perforce writes, no freehand JSON, no production overclaims. |
| Capability status | `skills/spine-slot-animation/SKILL.md`; `skills/review-spine-rigging/SKILL.md`; `references/capability_status.md` | The fork preserves proof vs production boundaries. |
| Quality gates | `skills/validate-spine-package/SKILL.md` | Validation is manual-only so readiness claims are deliberate. |
| Handoff ZIP and `.spine` creation | `skills/package-spine-handoff/SKILL.md` | Official Spine CLI import only; no hand-authored `.spine`. |

## Feature Coverage Mapping

| Feature / claim area | Progressive location | Guardrail |
|---|---|---|
| `v10_linear` legacy proof output | `skills/spine-slot-animation/SKILL.md`; `references/controls.md`; `references/spine_42_contract.md` | Legacy only; portable builder rejects it. |
| `spine_43_bezier` | `skills/compile-spine-package/SKILL.md`; `references/controls.md`; `scripts/bezier_curves.py` | Opt-in numeric timelines only; not global Bezier coverage. |
| Sequence attachments | `skills/compile-spine-package/SKILL.md`; `references/capability_status.md`; `scripts/sequence_attachments.py` | Opt-in `--enable-sequences`. |
| Mesh attachments | `skills/compile-spine-package/SKILL.md`; `skills/review-spine-rigging/SKILL.md`; `references/meshes_and_deform.md` | Reviewed `--mesh-plan` or review-required auto plan. |
| First-pass weighted meshes | `skills/review-spine-rigging/SKILL.md`; `scripts/compare_mesh_weight_parity.py`; `scripts/auto_bind_weights.py` | Not final weight painting or Spine Auto parity. |
| Multi-skin region variants | `skills/compile-spine-package/SKILL.md`; `assets/skin_plan_schema.json` | Region variants only; linked mesh variants remain unimplemented. |
| IK and transform constraints | `skills/compile-spine-package/SKILL.md`; `references/constraints.md` | Opt-in and review-required. |
| Clipping | `skills/compile-spine-package/SKILL.md`; `references/clipping.md` | Plan required; CPU/review gate remains. |
| Events | `skills/compile-spine-package/SKILL.md`; `references/events.md` | Event data only; runtime listeners are game-team owned. |
| Physics | `skills/compile-spine-package/SKILL.md`; `references/physics.md`; `assets/physics_policy.json` | Opt-in with policy, preview, and animator review. |
| Expression atlas variants | `skills/compile-spine-package/SKILL.md`; `references/vision_bridge.md` | Opt-in `--composite-expressions`; visual review still required. |
| H5G corpus/bakeoff evidence | `skills/spine-slot-animation/SKILL.md`; `references/h5g_corpus_bakeoff_usage.md`; `scripts/resolve_h5g_corpus_bakeoff.py` | Full workspace optional; G-drive report pack or bundled snapshot allowed as documented. |
| Visual remediation | `skills/spine-slot-animation/SKILL.md`; `references/visual_remediation.md`; `scripts/visual_remediation_loop.py` | Safe findings become controls; rig/compiler/art findings block. |
| Production export gate | `skills/validate-spine-package/SKILL.md`; `scripts/production_export_gate.py`; `assets/production_export_policy.json` | Non-exporting gate only; no `.skel`, license automation, Perforce, or source-art writes. |
| Avatar runtime contracts | `skills/review-spine-rigging/SKILL.md`; `scripts/validate_avatar_runtime_contract.py`; `assets/avatar_runtime_contract_schema.json` | Runtime ownership must be externally verified. |
| Mesh/weight parity fixtures | `skills/review-spine-rigging/SKILL.md`; `scripts/compare_mesh_weight_parity.py`; `assets/mesh_weight_parity_fixture_schema.json` | Review evidence, not automatic production approval. |

## Helper Skill Invocation Policy

Only `skills/spine-slot-animation/SKILL.md` is model-invoked by default. The following helpers are manual-only through `disable-model-invocation: true`:

- `compile-spine-package`
- `diagnose-spine-package`
- `validate-spine-package`
- `package-spine-handoff`
- `review-spine-rigging`

This prevents accidental compile, packaging, validation, or handoff actions while still making the workflows available when explicitly invoked.

## Capability Preservation Checklist

Before publishing this fork, verify:

- Every old workflow A-F maps to a hub/helper skill above.
- Every helper points to existing `scripts/`, `assets/`, and `references/` paths.
- No helper allows freehand final Spine JSON.
- No helper claims production rigging, final weights, deform, linked meshes, production export, runtime avatar ownership, or final art approval.
- `python scripts/run_local_evals.py` still passes.
- `claude plugin validate .` still passes.
