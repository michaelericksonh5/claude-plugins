# Validation

Three gates a package must pass before it ships. Plus an optional fidelity bakeoff for motion-quality claims.

## The three required gates

```
1. validation_report.json            — compiler-side checks
2. preview_validation_report.json    — preview renderer checks
3. Spine contract / import-version gate — strict current 4.x contract
```

For current packages, all three are required. For legacy v10_linear packages, only the first two apply — the current 4.x checker is not appropriate for 3.8 emissions.

Before saying anything is ready, run all three and confirm they pass.

## 4.x compatibility and import-version gate

The strict validator catches current 4.x contract violations. The import-version gate additionally proves that the CLI import version matches `shared_symbols.json` `skeleton.spine`.

### H5G reference

```powershell
uv run python research/spine_42_compatibility_checker.py <batch_root>
```

The argument may be a single `compiled/` package folder or a batch run root containing per-symbol `compiled/` folders.

Expected: `Summary: 0 error(s), 0 warning(s)`. Any error blocks release.

The H5G checker name is historical. Use it for the 4.x shape checks it supports, and treat local Spine CLI import as the final editor-import proof for 4.3 packages.

### What the 4.x checker flags

- Skeleton.spine string not targeting an approved 4.x editor line.
- `skeleton.width/height` equal to atlas page size instead of document size.
- `skins` emitted as an object instead of an array.
- Rotate timeline keys using `angle` instead of `value`.
- Slot color timelines using `color` instead of `rgba`.
- Two-color timelines using `twoColor` instead of `rgba2`.
- `rgba2` emitted without setup slot `dark`.
- Atlas regions referenced by attachments that don't exist.
- Sequence attachment frame regions that don't exist (`path_001`, `path_002`, etc.).
- Invalid curve fields: curves outside `export_profile: "spine_43_bezier"`, unsupported named curve strings, non-finite or nonnumeric Bezier arrays, wrong Bezier array lengths, out-of-segment handle times, non-monotonic handle times, or curves on unsupported discrete timelines (`attachment`, `sequence`, animation-level `events`, `drawOrder`, or `draw_order`).
- Atlas page filename mismatch with the actual PNG.
- Non-normal slot blend modes leaking through.
- Slots referencing missing bones / attachments / skin entries.
- drawOrder offsets referencing missing slots.

For the current default contract, see `references/spine_43_contract.md`. For older 4.2/3.8 migration details, see `references/spine_42_contract.md`.

### When the checker fails

The error message names the violating field and the slot / bone / animation where it appears. Fix the compiler emission, not the JSON by hand. If the user is using a third-party compiler, surface the error and point them at the matching contract section.

## Per-package validation report

`<output>/validation_report.json` is the compiler-side report. It captures:

- Recipe type and recipe support status.
- Applied controls and `unsupported_noop_controls` (controls that targeted missing slots).
- Referenced PNGs exist and parse.
- Atlas regions cover every JSON attachment.
- Draw order equals z-order.
- Curve profile constraint: omitted/default output is curve-free; `spine_43_bezier` is the current builder profile that may emit validated numeric curve arrays.
- Output file existence (`shared_symbols.json`, `shared_symbols.atlas`, and `shared_symbols.png`). Missing texture pages fail handoff because Spine Editor import and Spine Player preview both need the atlas page beside the atlas.
- Advanced-feature absence (no mesh / IK / deform / clipping / events unless an explicit policy opts in).
- Mesh automation fields when opted in: `mesh_candidate_report`, `auto_mesh_plan`, `mesh_deformation_qa`, first-pass weight summaries, and `__mesh_weight_test` for weighted mesh review.
- Animation loop validation: every emitted animation is classified as `setup`, `loop`, `settle_to_setup`, `transition`, or `burst`. Loop animations compare first and terminal keyed states for active bone/slot timelines; settle beats compare final keyed numeric bone channels to setup defaults.

Loop validation fields are machine-readable: `animation_loop_validation`, `animation_loop_intents`, and `loop_validation_status`. Any loop validation issue makes `validation_report.json` status `failed`. The validator is conservative for one-shot slot channels: transitions and bursts are classified but not forced to close, and settle checks avoid blocking intentional visibility changes unless a clear numeric setup-return issue is present.

A green `validation_report.json` is necessary but not sufficient. It catches structural problems; the 4.x compatibility/import-version gate catches contract-shape and editor-version problems; the preview validation catches render-time problems.

## Per-package preview validation report

`<output>/preview_validation_report.json` captures:

- JSON / atlas / page shape parses cleanly.
- Canvas bounds resolve.
- No missing attachments at any frame of any animation.
- Per-animation APNGs render (when the layered compiler emits APNG previews).
- `rawDataURIs` are embedded for `file://` browser compatibility, with keys matching `shared_symbols.json`, `shared_symbols.atlas`, and the atlas page line (`shared_symbols.png`).

If preview validation fails, the package isn't ready even if the other two gates pass.

## When all three pass

Confirm the package looks visually meaningful. Open `preview.html` (or the APNGs for the layered compiler) and check:

- Symbol is centered, recognizable.
- Idle motion is subtle and loopable.
- Land impact is short and settles to rest.
- Win celebration is decisive and returns to idle.
- No off-center parts, no Picasso pose, no overlay showing the wrong expression at rest, no halo, no seam.

If any of those visual checks fail, route to `references/pitfalls.md` for the matching diagnosis.

## Browser runtime acceptance probe

Representative runtime/preview proof is available for advanced HP symbol, avatar state, and supported UI/frame packages:

```powershell
python scripts/build_runtime_acceptance_fixtures.py
npx -p playwright node scripts/runtime_acceptance_probe.mjs `
  --packages-root generated/runtime_acceptance/packages
```

The fixture builder writes only under `generated/runtime_acceptance/` in this repo. The probe serves each package over localhost, opens `preview.html` in Chromium/Edge through Playwright, waits for `@esotericsoftware/spine-player` and a canvas, captures screenshots and page/console errors, writes per-package `runtime_acceptance.json` plus probe details, and writes `generated/runtime_acceptance/probe/runtime_acceptance_probe_report.json`.

Accepted production-gate evidence must use provenance `method: "runtime_probe"`, `tool: "h5g-runtime-acceptance-probe"`, `tool_version: "runtime-acceptance-probe-v1"`, and `execution_mode: "browser_runtime"`. Report-only fixtures, static review, manual checklists, and self-attested evidence are blocked and remain unverified. This is representative browser preview proof, not `.skel` export, game runtime integration, Perforce submission, or art approval.

## Visual remediation loop

Runtime proof says the preview loads. Visual remediation decides what to fix next.

Use:

```powershell
python scripts/visual_remediation_loop.py `
  --package-dir <compiled_package_dir> `
  --out-dir generated/visual_reviews/<asset> `
  --render-frames
```

Claude or the artist inspects `preview.html` and the generated packet, writes `visual_review.json`, then runs:

```powershell
python scripts/visual_remediation_loop.py `
  --review generated/visual_reviews/<asset>/visual_review.json `
  --out-dir generated/visual_reviews/<asset>
```

Safe visual findings such as `too_flashy`, `not_bouncy_enough`, or `idle_too_fast` become bounded controls for recompile. Structural findings such as `mesh_tearing`, `wrong_z_order`, `missing_attachment`, `deform_needed`, `linked_mesh_needed`, or `path_constraint_needed` block until the underlying rig/compiler/source-art issue is fixed.

This is the right place for Claude visual QA. It is still not final production art approval.

## Regression tests

A test suite locks in the contract. Run after any compiler change.

### H5G reference

```powershell
uv run python -m unittest research.test_layered_rig_compiler
```

Expected: all tests pass. Failing tests block merge.

The tests cover the current 4.x contract violations the compatibility checker checks, plus the parent-local bone math, plus the overlay polarity, plus the shared-timeline composition.

## Bakeoff (optional, for motion-fidelity claims)

The bakeoff compares generated rigs against indexed human-authored Spine evidence (real exports from previous games).

Use `scripts/resolve_h5g_corpus_bakeoff.py` before deciding which evidence tier is available. It detects the local full H5G research workspace, the read-only network report pack at `G:/artSource/_spineResources/H5G_Corpus_Bakeoff`, a generic network bakeoff resource, and the bundled advisory snapshot in `assets/h5g_corpus_evidence_snapshot.json`.

When the resolver reports `network_h5g_corpus_bakeoff_report_pack_available`, read `H5G_CORPUS_BAKEOFF_CONSOLIDATED_REPORT.md` first. It is the efficient middle-ground artifact: the full bakeoff/corpus findings are organized for Claude, while generated PNG previews, atlases, HTML previews, and duplicate historical payloads are excluded.

### H5G reference

```powershell
# Smoke run first (fast)
uv run python research/full_deep_animation_bakeoff.py --limit 25 --include-ui --include-review-buckets --progress

# Full run
uv run python research/full_deep_animation_bakeoff.py --include-ui --include-review-buckets --progress

# Summarize into closure gates
uv run python research/compiler_gap_bakeoff.py --bakeoff-run <run_dir>
```

### What the bakeoff reports

- Missing animation names per family.
- Missing affected bones / slots.
- Missing timeline types (translate / scale / rotate / slot_color / slot_attachment / draw_order / events / mesh-deform).
- Duration deltas vs reference.
- Motion-range deltas (amplitude per timeline type vs reference).

### Exact-local vs aggregate corpus-summary

Distinguish two count types in the bakeoff output:

- **Exact-local counts** — strict pass/fail per matched local reference. Use these for merge / release gates. Block on regression.
- **Aggregate corpus-summary counts** — advisory trend pressure across the indexed corpus. Use for future prioritization, not merge blocking.

Don't conflate the two. A regression in aggregate-corpus-summary counts is a signal to invest in coverage; a regression in exact-local counts is a release blocker.

If only the bundled snapshot is available, mark the result as advisory corpus guidance. Do not claim fresh full-bakeoff proof. If the network report pack is available but the full research workspace is not, treat it as shared reference evidence, not a fresh rerun.

### When NOT to run the bakeoff

- During fast iteration on a single symbol. The compatibility checker + preview is enough.
- Before approved source-layer fixtures exist for the family in question — the bakeoff has nothing to compare against.
- Without progress / checkpoint flags. A full bakeoff against thousands of indexed exports takes hours; without progress you can't tell hung from working.

## Advanced contract validation

For claims about production-readiness for source-layer intake, mesh / weights / deform, IK / constraints, clipping, runtime events, or production export:

### H5G reference

```powershell
uv run python research/advanced_spine_contracts.py `
  --project . `
  --output-dir research/generated/advanced_spine_contracts
```

The validator writes `advanced_spine_contract_validation.json` and `.md`. A `blocked` result is expected until approved source PSD fixtures, exact runtime/editor versions, Spine CLI/license approval, runtime event ownership, and runtime acceptance tests exist.

Treat mesh / IK / deform / clipping / events as policy / readiness-gated unless the report says otherwise. A passing schema or policy check is NOT the same as production authoring support.

## Production export gate

The production export gate checks manual export readiness without exporting:

```powershell
python scripts/production_export_gate.py `
  --package-dir <compiled_package_dir> `
  --production-export-profile <profile.json>
```

The gate writes `production_export_gate_report.json`. It requires:

- `validation_report.json` status `ok`.
- Exact approved Spine Editor, Spine CLI, and runtime versions from `assets/production_export_policy.json`.
- Approved license posture and approver metadata.
- An explicit JSON-vs-binary output-format decision.
- Browser runtime acceptance evidence proving required skins, physics, sequences, clipping, events, and blends loaded when the package claims or emits them.
- `perforce_writes: false` and `source_art_writes: false`.

This is not Spine CLI export. `export_invoked` is always `false`; the default policy keeps `cli_invocation_allowed: false`. A clean report means `ready_for_manual_export` with `runtime_acceptance_status: "verified_browser_runtime"` only when the gate runs the browser probe for the current package. Existing browser evidence files, report-only fixtures, static/manual checks, `.skel` conversion, license activation, Perforce submission, source-art mutation, and art approval remain insufficient.

See `references/spine_cli.md` for the official CLI command families. The validation rule is unchanged: production export remains gated, and CLI export/clean/pack/unpack/advanced flag use is documented only until an approved policy permits it.

## Autonomous-rigging proposal gates

Report-only rig proposals are validated as claim-boundary artifacts, not package readiness artifacts. The local evals check that:

- `assets/rig_proposal_schema.json` is closed and requires `proposal_mode: "report_only"`, `production_output_claimed: false`, and bundled evidence IDs from `assets/h5g_corpus_distilled_evidence.json`.
- `assets/autonomous_rigging_evidence_index.json` says the system is not a fully autonomous production rigger.
- `scripts/generate_rig_proposal.py` emits region/mesh decisions, review reasons, and blocked policy gates without creating Spine output.
- `scripts/compare_mesh_weight_parity.py` compares a candidate weighted mesh against a Chris-approved Spine export fixture for topology counts, weight-sum thresholds, and bones-per-vertex limits.
- `scripts/validate_avatar_runtime_contract.py` records avatar runtime state/event ownership and blocks runtime claims until the target game runtime owner verifies consumption.
- Genielabs remains conceptual prior art and PolyForm Noncommercial code is not copied or embedded.

These gates are necessary for autonomous-rigger research but not sufficient for production. Production mesh/weight, avatar, and export claims still require Chris-approved fixtures, target runtime acceptance, and the production export gate above.

## Audit manifest

Packages destined for handoff get an `audit_manifest.json`:

- Source package path.
- Review-only flag (no production write happened).
- Export profile.
- Recipe type.
- List of animations emitted.
- Validation status per gate.
- File hashes for every packaged file.

If you're handing off a package, confirm the audit manifest exists and the validation statuses are all green. If they aren't, the package isn't ready.

## Spine Editor handoff ZIP

For human animator review, use the packaged ZIP, not loose files:

```powershell
python scripts/package_spine_editor_handoff.py <compiled_package_dir>
```

Or build it directly:

```powershell
python scripts/build_spine_package.py ... --build-preview --spine-editor-zip
```

The ZIP must contain:

- `shared_symbols.json`
- `shared_symbols.atlas`
- `shared_symbols.png`
- `editor_images/` unpacked from the atlas for Spine Editor image lookup
- `CREATE_SPINE_PROJECT.ps1` for one-command native `.spine` creation on a machine with Spine installed
- `README_FOR_SPINE_EDITOR.md`
- `audit_manifest.json`
- `preview.html` when preview generation was requested

The packager refuses to write the ZIP if any required import file is missing or if `validation_report.json` is not `ok`.

Spine does not import the ZIP directly. The recipient unzips it and runs `CREATE_SPINE_PROJECT.ps1` to create a native `.spine` file through Spine's official CLI, or imports `shared_symbols.json` via **File -> Import Data...** and then sets the Spine **Images** path to the unzipped `editor_images/` folder if the imported attachments show as missing. The atlas files remain in the bundle for runtime preview/game package validation.

## The single rule

A package is ready iff:

1. `validation_report.json` shows no failures.
2. `preview_validation_report.json` shows no failures.
3. For current 4.x packages: the compatibility/import-version gates show `0 error(s), 0 warning(s)` where local tools are available.
4. The preview visually represents the symbol correctly.

If any of those isn't true, don't say it's ready. Say what specifically failed and what the next step is.
