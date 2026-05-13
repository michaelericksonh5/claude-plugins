---
name: slot-step-00
description: STEP 0 (optional) — Pull a Game Design Document from the team Google Drive, extract theme/mechanics/symbol structure, and seed the project. Run this BEFORE /slot-step-01 if a GDD already exists for this game. Skip directly to /slot-step-01 if you're pitching a new concept without a GDD. Use when the user says things like "grab the GDD", "pull the game design doc", "connect to Drive for [game name]", "bootstrap from the GDD", or "get the GDD for [game]".
---

# Step 0 — GDD Connect (optional)

Pulls a GDD from the team's shared Drive folder and uses it to bootstrap a
new project. After this skill runs, the brief is pre-populated and the
user can review/refine in `/slot-step-01`.

**Prerequisite:** Google Drive must be connected to Claude. If Drive tools
aren't available, tell the user to enable the Google Drive integration in
Claude settings, then reload.

This skill is **optional**. Skip directly to `/slot-step-01` if:
- The user is pitching a fresh concept (no GDD on Drive)
- Google Drive isn't connected and won't be in this session
- The user has the GDD content as plain text and prefers to paste it

---

## Startup protocol

Follow the standard startup from `shared/project_memory.md`, with two
caveats specific to step 0:

1. **Active project may not exist yet.** This is often the FIRST step in a
   project's life. If `~/.h5g-slot-active-project.json` is missing, that's
   fine — this skill creates the project. If it points to an existing
   project, ask the user: "Are you bootstrapping a new project, or
   re-syncing the GDD on the active project?"
2. **Drive tools must be present.** Detect Drive MCP tools at startup
   (look for `mcp__*__read_file_content`, `search_files`, etc.). If
   missing, tell the user to enable Google Drive in Claude settings and
   offer to skip ahead to `/slot-step-01` for a manual brief.

If both gates pass, continue to the workflow.

---

## Workflow

### Step 1 — Identify project + GDD

Ask: **"What's the GameID for this project?"** (numeric, e.g. `4470`).

Then ask: **"What's the game name or title of the GDD on Drive?"**

Search the canonical GDD folder
(`https://drive.google.com/drive/folders/1SfzTV7n6CPlNXjMTR-RfRLtXIaJ-wCtr`)
using a two-step approach — GDDs live in per-game subfolders, not as
direct children of the root folder:

**Step 1 — Find the game's subfolder:**
```
parentId = '1SfzTV7n6CPlNXjMTR-RfRLtXIaJ-wCtr' and title contains '<game name>'
```

**Step 2 — Find the GDD inside that subfolder:**
```
parentId = '<subfolder_id_from_step_1>' and title contains 'gdd'
```

**Fallback** — if step 1 or 2 returns empty (shared Drive traversal
limitations), search Drive-wide:
```
title contains 'gdd' and fullText contains '<game name>'
```

**Drive CQL notes for this MCP:**
- Use `parentId = '<id>'` — NOT `'<id>' in parents` (that syntax throws
  "Unsupported query field: parents")
- Do NOT include `trashed = false` — that field is unsupported and causes
  an error
- `parentId` only checks direct children, not nested subfolders — that's
  why the two-step approach is needed

Use the **highest version** if multiple are found. Confirm with the user.

### Step 2 — Read the GDD

Call `read_file_content` with the file ID. `.docx`, `.pdf`, and Google Docs
all return clean text. Do not download or convert to PDF.

### Step 3 — Read reference images (if any)

Search the same subfolder for image files (use the subfolder ID found in
Step 1, not the root folder ID):

```
parentId = '<subfolder_id>' and (mimeType = 'image/png' or mimeType = 'image/jpeg')
```

Call `read_file_content` on each — Claude sees them visually. Use them to
sharpen palette, mood, and style decisions before locking the brief.

### Step 4 — Bootstrap the project folder

Resolve `<PROJECT_BASE>` using the standard order from
`shared/project_memory.md` → "Resolving `<PROJECT_BASE>` at runtime":

1. `SLOT_ART_PROJECT_BASE` env var if set
2. The H5G shared Drive Stream path
   (`H:\Shared drives\Content Management - AI\Production_AI 2\Asset_Creation_Suite\`
   on Windows, the equivalent `/Volumes/GoogleDrive/Shared drives/...` on
   Mac) — only if it exists on this machine
3. `~/slot-art-projects/` per-user fallback

`username` comes from `os.userInfo().username` (or `%USERNAME%` on Windows
/ `$USER` on Mac/Linux as a fallback). Do not hardcode it.

Construct the project root:

```
<PROJECT_BASE>/{GameID}_{username}
```

Create the folder if it doesn't exist. Inside it, create:

- `project.json` — populated from the schema in `shared/project_memory.md`
- `game_brief.json` — partial brief seeded from GDD extraction

Set `~/.h5g-slot-active-project.json` to point to this new project.

### Step 5 — Extract GDD structure into the brief

Pull the following from the GDD text. Mark fields `null` if absent — never
fabricate. The target schema is `skills/slot-step-01/GAME_BRIEF_TEMPLATE.md`
(the seeded `game_brief.json` will be refined in `/slot-step-01`).

| Field in `game_brief.json` | Where to look in the GDD |
|---|---|
| `game_name` | The name as it appears in the GDD — which is always a preproduction codename at H5G (e.g. "Tesla", "Chevy"). Record it as-is for now and always add an open question flagging it: "game_name: GDD uses '[name]' as codename — confirm the player-facing title in /slot-step-01 before locking the brief." Never attempt to infer the visual theme from the codename. |
| `theme_summary` | Overview / concept |
| `grid` | Math spec ("5x3", "5x4", "5x6", "3x5") |
| `tier_plan.lp_family` | Are LPs card royals (`card_royals`), themed objects (`themed_objects`), gems (`gems`), or suits (`suits`)? Most newer H5G games use themed objects. |
| `wild.category` and `wild.breaks_theme_via` | Wild symbol section. Capture what the wild IS and what visually breaks the theme. |
| `scatter.label` and `scatter.shape` | Scatter section. **Note:** many newer games use a `WY` symbol with `mechanic: scatter` instead of a literal `SC` prefix; in that case the scatter info goes on the manifest entry for that `WY<N>`. |
| `jackpot_tier_names` | If the GDD describes jackpot tiers, build the explicit `{"JP1": "<name>", "JP2": "<name>", ...}` mapping. Modern H5G GDDs typically map `JP1` to **Grand** (Billionaire's series, Chevy family, Tesla, Blazing Stampede), but a few use `JP1 = Mini`. Read the GDD carefully — the wrong ordering ships the wrong metallic finish on the wrong tier. |
| `symbol_manifest` | Paytable or art spec table. **This is where the GDD-extraction work concentrates** — see Step 5b. |
| `mode_list` | Feature list (`base`, `free spins`, `bonus pick-me`, `wheel`, `Loot Link`, `Hold-and-Spin`, etc.) |
| `rtp` | Math spec (record only, not used in art prompts) |

### Step 5b — Mapping GDD symbols to the manifest schema

Real H5G GDDs use prose like "the Phoenix bonus coin pays a random
value and contributes to the Loot Link feature" — the extraction
needs to translate that into the structured manifest fields
`{id, tier, family, subject, role, mechanic, notes}` (the brief
schema documented in `slot-step-01/GAME_BRIEF_TEMPLATE.md`). The
`notes` field is optional but useful for GDD prose that doesn't fit
cleanly into `mechanic` — e.g. "only appears in free spins", "links
to the bonus reel". The mapping rules:

| GDD says about a symbol... | Pick `family` | Set `mechanic` to |
|---|---|---|
| "high-pay character" / "premium pay" / "hero symbol" | `HP` | `standard pay` |
| "mid-pay object" / "supporting cast" | `MP` | `standard pay` |
| "low-pay card royal" / "card filler" | `LP` | `standard pay` |
| "wild" / "substitutes for…" | `Wild` | the variant if specified (sticky, stacked, expanding, walking, multiplier, etc.) — else `standard wild` |
| "scatter triggers free spins" with `SC` prefix | `Scatter` | `scatter` |
| "scatter" / "trigger" but the GDD uses a `WY` prefix (Tesla WY1, Bankrush Gamma WY1, Chevy-Lite WY1 pattern) | `WYS` | `scatter` |
| "hold-and-spin coin" / "cash-on-reels coin" | `WYS` | `hold-and-spin coin` |
| "WYSIWYG collector" / "collects values during bonus" / "pays a value when…" with WY prefix | `WYS` | `wysiwyg collector` |
| "random-wilds shooter" / "shoots wilds onto the reels" | `WYS` | `random wilds shooter` |
| "collector with a multiplier" / "pins and accumulates" | `WYS` | `collector + multiplier` |
| "adds value to surrounding/above values" | `WYS` (with WY prefix) OR `SF` (with SF prefix) | `adder` |
| "direct payout symbol" with WY prefix (Billionaire's pattern) | `WYS` | `hp-equivalent direct payout` |
| "Loot Link trigger" with WY prefix | `WYS` | `loot link trigger` |
| "mystery transform" / "reveal" / "closed object that reveals" | `SF` | `mystery transform` |
| "hotspot multiplier" (`HOT_x*` or `SF<N>`) | `SF` (when SF prefix) OR keep `HOT_x*` family | `hotspot multiplier` |
| "hotspot adder / combiner / collapse / persist" | `SF` | `hotspot adder` / `hotspot combiner` / `hotspot collapse` / `persistent hotspot` |
| "upgradable collector" / "gold-bar collector that upgrades" | `SF` | `upgradable collector` |
| "immediate-payout collector" | `SF` | `immediate-payout collector` |
| "bonus value collector" | `SF` | `bonus value collector` |
| "transforming collector" / "collector that turns into a WY" | `SF` | `transforming collector` |
| "path-forming prize" / "Prize Path connection" | `SF` | `path-forming prize` |
| "lock-and-respin trigger" | `SF` | `lock-and-respin trigger` |
| "jackpot coin" / "on-grid coin that triggers jackpot mode" (Tesla SF1, Golden Knight pattern) | `SF` (when SF prefix) OR `Jackpot` (when JP1 prefix) | `jackpot coin` (SF role) or `jackpot trigger (matrix)` (JP role) |
| "bonus-game trigger" with SF or BO prefix | `BO` (when BO prefix) OR `SF` (when SF prefix) | `free spins trigger` / `bonus game trigger` |
| "jackpot tier — Grand/Major/Minor/Mini" | `Jackpot` | `jackpot tier — <TierName>` (use the GDD's name verbatim) |
| "blocker" / "obstacle" / "blank filler" | `Blocker` | `blocker` (or describe the mode if multiple blockers exist) |
| "double / triple / split" with D2_/D3_/SPLIT_ prefix | `SpecialMechanics` | `double pay` / `triple pay` / `split pay` |
| "Double HP" with DHP prefix (Eagles' Flight pattern) | `SpecialMechanics` | `double pay` |
| "pachinko ball / peg / bucket" | `Pachinko` | `pachinko ball` / `pachinko peg` / `pachinko bucket` |
| Compound — symbol does TWO things (bonus + WY payout, wild + jackpot contribution, etc.) | family of the **dominant** role | combined mechanic, e.g. `bonus trigger + coin payout` (for BWY) or `wild + jackpot contribution` (for WJP). Match the canonical `GAME_BRIEF_TEMPLATE.md` worked example wording when in doubt. |

If the GDD uses a prefix not in the documented vocabulary, route by
the symbol's visual description from the GDD's art spec — match to
the closest family, set `family` and `mechanic` accordingly, and
list the prefix under `open_questions` for vocabulary extension
review later.

Store the GDD source in both `project.json.gdd_source` and `game_brief.json.gdd_source`:

```json
"gdd_source": {
  "file_id": "<Drive ID>",
  "file_name": "<filename>",
  "drive_url": "https://drive.google.com/file/d/<ID>/view",
  "version_extracted": "<version>",
  "extracted_at": "<ISO date>"
}
```

### Step 6 — Atomic write + report

Atomic-write `project.json` and `game_brief.json` (write `.tmp`, then rename).

Set `current_step: "gdd_loaded"`, `next_step: "/slot-step-01"`. See
`shared/project_memory.md` → "current_step and next_step vocabulary".

Show a summary table:

```
GameID           : 4470
Project root     : <resolved PROJECT_BASE>/4470_<username>
Game name        : Jungle Kingdom
Grid             : 5x4
Symbols          : 13 (extracted)
Modes            : base, free spins, bonus pick-me
GDD source       : Jungle Kingdom Game Design Document v.0.0.2.docx
Reference images : 3 (visually analyzed)
Open questions   : 2 (style_lock, palette — to be locked in /slot-step-01)
```

### Step 7 — Next step nudge

```
✓ Step 0 — GDD Connect complete.
  Project active: {GameID}_{username}
  Folder: <project_root>
  Open:   file:///<project_root with / separators>

Next: run `/slot-step-01` to lock theme, palette, and tier plan.
Type `/slot-` to see the full numbered workflow.
```

---

## Re-syncing from an updated GDD

If `project.json.gdd_source.file_id` is already set, running this skill again
re-reads the same GDD and shows a diff. User approves changes one by one
before the brief is updated.

---

## When Drive isn't connected

Tell the user to enable Google Drive in Claude settings. Offer to skip
ahead to `/slot-step-01` for a manual brief.

## References

- `shared/project_memory.md` (project state schema, atomic writes)
- `shared/asset_naming.md` (file conventions for the project folder)
- `skills/slot-step-01/GAME_BRIEF_TEMPLATE.md` (target schema)
