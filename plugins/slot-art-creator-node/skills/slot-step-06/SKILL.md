---
name: slot-step-06
description: STEP 6 — Generate slot machine UI surfaces, bonus wheels, and in-game characters — reel frames/bezels, HUD chrome, paytable, win banners (small/medium/big/mega/epic), bonus screens (free-spins/pick-me/wheel intros), bonus wheels (jackpot/bonus/multiplier/pick-em — generated as full single-graphic wheels with every slice laid out, not individual slice files), multiplier badges, lobby tiles, logos (hero/standard/compact lockups), spin/bet buttons, control panels, and in-game animated avatars (the player-facing characters that react to wins — 0 to 5 per game). Reads the locked key art, symbol sheet, and background as references so every surface and character lives in the same world. UI must always rank below symbols in visual hierarchy; avatars sit alongside the reels and follow character-design discipline; wheels are bonus-feature chrome with their own readability discipline (slice labels must read during the spin animation). Run after /slot-step-05. Use this skill whenever the user asks to "design the UI", "make the buttons", "create the paytable", "generate the win banners", "design the bonus wheel", "make a jackpot wheel", "create the logo", "make the lobby tile", "generate the spin button", "design the reel frame", "create a character / mascot / avatar", "add a player-facing character", "make the free spins intro", "design the bonus screen", OR any chrome / HUD / wheel / lobby / button / banner / paytable / logo / bezel / character surface. Also triggers on bare nouns like "wheel", "paytable", "logo", "lobby tile", "win banner" when context is the active slot project.
---

# Step 6 — UI Designer

UI chrome is infrastructure. It must reinforce the theme without stealing
attention from the symbols or the win moments. The reel is always the hero.
Every UI surface generated here is anchored to the locked key art, the
approved symbols, and the approved background.

## Startup protocol

1. Resolve active project
2. Load `project.json`, `game_brief.json`
3. Read references in priority order:
   - `style_anchor.key_art_path` (required)
   - Approved symbol sheet (if available)
   - Approved base background (if available)
4. **If no active project**, follow the "no active project — guide
   through setup" pattern in `shared/project_memory.md`: route to
   `/slot-step-01` (and `/slot-step-02` for the key art), then resume
   the user's original UI / avatar request in the same conversation.
5. **If key art isn't locked yet** (`project.json.style_anchor.key_art_path`
   missing), route to `/slot-step-02` first — every UI surface and
   avatar reads the locked key art so chrome and characters live in the
   same visual world. After it's locked, return here to generate the
   surface the user originally asked for. Don't make the user re-invoke
   `/slot-step-06`.

## Workflow

### Step 1 — Pick the surface

Ask if not specified. Each surface has a dedicated category folder so
chrome doesn't get mixed with avatars and avatars don't get mixed with
banners — a designer reviewing one surface type opens one folder.

| Surface | Folder | Filename pattern |
|---|---|---|
| `bezel` (reel frame) | `Bezels/` | `Bezel_NNN.png` |
| `hud` (spin button + balance/bet) | `HUD/` | `HUD_NNN.png` |
| `paytable` | `Paytables/` | `Paytable_NNN.png` |
| `banner_<tier>` (win banners by tier) | `Win_Banners/` | `Banner_small_NNN.png`, `Banner_big_NNN.png`, etc. |
| `bonus_screen` (free spins / pick-me / wheel intro) | `Bonus_Screens/` | `BonusScreen_<variant>_NNN.png` |
| `wheel_<variant>` (full bonus wheel graphic) | `Wheels/` | `Wheel_jackpot_NNN.png`, `Wheel_bonus_NNN.png`, `Wheel_multiplier_NNN.png`, `Wheel_pickem_NNN.png` |
| `multiplier_xN` | `Multipliers/` | `Multiplier_x2_NNN.png`, `Multiplier_x10_NNN.png` |
| `lobby_tile` | `Lobby_Tiles/` | `Tile_NNN.png` |
| `logo_<lockup>` | `Logos/` | `Logo_hero_NNN.png`, `Logo_standard_NNN.png`, `Logo_compact_NNN.png` |
| `avatar_<id>` (in-game animated character) | `Avatars/` | `Avatar1_NNN.png` through `Avatar5_NNN.png` (up to 5 per game; many games have zero) |

### Step 2 — Build the prompt (READ the right surface template)

This skill uses **progressive disclosure** — the per-surface prompt
formulas live in dedicated companion files. Read ONLY the file for the
surface you're generating. Don't read all of them.

| Surface being generated | Read this file FIRST |
|---|---|
| `bezel` (reel frame) | `BEZEL_TEMPLATE.md` |
| `hud` | `HUD_TEMPLATE.md` |
| `banner_<tier>` (any tier — small/big/mega/epic) | `BANNERS_TEMPLATE.md` |
| `bonus_screen` (free-spins / pick-me / wheel intro) | `BONUS_SCREEN_TEMPLATE.md` |
| `wheel_<variant>` (full wheel graphic — jackpot / bonus / multiplier / pick-em) | `WHEEL_TEMPLATE.md` |
| `multiplier_xN` | `MULTIPLIER_TEMPLATE.md` |
| `lobby_tile` | `LOBBY_TILE_TEMPLATE.md` |
| `logo_<lockup>` (hero / standard / compact) | `LOGO_TEMPLATE.md` |
| `paytable` | `PAYTABLE_TEMPLATE.md` |
| `avatar_<id>` (in-game character) | `AVATAR_TEMPLATE.md` |

Each template file contains:
- Surface rules (palette, sizing, conventions)
- Prompt formula(s) with substitution markers
- Pre-gen quick checks specific to that surface
- Post-gen quick checks specific to that surface

If the user asks for "all UI surfaces" or "the full UI set," generate them
in this order so each can reference the prior approved chrome:

1. `bezel` — sets the metallic/palette baseline for chrome
2. `hud` — fits below the bezel
3. `banners` — escalation series (small → big → mega → epic)
4. `bonus_screen` variants — free-spins intro, pick-me intro, wheel
   intro (the bonus-mode entry screens, NOT the wheel graphic itself)
5. `wheel_<variant>` — full bonus-wheel graphics (jackpot / bonus /
   multiplier / pickem). Each variant is a single complete PNG
   (outer frame + slices + hub + pointer in one graphic) landing in
   `Wheels/`. Generate the jackpot wheel first if the brief has
   `jackpot_tier_names` so subsequent wheels can reference it for
   slice-color and frame consistency.
6. `multipliers` — denomination series
7. `paytable` — composes from approved symbols
8. `lobby_tile` — marketing surface (often last)
9. `logo` lockups — often a parallel track to gameplay UI
10. `avatar_<id>` — in-game animated characters (`Avatar1`–`Avatar5`).
    Games with zero avatars skip this surface. When present,
    generate after the symbol set is locked so the cast's
    brightness/saturation can be tuned to sit between HP and MP
    intensity.

### Step 3 — Pre-generation validation (Gate 1)

**Universal:**
- [ ] `style_lock` in prompt verbatim
- [ ] No hex / resolution / aspect ratio strings in prompt body

**UI hierarchy:**
- [ ] Prompt does NOT instruct chrome to be the brightest/dominant element
- [ ] For bezel: "reel is the hero" stated
- [ ] For banners: numeral stated as focal point
- [ ] Palette drawn from brief but kept secondary to symbols

**Surface-specific:**
- [ ] Grid dimensions stated for bezel
- [ ] Touch target sizes stated for HUD/pick-me
- [ ] Tier count and tier differences stated for banners

### Step 4 — Generate

**Pick the right tool first AND the right folder.** Every surface has
two routing decisions — which MCP tool to call, and which subfolder the
output lands in. Both are surface-determined:

| Surface | `output_dir` (subfolder of `project_root`) | Has visible required text? | Preferred tool (if `OPENAI_API_KEY` set) | Fallback (NB2-only) |
|---|---|---|---|---|
| `paytable` | `Paytables/` | yes (PAY TABLE header, pay values) | `gpt2_generate` | `nb2_generate` |
| `logo_<lockup>` | `Logos/` | yes (the wordmark spelling matters) | `gpt2_generate` | `nb2_generate` |
| `banner_<tier>` | `Win_Banners/` | usually no (composited at runtime) | `nb2_generate` (or `gpt2_edit` for runtime-baked labels) | `nb2_generate` |
| `bezel` | `Bezels/` | no | `nb2_generate` | `nb2_generate` |
| `hud` | `HUD/` | no | `nb2_generate` | `nb2_generate` |
| `bonus_screen` | `Bonus_Screens/` | no | `nb2_generate` | `nb2_generate` |
| `wheel_<variant>` | `Wheels/` | yes (every slice carries a label: `GRAND` / `×10` / `FREE SPINS` / etc.) | `gpt2_generate` | `nb2_generate` (be ready for 2–4 attempts to keep labels legible; verify every slice label at the QA gate) |
| `multiplier_xN` | `Multipliers/` | no | `nb2_generate` | `nb2_generate` |
| `lobby_tile` | `Lobby_Tiles/` | no (title appears at runtime) | `nb2_generate` | `nb2_generate` |
| `avatar_<id>` | `Avatars/` | no | `nb2_generate` | `nb2_generate` |

`gpt2_generate` accepts the same `output_dir` / `asset_name` shape as
`nb2_generate`. Keep `image_size: "2K"` for gpt2 even on hero lockups —
its 4K targets are experimental and unreliable for production; upscale
the approved 2K result with `nb2_upscale` if you need 4K marketing
output. See `shared/gpt_image2_prompting.md` for the full routing table.

Call `mcp__nb2node__nb2_generate` (NB2 path) or `mcp__nb2node__gpt2_generate` (gpt2 path — see routing table above):

**API args (NB2 path — most surfaces):**

| API arg | Value |
|---|---|
| `prompt` | composed prompt |
| `aspect_ratio` | match surface — bezel: game orientation, banner: portrait, tile: `1:1` or `4:3`, avatar: `1:1` |
| `image_size` | `"2K"` default |
| `output_dir` | `path.join(project_root, "<Folder>")` where `<Folder>` is the subfolder from the routing table above (e.g. `Bezels`, `HUD`, `Win_Banners`, `Avatars`). Folder is created on first write. |
| `asset_name` | the surface label, e.g. `"Bezel"`, `"HUD"`, `"Banner_big"`, `"Logo_hero"`, `"Avatar1"` (the MCP server appends `_NNN.png` and auto-increments by scanning the target folder for existing files with that prefix) |
| `references` | absolute paths — resolve `style_anchor.key_art_path`, `assets.sheet.approved`, and `assets.backgrounds.base.approved` against `project_root` first (`path.join(project_root, stored_relative_path)`), then pass the resolved absolutes. Filter null/undefined entries. |

**API args (gpt2 path — paytable, logos, or anything text-heavy):**

| API arg | Value |
|---|---|
| `prompt` | composed prompt (gpt-image-2 reasons better when the structural intent — row count, label positions, wordmark spelling — is stated explicitly) |
| `aspect_ratio` | match surface |
| `image_size` | `"2K"` (the stable production ceiling) |
| `quality` | `"high"` for hero / marketing surfaces |
| `output_dir` | `path.join(project_root, "Paytables")` or `path.join(project_root, "Logos")` — same per-surface routing as the NB2 path. |
| `asset_name` | same convention as NB2 |
| `extra_references` (gpt2_edit only) | absolute paths to approved symbol PNGs when composing them into a layout |

**Mandatory: display in chat.** Immediately after the generation call
returns, invoke the `Read` tool on EVERY output path it returned. Precede
each Read with a short markdown header naming the surface (e.g.
`### Bezel_001.png`, `### Logo_hero_001.png`) so each render is its own
visual beat — batched Reads without framing text get collapsed in some
chat clients and the images don't display. Claude Code renders PNG/JPEG
inline so the user sees the surface in chat without opening File Explorer.
Required by `shared/nb2_prompting.md` § "After every generation call" —
non-negotiable. Do this BEFORE the QA check below.

### Step 5 — Inline QA check (Gate 2)

**BLOCK** (auto-iterate):
- UI brighter/more dominant than symbols
- Bezel has opaque center (would cover reels)
- Banner numeral isn't the focal point
- Style doesn't match key art

**FLAG**:
- Chrome feels too busy
- Touch targets look small
- Palette slightly off from the symbol set

**PASS:** confirm and continue.

### Step 6 — Update state

All paths stored in `project.json` are relative to `project_root` and
include the subfolder, e.g. `"Bezels/Bezel_001.png"`,
`"Win_Banners/Banner_big_001.png"`, `"Avatars/Avatar1_002.png"`.

**Universal write protocol.** Every generation here appends an
**iteration record** (object form per `shared/project_memory.md` →
"Iteration record shape" + "Writing an iteration record (checklist
for skills)") to the appropriate slot's `iterations[]`. The record
captures `path` + `prompt` + `references` + `model` + `image_size` +
`aspect_ratio` + `attempt_index` + `parent_path` + `timestamp` per
the shared contract. For most UI surfaces `parent_path` is `null`
(fresh `nb2_generate` / `gpt2_generate`); for any surface that uses
`nb2_edit` or `gpt2_edit` against a prior approved asset (rare in
this skill — typical for `/slot-step-07` reskins), set `parent_path`
to the source's relative-with-subfolder path.

For surfaces with a flat slot (`bezel`, `hud`, `paytable`, `bonus_screen`,
`lobby_tile`):
- Append the iteration record to `project.json.assets.ui.<surface>.iterations`.
- If user approves, set `project.json.assets.ui.<surface>.approved` to
  the approved iteration's `path` field.

For nested groups (`banners.<tier>`, `multipliers.<denom>`, `logos.<lockup>`):
- Append the iteration record to `project.json.assets.ui.banners.<tier>.iterations`
  (or the equivalent nested slot for multipliers / logos).
- If user approves, set `.approved` on the nested record to the
  approved iteration's `path` field.

For **avatars** (the in-game character family):
- Append the iteration record to `project.json.assets.avatars.<AvatarN>.iterations`
  where `<AvatarN>` is `Avatar1` through `Avatar5`.
- If user approves, set `project.json.assets.avatars.<AvatarN>.approved`
  to the approved iteration's `path` field.
- The `assets.avatars` object is created in the schema even when a game
  has zero avatars — slots stay at `{iterations: [], approved: null}`
  until something lands.

For **wheels** (`wheel_jackpot`, `wheel_bonus`, `wheel_multiplier`,
`wheel_pickem`):
- Append the iteration record to `project.json.assets.ui.wheels.<variant>.iterations`
  where `<variant>` is `jackpot` / `bonus` / `multiplier` / `pickem`.
- If user approves, set `project.json.assets.ui.wheels.<variant>.approved`
  to the approved iteration's `path` field.
- Each wheel variant is its own slot — a game with both a jackpot
  wheel AND a multiplier wheel has both slots populated; a game with
  no wheels at all leaves them at `{iterations: [], approved: null}`.

Set `current_step: "ui_in_progress"`, `next_step: "/slot-step-06"`
(continue) or `"/slot-step-08"` (move to audit).

Schema for every UI and avatar slot follows the canonical asset record
shape in `shared/project_memory.md`.

### Step 7 — Next step nudge

```
✓ Step 6 — Bezel generated.
  File: Bezels/Bezel_001.png
  Reel is the hero, frame transparent center ✓
  Folder: <project_root>/Bezels/
  Open:   file:///<project_root>/Bezels/

Next options:
  - Generate other UI surfaces (HUD, paytable, banners, logos) with /slot-step-06 again
  - Generate in-game avatars with /slot-step-06 (avatar_1, avatar_2, ...)
  - Run `/slot-step-07` if reskinning an existing UI mock
  - Run `/slot-step-08` for full set audit

Type `/slot-` to see the full numbered workflow.
```

## Hard rules

- **Reel is always the hero.** Chrome ranks below symbols in brightness and weight.
- **No raw pixel counts** in prompts — semantic size terms only.
- **Win-banner tiers must differ in at least 2 dimensions.**
- **Three logo lockups** when generating a logo.

## References

- `shared/qa_preflight.md`, `shared/project_memory.md`, `shared/asset_naming.md`
- `shared/art_principles.md` §6 (typography), §7 (surfaces — bezel / HUD / background / paytable / win presentation / lobby tile), §8 (CVD + contrast)
- `shared/nb2_prompting.md` §9.2 (formula), §9.6 (UI / edit ops)
- `shared/gpt_image2_prompting.md` (full gpt2 playbook — when to prefer gpt-image-2 for paytables, logos, banners with copy; size mapping, quality, per-skill recommendations)

### Per-surface templates (read on demand)

- `BEZEL_TEMPLATE.md` — reel frame / bezel + thickness vocabulary
- `HUD_TEMPLATE.md` — bottom HUD strip (spin button + balance/bet/win)
- `BANNERS_TEMPLATE.md` — win celebration overlays (BIG / MEGA / EPIC)
- `BONUS_SCREEN_TEMPLATE.md` — intro screens for free-spins / pick-me
  / wheel-bonus modes (the announce screen, NOT the wheel itself)
- `WHEEL_TEMPLATE.md` — full bonus-wheel graphic (jackpot wheel,
  bonus wheel, multiplier wheel, pick-em wheel) — single-graphic
  output with all slices laid out, NOT individual slice files
- `MULTIPLIER_TEMPLATE.md` — multiplier badges by denomination
- `LOBBY_TILE_TEMPLATE.md` — lobby thumbnail
- `LOGO_TEMPLATE.md` — game logo (hero / standard / compact lockups)
- `PAYTABLE_TEMPLATE.md` — paytable layout chrome
- `AVATAR_TEMPLATE.md` — in-game animated character (player-facing
  mascot / host / cheering creature) — character-design discipline,
  not chrome
