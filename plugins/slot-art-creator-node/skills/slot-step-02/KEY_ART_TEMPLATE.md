# Key Art — Prompt Templates

## Master (1:1 — canonical hero illustration)

```
A master key art illustration for the mobile slot game "<game_name>",
<theme_summary>, <style_lock>, a single hero subject as the dominant focal point,
<hero_subject_phrase>, three-layer composition with foreground framing,
midground story, and distant sky for atmospheric perspective and parallax-ready
separation, spotlight composition with a calmer cleaner center and edge detail
carrying story, upper-left key light at 10 o'clock, <palette_leads.primary>
palette with <palette_leads.accents> accents, corners 20 to 40 percent darker
than center for a soft vignette, no UI mockup, no reels, no paylines, no spin
buttons, no HUD, no text, hero face or figure occupies roughly the center
60 to 70 percent of the composition, professional slot game art,
mobile slot key art, square master composition.
```

## Wide crop (16:9 — web banner / Google Play feature)

```
A master key art illustration for the mobile slot game "<game_name>",
<theme_summary>, <style_lock>, single hero subject, <hero_subject_phrase>,
three-layer composition, upper-left key light at 10 o'clock,
<palette_leads.primary> palette with <palette_leads.accents> accents,
soft vignette corners darker than center, no UI, no text,
wide horizontal composition for a web banner / feature crop,
hero subject left-of-center with midground extending to the right,
professional slot game art.
```

## Tall crop (9:16 — loading screen / mobile ad)

```
A master key art illustration for the mobile slot game "<game_name>",
<theme_summary>, <style_lock>, single hero subject, <hero_subject_phrase>,
three-layer composition, upper-left key light at 10 o'clock,
<palette_leads.primary> palette with <palette_leads.accents> accents,
soft vignette corners darker than center, no UI, no text,
tall vertical portrait composition for a loading screen / mobile ad crop,
hero subject in the upper two thirds with midground beneath,
professional slot game art.
```

## Rules

- **One visual idea.** Single hero focal point. No ensemble unless that IS the theme.
- **Hero occupies 60–70%** of the composition for character-centric comps.
- **Three-layer composition:** foreground framing → midground story → distant sky.
- **Spotlight composition:** calmer cleaner center; edge detail carries story.
- **Vignette:** corners 20–40% darker than center.
- **No UI inside key art.** No reels, paylines, spin buttons, HUD.
- **Master at 4K.** Crop derivatives from same master (or use nb2_smart_resize).
- **Anchor the hero.** Name and describe the hero explicitly — do not let NB2 invent one.

## After approving the master

Write the approved relative path (e.g. `"Key_Art/Key_Art_003.png"`) to
**`project.json.style_anchor.key_art_path`** — the canonical location
every downstream skill reads. Also set `style_anchor.locked_at` to the
current ISO timestamp. See the field contract in
`shared/project_memory.md` → "`style_anchor` field contract".

`game_brief.json.key_art_path` may carry a mirror string for human
readability, but downstream skills (`/slot-step-03`, `/slot-step-05`,
`/slot-step-06`, `/slot-step-09`, `/slot-step-10`) all read
`project.json.style_anchor.key_art_path`, join it with
`project_root`, and pass the resulting absolute path as a reference
image — that's what locks the visual identity of every later asset.
