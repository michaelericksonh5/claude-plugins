# Bezel / Reel Frame Template

The bezel (reel frame) sits between the background and the symbol grid.
Its job is to frame the reels, not steal attention. **Reel is always the
hero.** Default thickness is `thin`. Only go ornate when the brief
explicitly calls for it.

## Surface rules

- **Background:** flat solid black (it's a transparent overlay; the BG sits behind it in production)
- **Center:** transparent or semi-transparent so the reels show through
- **Outer border weight:** matches the interior grid divider lines
- **Aspect ratio:** match game orientation (`9:16` portrait or `16:9` landscape) — passed via API arg, not prompt body
- **Grid:** state `<cols>×<rows>` from `brief.grid` — omitting causes NB2 to guess

## Thickness vocabulary

| Level | Exact phrase to use in prompt |
|---|---|
| `ultra-thin` | `"outer border the same width as the interior divider lines — a razor-thin stone strip"` |
| `thin` (default) | `"outer frame slightly heavier than the interior lines but still narrow — not ornate"` |
| `moderate` | `"frame about a third of a symbol cell's height"` |
| `ornate` | `"thick sculptural frame with dimensional relief elements"` |

## Prompt — bezel, ultra-thin / thin (default)

```
A <cols>×<rows> <theme_summary>-themed slot reel frame floating on a
flat solid black background, <style_lock>,
outer stone border the same width as the interior grid lines —
ultra-thin, razor strip, not a thick frame,
one-pixel <palette_leads.primary>-tinted gold inner liner separating
the stone from the transparent black cell interiors,
matte stone surface, upper-left key light at 10 o'clock,
no glow, no chromatic aberration, no color fringing on the outer edge,
<cols> columns × <rows> rows of transparent black cells,
interior dividers matching the outer border width,
no symbols inside the cells, no text, no embellishment,
flat solid black outer background,
professional slot game art.
```

## Prompt — bezel with engraved theme motifs

Use when the brief calls for a bit of theme decoration without going ornate.

```
[Same as thin template but replace "no embellishment" with:]
shallow engraved <theme_summary> motifs on the corner blocks and
center top/bottom/side blocks only —
subtle relief carving, not painted, not brightly colored,
recessive against the stone surface.
```

## Material library — named directions

Bezels are an art problem where naming a specific material direction up
front beats trying to describe the look from scratch. Pick one (or
combine 2–3) per game and lock it into the prompt as a constraint. This
library is condensed from internal H5G bezel research, with every
entry validated against shipped production assets.

### Stone families

| Direction | Use when the brief calls for... |
|---|---|
| **Obsidian** | Volcanic / dark / premium themes. Dark volcanic stone, near-black with subtle warm highlights. Pair with gold inlay. |
| **Basalt** | Earthy / temple / ancient themes. Charcoal stone with neutral cool tones. Pair with copper or bronze inlay. |
| **Stepped Temple Stone** | Egyptian / Mesoamerican / temple themes. Geometric stepped relief along the outer edge — feels carved, not poured. |
| **Marble (warm)** | Roman / luxury / Olympic themes. Warm-toned marble with subtle veining. Pair with antique gold trim. |
| **Marble (cool)** | Norse / icy / mystical themes. Cool-toned marble. Pair with silver or pale gold. |
| **Sandstone** | Desert / pyramid / oasis themes. Warm tan tone with visible weathering. Pair with bronze or hammered copper. |

### Metalwork families

| Direction | Use when the brief calls for... |
|---|---|
| **Aged Gold Filigree** | Treasure / fairytale / regal themes. Soft warm-gold rim with curling scrollwork. Inlay should be thinner than the reel dividers. |
| **Hammered Copper** | Steampunk / industrial / rustic themes. Visible hammer marks, warm metallic surface, patina in recessed areas. |
| **Brushed Brass** | Art-deco / 1920s / luxury-mechanical themes. Anisotropic streaks along the bezel direction. |
| **Bone-Tooth Inner Rim** | Tribal / shamanic / primal themes. Pale bone inlay along the inner rim only — outer can be wood or stone. |
| **Iron / Wrought Frame** | Gothic / castle / horror themes. Black iron, visible rivets at corners. Cool tone, low saturation. |

### Cultural-motif families

| Direction | Use when the brief calls for... |
|---|---|
| **Obsidian Papel Picado Rail** | Día de los Muertos / Latin themes. Obsidian base with papel picado (cut-paper) silhouette rail along the top edge — magenta or warm-gold paper, intricate but at a single visual scale. |
| **Basalt Calavera Corners** | Skull / Día de los Muertos themes. Charcoal basalt frame with stylized calavera (sugar-skull) blocks at each corner. |
| **Lotus Scroll Rail** | Asian / Buddhist / floral-Asian themes. Carved lotus motifs along the bezel center blocks, paired with jade-green or red enamel accents. |
| **Celtic Knotwork Inlay** | Norse / Celtic / mythic themes. Continuous interwoven knot pattern along the bezel, in pale gold or silver. |
| **Egyptian Hieroglyph Frieze** | Egyptian-specific themes. Bottom-center block carries hieroglyph-style symbols at small scale — recessive, not the focal point. |

### Hybrid / modern families

| Direction | Use when the brief calls for... |
|---|---|
| **Neon-Edged Black** | Cyberpunk / Vegas-modern themes. Black frame with a thin neon emission strip along the inner rim — magenta, cyan, or acid green. |
| **Chrome with Glitch Noise** | Sci-fi / digital themes. Polished chrome surface with subtle digital noise / scanline artifacts. |
| **Floating Holographic Trim** | Future / sci-fi themes. Transparent prismatic edge effect at the outer border. Pairs with chrome or matte black. |
| **Bamboo Wrap** | Asian / nature themes. Natural bamboo segments wrapping the frame. Warm honey tone with subtle banding from the bamboo nodes. |

### Composition rules across all directions

These apply regardless of which material you pick:

- **Limit motif detail to 3 visual scales.** A bezel that has very fine
  filigree, medium-sized symbols, and large corner blocks reads as
  cluttered. Pick three sizes; don't fan out into four or five.
- **4–6 colors maximum** in the bezel. The reel symbols already carry
  the palette story — the bezel is meant to recede.
- **Inlay is always thinner than the reel dividers.** This is the
  single rule most often violated. If the brief gives you an "ornate"
  bezel, the inlay's outer edge should still be visibly thinner than
  the grid lines, so it visually nests inside the structural frame
  rather than competing with it.
- **Match the symbol set's light direction.** Upper-left key light at
  10 o'clock by default. Bezel highlights should be on the upper-left
  corner blocks and the upper edge.

## Pre-gen quick checks

- [ ] Grid dimensions stated as `<cols>×<rows>`
- [ ] "Reel is the hero" intent stated (the prompt should not describe a frame that dominates)
- [ ] Background is `flat solid black background, no gradients`
- [ ] No glow / no chromatic aberration / no color fringing stated
- [ ] No symbols / no text / no embellishment inside the cells

## Post-gen quick checks

- [ ] Center cells are transparent or near-transparent (reels would be visible)
- [ ] Frame doesn't dominate visually
- [ ] Grid divider lines match the outer border weight
- [ ] No accidental decorative elements inside the cells
- [ ] Light direction matches the symbol set's upper-left convention
