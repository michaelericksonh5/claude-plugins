---
name: slot-step-04
description: STEP 4 — Generate a full symbol contact sheet. Two modes — IDEATION (key art + GDD/manifest → propose what each symbol could look like, before locking individuals) and ASSEMBLE (lay out approved individual symbols). Often used right after /slot-step-02 to brainstorm the set visually before refining symbols in /slot-step-03. Use when the user asks to "show all the symbols", "lay out the symbol set", "brainstorm what the symbols should look like", "show me the full set", "give me a contact sheet", "see all symbols together", "the full symbol set", "symbol sheet", "all symbols at once", "preview the symbol set", "make a board with everything", "line up all symbols", "show every symbol", or "build the sheet".
---

# Step 4 — Symbol Contact Sheet

The contact sheet has two distinct uses:

1. **Ideation** — right after key art is locked, generate a proposed sheet
   from the manifest + GDD info. The user sees what each symbol could look
   like in one shot. They iterate on the sheet to lock the visual direction
   for the full set, *before* committing to individual symbols.
2. **Assemble** — once individual symbols are approved, compose them onto
   a single canvas as a deliverable.

Most projects start with ideation, jump to `/slot-step-03` to
refine the strongest symbols at high fidelity, then come back to assemble
mode for the final sheet.

## Startup protocol

Follow `shared/project_memory.md` → "Skill startup protocol", including
the "no active project — guide through setup" pattern.

1. Resolve active project. **If none exists**, route to `/slot-step-01`
   → `/slot-step-02` → resume contact-sheet generation here in the same
   conversation.
2. Load `project.json`, `game_brief.json`.
3. Read `project.json.style_anchor.key_art_path` (the locked key art) —
   required for both modes. **If not locked**, route to `/slot-step-02`
   first, then resume.
4. Detect mode by counting approved symbols:
   - Iterate `project.json.assets.symbols.*.approved`
   - If <50% of manifest symbols have a non-null `approved` field → **ideation mode** (default)
   - If ≥50% have `approved` set → **assemble mode** (default)
   - User can override either way explicitly

## Workflow

### Mode A — Ideation (no approved individuals yet)

The user has key art locked and a brief with a symbol manifest. They want
to see the full set in one shot to decide which symbols are strong.

**Inputs:**
- Key art (the visual style anchor)
- `brief.symbol_manifest` — the full list of symbol IDs and subjects
- `brief.theme_summary`, `brief.style_lock`, `brief.palette_leads`
- Any GDD reference images (read via `read_file_content` if `gdd_source.file_id` is set)
- User's verbal direction ("emphasize jungle creatures", "make the wild a totem")

**Build the prompt:** see `SHEET_TEMPLATE.md`. Key elements:

- "Same style and palette as the key art reference image"
- Grid layout from `brief.grid` (e.g. "5×4 reel grid → 13 symbol cells")
- Per-cell tier discipline restated:
  - HP cells: warm, dominant, rim glow, flat black background
  - MP cells: moderate warmth, subtle highlight, flat black background
  - LP cells: cool muted palette, no gold/amber/warm trim, flat white background
  - Wild cell: breaks category and palette (states what it is)
  - Scatter cell: circular badge
- Each cell labeled with its manifest subject in the prompt
- "Each cell is a square 1:1 with consistent padding"

**Reference images to pass:**
- `style_anchor.key_art_path` (always)
- Any GDD reference images (mood boards, concept art)

**Iterate freely.** Each generation produces `Sheet_001.png`,
`Sheet_002.png`, etc. The user picks one direction and moves to slot-03 to
refine individual symbols against it.

### Mode B — Assemble (individual symbols approved)

The user has approved individual symbols and wants a final layout-only
contact sheet for review/handoff.

**Inputs:**
- Approved symbol PNG paths from `project.json.assets.symbols.<id>.approved`
  (read each from the project root)
- Key art for style continuity reference (`style_anchor.key_art_path`)

**Approach:** call `mcp__nb2node__nb2_generate` (same tool as Mode A —
see Step 4 below) with all approved symbols passed in the `references`
array and a layout-focused prompt that says "compose these symbols on
one canvas in a grid, preserve each one's exact appearance, add only
spacing and a unified backdrop."

Conceptually this is closer to a layout op than a generation — the
individual symbols are already locked, the sheet just stages them — but
the API call is `nb2_generate` with multiple references, not
`nb2_edit`. `nb2_edit` requires a single `source` image; an
ideation/assemble contact sheet has multiple approved symbols and no
single source.

### Choose mode (or override)

Default is auto-detected. The user can override:

```
"Run a fresh ideation sheet — I want to explore a different direction"
"Assemble the approved symbols into a final sheet"
```

The skill switches modes accordingly.

### Step 3 — Pre-generation validation (Gate 1)

- [ ] `style_lock` in prompt verbatim
- [ ] No hex / resolution / aspect ratio in prompt body
- [ ] Each cell's tier phrase is correct
- [ ] LP cells stated as "no gold or warm trim"
- [ ] Wild cell breaks category and palette
- [ ] Cell count matches the manifest

### Step 4 — Generate

Call `mcp__nb2node__nb2_generate`:

| API arg | Value |
|---|---|
| `prompt` | composed sheet prompt |
| `aspect_ratio` | match the grid — typically `"5:4"` for a 5x4 grid display, or `"1:1"` if symbols are arranged in a tight square |
| `image_size` | `"4K"` (sheets render many cells; need the resolution — **nb2_generate only**; gpt-image-2 caps at 2K but is never used for sheets) |
| `output_dir` | `path.join(project_root, "Symbol_Sheets")` — all contact sheets land here. Folder is created on first write. |
| `asset_name` | `"Sheet"` (the MCP server appends `_NNN.png` and auto-increments by scanning `Symbol_Sheets/`) |
| `references` | absolute paths — resolve each path in `project.json` against `project_root` first. **Mode A (ideation)**: only the key art is reliably available, so pass `[style_anchor.key_art_path]` plus any GDD reference images you read in earlier. **Mode B (assemble)**: pass `[style_anchor.key_art_path, HP1_approved, MP1_approved, LP1_approved, WD1_approved]` (skip any whose `.approved` is null — never pass a literal "null"). Filter null/undefined paths before the call; `uploadLocalFile` inside the MCP tool will throw ENOENT if you don't. |

**Mandatory: display in chat.** Immediately after `nb2_generate` returns,
call the `Read` tool on EVERY output path it returned. Precede each Read
with a short markdown header naming the sheet (e.g. `### Symbol_Sheet_001.png`)
so each render is its own visual beat — batched Reads without framing
text get collapsed in some chat clients and the images don't display.
Claude Code renders PNG/JPEG inline so the user sees the contact sheet
in chat without opening File Explorer. Required by `shared/nb2_prompting.md`
§ "After every generation call" — non-negotiable. Do this BEFORE the
QA check below.

### Step 5 — Inline QA check (Gate 2)

Read the output. Check:

**BLOCK** (auto-iterate):
- Tier gradient unreadable (HP/MP/LP indistinguishable at a glance)
- Wild fails to break the set
- Any LP shows gold/amber
- Style mismatch from key art

**FLAG**:
- Cell padding inconsistent
- Light direction varies across cells
- One cell looks like it belongs to a different game

**PASS:** confirm and continue.

### Step 6 — Update state

- Append an iteration record to `project.json.assets.sheet.iterations`
  per `shared/project_memory.md` → "Writing an iteration record
  (checklist for skills)". Sheet-specifics:
  `path` = `"Symbol_Sheets/Sheet_NNN.png"`;
  `references` = `[<key art path>]` for ideation mode, or
  `[<key art path>, <each approved symbol path>...]` for assemble mode
  (with null-symbols filtered out);
  `parent_path` = `null` (sheets are always fresh `nb2_generate`).
- If user approves, set `project.json.assets.sheet.approved` to that
  same relative path (matches one of `iterations[].path`).
- Set `current_step: "sheet_locked"`, `next_step: "/slot-step-05"`.
- Atomic-write `project.json`.

Schema for the sheet slot follows the canonical asset record shape:
`{iterations, approved, upscaled}`.

### Step 7 — Next step nudge

In ideation mode:
```
✓ Step 4 — Ideation sheet generated.
  File: Symbol_Sheets/Sheet_001.png
  All 13 symbols proposed at a glance ✓
  Folder: <project_root>/Symbol_Sheets/
  Open:   file:///<project_root>/Symbol_Sheets/

Next options:
  - Iterate on this sheet for a different direction (run /slot-step-04 again)
  - Refine the strongest symbols at high fidelity in `/slot-step-03`
    (each symbol will use Sheet_001.png as a reference)
  - Generate the background in `/slot-step-05`

Type `/slot-` to see the full numbered workflow.
```

In assemble mode:
```
✓ Step 4 — Symbol sheet locked.
  File: Symbol_Sheets/Sheet_007.png
  All 13 approved symbols composed on one canvas ✓
  Folder: <project_root>/Symbol_Sheets/
  Open:   file:///<project_root>/Symbol_Sheets/

Next: run `/slot-step-05` to generate the game background.

Type `/slot-` to see the full numbered workflow.
```

## Hard rules

- **Sheet must match the locked key art's style.** Always pass key art as a reference.
- **Cell aspect ratios are 1:1.** A symbol that's not square looks broken in a slot grid.
- **Per-tier discipline holds at sheet scale.** LP cells still get cool palette, white BG.

## References

- `shared/project_memory.md`, `shared/asset_naming.md`, `shared/qa_preflight.md`
- `shared/nb2_prompting.md` §9.2 (master formula)
- `shared/art_principles.md` §3 (symbols)
- `SHEET_TEMPLATE.md` (full prompt template)
