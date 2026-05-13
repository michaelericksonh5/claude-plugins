# Bonus Wheel Template

Many H5G games include a **bonus wheel** as a feature surface — a
circular spinning wheel with slices arranged around it that the
player triggers from the base game. The wheel awards jackpot tiers,
multipliers, bonus picks, or free-spin counts depending on the
brief's mechanic.

**Single-graphic rendering.** Wheels are generated as **one full
graphic** containing the entire wheel with all slices laid out
around it — NOT as individual slice files. The runtime spins the
wheel and the rendered graphic handles the visual presentation of
all tier slices, the central hub, the indicator, and the frame.

This template covers four common wheel mechanics:

- **Jackpot wheel** — tier slices for Mini / Minor / Major / Grand
  (and 6-tier variants). Tesla's pattern: JP1–JP4 are wheel slices,
  not reel symbols.
- **Bonus wheel** — slices award different bonus modes (free spins,
  pick-em, hold-and-spin, etc.).
- **Multiplier wheel** — slices show different `×N` values; the
  landed slice multiplies the win.
- **Pick-em wheel** — slices reveal prize values when the player
  taps; functionally a pick-em game arranged radially.

The wheel template lives in `/slot-step-06` (UI surfaces) because the
wheel is **bonus-feature chrome**, not a reel symbol. Output lands in
the `Wheels/` category folder, not `Symbol_Art/`.

## Surface rules

- **Folder:** `Wheels/` (every wheel graphic lives in this single folder)
- **Filename:** `Wheel_<variant>_NNN.png` — variants are `jackpot`,
  `bonus`, `multiplier`, `pickem` (extend as needed)
- **Slot in `project.json`:** `assets.ui.wheels.<variant>` (where
  `<variant>` is `jackpot` / `bonus` / `multiplier` / `pickem`)
- **Aspect ratio:** typically `1:1` (the wheel is presented centered
  in the bonus screen). Some games use `4:5` portrait if the wheel
  is cropped at the left edge per the Source-of-Truths doc's
  "Bonus Wheel Design Standards"
- **Background:** **flat solid black, no gradients** — the wheel
  composites over the bonus-mode background at runtime. A textured
  background here would conflict.
- **Output is a complete wheel graphic:** outer frame · all tier
  slices laid out radially · central hub · pointer / indicator ·
  any decorative ring elements. Do NOT generate individual slices.

## Universal design rules (from the H5G Source-of-Truths)

Per Part 6 of the master design doc ("Bonus Wheel Design Standards"),
every wheel must follow these conventions regardless of variant:

- **Visual hierarchy on the slices.** Apply the pay-value color
  spectrum to slice colors:
  - Low values → cool tones (slate blue, steel blue, teal)
  - Mid values → transitional tones (sage green, amber, warm olive)
  - High values → warm tones (ember orange, dragon red, molten
    crimson)
  - Jackpot / max value → the most visually dominant slice;
    celestial gold or solar flare yellow; stands out instantly
    even in peripheral vision
- **Values readable.** Numeric values (`×10`, `MAJOR`, etc.) sit
  ON TOP of slice colors, not embedded within them. Typography is
  thick, clean, large enough to read at thumbnail size during the
  spin animation.
- **Center hub is simplified.** A focal element at the center is
  fine (eye, gem, theme emblem) but must NOT compete with the slice
  values for attention. If the center detail is pulling the eye
  away from the numbers, reduce it.
- **Frame ≠ feature.** Themed decoration on the wheel frame is OK
  and encouraged for immersion, but the decoration cannot compete
  with the slice values. Frame is a stage, slices are the actor.
- **Pointer / indicator.** A clear pointer (typically horizontal,
  pointing left, with the winning slice landing at the 3 o'clock
  position) on the outer edge of the wheel. The pointer ensures
  the win-result lands in the most-visible / most-readable area
  of the screen.

## Per-variant guidance

### Jackpot wheel

The wheel that awards the game's jackpot tiers. Tesla's pattern:
JP1–JP4 are wheel slices laid out around a four-slice wheel; landing
on one awards that tier's jackpot.

- Read `brief.jackpot_tier_names` to determine which slice gets
  which label (the per-game numeric ordering varies — see
  `shared/symbol_vocabulary.md` "Jackpot numeric ordering").
- Slice count typically matches the jackpot tier count (4 tiers →
  4 slices, 6 tiers → 6 slices). When the brief specifies a
  different layout (some games have duplicate slices to bias toward
  smaller tiers), generate to spec.
- Each slice carries its tier label (e.g. `MINI`, `MINOR`, `MAJOR`,
  `GRAND`) in thick readable type, with the slice color matching
  the tier's metallic finish band (bronze / silver / gold /
  platinum).
- Grand slice is the visually dominant one — celestial gold or
  bright warm gold, slightly larger numeric weight, optional star
  burst behind the label.

### Bonus wheel

Slices award different bonus modes (free spins, pick-em, hold-and-
spin, etc.) rather than monetary values.

- Each slice carries a short label describing the bonus it awards
  (`FREE SPINS`, `PICK-EM`, `HOLD & SPIN`, `MULTIPLIER`, etc.).
- Color hierarchy still applies: the most premium bonus (typically
  `JACKPOT` or `MULTI BONUS`) is the warmest / most dominant slice.
- If the brief gives a "lose slice" or "no win slice", that slice
  is the coolest / most desaturated — visibly less appealing than
  the win slices.

### Multiplier wheel

Slices show different `×N` values; the landed slice multiplies the
trigger win.

- Numeric values are the primary readable content. Type weight
  larger than on jackpot wheels — these are pure numbers.
- Color hierarchy maps to magnitude: `×2` cool, `×5` mid-warm,
  `×10` warm, `×50`+ hot, `×100`+ celestial gold.
- Center hub can carry a static `×` glyph or a "WIN MULTIPLIER"
  legend.

### Pick-em wheel

Slices reveal prizes when the player taps. Functionally a pick-em
game arranged radially around the wheel.

- Slices may be visually identical until revealed (the runtime
  handles the reveal animation). The base wheel art renders all
  slices in their **closed/unrevealed state** — a uniform design
  with a small indicator that the slice is interactive.
- A pointer is still present but plays a smaller role (the player
  picks via tap, not via spin).
- Optional: some pick-em wheels show prize previews on slices in a
  reduced/dimmed state — confirm with the brief.

## Prompt — Jackpot wheel (4-tier example)

```
[RENDER STYLE — LOCKED to attached key art reference]
Match the reference for rendering technique, surface finish, and
lighting direction. Inherit ONLY the rendering technique from the
reference; ignore its background color and palette, specified below.

[WHEEL COMPOSITION — full bonus wheel graphic, all slices visible]
A complete bonus wheel graphic for a slot game jackpot bonus, all
four tier slices laid out around the wheel as a single circular
composition. Outer themed frame with <theme_summary> decorative
motifs (subtle, recessive — does not compete with the slice values).
Central hub at the wheel center with a small thematic emblem (a
crown, a gem, a phoenix wing — drawn from the game's vocabulary)
that does NOT compete with the slice labels for attention. Clear
horizontal pointer or indicator on the outer right edge of the wheel
(3 o'clock position), pointing toward the wheel — the winning slice
will land at this position.

[FOUR JACKPOT TIER SLICES — laid out around the wheel]
Four equal pie slices arranged radially around the wheel:
- GRAND slice: celestial gold / bright warm gold base color, the
  visually dominant slice with optional star burst or radiant
  pattern behind the label. Label "<GRAND_LABEL>" in thick readable
  caps.
- MAJOR slice: rich warm gold base color. Label "<MAJOR_LABEL>" in
  thick readable caps.
- MINOR slice: silver / pewter base color. Label "<MINOR_LABEL>" in
  thick readable caps.
- MINI slice: bronze / copper base color. Label "<MINI_LABEL>" in
  thick readable caps.
All four labels sit ON TOP of the slice colors with clean readable
typography — large enough to read at thumbnail size during spin
animation. Thin metallic divider lines separate adjacent slices.

[COLOR SYSTEM FOR THE WHEEL]
- Slice palette follows the H5G pay-value color spectrum: Grand =
  celestial gold (warmest, most dominant), Major = warm gold, Minor
  = silver, Mini = bronze.
- Frame decoration: <palette_leads.primary> theme accents on the
  outer frame, but subtle / recessive — the slices and their labels
  dominate the visual.
- Background: flat solid black, no gradients (the wheel composites
  over the bonus-mode background at runtime).

[MOBILE CONSTRAINTS]
The wheel must be readable as a complete unit at the bonus-screen
size on a phone. Slice labels must be readable during the spin
animation — thick clean type, no fine decorative typography. Bold
clean shapes, high contrast between slice colors and labels.
Centered composition, the full wheel visible within the canvas with
generous margin. Flat solid black canvas background, no gradients,
no patterns.

high quality game asset, sharp clean edges, professional slot game
art, bonus wheel composition, all slices visible, mobile-optimized.
```

Substitute `<GRAND_LABEL>`, `<MAJOR_LABEL>`, etc. from
`brief.jackpot_tier_names`. Substitute `<theme_summary>` and
`<palette_leads.primary>` from the brief.

## Prompt — Multiplier wheel (variable slice count)

```
[RENDER STYLE — LOCKED to attached key art reference]
Same render-style discipline as the jackpot wheel.

[WHEEL COMPOSITION — full multiplier wheel graphic, all slices visible]
A complete bonus wheel graphic for a slot game multiplier bonus,
<N> slices laid out around the wheel as a single circular
composition. Outer themed frame, central hub with a "×" glyph or
"WIN MULTIPLIER" legend, clear horizontal pointer on the outer
right edge (3 o'clock position).

[<N> MULTIPLIER SLICES — laid out around the wheel]
<N> equal pie slices arranged radially. Each slice carries a
multiplier value in thick readable type:
- ×2 slice: cool slate blue base color
- ×3 slice: cool teal base color
- ×5 slice: sage green base color
- ×10 slice: warm amber base color
- ×25 slice: ember orange base color
- ×50 slice: dragon red base color
- ×100 slice: celestial gold base color (the visually dominant
  slice, optional radiant star burst behind the label)
Numeric values sit ON TOP of slice colors with clean readable
typography. The "×" prefix is part of the label, e.g. "×10".

[COLOR SYSTEM FOR THE WHEEL]
- Slice palette follows the H5G pay-value color spectrum mapped to
  multiplier magnitude (low = cool, high = warm).
- Frame decoration matches the jackpot wheel's discipline if both
  wheels appear in the same game — same themed motifs, same
  recessive treatment.
- Background: flat solid black, no gradients.

[MOBILE CONSTRAINTS]
Same as jackpot wheel: thick readable typography, slice labels
readable at thumbnail size, the wheel reads as a complete unit.

high quality game asset, sharp clean edges, professional slot game
art, multiplier wheel composition, all slices visible.
```

Substitute the slice count and value mapping from the brief.

## Prompt — Bonus wheel / Pick-em wheel skeletons

Follow the [Jackpot wheel](#prompt--jackpot-wheel-4-tier-example)
structure, swapping the four `[FOUR JACKPOT TIER SLICES]` for the
brief's bonus modes (FREE SPINS / PICK-EM / HOLD & SPIN / MULTI
BONUS / NO WIN — whatever the brief specifies). Apply the same
color-hierarchy rule: most premium bonus = warmest dominant slice;
least premium / lose slice = coolest / desaturated.

For pick-em wheels, slices are either:

- **Uniform unrevealed state** — all slices identical with a small
  interactive indicator (a "?" or a sealed cover), runtime reveals
  prizes on tap.
- **Dimmed preview** — slices show their prize values in a
  reduced / dimmed state, becoming bright on selection. Confirm
  with the brief which variant the GDD specifies.

## Pre-gen quick checks

- [ ] `style_anchor` (from `project.json.style_anchor.text`) is prepended verbatim
- [ ] Wheel variant matches the brief's mechanic (`jackpot` / `bonus` / `multiplier` / `pickem`)
- [ ] For jackpot wheels: `brief.jackpot_tier_names` mapping has been read — slice labels match
- [ ] Slice count specified explicitly (4 for standard jackpot, variable for bonus / multiplier)
- [ ] Each slice's label and color tier specified in the prompt body
- [ ] Pointer / indicator described (horizontal, right edge, 3 o'clock position)
- [ ] Color hierarchy stated (warm dominant for high-value, cool for low-value)
- [ ] Background is `flat solid black, no gradients`
- [ ] Frame decoration described as "subtle / recessive" — never competes with labels
- [ ] Center hub described as "simplified" — never competes with slice values

## Post-gen quick checks

- [ ] Reads as a single coherent wheel graphic (all slices visible, one composition)
- [ ] Slice labels are readable at thumbnail / bonus-screen size
- [ ] Color hierarchy is visible — the premium slice (Grand / max multiplier / most-coveted bonus) stands out instantly even in peripheral vision
- [ ] Frame decoration does NOT pull the eye away from slice labels
- [ ] Center hub does NOT compete with slice values
- [ ] Pointer / indicator clearly visible on the right edge
- [ ] No baked-in win indicator on a specific slice (runtime selects the winning slice; the art is neutral)
- [ ] For pick-em wheels: slices either uniformly closed OR consistently dimmed-preview, never mixed

## Anti-patterns

- ❌ Generating individual slice files — wheels are single-graphic surfaces
- ❌ Assuming `JP1 = Grand` (or `JP1 = Mini`) without reading `brief.jackpot_tier_names`
- ❌ Painting a runtime-determined win indicator into the art (e.g. a glowing slice that looks "already won")
- ❌ Frame decoration that overwhelms the slice labels — frame is the stage, slices are the actor
- ❌ Center hub with detailed art that competes with slice readability
- ❌ Cool-coded warm tiers or warm-coded cool tiers (breaks the H5G pay-value color spectrum)
- ❌ Fine decorative typography for slice labels — must be thick / clean / readable during fast spin animation
- ❌ Putting the wheel on a textured or gradient background — the runtime composites the wheel over the bonus background, so the art should sit on flat black
