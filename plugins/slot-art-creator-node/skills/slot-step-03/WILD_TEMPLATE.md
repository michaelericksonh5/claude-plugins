# Wild Symbol Template

The wild is the most distinctive symbol in the set. Its job is to be
**immediately recognizable as different** — a player glancing at the reel
must identify the wild from peripheral vision alone.

The wild breaks the theme in **THREE** dimensions:

1. **Silhouette family** — different outer shape than the pay symbols
   (sunburst/radial/medallion vs. the pay symbols' cartouche/shield/rectangle)
2. **Category** — different subject category from the pay set (text vs.
   characters, or object vs. characters)
3. **Color** — primary color does NOT appear in `palette_leads.primary` or
   `.accents`

This triple-break is what makes wilds readable on a fast spin. Just changing
color alone — keeping a similar plaque shape — is not enough. Peripheral
vision picks up shape silhouette before color.

This template uses the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1) is
prepended to every prompt verbatim — it lives in `project.json.style_anchor.text`.

## Tier rules

- **Background:** flat solid black, no gradients
- **Silhouette break:** outer shape is a DIFFERENT family than every pay symbol
- **Category break:** if the rest of the set is characters, the wild is text or an object. If the rest is objects, the wild is text. Never the same category.
- **Color break:** wild's primary color does NOT appear in `brief.palette_leads.primary` or `.accents`
- **Size phrase:** "barely contained fills frame edge to edge, large and dominant"
- **Text policy:** the word "WILD" itself is allowed (and common) as part of or all of the symbol

## Prompt — Wild

```
[RENDER STYLE — LOCKED to <style_lock>]
Same rendering technique as the rest of the set. Bold confident forms,
sharp clean edges. The wild's rendering must still feel like it belongs
to the same game world even though every other axis is breaking from the
pay-symbol set.

[BADGE SHAPE — categorically different from the pay symbols]
This wild's outer silhouette MUST be a DIFFERENT SHAPE FAMILY than every
pay symbol in the set. If the pay symbols use vertical cartouches or
shields, this wild uses a <radial sunburst / circular medallion /
hexagonal emblem — pick one per brief>. A player glancing at the reel
must identify this as the WILD from peripheral vision alone, based on
silhouette shape — not just color.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: WILD (special symbol, not part of the value gradient).
- Palette: <wild.breaks_theme_via from brief — e.g., "electric cyan
  lightning", "hot magenta neon", "acid green emission">. This color
  must NOT appear anywhere in palette_leads.primary or .accents.
- Halo / aura: strong emission glow in the wild's break-color radiating
  from the badge — far stronger than any HP halo. The break color is
  the most saturated element on the entire reel.
- Size phrasing: "barely contained, fills the frame edge to edge".

[SUBJECT INSIDE — "WILD" text label]
The word "WILD" is the most readable text at reel cell size. <If the
brief specifies a wild character or motif: a secondary thematic element
behind or below the WILD text. The WILD text is always the dominant
foreground element.>

[MOBILE CONSTRAINTS]
Centered on flat solid black background, no gradients. Clear silhouette
at thumbnail size — but more importantly, the OUTER SILHOUETTE SHAPE
reads instantly as different from every pay symbol. Sharp clean edges.

high quality game asset, professional slot game art, only one symbol
in the frame.
```

Substitution guide:
- Pick the silhouette family from a list that's categorically different
  from the pay symbols' silhouette family. If pay symbols are vertical
  cartouches, wild candidates: sunburst, circular medallion, hexagonal
  emblem, diamond, irregular asymmetric badge.
- `<wild.breaks_theme_via>` — pull from `brief.wild.breaks_theme_via`
  (e.g., `"electric cyan rim light"`, `"hot magenta neon"`).

## Pre-gen quick checks

- [ ] `style_anchor.text` (from `project.json.style_anchor.text`) is prepended to the prompt verbatim
- [ ] Wild's silhouette family is DIFFERENT from every pay symbol's silhouette family
- [ ] Wild's category is DIFFERENT from the rest of the set
- [ ] Wild's primary color does NOT appear in `palette_leads.primary` or `.accents`
- [ ] "Barely contained" or similar fill phrase is in the prompt
- [ ] Background is `flat solid black background, no gradients`
- [ ] Break-color is described as the most saturated element on the reel

## Post-gen quick checks

- [ ] At thumbnail size, the wild's OUTER SHAPE reads as a different family from the pay symbols (squint test — close your eyes halfway)
- [ ] Wild's color is unique to the wild (doesn't appear in any HP/MP/LP)
- [ ] Wild fills the frame to its edges (not floating in empty space)
- [ ] If the wild is text, the text is the dominant element
- [ ] The wild's emission/halo is visibly stronger than any HP halo in the set

## Common failure modes

- **Wild has the same plaque shape as the HP set, just recolored** — the
  silhouette break failed; regenerate with explicit "different shape
  family" instruction and name the target family (sunburst, medallion).
- **Wild matches the theme** — regenerate with stronger break instruction.
- **Wild's color is in the palette** — regenerate with explicit "use a
  color that doesn't appear in the rest of the set".
- **Wild is too small / floats in empty space** — restate "barely
  contained, fills frame edge to edge".
