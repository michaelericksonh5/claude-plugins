# Project Memory — Persistent State Across Sessions

Every slot-art-creator skill loads and updates a shared project state file
so locked decisions (theme, palette, key art path, asset registry) survive
Claude Code session restarts and conversation compaction.

This document describes the canonical state model. Every skill follows it.

## Contents

- **File layout** — where project folders live, what's inside each
- **`project.json` schema** — canonical structure: brief, style_anchor,
  assets (key/sheet/symbols/backgrounds/ui/qa), counters, timestamps
- **Skill startup protocol** — the 7-step routine every skill follows on
  invocation
- **Active-project pointer file** — `~/.h5g-slot-active-project.json`
- **Path convention** — relative in JSON, absolute at use time, with
  resolution rules for cross-platform safety
- **Atomic writes (Drive Stream safety)** — tmp-write + rename pattern
- **What happens after compaction** — how a fresh Claude session picks
  up where the previous one left off
- **What does NOT go in project memory** — chat messages, partial drafts,
  raw prompt text
- **Style anchor management** — building, storing, and reusing the
  game-wide discipline block from §9.2.1 of nb2_prompting.md
- **Non-linear workflow** — handling out-of-order step invocations

---

## File layout

```
<PROJECT_BASE>/
└── {GameID}_{username}/                ← one project folder per game
    ├── project.json                    ← THE source of truth
    ├── game_brief.json                 ← human-readable brief mirror
    │
    ├── Key_Art/                        ← master + wide/tall crops
    │   ├── Key_Art_001.png
    │   ├── Key_Art_001.meta.json
    │   ├── Key_Art_wide_001.png
    │   └── Key_Art_tall_001.png
    │
    ├── Symbol_Sheets/                  ← full-set contact sheets
    │   └── Sheet_001.png
    │
    ├── Symbol_Art/                     ← every individual reel symbol
    │   ├── HP1_001.png, HP1_002.png, ...
    │   ├── MP1_001.png, LP1_001.png, ...
    │   ├── WD1_001.png, SC_001.png, BO_001.png, ...
    │   └── (every prefix from shared/symbol_vocabulary.md)
    │
    ├── Backgrounds/                    ← base / freespins / bonus / pickme / wheel
    │   ├── BG_base_001.png
    │   ├── BG_freespins_001.png
    │   └── ...
    │
    ├── Avatars/                        ← in-game animated characters (0–5)
    │   ├── Avatar1_001.png
    │   └── Avatar2_001.png
    │
    ├── Bezels/                         ← reel frames
    ├── HUD/                            ← spin button, balance, bet, win
    ├── Paytables/                      ← paytable layouts
    ├── Win_Banners/                    ← small / medium / big / mega / epic
    ├── Bonus_Screens/                  ← free-spins / pick-me / wheel intros
    ├── Multipliers/                    ← x2, x10, ...
    ├── Logos/                          ← hero / standard / compact lockups
    ├── Lobby_Tiles/                    ← marketing thumbnails
    └── QA_Reports/                     ← audit .md reports from /slot-step-08
```

Each category folder is created on first write — empty folders are not
pre-created. `project.json` and `game_brief.json` always stay at the
project root. See `shared/asset_naming.md` for the full label table
and filename rules.

### Resolving `<PROJECT_BASE>` at runtime

Every skill resolves `<PROJECT_BASE>` in this order. First hit wins:

1. **`SLOT_ART_PROJECT_BASE` env var** — set per-machine when the user has
   a custom location, e.g. an external drive or shared mount that isn't
   on H:. Most flexible option.
2. **H5G shared Drive Stream** — `H:\Shared drives\Content Management - AI\Production_AI 2\Asset_Creation_Suite\`
   (Windows) or the equivalent Mac path (`/Volumes/GoogleDrive/Shared drives/...`).
   Used by H5G colleagues by default. Detected by checking `fs.existsSync`
   on the path; if missing, fall through.
3. **`~/slot-art-projects/`** — per-user local fallback. Created on first
   write if it doesn't exist. This is the path external (non-H5G) users
   land on without configuration.

Persist the resolved `<PROJECT_BASE>` into `project.json.project_root` as
an absolute path on creation, so subsequent skills don't have to re-resolve.

### H5G colleagues

The default path resolves to `H:\Shared drives\Content Management - AI\Production_AI 2\Asset_Creation_Suite\`
automatically because Drive Stream maps the same way for everyone with the
shared drive mounted. No configuration needed.

### External / non-H5G users

The default path doesn't exist, so resolution falls through to step 3 and
creates `~/slot-art-projects/<GameID>_<username>/` on first generation. To
relocate (e.g. to a Dropbox folder), set the env var before launching
Claude Code:

```
# Windows (PowerShell)
$env:SLOT_ART_PROJECT_BASE = "C:\Users\you\Dropbox\slot-art-projects"

# Mac/Linux
export SLOT_ART_PROJECT_BASE="$HOME/Dropbox/slot-art-projects"
```

Active project pointer (per-user, persists across sessions):

```
%USERPROFILE%\.h5g-slot-active-project.json   (Windows)
$HOME/.h5g-slot-active-project.json           (macOS/Linux)
```

This pointer file holds `{game_id, username, project_root, set_at}` so any
skill can find the active project without asking the user every time.

---

## `project.json` schema (canonical — every skill follows this)

```json
{
  "schema": "h5g_slot_project.v1",
  "game_id": "4470",
  "username": "merickson",
  "project_root": "H:\\Shared drives\\Content Management - AI\\Production_AI 2\\Asset_Creation_Suite\\4470_merickson",
  "created_at": "2026-05-06T15:30:00Z",
  "updated_at": "2026-05-06T16:45:00Z",

  "current_step": "key_art_locked",
  "next_step": "/slot-step-03",

  "brief": { "...full game_brief.json contents..." },

  "style_anchor": {
    "text": "You are generating art assets for a mobile slot machine game (\"Phoenix of Ardashir\" — a mystical regal phoenix awakens over ancient gold). Every output must be optimized for small phone screens — every element must be recognizable by silhouette alone when small on a phone. Use bold, clean shapes — no intricate micro-textures, no dense filigree that collapses at thumbnail size. High contrast between foreground and the flat background. Warm saturated colors signal high pay; cool muted colors signal low pay. Gold is reserved for premium and special symbols only. Maintain a consistent stylized semi-realistic slot game art rendering technique across the entire set.",
    "key_art_path": "Key_Art/Key_Art_003.png",
    "locked_at": "2026-05-06T16:00:00Z",
    "notes": "Approved by user — all downstream art reads this as visual reference"
  },

  "assets": {
    "key": {
      "iterations": ["Key_Art/Key_Art_001.png", "Key_Art/Key_Art_002.png", "Key_Art/Key_Art_003.png"],
      "approved": "Key_Art/Key_Art_003.png",
      "upscaled": null,
      "resized": []
    },
    "sheet": {
      "iterations": ["Symbol_Sheets/Sheet_001.png"],
      "approved": "Symbol_Sheets/Sheet_001.png",
      "upscaled": null
    },
    "symbols": {
      "HP1": {
        "iterations": [
          {
            "path": "Symbol_Art/HP1_001.png",
            "prompt": "[full rendered prompt with style_anchor + palette + tier phrase substituted]",
            "references": ["Key_Art/Key_Art_003.png"],
            "model": "gemini-3.1-flash-image-preview",
            "image_size": "2K",
            "aspect_ratio": "1:1",
            "attempt_index": 1,
            "parent_path": null,
            "timestamp": "2026-05-06T16:32:11Z"
          },
          {
            "path": "Symbol_Art/HP1_002.png",
            "prompt": "[revised rendered prompt after first attempt FLAG]",
            "references": ["Key_Art/Key_Art_003.png"],
            "model": "gemini-3.1-flash-image-preview",
            "image_size": "2K",
            "aspect_ratio": "1:1",
            "attempt_index": 2,
            "parent_path": null,
            "timestamp": "2026-05-06T16:38:47Z"
          }
        ],
        "approved": "Symbol_Art/HP1_002.png",
        "upscaled": "Symbol_Art/HP1_002_upscl_x2.png",
        "resized": [],
        "metrics_summary": {
          "measured_iteration": "Symbol_Art/HP1_002.png",
          "last_measured": "2026-05-06T17:05:00Z",
          "dominant_color_oklch": [
            { "l": 0.72, "c": 0.18, "h": 47, "pct": 0.34 },
            { "l": 0.18, "c": 0.02, "h": 0,  "pct": 0.41 },
            { "l": 0.55, "c": 0.14, "h": 28, "pct": 0.15 }
          ],
          "fill_pct": 0.83,
          "bg_uniformity_score": 0.97,
          "edge_density": 0.21
        },
        "modes": null
      },
      "HP2":  { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "MP1":  { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "LP1":  { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "WD1":  { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "SC":   { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "WY1":  { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "SF1":  { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "JP1":  { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "BWY1": { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "WJP1": { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "BL":   { "iterations": [], "approved": null, "upscaled": null, "resized": [] }
    },
    "backgrounds": {
      "base":      { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "freespins": { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "bonus":     { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "pickme":    { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "wheel":     { "iterations": [], "approved": null, "upscaled": null, "resized": [] }
    },
    "avatars": {
      "Avatar1": { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "Avatar2": { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "Avatar3": { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "Avatar4": { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
      "Avatar5": { "iterations": [], "approved": null, "upscaled": null, "resized": [] }
    },
    "ui": {
      "bezel":      { "iterations": [], "approved": null, "upscaled": null },
      "hud":        { "iterations": [], "approved": null, "upscaled": null },
      "paytable":   { "iterations": [], "approved": null, "upscaled": null },
      "bonus_screen": { "iterations": [], "approved": null, "upscaled": null },
      "lobby_tile": { "iterations": [], "approved": null, "upscaled": null },
      "banners": {
        "small":  { "iterations": [], "approved": null },
        "medium": { "iterations": [], "approved": null },
        "big":    { "iterations": [], "approved": null },
        "mega":   { "iterations": [], "approved": null },
        "epic":   { "iterations": [], "approved": null }
      },
      "multipliers": {
        "x2": { "iterations": [], "approved": null },
        "x5": { "iterations": [], "approved": null }
      },
      "logos": {
        "hero":     { "iterations": [], "approved": null },
        "standard": { "iterations": [], "approved": null },
        "compact":  { "iterations": [], "approved": null }
      },
      "wheels": {
        "jackpot":    { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
        "bonus":      { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
        "multiplier": { "iterations": [], "approved": null, "upscaled": null, "resized": [] },
        "pickem":     { "iterations": [], "approved": null, "upscaled": null, "resized": [] }
      }
    },
    "qa_reports": ["QA_Reports/QA_001.md"]
  },

  "gdd_source": {
    "file_id": null, "file_name": null, "drive_url": null,
    "version_extracted": null, "extracted_at": null
  }
}
```

### `style_anchor` field contract

`project.json.style_anchor` is an **object** with four fields. Every
downstream skill reads from it by name — don't relocate these fields.

| Field | Type | Written by | Read by |
|---|---|---|---|
| `text` | string (60–90 words) | `/slot-step-01` from the §9.2.1 template | every NB2 / gpt-image-2 generation skill — prepended verbatim to every prompt body |
| `key_art_path` | relative path from `project_root` including subfolder (e.g. `"Key_Art/Key_Art_003.png"`) | `/slot-step-02` on user approval | every skill that passes the key art as a reference image (`/slot-step-03`–`/slot-step-10`) |
| `locked_at` | ISO timestamp | `/slot-step-02` on user approval | `/slot-step-08` (audit), human ops |
| `notes` | optional string | `/slot-step-02` or user edit | human ops |

`game_brief.json` may carry a `style_anchor` string mirror and a
`key_art_path` mirror for human readability, but the canonical write
target and the canonical read source for downstream skills is always
`project.json.style_anchor`.

### Asset record shape (the universal pattern)

Every asset slot follows this shape. All path strings are relative to
`project_root` and include the asset's category subfolder.

```json
{
  "iterations": [
    {
      "path": "Symbol_Art/HP1_001.png",
      "prompt": "<full rendered prompt as sent to the model>",
      "references": ["Key_Art/Key_Art_003.png"],
      "model": "gemini-3.1-flash-image-preview",
      "image_size": "2K",
      "aspect_ratio": "1:1",
      "attempt_index": 1,
      "parent_path": null,
      "timestamp": "2026-05-06T16:32:11Z"
    }
  ],                                                   // append-only, never overwrite
  "approved": "Symbol_Art/HP1_002.png",                // null until user picks one
  "upscaled": "Symbol_Art/HP1_002_upscl_x2.png",       // null until /slot-step-09 runs
  "resized": [                                         // empty until /slot-step-10 runs
    {
      "aspect": "16:9",
      "dimensions": "3840x2160",
      "path": "Symbol_Art/HP1_002_resize_3840_2160.png"
    }
  ],
  "metrics_summary": null,                             // optional, populated by /slot-step-08
  "modes": null                                        // optional, populated by /slot-step-03 mode:<x>
}
```

- `iterations` — append-only list of every generated **iteration record** for this slot. Never overwrite, never re-order, never delete. See "Iteration record shape" below.
- `approved` — single path the user picked as canonical for this slot. Null if not yet approved. Always a string path that matches one of the `iterations[].path` values. Defaults to the latest iteration when ambiguous.
- `upscaled` — null until `/slot-step-09` produces a higher-resolution
  version of `approved`. The path uses the `_upscl_x<N>` suffix where
  `<N>` is the linear multiplier (2K→4K is `x2`).
- `resized` — empty until `/slot-step-10` produces aspect variants.
  Each entry carries the aspect, the exact `WxH` dimensions, and the
  path with the `_resize_<W>_<H>` suffix.
- `metrics_summary` — null until `/slot-step-08` runs `nb2_measure` on the approved iteration and writes back. See "metrics_summary field" below.
- `modes` — null unless the user has generated mode-specific variants (e.g. free-spins palette shifts). See "modes slot" below.

For UI banner tiers and multiplier denominations and logo lockups, the
nested object holds one record per variant, each following the shape above
(with `upscaled`/`resized` optional since banners rarely need them).

### Iteration record shape

Every entry in `iterations[]` is an **object** (not a bare path string).
The fields are:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `path` | string | yes | Relative-with-subfolder path, e.g. `"Symbol_Art/HP1_001.png"` |
| `prompt` | string | yes (may be `null` for legacy records) | The **fully rendered prompt** as sent to the model — every `<style_lock>`, `<palette_leads.primary>`, `<theme>`, etc. substituted with the actual locked text. Template-form prompts live in git, not here. |
| `references` | string[] | yes | Reference image paths passed alongside the prompt (relative-with-subfolder). Empty array if none. |
| `model` | string | yes | Model identifier returned by the MCP tool, e.g. `"gemini-3.1-flash-image-preview"`, `"fal-ai/nano-banana-2"`, `"gpt-image-2"`. |
| `image_size` | string | yes | The `image_size` arg, e.g. `"2K"`, `"4K"`, `"1K"`. |
| `aspect_ratio` | string | yes | The `aspect_ratio` arg, e.g. `"1:1"`, `"9:16"`. |
| `attempt_index` | integer | yes | 1-based index within this iteration's retry budget (e.g. inline-QA failed once → `attempt_index: 2`). Resets to `1` for a fresh generate, not a retry. |
| `parent_path` | string | yes (may be `null`) | If this iteration was produced by `nb2_edit` (or `gpt2_edit`) using a previous approved asset as `source`, the relative-with-subfolder path of that source. `null` for fresh generations. Lineage tracking. |
| `timestamp` | ISO string | yes | When the MCP tool returned this iteration. |

**Legacy migration shim.** Older `project.json` files may have flat string `iterations` arrays. When reading, accept both forms — treat a bare string as `{path: <string>, prompt: null, references: [], model: "unknown", image_size: "unknown", aspect_ratio: "unknown", attempt_index: 1, parent_path: null, timestamp: null}`. **Don't auto-rewrite** legacy files on read — the next write naturally upgrades them. New iterations always use the object form.

**Why we record the rendered prompt, not the template form.** Template files (`HP_TEMPLATE.md`, `JACKPOT_TEMPLATE.md`, etc.) are version-controlled in git, so their state at any point is recoverable. The **rendered** prompt — with style_anchor, palette, theme substituted — is what NB2 actually saw, and it's what you need to debug "why did this one come out wrong" or A/B-test "what changed between attempt 1 and attempt 2". The substituted form is the actually-useful artifact.

### Writing an iteration record (checklist for skills)

When a generation skill (`/slot-step-02` / `/slot-step-03` / `/slot-step-04` / `/slot-step-05` / `/slot-step-06` / `/slot-step-07`) finishes an MCP call and needs to persist the result, this is the **canonical write protocol**.

`/slot-step-09` (upscale) and `/slot-step-10` (smart-resize) are
deliberately **out of scope** here — they don't touch `iterations[]`.
Upscale writes a single string path to the `upscaled` field;
smart-resize appends `{aspect, dimensions, path}` objects to `resized`.
Provenance for those derived files lives in the per-PNG `.meta.json`
sidecar the MCP server already writes. See `/slot-step-09/SKILL.md`
Step 6 → "Provenance" and `/slot-step-10/SKILL.md` Step 6 →
"Provenance" for the rationale.

1. **Build the iteration record object.** Every field from "Iteration record shape" above must be present (use `null` only where the table explicitly allows it).
2. **Fill `prompt` with the FULLY RENDERED prompt** — exactly what you sent to the MCP tool. All `<style_lock>`, `<palette_leads.primary>`, `<theme>`, `<mystery.subject>`, etc. substituted with the locked values from `project.json.brief` and `project.json.style_anchor.text`. Template form is recoverable from git; the rendered form is the actually-useful artifact.
3. **Fill `references` with the array you actually passed** (relative-with-subfolder paths, resolved against `project_root`). Pass `[]` (empty array) if you passed no references, never `null`.
4. **Pull `model` from the MCP tool's response** — every gen tool reports the provider + model it routed to in the response body (e.g. `gemini-3.1-flash-image-preview`, `fal-ai/nano-banana-2`, `gpt-image-2`). Don't guess from the route; the response is authoritative.
5. **Track `attempt_index` based on conversation state.** For a fresh generate (user asked for a new asset, or first try on a new symbol), `attempt_index = 1`. For an auto-retry triggered by a BLOCK at the inline-QA gate, increment from the prior attempt (so the second try is `2`, the third is `3`). Don't reset between user approvals — a clean PASS at `attempt_index: 2` is a record of "the gate flagged once".
6. **Set `parent_path` when the call was edit-based.** `nb2_generate` / `gpt2_generate` → `parent_path: null`. `nb2_edit` / `gpt2_edit` / `nb2_upscale` / `nb2_smart_resize` → the relative-with-subfolder path of the `source` arg you passed. Mode-variant calls that use `nb2_edit` on the base-mode approved asset → the base-mode approved path. Captures lineage.
7. **Use the response timestamp** for `timestamp`. The MCP tool's response carries an ISO timestamp; use that, not the current time at write time.
8. **Append, don't overwrite.** `iterations[]` is append-only. The new record goes at the end of the array — never re-order, never delete, never replace a prior entry (even if you regret it).
9. **`approved` is still a flat path string.** Setting `approved` doesn't touch `iterations[]` — it just points at one of the existing `iterations[].path` values. If the user approves the latest one, `approved` becomes that record's `path`. To "un-approve", set `approved` back to `null` or to a prior iteration's path. The history stays intact regardless.
10. **Atomic-write `project.json`** per the existing tmp-write+rename pattern. Bump `updated_at`.

**Per-image .meta.json sidecars.** The MCP server already writes a `<basename>.meta.json` next to every generated PNG (existing behavior, see `nb2-mcp-server/index.js` → `writeSidecar`). That file carries the same provenance fields. The two are intentionally redundant: the sidecar is the per-file ground truth that survives moving the project folder; the `project.json.assets.*.iterations[]` array is the in-memory in-place query interface. Skills should use the `project.json` array for normal workflow; the sidecar is the fallback if `project.json` is ever corrupted.

**Skip the legacy flat-string form for new writes.** Even when reading a project with legacy flat-string `iterations`, when you add the next entry, switch the whole array to objects. Mixing object and string entries in one array makes downstream queries fragile.

### `metrics_summary` field

`/slot-step-08` runs `nb2_measure` on each approved asset during audit and writes a compact summary into the asset record. The full per-image metrics live in a sidecar file next to the image (`<asset>.metrics.json`) — the summary in `project.json` is the subset that fits in-memory for cross-asset queries (tier-pairwise deltas, LP warmth scan, etc.).

```json
"metrics_summary": {
  "measured_iteration": "Symbol_Art/HP1_002.png",
  "last_measured": "2026-05-06T17:05:00Z",
  "dominant_color_oklch": [
    { "l": 0.72, "c": 0.18, "h": 47, "pct": 0.34 },
    { "l": 0.18, "c": 0.02, "h": 0,  "pct": 0.41 },
    { "l": 0.55, "c": 0.14, "h": 28, "pct": 0.15 }
  ],
  "fill_pct": 0.83,
  "bg_uniformity_score": 0.97,
  "edge_density": 0.21
}
```

| Field | Meaning |
|---|---|
| `measured_iteration` | Which `iterations[].path` was measured. Usually equals `approved`. |
| `last_measured` | ISO timestamp. If `approved` changes, this becomes stale and `/slot-step-08` re-measures on next run. |
| `dominant_color_oklch` | Top N dominant colors (k-means on a downsampled image), each as `{l, c, h, pct}`. `l` is OKLCH lightness (0–1), `c` is chroma (0–~0.4), `h` is hue (0–360°), `pct` is the share of pixels in that cluster. |
| `fill_pct` | Pixel fill % of the subject — alpha-aware or BG-color-aware. Useful for tier-fill discipline (HP1 should be ~80–85%, LP ~58–65%). |
| `bg_uniformity_score` | 0–1 score: how flat the background is. 1.0 = pure solid color, <0.85 = visible gradient or pattern. Used by `/slot-step-08` to auto-RED non-flat export BGs. |
| `edge_density` | 0–1 Sobel-style edge density. Useful for "this LP is too busy" detection. |

`metrics_summary` is **null** if `/slot-step-08` hasn't been run yet OR if measurement was explicitly opted out (`nb2_measure` is opt-in per the v1.5.6+ contract — see `nb2-mcp-server` docs). Skills that read metrics must handle the null case gracefully.

### `modes` slot for mode-variant assets

Some games re-render specific symbols across modes (base / free-spins / bonus / pickme / wheel). When that happens, the variant doesn't replace the base — it sits in a parallel `modes.<mode>` sub-record:

```json
"WD1": {
  "iterations": [ ... base-mode iteration records ... ],
  "approved": "Symbol_Art/WD1_002.png",
  "upscaled": null,
  "resized": [],
  "metrics_summary": { ... },
  "modes": {
    "freespins": {
      "iterations": [
        {
          "path": "Symbol_Art/WD1_freespins_001.png",
          "prompt": "<rendered prompt with free-spins palette shift>",
          "references": ["Key_Art/Key_Art_003.png", "Symbol_Art/WD1_002.png"],
          "model": "gemini-3.1-flash-image-preview",
          "image_size": "2K",
          "aspect_ratio": "1:1",
          "attempt_index": 1,
          "parent_path": "Symbol_Art/WD1_002.png",
          "timestamp": "2026-05-06T17:30:00Z"
        }
      ],
      "approved": "Symbol_Art/WD1_freespins_001.png",
      "upscaled": null,
      "resized": [],
      "metrics_summary": null
    },
    "bonus": null
  }
}
```

- The top-level `iterations` / `approved` represents **base mode** — the default rendering.
- Each `modes.<mode>` sub-record follows the same asset-record shape (iterations + approved + upscaled + resized + metrics_summary).
- Mode names are stable: `freespins`, `bonus`, `pickme`, `wheel`. Defined in `shared/mode_variants.md`.
- `parent_path` in a mode variant's iteration record points at the base-mode approved asset — captures the lineage when `/slot-step-03 mode:<x>` uses `nb2_edit` on the base.
- Filenames carry the mode token: `WD1_freespins_NNN.png`, `JP1_bonus_NNN.png`. Skipping the mode token (e.g. `WD1_NNN.png`) implies base mode.

`modes` is **null** for symbols with no mode variants (the common case). `/slot-step-08` audits each populated mode against `shared/mode_variants.md` doctrine — e.g. LP symbols should never have `modes` populated (LP shouldn't recolor across modes).

See `shared/mode_variants.md` for the design doctrine (which tiers can have mode variants, glow/palette delta limits, recolor budget).

### `current_step` and `next_step` vocabulary

`current_step` uses the exact name of the most recently completed step.
`next_step` is a slash command (with leading `/`) the user should run next.

| current_step | next_step | Set by |
|---|---|---|
| `gdd_loaded` | `/slot-step-01` | slot-step-00 |
| `brief_locked` | `/slot-step-02` | slot-step-01 |
| `key_art_locked` | `/slot-step-03` | slot-step-02 |
| `symbols_in_progress` | `/slot-step-03` (continue) or `/slot-step-04` | slot-step-03 |
| `sheet_locked` | `/slot-step-05` | slot-step-04 |
| `backgrounds_in_progress` | `/slot-step-05` (continue) or `/slot-step-06` | slot-step-05 |
| `ui_in_progress` | `/slot-step-06` (continue) or `/slot-step-08` | slot-step-06 |
| `reskin_complete` | `/slot-step-08` | slot-step-07 |
| `audit_complete` | `/slot-step-09` (if audit GREEN) or specific design skill (if RED/YELLOW) | slot-step-08 |
| `upscale_in_progress` | `/slot-step-09` (continue) or `/slot-step-10` | slot-step-09 |
| `delivery_complete` | (project done) | slot-step-10 |

The `audit_complete` step's followup depends on the QA grade — included
in the QA report and the next-step nudge.

---

## Skill startup protocol

Every skill follows this exact sequence on invocation:

### Step 0: API key gate (generation skills only)

**Applies to:** `/slot-step-02` through `/slot-step-10`.
**Skip for:** `/slot-step-00`, `/slot-step-01`, `/slot-setup`, `/slot-help`, `/slot-tutorial`, `/slot-compare`.

Before touching project state, verify that the keys required for this
skill's generation calls are actually configured. Do this once per
invocation — not before every tool call.

**How to check:**

Use the Glob tool to find the setup script:

```
~/.claude/plugins/marketplaces/h5g-plugins/plugins/slot-art-creator-node/setup-keys.js
```

Then run it with the Bash/PowerShell tool:

```powershell
node "<absolute path from Glob>" --check
```

**Routing based on the output:**

| Output says | Action |
|---|---|
| `GEMINI_API_KEY OK` or `FAL_KEY OK` (either one) | NB2 tools are available — continue startup |
| Both `GEMINI_API_KEY MISSING` and `FAL_KEY MISSING` | Stop. Tell the user: "No NB2 key is configured — none of the generation tools will work. Run `/slot-setup` and I'll walk you through adding one." Route to `/slot-setup`, then resume the original request. |
| `OPENAI_API_KEY MISSING` and user is asking for a `gpt2_*` tool specifically | Tell the user: "The gpt-image-2 tools need an OpenAI key. Run `/slot-setup` and I'll help you add it." Route to `/slot-setup`, then return to the original request. |
| `OPENAI_API_KEY MISSING` but user only needs `nb2_*` tools | Fine — continue. OpenAI is optional. |

**If the Glob finds no script** (e.g. plugin installed differently):
Skip the programmatic check and proceed, but add a note: "I couldn't
locate the key validator — if generation fails with an auth error, run
`/slot-setup` to configure your API keys."

This gate catches the most common first-run failure mode: the user
installs the plugin and immediately runs a skill without ever setting
up keys. Rather than surfacing a raw MCP error, the skill routes them
to `/slot-setup` and comes back to finish the original request.

---

### Step 1: Find the active project

```
1. Did the user pass a GameID argument? (e.g., /slot-step-03 4470)
   → Yes: use that GameID to construct project_root, update active-project pointer
   → No: read ~/.h5g-slot-active-project.json
        → File exists: use it
        → File missing: route to "no active project — guide through setup"
                        (see below) instead of asking the user to pick
                        from a list. The list approach assumes the user
                        already has projects on disk; many first-time
                        users don't.
```

When constructing a NEW `project_root` from a GameID + username, resolve
the `<PROJECT_BASE>` in the order documented above (env var → H5G Drive
Stream → `~/slot-art-projects/`). The resulting `project_root` looks like:

```
<PROJECT_BASE>/<GameID>_<username>/
```

`username` comes from `os.userInfo().username` (or `$USER` / `%USERNAME%`
as a fallback). Persist the resolved absolute `project_root` into
`project.json` so later skills don't re-resolve.

### Step 2: Load project.json

Read `{project_root}/project.json`. If it doesn't exist, route to the
"no active project — guide through setup" path below. Exception:
`/slot-step-01` is the project-creator itself, so a missing
`project.json` is the expected state — create it from scratch (or seed
from `/slot-step-00`'s GDD extraction).

### The "no active project — guide through setup" pattern

When a generation skill (`/slot-step-02` through `/slot-step-10`) or a
review skill (`/slot-compare`) is invoked and there's no active project
to operate on, **do not dead-end the user**. Guide them through setup
and resume the original request automatically. The pattern:

1. **Acknowledge what they asked for.** "You asked to generate the HP1
   symbol — but there's no active project on this machine yet, so I'll
   set one up first and then come back to HP1."
2. **Route to the right setup step.** Default to `/slot-step-01` (lock
   the brief). If the user mentions a GDD already exists on Drive, route
   to `/slot-step-00` first (which seeds the brief from the GDD), then
   `/slot-step-01` to refine it.
3. **Keep the chain in one conversation.** Run the setup step
   conversationally — don't make the user re-invoke the original
   command after setup completes. The original request lives in the
   conversation history; just continue with it once the prerequisite is
   met.
4. **Walk the prerequisite chain.** Some skills have multiple
   prerequisites. `/slot-step-03` needs both a locked brief AND a
   locked key art, so the chain may be:
   `original /slot-step-03 ask → /slot-step-01 → /slot-step-02 →
   resume /slot-step-03`. Each link of the chain only runs once per
   project, so this is a one-time onboarding cost.
5. **Don't lecture.** Briefly explain *why* the prerequisite is needed
   (e.g., "the key art is the style anchor every symbol reads as a
   reference") but stay focused on getting the user to their original
   ask. Don't dump the full plugin tour — that's `/slot-tutorial`'s
   job.

The full prerequisite chain per skill:

| Skill | Needs | If missing, route to |
|---|---|---|
| `/slot-step-02` | active project + locked brief | `/slot-step-01` |
| `/slot-step-03` | the above + locked key art (`style_anchor.key_art_path` set) | `/slot-step-02` |
| `/slot-step-04` | the above | `/slot-step-02` (ideation mode runs without symbols) |
| `/slot-step-05` | the above (sheet optional) | `/slot-step-02` |
| `/slot-step-06` | the above (sheet + base BG strongly recommended) | `/slot-step-02` |
| `/slot-step-07` | the above + a source UI mock | ask user for source path; if no project at all, `/slot-step-01` |
| `/slot-step-08` | active project with at least one approved asset to audit | `/slot-step-01` if no project; otherwise the relevant design skill |
| `/slot-step-09` | active project + at least one approved 2K asset | the relevant design skill (often `/slot-step-03`) |
| `/slot-step-10` | active project + at least one approved asset | the relevant design skill |
| `/slot-compare` | active project (CROSS-PROJECT mode needs a second one) | `/slot-step-01` for the missing project |

`/slot-step-00`, `/slot-step-01`, `/slot-help`, `/slot-setup`,
`/slot-tutorial` do not need an active project — they either create one
or are project-agnostic.

### Example dialogue

User: `/slot-step-03 generate HP1`
(no `~/.h5g-slot-active-project.json` exists)

Skill response:
```
You asked to generate HP1 (the high-pay symbol), but there's no active
project on this machine yet. /slot-step-03 needs a locked brief AND a
locked key art before it can generate symbols on-style, so I'll walk
you through both quickly, then come back to HP1.

  Setup steps I'm about to run:
    1. /slot-step-01 — lock the game brief (theme, palette, style, tier
       plan, symbol manifest). This takes 2–5 minutes.
    2. /slot-step-02 — generate and lock the master key art. Becomes
       the visual style anchor every symbol reads.
    3. Return to HP1 generation automatically.

Do you have a Game Design Document on Drive for this game, or are you
pitching a fresh concept? (If you have a GDD, I'll prepend /slot-step-00
to seed the brief from it; if not, we'll lock the brief from scratch.)
```

The user replies, and the skill runs through the chain. When the brief
and key art are both locked, the skill returns to its original
responsibility (generating HP1) without asking the user to re-invoke
`/slot-step-03`.

### Step 3: Read the style anchor (the key art)

If `project.json.style_anchor.key_art_path` is set, read the image at
`{project_root}/{key_art_path}` using the Read tool. This image is the
visual ground truth for everything else generated. Pass it to NB2 as a
reference image when generating any new asset.

If style_anchor is NOT set and the current skill is anything other than
`/slot-step-01` or `/slot-step-02`, warn the user that downstream
art will be less consistent without a locked key art and offer to run
`/slot-step-02` first.

### Step 4: Do the skill's actual work

Generate, edit, review, etc. — the skill's specific job.

### Step 5: Save outputs

Save generated images to the **correct category subfolder** under
`project_root` with the correct naming convention (see
`shared/asset_naming.md`). The skill passes
`output_dir = path.join(project_root, "<Category_Folder>")` to the MCP
tool. Never overwrite — always auto-increment.

### Step 6: Update project.json

After every generation:
- Append the new file path to the appropriate `assets[...]` array
- Update `updated_at`
- Update `current_step` and `next_step`
- Atomic write: write to `project.json.tmp`, then rename to `project.json`
  (avoids corruption if the write is interrupted, especially on Drive Stream)

### Step 7: Nudge the next step

Every skill ends its response with the next-step nudge:

```
✓ [Skill] complete.

Next: run `/slot-XX-skillname` to [what the next step does].
Type `/slot-` to see the full numbered workflow.
```

---

## Active-project pointer file

`~/.h5g-slot-active-project.json` holds:

```json
{
  "schema": "h5g_active_project.v1",
  "game_id": "4470",
  "username": "merickson",
  "project_root": "H:\\Shared drives\\Content Management - AI\\Production_AI 2\\Asset_Creation_Suite\\4470_merickson",
  "set_at": "2026-05-06T15:30:00Z"
}
```

Every skill that successfully resolves an active project writes/updates
this pointer. It survives Claude Code restart and conversation compaction.

A user can switch projects in two ways:
1. Pass a different GameID as a skill argument: `/slot-step-03 4471`
2. Manually edit the pointer file (last resort)

---

## Path convention — relative-with-subfolder in JSON, absolute at use time

All asset paths recorded in `project.json` are stored as **relative
paths from `project_root`, including the category subfolder**. Use
forward slashes — they're valid on every OS, and `path.join` normalizes
them. Examples:

```json
"style_anchor": { "key_art_path": "Key_Art/Key_Art_003.png" }
"assets": {
  "key":     { "approved": "Key_Art/Key_Art_003.png" },
  "sheet":   { "approved": "Symbol_Sheets/Sheet_001.png" },
  "symbols": { "HP1": { "approved": "Symbol_Art/HP1_002.png" } },
  "ui":      { "bezel": { "approved": "Bezels/Bezel_001.png" } }
}
```

Why relative-with-subfolder:
- **Portable.** If a teammate copies the project folder to a different
  drive, every path still resolves against the new `project_root`.
- **Self-documenting.** The stored path tells the reader which category
  the asset belongs to without consulting a side table — `"Symbol_Art/HP1_002.png"`
  is obviously a symbol; `"Bezels/Bezel_001.png"` is obviously a bezel.
- **One join, not two.** `path.join(project_root, stored)` produces the
  absolute path in a single call. The skill never needs to know the
  category-to-folder mapping at read time — it's encoded in the
  stored path itself.

**At use time** — whenever you pass an asset path to:
- An MCP tool (`source`, `references`, `image`, etc. — `uploadLocalFile`
  does `fs.readFileSync` and needs absolute)
- A `Read` tool call (Read needs absolute path)
- A `Write` / save operation
- A child process that reads the file

… resolve to an absolute path first by joining with `project_root`:

```
absolute = path.join(project.project_root, project.style_anchor.key_art_path)
```

The `project_root` field in `project.json` IS stored as an absolute path
(it's the canonical project location), so resolution is one `path.join`
call. Skills that forget to resolve will silently fail with ENOENT or
have the MCP tool save to a wrong default folder.

**When writing new assets:** the skill calling the MCP tool is
responsible for passing the correct subfolder as `output_dir`. After
the MCP tool returns the absolute output path, the skill strips back
to a relative-from-project-root path (using `path.relative(project_root, absolute)`)
before storing in `project.json`. This keeps the JSON portable while
the MCP tool sees only absolutes.

## Atomic writes (Drive Stream safety)

Google Drive for Desktop / Drive Stream sometimes lags on file syncs.
To avoid corrupting `project.json` if a write is interrupted:

1. Read the existing `project.json` into memory
2. Modify in memory
3. Write to `project.json.tmp` in the same folder
4. Rename `project.json.tmp` → `project.json` (atomic on the same volume)

If a skill encounters a `.tmp` leftover from a previous crashed write,
warn the user and refuse to proceed until they decide whether to keep
the leftover or discard it.

---

## What happens after compaction

Conversation compaction discards the in-memory chat history but does not
touch any disk file. After compaction:

1. The user invokes any slot- skill
2. The skill follows the startup protocol above
3. `~/.h5g-slot-active-project.json` is read → project_root resolved
4. `project.json` is read → all locked decisions restored
5. The key art image is re-read into context as the visual anchor
6. Work continues as if nothing happened

The user does NOT need to re-establish theme, palette, style, or the
generated asset list. That's the entire point of project memory.

---

## What does NOT go in project memory

- API keys (handled by env vars / `setup-keys.js`)
- Generated image bytes (those live as PNGs on disk; `project.json` only stores paths)
- Per-image prompt history (each PNG gets its own `.meta.json` sidecar — see `shared/asset_naming.md`)
- Anything user-specific that isn't tied to this game project

---

## Style anchor management

The `style_anchor.key_art_path` field in `project.json` is what every
downstream skill reads as the visual ground truth. Three ways the user
controls it:

### 1. Approve at generation time (the default flow)

When `/slot-step-02` returns a generated image, it asks:

> Approve this as the locked key art, or iterate?

**On approve:** Claude sets
`style_anchor.key_art_path = "Key_Art/Key_Art_NNN.png"`, records the
timestamp, and writes `project.json`. Every later skill auto-reads this
file (resolved against `project_root`) as a reference.

### 2. Switch the anchor later

The user can change which key art is the locked anchor at any time:

```
"Use Key_Art_005 as the new anchor"
"Lock Key_Art_002 instead — it had better palette"
```

Any skill processes that as a state edit:
- Confirm `Key_Art/Key_Art_005.png` exists under the project folder
- Update `style_anchor.key_art_path = "Key_Art/Key_Art_005.png"`
- Update `style_anchor.locked_at` to now
- Write `project.json` atomically

### 3. Override per generation

For one-off generations using a different reference (e.g., trying a
specific symbol against an experimental key art that isn't locked yet),
pass an explicit reference image:

```
"Generate HP1 using Key_Art_007 as reference instead of the locked anchor"
```

The skill resolves `Key_Art/Key_Art_007.png` against `project_root` and
passes the absolute path to NB2's `references` arg without touching
`project.json`. The locked anchor stays unchanged.

### Picking by visual review (any skill, any time)

The user can ask: "Show me Key_Art_001, Key_Art_003, and Key_Art_005 —
I want to pick one to lock." Claude reads each image (using the
absolute path resolved from `Key_Art/Key_Art_NNN.png`), presents them,
and the user picks. The dedicated `/slot-compare` skill makes this
flow first-class.

Filenames are the canonical identifier. Sidecars
(`Key_Art/Key_Art_NNN.meta.json`) hold the prompt that produced each
one — useful for "I liked iteration 3, let me try a tweak of that
prompt" workflows.

---

## Non-linear workflow

The numbered slash commands are a **recommendation**, not enforcement.
After the foundation is laid (brief locked + key art locked), the user
can jump between skills as needed:

- After key art, run `/slot-step-04` in **ideation mode** to
  brainstorm symbols visually before refining individuals
- Bounce between `/slot-step-03` and `/slot-step-04`
  as you iterate
- Skip `/slot-step-04` entirely if you'd rather build symbols
  one at a time
- Run `/slot-step-05` while symbols are still in flux
- Run `/slot-step-08` at any checkpoint, not just at the end

Every skill's startup protocol detects what's already been done. They
adapt:
- If symbols don't exist yet, symbol-sheet runs in ideation mode
- If background isn't done yet, UI designer warns but proceeds
- If brief is missing, every skill stops and routes to `/slot-step-01`

The only hard ordering constraint: **brief and key art must be locked
before any other generation skill runs.** Those two anchor everything.
