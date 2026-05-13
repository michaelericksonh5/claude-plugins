---
name: slot-step-02
description: STEP 2 — Generate the master key art for the game. The approved key art becomes the visual style anchor — every downstream skill reads it as a reference image to keep symbols, backgrounds, and UI consistent. Run after /slot-step-01. Iterates freely until the user approves one as the locked anchor.
---

# Step 2 — Key Art

The key art is the most important single asset in the project. Once locked,
it becomes the visual ground truth that every other skill (symbols,
backgrounds, UI) reads as a reference. Lock it carefully.

## Startup protocol

Follow the standard protocol from `shared/project_memory.md` →
"Skill startup protocol":

1. Resolve active project from `~/.h5g-slot-active-project.json` or
   GameID arg. **If no active project exists**, follow the "no active
   project — guide through setup" pattern: acknowledge the user's
   original ask (generating key art), run `/slot-step-01` to lock the
   brief first, then resume key-art generation in the same
   conversation — don't make the user re-invoke `/slot-step-02`.
2. Load `project.json` and `game_brief.json` from project root.
3. **If brief isn't locked yet** (no `project.json.brief` or it's
   incomplete), same pattern: run `/slot-step-01` first, then resume
   key-art generation here. The brief carries the style_lock,
   palette_leads, theme_summary, and game_name that this step needs
   to compose a coherent prompt.

## Workflow

### Step 1 — Build the prompt

Use the templates in `KEY_ART_TEMPLATE.md`. Pull values from the brief:
`game_name`, `theme_summary`, `style_lock`, `palette_leads.primary`,
`palette_leads.accents`. Build a `<hero_subject_phrase>` from the brief's
HP1 manifest entry (the hero is usually the top HP).

If the user provided a reference image (concept art, an inspiration photo,
a previous game's key art), pass it to NB2 as a reference — see Step 3.

### Step 2 — Pre-generation validation (Gate 1)

Run from `shared/qa_preflight.md`:

- [ ] `style_lock` phrase is in the prompt verbatim
- [ ] No hex codes, no codenames, no resolution strings, no aspect ratio strings
- [ ] No UI / reels / paylines / spin buttons / HUD mentioned
- [ ] One hero subject only (not an ensemble unless theme demands it)
- [ ] Three-layer composition stated
- [ ] Spotlight composition / vignette stated
- [ ] No `negative_prompt` field

### Step 3 — Generate

Call `mcp__nb2node__nb2_generate`:

Before calling the tool, read `project.json.style_anchor.text` and prepend
it verbatim as the first paragraph of the prompt. This ~70-word block was
locked in `/slot-step-01` and is the canonical style token every generation
tool reads. Do not paraphrase or abbreviate it.

| API arg | Value |
|---|---|
| `prompt` | `style_anchor.text` (verbatim, from `project.json`) + the composed key-art prompt body (no resolution / aspect ratio strings) |
| `aspect_ratio` | `"1:1"` for the master; `"16:9"` for wide crop; `"9:16"` for tall crop |
| `image_size` | `"4K"` for the master (key art is the most important asset) |
| `output_dir` | `path.join(project_root, "Key_Art")` — every key art file lives in this subfolder. The folder is created on first write if it doesn't exist. |
| `asset_name` | filename prefix without extension — pass `nextFilename("Key_Art", "png")` minus extension, so `"Key_Art_001"`, `"Key_Art_002"`, ... The MCP server appends `.png` and dedupes if the file exists. |
| `references` | user-provided reference paths, if any (absolute paths) |

Compute `nextFilename` per `shared/asset_naming.md` — glob the
`Key_Art/` subfolder for `Key_Art_*.png`, find max number, increment.

### Step 4 — Inline QA check (Gate 2)

Read the generated image immediately. Check:

**BLOCK** (auto-iterate, max 2 retries):
- Style clearly doesn't match `style_lock`
- UI elements present (reels, buttons, HUD)
- Multiple competing heroes when one was specified
- No clear focal subject

**FLAG** (surface and ask):
- Hero feels off-brand or generic
- Palette drifted from `palette_leads`
- Vignette weak

**PASS:** Show the result and ask: "Approve this as the locked key art, or
iterate?"

### Step 5 — User approves OR iterates

**Persist the iteration record immediately after every generation** —
before asking for approval. Append an iteration record to
`project.json.assets.key.iterations` per `shared/project_memory.md` →
"Writing an iteration record (checklist for skills)". Key art
specifics:
- `path` = `"Key_Art/Key_Art_NNN.png"` (or `"Key_Art/Key_Art_wide_NNN.png"`
  / `"Key_Art/Key_Art_tall_NNN.png"` for crop variants).
- `prompt` = the fully rendered prompt sent to `nb2_generate` (or
  `nb2_edit` for iterate-by-edit flows).
- `references` = `[]` for fresh generates; `["Key_Art/Key_Art_NNN.png"]`
  with the source path when this was an iterate-by-edit on a prior
  master.
- `parent_path` = `null` for `nb2_generate`; the source's
  relative-with-subfolder path for `nb2_edit` iterations.
- `attempt_index` = increment within the same key-art session if the
  user keeps asking for tweaks (3rd master attempt → `3`).

**On approve:**
- Set `project.json.assets.key.approved` = the approved relative path
  (matches one of the `iterations[].path` values).
- Set `project.json.style_anchor.key_art_path` = the same approved
  relative path (e.g. `"Key_Art/Key_Art_003.png"`).
- Set `project.json.style_anchor.locked_at` = now.
- Set `current_step: "key_art_locked"`, `next_step: "/slot-step-03"`.
- Atomic-write `project.json`.

**On iterate:**
- User describes the change ("warmer", "different hero pose", etc.).
- Build a new prompt or call `mcp__nb2node__nb2_edit` referencing the
  previous `Key_Art_NNN.png` if the change is small (pass the absolute
  path: `path.join(project_root, "Key_Art", "Key_Art_NNN.png")`).
- Generate again at the next filename — never overwrite. Append a
  fresh iteration record per the rules above.

### Step 6 — Generate wide and tall crops (optional)

Once the master is locked, the user may want a wide marketing crop and a
tall mobile crop. Use the templates in `KEY_ART_TEMPLATE.md` and call
`nb2_generate` again with the appropriate `aspect_ratio` API arg.

| Crop | `aspect_ratio` | Output (in `Key_Art/`) |
|---|---|---|
| Wide marketing | `"16:9"` | `Key_Art_wide_001.png` |
| Tall mobile | `"9:16"` | `Key_Art_tall_001.png` |

Do NOT specify aspect ratio in the prompt body — it's an API arg only.

### Step 7 — Next step nudge

```
✓ Step 2 — Key art locked.
  Approved : Key_Art/Key_Art_003.png
  Locked at: 2026-05-06T16:00:00Z
  This image is now the style anchor for every later asset.
  Folder: <project_root>/Key_Art/
  Open:   file:///<project_root>/Key_Art/

Next: run `/slot-step-03` to start generating reel symbols.
Each symbol will use this key art as a visual reference automatically.

Type `/slot-` to see the full numbered workflow.
```

## Hard rules

- **One visual idea.** Single hero focal point.
- **No UI inside key art.** No reels, paylines, spin buttons, HUD.
- **Master at 4K.** Key art is the highest-priority asset.
- **Lock once.** Once `style_anchor.key_art_path` is set, every later skill
  reads that image as a style reference automatically.
- **Iterate freely until locked.** Generate as many `Key_Art_NNN.png` as needed.
  Never overwrite. The "approved" pointer in `project.json` is what matters.

## References

- `shared/project_memory.md` (project state, `style_anchor` field contract)
- `shared/asset_naming.md` (`Key_Art` / `Key_Art_wide` / `Key_Art_tall` labels inside the `Key_Art/` folder)
- `shared/qa_preflight.md` (validation gates)
- `shared/nb2_prompting.md` §9.2 (master prompt structure)
- `shared/art_principles.md` §1 (the ten core principles — especially #5 one focal point, #6 global light, #7 reel is the hero, #8 gold is reserved) and §7 ("Background" bullet — three-layer composition, vignette, atmospheric perspective)
- `KEY_ART_TEMPLATE.md` (master / wide / tall prompt templates)
