# Spine 4.3 Readiness Audit

Audit date: 2026-05-20

## Scope

This audit covers the `spine-slot-animation` plugin and its single bundled skill, `skills/spine-slot-animation/SKILL.md`, plus the referenced compiler scripts, policy assets, references, and local eval registry.

## Research Baseline

Authoritative Spine docs support these operating rules:

- Exported JSON/binary data imports back into Spine only with the same editor version that exported the data. For generated data, `skeleton.spine` must match the JSON structure being emitted, and the Spine CLI import must use that same version.
- Spine project files are backward-compatible and are the safe bridge to newer editors after import.
- Spine Runtimes must match the editor major/minor export line. The plugin targets Spine Editor `4.3.04` and Spine Player `4.3.1`.
- Current 4.x JSON uses array-form `skins`, bone rotate timeline key `value`, slot color timeline `rgba`, weighted mesh vertices encoded as bone count plus bone/bind/weight tuples, and deform timelines under `animations -> deform -> skin -> slot -> mesh`.
- Meshes, weights, deform, linked meshes, physics, events, clipping, and constraints remain feature-specific contracts, not things to infer by changing a version string.

## Skill Readiness

`spine-slot-animation` is structurally ready for the 4.3 default path:

- Frontmatter and description explicitly trigger on Spine 4.3 / 4.3.04, slot symbols, PSD/layer pipelines, preview failures, rigging, bounded revisions, and compatibility errors.
- The default path routes new packages through `scripts/build_spine_package.py`, emitting `shared_symbols.json`, atlas, preview, validation report, and optional editor handoff ZIP.
- The skill now states the editor import rule directly: do not fix import errors by editing `skeleton.spine`; import with the same version recorded in the data, then use `.spine` as the bridge.
- 3.8/v10 and 4.2 references are preserved only as legacy migration paths.
- Production rigging, final weight painting, deform timelines, linked meshes, production export, runtime avatar integration, and final art approval remain explicitly blocked or review-gated.

## Compiler And Gate Readiness

The 4.3 path is centralized through `scripts/spine_version_policy.py`:

- `DEFAULT_SPINE_EDITOR_VERSION = "4.3.04"`
- `DEFAULT_SPINE_PLAYER_VERSION = "4.3.1"`
- Supported editor lines remain limited to 4.x prefixes currently accepted by the local validator.

Critical enforcement points:

- `scripts/build_spine_package.py` writes `skeleton.spine` from the configured target version and validates the 4.x shape.
- `scripts/create_spine_project.py` reads `shared_symbols.json` `skeleton.spine` and rejects any CLI import-version mismatch before invoking Spine.
- `scripts/package_spine_editor_handoff.py` generates `CREATE_SPINE_PROJECT.ps1` with the same mismatch guard for Chris's machine.
- `scripts/build_preview_html.py` loads Spine Player `4.3.1`.
- `assets/production_export_policy.json` and `assets/production_export_profile_schema.json` require the 4.3 editor/runtime versions for approval.

## Findings Fixed In This Audit

Secondary docs and policy still had stale 4.2 wording after the main migration. Updated:

- `assets/ui_system_template_policy.json`: production claim now says deterministic Spine 4.3 packages.
- `references/full_automation_buildout_plan.md`: Bezier phase now says modern 4.3 curve policy.
- `references/meshes_and_deform.md`: region attachment capability now says correct 4.x contract.
- `references/spine_42_contract.md`: marked as legacy, removed claims that the skill defaults to 4.2, and documented `spine_43_bezier` as current with `spine_42_bezier` as a legacy alias.
- `Plan.txt`: Bezier phase now says modern 4.3 curve policy.

## Verification Results

Passed:

- JSON syntax checks for touched JSON policy/schema files.
- Targeted regression tests for eval coverage, 4.3 Bezier output, and CLI version mismatch rejection.
- Full local eval suite: `118` tests passed.
- Skill placeholder scan: no `TODO`, `FIXME`, `TBD`, `[INSERT`, or `<placeholder>` markers in the bundled skill.
- Plugin skill inventory: one bundled skill, `./skills/spine-slot-animation`.

Not proven on this machine:

- Live Spine CLI import into a native `.spine` project. `Spine.com` was not found on PATH here, so the final editor-import proof must be run on Chris's licensed Spine install or another machine with Spine CLI available.
- Final production export (`.skel`, Perforce writes, source-art writes) is intentionally not automated by this plugin.

## Remaining Honest Gaps

These are not bugs in the 4.3 migration; they are capability boundaries the skill correctly preserves:

- Automatic weighted meshes are first-pass review artifacts, not final Spine Auto parity or hand-painted production weights.
- Deform timelines and linked meshes are documented but not emitted.
- Avatar runtime ownership is gated by runtime contract verification; the Spine package alone does not implement persistent game state.
- Browser preview proof is representative runtime acceptance, not final art approval.
- Production export gate can report `ready_for_manual_export`; it does not invoke licensed export or submit assets.

## Verdict

The plugin is ready for the clean Spine 4.3.04 generation path at the deterministic proof/handoff level. The remaining blockers are real production boundaries, not stale version assumptions: live Spine CLI import proof on Chris's machine, artist review, final mesh/weight approval, avatar runtime integration, and production export execution.
