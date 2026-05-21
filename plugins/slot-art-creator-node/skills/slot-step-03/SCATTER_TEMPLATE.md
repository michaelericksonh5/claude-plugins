# Scatter Symbol Template (`SC` prefix — legacy scatter)

The scatter is the bonus trigger. It's instantly recognizable as a
**circular badge with a label and radiant burst**. Players need to spot it
on a busy reel grid in under a second.

This template covers the **legacy `SC` / `SC1+` prefix**. Modern H5G
games typically use the **WYS family** (a `WY` symbol with
`mechanic: scatter`) for the same role — Tesla `WY1`, Bankrush Gamma
`WY1`, Chevy-Lite `WY1` all play the scatter role under the WYS
prefix. When the brief's manifest puts a `WY<N>` with
`mechanic: scatter`, route to `COIN_TEMPLATE.md` (the WYS Family
Template) and apply the scatter role overlay from there — not this
template. This template is for the literal `SC` prefix only.

These templates use the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`.

## Tier rules

- **Background:** flat solid black, no gradients
- **Shape:** circular badge — NOT square, NOT a free-form object
- **Palette:** warm and luminous — gold, amber, sun-bright accents are allowed and encouraged (this is the OPPOSITE of LP)
- **Label:** the word "SCATTER" or `brief.scatter.label` is part of the symbol
- **Size phrase:** "prominent, circular badge-shaped, fills the cell"

## Prompt — Scatter

```
"<scatter.label>" label, special bonus symbol,
circular badge-shaped, prominent, fills the cell,
warm luminous <palette_leads.primary> with radiant burst rays,
radiant warm palette,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Substitution:
- `<scatter.label>` — pull from `brief.scatter.label` (default: `"SCATTER"`)

## Pre-gen quick checks

- [ ] `style_anchor` (from `project.json.style_anchor.text`) is prepended verbatim
- [ ] Shape is "circular badge" stated explicitly
- [ ] Label text is part of the prompt
- [ ] Background is `flat solid black background, no gradients`
- [ ] Warm luminous palette is allowed (this is one of the few places where warm palettes apply outside HP)

## Post-gen quick checks

- [ ] Recognizable as a circular badge
- [ ] Label text is readable at thumbnail size
- [ ] Distinct from any HP symbol (radiant burst is the giveaway)
- [ ] Background is flat black

## Variations

- **Bonus trigger** uses the same template with `label = "BONUS"` and a slightly different burst pattern
- **Free-spins trigger** sometimes uses the scatter symbol; check the brief
