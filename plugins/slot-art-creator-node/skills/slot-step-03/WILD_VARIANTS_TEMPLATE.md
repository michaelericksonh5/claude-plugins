# Wild Variants Template

The basic wild template (`WILD_TEMPLATE.md`) covers the standard
substitute-for-anything wild. Most modern slots ship **multiple wild
variants** with different mechanics — each gets its own ID (`WD1`,
`WD2`, `WD3`) and its own visual treatment.

This template covers nine common variants. Read the section that
matches the variant in the brief. The base wild rules from
`WILD_TEMPLATE.md` (theme break + color break + barely-contained sizing)
apply to ALL variants.

This template uses the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`. The `<style_lock>` placeholder
below is substituted with the same text at prompt-assembly time.

## Universal rules (apply to every variant)

- **Background:** flat solid black, no gradients
- **Theme break:** different category from the rest of the set
- **Color break:** primary color does NOT appear in `palette_leads`
- **Distinctness:** each variant must be visually distinguishable from
  every other wild variant in the same game
- **Currency:** the word "WILD" is allowed and common as part of the symbol

---

## Sticky Wild

Locks in place for N spins. Visual cue: a **chain, pin, or lock motif**
overlaid on the wild design.

```
"WILD" label, special slot wild symbol — sticky variant,
locked in place with chains or a pinned anchor element overlaid,
<wild.breaks_theme_via> palette breaking the theme,
barely contained — fills frame edge to edge,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Additional pre-gen check:
- [ ] Lock / chain / pin element is described and visually integrated

---

## Stacked Wild

Renders as a **vertical stack** covering the full reel column. Even when
generated as a single cell, the art should hint at the stacked context
with an aspect ratio that reads as elongated.

```
"WILD" label, special slot wild symbol — stacked variant,
elongated vertical treatment suggesting a multi-cell stack,
<wild.breaks_theme_via> palette,
barely contained, fills frame top to bottom edge,
<style_lock>,
centered on flat solid black background no gradients,
sharp clean edges, professional slot game art.
```

Generate with `aspect_ratio: "1:1"` for the manifest cell. The runtime
composites the stacked appearance.

---

## Expanding Wild

Grows to fill the full reel after landing. Visual cue: **expansion rays
or a pulse motif** suggesting outward growth.

```
"WILD" label, special slot wild symbol — expanding variant,
expansion rays radiating outward from the central wild element,
<wild.breaks_theme_via> palette,
barely contained — fills frame edge to edge,
<style_lock>,
centered on flat solid black background no gradients,
sharp clean edges, professional slot game art.
```

---

## Walking Wild / Wild Train

Moves one position per spin (also called "Wild Train" or snake wild).
Visual cue: a **directional arrow or motion blur trail**.

```
"WILD" label, special slot wild symbol — walking variant,
directional motion treatment with trailing motion blur or arrow indicators
suggesting forward movement,
<wild.breaks_theme_via> palette,
barely contained — fills frame edge to edge,
<style_lock>,
centered on flat solid black background no gradients,
sharp clean edges, professional slot game art.
```

For the "Wild Train" snake variant, the symbol may be themed as
**linked carriages** rather than a single wild — check the brief.

---

## Respin Wild

Triggers a respin when it lands. Visual cue: a **refresh / circular-arrow
loop motif**.

```
"WILD" label, special slot wild symbol — respin variant,
circular refresh arrow loop integrated into the wild treatment,
<wild.breaks_theme_via> palette,
barely contained — fills frame edge to edge,
<style_lock>,
centered on flat solid black background no gradients,
sharp clean edges, professional slot game art.
```

---

## Transforming Wild

Converts low-pays to high-pays. Visual cue: **morph / particle dissolve**
suggesting transformation in motion.

```
"WILD" label, special slot wild symbol — transforming variant,
particle dissolve or morphing energy treatment around the wild element
suggesting transformation in motion,
<wild.breaks_theme_via> palette,
barely contained — fills frame edge to edge,
<style_lock>,
centered on flat solid black background no gradients,
sharp clean edges, professional slot game art.
```

---

## Multiplier Wild

Multiplies the win it's part of (×2, ×3, ×5 …). The numeric multiplier
is the dominant element — even more prominent than the WILD label.

```
"×<value>" multiplier with smaller "WILD" subtitle, special slot wild symbol,
multiplier number as the dominant focal element in metallic gold or
<wild.breaks_theme_via> palette,
barely contained — fills frame edge to edge,
<style_lock>,
centered on flat solid black background no gradients,
sharp clean edges, professional slot game art.
```

Substitute `<value>` from the brief (typically 2, 3, 5, or 10).

Additional pre-gen check:
- [ ] Multiplier number is the dominant focal element
- [ ] Value matches the brief

---

---

## Duplicating Wild

Replicates itself into adjacent positions when it lands (Green Machine
Blitz mechanic). Visual cue: **mirror / clone aura** around the wild
showing the duplication direction.

```
"WILD" label, special slot wild symbol — duplicating variant,
clone aura with mirror echoes radiating sideways from the central wild,
suggesting visual replication into adjacent cells,
<wild.breaks_theme_via> palette breaking the theme,
barely contained — fills frame edge to edge,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Quick check:
- [ ] Mirror / clone effect is visible but doesn't crowd the central wild element

---

## Scatter-Wild Hybrid (`SW`)

Acts as **both scatter and wild** simultaneously (Book of Dead's Book
symbol is the canonical example). Triggers free spins when 3+ land,
AND substitutes for pay symbols. The art combines a circular scatter
badge composition with the WILD label/break.

```
Hybrid scatter and wild slot symbol, "SCATTER WILD" or theme equivalent,
combines the radiant burst rays of a scatter symbol with the dominant
WILD label aesthetic of a wild symbol,
warm luminous palette characteristic of scatters,
"WILD" or hybrid label clearly readable,
fills the cell prominently — even larger than a regular scatter,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Quick checks:
- [ ] BOTH scatter aesthetic (radiant rays, circular composition) AND wild aesthetic (WILD label, theme break) present
- [ ] Reads as more important than either a regular scatter or a regular wild
- [ ] Differentiable from `SC` (no wild label) and from `WD1` (no radiant burst)

---

## Compound prefixes that route here

Several compound prefixes combine the Wild family with another role.
They follow the universal wild rules above plus a secondary overlay
from the named family. All of them use the same `<PREFIX>_NNN.png`
naming pattern as primitive prefixes and live in `Symbol_Art/`.

### `WJP`, `WJP1`+ — Wild + Jackpot contribution

A wild that also contributes to the jackpot pool when it participates
in a winning line (Billionaire's Gamma pattern). Base = wild
variants from this template; overlay = jackpot-contribution cues
pulled from `JACKPOT_TEMPLATE.md`.

```
[Wild base — pick the closest sibling variant from this template,
or generate from the standard wild grammar]
+
[Jackpot overlay]: metallic edge tint matching the brief's highest
jackpot tier finish (typically gold for Grand). Subtle tier sigil
(crown, star) integrated near the wild label without overpowering
it. Soft warm-gold halo at the edges.
```

The wild label and category break still dominate — the jackpot
overlay is a tier-mark, not a takeover. A WJP should still read as
"a wild" at a glance, with "and it counts toward the jackpot" as a
secondary cue.

### `WDWY`, `WDWY1`+ — Wild + WYS (scatter-wild hybrid for WYS family)

A wild for the WYS family symbols that often also acts as a scatter
(Chevy family pattern). Base = scatter-wild hybrid section above;
overlay = WYS coin/portal silhouette behind the wild label.

```
[Scatter-wild hybrid base from the "Scatter-Wild Hybrid (`SW`)"
section above]
+
[WYS overlay]: behind the WILD label, a coin/portal disc silhouette
echoing the WYS family. The disc carries the wild's break color, not
the family's standard hue — this is a WILD that happens to live in
WYS family territory, not a coin with a wild label.
```

The composition keeps the wild's category break and electric palette
dominant; the disc/portal silhouette is the WYS visual hook that
ties it to the family in the player's mind.

### `WDSF`, `WDSF1`+ — Wild + SF (wild SF created by duplication)

A wild SF created by a duplication mechanic (Chevy-Alt pattern). Base
= wild variants from this template; overlay = SF family
sphere/portal silhouette behind the wild label, pulled from
`MYSTERY_TEMPLATE.md` (the SF Family Template).

### `MUWD`, `MUWD1`+ — Multiplier Wild

Same as the Multiplier Wild variant above. The `MUWD` prefix is the
H5G compound alias for the same mechanic — use the
[Multiplier Wild](#multiplier-wild) section's prompt as-is. Filename
will be `MUWD1_001.png` etc.

### `MUWDBO`, `MUWDBO1`+ — Multiplier Wild + Bonus framing

Same as the Multiplier Wild above, with an added bonus-trigger
overlay layered on. Pull the warm-radial-burst cue from
`BONUS_TRIGGER_TEMPLATE.md`. The result reads as "a multiplier
wild that ALSO triggers the bonus when N land" — common in Honda's
combo-bonus mechanic.

```
[Multiplier Wild base from this template]
+
[Bonus overlay]: warm radial burst rays behind the wild label, plus
an optional small "BONUS" or themed tag at the bottom of the symbol.
The multiplier `×N` slot still dominates; the bonus cue is a
secondary signal.
```

---

## Pre-gen quick checks (all variants and compounds)

- [ ] `style_anchor.text` (from `project.json.style_anchor.text`) is prepended to the prompt verbatim
- [ ] Variant-specific visual cue is in the prompt (chain for sticky, motion blur for walking, etc.)
- [ ] For compounds: secondary-overlay cues from the partner family are present (jackpot tier mark for WJP, WYS portal silhouette for WDWY, SF sphere silhouette for WDSF, bonus burst for MUWDBO)
- [ ] Color is NOT in `palette_leads.primary` or `.accents`
- [ ] Category breaks the rest of the set
- [ ] "Barely contained" / fill phrase present
- [ ] Background is `flat solid black background, no gradients`

## Post-gen quick checks (all variants)

- [ ] Visually distinguishable from every other wild variant in this game
- [ ] Variant cue is unmistakable (locked feels locked, walking feels in motion)
- [ ] Reads as a wild — the WILD label or wild meaning is present
- [ ] Color is unique to this wild
- [ ] Fills the frame; doesn't float in empty space

## Generating multiple variants in one game

When a game ships with two or more wild variants:
1. Generate the simplest variant first (usually the standard wild)
2. Use it as a reference image for subsequent variants
3. State explicitly in each subsequent prompt: "visually distinct from
   the [other variant] already generated — different motif, different
   accent color"
4. After all variants are generated, read them side by side and confirm
   each one's mechanic reads at a glance
