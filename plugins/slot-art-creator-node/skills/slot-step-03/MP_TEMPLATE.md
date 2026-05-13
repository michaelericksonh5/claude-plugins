# MP — Mid-Pay Symbol Templates

MP symbols sit visibly below HP and visibly above LP in the value gradient.
There are usually 2 in a set (MP1, MP2). They're typically themed objects
relevant to the world — not characters (that's HP) and not generic
card/gem fillers (that's LP).

These templates use the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1) is
prepended to every prompt verbatim — it lives in `project.json.style_anchor.text`.

## Tier rules

- **Background:** flat solid black, no gradients (same as HP)
- **Palette:** moderate warm-leaning, NOT as saturated as HP
- **Light:** subtle highlight only — NO rim glow (reserved for HP)
- **Size phrase:** "one tier below the high-pay characters, generous size with visible padding"
- **Tier hierarchy:** noticeably cooler/less saturated than HP, noticeably warmer/larger than LP

## Prompt — MP themed object

```
[RENDER STYLE — LOCKED to attached key art reference]
Match the reference for rendering technique and surface finish. Same
rendering language as the HP set. <surface-finish phrase from brief —
e.g. "satin semi-matte sculpted clay + soft paint">. Bold confident
forms, not photorealistic. Inherit ONLY the rendering technique from
the reference — ignore its background color and palette, which are
specified below.

[PLAQUE SHAPE — simpler than HP]
<Plaque construction: one tier less ornate than HP — narrower frame,
fewer motifs, less filigree>. Generous size but visibly one tier below
the HP plaques in frame complexity and outer scale. Maximum 2–3
decorative motifs on the frame.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: mid-pay (MP<N>), one tier below the high-pay characters.
- Enamel field color: <moderate warm-leaning color from palette_leads> —
  cooler and less saturated than the HP enamels.
- Halo / aura: NO halo, NO rim glow. Subtle highlight only on the
  subject's upper-left surface.
- Size phrasing: "generous size with visible padding, one tier below
  the high-pay characters".

[SUBJECT INSIDE — <subject from manifest>]
<1–2 sentence subject brief>.

[MOBILE CONSTRAINTS]
Clear silhouette at thumbnail size. Visible padding around the subject —
do not fill the frame edge to edge. Centered composition, perfectly
upright. Flat solid black background, no gradients, no patterns.

high quality game asset, sharp clean edges, professional slot game art,
mobile-optimized icon, only one symbol in the frame.
```

## Pre-gen quick checks

- [ ] `style_anchor.text` (from `project.json.style_anchor.text`) is prepended to the prompt verbatim
- [ ] `[RENDER STYLE — LOCKED]` block present with explicit "Inherit ONLY X, ignore Y" clause
- [ ] Background is `flat solid black background, no gradients`
- [ ] Palette is moderate — explicitly cooler/less saturated than HP
- [ ] No glow language — "subtle highlight only"
- [ ] Decorative motifs capped at 2–3 on the plaque frame
- [ ] Subject matches the manifest

## Post-gen quick checks

- [ ] Silhouette readable
- [ ] Visibly less saturated than HP1/HP2 in the set
- [ ] Visibly warmer/richer than LP in the set
- [ ] No rim glow (that's HP territory)
- [ ] Light direction consistent with the set
- [ ] Plaque frame is visibly simpler than HP plaques in the same set
