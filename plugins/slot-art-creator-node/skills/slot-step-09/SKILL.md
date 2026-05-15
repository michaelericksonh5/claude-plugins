---
name: slot-step-09
description: STEP 9 — Upscale approved slot art to a higher resolution with NB2 using the proven Path-A workflow (vision model in the loop). Typical jumps are 2K→4K (linear x2) or 1K→4K (linear x4); the output file is named with the suffix `_upscl_x<N>` where `<N>` is the linear multiplier, and the file lives in the same category folder as its source so a designer reviewing `Symbol_Art/` sees the 2K HP1 and the 4K HP1 side by side. NB2 has a strong bias toward regenerating rather than upscaling; this skill's prompt structure forces it into upscale mode by following the 6-part preservation template and reviewing the output against an 8-axis rubric, iterating on failure. Run after /slot-step-08 passes GREEN. Use when the user asks to "upscale", "increase the resolution", "make this 4K", "uprez this asset", "go from 2K to 4K", "get a higher-res version", "blow this up", "make this bigger", "supersize this", "higher resolution", "upres", "scale this up", or "improve the resolution".
---

# Step 9 — NB2 Upscaler

Upscales approved 2K assets to 4K for production delivery. NB2 wants to
regenerate rather than preserve; this skill's preservation-first prompt
structure plus inline review forces it into upscale mode.

For multi-aspect-ratio variants of one source, use `/slot-step-10`
instead.

## Startup protocol

Follow `shared/project_memory.md` → "Skill startup protocol", including
the "no active project — guide through setup" pattern.

1. Resolve active project. **If none exists**, the user is asking to
   upscale something that hasn't been generated — route to
   `/slot-step-01` to set up a project, then explain that there's
   nothing approved yet to upscale. Suggest the design skills
   (`/slot-step-02` for key art, `/slot-step-03` for symbols, …) so
   the user can build up assets, then return here.
2. Load `project.json`.
3. Identify which approved assets to upscale. Common targets:
   - All approved symbols (HP/MP/LP/Wild/Scatter)
   - The locked key art (already at 4K — skip if so)
   - Approved backgrounds (often need 4K for marketing)
   - Approved logos

   If nothing is approved yet, tell the user honestly and route to the
   appropriate design skill — never invent a source asset.

## Workflow

### Step 1 — Pick the source asset

The source is usually an approved file from one of the project's
category subfolders. Common sources (paths are project-relative; resolve
against `project_root` before passing to the MCP tool):

- `Symbol_Art/HP1_002.png` (the approved iteration of HP1)
- `Backgrounds/BG_base_001.png`
- `Logos/Logo_hero_001.png`
- `Key_Art/Key_Art_003.png` (the locked master)

Compute the **linear multiplier** `<N>` from the source size and target
size — e.g. 2K→4K is x2 (dimensions double), 1K→4K is x4, 1K→2K is x2.
Read the source's `.meta.json` sidecar to get the source's `image_size`
field; the target is whatever you're upscaling to.

**If the user pastes / attaches an external asset in chat** that they want
upscaled, that path lives in a temp location outside the allowed-roots
envelope — `nb2_upscale` will reject it. Stage it first:

```
nb2_stage_image({ source: "<chat-temp-path>", label: "user_upscale_source" })
  → ~/.h5g-slot-art-creator/inputs/user_upscale_source_NNN.png
```

Pass the staged path as `source` to `nb2_upscale` in Step 4. See
`shared/chat_image_staging.md` for full details.

### Step 2 — Build the 6-part preservation prompt

**Read `UPSCALE_TEMPLATE.md` and use it verbatim as the prompt
template.** It is the canonical source: it documents the 10-item
visual inventory you fill in BEFORE writing the prompt, the 6-part
prompt structure (opening + preservation bullets + material
restatement + enhance-only allowance + hard negatives + closing
deliverable), and the per-tier worked examples. Do not improvise a
prompt from memory — NB2's bias is to regenerate rather than upscale,
and the template's structure is what forces it into upscale mode.

As a sanity-check, every assembled upscale prompt should
unambiguously cover these six preservation axes (the schema underneath
the prompt template):

1. **Subject** — the exact same character/object/scene; same pose,
   expression, details, composition
2. **Palette** — exact same colors; no hue / saturation / warmth shifts
3. **Style** — exact same render style; no change in brushwork or finish
4. **Edges** — preserve every visible edge; no smoothing or added detail
5. **Background** — exact same background; flat solid black/white preserved exactly
6. **Aspect ratio** — exact same proportions; no crop or canvas extension

If any axis is silent or contradicted in the assembled prompt, go back
to `UPSCALE_TEMPLATE.md` and pull in the missing bullets — the audit
list in Step 3 below depends on all six being present.

### Step 3 — Pre-generation validation (Gate 1)

- [ ] Source image path exists and is a real PNG
- [ ] All 6 preservation axes covered in the prompt (Subject, Palette,
      Style, Edges, Background, Aspect ratio)
- [ ] No hex / resolution / aspect ratio strings in prompt body
- [ ] No instructions that contradict preservation. **Unscoped** "improve" / "enhance" / "add detail" language is contradiction — it tells NB2 to regenerate. The template's `Enhance only:` block (part 4 of `UPSCALE_TEMPLATE.md`) is the one exception and is **required**, not forbidden: it tightly scopes 2–4 enhance-only items (e.g. "edge sharpness, highlight crispness, subtle micro-surface detail") that the upscale step is allowed to touch. Anything outside that scoped block stays untouched.

### Step 4 — Generate

NB2 is stochastic — the same source + prompt yields a slightly different
output each call. For routine upscales, one call is fine. For **hero
assets** (key art, logo, the game's signature symbol, anything going on
marketing surfaces), generate N variants in parallel and pick the best.

**Choosing N:**
- Routine symbol upscale (LP/MP, repeated set): `N=1`. Single call, retry
  on failure.
- Standard HP / banner upscale: `N=2`. Cheap insurance against a bad draw.
- Key art / logo / marquee asset: `N=3 or 4`. The cost of picking the
  best is small relative to the value of getting the hero right.

**How to run N>1:**

Issue N parallel `nb2_upscale` calls with the same `prompt` and `source`
but different `asset_name` suffixes (the `_v<N>` is appended **after**
the `_upscl_x<N>` suffix):

```
nb2_upscale(asset_name="HP1_002_upscl_x2_v1", ...)
nb2_upscale(asset_name="HP1_002_upscl_x2_v2", ...)
nb2_upscale(asset_name="HP1_002_upscl_x2_v3", ...)
nb2_upscale(asset_name="HP1_002_upscl_x2_v4", ...)
```

Send them in a single tool batch (parallel MCP calls in one turn). Then
in Step 5, review all N outputs together against the 8-axis rubric and
pick the winner. **Rename the winner to drop the `_v<N>` suffix** so
the canonical upscaled file is `HP1_002_upscl_x2.png`. Optionally
archive the runner-ups under their versioned names (don't delete —
they're decent fallbacks if the winner has a subtle issue you catch
later).

For a single-call run, call `mcp__nb2node__nb2_upscale`:

| API arg | Value |
|---|---|
| `prompt` | composed preservation prompt |
| `source` | absolute path to the approved source asset — resolve the stored relative path against `project_root` first (e.g. `path.join(project_root, "Symbol_Art/HP1_002.png")`) |
| `image_size` | the target — typically `"4K"`. The linear multiplier `<N>` in the filename is computed from source-size→target-size, not from this arg directly. |
| `aspect_ratio` | omit; inherit from source |
| `output_dir` | **the source's category folder** — `path.dirname(absolute_source_path)`. Upscaled outputs live next to their source so `Symbol_Art/HP1_002.png` and `Symbol_Art/HP1_002_upscl_x2.png` sit side by side. |
| `asset_name` | `"<source_basename>_upscl_x<N>"` where `<source_basename>` is the source filename without extension and `<N>` is the linear multiplier. Example: source `Symbol_Art/HP1_002.png` upscaled 2K→4K → pass `"HP1_002_upscl_x2"`. The MCP server appends `.png`. |

**Mandatory: display in chat.** Immediately after `nb2_upscale` returns,
call the `Read` tool on the output path (the `_upscl_x<N>.png` file).
Claude Code renders PNG/JPEG inline so the user sees the upscaled asset
in chat without opening File Explorer. Required by
`shared/nb2_prompting.md` § "After every generation call" —
non-negotiable. Do this BEFORE the review rubric below.

### Step 5 — Inline review (Gate 2) — 8-axis rubric

For **N=1**: read source and output, compare against the rubric below.

For **N>1**: read source and ALL N outputs, score each output against
the rubric, then declare the highest-scoring output the winner. Rename
the winner to drop the `_v<N>` suffix so the canonical upscale name is
`<source_basename>_upscl_x<N>.png`; keep the runners-up with their
versioned names. If two outputs tie, prefer the one closer to the
source's edge structure (most preservation, least redesign).

Compare each output to the source:

| Axis | PASS | FAIL action |
|---|---|---|
| Subject | Exact same character/scene | Strengthen "preserve exactly" + restate subject |
| Palette | Hue/saturation match | Add: "exact same colors, do not shift hue" |
| Style | Same render finish | Add: "preserve brushwork and rendering style exactly" |
| Edges | Every visible edge preserved | Add: "do not smooth or simplify edges" |
| Background | Flat solid match | Restate background spec |
| Aspect ratio | Identical proportions | Restate aspect preservation; check API arg inheritance |
| Detail | No new details added | Add: "do not invent or add detail" |
| Resolution | Output is meaningfully higher than source | If too close, retry with stronger size cue |

Any FAIL → patch prompt and regenerate. Cap at **3 attempts total per
asset (initial call + up to 2 retries)**. After the third failure, stop
and report which axes NB2 was unable to preserve and what you tried — at
that point the source is likely the problem (too low-res, too ambiguous,
or stylistically incompatible with NB2's upscale mode). This matches
`REVIEW_RUBRIC.md` → "When to stop iterating".

### Step 6 — Update state

For each upscaled asset, set the `upscaled` field in the canonical asset
record. Paths are project-relative including the subfolder (same as
every other asset path in `project.json`):

```json
"assets.symbols.HP1.upscaled":      "Symbol_Art/HP1_002_upscl_x2.png"
"assets.backgrounds.base.upscaled": "Backgrounds/BG_base_001_upscl_x2.png"
"assets.key.upscaled":              "Key_Art/Key_Art_003_upscl_x2.png"
"assets.avatars.Avatar1.upscaled":  "Avatars/Avatar1_002_upscl_x2.png"
```

The `iterations` and `approved` fields are NOT touched. The original
file stays in place; the upscaled version lives in the same folder as
a sibling and is referenced via the `upscaled` field.

**Provenance.** The `upscaled` field is a flat path string, not an
iteration object — the schema is intentionally narrower here because
upscale is a terminal derivation. The full prompt + model + source
lineage for each upscale lives in the per-file `<basename>.meta.json`
sidecar the MCP server writes next to the PNG (existing behavior).
If you need to debug "why does HP1's 4K look slightly different from
its 2K", read `HP1_002_upscl_x2.meta.json` — it carries the prompt,
the model the server routed to, the source path, and the timestamp.
Skills don't have to surface this into `project.json` for upscales.

Set `current_step: "upscale_in_progress"`, `next_step: "/slot-step-09"`
(continue) or `"/slot-step-10"` (move to delivery variants).

Schema follows the canonical asset record shape in `shared/project_memory.md`:
`{iterations, approved, upscaled, resized, metrics_summary, modes}`.

### Step 7 — Next step nudge

```
✓ Step 9 — Upscaled (linear x2, target 4K).
  Source : Symbol_Art/HP1_002.png
  Output : Symbol_Art/HP1_002_upscl_x2.png
  All 8 preservation axes passed ✓
  Folder: <project_root>/Symbol_Art/
  Open:   file:///<project_root>/Symbol_Art/

Next options:
  - Continue upscaling other approved assets with /slot-step-09 again
  - Run `/slot-step-10` for multi-aspect deliverables
  - Run `/slot-step-08` to confirm the upscale didn't break anything

Type `/slot-` to see the full numbered workflow.
```

## Hard rules

- **Preserve, don't regenerate.** Every output is a higher-res version of
  the source — no new detail, no style drift, no palette shift.
- **Original stays.** Never overwrite the 2K source.
- **Auto-iterate on failure.** 3 attempts total per asset (initial call + up to 2 retries) — same wording as `REVIEW_RUBRIC.md`.

## References

- `shared/upscale_workflow.md` — Path-A explained (vision-LLM-in-the-loop,
  N-and-pick batches, forbidden-adjective list, identity-lock clause).
  This is the conceptual basis for this entire skill — read it once.
- `shared/chat_image_staging.md` — required when the source isn't already
  inside the active project folder
- `shared/qa_preflight.md`, `shared/project_memory.md`, `shared/asset_naming.md`
- `shared/nb2_prompting.md` §9.6 (edit/upscale operations)
- `UPSCALE_TEMPLATE.md` (6-part preservation prompt template)
- `REVIEW_RUBRIC.md` (8-axis pass/fail rubric)
