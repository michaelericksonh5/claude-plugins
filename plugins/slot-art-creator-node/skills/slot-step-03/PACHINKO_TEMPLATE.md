# Pachinko / Drop-Style Template

Pachinko-style games (Drop Zone family) are **fundamentally different**
from spinning-reel slots. They use a vertical drop mechanic — balls fall
through pegs into award buckets. The "symbol manifest" for these games is
correspondingly different.

If a brief lists `BALL`, `PEG`, or `BUCKET_*` prefixes, this is a
pachinko game. Use this template instead of the standard reel-symbol
templates.

For non-pachinko slots, ignore this template entirely.

## When to use

- Brief explicitly names "Pachinko" or "Drop" as the reel type
- Symbol manifest contains `BALL`, `PEG`, `BUCKET_*` prefixes
- Game info mentions "vertical drop", "pegs", "buckets"

This template uses the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`. The `<style_lock>` placeholder
below is substituted with the same text at prompt-assembly time.

## Universal rules

- **Background:** flat solid black (each symbol exports as transparent / black BG)
- **Each symbol is a UI element more than a "symbol"** — they're game-board pieces
- **High contrast**: pachinko boards are visually busy; each piece must stand apart
- **Theme integration**: pegs and buckets must read as part of the game's world
  (e.g., a Greek mythology pachinko game has columns or temple pegs, not generic dots)

---

## `BALL` — drop ball

The animated dropping element. Multiple balls in flight is common; one
art produces all of them at runtime via animation.

```
A single drop ball game piece for a pachinko-style mobile slot,
spherical with a clean specular highlight in the upper-left,
<theme_summary> themed surface treatment — engraved, painted, or stylized
to match the game's visual world,
metallic / glossy finish in <palette_leads.primary> hue,
fills the cell prominently with a small border,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one ball in the frame.
```

Tier escalation if multiple ball types exist (e.g., bronze / silver / gold balls):
- Bronze ball: copper hue with engraved theme detail
- Silver ball: chrome hue with subtle theme detail
- Gold ball: gilded hue with premium theme detail
- Platinum ball: white-gold hue with maximum theme detail

---

## `PEG` — deflector peg

The deflectors that scatter falling balls. Often a dense grid of these on
the board.

```
A single deflector peg game piece for a pachinko-style mobile slot,
small <theme_summary>-themed cylindrical or spherical peg —
could be a temple column shard, a crystal nub, a metallic stud,
depending on the theme,
fills the cell with generous padding (pegs appear small in the game),
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one peg in the frame.
```

Pegs are deliberately small in the visual hierarchy — they're a hundred
identical pieces on the board. Don't over-render.

---

## `BUCKET_x<value>` — award bucket

The landing buckets at the bottom of the board with multiplier values.
Each multiplier denomination gets its own bucket art.

```
A pachinko award bucket for a "<value>" multiplier slot,
themed receptacle with the multiplier value space visible at the front,
<tier_metallic> finish (bronze for x2-x5, silver for x10-x25, gold for x50-x100, platinum for x500+),
clean text space reserved for the runtime "<value>" overlay,
<theme_summary> themed,
fills the cell prominently with a small border,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one bucket in the frame.
```

Substitute `<value>` based on the brief's bucket denomination set
(typical: x2, x5, x10, x25, x50, x100, x500, x1000).

Tier convention (matches multiplier badge tiers):
- x2–x5: bronze / copper
- x10–x25: silver / blue
- x50–x100: gold ornate
- x500+: platinum / diamond

---

## Generating a full pachinko set

When a brief calls for a pachinko game's full symbol set, generate in
this order:

1. `PEG` first — the most common piece on the board, sets the theme tone
2. `BALL` (one per tier if multiple) — uses peg as a reference for theme consistency
3. `BUCKET_*` denominations in ascending value order — each references prior buckets
   so the metallic tier escalation reads consistently

Pass each prior approved piece as a reference image when generating the
next one.

## Pre-gen quick checks

- [ ] Brief explicitly indicates pachinko / drop-style game
- [ ] `<theme_summary>` is integrated into the piece's surface treatment
- [ ] Background is `flat solid black background, no gradients`
- [ ] For buckets: clean text space reserved for runtime value
- [ ] For multiple balls / buckets: tier metallic finish matches the denomination

## Post-gen quick checks

- [ ] Piece reads as theme-integrated (not a generic ball / peg / bucket)
- [ ] Buckets escalate in metallic tier visually
- [ ] Pegs are small enough not to dominate when many appear together
- [ ] Each piece is recognizable at thumbnail size

## What NOT to generate from this template

- The pachinko **board** itself (that's a background — use `slot-step-05`)
- The bucket grid layout (that's UI — use `slot-step-06`)
- Win banners, multiplier celebrations (UI — use `slot-06`)

This template is only for the per-piece game elements (ball, peg, bucket).
