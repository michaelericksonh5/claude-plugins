---
name: spine-slot-animation
description: >-
  Generate validated Spine 2D animations for slot-machine games — symbols
  (high-pay, medium-pay, low-pay, wild, scatter, bonus, jackpot, special
  feature, value), winframes, meters, transitions, celebrations, and avatars
  — from PSD layers, separated PNG parts, or natural-language revision notes.
  Use this skill whenever the user mentions slot symbols, slot animation,
  reel art, Spine 4.3 / Spine 4.3.04 / spine-player, idle/breathe/land/win
  loops, HP/LP/MP/JP/WD/SC/BO/SF/WYS naming, PSD-to-Spine pipelines,
  shared_symbols.json / shared_symbols.atlas, or revision notes like "more
  bouncy", "less flashy", "slower idle", "stronger land". Use it even when
  the request is implicit — "animate this symbol", "rig these layers",
  "build a slot reel piece", "fix this 4.3 compatibility error",
  "the eyes show closed at rest", "the canvas is blank in Spine Player".
  The skill enforces one rule: AI proposes classification, layer roles,
  recipe choice, and bounded controls; deterministic tooling owns the
  Spine JSON, atlas, and validation. Never freehand raw Spine JSON.
---

# Spine Slot Animation

A skill for proposing and validating Spine 2D animations for slot-machine games. The skill routes 15 recipe families across symbols, UI, and avatars, defaults to Spine Editor 4.3.04 / Spine Player 4.3.1 with a 3.8 v10_linear fallback only for legacy H5G proof outputs, and shepherds work through a deterministic compile → preview → validate loop. It is portable and resolves H5G bakeoff/corpus evidence in this order: full local H5G research workspace, read-only G-drive consolidated report pack at `G:/artSource/_spineResources/H5G_Corpus_Bakeoff`, then the bundled distilled snapshot. It is not a claim of fully autonomous production rigging for every possible asset; use [references/capability_status.md](../../references/capability_status.md) before answering completeness questions.

## Core rule

```text
AI proposes context, classification, recipe choice, layer-role mapping,
and bounded controls. Deterministic tooling owns JSON generation, atlas
packing, preview generation, and validation.
```

Never freehand `shared_symbols.json`, atlas metadata, or raw timeline keyframes in chat. Every Spine package must come from a compiler that the validators cover. If the user asks for "just edit the JSON", redirect them to controls JSON + a recompile.

## Quick orientation

The skill answers four shapes of request. Identify which one applies, then jump to the right section.

| Shape | What the user has | What they want | Go to |
|---|---|---|---|
| **A. Direction-only** | An existing rig + a revision note | Update without re-rigging | [Workflow A](#workflow-a-revision-notes--bounded-controls) |
| **B. New rig from PNGs** | Per-layer PNG exports | A first-pass Spine package | [Workflow B](#workflow-b-pngs--first-pass-spine-package) |
| **C. New rig from PSD** | A Photoshop `.psd` source | A first-pass Spine package | [Workflow C](#workflow-c-psd--first-pass-spine-package) |
| **D. Diagnose / fix** | A broken package or error | A correct fix on the current 4.3 contract | [Workflow D](#workflow-d-diagnose--fix) |
| **E. Autonomous rigging review** | Interpreted layers or corpus evidence | Auditable region/mesh proposal and missing gates | [Workflow E](#workflow-e-autonomous-rigging-review) |
| **F. Visual remediation** | A compiled package + preview | Preview, diagnose, fix, and recompile | [Workflow F](#workflow-f-visual-remediation-loop) |

Don't guess which shape applies. Ask one short clarifying question if it isn't obvious. The user will tell you what they have in hand.

## Defaults

- **Spine version target:** Spine Editor 4.3.04 and Spine Player 4.3.1 by default. Use `--target-spine-version` only when a project intentionally needs a different supported 4.x editor line.
- **Editor import rule:** do not fix import errors by editing `skeleton.spine` alone. Spine JSON must be imported with the same editor version recorded in `skeleton.spine`; project files are the safe bridge to newer editors.
- **3.8 fallback profile:** `v10_linear` only when invoking the legacy H5G proof compiler. The portable builder rejects it; omit `export_profile` for the current 4.3 default path. See [references/spine_43_contract.md](../../references/spine_43_contract.md).
- **FPS:** 24.
- **Atlas:** straight alpha (non-premultiplied). Player config: `premultipliedAlpha: false`. Alpha-trimmed, RGB-bleed transparent pixels, 1-px edge extrusion.
- **Blend modes:** every slot compiles as `normal`. Non-normal blends are stripped at compile time. See [references/pitfalls.md](../../references/pitfalls.md#blend-modes-are-stripped).
- **Root bone:** always named `"root"`.
- **Skins:** always emitted as an array of skin objects (4.x form), never as a 3.8 object.
- **Spine CLI:** understand the official command families, but only automate the approved import/info path. See [references/spine_cli.md](../../references/spine_cli.md).

## The 15 recipe families

The skill chooses one of 15 implementable families. Two more are review-gated and must be triaged by a human.

```
hp_symbol      lp_symbol      mp_symbol      wild_symbol      scatter_symbol
bonus_symbol   bo_special_symbol               jackpot_symbol  special_feature_symbol
value_symbol   winframe_explode               meter            transition
celebration    avatar
                                review-gated: blocker_or_bonus_symbol, non_symbol_or_unknown
```

For naming, source-layer contract, generated animations, and controls per family, read [references/families.md](../../references/families.md). Use the bundled classifier `scripts/classify_family.py` to propose a family from layer names — it returns the family key, confidence, and the evidence that drove the decision.

Three signals together identify a family: filename / layer-name prefix, role map (when an H5G role map is available), and layer composition. **Never classify by visual style alone.** A premium-looking King card is still `lp_symbol` if the role map says low-pay.

## Workflow A: revision notes → bounded controls

**Trigger:** the user has a rig (or a recipe family in mind) and a note like "more bouncy", "less flashy", "faster idle", "stronger land".

**Output contract:** one JSON object matching the bounded controls schema. No prose, no markdown fences, no raw Spine JSON, no keyframes.

The schema lives at [assets/recipe_controls_schema.json](../../assets/recipe_controls_schema.json). For the natural-language → controls mapping, read [references/controls.md](../../references/controls.md).

Skeleton response (replace with mapped values; omit fields you aren't changing):

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

All numeric fields default to `1.0` and are optional. Unknown fields fail compilation by design — the schema is closed. Stay moderate; values near 1.0 unless the user asks for a strong change.

After emitting controls JSON, point the user to the compile command that consumes it. See [references/compilers.md](../../references/compilers.md#applying-controls).

## Workflow B: PNGs → first-pass Spine package

**Trigger:** the user has separated transparent PNG parts in a folder.

**Default path: the bundled portable pipeline.** Run the end-to-end driver:

```
python scripts/build_spine_package.py \
    --layer-dir <folder of PNGs> \
    --family <recipe family> --rank <N> \
    --doc-width <PSD doc width> --doc-height <PSD doc height> \
    --controls <controls.json> \
    --out-dir <output_dir> \
    --build-preview \
    --spine-editor-zip
```

If the current machine has Spine installed and the user wants a native project file immediately, add:

```
    --create-spine-project \
    --spine-cli "C:\Program Files\Spine\Spine.com"
```

The driver runs the four stages — interpret layers → build rig layout → compose animations → pack atlas → assemble + validate — and emits a complete package tagged for the configured Spine editor version. This works without the H5G research/ tree.

For weighted mesh review, stay explicit: `--report-mesh-candidates` only writes a deterministic report, `--auto-mesh-plan` writes and applies a conservative draft plan, and `--auto-bind-weights` emits first-pass review-required weights. Reviewed `--mesh-plan` files override automatic drafts. Never describe these weights as Spine Auto parity or final weight painting.

For animator handoff, deliver `<output_dir>/spine_editor_handoff.zip`, not loose files selected by hand. Chris does not import the ZIP directly; he unzips it and runs `CREATE_SPINE_PROJECT.ps1` to create the native `.spine` file through his installed Spine CLI. The script imports with the version recorded in `shared_symbols.json` `skeleton.spine`, and refuses mismatches. Manual **File -> Import Data...** only works when Chris opens the same Spine version recorded in the JSON. The ZIP contains `shared_symbols.json`, `shared_symbols.atlas`, `shared_symbols.png`, unpacked `editor_images/`, `CREATE_SPINE_PROJECT.ps1`, an import README, and an audit manifest. If the atlas PNG is missing, the ZIP step fails instead of shipping a broken package.

**Alternative path: H5G compilers** (when working inside the H5G tree, or when you specifically need the legacy 3.8 v10_linear profile for a proof package):

- **Proof compiler** (`hp_symbol_proof_compiler.py`): single body PNG + recipe key → single-bone skeleton with v10_linear timelines. Use for legacy proof packages.
- **Layered rig compiler** (`layered_rig_compiler.py`): separated per-layer PNGs → multi-bone skeleton. Same conceptual output as the portable pipeline, with H5G-specific motion profile fitting from real-world exports.

Choose the portable pipeline by default. Use the H5G compilers when the user explicitly requests 3.8 v10_linear output, or when integrating with the H5G research/ tree's fitted motion profiles. Commands and flags for both are in [references/compilers.md](../../references/compilers.md). Required validations are in [references/validation.md](../../references/validation.md). Common per-layer naming pitfalls are in [references/intake.md](../../references/intake.md).

## Workflow C: PSD → first-pass Spine package

**Trigger:** the user has a Photoshop `.psd` file.

Two intake paths, both producing the same downstream contract (`h5g_layer_manifest.json` + per-layer PNGs):

- **PSD-native intake** (preferred): read the `.psd` directly via `psd-tools`. Best when build machine can reach the PSD.
- **Photoshop JSX export**: run an ExtendScript inside Photoshop that walks the layer tree. Use when `.psd` lives on a network share unreachable from the build machine, when live effects / smart-object fidelity matters, or when the PSD has clipping masks `psd-tools` can't faithfully rasterise.

After intake, hand off to Workflow B with the emitted PNG layers. See [references/intake.md](../../references/intake.md) for the full layer-naming contract, boilerplate filtering, parent-local bone placement math, and overlay polarity (the eye-blink / mouth-O / hat-top problem).

**Do not silently open or copy PSDs outside the documented intake workflow.** PSDs can be hundreds of MB. Silent reads waste bandwidth and risk lockfile conflicts.

## Workflow D: diagnose / fix

**Trigger:** the user reports a broken preview, a blank canvas, a runtime error, an off-center rig, a permanently-visible eye-blink overlay, or a Spine compatibility error.

The full error → cause → fix table is in [references/pitfalls.md](../../references/pitfalls.md). The most frequent are:

- Blank canvas, no console error → `skins` emitted as 3.8 object form. Fix: emit array form.
- No rotation → rotate keys using `angle` instead of `value`. Fix: emit `value`.
- Eye-blink overlay shown at rest → overlay slot setup color not `ffffff00`. Fix: alpha-0 in setup, stepped-attachment timeline during the action.
- Console: `Cannot read properties of null (reading 'r')` → `rgba2` emitted without setup `dark` color. Fix: remove `rgba2` or add slot `dark`.
- Symbol off-center, very small → `skeleton.width/height` set to atlas page size. Fix: use the PSD document size.

For any Spine contract error, run the compiler validation and import-version checks first ([references/validation.md](../../references/validation.md)) to enumerate every contract violation before proposing a fix.

## Workflow E: autonomous rigging review

**Trigger:** the user asks whether the system can autonomously rig, asks for a rig proposal before compiling, or asks about production mesh/avatar rigging readiness.

Use `references/h5g_corpus_distilled_knowledge.md`, `assets/h5g_corpus_distilled_evidence.json`, `references/autonomous_rigging_research.md`, `references/rig_proposal.md`, and `assets/autonomous_rigging_evidence_index.json`. When layer interpretation exists, generate a report-only proposal:

```
python scripts/generate_rig_proposal.py \
    --family <recipe family> \
    --layer-interpretation <interpreted_layers.json> \
    --out generated/rig_proposals/<asset>.rig_proposal.json
```

This does not compile a Spine package. It only records confidence, review reasons, region decisions, mesh candidates, bundled evidence IDs, support status, and missing policy gates. It must continue to say the system is not a fully autonomous production rigger until Chris-approved mesh/weight parity fixtures, avatar runtime-state proof, target runtime acceptance, and production export policy gates are verified. Keep Genielabs as conceptual prior art only; do not copy PolyForm Noncommercial code or generic humanoid presets.

For mesh candidates, the follow-on parity gate is:

```
python scripts/compare_mesh_weight_parity.py \
    --approved <chris_approved_spine_export.json> \
    --candidate <candidate_shared_symbols.json> \
    --out generated/mesh_weight_parity/<fixture>.json
```

For avatar proposals, the follow-on runtime ownership gate is:

```
python scripts/validate_avatar_runtime_contract.py \
    --contract <avatar_runtime_contract.json> \
    --out generated/avatar_runtime_contracts/<avatar>.json
```

Passing these gates provides review evidence. It still does not replace Chris approval, target runtime proof, or production export policy approval.

## Workflow F: visual remediation loop

**Trigger:** the user asks to preview and fix issues, says the motion/rig "looks wrong", asks for Claude visual approval, or wants an iterative visual QA loop instead of a pass/fail report.

Claude should inspect the preview evidence and produce a structured visual review, not a vague opinion. Create the packet:

```
python scripts/visual_remediation_loop.py \
    --package-dir <compiled_package_dir> \
    --out-dir <review_dir> \
    --render-frames
```

Open `preview.html` and the generated frames. Record findings as `visual_review.json` using the issue codes in [references/visual_remediation.md](../../references/visual_remediation.md), then apply them:

```
python scripts/visual_remediation_loop.py \
    --review <visual_review.json> \
    --out-dir <review_dir>
```

If the report writes `visual_remediation.controls.json`, recompile with those bounded controls, rebuild the preview, and repeat. If the report is `blocked`, fix the named rig/compiler/source-art/mesh issue first. Do not hide mesh tearing, wrong z-order, missing attachments, expression polarity, deform needs, linked mesh needs, or path-constraint needs behind cosmetic controls.

This is AI visual QA remediation. It can reject bad previews and suggest deterministic fixes. It is still not final production art approval; Chris or an assigned art owner owns final signoff.

## Non-negotiables

The full list with the reasoning behind each item is in [references/boundaries.md](../../references/boundaries.md). The headlines:

- Do not write to source-art directories. Build outputs go to a separate tree.
- Do not auto-commit to version control / asset management. The art team reviews each handoff.
- Do not open or copy `.psd` / `.psb` files outside the documented intake workflow.
- Do not claim production-ready for mesh, IK, deform, clipping, events, or production export — these are all gated by separate review processes.
- Do not treat Claude visual QA as final art approval. Use the visual remediation loop to find and fix issues, then keep Chris/art-owner signoff as the final gate.
- Do not freehand raw Spine JSON. Generate it through a compiler the regression tests cover.
- Do not silently compile PSD/PSB source-layer manifest rows. They require human review.
- Do not make Chris's core workflow depend on the full H5G research workspace. Use `scripts/resolve_h5g_corpus_bakeoff.py` to detect the full research workspace or read-only `G:/artSource/_spineResources/H5G_Corpus_Bakeoff`; when the network report pack exists, read `H5G_CORPUS_BAKEOFF_CONSOLIDATED_REPORT.md` first, then `H5G_CORPUS_BAKEOFF_CONSOLIDATED_INDEX.json` and supporting raw reports as needed. Fall back to the bundled corpus snapshot for default guidance. Full bakeoff reruns are optional H5G-internal validation only.

## Capability status

Before telling a user the system "understands" or "can rig" an asset class, check [references/capability_status.md](../../references/capability_status.md) and `assets/compiler_evidence_index.json`. Do not promote a feature, family, role, or UI bucket to supported unless the compiler evidence index has matching queryable evidence for it. The current truth:

- Supported: recipe-family routing, natural-language bounded controls, PNG-layer first-pass rigs, standard shared-timeline symbol animations with deterministic loop/settle endpoint validation, evidence-backed UI/system proof templates for `meter`, `transition`, `celebration`, `winframe_explode`, and existing symbol frame/glow layers, avatar state-frame proof packages with an `avatar_state_manifest.json` sidecar, heuristic topology motion, opt-in IK/transform/clipping/events, opt-in policy-gated physics candidates/constraints with preview required, opt-in reviewed mesh attachment emission via `--mesh-plan`, opt-in automatic review-required mesh candidate/draft-plan generation via `--report-mesh-candidates --auto-mesh-plan`, opt-in first-pass weighted mesh binding via `--auto-bind-weights`, mesh/weight parity fixture comparison via `scripts/compare_mesh_weight_parity.py`, avatar runtime ownership validation via `scripts/validate_avatar_runtime_contract.py`, opt-in reviewed multi-skin region variants via `--skin-plan`, validation and preview loops, AI visual remediation through `scripts/visual_remediation_loop.py`, representative browser runtime proof through `scripts/build_runtime_acceptance_fixtures.py` + `scripts/runtime_acceptance_probe.mjs`, and a non-exporting production export approval gate that accepts only browser-runtime probe evidence.
- Helper-only/review-required: mesh hull tracing and setup-pose QA. Automatic mesh drafts and auto weights are useful review inputs, but they are not production weight painting, Spine Auto parity, or final rigger approval. Sequence attachments are now opt-in with `--enable-sequences`.
- Opt-in only: `spine_43_bezier` emits numeric 4.x Bezier arrays for supported bone `rotate` / `translate` / `scale` and slot `rgba` / `alpha` timelines. Attachment, sequence, animation-level events, and draw-order timelines stay curve-free. It is not global Bezier/path/deform feature coverage. Default 4.3 output stays curve-free; legacy `v10_linear` proof packages are separate from the portable builder.
- Review-only: button idle/hover/press, row blockers, broad background drift/parallax, foreground ambient overlays, generic `vfx_only`, and unknown UI/system buckets. These fail or report review-required instead of compiling a guessed template.
- Not implemented: production weight painting, deform timelines, linked meshes, skin-specific linked mesh variants, path-constraint emission, general background/UI ambience outside documented families, and production Spine CLI export. Browser runtime proof is representative preview acceptance only; it is not final production export or art approval. The production export gate does not invoke Spine CLI, convert `.skel`, activate licenses, write to Perforce, or write to source art.
- Autonomous rigging: report-only proposal support exists through `scripts/generate_rig_proposal.py`, `assets/rig_proposal_schema.json`, and `references/rig_proposal.md`. This is not production rigging and cannot approve mesh topology, final weights, deform keys, avatar runtime state, or `.skel` export.

Phase 11 promoted-feature eval coverage lives in `assets/eval_coverage_registry.json`; `scripts/run_local_evals.py` emits `assets/eval_coverage_report.json`. The local suite includes a registry integrity eval that fails when a promoted feature lacks positive/guard coverage or names a missing test; browser runtime proof is run manually with Playwright so unit evals do not require a browser.

If the user asks whether the system is complete front to back, the honest answer is no: it is a deterministic proof/review pipeline with clear gates and known gaps.

## When to ask vs when to act

Ask one short clarifying question when:

- The workflow shape (A/B/C/D) is ambiguous from the request.
- A family classification has confidence below 0.7 and the role map can't tie-break.
- The user mentions inputs you can't see (e.g., "the PSD" but no path) and a path is required to proceed.
- A control would push outside the documented ranges (`bounce_strength > 2.0`, etc.).

Don't ask when:

- The user gave a direction note and a recipe is implied (Workflow A — just emit controls JSON).
- The user gave a layer folder path or PSD path — go run intake / compile and report results.
- The user asks "what does my error mean" — look it up in [references/pitfalls.md](../../references/pitfalls.md) and answer.

## Quality gates

A package is not ready until all three pass. Before saying anything is ready, check:

1. `validation_report.json` in the output folder — compiler-side checks.
2. `preview_validation_report.json` — preview renderer checks.
3. The current Spine contract/import-version gate. Expected: `0 error(s), 0 warning(s)` where a local checker is available, and no JSON/CLI version mismatch.
4. `spine_editor_handoff.zip` — for art-team handoff; must contain JSON, atlas, PNG, unpacked editor images, README, and audit manifest. It is a review bundle, not a native `.spine` file.

If you're claiming motion fidelity, also run the deep animation bakeoff against indexed human-authored exports. Distinguish exact-local counts (pass/fail gates) from aggregate corpus-summary counts (advisory). See [references/validation.md](../../references/validation.md#bakeoff).

## References (load on demand)

- [references/families.md](../../references/families.md) — All 15 family contracts: purpose, naming, source layers, generated animations, controls, pitfalls.
- [references/capability_status.md](../../references/capability_status.md) — Current capability matrix: supported, opt-in/helper-only, and not implemented.
- [references/full_automation_buildout_plan.md](../../references/full_automation_buildout_plan.md) — Phased plan for moving helper-only features into deterministic compiler support with eval gates.
- [references/h5g_corpus_distilled_knowledge.md](../../references/h5g_corpus_distilled_knowledge.md) — Bundled portable H5G corpus/bakeoff knowledge pack for family, animation, role, UI/system, avatar, mesh/deform, production-boundary, and known-gap guidance.
- [references/autonomous_rigging_research.md](../../references/autonomous_rigging_research.md) — Evidence, fixtures, and final acceptance gates before any autonomous-production-rigger claim.
- [references/rig_proposal.md](../../references/rig_proposal.md) — Report-only rig proposal schema and helper.
- [references/external_avatar_rigging_review.md](../../references/external_avatar_rigging_review.md) — External avatar pipeline concepts and Genielabs license boundary.
- [references/spine_43_contract.md](../../references/spine_43_contract.md) — Current Spine 4.3 JSON/import contract and migration boundaries.
- [references/spine_42_contract.md](../../references/spine_42_contract.md) — Legacy 4.2/3.8 migration reference.
- [references/spine_cli.md](../../references/spine_cli.md) — Official Spine CLI command families and plugin support boundaries: automated import/info, policy-gated export/clean/pack/unpack/advanced flags, and unsupported production writes/license automation.
- [references/rig_design.md](../../references/rig_design.md) — Spine's design philosophy for slot work: when to reach for region vs mesh, IK vs FK, transform constraints, path constraints, clipping, events; rig hierarchy patterns; pivot placement; what's automated vs what's an animator's call.
- [references/controls.md](../../references/controls.md) — Bounded controls schema, ranges, natural-language mapping, common combinations.
- [references/intake.md](../../references/intake.md) — Layer naming, boilerplate filtering, visible-vs-hidden layers, PSD-native intake, JSX export, sidecar JSON, parent-local bone math, overlay polarity.
- [references/compilers.md](../../references/compilers.md) — Proof compiler vs layered rig compiler, CLI commands, controls application, batch orchestration, packaging.
- [references/meshes_and_deform.md](../../references/meshes_and_deform.md) — Region vs mesh attachments, vertex placement principles, weights / skinning, deform timelines, linked meshes, performance budgets.
- [references/constraints.md](../../references/constraints.md) — IK (one-bone and two-bone), transform, path constraints. JSON contract, when to use each, what the skill auto-emits.
- [references/events.md](../../references/events.md) — Event triggers, payloads, runtime listener contract, slot-game conventions, the skill's `--enable-events` plan format.
- [references/clipping.md](../../references/clipping.md) — Clipping attachments, CPU cost trade-offs, draw order, self-intersection rule, the skill's `--enable-clipping` plan format.
- [references/validation.md](../../references/validation.md) — Current 4.x compatibility/import-version gates, per-package validation reports, preview validation, bakeoff, exact-local vs corpus-summary distinction.
- [references/pitfalls.md](../../references/pitfalls.md) — Common errors and fixes: blank canvas, no rotation, eye-blink visible at rest, off-center rig, Picasso pose, hat seam, WebGL rendering differences vs APNG.
- [references/boundaries.md](../../references/boundaries.md) — Non-negotiables: source art, version control, PSD handling, production claims, freehand JSON, manifest compilation, bakeoff size.

## Scripts and assets

The skill bundles a complete portable pipeline. The most important one to know about:

- **`scripts/build_spine_package.py`** — End-to-end driver. Takes a folder of per-layer PNGs (with optional Photoshop manifest), a family, and optional bounded controls; emits `shared_symbols.{json,atlas,png}` + `validation_report.json` tagged for the configured Spine editor target, defaulting to 4.3.04. One command, no H5G tree required. The report includes required output-file checks, `animation_loop_validation`, `animation_loop_intents`, and `loop_validation_status`; loop animations must close, settle beats must return keyed numeric bone channels to setup defaults, and transitions/bursts are classified without being forced to close. The opt-in `spine_43_bezier` profile decorates supported numeric timelines with numeric Bezier arrays; default output is curve-free, and `v10_linear` is rejected because it belongs to the legacy proof compiler.

  ```
  python build_spine_package.py --layer-dir <png_folder> --family hp_symbol --rank 3 \
      --doc-width 178 --doc-height 178 --controls more_bouncy.controls.json \
      --out-dir <output>
  ```

  Internally it runs the four pipeline stages below. Run them individually only when you need to inspect or override an intermediate step.

- [scripts/interpret_layers.py](../../scripts/interpret_layers.py) — Layer interpreter. For each PNG, infers semantic role, rig role, parent hint, pivot hint, alpha polarity (visible_at_rest vs hidden_at_rest for blink/laugh overlays), blend hint, animation uses, confidence, evidence. Handles arbitrary symbol art via pattern matching + manifest bounds. Output: a JSON with one entry per layer.

- [scripts/build_rig_layout.py](../../scripts/build_rig_layout.py) — Rig layout builder. Reads interpreter output + per-layer bounds and emits `rig_layout.json` with parent-local bone placement (Y-flipped from PSD to Spine), z-ordered slots, overlay polarity baked in (`setup_color: ffffff00` for hidden overlays), and the always-`root` root bone.

- [scripts/compose_animations.py](../../scripts/compose_animations.py) — 4.x animation composer. Reads a rig layout, a family, and bounded controls; emits the family's idle/breathe/land/win/smart or supported UI/system proof animations using current JSON field names (`rotate`→`value`, slot color→`rgba`, stepped attachment timelines for blinks/laugh, deltas not absolutes). Respects motion amplitude tiers (restrained/medium/energetic) per family and rejects families without deterministic templates.

- [scripts/build_avatar_states.py](../../scripts/build_avatar_states.py) — Avatar state-machine composer. Reads State<N>Idle / State<N>to<M> / State<N>Awarded / State<N>Close layers and emits the proof state graph: per-state idles (one attachment visible, others alpha-0), transitions (cross-fade), awarded beats (pulse + lift), close beats (settle). Avatar builds also write `avatar_state_manifest.json` as a sidecar with state IDs, transitions, deterministic event names (`avatar/state_<n>_awarded`, `avatar/state_<n>_close`, `avatar/state_<from>_to_<to>`), and runtime/art-review flags. The game runtime still owns persistent state and listener consumption; `runtime_consumer_verified` remains `false` until integration proves it.

- [scripts/build_atlas.py](../../scripts/build_atlas.py) — Atlas packer. Alpha-trims, RGB-bleeds transparent pixels (4 iterations) so WebGL bilinear filtering doesn't sample garbage, 1-px edge extrusion in the page, Linear/Linear filter, straight alpha (`pma: false`). Emits `shared_symbols.atlas` with the page name on line 0.

- [scripts/classify_family.py](../../scripts/classify_family.py) — Deterministic family classifier from layer names (used by the interpreter and by Claude when answering classification questions without yet running the pipeline).

- [assets/recipe_controls_schema.json](../../assets/recipe_controls_schema.json) — The bounded controls schema, machine-readable. Reference this when emitting controls JSON or validating a user-supplied controls file.
- [assets/avatar_state_manifest_schema.json](../../assets/avatar_state_manifest_schema.json) — The avatar sidecar manifest schema. It records the proof state graph and explicitly says runtime integration, preview, and art approval are still required.
- [assets/production_export_profile_schema.json](../../assets/production_export_profile_schema.json) and [assets/production_export_policy.json](../../assets/production_export_policy.json) — Phase 10 production export approval inputs. They require exact approved Spine Editor/CLI/runtime versions, license posture approval, approved runtime-probe provenance with package hashes, output-format decision, no Perforce/source-art writes, and approver metadata.
- [assets/h5g_corpus_distilled_evidence.json](../../assets/h5g_corpus_distilled_evidence.json), [assets/rig_proposal_schema.json](../../assets/rig_proposal_schema.json), and [assets/autonomous_rigging_evidence_index.json](../../assets/autonomous_rigging_evidence_index.json) — bundled corpus evidence plus report-only autonomous-rigging proposal gates. They preserve claim boundaries and never authorize production output.

**Advanced features (gated, opt-in):** The pipeline supports IK constraints, transform constraints, clipping attachments, and events. Each is reviewed-by-design — defaults stay constraint-free / event-free because most slot symbols don't need them, but the flags exist when a rigger does:

- `--enable-ik` — auto-detects arm_L+hand_L and arm_R+hand_R pairs and emits two-bone IK with mix-keyed win animations. The animator tunes the target's position. See [references/constraints.md](../../references/constraints.md) and [references/rig_design.md](../../references/rig_design.md#ik-constraint--for-limb-pinning-during-win-choreography).
- `--enable-transform-constraints` (+ optional `--transform-constraints-plan`) — auto-emits shadow-follows-body constraints; user plan adds custom ones. See [references/constraints.md](../../references/constraints.md#transform-constraints).
- `--enable-clipping <plan.json>` — user supplies polygon vertices and end slot; skill validates non-self-intersection and emits the clipping attachment. See [references/clipping.md](../../references/clipping.md).
- `--enable-events <plan.json>` — user supplies the event definitions and per-animation timelines; skill validates and splices into animations. See [references/events.md](../../references/events.md).
- `--enable-physics` (+ optional `--physics-plan`) — records physics candidates for supported wardrobe/natural-motion roles and emits physics constraints only for roles permitted by `assets/physics_policy.json`. Review-only roles stay candidates, zero-length rotate/scale/shear cases are warning-gated, over-budget constraint counts fail validation, and preview playback is required before any motion approval. See [references/physics.md](../../references/physics.md).
- `--enable-sequences` — auto-detects numbered VFX frame groups (`foo_001`...`foo_NNN`), packs all frames into the atlas, and emits one Sequence attachment with a slot `sequence` timeline on win-like animations.
- `--mesh-plan <mesh_plan.json>` — emits mesh attachments for layers/slots explicitly listed in a reviewed mesh plan. The plan supplies hull vertices, interior vertices, UVs, triangles, hull count, and vertex budget; validation rejects bad topology, missing source images, and over-budget meshes. Reviewed plans override automatic drafts.
- `--auto-mesh-plan` — writes and applies a conservative review-required draft mesh plan from eligible source layers. This is topology-aware first-pass support for mesh authoring, not final rigger approval.
- `--auto-bind-weights` — with `--mesh-plan` or `--auto-mesh-plan`, converts mesh attachments to weighted meshes using explicit or generated existing allowed bones and the closed weight binding policy. This is first-pass topology-aware binding with projection, endpoint locks, triangle-neighbor smoothing, and pruning; `bindX`/`bindY` are approximate local offsets unless setup transforms are simple, and animator review/final weight painting remain required.
- `--skin-plan <skin_plan.json>` — emits reviewed multi-skin region variants. The default skin remains first for fallback; named skins may override existing default slot attachment keys with alternate PNG paths under `layer_dir` and may list existing skin bones or existing `ik`/`transform`/`path`/`physics` constraint memberships. Linked meshes and skin-specific complex constraints are not implemented.
- `--target-spine-version <version>` — tags `shared_symbols.json` with the Spine editor version Chris will import with. Default is `4.3.04`.
- `--build-preview` — generates `preview.html` in the output package, loading `@esotericsoftware/spine-player@4.3.1` from CDN to play the package locally. Closes the offline-review loop. See `scripts/build_preview_html.py`.
- `--spine-editor-zip` — writes `spine_editor_handoff.zip` with the runtime import set, unpacked `editor_images/`, `CREATE_SPINE_PROJECT.ps1`, `README_FOR_SPINE_EDITOR.md`, and `audit_manifest.json`. This is the artifact to send to Christian or another Spine animator; it is unzipped before import and can create a native `.spine` project on a machine with Spine installed.
- `--create-spine-project` (+ optional `--spine-cli`, `--spine-version`, `--spine-project-output`) — invokes Spine's official CLI import (`-i -o -r`) to create a native `.spine` project when Spine is installed on the current machine, then may probe it with `-i`. If `--spine-version` is supplied, it must match `shared_symbols.json` `skeleton.spine`; mismatches fail with instructions to regenerate or import with the data version first. It writes `spine_project_report.json`. This does not hand-write the proprietary `.spine` format and does not enable production export automation; see [references/spine_cli.md](../../references/spine_cli.md).
- `--production-export-profile <profile.json> --check-production-export-gate --run-runtime-acceptance-probe` — runs the non-exporting Phase 10 production export gate, executes the browser runtime probe before trusting runtime evidence, and writes `production_export_gate_report.json`. A clean gate reports `ready_for_manual_export`; it still does not invoke Spine CLI or perform production writes.

**Vision bridges (helper tools, not blanket production automation):** Claude has vision; combined with deterministic algorithms, these can reduce review work. They do not remove artist/rigger approval for mesh, weights, physics, or final art direction. See [references/vision_bridge.md](../../references/vision_bridge.md).

- `scripts/trace_mesh_hull.py` — alpha-channel contour → mesh hull vertices (approximates Spine Editor's Trace tool with the same Detail / Padding / Alpha threshold parameters). Helper only; mesh emission still requires a reviewed `--mesh-plan`.
- `scripts/composite_expression_heads.py` — pre-bakes head + each available expression overlay into full-canvas neutral/blink/smile/laugh/mouth_open/mouth_closed/side_eye attachments (eliminates the WebGL overlay-alpha-matte seam from `pitfalls.md`). Triggered by `--composite-expressions` in the driver as an opt-in atlas-variant path when source expression layers exist; preview and artist review remain required before final facial acting approval.
- `scripts/auto_bind_weights.py` — topology-aware projection + endpoint locks + triangle smoothing + prune first-pass weight binding. It is not Spine Editor Auto parity; package emission is gated by `--mesh-plan --auto-bind-weights` or `--auto-mesh-plan --auto-bind-weights` and remains review-required.
- `scripts/render_preview_frames.py` — renders setup-pose PNGs for vision-driven QA. Triggered by `--render-qa-frames` in the driver. Claude can then read the rendered PNG and flag visible issues.
- **Vision-guided IK target keyframes** — when the user supplies a reference image marked with "the hand should land here," Claude reads the position and emits IK target translate keys. (Process documented in `vision_bridge.md`; script-level automation planned.)

**What still genuinely requires human review or future implementation:** Production Spine CLI export (license activation and actual export invocation; the current Phase 10 gate is non-exporting and must run the browser probe before trusting runtime evidence), avatar runtime consumption/listeners and persistent state across spins (game runtime code, not Spine data), final art-direction approval, final physics tuning/approval in preview or Spine Editor, final mesh authoring approval, final weight painting, linked mesh / complex skin-specific authoring, Bezier coverage beyond the opt-in supported numeric timelines, path-constraint emission, and ambient background/UI systems outside the documented recipe families.

**Native `.spine` files:** Only create `.spine` projects through Spine's official CLI import (`Spine -i shared_symbols.json -o output.spine -r <name>`) via `scripts/create_spine_project.py` or the ZIP's `CREATE_SPINE_PROJECT.ps1`. Never reverse-engineer or hand-write the proprietary project format. If Spine is not installed locally, provide the handoff ZIP so Chris can run the included script on his licensed machine. See [references/compilers.md](../../references/compilers.md#native-spine-project-generation).

**Per-project context + learning loop:** the skill remembers what works on your projects. Each project (game / SKU / season) gets its own `PROJECT_CONTEXT.json` next to its layer folders. The skill reads it on every invocation and applies the project's preferred defaults. After each build, capture feedback (`scripts/capture_feedback.py` with `--accept` / `--revise` / `--reject`); after ~5 graded builds, distill (`scripts/distill_patterns.py --update-context`) to roll the learnings into the context's `preferred_defaults`. Next build automatically picks up the bouncier-for-this-game or more-flashy-for-this-game numbers. Full schema and workflow in [references/project_context.md](../../references/project_context.md).

**Tested coverage** (each passes the local structural validation and current 4.x contract gates available in this plugin):

- Layered HP character (9 layers: BG, frame, frame_glow, head, eyes_blink, laugh, hand_L, hand_R, hat_top) → 5 animations on shared timeline (HP, HPidle, HPbreathe, HPland, HPwin), with idle/breathe loop closure and land/win numeric settle validation reported in `validation_report.json`.
- LP letter (1 body + sheen) → 3 animations (LP, LPidle, LPland).
- JP jackpot (BG, body, GRAND text, glow, sparkle) → 4 animations (JP, JPidle, JPland, JPsmart).
- BO bonus (BG, body, lit, glow) → 4 animations (BO, BOidle, BOland, BOsmart).
- Avatar with 3-state machine (State0Idle, State0to1, State1Idle/Awarded/Close, State1to2, State2Idle/Awarded/Close) → animations plus `avatar_state_manifest.json` sidecar. Local Phase 9 evals verify states/transitions/awarded/close event names, report fields, malformed-state/default-state guards, and `runtime_consumer_verified: false`.
- Local Phase 1/5/6 evals cover opt-in Sequence attachments from numbered PNG frames, reviewed multi-skin region variants from a `--skin-plan`, and opt-in composited expression atlas variants from synthetic source layers. These prove compiler structure and deterministic PNG integration, not browser runtime playback or final art-direction approval.
- Local Phase 8 evals cover existing frame/glow/sparkle layer behavior, supported `winframe_explode` UI/system proof reporting, and review-only background parallax rejection. These prove deterministic gating and compiler structure, not final production UI animation approval.
- Local Phase 10 evals cover the production export gate: missing profiles, incomplete approvals, unsafe Perforce/source-art write requests, and a complete dry-run profile that reaches `ready_for_manual_export` without invoking Spine CLI.
- Local Phase 11 eval coverage is consolidated in `assets/eval_coverage_registry.json` and `assets/eval_coverage_report.json`: eval-17 through the production export gate each record promoted status, docs path, required gates, and positive/guard test names.

## Working with the H5G reference implementation

If the user's working directory is the H5G project tree (the `Claude Spine` folder), the reference compilers and validators live under `research/`. Command examples in the references use the H5G paths. For a portable install, substitute the equivalent script in the target pipeline. Core family/rigging guidance comes from the bundled distilled corpus pack, so Chris does not need `research/` unless an H5G-internal user explicitly wants to rerun full bakeoff validation.
