# H5G Symbol Vocabulary — Families, Prefixes, and Routing

This is the master reference for every symbol type a slot game might use.
Symbol manifests in `game_brief.json` use these standardized prefixes.
Every skill that handles symbols (`/slot-step-00`, `/slot-step-01`,
`/slot-step-03`, `/slot-step-04`, `/slot-step-08`, `/slot-step-09`)
reads this file when it needs to disambiguate.

> Source: distilled from the team's internal Slot Symbol Taxonomy and
> the **Symbol Catalog** auto-generated from 26 shipped H5G GDDs
> (games 3920 through 4470 — Golden Knight Infinity through Tesla),
> covering 428 distinct symbol entries across 17 categories.

---

## The core idea — family + role

H5G's symbol vocabulary works on **two axes**:

1. **Family** = the visual identity shared across every member of that
   prefix. The WYS family looks like coins / portals / spherical
   feature-tokens. The wild family looks like a category-breaking shape
   in an electric color. The blocker family looks dead/dark/decorative.
   Family is **art-direction**.

2. **Role** = what the specific symbol *does* in the GDD's math
   (collector, scatter, multiplier, free-spins trigger, etc.). Role is
   set by the brief's `mechanic` field, not by the literal prefix.

This split exists because H5G's GDDs **reuse the same prefix for
different mechanics across games**. The catalog of 26 games shows `WY1`
used for 8 different things (hold-and-spin coin, WYSIWYG collector,
scatter, random-wilds shooter, collector+multiplier, adder, HP-equivalent
payout, Loot Link trigger) — but every one of those `WY1` symbols is
visually a coin or portal. **Visual identity is stable; mechanic is
game-specific.**

The art-generation routing follows the family. The mechanic from the
brief drives **overlay cues** added on top of the family's base
template (an SF symbol acting as a "hotspot multiplier" gets a `×N`
numeric overlay; an SF acting as a "path-forming prize" gets directional
arrow motifs; both still render as the SF family's spherical
feature-token base).

---

## Prefix table (canonical)

### Pay tiers

| Prefix | Family | Pay tier | Common variants |
|---|---|---|---|
| `HP1`–`HP4` | High-Pay | Premium | character, iconic object, stacked / oversized, animated |
| `MP1`–`MP3` | Mid-Pay | Mid | themed object, themed animal, themed artifact |
| `LP1`–`LP6` | Low-Pay | Filler | card royals, suits, fruits, gems, themed small objects |

### Wild family

| Prefix | Family | Common variants |
|---|---|---|
| `WD` / `WD1`+ | Wild | sticky, stacked, expanding, walking, respin, transforming, multiplier, duplicating, **scatter-wild hybrid** |

### Scatter family

| Prefix | Family | Notes |
|---|---|---|
| `SC` / `SC1`+ | Scatter | Classic scatter — circular badge with `SCATTER`/`BONUS` label. Legacy term; many newer GDDs use `WY` for the same role. |
| `SW` | Scatter-Wild hybrid | Acts as **both** scatter AND wild (Book-of-Dead style) — see also `WDWY` compound below. |

### WYS family (coin / portal / spherical feature-tokens)

The WYS family is the **largest and most overloaded** family in H5G's
vocabulary. Every member shares the same visual identity — a coin,
portal, sphere, or medallion — but the brief's `mechanic` field
determines what it actually does.

| Prefix | Family | Brief-driven roles |
|---|---|---|
| `WY`, `WY1`–`WY10+` | WYS family | hold-and-spin coin · WYSIWYG collector · scatter · random-wilds shooter · collector+multiplier · adder · HP-equivalent payout · Loot Link trigger |
| `WYS`, `WYS1`–`WYS2+` | WYS family (variant prefix; same family) | same range of roles as `WY` |

Visual identity (every member, regardless of role):
- **Shape:** circular medallion, portal disc, or sphere
- **Currency space:** a clean flat numeral area (runtime overlays the value; never paint the digits into the art)
- **Color differentiation:** when multiple WYS variants appear in one game, use **distinct hue families** — gold/red/green/blue — never subtle shifts
- **Edge halo:** warm luminous halo radiates from the disc; canvas background stays flat black

Common brief-driven roles within the WYS family:

| Role | What the GDD says | Overlay added to the base coin/portal |
|---|---|---|
| Hold-and-spin coin | "Standard coin — currency value" | flat numeral space, gold default |
| WYSIWYG collector | "Pays a value during bonus when collected" | dollar/value sigil inside the disc |
| Scatter | "Triggers free spins / bonus when N land" | radiant burst rays around the disc, `SCATTER` label optional |
| Random-wilds shooter | "Stays on a specific row; shoots wilds onto reels" | directional arrows / energy beam motif on the portal |
| Collector + multiplier | "Pins to position; gathers values; ×N at end" | accumulator gauge or chevron ring around the disc |
| Adder | "Adds its value to surrounding/above values" | `+` glyph integrated with numeral space |
| HP-equivalent direct payout | "Pays a direct value like a regular HP symbol" | warm-gold premium treatment, same warmth band as HP1 |
| Loot Link trigger | "Activates the Loot Link bonus" | portal-style swirl behind the disc face |

For art generation, use `skills/slot-step-03/COIN_TEMPLATE.md` (the
WYS Family Template).

### SF family (special-feature symbols — also coin / portal / spherical)

The SF family is **just as overloaded** as WYS. Across 26 games SF is
used for hotspots, collectors, path-formers, lock-and-respin, jackpot
coins, bonus-game triggers, and mystery transforms. Every member shares
a visual family: coin / portal / spherical / feature-token shapes,
sometimes with a "closed object" motif (chest, orb, crystal ball) for
mystery sub-roles.

| Prefix | Family | Brief-driven roles |
|---|---|---|
| `SF`, `SF1`–`SF11+` | SF family | hotspot modifier · upgradable collector · immediate-payout collector · bonus value collector · transforming collector · path-forming prize · lock-and-respin · jackpot coin · bonus-game trigger · mystery transform |

Visual identity:
- **Shape:** circular feature-token, sphere, portal, or closed object (chest / orb / crystal ball) for mystery sub-roles
- **Surface:** slightly more "energetic" than WYS — pulse glow, particle motes drifting nearby, or a closed-object texture
- **Color:** warm luminous palette tied to the brief's primary; SF symbols are usually distinguished from WYS by shape silhouette rather than hue

Common brief-driven roles within the SF family:

| Role | What the GDD says | Overlay added to the base SF token |
|---|---|---|
| Hotspot multiplier | "Multiplies surrounding values by N" | `×N` numeric overlay, radial pulse |
| Hotspot adder | "Adds its value to all surrounding cells" | `+` sigil + outward arrows |
| Hotspot combiner | "Sums values in surrounding cells" | converging arrows + sum motif |
| Hotspot collapse | "Resolves a collapse / clear event" | imploding particle ring |
| Persistent hotspot | "Stays fixed across multiple bonus spins" | pin / lock anchor motif |
| Upgradable collector | "Gold bar / value collector that upgrades through the feature" | tier-marker chevrons stacked above the disc |
| Immediate-payout collector | "Collects WY values in base game, pays instantly" | dollar sigil with a cash-burst halo |
| Bonus value collector | "Gathers WY values during bonus, pays at end" | meter / gauge motif |
| Transforming collector | "Collects WY symbols then transforms into a WY" | morph / particle dissolve motif |
| Path-forming prize | "Creates a path activating adjacent specials" | directional path/bridge motif on the disc |
| Lock-and-respin trigger | "Locks others in place, grants respins" | chain / lock anchor + refresh ring |
| Jackpot coin | "Lands on the matrix; N of them trigger jackpot mode" | metallic medallion finish + crown / star sigil |
| Bonus-game trigger | "Triggers the bonus round when N land" | warm radial burst, `BONUS` label optional |
| Mystery transform | "Closed state until reveal; transforms into a random pay symbol" | closed object (chest / orb / `?` motif) instead of an open disc |

For art generation, use `skills/slot-step-03/MYSTERY_TEMPLATE.md` (the
SF Family Template — yes, the filename is historical; the template
covers the full SF family).

### Bonus trigger family

| Prefix | Family | Notes |
|---|---|---|
| `BO`, `BO1`+ | Bonus trigger | A dedicated bonus-game launcher, distinct from scatter. Many games ship both `BO` AND `SC` — each triggers a different feature. Check the brief. Visual: typically a **non-circular themed badge** (scroll, crystal, symbol of power) — designed to look meaningfully different from WYS coins and SC scatters. |
| `BAG` / `BAG_BO` | Money-bag scatter (sub-variant) | Green or theme-colored money bag; collected into a top row or meter. `BAG_BO` is the bonus-tagged variant. |
| `MOJ` | Money-emoji trigger | "💰" or themed emoji that triggers scatter collection over N spins. |

For art generation, use `skills/slot-step-03/BONUS_TRIGGER_TEMPLATE.md`.

### Blocker family

| Prefix | Family | Notes |
|---|---|---|
| `BL`, `BL1`, `BL2`+ | Blocker / Dead / Obstacle | Does not pay; blocks clusters/paylines. Numbered variants (`BL1`, `BL2`) appear when one game ships **multiple blocker types** for different modes (e.g. base-game blocker vs bonus-game blocker). Visual: dead/dark themed object — broken stone, rusted gear, obsidian shard, ash pile. |

For art generation, use `skills/slot-step-03/BLOCKER_TEMPLATE.md`.

### Jackpot family

| Prefix | Family | Notes |
|---|---|---|
| `JP`, `JP1`–`JP4` | Jackpot tiers (4-tier — most common) | Metallic medallion per tier; the **numeric ordering varies per game** (see "Jackpot numeric ordering" below). |
| `JP1`–`JP6` | Jackpot tiers (6-tier extension) | Mini · Minor · Major · Mega · Grand · Premium (Joker's Gems Jackpots style). |
| `JP1` (matrix-trigger flavor) | Jackpot trigger | Some games use `JP1` as the on-grid coin that triggers jackpot mode (Golden Knight, Tesla pattern) rather than as the highest tier. The brief disambiguates. |

**Jackpot numeric ordering — read the brief, never assume.** The
catalog of 26 shipped games shows multiple orderings of `JP1`–`JP4`:

| Game | `JP1` | `JP2` | `JP3` | `JP4` |
|---|---|---|---|---|
| Nissan | Mini | Minor | Major | Grand |
| Bankrush Beta | **Major** | Minor | Mini | — |
| Bankrush Gamma | **Major** | Minor | Mini | Grand |
| Billionaire's Beta / Gamma | **Grand** | Major | Minor | Mini |
| Chevy family (4 games) | **Grand** | Major | Minor | Mini |
| Tesla | **Grand** | Major | Minor | Mini |
| Blazing Stampede | **Grand** | Major | Minor | (no JP4) |

`JP1` means "Grand" in 9 of 11 games that use numeric jackpot prefixes.
Some older games still use `JP1` = "Mini". **Always read
`brief.jackpot_tier_names`** (an explicit mapping like
`{"JP1": "Grand", "JP2": "Major", "JP3": "Minor", "JP4": "Mini"}`) —
never guess from the prefix number alone.

Tier names also vary by game family:

| Common naming | Variant 1 | Variant 2 |
|---|---|---|
| Mini · Minor · Major · Grand | Bronze · Silver · Gold · Platinum | Hourly · Daily · Anytime |

For art generation, use `skills/slot-step-03/JACKPOT_TEMPLATE.md`.

### Loot Link / Hotspot family

These prefixes describe **Loot Link mini-matrix mechanics** in the
plugin's idealized vocabulary. Real-world GDDs frequently use generic
`SF1`–`SF11` numeric IDs for Loot Link symbols instead — when that
happens, the brief's `mechanic` field tells `slot-step-03` which Loot
Link role each `SF<N>` actually plays.

| Prefix | Mechanic |
|---|---|
| `COL` | Collector — pulls value into a meter or sweeps adjacent scatters |
| `ACT` | Activator — triggers another mechanic (spawn wild, duplicate, expand) when present |
| `HOT_x2`, `HOT_x5`, ... | Hotspot multiplier — multiplies surrounding values by N |
| `HOT_ADD` | Hotspot adder — adds the symbol's value to all surrounding cells |
| `HOT_COMB` | Hotspot combiner — sums values in surrounding cells |
| `HOT_COLLAPSE` | Hotspot collapse — resolves a collapse / clear event |
| `HOT_PERSIST` | Persistent hotspot — stays fixed across multiple bonus spins |

For art generation, use `skills/slot-step-03/LOOTLINK_TEMPLATE.md`.

### Pay-multiplier symbols

| Prefix | Family | Notes |
|---|---|---|
| `D2_<base>`, `D3_<base>` | Pay multiplier (renders as N of the base) | E.g. `D2_HP1` renders as 2 of HP1 stacked, pays as 2× HP1. `D3_HP1` = 3× treatment. |
| `DHP1`+ | Double HP (alias) | Same idea as `D2_HP1` but uses the H5G alias form (Eagles' Flight pattern). Route to the same Special-Mechanics template. |
| `SPLIT_<base>` | Split symbol | Mirrored / split treatment; pays as multiple. |
| `MULT_<value>` | Dedicated multiplier (not a wild) | E.g. `MULT_x10`. Stand-alone multiplier overlay symbol. |

For art generation, use `skills/slot-step-03/SPECIAL_MECHANICS_TEMPLATE.md`.

### Pachinko / Drop Zone family

For pachinko-style games (vertical drop, pegs, buckets — different game type entirely):

| Prefix | Family | Notes |
|---|---|---|
| `BALL` | Drop ball | the animated dropping element |
| `PEG` | Peg | the deflectors on the board |
| `BUCKET_<value>` | Award bucket | e.g. `BUCKET_x100`, `BUCKET_x1000` |

For art generation, use `skills/slot-step-03/PACHINKO_TEMPLATE.md`.

### Replacement / runtime swap

| Prefix | Family | Notes |
|---|---|---|
| `R`, `R1`+ | Replacement | Runtime substitution; a triggered event swaps this in for another symbol. Often two variants per game (`R1`, `R2`) with different replacement targets. Visual: distinctive but theme-coherent — needs to catch the eye on landing. |

If a brief shows an `R` symbol with `mechanic: TBD`, hold on art
generation and ask the user (or developer) for clarification — `R`
mechanics vary substantially between games.

---

## Compound prefixes — first-class symbols

Compound prefixes combine two role/family signals in one symbol ID.
They live in `Symbol_Art/` with the same `<PREFIX>_NNN.png` naming as
any other symbol (`BWY_001.png`, `WJP_001.png`, etc.) and route to a
**dominant base template + secondary overlay**.

| Compound | Means | Routes to (dominant template) | Overlay from |
|---|---|---|---|
| `BWY`, `BWY1`+ | Bonus + WYS (bonus-game trigger that also pays a WYS value) | `COIN_TEMPLATE.md` (WYS family) | bonus-trigger visual cues — warm radial burst, themed badge motif |
| `WJP`, `WJP1`+ | Wild + Jackpot (wild that also contributes to jackpot pool) | `WILD_VARIANTS_TEMPLATE.md` | jackpot-contribution overlay — metallic edge, tier sigil |
| `WDWY`, `WDWY1`+ | Wild + WYS (wild for WYS symbols; often also acts as scatter — Chevy pattern) | `WILD_VARIANTS_TEMPLATE.md` (scatter-wild hybrid section) | WYS coin/portal silhouette behind the wild label |
| `WDSF`, `WDSF1`+ | Wild + SF (wild SF created by duplication — Chevy-Alt pattern) | `WILD_VARIANTS_TEMPLATE.md` | SF family feature-token silhouette behind the wild label |
| `MUWD`, `MUWD1`+ | Multiplier + Wild (wild that carries a multiplier value) | `WILD_VARIANTS_TEMPLATE.md` (multiplier-wild section) | `×N` numeric overlay |
| `MUWDBO`, `MUWDBO1`+ | Multiplier + Wild + Bonus | `WILD_VARIANTS_TEMPLATE.md` (multiplier-wild) | `×N` + bonus framing |
| `SFWY`, `SFWY1`+ | SF + WYS (special-feature WYSIWYG collector) | `MYSTERY_TEMPLATE.md` (SF family) | WYS coin/portal visual notes |
| `DHP`, `DHP1`+ | Double HP (renders as 2× the base HP) | `SPECIAL_MECHANICS_TEMPLATE.md` | mirrored/doubled HP treatment |
| `WYS`, `WYS1`+ | WYSIWYG-with-variant-naming (alias for the WYS family) | `COIN_TEMPLATE.md` (WYS family) | same as `WY` |

When a compound prefix appears in a brief but a downstream skill can't
identify which is the dominant family, **default to whichever family
the symbol's `subject` and `role` text emphasize most** — and surface
the ambiguity to the user before generating.

---

## Routing by manifest role, not literal prefix

The catalog of 26 H5G GDDs shows the same prefix often means different
things across games. `WY1` is a coin in some games, a WYSIWYG collector
in others, a scatter in others. `SF1` is a Loot Link gold-bar collector
in Bankrush, a jackpot coin in Tesla, a path-forming prize in Blazing
Stampede.

The art skills (`/slot-step-03` especially) route by:

1. **Family** — pick the template (`COIN_TEMPLATE.md`, `MYSTERY_TEMPLATE.md`,
   etc.) from the prefix's family in the table above.
2. **Role overlay** — read the manifest's `mechanic` field on the
   specific symbol and apply the corresponding overlay cues from the
   family template's "brief-driven roles" table.
3. **Compound resolution** — if the prefix is compound, pick the
   dominant base template per the compound table above, then layer the
   secondary mechanic on top.

When in doubt, **the brief's `mechanic` text wins over the prefix's
literal name**. A symbol labeled `WY1` with `mechanic: "loot link
trigger"` routes the same way as one labeled `SF1` with the same
mechanic.

### Unknown / future prefix fallback

If a future GDD introduces a prefix not in this document:

1. Read the symbol's `subject` and `role`/`mechanic` text from the
   manifest.
2. Match it to the closest existing family by **visual identity** (is
   the description coin-like? a closed mystery object? a themed badge?
   a metallic medallion?).
3. Route to that family's template, apply the closest matching
   role overlay.
4. **Surface the unknown prefix to the user** in the next-step nudge so
   the vocabulary can be extended in a future release.

This keeps the system forward-compatible — new H5G mechanics can ship
on day one of a new GDD landing in `/slot-step-00`, even before this
vocabulary file is updated.

---

## Reading the symbol manifest

The `symbol_manifest` array in `game_brief.json` describes every
symbol the game ships. Each entry should carry **enough information for
the family + role routing to work without re-asking the user**.

```json
"symbol_manifest": [
  {"id": "HP1", "tier": "HP",      "family": "HP",       "subject": "phoenix bust",     "role": "high-pay character",                 "mechanic": "standard pay"},
  {"id": "WD1", "tier": "special", "family": "Wild",     "subject": "WILD label",       "role": "sticky wild",                        "mechanic": "sticky wild"},
  {"id": "WY1", "tier": "special", "family": "WYS",      "subject": "gold coin",        "role": "hold-and-spin coin",                 "mechanic": "hold-and-spin coin"},
  {"id": "WY2", "tier": "special", "family": "WYS",      "subject": "red portal disc",  "role": "scatter (random wilds shooter)",     "mechanic": "random wilds shooter"},
  {"id": "BO",  "tier": "special", "family": "BO",       "subject": "bonus medallion",  "role": "bonus game trigger",                 "mechanic": "free spins trigger"},
  {"id": "SF1", "tier": "special", "family": "SF",       "subject": "crystal ball",     "role": "mystery transform",                  "mechanic": "mystery transform"},
  {"id": "BL",  "tier": "special", "family": "Blocker",  "subject": "obsidian shard",   "role": "blocker — does not pay",             "mechanic": "blocker"},
  {"id": "JP1", "tier": "special", "family": "Jackpot",  "subject": "Grand jackpot",    "role": "highest jackpot tier",               "mechanic": "jackpot tier — Grand"},
  {"id": "BWY1","tier": "special", "family": "WYS",      "subject": "bonus coin",       "role": "bonus trigger + coin payout",        "mechanic": "bonus trigger + coin"},
  {"id": "WJP1","tier": "special", "family": "Wild",     "subject": "jackpot wild",     "role": "wild that contributes to jackpot",   "mechanic": "wild + jackpot contribution"}
]
```

Field reference:

- `id` — the literal prefix as the symbol's filename label (e.g.
  `HP1`, `BWY1`). This is what the file gets named: `Symbol_Art/<id>_NNN.png`.
- `tier` — one of `HP`, `MP`, `LP`, `special`.
- `family` — the visual family for routing. One of `HP`, `MP`, `LP`,
  `Wild`, `Scatter`, `WYS`, `SF`, `BO`, `Blocker`, `Jackpot`,
  `Pachinko`, `Replacement`, `SpecialMechanics`.
- `subject` — the user-facing thematic noun ("phoenix bust", "red coin",
  "crystal ball"). Drives the descriptive part of the prompt.
- `role` — short human-readable description of what the symbol is
  *playing* in the game. Optional but useful for tutorial / docs.
- `mechanic` — the **routing key**. The art skills look up the family
  template's "brief-driven roles" table for this string and apply the
  corresponding overlay cues.

The brief also carries `jackpot_tier_names` when JP symbols exist:

```json
"jackpot_tier_names": {
  "JP1": "Grand",
  "JP2": "Major",
  "JP3": "Minor",
  "JP4": "Mini"
}
```

---

## Naming convention for output files

Every reel symbol — regardless of family or compound status — lives in
the `Symbol_Art/` subfolder of the project root. Each symbol uses its
`id` as the filename label, with a three-digit counter scoped to the
folder. The compound prefixes follow exactly the same pattern as the
primitives.

```
Symbol_Art/HP1_001.png, Symbol_Art/HP1_002.png, ...
Symbol_Art/WD1_001.png, Symbol_Art/WD2_001.png, ...
Symbol_Art/WY1_001.png, Symbol_Art/WY2_001.png, Symbol_Art/WYS1_001.png, ...
Symbol_Art/SC_001.png, Symbol_Art/SW_001.png
Symbol_Art/BO_001.png, Symbol_Art/BAG_001.png, Symbol_Art/BAG_BO_001.png, Symbol_Art/MOJ_001.png
Symbol_Art/SF_001.png, Symbol_Art/SF1_001.png, ...
Symbol_Art/BL_001.png, Symbol_Art/BL1_001.png, Symbol_Art/BL2_001.png
Symbol_Art/JP1_001.png ... Symbol_Art/JP6_001.png
Symbol_Art/COL_001.png, Symbol_Art/ACT_001.png, Symbol_Art/HOT_x2_001.png, ...
Symbol_Art/R1_001.png
Symbol_Art/BWY_001.png, Symbol_Art/BWY1_001.png
Symbol_Art/WJP_001.png, Symbol_Art/WJP1_001.png
Symbol_Art/WDWY1_001.png, Symbol_Art/WDSF1_001.png
Symbol_Art/MUWD1_001.png, Symbol_Art/MUWDBO1_001.png
Symbol_Art/SFWY1_001.png
Symbol_Art/DHP1_001.png
Symbol_Art/D2_HP1_001.png, Symbol_Art/SPLIT_HP1_001.png, Symbol_Art/MULT_x10_001.png
Symbol_Art/BALL_001.png, Symbol_Art/PEG_001.png, Symbol_Art/BUCKET_x100_001.png
```

Each PNG is paired with a `.meta.json` sidecar in the same folder
containing its prompt and parameters. See `shared/asset_naming.md` for
the full label table and `shared/project_memory.md` for the project's
full folder layout.

---

## Template routing summary

The art-generation skills route based on family (derived from prefix or
brief):

| Family | Reads template | Covers |
|---|---|---|
| `HP` | `HP_TEMPLATE.md` | HP1, HP2, HP3, HP4 |
| `MP` | `MP_TEMPLATE.md` | MP1, MP2, MP3 |
| `LP` | `LP_TEMPLATE.md` | LP1–LP6 (cards / suits / fruits / gems / themed) |
| `Wild` (basic) | `WILD_TEMPLATE.md` | WD, WD1 (basic substitution) |
| `Wild` (variant or compound) | `WILD_VARIANTS_TEMPLATE.md` | WD2+, MUWD, MUWDBO, WDWY, WDSF, WJP |
| `Scatter` | `SCATTER_TEMPLATE.md` | SC, SC1+ (also SW handled here when classic scatter visual) |
| `WYS` | `COIN_TEMPLATE.md` (WYS Family Template) | WY, WY1–WY10+, WYS, WYS1+, BWY, SFWY (as WYS-overlay-SF) |
| `BO` | `BONUS_TRIGGER_TEMPLATE.md` | BO, BO1+, BAG, BAG_BO, MOJ |
| `SF` | `MYSTERY_TEMPLATE.md` (SF Family Template) | SF, SF1+, plus SFWY when SF visual dominates |
| `Blocker` | `BLOCKER_TEMPLATE.md` | BL, BL1, BL2+ |
| `Jackpot` | `JACKPOT_TEMPLATE.md` | JP1–JP6 (matrix triggers AND tier indicators); read `brief.jackpot_tier_names` |
| `Replacement` | clarify mechanic with user, then route by visual treatment | R, R1, R2+ |
| `SpecialMechanics` | `SPECIAL_MECHANICS_TEMPLATE.md` | D2_/D3_/SPLIT_/MULT_, DHP |
| `Pachinko` | `PACHINKO_TEMPLATE.md` | BALL, PEG, BUCKET_<value> |
| Loot Link mini-matrix | `LOOTLINK_TEMPLATE.md` | COL, ACT, HOT_*, plus SF<N> / WY<N> / BWY<N> when the brief's mechanic field says "loot link …" |

The compound prefixes route to the family of their **dominant base
mechanic**, with secondary mechanics layered as overlay cues per the
"Compound prefixes — first-class symbols" table.
