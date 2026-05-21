# Loot Link / Hotspot Template

Loot Link / Hotspot / Hold-and-Spin side mechanics are a **family** of
modern slot bonus games where a separate small grid appears alongside or
replacing the main reels. This grid has its own dedicated symbol
vocabulary that doesn't appear in the base game.

Found in: Charm Blitz, Green Machine Blitz, Billionaire's Bank Jackpot,
BetMGM Loot Link family, Super Stack Fortunes, and many more H5G games.

If a brief lists any of these symbol prefixes, generate using the
patterns below: `COL`, `ACT`, `HOT_x2`+, `HOT_ADD`, `HOT_COMB`,
`HOT_COLLAPSE`, `HOT_PERSIST`, `BAG`, `MOJ`.

This template uses the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`. The `<style_lock>` / `<reference>`
placeholders below are substituted with the same text at
prompt-assembly time.

### Real-world GDDs often use SF / WY / BWY for Loot Link symbols

The prefix vocabulary above (`COL`, `ACT`, `HOT_*`, etc.) is the
plugin's **canonical** Loot Link taxonomy. Actual GDDs across the
H5G library don't always follow it. The Symbol Catalog of 26 shipped
games shows Loot Link mechanics labeled with generic prefixes:

| Game | Loot Link role | Prefix the GDD actually uses |
|---|---|---|
| Bankrush Beta | Loot Link trigger | `SF7`–`SF11`, `WY1` |
| Bankrush Beta | Hotspot modifier (5 types) | `SF2`–`SF6` |
| Bankrush Beta | Upgradable gold-bar collector | `SF1` |
| Bankrush Gamma | Hotspot modifier (5 types) | `SF2`–`SF6` |
| Bankrush Gamma | Upgradable collector | `SF1` |
| Billionaire's Beta | Immediate-payout collector | `SF1` |
| Billionaire's Beta | Bonus value collector | `SF2` |
| Billionaire's Gamma | Loot Link bonus trigger | `SF1` |
| Chevy family | Loot Link activator | `SF1` |
| Da Vinci Deluxe Ways 2 | Loot Link trigger | `WYSIWYG` |
| Majestic Cats | Loot Link feature start | `WYSIWYG` |
| Tesla | Jackpot Coin (in Loot Link context) | `SF1` |

**Route by the brief's `mechanic` field, not the literal prefix.** A
symbol with `id: "SF1"` and `mechanic: "hotspot multiplier"` is a
Loot Link hotspot multiplier — generate using this template's
`HOT_x<N>` section even though the filename will be `SF1_001.png`
not `HOT_x2_001.png`. The filename always matches the brief's `id`
field; the prompt is selected by the `mechanic` field.

This forward-compat principle is documented in
`shared/symbol_vocabulary.md` → "Routing by manifest role, not
literal prefix".

## Contents — jump to the symbol you're generating

- **Universal rules** — apply to every Loot Link symbol
- **Collector (`COL`)** — vessel-with-vacuum aesthetic (chest, magnet, funnel)
- **Activator (`ACT`)** — trigger / activator symbols (e.g. "PLAY" / "GO")
- **Hotspot operators** — multipliers and accumulators that modify nearby cells
  - **`HOT_x2` / `HOT_x3` / `HOT_x4` / `HOT_x5` / `HOT_x10`** — flat multipliers
  - **`HOT_ADD`** — adds a fixed value to landed coins
  - **`HOT_COMB`** — combines adjacent values
  - **`HOT_COLLAPSE`** — collapses to a single high-value cell
  - **`HOT_PERSIST`** — persists across spins
- **Bag scatters (`BAG`)** — premium scatter-tier rewards
- **Money emoji (`MOJ`)** — face-character coin variant

Each section has its own pre-gen prompt + post-gen checks. Read only the
section for the symbol you're generating.

## Universal rules (all Loot Link symbols)

- **Background:** flat solid black, no gradients
- **Sizing:** "fills the cell prominently with thick rim"
- **Family resemblance:** all Loot Link symbols in one game must read as
  members of the same set — same rim treatment, same overall composition,
  different functional cues
- **Visual differentiation between operators:** must be **strong** so
  players can read each symbol's mechanic at a glance during fast spins
- **Currency space:** if the symbol carries a numeric value (most do),
  reserve clean center space for runtime overlay

---

## Collector (`COL`)

Pulls value into a meter, or sweeps adjacent scatters into a collected
total. Visual: a **vessel-with-vacuum** aesthetic — chest, magnet, suction
funnel — clearly **gathering**.

```
A circular Loot Link collector slot symbol,
clearly a gathering vessel — magnet, suction funnel, or open treasure chest
with energy lines being pulled inward,
fills the cell prominently with thick metallic rim,
clean center reserved for currency value (no number painted in),
<theme_summary> themed,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Quick checks:
- [ ] Vessel reads as actively gathering (energy lines pulled IN, not pushed out)
- [ ] Distinct from a static container (it's a collector, not a chest sitting still)
- [ ] Currency space is reserved

---

## Activator (`ACT`)

Triggers another mechanic when present — spawns wilds, duplicates symbols,
expands into adjacent cells. Visual: a **starburst / lightning bolt /
trigger** aesthetic — clearly **emitting energy**.

```
A circular Loot Link activator slot symbol,
clearly emitting energy outward — starburst rays, lightning bolts, or
particle bursts radiating from a central core,
fills the cell prominently with thick metallic rim,
opposite of the collector — pushes energy OUT instead of pulling IN,
<theme_summary> themed core element,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Quick checks:
- [ ] Energy reads as outward-radiating (opposite of collector)
- [ ] Visually distinct from `COL` — players must instantly tell which is which
- [ ] Trigger cue is unmistakable

---

## Hotspot multiplier (`HOT_x2`, `HOT_x5`, `HOT_x10`, ...)

Multiplies the value of surrounding cells. The multiplier number is the
**dominant element** — it's the whole point of the symbol.

```
A circular Loot Link hotspot multiplier slot symbol,
"×<value>" as the dominant focal element in metallic gold,
medallion frame surrounding the multiplier number,
arrows or rays pointing OUTWARD to indicate the multiplier
affects surrounding cells,
fills the cell prominently with thick metallic rim,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Substitute `<value>` with 2, 3, 5, 10, etc. Generate one per multiplier
denomination needed.

Tier escalation (when multiple multiplier values exist):
- `HOT_x2`, `HOT_x3`: bronze / copper finish
- `HOT_x5`, `HOT_x10`: silver finish
- `HOT_x15`+: gold finish
- `HOT_x50`+: platinum / diamond finish

---

## Hotspot adder (`HOT_ADD`)

Adds the symbol's carried value to surrounding cells. Visual: a **plus sign
or addition motif** with the added value visible.

```
A circular Loot Link hotspot adder slot symbol,
large plus "+" symbol as the focal element with currency space below,
medallion frame, arrows pointing OUTWARD to surrounding cells,
indicates the symbol ADDS value to neighbors,
fills the cell prominently with thick metallic rim,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Quick checks:
- [ ] Plus sign is unmistakable (different from multiplier ×)
- [ ] Visually distinct from `HOT_x2`+ multipliers
- [ ] Arrows point OUTWARD

---

## Hotspot combiner (`HOT_COMB`)

Combines / sums multiple surrounding values. Visual: **converging arrows**
or a **merge motif**.

```
A circular Loot Link hotspot combiner slot symbol,
multiple converging arrows pointing INWARD to a central merge point,
"COMBINE" or merge symbol at the center,
medallion frame with thick metallic rim,
visually distinct from multipliers and adders — arrows go INWARD here,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Quick checks:
- [ ] Arrows converge INWARD (opposite of adder/multiplier)
- [ ] Combiner cue is unmistakable
- [ ] Distinct from collector (combiner combines values; collector gathers physical scatters)

---

## Hotspot collapse (`HOT_COLLAPSE`)

Triggers a collapse / clear event. Visual: a **downward implosion** or
**vortex motif**.

```
A circular Loot Link hotspot collapse slot symbol,
swirling vortex or downward implosion at the center,
particles or energy lines spiraling INTO a central point of collapse,
medallion frame with thick metallic rim,
distinct from combiner — this feels like a removal event, not a merge,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

---

## Persistent hotspot (`HOT_PERSIST`)

Stays fixed across multiple spins of the bonus. Visual: a **lock / anchor
overlay** on top of any of the above operator types.

```
[Use the appropriate operator base prompt — multiplier, adder, etc.]
[Then add this overlay sentence:]
A small lock or anchor icon in the upper corner of the symbol indicating
this operator persists across bonus spins.
```

Quick check:
- [ ] Lock / anchor overlay is small but unmistakable
- [ ] The base operator type is still readable underneath the persistence cue

---

## Bag scatter (`BAG`) and bonus bag

Money bags or theme-shaped scatter pouches that fill a top row or meter.
Distinct from coins (`WY`) — bags are usually **soft / cloth aesthetic**
with a tied neck.

```
A green money bag slot scatter symbol,
soft cloth bag with tied neck, themed embossing on the body,
clean center reserved for currency value (no number painted in),
fills the cell prominently,
<theme_summary> themed,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

For the **bonus bag** variant (`BAG_BO`) — same but with the word
"BONUS" embossed prominently on the bag and a slightly different
hue (gold or accent color) to mark it as special.

```
[Same as bag template but ADD:]
"BONUS" text embossed prominently on the front of the bag in metallic gold,
the bag has a more golden / premium hue to mark it as the bonus trigger variant.
```

---

## Money emoji trigger (`MOJ`)

A "💰" or theme-emoji-style symbol that triggers scatter collection over
N spins. Visual: emoji-stylized but theme-cohesive.

```
A money emoji slot trigger symbol,
stylized money / cash emoji rendered in the game's theme art style —
not a flat emoji, but a theme-integrated render,
glowing aura indicating it activates a collection feature,
fills the cell prominently,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

---

## Generating a full Loot Link symbol set

When a brief calls for a Loot Link bonus mode with multiple symbol types,
generate them in this order so each can reference the prior:

1. `COL` (collector) — sets the "Loot Link rim" baseline
2. `ACT` (activator) — distinct opposite of collector
3. `HOT_x2` first multiplier — establishes the multiplier rim aesthetic
4. Other multiplier denominations (x5, x10, x25 etc.) — match aesthetic
5. `HOT_ADD`, `HOT_COMB`, `HOT_COLLAPSE` — distinct directional cues from multipliers
6. `BAG`, `BAG_BO` — soft cloth aesthetic family
7. `MOJ` — emoji-style trigger

After all are generated, lay them out side by side and confirm:
- Same rim grammar across all symbols (they look like family)
- Each operator's mechanic reads at a glance (in/out/multiply/combine/collapse)
- Bag family is clearly different from operator family
- Numeric multipliers escalate visually (bronze → silver → gold → platinum)

## Pre-gen quick checks (universal)

- [ ] The symbol's mechanic cue is in the prompt (gathering / radiating / multiplying / converging / etc.)
- [ ] Distinct from sibling Loot Link symbols already generated
- [ ] Currency space reserved when the symbol carries a value
- [ ] Family resemblance to other Loot Link symbols in the same game (same rim treatment)

## Post-gen quick checks (universal)

- [ ] Mechanic is unmistakable visually (collector pulls in, activator pushes out)
- [ ] Distinct hue or treatment vs sibling symbols
- [ ] Readable at thumbnail (Loot Link grids are often 9-slot or 24-slot — symbols appear small)
- [ ] Reads as part of a coordinated symbol family
