# Jackpot Family Template (`JP` prefix)

Jackpot symbols come in three functional flavors across the H5G
library: **matrix triggers** (the symbol that lands on the reel grid
and triggers jackpot mode), **tier indicators** (the per-tier
metallic medallions — Mini / Minor / Major / Grand and variants),
and **jackpot-mode sub-roles** that reuse JP prefixes inside
specific feature mechanics (Loot Link Jackpots, Prize Path Jackpots,
Jackpot Wheel slices).

Every JP member uses the same visual family: **metallic medallion
or coin-shaped badge**, with a tier-specific finish (bronze → silver
→ gold → platinum, or theme-specific variants per the brief).

These templates use the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`.

---

## CRITICAL — JP numeric ordering is per-game

**Never assume `JP1 = Mini` or `JP1 = Grand`.** The catalog of 26
shipped H5G games shows both orderings in production use:

| Game | `JP1` | `JP2` | `JP3` | `JP4` |
|---|---|---|---|---|
| Nissan | Mini | Minor | Major | Grand |
| Bankrush Beta | **Major** | Minor | Mini | — |
| Bankrush Gamma | **Major** | Minor | Mini | Grand |
| Billionaire's Beta / Gamma | **Grand** | Major | Minor | Mini |
| Chevy family (4 games) | **Grand** | Major | Minor | Mini |
| Tesla | **Grand** | Major | Minor | Mini |
| Blazing Stampede | **Grand** | Major | Minor | (no JP4) |

`JP1` means "Grand" in **9 of 11** games that use numeric JP prefixes.
A handful of older games (Nissan, Eagles' Flight in non-numeric form)
use the conventional `JP1 = Mini` order. Many games use explicit
named labels (`"Mini Jackpot"`, `"Major Jackpot"`) without numeric
prefixes at all.

**Always read `brief.jackpot_tier_names`** — an explicit mapping like:

```json
"jackpot_tier_names": {
  "JP1": "Grand",
  "JP2": "Major",
  "JP3": "Minor",
  "JP4": "Mini"
}
```

If the brief is missing this field, **stop and ask the user before
generating any JP art**. Getting this wrong means the most premium
tier ends up rendered with the bronze finish — visible to the player,
embarrassing in production.

## Tier-to-finish convention

| Tier name | Default metallic finish | Alternate naming families |
|---|---|---|
| Mini | bronze | Bronze |
| Minor | silver | Silver |
| Major | gold | Gold |
| Grand | platinum or diamond | Platinum |
| Mega (6-tier games) | rose-gold or burnished copper | (6-tier extension only) |
| Premium (6-tier games) | iridescent / mother-of-pearl / opal | (6-tier extension only) |

Theme-specific overrides are common — Egyptian games may use
turquoise / lapis / carnelian instead of bronze / silver / gold. The
brief's `subject` field on each `JP<N>` should specify; if not,
default to the metallic finish for the tier the brief's
`jackpot_tier_names` maps that JP to.

---

## Functional flavors — which prompt to use

| Mechanic the brief specifies | Use prompt section |
|---|---|
| `jackpot tier — Mini` / `jackpot tier — Minor` / `jackpot tier — Major` / `jackpot tier — Grand` / `jackpot tier — Mega` / `jackpot tier — Premium` | [Tier indicator (medallion)](#tier-indicator-medallion) |
| `jackpot trigger (matrix)` — the on-grid coin that triggers jackpot mode (Golden Knight Infinity, Tesla SF1 = "Jackpot Coin" pattern) | [Matrix trigger (jackpot coin)](#matrix-trigger-jackpot-coin) |
| `loot link jackpot` — JP symbols used inside the Loot Link bonus, awarded by connection (Majestic Cats, Da Vinci Deluxe Ways 2, Bankrush, Nissan pattern) | [Loot Link Jackpot](#loot-link-jackpot) |
| `prize path jackpot` — JP awarded via Prize Path connection (Blazing Stampede pattern) | [Prize Path Jackpot](#prize-path-jackpot) |
| `jackpot wheel slice` — full wheel graphic (Tesla pattern) | **NOT a reel symbol.** Route to `slot-step-06/WHEEL_TEMPLATE.md` and the `Wheels/` category folder, not here. |

---

## Tier indicator (medallion)

The standard JP tier indicator — appears on the jackpot reel, the
jackpot panel UI, or as a reel symbol in some games. Circular
metallic medallion fills the cell edge-to-edge.

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference for rendering technique, surface finish, and
lighting direction. Inherit ONLY the rendering technique from the
reference; ignore its background color and palette, specified below.

[MEDALLION SHAPE — circular jackpot tier indicator]
A circular jackpot tier medallion, fills the entire cell edge-to-edge.
Thick metallic outlined badge with sunburst pattern behind the label.
Premium ornate frame around a recessed inner face. Layered
construction: outer metallic frame · inner recessed face · centered
tier label.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (Jackpot family — <TIER_NAME> tier).
- Metallic finish: <TIER_METALLIC> (bronze for Mini, silver for Minor,
  gold for Major, platinum for Grand — OR the theme-specific override
  from the brief).
- Halo / aura: warm radiant glow tied to the metallic finish (cooler
  for silver / platinum; warmer for bronze / gold).

[SUBJECT INSIDE — "<TIER_LABEL>" label]
The tier name in caps — "<TIER_LABEL>" (e.g. "MINI", "MAJOR",
"GRAND"). Bold readable type, centered, scale tuned to read at
thumbnail size. A small thematic motif sits behind or below the
label (e.g. a phoenix wing, a crown, a thematic emblem from the
game's vocabulary).

[MOBILE CONSTRAINTS]
Fills entire cell edge-to-edge — this is a "fills 95% of cell"
symbol per `shared/art_principles.md` §3.5 jackpot tier band. Bold
clean shapes, high contrast between the metallic finish and the
black background. Centered, perfectly upright. Flat solid black
background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, mobile-optimized icon, only one symbol in the frame.
```

Substitute `<TIER_NAME>`, `<TIER_LABEL>`, and `<TIER_METALLIC>` from
the brief's `jackpot_tier_names` mapping for the specific `JP<N>`
being generated.

### Differentiation across tiers

When generating multiple tier indicators (JP1, JP2, JP3, JP4):

1. Generate the **highest-tier** medallion first (the one the brief
   maps to "Grand" — usually JP1 in modern games). This becomes the
   family anchor.
2. Pass it as a reference image when generating sibling tiers and
   state explicitly:

> "Same medallion grammar as the Grand jackpot already generated
> — same frame complexity, same engraving complexity, same overall
> composition. Differs only in metallic finish (this tier is
> <TIER_METALLIC>) and tier label ("<TIER_LABEL>")."

3. After all tiers are generated, lay them out side by side and
   confirm a clear value gradient — the Grand medallion should look
   visibly more premium than the Mini one, but they should read as
   a coordinated family (same grammar, different finish).

---

## Matrix trigger (jackpot coin)

The on-grid coin that triggers jackpot mode when N land — Golden
Knight Infinity, Tesla SF1 "Jackpot Coin" pattern. Some GDDs use
`JP1` for this role (in games where JP2-JP4 are the tier indicators);
others use `SF1` or a custom prefix.

```
[RENDER STYLE — LOCKED to <reference|style_lock>]
Match the reference for rendering technique. Inherit ONLY the
rendering technique; palette below overrides.

[COIN SHAPE — jackpot trigger coin]
A circular jackpot trigger coin, fills the cell prominently with a
small border. Coin grammar — thick metallic rim, recessed face,
themed engraving — but tuned for the "trigger this feature" energy:
strong warm-gold luminous edge, particle motes drifting near the
disc face.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: special (Jackpot family — matrix trigger).
- Metallic finish: warm gold (the family-anchor finish).
- Halo: strong radiant warm-gold glow + soft sparkle particles.

[SUBJECT INSIDE — jackpot emblem]
A jackpot emblem on the coin face — crown, lightning bolt, or
thematic icon that clearly reads "this is THE jackpot coin". The
emblem dominates the disc face; no numeral space needed (this coin
doesn't carry a value, it triggers a feature).

[MOBILE CONSTRAINTS]
Distinct from any WYS coin in the set — the warm-gold luminous glow
and the jackpot emblem are the giveaways. Flat solid black
background, no gradients.

high quality game asset, sharp clean edges, professional slot game
art, only one symbol in the frame.
```

---

## Loot Link Jackpot

In Loot Link / Hold-and-Spin bonus games, JP symbols are awarded
when the player fills a connected pattern. The visual is the same
tier-indicator medallion (above), but the brief may want to
emphasize the "earned via connection" energy.

Use the [Tier indicator (medallion)](#tier-indicator-medallion)
prompt and add this overlay clause inside `[COLOR SYSTEM]`:

> "Role overlay: subtle connector lines / energy threads radiating
> from the medallion edge — this jackpot was earned via connection
> in the Loot Link bonus."

The connector-line motif should be short and clearly part of the
medallion, not a full path crossing the cell.

---

## Prize Path Jackpot

Similar to Loot Link Jackpot but specific to Prize Path mechanics
(Blazing Stampede). Same medallion grammar, with a directional path
overlay.

Use the [Tier indicator (medallion)](#tier-indicator-medallion)
prompt and add this overlay clause:

> "Role overlay: a stylized path/trail emerging from the medallion
> base — short luminous lines suggesting this jackpot connects via
> a Prize Path."

---

## Jackpot Wheel slices — route elsewhere

If the brief's `mechanic` for a JP symbol is `jackpot wheel slice`,
the symbol is **not a reel asset** — it's a slice within a full
wheel graphic. The Tesla pattern uses JP1-JP4 as wheel slices on a
dedicated bonus wheel UI surface.

For wheel art:

1. **Stop generating reel-symbol JP art.**
2. Route the user to `/slot-step-06` with the `wheel_<variant>`
   surface and the `WHEEL_TEMPLATE.md` template.
3. The wheel renders as a **single full graphic** with all tier
   slices laid out around it, not as individual slice files.
4. Output lands in `Wheels/` (a category folder), not `Symbol_Art/`.

---

## Pre-gen quick checks

- [ ] `style_anchor` (from `project.json.style_anchor.text`) is prepended verbatim
- [ ] `brief.jackpot_tier_names` mapping has been read — the agent knows whether `JP1` is Grand or Mini for this specific game
- [ ] Tier label matches the brief's mapping (caps, exact spelling: "MINI" not "MIN", etc.)
- [ ] Metallic finish matches the tier rule OR the brief's theme-specific override
- [ ] "Fills entire cell edge to edge" stated (jackpot tier band)
- [ ] Background is `flat solid black background, no gradients`
- [ ] For matrix trigger: emblem dominates, no numeral space (this coin doesn't carry a value)
- [ ] For Loot Link / Prize Path overlays: the overlay cue is added, not omitted
- [ ] Wheel-slice route is rejected and redirected to `/slot-step-06` if the brief asks for it here

## Post-gen quick checks

- [ ] Medallion is circular and fills the cell edge-to-edge
- [ ] Tier label is clearly readable at thumbnail size
- [ ] Metallic finish reads as distinctly bronze / silver / gold / platinum (not generic warm)
- [ ] Tier hierarchy reads visibly across the set (Grand > Major > Minor > Mini in premium feel)
- [ ] Differentiable from scatter and other special symbols (scatter has burst rays; jackpot has the metallic medallion frame)
- [ ] For matrix trigger: emblem reads as "the jackpot coin" — not a generic gold coin
- [ ] Silhouette readable at 64 px (black-fill test per `shared/art_principles.md` §10)

## Multiple jackpot tiers in one game (4-tier and 6-tier)

The most common configuration is 4 tiers (`JP1`–`JP4`, mapping to
Grand / Major / Minor / Mini in modern games). Joker's Gems Jackpots
and similar premium games extend to 6 tiers (`JP1`–`JP6`, adding
"Mega" and "Premium" — typically the brief specifies the mapping).

Generate in tier order from highest to lowest (Grand → Major →
Minor → Mini → ...) so the family anchor is set by the most
premium tier. Pass each tier as a reference when generating the
next so the family grammar stays consistent — only the metallic
finish and tier label change.

## Anti-patterns

- ❌ Assuming `JP1 = Mini` (the catalog shows 9/11 modern games use `JP1 = Grand`)
- ❌ Generating jackpot art without reading `brief.jackpot_tier_names`
- ❌ Painting a static currency value into the medallion face (the jackpot value is set at runtime by the engine)
- ❌ Letting the jackpot medallion look like a regular WYS coin — the metallic frame and tier label are the differentiators
- ❌ Generating wheel slices as individual JP symbols (route to `/slot-step-06` for the wheel surface instead)
- ❌ Different rendering techniques across tiers (a painterly Grand medallion paired with a cel-shaded Mini — the family grammar must be consistent)
