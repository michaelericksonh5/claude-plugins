# Full Automation Buildout Plan

This plan turns the current honest capability matrix into implementation phases. It follows the skill rule: Claude classifies and chooses intent; deterministic scripts emit Spine data; validators and preview prove the package.

## Skill Architecture Requirements

The skill should stay discoverable and lean:

- `SKILL.md` keeps trigger phrases, workflows, hard boundaries, and links.
- `references/` holds detailed Spine contracts, feature policies, and implementation notes.
- `scripts/` owns deterministic generation and validation.
- `assets/` holds schemas and reusable fixtures.
- Every new feature gets an eval before it is described as supported.

Do not put every Spine feature explanation into `SKILL.md`. Put only the routing rule there, then link to the relevant reference.

## Phase 1: Wire Existing Helpers Into Compiler

### 1. Sequence Attachment Emission

Status: implemented as opt-in `--enable-sequences`.

What it does:

- Detects numbered VFX groups such as `sparkle_001.png` through `sparkle_012.png`.
- Collapses those layers to one Spine 4.2 Sequence attachment.
- Packs every numbered frame into the atlas as `parts/sparkle_001`, `parts/sparkle_002`, etc.
- Adds a slot `sequence` timeline on win-like animations.

Validation:

- The attachment has a `sequence` block using the 4.2 `setup` field.
- All expected sequence frame atlas regions exist.
- Slot timeline name `sequence` is accepted by the validator.

Remaining:

- Add a file-backed eval fixture with real PNG frames.
- Add controls for mode (`once`, `loop`, `pingpong`) and duration.

### 2. Physics Candidate Autonomy

Status: opt-in `--enable-physics` exists.

Buildout:

- Expand detection from capes/hair/tails/dangles to dresses, skirts, sleeves, ribbons, flags, cloth panels, beards, mustaches, and loose accessories.
- Add a `physics_policy.json` input so projects can decide whether physics is default-on for specific roles.
- Validate zero-length bones and warn when a physics constraint affects a setup bone with no useful length.

Validation:

- Candidate report in `validation_report.json`.
- Runtime preview with physics enabled in the target Spine 4.3 player.
- Performance budget: cap default auto-physics to a small number of constraints per symbol unless user opts in.

### 3. Expression Atlas Variants

Status: overlay polarity and optional expression compositing exist.

Buildout:

- Promote composited expression heads from side output to actual package attachments.
- Replace separate overlay slots with head attachment swaps when `--composite-expressions` is enabled.
- Support common face states: neutral, blink, smile, laugh, open mouth, closed mouth, side-eye.

Validation:

- Setup pose shows only the neutral face.
- Blink/laugh/smile attachments are hidden until keyed.
- Preview comparison confirms no alpha-matte seam.

## Phase 2: Add New Compiler Contracts

### 4. Mesh Attachment Emission

Status: reviewed opt-in supported with `--mesh-plan`; automatic candidate reporting and draft mesh plans are review-gated behind `--report-mesh-candidates` and `--auto-mesh-plan`.

Buildout:

- Add a mesh plan schema: source layer, hull vertices, optional interior vertices, triangles, hull count, and target slot.
- Add `--mesh-plan <mesh_plan.json>` to the builder.
- Emit `type: "mesh"` attachments only for planned layers.
- Keep region output as the default for all unplanned layers.

Required validation:

- `uvs`, `vertices`, `triangles`, and `hull` are present and consistent.
- Triangle indices are in range.
- Hull has at least three vertices and no self-intersection.
- Atlas path exists.
- Vertex count stays below project budget.

Do not auto-mesh every character body. Mesh only when a plan or policy marks the layer as a mesh candidate.

### 5. Weighted Mesh Emission

Status: reviewed opt-in supported with `--auto-bind-weights`; automatic weights are first-pass review artifacts, not Spine Auto parity or final weight painting.

Buildout:

- Extend mesh plan to list influencing bones.
- Use `auto_bind_weights.py` to produce first-pass weighted vertex arrays.
- Add `--auto-bind-weights` as a reviewed opt-in.
- Emit weighted mesh `vertices` format only when the mesh plan has bound bones.

Required validation:

- Every weighted vertex has at least one bone influence.
- Bone indices exist and weights sum to 1.0 per vertex.
- Bones-per-vertex does not exceed the configured budget.
- Report vertex-transform cost estimate.

Final weight painting remains an artist review step until a visual deformation test is approved.

### 6. Multi-Skin Variant Emission

Status: implemented as opt-in `--skin-plan` for reviewed region variants. Linked mesh variants remain unimplemented.

Buildout:

- Add a variant skin plan schema:
  - skin name
  - slot attachment key
  - actual attachment path
  - optional skin bones
  - optional skin constraints
- Emit `skins` as an array containing `default` plus named variant skins.
- Pack alternate variant PNGs into the atlas and expose skins in preview HTML.
- Support linked mesh variants only after mesh emission is stable.

Required validation:

- Every skin attachment key resolves under the same slot.
- Default skin still contains shared attachments.
- Non-default skins do not reference missing atlas regions.
- Skin-specific bones/constraints are present only in skins that use them.
- Preview HTML configures the Spine Player skin list; interactive skin switching and browser playback still require separate runtime review.

### 7. Bezier Curve Emission

Status: implemented as opt-in `spine_43_bezier` coverage for supported numeric timelines only; `spine_42_bezier` remains a legacy alias.

Buildout:

- Keep `v10_linear` strictly linear.
- Added a separate modern 4.3 curve policy, not a loose controls flag.
- Added curve presets `ease_in`, `ease_out`, `ease_in_out`, `overshoot`, and `settle`.
- Apply curves only to timelines covered by policy: bone translate, rotate, scale, and slot rgba/alpha where present. Attachment, sequence, animation-level events, and draw-order timelines stay curve-free; constraint mixes and sequence timing are not covered.

Required validation:

- Curve format matches current Spine 4.x JSON.
- No Bezier curves appear in `v10_linear` output.
- Curves are bounded and do not change animation duration.
- Preview confirms loop endpoints still close cleanly.

## Phase 3: Broaden Asset Understanding

### 8. UI, Frame, And Background Ambience

Status: partially covered by `meter`, `transition`, `celebration`, and `winframe_explode`.

Buildout:

- Add ambient recipes for:
  - symbol frame idle glow
  - frame win burst
  - UI button hover/press/idle
  - meter idle/collect/fill
  - background parallax/drift
  - foreground overlay shimmer
- Separate symbol-local motion from screen-space UI motion.
- Add role-specific amplitude profiles so a background drift never gets symbol bounce and a symbol frame never gets full-screen transition motion.

Required validation:

- Animation names match family contract.
- Ambient loops close.
- Background/UI animations do not move reel-symbol anchors unless explicitly planned.
- Preview includes representative UI/background fixtures.

### 9. Character Wardrobe And Secondary Motion Semantics

Status: partial via physics presets and name heuristics.

Buildout:

- Expand layer semantics for hair, beard, mustache, dress, skirt, sleeve, cloak, cape, robe, scarf, ribbon, belt, chain, necklace, earring, tail, wing.
- Add parent and pivot hints for each role.
- Decide per role: FK only, physics candidate, mesh candidate, or weighted mesh candidate.

Required validation:

- Layer interpretation explains why each wardrobe piece was classified.
- Physics candidates are reported before emission.
- Mesh candidates do not silently become meshes without a mesh plan.

## Phase 4: Production Handoff

### 10. Spine CLI Export And Runtime Acceptance

Status: representative browser runtime preview proof is implemented for advanced HP symbol, avatar state, and supported UI/frame packages. The production export gate is implemented as a blocking non-exporting check that must run the browser runtime probe before trusting browser evidence; report-only, static, manual, and self-attested browser evidence files remain blocked. Spine CLI export, `.skel` conversion, license activation, Perforce automation, and source-art writes remain not implemented.

Buildout:

- Added project-level policy for approved Spine Editor/CLI/runtime versions.
- Added `scripts/production_export_gate.py` to validate approvals, package validation status, advanced-feature counts, approved browser-runtime probe provenance with package hashes, output-format decision, no Perforce/source-art writes, and approver metadata.
- Added `scripts/build_runtime_acceptance_fixtures.py` and `scripts/runtime_acceptance_probe.mjs` to compile representative preview packages, serve them over localhost, load `preview.html` in Chromium/Edge via Playwright, and write screenshot-backed runtime evidence.
- Add export scripts only after license/runtime approval explicitly authorizes CLI invocation.
- Add target-runtime smoke tests for Web Player and whichever game runtime is used before allowing production export automation.

Required validation:

- Runtime major.minor matches export major.minor.
- JSON or binary output loads in target runtime.
- Physics, skins, blend modes, sequences, and events behave in runtime, not just in static JSON.
- Gate report keeps `export_invoked=false` and `cli_invocation_allowed=false` under the bundled policy; a clean result is `ready_for_manual_export` with `runtime_acceptance_status: "verified_browser_runtime"` only when the gate executes the runtime probe for the current package.

### 11. Persistent Avatar Game State

Status: Spine data can represent state-frame animations; game state belongs to runtime code.

Buildout:

- Emit an avatar state manifest for game code: states, transitions, awarded beats, close beats, event names.
- Do not claim persistent state until the game runtime consumes that manifest.

## Eval Expansion

Add evals before moving status from helper-only to supported or from reviewed opt-in to default:

- `eval-17-sequence-auto-emission`
- `eval-18-mesh-plan-emission`
- `eval-19-auto-bind-weighted-mesh`
- `eval-20-multi-skin-variants`
- `eval-21-bezier-modern-profile`
- `eval-22-ui-frame-ambient-loop`
- `eval-23-background-parallax-ambient`
- `eval-24-character-wardrobe-physics`
- `eval-25-expression-atlas-variants`
- `eval-26-avatar-state-manifest`
- `eval-28-production-export-gate`
- `eval-30-automatic-weighted-mesh`

Each eval needs:

- User-style prompt.
- Fixture inputs.
- Expected files.
- JSON contract checks.
- Preview/visual or runtime acceptance where relevant.
- A refusal/guard case where the skill must not overclaim.

## Completion Definition

The system is not "fully complete" until:

1. Each planned feature has deterministic compiler support.
2. Each feature has a schema or policy file.
3. Each feature has a validator.
4. Each feature has at least one positive eval and one guard eval.
5. The skill docs say exactly what is supported, opt-in, helper-only, and not implemented.
6. A representative package loads in the target Spine 4.3 runtime.
