# Non-Negotiable Boundaries

Project-level constraints with the reasoning behind each. These exist to prevent specific past failure modes.

## Do not write to source-art directories

In the H5G reference implementation: never write to `G:\artSource\` or any equivalent canonical art-source location.

**Why:** Artists own that workspace. The build pipeline is read-only against source art. Writing into source art creates lockfile conflicts on shared drives, risks accidental overwrite of in-progress work, and breaks the artist's mental model of where their files live.

**How to apply:** Build outputs go to a separate directory tree (in H5G: `research/generated/`, `photoshop2spine/exports/`, or `bakeoff/`). When the user asks "where should this go", default to a build-output location, never to source art.

## Do not auto-commit to version control or asset management

In the H5G reference implementation: never write to or submit to Perforce.

**Why:** The art team reviews each handoff before integration. Auto-commits would bypass that review and push unvalidated work into the production stream.

**How to apply:** Generate handoff packages and put them in a review-only folder. Tell the user where the package is. Let them initiate the version-control / asset-management write step themselves.

## Do not open or copy PSD/PSB files outside the documented intake workflow

**Why:** PSDs can be hundreds of MB to GB. Silently opening them costs network bandwidth and risks lockfile conflicts in some asset-management systems. The intake workflow exists to batch the cost and document what was read.

**How to apply:** Only read `.psd` / `.psb` files via `psd_native_intake.py` or an equivalent intake step. Don't open a PSD just to inspect the layer tree — use the manifest the intake step produces.

## Do not claim production-ready for mesh, IK, deform, clipping, events, or production export

**Why:** All of these are gated by separate review processes in any serious slot-game pipeline. Mesh weights need animator review, IK constraints need rigger review, clipping requires CPU budget approval, events need runtime listener ownership, and production export requires Spine CLI / license approval and runtime acceptance tests.

The default compiler path emits no mesh, deform, clipping, events, IK, transform constraints, physics, non-default skins, or Bezier curves unless an explicit opt-in flag, plan, or profile is supplied. Some advanced helpers can emit reviewed IK, transform constraints, clipping, events, physics, meshes, weights, multi-skin region variants, or `spine_43_bezier` curves for supported numeric timelines, but a passing schema or policy check is NOT the same as production authoring support. The Phase 10 production export gate is report-only: it can block or mark a package ready for manual export review, but it never invokes Spine CLI, converts `.skel`, activates licenses, writes to Perforce, or writes to source art. Final weights, deform timelines, broader Bezier coverage, linked meshes, and complex skin-specific constraint authoring are not production-emitted by the default builder today.

**How to apply:** When asked about mesh / IK / deform / clipping / events / production export, state the current readiness honestly. The default is "blocked pending review gates" until the relevant review process explicitly approves the feature for the project.

## Do not freehand raw Spine JSON in chat or in code

**Why:** Any free-hand JSON is a regression risk. The compiler exists to make output reproducible and to let the regression tests catch violations of the current 4.x contract. Hand-edited JSON bypasses both.

**How to apply:**

- For revision notes: emit bounded controls JSON (see `references/controls.md`); let the compiler apply it.
- For new symbols: run the compiler against PNG/PSD inputs.
- For bug fixes: change the compiler emission, not the output JSON.
- For one-off Spine Editor work: do it inside Spine Editor and re-export; don't hand-edit the JSON output.

If the user insists on a hand-edited JSON workaround, surface the risk: the change won't survive the next compile, the regression tests won't cover it, and the next person looking at the file won't know it was hand-edited.

## Do not run massive bakeoffs without progress / checkpoints

**Why:** Bakeoffs comparing thousands of indexed Spine exports take hours. Without progress flags you can't distinguish a hung run from a working run, and a hung run wastes a workday.

**How to apply:** Always use `--progress` (or the equivalent) on bakeoffs. Run a `--limit 25` smoke test first to confirm the pipeline is healthy. Only then run the full bakeoff. Save bakeoff outputs to a timestamped run directory so partial results survive crashes.

## Do not silently compile PSD/PSB source-layer manifest rows

**Why:** Source-layer scans flag thousands of candidate folders. Most aren't ready to compile (wrong manifest schema, missing required layers, ambiguous classification). Silent compilation produces noise in the output and burns hours of human review time.

**How to apply:** Treat PSD/PSB manifest rows as review-gated by default. Compile only rows where the manifest has been explicitly approved (the H5G reference uses a manual review flag). PNG-folder rows that already passed intake review can be compiled directly.

## Boundaries summary

When in doubt about whether an action is safe:

- **Reads from source art:** OK if minimal, scripted, and through the intake workflow.
- **Writes to source art:** never.
- **Writes to version control / asset management:** never. Always produce review-only packages.
- **Hand-editing JSON:** never. Change the compiler instead.
- **Claiming production-ready features that are review-gated:** never. State the current readiness honestly.

These are not stylistic preferences. Each one corresponds to a specific past incident that cost time or trust.

## What to say when a user asks for something on this list

Don't refuse silently. Explain what the boundary is and why, and offer the equivalent safe action. Examples:

> "I won't write directly to `G:\artSource\` — that's the artist's canonical workspace. I'll generate the new symbol package under `research/generated/<batch>/` and you can hand it to art for integration."

> "I won't hand-edit the `shared_symbols.json` — the regression tests cover the compiler's emission, not free-hand changes. The behavior you want maps to `bounce_strength: 1.4` in the controls JSON; let me regenerate the package with that."

> "I'll skip the bakeoff for now — the smoke run takes 2 minutes and confirms what we need; the full bakeoff is hours and isn't necessary for this iteration."

Boundaries are part of the contract, not friction. The user will appreciate the explanation when they understand the underlying reason.
