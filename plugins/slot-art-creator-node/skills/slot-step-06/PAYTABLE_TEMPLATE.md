# Paytable Layout Template

The paytable is a static info screen showing each symbol's payout
ladder. It must use the **same symbol art as the reels** — alternate art
breaks player trust. This skill generates the layout with placeholder
slots; `/slot-step-03` produces the actual symbol art that gets
composited in.

## Which model to use — gpt-image-2 is often the better choice here

Paytables are **text-heavy with structural constraints** (rows, columns,
labels, pay values). This is exactly where **gpt-image-2** (OpenAI's
gpt2_generate tool) outperforms NB2:

- **Text rendering:** NB2 frequently misspells or scrambles text in
  the image. gpt-image-2 renders text reliably — column headers, pay
  values, multiplier badges all come out legible.
- **Structural reasoning:** "8-row paytable, symbol on left, value on
  right, consistent column alignment" — gpt-image-2 plans this before
  generating; NB2 is more of a stylized illustrator.
- **Composition:** if you want to compose the actual approved symbols
  INTO the paytable layout, `gpt2_edit` accepts up to ~16 reference
  images and composites them with the prompt's structure.

When you call this skill, if `OPENAI_API_KEY` is set:
- For the layout-only paytable (placeholder slots): use **`gpt2_generate`**
  at `quality: high` and `image_size: "2K"` (gpt-image-2's stable
  production ceiling — 4K is experimental). Same `output_dir` /
  `asset_name` shape as the NB2 path.
- For composing the real symbols into the paytable: use **`gpt2_edit`**
  with the approved symbol PNGs as `extra_references`, also at
  `image_size: "2K"`. If you need 4K marketing output, generate at 2K
  with gpt2 and then run `nb2_upscale` on the approved result.

If `OPENAI_API_KEY` is NOT set, fall back to `nb2_generate` at
`image_size: "2K"` and treat the text as approximate — it'll need to be
re-composited at runtime by engineering.

See `shared/gpt_image2_prompting.md` for full guidance on the gpt2 tools.

## Surface rules

- **Symbol art:** placeholder squares only — DO NOT generate decorative
  symbol art here. Real symbols are pulled from the approved set.
- **Background:** dimmed dark themed panel (60–80% dark overlay or solid)
- **Body text:** light off-white, never pure white (pure white is harsh on dark BG)
- **Pay values:** warm gold tabular numerals
- **Section header:** "PAY TABLE" at the top
- **Row count:** 4–6 symbols per page in portrait

## Prompt — paytable layout

```
A mobile slot game paytable info screen, <theme_summary> themed, <style_lock>,
dimmed dark background panel with subtle <palette_leads.primary> themed border,
six rows of empty symbol slots paired with pay value text in
warm gold tabular numerals,
section header "PAY TABLE" at the top, generous padding,
body text light off-white never pure white,
no actual symbol art (placeholder squares only),
mobile-readable typography for a portrait paytable layout.
```

## Pre-gen quick checks

- [ ] "No actual symbol art (placeholder squares only)" stated
- [ ] "PAY TABLE" header text included
- [ ] Body text is "off-white, never pure white"
- [ ] Pay values are "warm gold tabular numerals"
- [ ] Row count specified (typically 6)

## Post-gen quick checks

- [ ] Symbol slots are clearly placeholder squares (nothing drawn inside them)
- [ ] Header reads "PAY TABLE"
- [ ] Pay value column is gold and feels like tabular numerals (consistent width)
- [ ] Background panel is dimmed (the game BG would show faintly through it)
- [ ] Generous padding — not crowded

## What happens after generation

This skill produces the **layout**. The paytable in the final game is a
composite:

1. `/slot-step-06` generates `Paytable_NNN.png` (the chrome layout)
2. `/slot-step-03` produces `HP1_NNN.png`, `MP1_NNN.png`, etc.
3. Production composites the approved symbol PNGs into the paytable
   slots — done outside this plugin in your asset pipeline

Do NOT try to generate the symbols inline as part of the paytable. They
won't match the approved reel art and will break player trust.
