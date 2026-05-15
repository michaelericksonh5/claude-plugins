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

### Step 4 — Generate at 9:16 / 4K (single call, native aspect, no resize)

**The deliverable IS the 9:16 / 4K source.** Jon Meschino's downstream pipeline
handles the scale and crop to H5G's exact 1536×3324 iPhone fullscreen target.
He explicitly said in spec discussion: *"as far as AI goes, you can generate
1080x1080 images or 1080x1920 videos or whatever. jin will take those and
size them appropriately for the game layout"* and *"so for ai generation you
can just care about aspect and not pixel size."*

The previous v1.7.0–v1.7.10 two-call pipeline (generate 9:16 → smart-resize
to 1536×3324) was a misinterpretation of his spec. The resize step always
either cropped horizontal content or recomposed the scene because Gemini
NB2 has no native aspect close to 19.5:9 portrait (target ratio 0.462,
closest native 9:16 = 0.5625, 22% wider). The result was unusable
deliverables AND deleted sources in the worst cases.

**As of v1.7.11: one call. 9:16. 4K. Deliver as-is.** Artists adjust
within their layout in Jon's pipeline.

Call `mcp__nb2node__nb2_generate`:

| API arg | Value |
|---|---|
| `prompt` | composed prompt (per `PROMPT_TEMPLATES.md` — note the bezel-artifact fixes there) |
| `aspect_ratio` | `"9:16"` |
| `image_size` | `"4K"` (Gemini returns ~2160×3840 or ~2304×4096 at this tier — both work for Jon's pipeline) |
| `output_dir` | `path.join(project_root, "Backgrounds")` |
| `asset_name` | `"BG_<variant>"` (the MCP appends `_NNN.png` and auto-increments by scanning `Backgrounds/`) |
| `references` | absolute paths — resolve `style_anchor.key_art_path` and `assets.sheet.approved` against `project_root` first (`path.join(project_root, stored_relative_path)`), then pass the resolved absolutes. Filter null/undefined entries. |

**File on disk after a successful call:**

```
Backgrounds/BG_<variant>_NNN.png           ← the deliverable (~2160×3840 or larger, 9:16 native)
Backgrounds/BG_<variant>_NNN.meta.json
```

That's it. No `_src` suffix, no `_resize_...` suffix, no cleanup step, no
intermediate to delete. The 9:16 / 4K PNG IS the canonical asset path
recorded in `project.json`.

**Optional `--target W×H` for non-Jon-pipeline consumers:** if a project
explicitly needs a specific pixel target produced inside the plugin (e.g.
a future consumer that doesn't have a downstream resize pipeline), the
user can pass `--target 1536x3324` to opt into a `nb2_smart_resize` step
after generation. **This is not the default.** Smart-resize has known
quality issues when the target aspect diverges materially from Gemini's
native aspects (cropping or recomposition artifacts) — only use it when
the downstream pipeline can't handle the 9:16 / 4K deliverable.

**For OpenAI `gpt-image-2` users (if a background gets generated via gpt2
for any reason)**: gpt-image-2's stable ceiling is 2K. To reach a 4K-class
deliverable, generate at 2K with `gpt2_generate` then run `nb2_upscale` to
linear ×2. The `nb2_upscale` tool preserves source pixels (Path-A recipe)
and is the only faithful upscale in the plugin. Don't try to generate at
4K with gpt-image-2 — OpenAI flags those targets experimental and the
plugin doesn't expose them.

**Mandatory: display in chat.** Immediately after `nb2_generate` returns,
call the `Read` tool on EVERY output path it returned. Claude Code renders
PNG/JPEG inline so the user sees the background in chat without opening
File Explorer. Required by `shared/nb2_prompting.md` § "After every
generation call" — non-negotiable. Do this BEFORE the QA check below.

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
  (checklist for skills)". Background specifics (v1.7.11+ single-file layout):
  `path` = `"Backgrounds/BG_<variant>_NNN.png"` (the 9:16 / 4K deliverable);
  `references` = `[<key art path>, <approved sheet path if any>]`;
  `parent_path` = `null` (backgrounds are always fresh `nb2_generate`);
  `attempt_index` increments for retries within this variant.
- If user approves, set `project.json.assets.backgrounds.<variant>.approved`
  to that same relative path (matches one of `iterations[].path`).
- Note: the `delivery_path` field from v1.7.10 is **dropped** as of v1.7.11
  because the source IS the deliverable now. Downstream skills should
  read `approved` directly — no separate delivery file to look up. If a
  project ever opts into the optional `--target W×H` resize step, the
  resized output goes under `resized[]` per the canonical asset record
  shape, not as a separate `delivery_path`.
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
