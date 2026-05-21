---
name: slot-compare
description: Side-by-side visual comparison of slot art assets. Three modes — ITERATION (multiple iterations of the same asset within one project, e.g. Key_Art_001 vs Key_Art_003 vs Key_Art_005, to help pick a winner), ASSET (different assets within one project, e.g. HP1 vs MP1 vs LP1 to verify tier hierarchy reads correctly, or the full approved set in one view), and CROSS-PROJECT (same asset slot across two projects — useful for reskins, sequel consistency, A/B style explorations). Reads images inline via the Read tool, scores them against the rubric, and produces a structured comparison report. Readonly — never writes to project.json. Use this whenever the user asks to compare, evaluate side-by-side, pick a winner between, choose between iterations, verify hierarchy, check consistency across, or audit two versions of any slot art asset — even when they don't explicitly say "compare" (e.g. "which is better", "which key art should I lock", "do these symbols still read as a tier set", "does the reskin still feel like the same game", "rank these", "A vs B", "score these", "are these consistent", "do these match", "which one wins", "pick the best one", "evaluate these options").
---

# Slot Compare — Side-by-Side Visual Review

This skill exists because picking between options requires *looking at
them together*, not in sequence. Reading one image then scrolling up to
re-read the previous one is how subtle differences get missed. Compare
loads them simultaneously and grades them against the same rubric.

It is **readonly** — it never writes to `project.json` or any asset
file. Use it freely for decision support; the user still drives all
state changes through `/slot-step-02` (key art approval),
`/slot-step-03` (symbol approval), etc.

## When to use which mode

| Situation | Mode |
|---|---|
| User has generated 3–6 iterations of one asset and needs to pick one to lock | **ITERATION** |
| User wants to verify the symbol set still reads as a clean tier gradient | **ASSET** |
| User wants to verify a reskin still feels like the same game as the source | **CROSS-PROJECT** |
| User asks "which is better" without naming the inputs | Ask which mode they want, then proceed |

Default to **ITERATION** when the user names two or more filenames from
the same project. Default to **ASSET** when the user names asset IDs
(HP1, LP1, WD1…) without iteration numbers. Default to
**CROSS-PROJECT** when the user names two project folders / GameIDs.

## Startup protocol

Follow `shared/project_memory.md` → "Skill startup protocol", including
the "no active project — guide through setup" pattern.

1. Resolve the active project from `~/.h5g-slot-active-project.json` or
   from the user's GameID arg. **If none exists**, the user is asking
   to compare assets that don't exist — route to `/slot-step-01` to
   set up a project, then explain that there's nothing to compare yet
   and surface the relevant design skill (likely `/slot-step-02` for
   key art iterations, which is the most common comparison target).
   Resume the comparison here once at least two candidates exist.

   For **CROSS-PROJECT mode**, also resolve the second project the
   same way. If the user names a second project that doesn't exist on
   disk, ask them to point you at the right path or GameID — don't
   substitute a fabricated location.
2. Load `project.json` from each project in scope.
3. Detect mode (or accept user override).
4. Do **not** modify anything. This skill writes no JSON, generates no
   art, calls no MCP generation tools. The "guide through setup"
   handoff above is the only thing that routes the user to another
   skill, and even that doesn't modify state from inside this skill.

## Workflow

### Step 1 — Resolve the comparison set

Based on mode:

**ITERATION mode** — single asset slot, multiple iterations:
- Pick the asset (key art, sheet, a specific symbol ID, a specific UI
  surface, a specific background variant).
- Read its `iterations` array from `project.json` and select 2–6 of
  them. If the user named specific filenames, use exactly those. If
  they said "all iterations of HP1", use the whole array.
- If `approved` is already set, mark which one is currently approved
  so the user sees the baseline.

**ASSET mode** — different assets within one project:
- Pick the asset slots (e.g. "all approved symbols",
  "HP1 + MP1 + LP1 to verify the gradient", "all three logo lockups").
- Read each slot's `approved` filename. Skip any that are `null` with
  a one-line note ("HP2 has no approved iteration yet — comparing the
  rest").

**CROSS-PROJECT mode** — same slot, two projects:
- Resolve `project_root` for both projects.
- Pick the asset slot to compare (typically `key`, `logo_hero`, or a
  specific HP).
- Read the `approved` filename from each project's `project.json` for
  that slot. If either is `null`, ask the user to name the iteration
  explicitly (`Key_Art_002` vs `Key_Art_005`).

### Step 2 — Build absolute paths

Paths in `project.json` are stored as relative-to-project-root strings
that include the category subfolder (e.g. `"Symbol_Art/HP1_002.png"`,
`"Key_Art/Key_Art_003.png"`). Resolve each one to an absolute path
before passing it to the Read tool:

```
absolute = path.join(project.project_root, relative_path)
```

This is one `path.join` call — the stored string already encodes the
subfolder, so the comparison skill doesn't need to know the
category-to-folder mapping. Just resolve and read.

For CROSS-PROJECT mode, each project's stored paths resolve against
*that project's* root, not the active one. This matters when a user
has the Phoenix project active and asks to compare against the Jungle
Kingdom project — Jungle Kingdom files resolve against the Jungle
Kingdom root.

### Step 3 — Show the comparison inline

Read every image in the comparison set with the `Read` tool. Claude
Code renders PNGs inline in chat, so all of them appear in one view.
Read them in a deliberate order — the order itself communicates
intent:

| Mode | Order |
|---|---|
| ITERATION | Chronological by filename index (`Key_Art_001` → `Key_Art_002` → `Key_Art_003`) so the user sees the evolution. Mark the currently-approved one if any. |
| ASSET — tier check | Tier order, highest value first: Jackpot → Wild → Scatter → HP1 → HP2 → MP1 → MP2 → LP1 → … → LP6 |
| ASSET — UI surface trio | Hero → Standard → Compact for logos; Bezel → HUD → Paytable for chrome; Small → Medium → Big → Mega → Epic for banner tiers |
| ASSET — backgrounds | Base → Free-spins → Bonus → Pick-me → Wheel |
| CROSS-PROJECT | Source-of-truth project first, then the other one(s) |

Echo the absolute path on its own line below each image, the same way
`shared/nb2_prompting.md` → "After every generation call" prescribes.
This lets the user open the file in their image viewer if they want a
larger look.

### Step 4 — Grade each candidate against the rubric

For each candidate in the set, score against the applicable rubric.
Pick the rubric by what's being compared, not by mode:

| Asset type | Rubric source |
|---|---|
| Key art iterations | `shared/qa_preflight.md` Gate 1 universal checks + `shared/art_principles.md` §1 (the ten core principles — especially #5/#6/#7/#8) and §7 ("Background" bullet for three-layer composition + vignette) |
| Symbol iterations | `shared/qa_preflight.md` "Symbol-specific pre-generation checks" + "Quick-grade table" + `shared/art_principles.md` §3 (symbols), §3.5 (cell-fill by tier), §10 ("Per-symbol" checklist) |
| Full symbol set (tier gradient) | `shared/art_principles.md` §10 ("Per-set" checklist), `shared/qa_preflight.md` "Visual hierarchy awareness" + "Between symbols: hierarchy check", plus the auto-RED escalations from `skills/slot-step-08/SKILL.md` Step 4 |
| WYS / SF / compound-prefix iterations (`WY*`, `WYS*`, `SF*`, `BWY*`, `WJP*`, `WDWY*`, `WDSF*`, `MUWD*`, `MUWDBO*`, `SFWY*`, `DHP*`) | The Symbol-iterations rubric above applies (silhouette, tier fill, palette warmth, style match), PLUS family-specific role discipline from `shared/symbol_vocabulary.md` "Routing by manifest role, not literal prefix" and the family template's role-overlay table — `skills/slot-step-03/COIN_TEMPLATE.md` (WYS family, 8 brief-driven roles) or `skills/slot-step-03/MYSTERY_TEMPLATE.md` (SF family, 14 brief-driven roles). Compounds: grade against the **dominant** family first, then check the secondary overlay per `skills/slot-step-03/SKILL.md` "Compound prefixes" table. The brief's `mechanic` field is the canonical role selector — a candidate that nails the family silhouette but the wrong role overlay is still a miss. |
| Background iterations | `shared/art_principles.md` §7 ("Background" bullet — three-layer composition, vignette), `shared/qa_preflight.md` "Symbol/environment exclusivity", and `skills/slot-step-05/SKILL.md` Step 5 inline QA check list |
| UI surface iterations | `shared/art_principles.md` §7 ("UI / HUD" bullet — touch targets, opacity, chrome ranks below symbols), `shared/qa_preflight.md` Gate 1 universal checks + Gate 2 post-generation check |
| Avatar iterations | `skills/slot-step-08/QA_RUBRIC.md` "Per-avatar rubric" + the avatar discipline rules in `skills/slot-step-06/AVATAR_TEMPLATE.md` |
| Avatar cast (multi-character consistency) | `skills/slot-step-08/QA_RUBRIC.md` "Per-cast checks" + `skills/slot-step-06/AVATAR_TEMPLATE.md` "Cross-cast consistency check" |
| Logo trio (hero/standard/compact) | `skills/slot-step-06/LOGO_TEMPLATE.md` — same wordmark, palette family, visible complexity reduction |
| Cross-project key art | `shared/art_principles.md` §10 ("Per-prompt") + brand consistency check (palette family, style_lock match) |

For each candidate, produce **one short paragraph** noting:
- What it does well
- What it does worse than the others in the set
- Any auto-RED finding (LP gold, mixed LP families, tier inversion,
  silhouette unreadable at thumbnail, etc.) — these dominate scoring

### Step 5 — Produce the comparison report

Output the report inline in chat (do NOT write a file to the project
folder — this skill is readonly). Structure:

```markdown
# Comparison report — {mode}: {what was compared}

Project(s): {GameID}_{username} {and second project for CROSS-PROJECT}
Comparison set: {N} candidates
Generated: {ISO timestamp}

---

## Side-by-side

[The N images already rendered inline above, in the order from Step 3]

---

## Per-candidate notes

### {filename_1} {(currently approved if applicable)}
- Strengths: {one-line}
- Weaknesses vs others in set: {one-line}
- Rubric findings: {bullet list — flag any auto-RED in **bold**}

### {filename_2}
- …

{etc.}

---

## Winner (if applicable)

{For ITERATION mode and logo-trio ASSET mode, name a winner with a
one-sentence justification grounded in the rubric. For full-symbol-set
ASSET mode and CROSS-PROJECT mode, summarize "the set reads as
coherent" / "the reskin holds up" instead of picking a winner —
those modes are diagnostic, not selection.}

---

## Recommended next action

{One sentence. Examples below.}
```

**Examples of the "Recommended next action" line:**

- ITERATION (key art): `"Lock Key_Art/Key_Art_003.png as the style anchor by approving it in /slot-step-02."`
- ITERATION (symbol): `"Approve Symbol_Art/HP1_002.png — say 'approve HP1_002' to set assets.symbols.HP1.approved."`
- ASSET (tier check passed): `"Tier gradient is clean — proceed to /slot-step-05 (backgrounds) or /slot-step-08 (audit)."`
- ASSET (tier check failed): `"Re-run /slot-step-03 for MP1 — its warmth is too close to HP2 and the gradient breaks at the HP→MP boundary."`
- CROSS-PROJECT (reskin holds): `"Reskin is consistent — same hero silhouette, same value hierarchy, distinct palette. Safe to ship."`
- CROSS-PROJECT (reskin drifted): `"The new wild lost its category break — restate the WD palette-break rule and re-run /slot-step-03 for WD1 in the new project."`

### Step 6 — Offer the user the next move

End with a short question that lets them act on the report:

```
Want me to:
  - Walk through the rubric findings for any single candidate in more detail?
  - Compare a different subset of these assets?
  - Move on to {recommended next slash command}?
```

Don't run the next command yourself — surface the choice and let them
trigger it. This keeps the readonly contract clean.

## What this skill does NOT do

- **No state writes.** It does not set `assets.<slot>.approved`, does
  not append to `iterations`, does not touch `style_anchor`. The user
  drives those decisions through the per-step skills.
- **No generation.** It does not call `nb2_generate`, `nb2_edit`,
  `nb2_upscale`, `nb2_smart_resize`, or any `gpt2_*` tool. If the
  comparison shows a candidate needs improvement, route the user to
  the appropriate generation skill — don't generate from here.
- **No audit report.** Cross-asset audit with a written `QA_NNN.md`
  report is `/slot-step-08`'s job. This skill produces a transient
  inline report only.
- **No iteration loop.** It scores what's already on disk. If the user
  wants to generate more candidates and compare again, they re-run
  the generation skill and then re-run this one.

## Hard rules

- **Readonly.** This skill produces a transient inline report only.
  It does not write `project.json`, does not modify any asset record,
  does not create files in the project folder, and does not call any
  MCP generation tool. (Reading is fine — the Read tool renders
  images for comparison; that's the whole point of the skill.)
- **Show the images.** Use the Read tool on every absolute path so
  Claude Code can render them inline. Don't grade from filenames alone.
- **Cite the rubric.** Every finding traces to a specific section of
  `shared/art_principles.md`, `shared/qa_preflight.md`, or a per-step
  SKILL.md. Vague aesthetic claims ("this one feels nicer") are not
  scoring criteria — name the principle.
- **Auto-RED dominates.** A candidate with any auto-RED escalation
  (LP gold, mixed LP family, broken tier, unreadable silhouette) loses
  to one without, regardless of polish.
- **No invented assets.** If a filename isn't actually in the project
  folder, say so and stop. Never grade a hypothetical asset.

## References

- `shared/project_memory.md` (asset record shape, path resolution rules)
- `shared/qa_preflight.md` (per-asset rubrics)
- `shared/art_principles.md` (the foundational design principles every
  rubric flows from — especially §3, §3.5, §7, §10)
- `shared/symbol_vocabulary.md` (family + role model, including
  routing by manifest role for WYS/SF/compound prefixes — needed for
  the WYS/SF/compound rubric row above)
- `shared/nb2_prompting.md` §9.2 (master prompt structure — read this
  when grading a candidate's prompt construction, e.g. to confirm
  the style anchor was prepended verbatim)
- `skills/slot-step-08/QA_RUBRIC.md` (cross-asset rubric — fall through
  to this when grading sets, not individual candidates)
- `skills/slot-step-06/LOGO_TEMPLATE.md` "Cross-lockup consistency check"
  (canonical guidance for logo trio comparisons)
- `skills/slot-step-06/AVATAR_TEMPLATE.md` (canonical avatar discipline
  + "Cross-cast consistency check" — fall through for avatar-iteration
  and avatar-cast comparisons)
