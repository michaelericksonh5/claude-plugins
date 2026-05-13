# Special Mechanics Template

Less common symbol types that don't fit cleanly into the major
categories above. Most games use one or zero of these. Read the section
that matches the symbol in the brief.

If a symbol type ISN'T listed here and isn't in any other template,
stop and ask the user to clarify the mechanic before generating.

This template uses the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`. The `<style_lock>` placeholder
below is substituted with the same text at prompt-assembly time.

---

## Split / Double / Triple symbols (including `DHP` alias)

A family of pay-multiplier symbols where one cell pays as **two or three
of itself**. Found in Split Dragon (split mechanic), Da Vinci Deluxe
Ways (double + triple symbols), and similar multi-pay games.

ID convention:
- `SPLIT_<base>` — generic split (pays as 2)
- `D2_<base>` — explicit double (pays as 2)
- `D3_<base>` — explicit triple (pays as 3)
- `DHP`, `DHP1`+ — H5G alias form for "Double HP" (Eagles' Flight PB
  pattern). Treat `DHP1` as functionally equivalent to `D2_HP1` —
  same visual treatment, just a different naming convention. Filename
  is `DHP1_001.png` (not `D2_HP1_001.png`) when the brief uses this
  alias.

Example: `D2_HP1` is "HP1 with the double overlay" and pays as 2× HP1.
`DHP1` is the same idea expressed in H5G's compact-alias form —
typically a doubled or split rendering of the game's HP1 character.

### Split / Double prompt

```
<base_subject> as a split slot symbol — pays as 2 of itself,
the symbol shows a clear "doubled" or "split" visual cue —
either a mirrored / twin treatment with the subject visible TWICE,
or a small "×2" badge in the upper corner,
fills the cell prominently,
<style_lock>,
centered on flat solid <bg> background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one cell — but with the doubled treatment within it.
```

### Triple prompt

```
<base_subject> as a triple slot symbol — pays as 3 of itself,
the symbol shows a clear "tripled" visual cue —
the subject visible three times in a tight stacked or arrayed composition,
OR a prominent "×3" badge with the base symbol behind,
fills the cell prominently,
<style_lock>,
centered on flat solid <bg> background no gradients,
clear silhouette, sharp clean edges, professional slot game art.
```

**Rules:**
- Base symbol art should match its tier's normal treatment
- The "split / double / triple" cue is an OVERLAY on top — not a redesign of the base
- Background follows the base symbol's tier (HP→black, LP→white, etc.)
- For Split Dragon-style games: the wild symbol should "count as 2" of
  the split base — note this in the WILD prompt, not here
- Generate the base symbol FIRST, then pass it as a reference image when
  generating the doubled/tripled variant so the base art matches exactly

---

## Collector symbols

Accumulate currency or trigger values into a meter. Visual: a **vessel**
(jar, chest, pouch, urn, cauldron) — clearly a container.

```
<collector.subject> as a slot collector symbol,
clearly a vessel — a jar, chest, pouch, or container,
glowing accumulator aesthetic, fills the cell prominently,
<style_lock>,
<palette_leads.primary> palette with a slight glow indicating accumulated value,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

**Rules:**
- Vessel must look open or have a visible "filled" interior
- Glow communicates the accumulated state
- NOT a coin (that's WY territory)

---

## Multiplier symbols (non-wild)

Some games have a dedicated multiplier symbol (not a multiplier wild).
The number is the dominant element.

```
"×<value>" multiplier slot symbol,
dominant numeric multiplier in metallic gold,
sunburst or radiant pattern behind the number,
<style_lock>,
centered on flat solid black background no gradients,
sharp clean edges, professional slot game art.
```

If multiple denominations exist (×2, ×5, ×10), use the metallic tier
escalation from `JACKPOT_TEMPLATE.md`:
bronze (×2–3) → silver (×5–10) → gold (×15–25) → platinum (×50+).

---

## Hold & Spin / Lock-and-spin trigger

Some hold-and-spin features have a **dedicated trigger symbol** distinct
from the WY coins themselves. Often called a "Link" symbol.

```
A circular link / hold-and-spin trigger slot symbol,
distinct from the WY coin family — feels like a feature LAUNCHER, not a coin,
"LINK" or theme label in metallic treatment,
fills the cell prominently with a thick gilded border,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art.
```

---

## Megaways tile / column counter

For Megaways-style games, the "column counter" or "ways indicator" is a
small UI element overlaid on each reel. Not a reel symbol per se — but
sometimes generated as art.

This is usually a UI element. If it appears in the symbol manifest,
treat as a small numeral badge with a thin themed frame.

---

## Cluster-pay base symbols

Cluster-pay slots have all-the-same-shape symbols (typically gems or
candies) that connect in clusters of 5+. They look like LPs but the
mechanic differs — generate as LPs (using `LP_TEMPLATE.md`) with the
gem family, and note in the brief that the game is cluster-pay.

No special art treatment is needed — the cluster-pay mechanic is a
runtime behavior, not a visual one.

---

## Tumble / Cascade symbols

Symbols that tumble (fall) into place after winning combinations are
removed. Same art as base symbols — no special treatment. The cascade
is a runtime animation, not a separate symbol.

---

## Persistent symbols

Some games have NON-WILD symbols that persist across multiple spins —
e.g., a multiplier that locks to a position and stays there for the rest
of the bonus, or a money emoji that stays for N spins. The persistence
is a runtime mechanic, but the **art** should hint at the locked state.

```
[Use the appropriate base symbol prompt — multiplier, money emoji, etc.]
[Then add this overlay sentence:]
A small lock or anchor icon in the upper corner of the symbol indicating
this symbol persists in place across spins.
```

The lock overlay is the same convention as `HOT_PERSIST` from
`LOOTLINK_TEMPLATE.md` — keep it consistent across the game so players
recognize "lock = persistent" universally.

---

## Buy Bonus / Power Bet indicators

These are NOT reel symbols — they're UI elements (buttons or HUD
indicators that let the player buy or activate a feature). Use
`/slot-step-06` with the `hud` or `bonus_screen` surface, NOT
this template.

If a brief lists `BUY_BONUS` or `POWER_BET` as a "symbol," confirm with
the user that they don't actually mean the UI button.

---

## Pre-gen quick checks (universal)

- [ ] Symbol type is identified clearly (split / collector / multiplier / etc.)
- [ ] Background color matches the tier convention (HP/wild = black, LP = white, special = black)
- [ ] No hex / resolution / aspect ratio in prompt body
- [ ] If multiple variants of the same special type, each is described as
  distinct from siblings

## Post-gen quick checks (universal)

- [ ] Mechanic is communicated visually (split feels split, collector
  feels containing, multiplier feels valuable)
- [ ] Distinguishable from any other special symbol in this game
- [ ] Theme-appropriate
- [ ] Style matches the locked key art

## Unsupported / unrecognized mechanics

If a brief lists a symbol type that isn't covered by any template
(e.g., "Quantum symbol", "Phase shift token"), STOP and ask the user:

> "The brief lists `<id>` with mechanic `<mechanic>`. I don't have a
> template for this — can you describe what visual treatment you want
> and I'll generate from your description? Or do you want me to skip
> this one for now?"

Don't fabricate a treatment.
