# SF Family Template (`SF` prefix — also `SFWY` compounds)

The SF family is H5G's "Special Feature symbol" — a generic
feature-family bucket used across the production library for at
least **14 distinct mechanics**: mystery transform, hotspot
multiplier, hotspot adder, hotspot combiner, hotspot collapse,
persistent hotspot, upgradable collector, immediate-payout collector,
bonus value collector, transforming collector, path-forming prize,
lock-and-respin trigger, jackpot coin (SF role), bonus-game trigger
(SF role). The full mapping lives in the role-overlay table below.

**Family rule: visual identity is stable, role comes from the brief.**
Every SF member renders as a feature-token in the WYS-adjacent
visual family — coin / portal / spherical token, often with a
"closed object" motif (chest / orb / crystal ball) for mystery sub-
roles. Read `brief.symbol_manifest[].mechanic` for the specific role
this `SF<N>` plays in the game, then layer the role overlay cues
from the table below.

> Filename note: this file is `MYSTERY_TEMPLATE.md` for backward
> compatibility — the original SF role was mystery transforms. It
> now covers the full SF family.

These templates use the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`.

## Universal rules (every SF member)

- **Shape:** circular feature-token, sphere, portal, or "closed
  object" (treasure chest, gift box, orb, crystal ball, sealed
  envelope) — adjacent visual family to WYS, with slightly more
  "energetic" surface treatment.
- **Background:** flat solid black, no gradients.
- **Surface energy:** pulse glow, particle motes drifting nearby,
  or a closed-object texture (for mystery sub-roles).
- **Color:** warm luminous palette tied to `palette_leads.primary`;
  SF symbols are usually distinguished from WYS by **shape
  silhouette** rather than hue — a sphere with energy reads
  differently than a coin with engraving even at the same color.
- **Sizing phrase:** "prominent, fills the cell, more visually
  weighted than MP/LP" — SF is special, not background.

## Brief-driven role overlays

Every SF symbol uses the universal rules above as its base. The
brief's `mechanic` field selects one of these role rows; apply the
named overlay cues on top of the base feature-token silhouette.

| `mechanic` value | Overlay cues to add to the base feature-token |
|---|---|
| `mystery transform` (original/default) | Closed-object treatment — treasure chest with glowing crack, gift box with ribbon, crystal ball with shrouded interior, sealed envelope with wax seal, veiled portrait, question-mark medallion. Closed and unrevealed; the runtime animates the reveal. |
| `hotspot multiplier` | Spherical portal token with a clean `×N` numeric overlay slot. Radial pulse rings emanating outward (it multiplies surrounding cells). Slot reserves space for the numeric value — runtime fills it. |
| `hotspot adder` | Sphere with a composed `+` sigil inside. Outward radial arrows (it spreads its value). |
| `hotspot combiner` | Sphere with converging arrows pointing inward — it sums what's around it. Optional sum-sigil (Σ-style mark) at the center. |
| `hotspot collapse` | Sphere with imploding particle ring — it resolves a collapse/clear event. Energy contracts inward. |
| `persistent hotspot` | Sphere with a pin/lock anchor motif at the bottom — it stays fixed across multiple bonus spins. |
| `upgradable collector` | Coin/portal-style disc with tier-marker chevrons stacked above it (the upgrade tiers). Bankrush Gamma SF1 "gold bar collector that upgrades through Loot Link" pattern. |
| `immediate-payout collector` | Coin/portal-style disc with a dollar-sigil and a cash-burst halo. Pays instantly on land — the burst is what communicates that energy. |
| `bonus value collector` | Coin/portal-style disc with a meter / gauge motif on the rim showing accumulation. Gathers WY values during bonus and pays at end. |
| `transforming collector` | Coin/portal-style disc with morph / particle dissolve motif. It will transform into a WY symbol mid-bonus. |
| `path-forming prize` | Sphere or disc with a directional path / bridge motif — short luminous lines extending in 2-4 directions. It connects to adjacent special symbols. |
| `lock-and-respin trigger` | Sphere with a chain / lock anchor + refresh / arrow-loop ring. It locks others and grants respins. |
| `jackpot coin` (SF role) | Metallic medallion finish + crown / star sigil at the center. Same visual band as a JP-family medallion. The Tesla SF1 "jackpot coin" pattern. |
| `bonus-game trigger` (SF role) | Warm radial burst + themed badge surface. Optional `BONUS` or `FREE SPINS` label arcing through the disc. Tesla SF2, Honda SF1, Billionaire's Gamma SF1 pattern. |

When in doubt, **the brief's `subject` text wins**. A brief that
says `"crystal ball with shrouded interior"` and `mechanic: "mystery
transform"` gets the closed-object treatment with the mystery role
overlay; a brief that says `"sphere of energy"` and `mechanic: "hotspot
multiplier"` gets the sphere treatment with the multiplier overlay.

---

## Prompt — SF as mystery transform (the original / most common role)

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference for rendering technique, surface finish, and
lighting direction. Inherit ONLY the rendering technique from the
reference; ignore its background color and palette, specified below.

[CLOSED-OBJECT SHAPE — <mystery.subject>]
<mystery.subject> as a mystery symbol slot icon, closed and
unrevealed state. The secret is hidden inside; the player can't
yet see what's there. A glowing crack, shimmering surface, or
luminous seam hints that something is inside — without revealing it.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (SF family — mystery role).
- Primary palette: <palette_leads.primary> with a mysterious accent
  glow (cool-shifted for fantasy; warm for treasure).
- Halo: subtle luminous edge — enough to suggest "something inside"
  without giving it away.

[SUBJECT INSIDE — closed state]
The closed/unrevealed state ONLY. Do NOT paint a revealed pay
symbol inside the closed object — that's the runtime animation.
Single subject, fills the cell prominently with a small border.

[MOBILE CONSTRAINTS]
Clear silhouette at thumbnail size. Reads as "something secret is
here". Centered, flat solid black background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, only one symbol in the frame.
```

Substitute `<mystery.subject>` from the brief. Common choices:

| Subject | When to use |
|---|---|
| Closed treasure chest with glowing crack | fantasy / adventure / pirate |
| Gift box with ribbon | holiday / casual / candy themes |
| Crystal ball with shrouded interior | mystical / fortune-telling |
| Sealed envelope with wax seal | classic / Victorian / mystery |
| Question-mark medallion | retro / classic Vegas / fruit machines |
| Veiled portrait | gothic / horror / Victorian |
| Wrapped scroll with shimmer | Egyptian / ancient / library |
| Glowing orb with hidden silhouette | sci-fi / fantasy |

---

## Prompt — SF as hotspot multiplier (Loot Link / Bankrush pattern)

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference for rendering technique. Inherit ONLY the
rendering technique; palette and hotspot overlay below override.

[SPHERICAL PORTAL TOKEN — hotspot multiplier]
A spherical portal token, fills the cell prominently with a small
border. Layered construction: outer luminous edge · recessed sphere
surface · clean centered numeric slot reserved for the `×N`
multiplier value (runtime fills it — DO NOT paint a static number
in unless the brief calls for one).

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (SF family — hotspot multiplier role).
- Primary palette: warm luminous tied to <palette_leads.primary>,
  with electric-blue or electric-cyan accent on the radial pulse.
- Role overlay: radial pulse rings emanating outward from the
  sphere — visible at thumbnail size, suggests "this multiplies
  surrounding cells".

[SUBJECT INSIDE — numeric slot]
Clean centered numeric slot for the runtime `×N` value. Behind/around
the slot, subtle themed motif (a stylized lightning bolt, an arcane
sigil — appropriate to the brief's theme).

[MOBILE CONSTRAINTS]
Distinct from WYS coins by silhouette — this is a sphere with
outward radial pulse, not a coin with engraving. Flat solid black
background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, only one symbol in the frame.
```

---

## Prompt — SF as path-forming prize (Blazing Stampede pattern)

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Same SF visual family as siblings. Differs in role overlay.

[SPHERICAL TOKEN — path-forming prize]
A spherical feature token, fills the cell prominently. Short
luminous path-lines extend outward in 2-4 directions — these are
the "bridges" the symbol forms to adjacent specials. The lines are
short and clearly part of the token, not full lines across the
cell.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (SF family — path-forming prize role).
- Primary palette: warm luminous, tied to <palette_leads.primary>.
- Role overlay: directional path/bridge motif (short luminous lines).

[SUBJECT INSIDE — connection emblem]
A connection emblem at the center of the sphere — a node, a star,
a thematic sigil that reads as "this connects".

[MOBILE CONSTRAINTS]
Distinct from other SF roles by the visible path-lines. Flat solid
black background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, only one symbol in the frame.
```

---

## Other role overlays (briefer prompt skeletons)

For roles less common than the above, build the prompt from:

```
[Universal SF base from this template]
+
[Role overlay cues from the brief-driven roles table above]
+
[Per-game palette / theme direction from the brief]
```

Specifically:

- **Hotspot adder / combiner** — same spherical base; swap the
  `×N` numeric slot for the `+` glyph (adder) or converging-arrows
  motif (combiner).
- **Hotspot collapse** — imploding particle ring contracting toward
  the center.
- **Persistent hotspot** — add a pin / lock anchor motif at the
  bottom of the sphere.
- **Upgradable collector / immediate-payout collector / bonus value
  collector / transforming collector** — these are WYS-adjacent
  roles. The SF visual base is fine, but consider whether the
  brief's `subject` describes a coin (`"gold bar collector"`)
  versus a feature-token. If it's coin-shaped, route to
  `COIN_TEMPLATE.md` (WYS family) and apply the collector role
  overlay there instead.
- **Lock-and-respin trigger** — chain/lock anchor at the bottom +
  refresh / arrow-loop ring.
- **Jackpot coin** (when SF plays the jackpot-coin role) — consider
  routing to `JACKPOT_TEMPLATE.md` instead if the brief positions
  this symbol as part of the jackpot family.
- **Bonus-game trigger** (when SF plays the bonus-trigger role) —
  consider routing to `BONUS_TRIGGER_TEMPLATE.md` instead if the
  symbol is functionally a bonus trigger that just happens to use
  the SF prefix.

The decision rule: **if the visual identity is closer to a different
family's silhouette, route there**. The SF family template covers
the SF visual base; when a brief describes an SF symbol that's
really a coin or a metallic jackpot medallion, route by visual
identity.

---

## Pre-gen quick checks

- [ ] `style_anchor` (from `project.json.style_anchor.text`) is prepended verbatim
- [ ] `[RENDER STYLE — LOCKED]` block present with explicit "Inherit ONLY X, ignore Y" clause
- [ ] Shape is "spherical token" or the brief's specific closed-object subject
- [ ] Role overlay cues from the brief's `mechanic` field are present in the prompt body
- [ ] For mystery role: symbol is the CLOSED / unrevealed state (no revealed pay symbol inside)
- [ ] For multiplier role: numeric slot reserved (no static number painted unless brief specifies)
- [ ] Background is `flat solid black background, no gradients`
- [ ] Single subject — not multiple objects competing

## Post-gen quick checks

- [ ] Silhouette readable at 64 px (black-fill test per `shared/art_principles.md` §10 "Per-symbol")
- [ ] Role overlay cues visible at thumbnail size — not micro-decoration
- [ ] Distinguishable from WYS coins (SF reads as a sphere / closed object with energy; WYS reads as a coin with engraving)
- [ ] Distinguishable from BONUS / WILD / SCATTER symbols in the same set
- [ ] For mystery: looks closed / sealed — does NOT show a revealed symbol
- [ ] Theme-appropriate (a treasure chest in a sci-fi game is wrong; an energy sphere in a pirate game is wrong)

## Anti-patterns

- ❌ Showing the revealed symbol inside the closed-state SF (that's the runtime animation, not the art)
- ❌ Using a generic `?` symbol when the theme calls for an object
- ❌ Painting the runtime `×N` multiplier value into the art for hotspot roles (leave the slot clean)
- ❌ Making the SF look identical to a WYS coin — SF and WYS share a family neighborhood but should be visibly distinct (SF: sphere + energy; WYS: coin + engraving)
- ❌ Drawing actual transformation in progress (use the closed state)

## Multiple SF symbols in one game

When a game ships `SF1`, `SF2`, `SF3` (different mechanics — common in
Loot Link / Hotspot games like Bankrush Beta with SF2-SF6 hotspots
plus SF7-SF11 Loot Link triggers), each variant must be visibly
distinct from its siblings.

- Generate `SF1` first as the family anchor.
- Pass it as a reference image when generating `SF2`, `SF3`, etc.
- State explicitly in each subsequent prompt:

> "Same SF visual family as the SF1 already generated — same base
> sphere/token construction, same energy treatment. Differs in role
> overlay: [the role-specific cues from the brief's `mechanic` field]."

After generating multiple SF variants, lay them out side by side and
confirm they read as a coordinated family — same SF grammar,
different role cues.

## Compound prefixes that route here

`SFWY`, `SFWY1`+ → SF family dominant, with WYS visual notes. Use
this template's universal SF base, then pull coin-grammar notes from
`COIN_TEMPLATE.md` (the WYS Family Template) for the secondary
visual layer.

`WDSF`, `WDSF1`+ → Wild family dominant, with SF visual notes. Route
to `WILD_VARIANTS_TEMPLATE.md` and pull SF-family visual notes from
this template for the secondary layer.
