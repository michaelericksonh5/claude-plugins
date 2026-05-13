---
name: slot-step-01
description: STEP 1 — Lock the game brief (theme, palette, style, tier plan, symbol manifest) into project.json. This is the foundation every later skill reads. Run after /slot-step-00 (if you have a GDD) or as the first step if pitching a fresh concept. Always run before /slot-step-02.
---

# Step 1 — Game Brief

This is the foundation of every project. The brief locks theme, palette,
style, tier structure, and the full symbol manifest. The brief captures
**design intent**; at lock time it's mirrored into `project.json`,
which is the **runtime canonical state** every other skill (02 through
10) reads. When the two ever disagree, `project.json` wins — see
`GAME_BRIEF_TEMPLATE.md` for the full contract. Getting the brief
right here is cheap; getting it wrong is expensive because every
downstream skill inherits the locked values via `project.json`.

## Startup protocol

Follow the standard startup from `shared/project_memory.md`:

1. **Resolve project.** Did the user pass a GameID arg? Use it. Otherwise
   read `~/.h5g-slot-active-project.json`. If neither exists, ask the user
   for a GameID and create the project folder.
2. **Construct project root.** Resolve `<PROJECT_BASE>` per
   `shared/project_memory.md` (env var → H5G Drive Stream → `~/slot-art-projects/`),
   then join `<PROJECT_BASE>/{GameID}_{username}/`. `username` comes from
   `os.userInfo().username` — never hardcoded.
3. **Load existing state.** If `project.json` exists, this is an iteration —
   show the user what's locked and ask what to change. If not, create from
   scratch (or seeded from `/slot-step-00` output).

## Workflow

### Step 1 — Determine inputs

Either the user has a GDD (run `/slot-step-00` first if so), or they
have a pitch. Ask once for whichever is missing.

### Step 2 — Lock the brief fields

Required fields (full schema in `GAME_BRIEF_TEMPLATE.md`):

- `game_name` — user-facing theme name, NEVER the internal codename
- `mood` — 1–2 words
- `theme_summary` — ≤ 2 sentences
- `style_lock` — exactly one phrase from `shared/nb2_prompting.md` §9.4
- `palette_leads` — `primary`, `accents`, `forbidden_on_lp` (named colors only, no hex)
- `grid` — e.g. `"5x4"`
- `tier_plan` — canonical baseline: 3 specials + 2 HP + 2 MP + 5–6 LP.
  One LP family. Modern feature-rich games (Loot Link, Hold-and-Spin,
  Billionaire's series) ship 20–45 symbols including WYS/SF
  feature-token families — don't force them down to 13.
- `wild` — what it IS, how it BREAKS the theme
- `scatter` — label and shape (or note that the game uses a `WY` symbol with the scatter role from the WYS family)
- `jackpot_tier_names` — when the game has jackpot symbols, set this
  explicit mapping (`{"JP1": "Grand", "JP2": "Major", "JP3": "Minor",
  "JP4": "Mini"}` for the most common modern ordering — but check the
  GDD; 9 of 11 catalog games use JP1=Grand but a few use JP1=Mini)
- `symbol_manifest` — full schema `{id, tier, family, subject, role,
  mechanic, notes}` for every symbol the game ships. **Walk every
  symbol** including the WYS / SF families, the jackpot tiers, and
  any compound prefixes (BWY, WJP, etc.) — see Step 2b below
- `mode_list` — `["base", "free spins", "bonus pick-me", "wheel", ...]`
- `rtp` — informational only

### Step 2b — Walk the full symbol manifest

The catalog of 26 shipped H5G games shows modern feature games carry
**20–45 distinct symbols** including extensive WYS / SF feature
families and compound prefixes. Don't shortcut the manifest to just
HP/MP/LP/Wild/Scatter — that misses the actual production complexity.

When the user has a GDD, the manifest comes from `/slot-step-00`'s
GDD extraction (which maps GDD prose into the family + mechanic
fields). When the user is pitching fresh without a GDD, walk them
through every family the game uses:

1. **Pay tiers (always)** — HP1/HP2 (2 high-pay characters or iconic
   objects), MP1/MP2 (2 mid-pay objects), LP1–LP6 (5–6 low-pay; ask
   whether card royals, themed objects, gems, or suits).
2. **Wild (almost always)** — WD1 standard, plus any variants (WD2
   sticky, WD3 expanding, etc.). For each variant, capture the
   `mechanic` (sticky / stacked / expanding / walking / respin /
   transforming / multiplier / duplicating / scatter-wild-hybrid).
3. **Scatter / Bonus** — either a legacy `SC` symbol OR a `WY`
   symbol with `mechanic: scatter` (newer H5G pattern). Plus
   optionally a `BO` symbol if the game has a separate bonus
   trigger.
4. **WYS family (most modern feature games)** — Ask: "Does the game
   have coins, portals, or spherical feature tokens?" If yes, walk
   every `WY<N>` / `WYS<N>` the GDD specifies. For each, capture
   the role (hold-and-spin coin, WYSIWYG collector, scatter, random-
   wilds shooter, collector+multiplier, adder, HP-equivalent payout,
   Loot Link trigger). The catalog shows games ship 1–9 WYS symbols.
5. **SF family (Loot Link / Hotspot / Mystery games)** — Ask: "Does
   the game have hotspot multipliers, collectors, path-formers, or
   mystery symbols?" If yes, walk every `SF<N>` and capture the role
   (mystery transform / hotspot multiplier or adder or combiner or
   collapse or persist / upgradable collector / immediate-payout
   collector / bonus value collector / transforming collector /
   path-forming prize / lock-and-respin / jackpot coin / bonus-game
   trigger).
6. **Jackpot tiers (when present)** — Walk JP1 through JP4 (or
   JP1–JP6 for 6-tier games). Explicitly set
   `brief.jackpot_tier_names` BEFORE filling the manifest entries
   so the tier labels are consistent. Default to JP1=Grand for newer
   games unless the GDD says otherwise.
7. **Loot Link family (when the game has Loot Link / Hotspot
   mechanics)** — Either via the canonical COL / ACT / HOT_*
   prefixes OR via generic SF / WY / BWY labels (the catalog shows
   real GDDs use both). Capture the mechanic per symbol.
8. **Blocker (cluster/grid-clear games)** — BL standalone, OR BL1
   and BL2 if the game uses mode-specific blockers or damage-tier
   blockers.
9. **Pay multipliers (when present)** — D2_HP1, D3_HP1, SPLIT_HP1,
   MULT_x10, DHP1 (H5G alias for D2_HP1), etc.
10. **Pachinko / Drop Zone (when the game is pachinko-style)** —
    BALL, PEG, BUCKET_x100, etc.
11. **Compound prefixes (modern combo games)** — BWY (bonus+WYS),
    WJP (wild+jackpot), WDWY (wild+WYS scatter-wild hybrid), WDSF
    (wild+SF), MUWD (multiplier wild), MUWDBO (multiplier wild +
    bonus), SFWY (SF+WYS). When the GDD describes a symbol that
    does two things, use a compound prefix rather than a single
    primitive — the visual will reflect both roles.
12. **Replacement (R1+)** — only if the GDD calls it out.

Full prefix vocabulary + family routing lives in
`shared/symbol_vocabulary.md`. The manifest's `mechanic` field is
what the art skills later read to pick the right template overlay,
so capture it specifically (don't write "TBD" — ask the user instead).

### Step 3 — Build the Style Anchor

Construct a single ~60–90-word block of game-wide discipline that will
be prepended verbatim to every future NB2 prompt (see
`shared/nb2_prompting.md` §9.2.1). Fill the template with this brief's
values:

```
You are generating art assets for a mobile slot machine game ("<game_name>"
— <theme_summary>). Every output must be optimized for small phone
screens — every element must be recognizable by silhouette alone when
small on a phone. Use bold, clean shapes — no intricate micro-textures,
no dense filigree that collapses at thumbnail size. High contrast between
foreground and the flat background. Warm saturated colors signal high
pay; cool muted colors signal low pay. Gold is reserved for premium and
special symbols only. Maintain a consistent <style_lock> rendering
technique across the entire set.
```

Save the filled-in string to **`project.json.style_anchor.text`** — this
is the canonical location every downstream skill reads (see the field
contract in `shared/project_memory.md` → "`style_anchor` field contract").
Mirror the same string to `game_brief.json.style_anchor` for human
readability when the brief is reviewed standalone, but treat
`project.json.style_anchor.text` as the source of truth. Do NOT write it
under `project.json.brief` — that field holds the structured brief
(theme, palette, manifest…), not the style anchor.

### Step 4 — Confirm with user

Show the brief AND the style anchor, ask for sign-off. Get explicit
"lock it" before writing.

### Step 5 — Persist

Atomic-write to BOTH:
- `{project_root}/game_brief.json` — human-readable mirror (includes the
  full structured brief AND `style_anchor` as a string for convenience)
- `{project_root}/project.json` — the master state. Update these fields:
  - `brief` — the full structured brief (theme, palette, manifest, …)
  - `style_anchor.text` — the 60–90-word block from Step 3 (canonical
    location every downstream skill reads)
  - `current_step: "brief_locked"`
  - `next_step: "/slot-step-02"`
  - `updated_at: <ISO timestamp>`

Update `~/.h5g-slot-active-project.json` to point here.

### Step 6 — Next step nudge

```
✓ Step 1 — Game Brief locked.
  Game        : Phoenix of Ardashir
  Mood        : mystical regal
  Style lock  : stylized semi-realistic slot game art
  Palette     : deep midnight indigo with antique gold and burning crimson
  Symbols     : 13 (3 special, 2 HP, 2 MP, 6 LP card royals)
  Saved to    : <project_root>/game_brief.json + project.json
  Folder: <project_root>
  Open:   file:///<project_root with / separators>

Next: run `/slot-step-02` to generate the master key art.
The approved key art becomes the visual style anchor for every later asset.

Type `/slot-` to see the full numbered workflow.
```

## Hard rules

- **Never** put internal GDD codenames anywhere creative-facing
- **Never** describe palette in hex — named colors only
- **Never** mix LP families
- **Style lock must be exactly one phrase**, not a list
- If the GDD is silent on a field, mark it `null` and surface it as an open question

## References

- `shared/project_memory.md` (state schema, startup protocol)
- `shared/asset_naming.md` (file conventions)
- `shared/nb2_prompting.md` §9.4 (style library), §9.8 (brief fields)
- `shared/art_principles.md` §3 (tiers), §4 (palette construction)
- `GAME_BRIEF_TEMPLATE.md` (full schema and example)
