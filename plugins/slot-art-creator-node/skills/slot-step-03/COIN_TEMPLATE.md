# WYS Family Template (`WY` / `WYS` prefixes)

The WYS family is the single most-used special-symbol family in H5G's
production library. Across 26 shipped GDDs the catalog shows `WY1`
alone used for **eight different roles**: hold-and-spin coin, WYSIWYG
collector, scatter, random-wilds shooter, collector + multiplier,
adder, HP-equivalent direct payout, and Loot Link trigger. Every one
of those `WY1` symbols looks like the same family — a coin, portal,
or spherical feature-token — but the mechanic varies per game.

**Family rule: visual is stable, role comes from the brief.** Read
`brief.symbol_manifest[].mechanic` for the specific role each `WY<N>`
or `WYS<N>` plays in this game, then layer that role's overlay cues
on top of the universal coin/portal silhouette.

These templates use the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`.

## Universal rules (every WYS member)

- **Shape:** circular coin, portal disc, sphere, or medallion. The
  silhouette must read as "round feature-token" before any role cue
  is layered on.
- **Background:** flat solid black, no gradients.
- **Currency / numeral space:** clean blank area in the center
  reserved for the runtime overlay — DO NOT paint a number into the
  art unless the brief explicitly calls for a static label.
- **Edge:** thick metallic outline / rim consistent with the family.
- **Sizing phrase:** "fills the cell, prominent, slightly larger than
  the LP/MP symbols".
- **Differentiation:** when multiple WYS variants exist in one game,
  hue families must be strongly distinct (not subtle shifts) so
  players read the difference at a glance during fast spins.
- **Halo:** warm luminous halo radiates **from the disc**, with the
  canvas background staying flat black — never bleed glow onto the BG.

## Color convention (default — overridden by the brief)

When the brief doesn't specify variant colors, fall back to:

| ID | Default color | Default role |
|---|---|---|
| `WY1` | gold | standard coin — currency value |
| `WY2` | red / crimson | random-wilds variant — shoots wilds onto the matrix |
| `WY3` | green / emerald | special collector — pins to position, fills a side meter |
| `WY4` | blue / silver | combined trigger / special bonus launcher |

`WYS1` / `WYS2` typically follow `WY1` / `WY2` conventions. Always
check `brief.symbol_manifest[].subject` for the actual color the
brief specifies — many games override the defaults (Billionaire's
series uses purple `WY1` and green `WY2` for direct-payout roles,
not the coin defaults).

---

## Brief-driven role overlays

Every WYS symbol uses the universal rules above as its base. The
brief's `mechanic` field for each `WY<N>` / `WYS<N>` selects one of
the role rows below; apply the named overlay cues on top of the base
coin/portal silhouette.

| `mechanic` value | Overlay cues to add to the base coin/portal |
|---|---|
| `hold-and-spin coin` (default) | Flat numeral space dead center. Engraved themed motif behind the numeral space. Coin-grammar rim with sunburst or bevel. |
| `wysiwyg collector` | Dollar / value sigil inside the disc (e.g. `$` glyph, or a stylized currency mark). Disc face slightly recessed — looks like a vessel that collects. |
| `scatter` | Radiant burst rays emanating from the disc. Warmer / more luminous palette than the standard coin. Optional `SCATTER` or `BONUS` label arcs around the disc. **This is the modern H5G scatter pattern (Tesla WY1, Bankrush Gamma WY1, Chevy-Lite WY1) — newer games use WY as the scatter rather than the legacy `SC` prefix.** |
| `random wilds shooter` | Directional arrows or energy beam motif extending outward from the disc. Portal-style swirl behind the disc face (it's shooting things). Hue typically red or electric (Tesla WY2 pattern). |
| `collector + multiplier` | Accumulator gauge or chevron ring around the disc rim. Position-pin / anchor motif at the bottom. `×N` numeric overlay slot reserved at top of the disc (the runtime fills the multiplier; the art reserves space). |
| `adder` | `+` glyph integrated with the numeral space (composed, not stamped). Outward radial arrows hinting that the value spreads. Billionaire's `WY8` / `WY9` pattern. |
| `hp-equivalent direct payout` | Warm-gold premium treatment, same warmth band as HP1. Coin grammar drops the numeral space — instead the disc face shows a themed icon (a coin can render as a "purple gem coin" or "green energy coin" — Billionaire's `WY1` / `WY2` pattern). The result reads more like a premium themed symbol than a coin slot. |
| `loot link trigger` | Portal-style swirl visible behind the disc face. Suggests a doorway / activation into the bonus mode. Often paired with directional energy radiating off the edge. |

When a single GDD uses multiple WYS variants, the brief's per-symbol
`mechanic` selects which overlay row applies to each one. Generate
`WY1` first (typically the "anchor" variant) and pass it as a
reference image when generating sibling variants so the family
grammar stays coherent.

---

## Prompt — `WY1` standard hold-and-spin coin (the default role)

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference for rendering technique, surface finish, and
lighting direction (warm key from upper-left, cool fill from
lower-right). Bold confident forms, no drawn outlines, not
photorealistic. Inherit ONLY the rendering technique from the
reference — ignore its background color and palette, specified below.

[COIN SHAPE — circular hold-and-spin medallion]
A circular gold coin slot symbol, fills the cell prominently. Thick
metallic gold rim with sunburst or beveled-edge treatment. Clean
center reserved for the runtime currency value — DO NOT paint a
number into the art. Layered construction: outer metal rim · inner
recessed face · centered themed engraving · clean numeral space at
the very center.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (WY family).
- Primary palette: warm gold with <palette_leads.primary> theme
  accent on the engraving.
- Halo / aura: warm-gold halo radiating from the coin face. Canvas
  background stays flat pure black.

[SUBJECT INSIDE — themed engraving]
<theme_summary> themed engraving behind the numeral space — a small
icon or motif drawn from the game's vocabulary (a phoenix wing, a
crown, a thematic emblem). Subtle, recessive — the coin grammar
dominates, the engraving is a tier-mark.

[MOBILE CONSTRAINTS]
Recognizable as a tiny thumbnail on a phone. Bold clean rim, high
contrast between the metallic rim and the flat black background.
Centered composition, perfectly upright. Flat solid black background,
no gradients, no patterns.

high quality game asset, sharp clean edges, professional slot game
art, mobile-optimized icon, clear strong silhouette at small sizes,
only one symbol in the frame.
```

---

## Prompt — `WY2` red / random-wilds shooter variant

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference and the previously-generated `WY1` for rendering
technique, rim treatment, and overall coin grammar. Inherit ONLY the
rendering technique from the reference; the palette and overlay cues
below override.

[COIN SHAPE — circular shooter portal disc, same grammar as WY1]
Same coin construction as the `WY1` gold coin already generated —
same overall composition, same rim treatment, same engraving
complexity. Differs in palette and role overlay.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (WY family — random-wilds shooter variant).
- Primary palette: crimson red / electric red with energy-crackle
  highlights on the rim.
- Role overlay: directional arrows or energy beam motif extending
  outward from the disc rim. Portal-style swirl behind the disc face.
  This coin LOOKS LIKE it's shooting something.

[SUBJECT INSIDE — themed engraving (red-shifted)]
Same themed engraving family as `WY1` but rendered in the red-shifted
palette. The engraving doesn't compete with the directional / portal
overlay.

[MOBILE CONSTRAINTS]
Recognizable as a tiny thumbnail. Clearly different from `WY1` by
hue alone. Flat solid black background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, mobile-optimized icon, only one symbol in the frame.
```

---

## Prompt — `WY3` green / collector + multiplier variant

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Same coin grammar as `WY1` / `WY2` already generated — same rim
treatment, same engraving complexity, same overall composition.
Differs in palette and role overlay.

[COIN SHAPE — circular collector medallion]
Same coin construction as the WY family already generated. Add an
accumulator gauge or chevron ring around the disc rim — small
indicator marks suggesting "collected so far". Position-pin / anchor
motif at the bottom of the disc — it pins.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (WY family — collector + multiplier variant).
- Primary palette: emerald green / collector-green with cool
  highlights.
- Role overlay: accumulator gauge or chevron ring · pin/anchor motif
  · reserved `×N` slot at the top of the disc (runtime fills it).

[SUBJECT INSIDE — themed engraving (green-shifted)]
Themed engraving in green-shifted palette, same family as `WY1` /
`WY2`.

[MOBILE CONSTRAINTS]
Clearly different from `WY1` (gold) and `WY2` (red) by hue. The
collector cues are visible at thumbnail size — not micro-decoration.
Flat solid black background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, mobile-optimized icon, only one symbol in the frame.
```

---

## Prompt — `WY4` blue/silver combined trigger / special bonus launcher

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Same coin grammar as the WY family already generated. Differs in
palette and role overlay.

[COIN SHAPE — circular trigger medallion]
Same coin construction. Add a mystical / power aesthetic — the disc
face has a centered emblem suggesting "ultimate" / "trigger" /
"combined-power".

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (WY family — combined trigger / bonus launcher).
- Primary palette: silvery blue / platinum with mystical highlights.
- Role overlay: a centered emblem (a star, a sigil, a power crystal)
  inside the disc face — it's the "best of the coin family".

[SUBJECT INSIDE — themed power emblem]
A power emblem instead of the standard engraving — drawn from the
game's vocabulary but more prominent than a regular tier-mark.

[MOBILE CONSTRAINTS]
Clearly different from `WY1` / `WY2` / `WY3` by hue. Reads as the
"premium" coin of the family at thumbnail size. Flat solid black
background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, mobile-optimized icon, only one symbol in the frame.
```

---

## Prompt — WYS as scatter (modern H5G pattern)

When the brief's `mechanic` for a `WY<N>` is `scatter`, the symbol
plays a scatter role and gets the scatter overlay applied to the
universal WYS coin/portal base. This is the modern H5G pattern
(Tesla WY1, Bankrush Gamma WY1, Chevy-Lite WY1) — for the legacy `SC`
prefix scatter, use `SCATTER_TEMPLATE.md`.

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference for rendering technique. Inherit ONLY the
rendering technique; palette and scatter overlay below override.

[COIN / PORTAL SHAPE — circular scatter medallion]
A circular scatter symbol, fills the cell prominently. WYS family
coin/portal grammar — thick metallic rim, recessed face — but tuned
for scatter readability. Radiant burst rays emanate outward from the
disc. The disc face is luminous and warm.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (WY family — scatter role).
- Primary palette: warm luminous gold / amber — same warmth band as
  the master Scatter convention. Brighter than the standard `WY1`
  coin; this one is meant to be the most visible thing on the reel.
- Halo / aura: strong radiant burst rays + soft sparkle particles
  near the disc face.

[SUBJECT INSIDE — "<scatter.label>" label]
The word "<scatter.label>" (default: "SCATTER") arcs across or sits
inside the disc face, clearly readable at reel-cell size. A
secondary themed icon (a stylized sun, a phoenix feather, a
thematic emblem) sits below the label.

[MOBILE CONSTRAINTS]
Players need to spot this on a busy reel grid in under a second.
Clear silhouette at thumbnail size. Distinct from any HP, MP, LP,
or other WYS variant in the set — the burst rays are the giveaway.
Flat solid black background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, only one symbol in the frame.
```

---

## Prompt — WYS as WYSIWYG collector (Dodge / Billionaire pattern)

When `mechanic` = `wysiwyg collector`, the symbol pays a runtime
value during a bonus mode when collected. It looks like a coin but
with a clearer "vessel" feel.

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
WY family coin grammar, but slightly more recessed face — this coin
is a vessel, not a transmitter.

[COIN SHAPE — circular collector vessel]
Same coin construction as the WY family. The disc face is slightly
recessed and shows a dollar-sigil or currency mark composed into the
themed engraving. Runtime overlays the numeric value into the clean
numeral space.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (WY family — WYSIWYG collector).
- Primary palette: themed family hue (gold default; brief may
  override to purple, green, or other per game).
- Role overlay: dollar-sigil or currency-mark glyph composed behind
  the numeral space.

[SUBJECT INSIDE — collector emblem]
A subtle "value-bearing" emblem behind the numeral space —
suggesting the coin carries a worth.

[MOBILE CONSTRAINTS]
Clear silhouette. Reads as a coin first, with the currency cue
secondary. Flat solid black background.

high quality game asset, sharp clean edges, professional slot game
art, only one symbol in the frame.
```

---

## Other role overlays (briefer prompt skeletons)

For roles less common than the above, build the prompt from:

```
[Universal WYS base from this template]
+
[Role overlay cues from the brief-driven roles table]
+
[Per-game palette / engraving direction]
```

Specifically:

- **Adder** (Billionaire `WY8` / `WY9` pattern) — replace the dollar
  sigil with a composed `+` glyph integrated into the numeral space.
  Add subtle outward radial arrows.
- **HP-equivalent direct payout** (Billionaire `WY1` / `WY2` for
  Purple / Green direct payouts) — drop the numeral space; treat
  this more like a premium themed HP symbol on a coin/medallion
  body. Same warmth band as HP1.
- **Loot Link trigger** — portal-style swirl behind the disc face.
  Suggests a doorway / activation. Often paired with directional
  energy on the rim.

---

## Pre-gen quick checks

- [ ] `style_anchor` (from `project.json.style_anchor.text`) is prepended verbatim
- [ ] `[RENDER STYLE — LOCKED]` block present with explicit "Inherit ONLY X, ignore Y" clause
- [ ] Shape is "circular coin / medallion / portal" stated explicitly
- [ ] Currency / numeral space is reserved (no static number in the art unless brief specifies)
- [ ] Color matches the variant convention OR the brief override (check `subject`)
- [ ] Role overlay cues from the brief's `mechanic` field are present in the prompt body
- [ ] Each variant prompt explicitly states it's distinct from sibling variants
- [ ] Background is `flat solid black background, no gradients`
- [ ] Theme engraving is described (otherwise NB2 makes generic coins)

## Post-gen quick checks

- [ ] Reads as a coin / portal / sphere (circular metallic rim, not a flat or rectangular shape)
- [ ] Center has clean space for the runtime overlay (unless brief specified a static label)
- [ ] Hue family is unmistakable (gold ≠ red ≠ green ≠ blue ≠ purple at a glance)
- [ ] Role overlay cues are visible at thumbnail size — not micro-decoration that vanishes
- [ ] Silhouette readable at 64 px (black-fill test per `shared/art_principles.md` §10 "Per-symbol")
- [ ] When multiple variants exist, side-by-side they look like a coordinated coin family — same coin grammar, different colors / mechanics
- [ ] For the scatter role: burst rays clearly visible, palette warmer than the standard `WY1` coin, distinct from any HP symbol

## Generating multiple WYS variants

Generate the **default-color variant** first (`WY1` gold) as the
family anchor, then use it as a reference image for `WY2`, `WY3`,
`WY4`, `WYS1`, `WYS2`, etc. Pass `WY1`'s file as `references` in
subsequent generations and state explicitly:

> "Same coin grammar as the WY1 gold coin already generated — same
> rim treatment, same engraving complexity, same overall composition.
> Differs only in [hue family] and [role overlay]: [the role-specific
> cues from the brief]."

After all variants are generated, lay them out side by side and
confirm they read as a coordinated family at thumbnail size.

## Currency overlay (runtime)

The actual currency amount (e.g. "$10", "×100") is added at runtime
by the game engine, NOT painted into the art. The art always renders
with a CLEAN center space — usually a recessed area where the
engine drops the dynamic text.

**Exception:** if the brief explicitly calls for a static label
(e.g. `"TRIGGER"` or `"BONUS"` written on the coin face), include it.
Otherwise, leave the center clean.

## Compound prefixes that route here

`BWY`, `BWY1`+ → WYS family + bonus-trigger overlay. Use this
template's universal WYS base, then add the bonus-trigger overlay
cues from `BONUS_TRIGGER_TEMPLATE.md` (themed badge motif, warm
radial burst, optional `BONUS` label).

`SFWY`, `SFWY1`+ → SF family dominant, with WYS visual notes. Route
to `MYSTERY_TEMPLATE.md` (the SF Family Template) and pull
coin-grammar notes from this template for the visual base.

`WDWY`, `WDWY1`+ → Wild family dominant (scatter-wild hybrid),
with WYS visual notes. Route to `WILD_VARIANTS_TEMPLATE.md`
(scatter-wild section).

`WYS`, `WYS1`+ → alias for the WYS family. Use this template as-is
with the brief's `mechanic` selecting the role overlay.
