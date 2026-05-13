---
name: slot-step-08
description: STEP 8 — Final production audit for a complete deliverable. Reviews the full symbol set, background suite, or UI collection as a unified whole. Each generation skill does inline checks per asset; this skill does cross-asset consistency review and produces a structured RED/YELLOW/GREEN sign-off report for handoff. Run when a set is done. Use when the user asks to "audit the symbols", "QA the art", "check if this is production-ready", "review the full set", "get a sign-off report", "is this ready to ship", or "run the final check".
---

# Step 8 — Final Production Audit

Each generation skill (slot-03 through slot-07) runs pre-generation
validation and inline post-generation checks. Those gates catch blocking
issues per asset before moving on. This skill is for what those inline
checks cannot see: the full set read as a unified whole.

Run this at:
- End of a full symbol set
- End of a background suite
- Before client/stakeholder handoff
- After NB2 edit/upscale (slot-09) or smart-resize (slot-10), to confirm
  the change didn't break anything

## Startup protocol

Follow `shared/project_memory.md` → "Skill startup protocol", including
the "no active project — guide through setup" pattern.

1. Resolve active project. **If none exists**, the user is asking to
   audit something that hasn't been built — route to `/slot-step-01`
   to set up a project, then explain that there's nothing to audit
   yet and surface the next reasonable step (`/slot-step-02` to
   generate key art). The audit can run once any assets are approved.
2. Load `project.json`, `game_brief.json`.
3. Read all references:
   - `style_anchor.key_art_path` (the original locked anchor — if
     unlocked, route to `/slot-step-02` first since the audit grades
     consistency against the anchor)
   - GDD source images from Drive if `gdd_source.file_id` is set and
     the brief's color direction feels uncertain
4. List all approved assets in scope. If literally nothing has been
   approved yet, tell the user honestly: there's nothing to grade.
   Suggest running the relevant design skill first.

## Workflow

### Step 1 — Identify deliverable scope

Ask user:
- **Symbol set** — all approved per-symbol PNGs + the contact sheet
- **Background suite** — all variants
- **Avatar cast** — every approved in-game animated character
  (`assets.avatars.Avatar1`–`Avatar5`). Games with zero avatars skip
  this scope.
- **UI collection** — all UI surfaces, including any approved bonus
  wheels in `assets.ui.wheels.*` (jackpot / bonus / multiplier /
  pickem). Wheels grade against their own rubric — see Step 3 and
  `QA_RUBRIC.md` "Per-wheel rubric".
- **Wheel collection** — only the bonus wheels, when the user wants a
  focused wheel sign-off (e.g. after iterating jackpot + bonus +
  multiplier wheels together). Games with no wheels skip this scope.
- **Full cross-asset review** — symbols + background + avatars + UI
  (including wheels) together
- **Final sign-off** — everything in the project, with a written report

### Step 2 — Read all assets in scope

Use the Read tool to visually inspect every image. Do not summarize from
filename — actually look at each one.

For symbol sets, read in tier order: Jackpot → Wild → Scatter → HP1 → HP2 →
MP1 → MP2 → LP1 → ... → LP6.

For avatars (when present), read all of `Avatar1` through `Avatar5` in
numeric order — this is the order `/slot-step-06` generates them, and
it usually matches role hierarchy (lead → sidekick → supporting cast),
which is the most useful read order for cross-cast consistency grading.

For bonus wheels (when present), read them in this order: jackpot →
bonus → multiplier → pickem. Wheels are full single-graphic
deliverables (outer frame · slices · hub · pointer), so each one is a
single PNG in `Wheels/`. Read `brief.jackpot_tier_names` BEFORE
opening the jackpot wheel so you can grade whether the slice labels
match the brief's tier ordering (`JP1` is not always `Grand`).

### Step 3 — Grade

**Read `QA_RUBRIC.md` for the full per-surface tables and edge cases.**
The rubric is the canonical source. The summaries below are pointers for
quick reference at grading time — they intentionally don't repeat every
edge-case row from the rubric. If anything below feels under-specified
for an asset you're grading, fall through to `QA_RUBRIC.md`.

| Scope | What to check (summary — see QA_RUBRIC.md for full tables) |
|---|---|
| **Symbol set — tier gradient** | Cover the labels and ask "which is higher value?" — the answer must be obvious at HP1→HP2, HP2→MP1, MP→LP. Wild clearly breaks category + palette. Scatter is a circular badge identifiable as a trigger. |
| **Symbol set — LP discipline** | Zero gold/amber/warm trim on any LP. LP family consistent (all card royals, or all gems, etc. — never mixed). |
| **Symbol set — export BG** | HP/Wild/Scatter/Jackpot on flat solid black; LP on flat solid white; no gradients or patterns. |
| **Symbol set — style** | All symbols share `style_lock`. Light direction consistent (upper-left ~10 o'clock). |
| **Symbol set — readability** | Clear silhouette at thumbnail size on every symbol. |
| **Backgrounds** | Bottom 30% dark on all variants. Reel zone dimmed. Three-layer depth. Free-spins more saturated/warm than base. Bonus has more drama. BG palette recedes behind symbol palette. |
| **Avatars** (when present) | All on flat solid black, neutral idle pose, 1:1 aspect. Same `style_lock` and palette family as the symbol set — no photoreal avatars in a stylized game. Cast brightness/saturation sits between HP and MP intensity (not louder than the reel set). Multi-avatar games: same key light direction, same rendering technique, palette family shared but each avatar uses a different accent. Avatars must NOT replicate any symbol-set subject (symbol/environment exclusivity also applies here). |
| **UI** | Chrome ranks below symbols in brightness and visual weight. Bezel has transparent/open center. Banner tiers distinguishable across ≥2 axes (see `skills/slot-step-06/BANNERS_TEMPLATE.md`). Touch targets visually generous. Logo readable at thumbnail. |
| **Wheels** (when present) | Single graphic per variant (outer frame + slices + hub + pointer in one PNG, NOT per-slice files). Flat solid black background. Slice color gradient follows the pay spectrum: cool slate/teal for low, transitional sage/amber for mid, ember/crimson for high, gold for jackpot/max — jackpot slice clearly dominates peripheral vision. Jackpot wheel's tier labels match `brief.jackpot_tier_names` exactly (a `Grand` label on a `JP1` slice when the brief maps `JP1` differently is a RED). Center hub recedes; slice values are readable at the wheel's expected on-screen size. See `QA_RUBRIC.md` "Per-wheel rubric". |
| **Lobby tile — competitor-grid check** | Has the lobby tile been reviewed inside a 3×4 or 4×5 mockup of competitor tiles at thumbnail size (~200 px)? If not, this is an automatic YELLOW. See `skills/slot-step-06/LOBBY_TILE_TEMPLATE.md` "Competitor-grid mockup discipline" for the procedure. The tile must draw the eye within 500 ms, look categorically different from neighbors, and have a readable title wordmark at thumbnail size. |
| **Production handoff readiness** | If the audit is for the final production sign-off (not a mid-project check), the production-handoff checklist in `shared/production_handoff.md` should be reviewable — atlas-friendly padding, pngquant/oxipng optimization, sRGB color space confirmed, banding check on gradients. These are technical-delivery prerequisites, not creative ones. |
| **Cross-asset** | Everything feels like one cohesive world. No surface competes at wrong hierarchy level. Palette family consistent. |
| **Symbol/environment exclusivity** | No symbol-set subject is repeated across BG/frame/UI as a recurring decorative motif. See `shared/qa_preflight.md` "Symbol/environment exclusivity" for the rule and why it matters. |

### Step 3.5 — Measurement-backed checks (numeric, deterministic)

The prose grading above relies on Claude's visual judgment — useful
for subjective calls ("does this feel premium?"), but stochastic and
inconsistent for the rules that are actually numeric. This step runs
`nb2_measure` on every approved asset in scope, embeds the results
into `project.json.assets.*.metrics_summary`, and applies the
deterministic checks defined in `QA_RUBRIC.md` → "Measurement-backed
rubric (deterministic numeric checks)".

**1. Measure approved assets.** For each slot in scope, if `approved`
is non-null and (`metrics_summary` is null OR `metrics_summary.last_measured`
is older than the approved iteration's `timestamp`):

```
nb2_measure({ source: path.join(project_root, <approved path>) })
```

The MCP tool returns the metrics block and writes a sidecar
`<basename>.metrics.json` next to the PNG. Embed the **summary subset**
(`dominant_color_oklch`, `fill_pct`, `bg_uniformity_score`,
`edge_density`, plus `measured_iteration` and `last_measured`) into
`project.json.assets.<slot>.metrics_summary` per the schema in
`shared/project_memory.md` → "metrics_summary field".

Batch them: a 13-symbol set is 13 calls. Each call is ~200-400 ms on a
2K image; the whole set takes 5-10 seconds. If `metrics_summary` is
already fresh (`last_measured` ≥ approved's `timestamp`), skip the
measurement — the prior data is still valid.

**2. Apply the deterministic checks** from `QA_RUBRIC.md` →
"Measurement-backed rubric". These produce RED / YELLOW findings that
sit alongside (and don't replace) the visual-judgment ones from Step 3:

- **LP warmth scan.** For every LP slot's `metrics_summary.dominant_color_oklch`,
  flag RED if any cluster has `h ∈ [30°, 90°]` AND `c > 0.05` AND
  `pct > 0.05` (a meaningful warm-gold/amber region). LP discipline
  is the most common failure mode and the most testable numerically.
- **Tier-pairwise saturation step.** For adjacent tiers (HP1↔HP2,
  HP2↔MP1, MP↔LP), compute the difference in dominant-color OKLCH
  chroma. Flag YELLOW if the gap is `< 0.04` (≈15 points on the
  traditional 100-point sat scale); flag RED if `< 0.02` (tiers
  visually indistinguishable). Sourced from `art_principles.md` §10
  "Per-set" + `QA_RUBRIC.md` "Per-set rubric → Saturation step".
- **Tier-pairwise lightness gap.** For adjacent tiers, compute the
  difference in dominant-color OKLCH lightness. Flag YELLOW if `< 0.10`;
  flag RED if `< 0.05`. Sourced from `art_principles.md` §10 and the
  per-set rubric.
- **Background uniformity.** For every slot whose surface should have
  a flat BG (HP/MP/LP/Wild/Scatter/Jackpot/avatars/wheels), flag RED
  if `bg_uniformity_score < 0.85`. Flag YELLOW if `< 0.95`. Catches
  gradient backgrounds the visual gate sometimes misses.
- **Fill % by tier.** Compare `fill_pct` to the expected band from
  `QA_RUBRIC.md` "Fill % by tier". Flag YELLOW if outside the band
  by more than `±0.05` (5%); flag RED if outside by more than `±0.10`.
- **Wild palette-break verification.** Compute the OKLCH distance
  between the Wild's dominant color and the brief's `palette_leads.primary`
  (after converting the palette swatch to OKLCH). Flag RED if the
  distance is `< 0.15` — wild's color must actually break the theme,
  not just feel different.

**3. Inline the numeric findings into the report** alongside the
visual ones. Each finding should cite both the rule
(`art_principles.md` §X / `qa_preflight.md` Y) AND the measured
number (e.g. "LP3 shows warm cluster at h=51°, c=0.082, pct=0.07 —
RED per `QA_RUBRIC.md` measurement-backed rubric § LP warmth scan").

**When measurement isn't available.** If `nb2_measure` fails (missing
key, file unreadable, etc.), fall through to visual-only grading from
Step 3 and note in the report that numeric verification was skipped.
Don't block the audit — measurement is an additive deterministic
layer, not a precondition.

### Step 4 — Auto-RED escalations

Always RED regardless of other grades. `QA_RUBRIC.md` has the full
canonical list (items 1–13); the most common production blockers,
grouped by surface, are:

**Symbol set:**
- Any LP shows gold/amber/warm trim
- HP uses same warmth/saturation as an LP
- Export background has gradient or pattern instead of flat solid
- Wild uses same primary palette as the rest of the set
- Any symbol unrecognizable at 64px thumbnail
- Style varies between two symbols in the same set
- LP family is mixed within one set

**Avatars (when in scope):**
- An avatar has visible baked-in text (nameplate / label / speech bubble)
- An avatar's background is anything other than flat solid black
- An avatar replicates a reel-symbol subject (breaks symbol/environment
  exclusivity — e.g. the HP1 phoenix also appearing as Avatar1)

**Wheels (when in scope) — auto-RED items 11-13:**
- **(11)** Per-slice files exist instead of a single complete wheel
  graphic (outer frame + slices + hub + pointer must be one PNG)
- **(12)** Wheel background is anything other than flat solid black
- **(13)** Jackpot wheel labels contradict `brief.jackpot_tier_names`
  (e.g. the slice for `JP1` says `Grand` when the brief maps
  `JP1 = Mini`, or vice versa)

Plus a rubric-derived RED from `QA_RUBRIC.md` "Per-wheel rubric →
Slice color hierarchy" (not numbered in the auto-RED list because it
falls out of the per-wheel rubric rather than the universal-RED list):
- Wheel slice tier ordering inverts the pay spectrum (e.g. jackpot
  slice is cool slate while a low-value slice is warm gold)

**Mode variants (when any symbol has populated `modes`) — auto-RED items 14-15:**
- **(14)** An LP or MP symbol has a populated `modes` block. LP and
  MP must stay identical across modes per
  `shared/mode_variants.md` per-tier delta rules — recoloring them
  destroys the player's visual baseline. The fix is to delete the
  offending `modes.<mode>` sub-record (and remove the mode-suffixed
  PNG files from the category folder).
- **(15)** Recolor budget exceeded. If **6 or more** symbols across
  the game have populated `modes` blocks, surface RED with the count
  (5 symbols is YELLOW — over the recommended 3-4 budget, designer
  must justify; 6+ is RED). Per `shared/mode_variants.md` "Recolor
  budget".

### Step 5 — Write the report

Save to `{project_root}/QA_Reports/QA_NNN.md`. Scan `QA_Reports/`
(create the folder if it doesn't exist) for existing `QA_*.md`,
increment past the max. The report file is markdown, not PNG, but
follows the same naming convention. Example: first audit →
`QA_Reports/QA_001.md`; re-audit after fixes → `QA_Reports/QA_002.md`.

```markdown
# QA Audit — {game_name}

Date: {ISO date}
Project: {GameID}_{username}
Scope: {what was reviewed}
Overall: RED | YELLOW | GREEN

---

## RED — Blocks handoff
- [specific finding with asset name]

## YELLOW — Needs review before handoff
- [specific finding with asset name]

## GREEN — Confirmed
- [specific finding with asset name]

## Required human visual checks
- [items requiring a person to look at the file on screen]

## Recommended next action
[One sentence]
```

**Overall grade logic:**
- Any RED → overall RED
- No RED, any YELLOW → overall YELLOW
- All GREEN → overall GREEN

### Step 6 — Update state

- Append the relative path (`"QA_Reports/QA_NNN.md"`) to
  `project.json.assets.qa_reports`
- Set `current_step: "audit_complete"`
- Set `next_step` based on overall grade:
  - GREEN → `/slot-step-09`
  - YELLOW or RED → the specific design skill that owns the failing assets
    (e.g. `/slot-step-03` if LP gold contamination, `/slot-step-05` if BG too bright)
- Record the grade in the report itself, not in `current_step`

See `shared/project_memory.md` → "current_step and next_step vocabulary"
for the full canonical list.

### Step 7 — Next step nudge

```
✓ Step 8 — Production Audit: GREEN
  Report: QA_Reports/QA_002.md
  All 13 symbols, 3 BG variants, 5 UI surfaces passed.
  Folder: <project_root>/QA_Reports/
  Open:   file:///<project_root>/QA_Reports/

Next: run `/slot-step-09` to upscale the approved assets to 4K
for production delivery.

Or `/slot-step-10` if you need multi-aspect crops of a hero asset.

Type `/slot-` to see the full numbered workflow.
```

## What this skill does NOT do

- **Does not generate or modify art.** Design skills (03–07) do that.
- **Does not catch per-asset blocking issues.** Inline gates in design skills do that.
- **Does not replace human art director review.** YELLOW items and "Required
  human visual checks" exist because some calls require a person's judgment.

## References

- `shared/project_memory.md`, `shared/qa_preflight.md`
- `shared/art_principles.md` §10 (full checklists), §8 (CVD and contrast)
- `QA_RUBRIC.md` (detailed per-surface tables)
