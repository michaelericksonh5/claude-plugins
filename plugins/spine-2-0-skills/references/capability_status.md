# Capability Status

This document is the truth table for what the `spine-slot-animation` skill can claim today. It exists to prevent overclaiming when a user asks whether the system understands every part of slot-game Spine production.

## Bottom line

The system is a strong deterministic proof and review pipeline for slot-game Spine packages. It is not a fully autonomous production rigger for every possible symbol, avatar, UI element, background, mesh, skin, and physics case.

The plugin includes a portable H5G corpus/bakeoff snapshot in `assets/h5g_corpus_evidence_snapshot.json`, a distilled evidence pack in `assets/h5g_corpus_distilled_evidence.json`, and usage guidance in `references/h5g_corpus_bakeoff_usage.md`, so core family, motion, role, UI/system, avatar, mesh/deform, and boundary guidance does not require the full H5G research workspace. When available, `scripts/resolve_h5g_corpus_bakeoff.py` can detect the full research workspace or the read-only G-drive report pack at `G:/artSource/_spineResources/H5G_Corpus_Bakeoff`; if the report pack exists, the resolver exposes `H5G_CORPUS_BAKEOFF_CONSOLIDATED_REPORT.md`, `H5G_CORPUS_BAKEOFF_CONSOLIDATED_INDEX.json`, coverage, recipe, layer interpretation, and motion-profile paths. Autonomous-rigging research also has a report-only evidence layer in `assets/autonomous_rigging_evidence_index.json`, `assets/rig_proposal_schema.json`, and `references/rig_proposal.md`. These artifacts can explain proposed region/mesh decisions with confidence and review reasons, but they do not promote the system to production rigging.

Phase 11 promoted-feature eval coverage is tracked in `assets/eval_coverage_registry.json` and emitted by `scripts/run_local_evals.py` to `assets/eval_coverage_report.json`. The local eval suite covers promoted feature gates from eval-17 through the production export gate; browser runtime proof is run manually through the Playwright probe so unit evals do not require a browser.

The correct operating model remains:

```text
AI proposes context. Deterministic tooling compiles. Validators and previews prove or reject. Artists review.
```

## Supported by the default package builder

| Area | Current status |
|---|---|
| 15 recipe-family taxonomy | Supported: symbols, winframes, meters, transitions, celebrations, avatars. `blocker_or_bonus_symbol` and `non_symbol_or_unknown` remain review-gated. |
| Natural-language revision notes | Supported for bounded controls only: bounce, land duration, idle duration, glow, sparkle, premium, motion, feature-active intensity. Unknown controls fail. |
| PNG-layer first-pass package | Supported by `scripts/build_spine_package.py`: interpretation, rig layout, animation composition, atlas, `shared_symbols.json`, validation report. |
| PSD input | Documented intake path only. PSDs must become manifests + PNG layers before compile. Do not silently open or copy PSD/PSB sources. |
| Standard symbol animations | Supported per family: setup/default, idle, breathe where applicable, land, win or smart where applicable. `validation_report.json` now records loop intent classification and deterministic endpoint checks: loop animations must close, and settle beats return keyed numeric bone channels to setup defaults. These are template motions, not proof of final art direction. |
| Evidence-backed UI/system proof templates | Supported for `meter`, `transition`, `celebration`, `winframe_explode`, and symbol frame/glow behavior when source layers/slots such as `frame`, `frame_glow`, `glow`, or `sparkle` already exist. The package builder reports `ui_system_template`, `ui_system_review_required`, `ui_system_evidence`, and `ui_system_unsupported_reason` in `validation_report.json`. |
| Avatar production path | Supported as a state-frame proof package plus `avatar_state_manifest.json` sidecar: `Avatar`, `State<N>Idle`, `State<N>to<M>`, `State<N>Awarded`, `State<N>Close`, declared deterministic avatar event names, and validation report fields. Persistent game state and event listeners are runtime code, not Spine data; `runtime_consumer_verified` remains `false` until integration proves consumption. |
| Humanoid vs creature topology | Supported as heuristic detection and motion overlays: humanoid default, quadruped gait, many-legged wave, serpentine undulation, wing flap, tail modifier. Review is required for unusual anatomy. |
| Expression overlays | Supported by default via hidden-at-rest overlay slots and stepped attachment timelines. |
| 4.3 structural compatibility | Supported by compiler-side 4.x checks, import-version checks, and documented current 4.3 contract. Compiler-side validation includes conservative loop/settle endpoint validation after final Spine JSON assembly. A package is not ready until validation, preview validation, and matching-version Spine CLI import proof pass. |
| AI visual remediation | Supported through `scripts/visual_remediation_loop.py` and `references/visual_remediation.md`. Claude or an artist inspects `preview.html`/frames, records structured visual issues, and safe findings become bounded controls for recompile. Rig, mesh, z-order, missing attachment, deform, linked-mesh, and path-constraint findings block instead of being hidden by cosmetic controls. |
| Browser runtime preview proof | Supported for representative packages. Run `python scripts/build_runtime_acceptance_fixtures.py`, then `npx -p playwright node scripts/runtime_acceptance_probe.mjs --packages-root generated/runtime_acceptance/packages` to serve each preview over localhost, load `preview.html` in Chromium/Edge, capture screenshots/details, and write `runtime_acceptance.json` evidence with `execution_mode: "browser_runtime"`. This proves representative Spine Player preview loading only; it is not final production export or art approval. |
| Spine Editor handoff ZIP | Supported with `--spine-editor-zip` or `scripts/package_spine_editor_handoff.py`. The ZIP contains the complete import set (`shared_symbols.json`, `shared_symbols.atlas`, `shared_symbols.png`), unpacked `editor_images/`, `CREATE_SPINE_PROJECT.ps1`, README, and audit manifest, and refuses incomplete packages. |
| Native `.spine` project creation | Supported only when a licensed Spine CLI is available. `scripts/create_spine_project.py` and `--create-spine-project` invoke Spine's official CLI import to create `.spine`; they do not hand-write the proprietary project format. Packages also include `CREATE_SPINE_PROJECT.ps1` so Chris can create the project locally. |
| Spine CLI reference layer | Supported as documentation and bounded automation. `references/spine_cli.md` records the official CLI command families, while plugin automation stays limited to JSON-to-`.spine` import and project info probes. |
| Production export approval gate | Supported as a blocking non-exporting gate: `scripts/production_export_gate.py` validates exact approved versions, license posture, browser-runtime probe provenance with package hashes, output-format decision, no Perforce/source-art writes, and approver metadata. Report-only/static/manual evidence is blocked. It does not invoke Spine CLI or produce `.skel`. |
| Report-only rig proposals | Supported as documentation/eval-gated research through `scripts/generate_rig_proposal.py`. Proposals classify region decisions, mesh candidates, confidence, and missing gates. They do not compile Spine output, create mesh plans, paint weights, or approve production rigging. |
| Mesh/weight parity fixtures | Supported as a fixture gate through `assets/mesh_weight_parity_fixture_schema.json` and `scripts/compare_mesh_weight_parity.py`. This compares Chris-approved Spine exports against candidate weighted meshes for topology and weight-sum sanity. It is evidence for review, not automatic production approval. |
| Avatar runtime contracts | Supported as a runtime ownership gate through `assets/avatar_runtime_contract_schema.json` and `scripts/validate_avatar_runtime_contract.py`. Avatar runtime state/event claims stay blocked until a target runtime owner verifies state and event consumption. |
| Bundled and network corpus/bakeoff guidance | Supported through `assets/h5g_corpus_evidence_snapshot.json`, `assets/h5g_corpus_distilled_evidence.json`, `references/h5g_corpus_distilled_knowledge.md`, `references/h5g_corpus_bakeoff_usage.md`, and `scripts/resolve_h5g_corpus_bakeoff.py`. The preferred shared source is the read-only G-drive report pack with `H5G_CORPUS_BAKEOFF_CONSOLIDATED_REPORT.md` and index. Bundled snapshots are advisory and not production approval. Full bakeoff reruns are optional H5G-internal validation. |

## Opt-in or helper-only support

| Area | Current status |
|---|---|
| IK constraints | Opt-in with `--enable-ik`. Auto-detects arm/hand pairs and emits targets/mix timelines. Target choreography still needs rigger or vision-guided review. |
| Transform constraints | Opt-in with `--enable-transform-constraints` or a user plan. Use for follow relationships such as shadows/accessories. |
| Clipping | Opt-in with `--enable-clipping <plan.json>`. Requires user-supplied polygon and end slot. CPU budget review remains required. |
| Events | Opt-in with `--enable-events <plan.json>`. The skill emits event data; the game team owns listeners and runtime behavior. |
| Avatar events | Avatar manifests always declare deterministic event names for transitions, awarded beats, and close beats. Event timelines are emitted only when `--enable-events <plan.json>` supplies matching manifest names and times. |
| Physics constraints | Opt-in with `--enable-physics`. Policy-gated candidate reporting covers hair, beard, mustache, dress, skirt, robe, cloak, cape, sleeve, scarf, ribbon, belt, chain, necklace, earrings, dangling jewelry, tails, wings, and antennae. Only default-on policy roles emit constraints; review-only roles stay candidates. Preview and animator review remain required for motion approval. |
| Mesh candidate reporting | Opt-in with `--report-mesh-candidates`. Writes deterministic conservative classifications without changing package output. |
| Automatic draft mesh plans | Opt-in with `--auto-mesh-plan`. Generates review-required draft mesh plans for conservative roles only; reviewed `--mesh-plan` files override drafts. This is not rigger signoff. |
| Mesh hull tracing | Helper script exists: `scripts/trace_mesh_hull.py`. Automatic drafts use conservative alpha-bound hulls and low role budgets. |
| Unweighted mesh attachments | Opt-in with `--mesh-plan <mesh_plan.json>` or `--auto-mesh-plan`. Reviewed plans emit explicitly planned 4.x meshes; automatic drafts are first-pass review artifacts and are blocked by the same topology/budget validation. |
| First-pass weighted mesh binding | Opt-in with `--auto-bind-weights` plus a reviewed or automatic mesh plan. Emits weighted vertices only with explicit/generated existing allowed bones and a closed weight policy. Uses topology-aware projection, endpoint locks, smoothing, and pruning; bind positions are approximate local offsets, and animator review is required. |
| Multi-skin region variants | Opt-in with `--skin-plan <skin_plan.json>`. Emits default-first 4.x skins plus reviewed named variant skins that override existing default slot attachment keys with alternate region PNGs under `layer_dir`. Default fallback remains required, preview lists available skins, and browser/runtime playback is not claimed unless separately executed. |
| Sequence attachments | Opt-in with `--enable-sequences`. Numbered VFX frames (`foo_001`...`foo_NNN`) collapse into one Sequence attachment while all frames still pack into the atlas. |
| Expression atlas variants | Opt-in with `--composite-expressions` when source head + expression overlay layers exist. Local eval coverage proves the builder packs available neutral/blink/smile/laugh/mouth_open/mouth_closed/side_eye composited head attachments, removes source overlay output, and uses head-slot attachment swaps. Deterministic PNG QA checks are structural only; Spine Player preview and artist review are still required for expression timing, seams, and final facial acting approval. |
| Preview HTML | Opt-in with `--build-preview`. It embeds JSON/atlas/PNG through Spine Player `rawDataURIs`, exposes deterministic `window.__h5gSpinePlayerConfig`, `window.__h5gSpinePlayer`, and `window.__h5gSpinePreviewState` hooks for the browser probe, and displays runtime load/error status. Useful for review; still requires visual inspection. |
| Setup-pose visual QA | Opt-in with `--render-qa-frames`. Triage only; Spine Web Player remains authoritative for motion. |

## Not implemented today

| Area | Status |
|---|---|
| Bezier curve emission profile | Opt-in through `export_profile: "spine_43_bezier"` with `bezier_preset` (`ease_in`, `ease_out`, `ease_in_out`, `overshoot`, `settle`). The legacy alias `spine_42_bezier` is still accepted for older controls. Emits numeric absolute Bezier arrays only on supported numeric timelines currently covered by policy: bone `rotate` / `translate` / `scale` and slot `rgba` / `alpha` when present. Default 4.3 output remains curve-free; `v10_linear` belongs to the legacy proof compiler and is rejected by the portable builder. Attachment, sequence, animation-level events, and draw-order timelines reject curves. This is not global Bezier/path/deform feature coverage. |
| Production weight painting | Not implemented. Auto-bound weighted meshes are first-pass proof output only and require animator review in Spine Editor. |
| Deform timelines | Not implemented and intentionally discouraged unless a reviewed production case requires them. Prefer weights driven by bones. |
| Linked meshes | Not implemented. Mesh variants and linked-mesh inheritance are future multi-skin/mesh work. |
| Skin-specific linked meshes / complex constraints | Not implemented. `--skin-plan` is region-variant only; linked mesh inheritance and new skin-specific constraint authoring remain future reviewed work. |
| Path constraints | Documented as rare; not emitted by the current package builder. A skin plan may list existing path constraint membership only if a top-level path constraint already exists from another reviewed path. |
| Ambient background animation | Review-only. Broad background drift/parallax and foreground ambient overlays have generated evidence, but no deterministic source-layer/parallax-depth/compiler contract. |
| Buttons / row blockers / generic UI VFX | Review-only. Button idle/hover/press, row blockers, `vfx_only`, and unknown UI/system buckets fail or report review-required instead of compiling guessed templates. |
| Full UI/game-screen animation system | Partially covered through meter, transition, celebration, winframe, and symbol frame/glow proof templates. This is not final production UI animation approval. |
| Final avatar runtime integration | Not implemented. The compiler emits a manifest for the game team, but it does not implement persistent state storage, state advancement, runtime event listeners, or art-approved acting. |
| Production Spine CLI export | Not implemented. The gate can report `ready_for_manual_export` when approvals and browser runtime evidence are complete, but `.skel` conversion, production export automation, license activation management, Perforce automation, source-art writes, and art approval remain blocked. |
| Fully autonomous production rigger | Not implemented. Requires approved mesh/weight parity fixtures, avatar runtime-state proof, target runtime acceptance, approved export policy, and Chris/art approval before any such claim. |

## How to answer completeness questions

When asked "does it fully understand everything front to back?", answer no. Then route to evidence:

1. Use `references/families.md` for asset-family classification.
2. Use `references/rig_design.md` for rigging judgment.
3. Use this file for current capability status.
4. Use `assets/eval_coverage_registry.json` and `assets/eval_coverage_report.json` to verify promoted-feature local eval coverage.
5. Use `references/validation.md` before any readiness claim.
6. Use `references/meshes_and_deform.md`, `references/constraints.md`, `references/physics.md`, `references/events.md`, and `references/clipping.md` only when those features are specifically in scope.
7. Use `references/visual_remediation.md` when the user wants Claude to look at the preview and fix issues through an iteration loop.
8. Use `references/autonomous_rigging_research.md` and `references/rig_proposal.md` for autonomous-rigger questions; answer that this is report-only until the listed parity and approval gates are verified.
9. Use `references/h5g_corpus_bakeoff_usage.md`, `assets/h5g_corpus_evidence_snapshot.json`, and `scripts/resolve_h5g_corpus_bakeoff.py` to decide whether full research, the read-only G-drive consolidated report pack, a generic G-drive bakeoff resource, or bundled advisory snapshot evidence is available.

The skill should never imply that a clean proof package means production-complete motion, production mesh/weights, production physics, or art-director approval.
