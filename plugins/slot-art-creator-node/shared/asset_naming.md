# Asset Naming Convention

Every generated file in a project lives in a **category subfolder** under
`<project_root>`, named so that anyone opening the folder in File
Explorer can find what they want without scanning a flat dump.

```
<project_root>/
├── project.json
├── game_brief.json
├── Key_Art/               ← key art master + crops
├── Symbol_Sheets/         ← full-set contact sheets
├── Symbol_Art/            ← every individual reel symbol
├── Backgrounds/           ← base / freespins / bonus / pickme / wheel
├── Avatars/               ← in-game animated characters (0–5 per game)
├── Bezels/                ← reel frames
├── HUD/                   ← HUD chrome (spin button, balance, bet, win)
├── Paytables/             ← paytable layouts
├── Win_Banners/           ← small / medium / big / mega / epic
├── Bonus_Screens/         ← intro screens for free-spins / pick-me / wheel bonuses
├── Wheels/                ← full bonus-wheel graphics (jackpot / bonus / multiplier / pick-em)
├── Multipliers/           ← multiplier badges by denomination
├── Logos/                 ← hero / standard / compact lockups
├── Lobby_Tiles/           ← marketing thumbnails
└── QA_Reports/            ← audit .md reports from /slot-step-08
```

`project.json` and `game_brief.json` stay at the root — they're
project-wide state, not assets.

---

## Naming rules

1. **Format:** `{Label}_{NNN}.{ext}` — three-digit zero-padded counter
2. **Per-label counter, scoped to the folder:** `HP1_001`, `HP1_002` —
   each label has its own counter, computed by scanning the asset's
   category folder only (not the project root)
3. **No overwrites, ever:** before saving, scan the asset's folder for
   files matching `{Label}_*.{ext}`, find the max number, increment by 1
4. **No metadata in the filename:** no resolution, no aspect ratio, no
   timestamp, no prompt slug. Just the label and the number. (Exception:
   upscaled/resized variants — see "Derived variants" below.)
5. **PNG only** for image assets (use `.md` for QA reports, `.json` for
   manifests and sidecars)
6. **Every PNG gets a sidecar.** `HP1_001.png` is paired with
   `HP1_001.meta.json` containing the prompt, model, provider,
   references, timestamps. Lives next to the PNG in the same folder.
   Written automatically by the MCP server. Never deleted.

---

## Sidecar metadata files

Every generated PNG produces a paired `.meta.json` in the same folder:

```
Symbol_Art/HP1_001.png         ← the image
Symbol_Art/HP1_001.meta.json   ← what produced it
```

Schema (`h5g_asset.meta.v1`):

```json
{
  "schema": "h5g_asset.meta.v1",
  "filename": "HP1_001.png",
  "full_path": "<project_root>/Symbol_Art/HP1_001.png",
  "generated_at": "2026-05-06T16:30:12.345Z",
  "tool": "nb2_generate",
  "provider": "fal.ai",
  "model": "fal-ai/nano-banana-2",
  "prompt": "Phoenix character bust facing front, wings spread, ...",
  "image_size": "2K",
  "aspect_ratio": "1:1",
  "reference_images": ["<project_root>/Key_Art/Key_Art_003.png"],
  "source_image": null,
  "duration_seconds": 12.4
}
```

Why sidecars matter:
- **Provenance.** Anyone can see exactly what prompt + references produced
  any PNG. Critical for QA, iteration, and audit.
- **Repro.** A user can re-run a generation by reading the sidecar and
  passing the same prompt/refs back to `nb2_generate`.
- **Survives copying.** When a user shares the project folder with a
  partner, the sidecars come along.
- **Independent of `project.json`.** If `project.json` is corrupted or
  deleted, the sidecars still tell you what each image is.

The sidecar is written automatically by the MCP server. Design skills
don't need to do anything extra. Failure to write the sidecar never
blocks the generation result; it's logged and ignored.

---

## Label table — folder × label

Every generated asset belongs to exactly one of these category folders.
The skill responsible for generation passes `output_dir = path.join(project_root, "<Folder>")`
to the MCP tool so files land in the right place automatically.

### Key art

| Asset | Folder | Label | Examples |
|---|---|---|---|
| Master key art | `Key_Art/` | `Key_Art` | `Key_Art_001.png`, `Key_Art_002.png` |
| Wide crop (16:9) | `Key_Art/` | `Key_Art_wide` | `Key_Art_wide_001.png` |
| Tall crop (9:16) | `Key_Art/` | `Key_Art_tall` | `Key_Art_tall_001.png` |

### Symbol sheets (contact sheets)

| Asset | Folder | Label | Examples |
|---|---|---|---|
| Full-set contact sheet | `Symbol_Sheets/` | `Sheet` | `Sheet_001.png`, `Sheet_002.png` |

### Symbol art (individual reel symbols — every prefix from `shared/symbol_vocabulary.md`)

| Asset | Folder | Label | Examples |
|---|---|---|---|
| HP1–HP4 symbols | `Symbol_Art/` | `HP1`–`HP4` | `HP1_001.png`, `HP4_002.png` |
| MP1–MP3 symbols | `Symbol_Art/` | `MP1`–`MP3` | `MP1_001.png` |
| LP1–LP6 symbols | `Symbol_Art/` | `LP1`–`LP6` | `LP3_001.png` |
| Wild — standard | `Symbol_Art/` | `WD` or `WD1` | `WD1_001.png` |
| Wild — variants | `Symbol_Art/` | `WD2`, `WD3`, ... | `WD2_001.png` |
| Scatter (classic) | `Symbol_Art/` | `SC` | `SC_001.png` |
| Scatter-Wild hybrid | `Symbol_Art/` | `SW` | `SW_001.png` |
| Coin / Hold-and-Spin | `Symbol_Art/` | `WY1`–`WY4` | `WY1_001.png`, `WY2_001.png` |
| Bonus trigger | `Symbol_Art/` | `BO` | `BO_001.png` |
| Mystery / Special Feature | `Symbol_Art/` | `SF` | `SF_001.png` |
| Blocker / Dead | `Symbol_Art/` | `BL`, `BL1`, `BL2`+ | `BL_001.png`, `BL1_001.png`, `BL2_001.png` (numbered variants when a game ships multiple blocker types for different modes) |
| Jackpot tiers | `Symbol_Art/` | `JP1`–`JP6` | `JP1_001.png`, `JP6_001.png` |
| Replacement | `Symbol_Art/` | `R1`+ | `R1_001.png` |
| Money bag scatter | `Symbol_Art/` | `BAG`, `BAG_BO` | `BAG_001.png`, `BAG_BO_001.png` |
| Money emoji trigger | `Symbol_Art/` | `MOJ` | `MOJ_001.png` |
| Loot Link Collector | `Symbol_Art/` | `COL` | `COL_001.png` |
| Loot Link Activator | `Symbol_Art/` | `ACT` | `ACT_001.png` |
| Hotspot multiplier | `Symbol_Art/` | `HOT_x<N>` | `HOT_x2_001.png`, `HOT_x10_001.png` |
| Hotspot operators | `Symbol_Art/` | `HOT_ADD`, `HOT_COMB`, `HOT_COLLAPSE`, `HOT_PERSIST` | `HOT_ADD_001.png` |
| WYSIWYG variant naming | `Symbol_Art/` | `WYS`, `WYS1`–`WYS2+` | `WYS_001.png`, `WYS1_001.png`, `WYS2_001.png` |
| Bonus + WYS compound | `Symbol_Art/` | `BWY`, `BWY1`+ | `BWY_001.png`, `BWY1_001.png` |
| Wild + Jackpot compound | `Symbol_Art/` | `WJP`, `WJP1`+ | `WJP_001.png`, `WJP1_001.png` |
| Wild + WYS compound (scatter-wild hybrid) | `Symbol_Art/` | `WDWY`, `WDWY1`+ | `WDWY1_001.png` |
| Wild + SF compound | `Symbol_Art/` | `WDSF`, `WDSF1`+ | `WDSF1_001.png` |
| Multiplier + Wild compound | `Symbol_Art/` | `MUWD`, `MUWD1`+ | `MUWD1_001.png` |
| Multiplier + Wild + Bonus compound | `Symbol_Art/` | `MUWDBO`, `MUWDBO1`+ | `MUWDBO1_001.png` |
| SF + WYS compound | `Symbol_Art/` | `SFWY`, `SFWY1`+ | `SFWY1_001.png` |
| Double HP (alias) | `Symbol_Art/` | `DHP`, `DHP1`+ | `DHP1_001.png` |
| Double / Triple base | `Symbol_Art/` | `D2_<base>`, `D3_<base>` | `D2_HP1_001.png` |
| Split symbol | `Symbol_Art/` | `SPLIT_<base>` | `SPLIT_HP1_001.png` |
| Non-wild multiplier | `Symbol_Art/` | `MULT_x<N>` | `MULT_x10_001.png` |
| Pachinko ball | `Symbol_Art/` | `BALL` or `BALL_<tier>` | `BALL_001.png`, `BALL_gold_001.png` |
| Pachinko peg | `Symbol_Art/` | `PEG` | `PEG_001.png` |
| Pachinko bucket | `Symbol_Art/` | `BUCKET_x<N>` | `BUCKET_x100_001.png` |

### Backgrounds

| Asset | Folder | Label | Examples |
|---|---|---|---|
| Base background | `Backgrounds/` | `BG_base` | `BG_base_001.png` |
| Free spins | `Backgrounds/` | `BG_freespins` | `BG_freespins_001.png` |
| Bonus | `Backgrounds/` | `BG_bonus` | `BG_bonus_001.png` |
| Pick-me | `Backgrounds/` | `BG_pickme` | `BG_pickme_001.png` |
| Wheel | `Backgrounds/` | `BG_wheel` | `BG_wheel_001.png` |

### Avatars (in-game animated characters)

Up to 5 avatars per game (some games have none). Each avatar is a
separate slot with its own iterations.

| Asset | Folder | Label | Examples |
|---|---|---|---|
| Avatar 1 | `Avatars/` | `Avatar1` | `Avatar1_001.png`, `Avatar1_002.png` |
| Avatar 2 | `Avatars/` | `Avatar2` | `Avatar2_001.png` |
| Avatar 3 | `Avatars/` | `Avatar3` | `Avatar3_001.png` |
| Avatar 4 | `Avatars/` | `Avatar4` | `Avatar4_001.png` |
| Avatar 5 | `Avatars/` | `Avatar5` | `Avatar5_001.png` |

### UI surfaces

Each surface gets its own folder so a designer reviewing chrome can see
just what they need without symbol/background noise.

| Asset | Folder | Label | Examples |
|---|---|---|---|
| Reel frame / bezel | `Bezels/` | `Bezel` | `Bezel_001.png` |
| HUD chrome | `HUD/` | `HUD` | `HUD_001.png` |
| Paytable | `Paytables/` | `Paytable` | `Paytable_001.png` |
| Win banner — small | `Win_Banners/` | `Banner_small` | `Banner_small_001.png` |
| Win banner — medium | `Win_Banners/` | `Banner_medium` | `Banner_medium_001.png` |
| Win banner — big | `Win_Banners/` | `Banner_big` | `Banner_big_001.png` |
| Win banner — mega | `Win_Banners/` | `Banner_mega` | `Banner_mega_001.png` |
| Win banner — epic | `Win_Banners/` | `Banner_epic` | `Banner_epic_001.png` |
| Bonus screen — free spins intro | `Bonus_Screens/` | `BonusScreen_freespins` | `BonusScreen_freespins_001.png` |
| Bonus screen — pick-me | `Bonus_Screens/` | `BonusScreen_pickme` | `BonusScreen_pickme_001.png` |
| Bonus screen — wheel intro | `Bonus_Screens/` | `BonusScreen_wheel` | `BonusScreen_wheel_001.png` |
| Wheel — jackpot | `Wheels/` | `Wheel_jackpot` | `Wheel_jackpot_001.png` |
| Wheel — bonus | `Wheels/` | `Wheel_bonus` | `Wheel_bonus_001.png` |
| Wheel — multiplier | `Wheels/` | `Wheel_multiplier` | `Wheel_multiplier_001.png` |
| Wheel — pick-em | `Wheels/` | `Wheel_pickem` | `Wheel_pickem_001.png` |
| Multiplier badge | `Multipliers/` | `Multiplier_x<N>` | `Multiplier_x2_001.png`, `Multiplier_x10_001.png` |
| Logo — hero | `Logos/` | `Logo_hero` | `Logo_hero_001.png` |
| Logo — standard | `Logos/` | `Logo_standard` | `Logo_standard_001.png` |
| Logo — compact | `Logos/` | `Logo_compact` | `Logo_compact_001.png` |
| Lobby tile | `Lobby_Tiles/` | `Tile` | `Tile_001.png` |

### QA reports

| Asset | Folder | Label | Examples |
|---|---|---|---|
| Audit report | `QA_Reports/` | `QA` | `QA_001.md`, `QA_002.md` |

### Derived variants — upscaled and resized

These two suffixes describe **operations** on an existing approved asset,
not new asset slots. The derived file lives in the **same folder as the
source** (so a designer reviewing `Symbol_Art/` sees the 2K HP1 and its
upscaled 4K sibling side by side).

| Operation | Suffix pattern | Examples |
|---|---|---|
| Upscale | `_upscl_x<N>` where `<N>` is the linear multiplier of the upscale (2K→4K is `x2` since dimensions doubled; 1K→4K is `x4`) | `HP1_002.png` → `HP1_002_upscl_x2.png` |
| Smart-resize | `_resize_<W>_<H>` where `<W>_<H>` is the exact output dimensions in pixels | `Key_Art_003.png` → `Key_Art_003_resize_768_1536.png` |
| Variant fan-out (hero upscale only) | append `_v<N>` to the upscale suffix before picking the winner | `HP1_002_upscl_x2_v1.png`, `..._v2.png`, `..._v3.png` — after picking, rename winner to drop `_v<N>` |

Both suffixes preserve the source filename verbatim so any team member
can trace the derived file back to its origin by inspection. The `_4K`
and `_resized` suffixes used in earlier versions of this plugin are
**retired** — do not use them in new generations.

### Mode variants — `<symbol>_<mode>_NNN.png`

Mode variants are per-symbol re-renderings for non-base game modes
(free spins, bonus, pick-em, wheel). They are **not** derived files —
they're fresh generations or edits that coexist with the base-mode
asset. See `shared/mode_variants.md` for the design doctrine
(which tiers can have variants, the recolor budget, when to use
`nb2_edit` vs `nb2_generate`).

| Mode | Suffix pattern | Example |
|---|---|---|
| Base (default) | no mode token | `WD1_001.png`, `HP1_002.png` |
| Free spins | `_freespins` | `WD1_freespins_001.png` |
| Bonus | `_bonus` | `JP1_bonus_001.png` |
| Pick-em | `_pickme` | `SF1_pickme_001.png` |
| Wheel | `_wheel` | rarely used; wheels themselves live in `Wheels/` |

Mode variants live in the same category folder as the base asset
(`Symbol_Art/` for symbols, `Avatars/` for avatars when applicable),
keyed by the mode-suffixed filename. The MCP server's auto-increment
scans the folder for files matching `<symbol_id>_<mode>_*` and picks
the next index.

Storage in `project.json`: mode variants land in the per-symbol
`modes.<mode>` sub-record, never in the top-level `iterations` array
(which is reserved for base mode). See `shared/project_memory.md` →
"modes slot for mode-variant assets" for the schema.

---

## How to compute the next filename

Pseudocode every skill uses:

```
function nextFilename(projectRoot, folder, label, ext = "png"):
    folderPath = path.join(projectRoot, folder)
    pattern = `{label}_*.{ext}`
    existing = glob(folderPath, pattern)

    if existing is empty:
        return `{label}_001.{ext}`

    highest = max number across all matched files
    next = highest + 1

    return `{label}_{next:03d}.{ext}`
```

Two important details:

- The scan is **scoped to the asset's category folder**, not the
  project root. `nextFilename` for `HP1` looks in `Symbol_Art/`, not
  in the project root.
- The folder is **created on first write** if it doesn't exist. Skills
  don't pre-create empty folders.

Examples:
- `Symbol_Art/` is empty → `HP1_001.png`
- `Symbol_Art/` has `HP1_001.png` and `HP1_002.png` → next is `HP1_003.png`
- `Symbol_Art/` has `HP1_001.png`, `HP1_002.png`, `HP1_005.png` (gap) → next is `HP1_006.png`
  (we always go past the max, never fill gaps)

---

## What about iterations of the same conceptual asset?

When a user says "iterate on HP1 — make it darker," generate `HP1_002.png`
in `Symbol_Art/` without touching `HP1_001.png`. The user reviews both
and tells you which to mark as approved.

The approved version is recorded in `project.json.assets.symbols.HP1`.
Each `iterations[]` entry is an **iteration record object** per
`shared/project_memory.md` → "Iteration record shape", capturing
`{path, prompt, references, model, image_size, aspect_ratio,
attempt_index, parent_path, timestamp}`. `approved` stays as a flat
path string pointing at one of the `iterations[].path` values:

```json
"symbols": {
  "HP1": {
    "iterations": [
      {
        "path": "Symbol_Art/HP1_001.png",
        "prompt": "<rendered prompt>",
        "references": ["Key_Art/Key_Art_003.png"],
        "model": "gemini-3.1-flash-image-preview",
        "image_size": "2K",
        "aspect_ratio": "1:1",
        "attempt_index": 1,
        "parent_path": null,
        "timestamp": "2026-05-06T16:32:11Z"
      },
      { "path": "Symbol_Art/HP1_002.png", "..." },
      { "path": "Symbol_Art/HP1_003.png", "..." }
    ],
    "approved": "Symbol_Art/HP1_002.png"
  }
}
```

At use time, resolve to absolute by `path.join(project_root, <path>)`.
This means iteration 002 is the one downstream skills should reference,
even though 003 came later (e.g. user preferred 002 after seeing 003).

**Legacy flat-string `iterations` arrays** from pre-v1.5.7 projects
are still readable per the migration shim documented in
`shared/project_memory.md`. The next write to any slot naturally
upgrades the whole array to objects.

---

## What about full-set "approved" snapshots?

After all symbols are individually approved, the symbol-sheet skill
assembles them into a contact sheet → `Symbol_Sheets/Sheet_001.png`.
If the set is later refined (one symbol replaced), the new sheet is
`Symbol_Sheets/Sheet_002.png`. Old sheets stay on disk for historical
reference.

---

## Anti-patterns (do not do these)

- ❌ Writing files to the project root instead of the category subfolder
- ❌ `HP1_2K.png` — no resolution in the filename
- ❌ `HP1_v2.png` — use the counter, not "v2" (exception: `_v<N>` on
  derived-variant fan-out, dropped after picking a winner)
- ❌ `HP1_phoenix.png` — no subject in the filename (it's already in
  the brief and project.json)
- ❌ `HP1_final.png` — "final" gets stale; use the `approved` field in
  project.json
- ❌ `HP1.png` — no counter; how would you iterate?
- ❌ `2026-05-06_HP1.png` — no timestamps; project.json carries the
  timestamps
- ❌ Overwriting an existing file — always increment, even if you think
  the old one was bad
- ❌ Spelling out long names like `WILD.png`, `SCATTER.png`, `BONUS.png` —
  use the canonical short prefixes from `shared/symbol_vocabulary.md`
  (`WD1`, `SC`, `BO`)
- ❌ `HP1_002_4K.png` — the `_4K` suffix is retired; use `_upscl_x2`
- ❌ `BG_base_001_resized.png` — the bare `_resized` suffix is retired;
  use `_resize_<W>_<H>` with exact pixel dimensions

---

## Why subfolders, not a flat root?

A finished game has 40–80 generated PNGs across a dozen asset types.
A flat root forces every team member to mentally filter the list every
time they open it. Subfolders make the structure self-documenting:
"the bezels are in `Bezels/`", "the avatars are in `Avatars/`", "the
audit reports are in `QA_Reports/`". File Explorer, Drive Stream, and
any handoff package all show the structure without anyone needing to
read a README.

This is the single rule the plugin enforces about where files live —
everything else (counters, sidecars, approval tracking) flows from it.
