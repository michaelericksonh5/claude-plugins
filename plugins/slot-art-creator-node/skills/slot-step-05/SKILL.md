---
name: slot-step-05
description: STEP 5 — Generate the environment background(s) for the slot machine — base, free-spins, bonus, pick-me, wheel. Reads the locked key art and approved symbol sheet as references so the background sits in the same world without competing for attention. The background must support the reels, not steal from them. Run after /slot-step-04 (or directly after /slot-step-03 if a contact sheet isn't needed). Always run before /slot-step-06.
---

# Step 5 — Background Designer

A background that draws the eye has failed. Its job is to establish
atmosphere, hold the player in the world, and step back the moment the
reels appear. This skill encodes those constraints into every prompt
before sending, anchored to the locked key art and symbol set.

## Startup protocol

1. Resolve active project
2. Load `project.json`, `game_brief.json`
3. Read `project.json.style_anchor.key_art_path` — the locked key art
4. Read the approved symbol sheet (`project.json.assets.sheet.approved`)
   if available — it sets the brightness/saturation ceiling for the
   background (background must always rank below the symbols)
5. **If no active project**, follow the "no active project — guide
   through setup" pattern in `shared/project_memory.md`: route to
   `/slot-step-01` (and `/slot-step-02` for the key art), then resume
   background generation here in the same conversation.
6. **If key art isn't locked yet** (`project.json.style_anchor.key_art_path`
   missing), route to `/slot-step-02` first — every background reads the
   locked key art as a style reference. After it's locked, return here
   to generate the background the user originally asked for. Don't make
   the user re-invoke `/slot-step-05`.

## Workflow

### Step 1 — Determine variant

Ask if not specified:

| Variant | Filename | When |
|---|---|---|
| `base` | `BG_base_NNN.png` | Standard gameplay (default) |
| `freespins` | `BG_freespins_NNN.png` | Hue-shifted, +saturation, stronger vignette |
| `bonus` | `BG_bonus_NNN.png` | Full palette shift, max drama |
| `pickme` | `BG_pickme_NNN.png` | Full-screen scene, no reel grid |
| `wheel` | `BG_wheel_NNN.png` | Backdrop for circular wheel |

### Step 2 — Build the prompt

See `PROMPT_TEMPLATES.md`. Every background includes the four hard rules:

1. "bottom 30% of frame stays dark for UI controls"
2. "center reel zone 10–20% darker than surrounding areas"
3. "three-layer composition: foreground framing → midground story → distant sky"
4. "dark vignette, corners 20–40% darker than center"

**Palette discipline:** background palette is the same hue family as the
symbols but 20–30% less saturated. The brightest background element must
be dimmer than the dimmest symbol.

### Step 3 — Pre-generation validation (Gate 1)

- [ ] `style_anchor.text` (from `project.json`) is prepended verbatim as the first paragraph of the prompt
- [ ] Prompt uses **structured prose** — NOT bracketed-block format (that's for symbols only; background templates in `PROMPT_TEMPLATES.md` are all prose)
- [ ] `style_lock` in prompt verbatim
- [ ] No hex / resolution / aspect ratio strings in prompt body
- [ ] All four hard rules stated explicitly
- [ ] No instruction that puts a bright element in the center reel zone
- [ ] No instruction to show reels or grid lines
- [ ] Palette is cooler/less saturated than symbol palette
- [ ] Variant modifier matches the requested variant
- [ ] **Symbol/environment exclusivity:** for each subject in
      `brief.symbol_manifest`, the prompt either (a) does not mention
      it at all, or (b) mentions it exactly once as an intentional
      callback. NEVER carpet the BG in a symbol-set subject. See
      `shared/qa_preflight.md` "Symbol/environment exclusivity" for
      the why and how. The theme has a wider vocabulary than the
      symbol roster — pull from that for environmental motifs.

### Step 4 — Generate

Call `mcp__nb2node__nb2_generate`:

| API arg | Value |
|---|---|
| `prompt` | composed prompt |
| `aspect_ratio` | `"9:16"` portrait (default), `"16:9"` landscape, `"4:3"` tablet |
| `image_size` | `"2K"` default; `"4K"` for marketing (**nb2_generate only** — gpt-image-2 caps at 2K; backgrounds always use NB2) |
| `output_dir` | `path.join(project_root, "Backgrounds")` — every BG variant lives in this single folder. Folder is created on first write. |
| `asset_name` | `"BG_<variant>"`, e.g. `"BG_base"`, `"BG_freespins"` (the MCP server appends `_NNN.png` and auto-increments by scanning `Backgrounds/`) |
| `references` | absolute paths — resolve `style_anchor.key_art_path` and `assets.sheet.approved` against `project_root` first (`path.join(project_root, stored_relative_path)`), then pass the resolved absolutes. Filter null/undefined entries. |

### Step 5 — Inline QA check (Gate 2)

Read the output:

**BLOCK** (auto-iterate, max 2 retries):
- Bottom of frame is bright (UI panel would be unreadable)
- Center is the brightest zone
- No depth or layering — flat single plane
- Style clearly doesn't match key art

**FLAG**:
- Vignette very light
- Reel zone only marginally darker
- Palette too saturated — may compete with symbols
- Atmospheric perspective weak

**PASS:** confirm and continue.

### Step 6 — Update state

- Append an iteration record to
  `project.json.assets.backgrounds.<variant>.iterations` per
  `shared/project_memory.md` → "Writing an iteration record
  (checklist for skills)". Background specifics:
  `path` = `"Backgrounds/BG_<variant>_NNN.png"`;
  `references` = `[<key art path>, <approved sheet path if any>]`;
  `parent_path` = `null` (backgrounds are always fresh `nb2_generate`);
  `attempt_index` increments for retries within this variant.
- If user approves, set `project.json.assets.backgrounds.<variant>.approved`
  to that same relative path (matches one of `iterations[].path`).
- Set `current_step: "backgrounds_in_progress"` (or check if all needed
  variants are approved → `"ui_in_progress"` is the next natural state once
  the user moves on)
- Set `next_step: "/slot-step-05"` (continue) or
  `"/slot-step-06"` (move to UI)
- Atomic-write `project.json`

Schema for each background slot follows the canonical asset record shape
in `shared/project_memory.md`: `{iterations, approved, upscaled, resized}`.

### Step 7 — Next step nudge

```
✓ Step 5 — Background ('base' variant) generated.
  File: Backgrounds/BG_base_001.png
  Bottom dark, reel zone dimmed, three-layer depth ✓
  Folder: <project_root>/Backgrounds/
  Open:   file:///<project_root>/Backgrounds/

Next options:
  - Generate other variants (free-spins, bonus, pick-me, wheel) with /slot-step-05 again
  - Run `/slot-step-06` to design bezel, HUD, paytable, win banners
  - Run `/slot-step-08` to audit the background suite

Type `/slot-` to see the full numbered workflow.
```

## Hard rules

- **Bottom 30% always dark.**
- **Reel zone always dimmed.**
- **Three-layer depth required.**
- **Vignette required.**
- **Background palette ranks below symbol palette in brightness.**

## What to push back on

- "Show the reels in the background" → no
- "Bright sky behind the reels" → only with a 60–80% dark frosted panel between BG and reels
- "Center the hero in the BG" → no, push focal content to edges or top third

## References

- `shared/qa_preflight.md`, `shared/project_memory.md`, `shared/asset_naming.md`
- `shared/art_principles.md` §7 ("Background" bullet — three-layer composition, vignette, ~10–20% brightness drop under the grid), §1 (the ten core principles — especially #1 mobile-first, #6 global light, #7 "the reel is the hero")
- `shared/nb2_prompting.md` §9.2 (master prompt structure) — note: §9.2.3 covers bracketed-block templates for *symbols*; background prompts use the prose format in `PROMPT_TEMPLATES.md`, not the symbol bracketed-block format
- `PROMPT_TEMPLATES.md` (per-variant templates)
