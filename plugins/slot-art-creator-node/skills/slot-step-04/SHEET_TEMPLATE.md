# Symbol Sheet — Prompt Template

## Master template

```
A <layout> contact sheet of slot machine symbols for the game "<game_name>",
<theme_summary>, <style_lock>,
single canvas with the grid clearly divided into <N> equal cells,
no grid lines drawn, equal padding between cells,
all symbols share an upper-left key light at 10 o'clock and the same outline policy.

Cells, top-left to bottom-right:
1. <cell_1_description>
2. <cell_2_description>
...
N. <cell_N_description>

One unified flat solid <export_bg> background, no gradients, no mats.
One palette across the sheet — <palette_leads.primary> for warm tiers,
cool muted neutrals for low-pay cells.
Pay tier hierarchy visible at a glance: high-pay cells larger, warmer,
and more saturated than low-pay cells.

Mobile-readable thumbnails, sharp clean edges, professional slot game art,
one canvas only, <aspect> aspect ratio.
```

## Per-cell phrasing grammar

```
<N>. <symbol_id> — <subject>, <tier_phrase>, <palette_clause>
```

## Tier-specific cell phrases

| Tier | tier_phrase | palette_clause |
|---|---|---|
| HP | `"large and prominent, fills most of its cell, soft inner rim glow"` | `"warm <primary> with metallic highlights"` |
| MP | `"generous size with visible padding, no glow, subtle highlight"` | `"moderate warm-leaning palette"` |
| LP | `"small and understated with generous empty space, letter or shape reads first"` | `"cool muted only — no warm gold or amber, not even trim"` |
| Wild | `"barely contained, fills its cell edge to edge, electric emissive break-color"` | describe the wild's break color |
| Scatter | `"circular badge-shaped, prominent"` | `"warm luminous golden ticket"` |

## Layout reference

| Layout | Cells | Typical contents | Aspect |
|---|---|---|---|
| `2x3` | 6 | 2 HP + 2 MP + 2 LP | `4:3` |
| `3x3` | 9 | 2 HP + 2 MP + 4 LP + 1 special | `1:1` |
| `3x4` | 12 | Full manifest minus jackpot | `3:4` |
| `4x3` | 12 | Wide-format full manifest | `4:3` |

## Hard rules

- **LP discipline holds on sheets** — LP cells in the same prompt as HP cells must still avoid `gold`/`amber`/`detailed`.
- **One unified background** — all black OR all white across all cells; never mixed.
- **One global light direction** — declared once for the whole sheet.
- **No grid lines or labels** — unless user explicitly asks for an annotated review sheet.
- **Single canvas** — one image back, not separate per-cell images.

## After generating

Append an **iteration record** (object form per
`shared/project_memory.md` → "Iteration record shape" + "Writing an
iteration record (checklist for skills)") to
`project.json.assets.sheet.iterations`. The record's `path` is the
relative-with-subfolder string (`"Symbol_Sheets/Sheet_NNN.png"`); the
`prompt`, `references`, `model`, `image_size`, `aspect_ratio`, and
`timestamp` come from the actual `nb2_generate` call you just made.

If the user approves it, set `project.json.assets.sheet.approved` to
that same relative-with-subfolder path (it matches one of the
`iterations[].path` values). Downstream skills (`/slot-step-03`,
`/slot-step-06`) read `project.json.assets.sheet.approved`, resolve
it against `project_root`, and pass the resulting absolute path to
NB2 as a reference to anchor symbol-set style.

There is no `game_brief.json.symbol_sheet_path` field — that was the old
v0 location and is no longer read by any skill.
