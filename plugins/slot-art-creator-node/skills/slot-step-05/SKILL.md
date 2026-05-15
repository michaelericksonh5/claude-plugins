---
name: slot-step-05
description: STEP 5 — Generate the environment background(s) for the slot machine — base, free-spins, bonus, pick-me, wheel. Reads the locked key art and approved symbol sheet as references so the background sits in the same world without competing for attention. The background must support the reels, not steal from them. Run after /slot-step-04 (or directly after /slot-step-03 if a contact sheet isn't needed). Always run before /slot-step-06. Use when the user asks to "create the background", "generate the game BG", "make the environment", "design the scene behind the reels", "show what the reels will sit in front of", "make the BG", "what's behind the reels", "the bonus environment", "the scene", "make the free spins background", "design the bonus background", "build the wheel background", or asks for any background variant (free-spins BG, bonus BG, etc.).
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

### Step 4 — Generate at fullscreen delivery size (1536×3324)

**All backgrounds delivered by this skill are 1536×3324** — H5G's iPhone
portrait fullscreen design size, the size Jon's downstream asset script
expects as the 3x source (he generates 2x and 1x automatically). This
applies to every variant (base, freespins, bonus, pickme, wheel) without
exception. Symbol art (`/slot-step-03`) and UI art (`/slot-step-06`)
are NOT affected by this rule — they keep their own native sizes.

**Two-call pipeline.** NB2 has no native 19.5:9 aspect (1536/3324 ≈ 0.462),
so we generate at the closest native aspect (9:16) and recompose to exact
pixels with `nb2_smart_resize`. Both calls use the same NB2 model end-to-end
on Gemini-only setups.

**Call 1 — generate the artwork at 9:16:**

Call `mcp__nb2node__nb2_generate`:

| API arg | Value |
|---|---|
| `prompt` | composed prompt |
| `aspect_ratio` | `"9:16"` |
| `image_size` | `"2K"` |
| `output_dir` | `path.join(project_root, "Backgrounds")` |
| `asset_name` | `"BG_<variant>_src"` (the `_src` suffix marks this as a temporary 9:16 intermediate; will be deleted in step 4c) |
| `references` | absolute paths — resolve `style_anchor.key_art_path` and `assets.sheet.approved` against `project_root` first (`path.join(project_root, stored_relative_path)`), then pass the resolved absolutes. Filter null/undefined entries. |

**Call 2 — recompose to 1536×3324:**

Call `mcp__nb2node__nb2_smart_resize` on the path returned by call 1:

| API arg | Value |
|---|---|
| `source` | absolute path to the `BG_<variant>_src_NNN.png` from call 1 |
| `target_sizes` | `["1536x3324"]` |
| `output_dir` | `path.join(project_root, "Backgrounds")` |
| `asset_name` | `"BG_<variant>_tmp"` (the MCP appends `_resize_1536_3324.png`; this lands as `BG_<variant>_tmp_resize_1536_3324_NNN.png`. Step 4c renames it to the canonical `BG_<variant>_NNN.png` form so downstream skills find it at the expected path.) |
| `prompt` | (optional) one short sentence telling NB2 what the source is — e.g. `"Recompose this slot machine bonus background to the target portrait dimensions, preserving the depth, vignette, and dim center reel zone."` |

**Call 4c — cleanup (mandatory, not optional):**

After call 2 succeeds:

1. **Rename** the resize output to the canonical filename. Use the next available `NNN` counter scanning `Backgrounds/` for existing `BG_<variant>_<NNN>.png` files:
   ```
   Backgrounds/BG_<variant>_tmp_resize_1536_3324_NNN.png  →  Backgrounds/BG_<variant>_NNN.png
   ```
2. **Delete** the 9:16 intermediate: `Backgrounds/BG_<variant>_src_NNN.png` (the source from call 1) AND its sidecar `.meta.json`. The intermediate has no value once the resized version exists; keeping it around clutters the project folder and confuses `/slot-compare`.
3. **Rename the sidecar** too: `BG_<variant>_tmp_resize_1536_3324_NNN.meta.json` → `BG_<variant>_NNN.meta.json`. Update the `filename` field inside it to match the new name. (The other sidecar fields — prompt, model, references, dimensions — stay accurate.)

The canonical filename `BG_<variant>_NNN.png` is what step 6 records in `project.json.assets.backgrounds.<variant>.iterations[].path` and what every downstream skill (`/slot-step-06`, `/slot-step-08`, `/slot-compare`) reads. There is no ambiguity — the two-call pipeline is hidden from anyone reading `project.json`.

**Routing**: with `GEMINI_API_KEY` set, `nb2_smart_resize` routes through
NB2 (`gemini-3.1-flash-image-preview`) with an oversample-then-crop recipe —
same model the generation step uses. With only `FAL_KEY` set, it routes
through fal's `nano-banana-pro` smart-resize endpoint (single API call,
no local crop). Either path works fully for 1536×3324.

**Override for non-H5G projects:** if the active project's
`brief.delivery_spec.fullscreen` declares different `{width, height}`
values, use those instead of 1536×3324. This field doesn't exist in the
brief schema yet — see the PSD/layout ingest note in the "Future work"
section at the bottom of this file. Until that's wired up, 1536×3324 is
the unconditional default.

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

- **Final dimensions are 1536×3324** for every variant. Anything else is a regression.
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

## Future work — PSD / layout ingest

Right now this skill hardcodes 1536×3324 as the universal H5G iPhone
fullscreen target. Long-term direction (per Jon Meschino's spec): consume
a PSD or layout JSON that declares *every* asset's target dimensions
inside a specific game's full layout, and have each generation skill read
its target size from that spec instead of hardcoding a value. The data
shape would live at `project.json.brief.delivery_spec`:

```jsonc
"delivery_spec": {
  "platform": "iphone-portrait",
  "fullscreen": { "width": 1536, "height": 3324 },
  "symbol_canvas": { "width": <from PSD>, "height": <from PSD> },
  "ladder_factors": [3, 2, 1],
  "output_root": "Textures/Portrait"
  // ...plus a per-surface map from a PSD ingest
}
```

A future `/slot-step-00b` (or extension to `/slot-step-00`) would parse a
PSD via JSX or a Figma file via the Figma API and populate the spec.
Until that exists, this skill's fullscreen default IS the de-facto spec
for H5G mobile portrait slots — change the constant in Step 4 if H5G's
design size ever changes.

For downsampling 3x → 2x → 1x: Jon's own asset pipeline handles that
deterministically from the 3x source, so this skill does NOT produce
2x/1x outputs. Single delivery: one PNG per background variant at
1536×3324.
