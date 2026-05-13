# Win Banner Templates

Win banners are the celebration overlays for big wins. They're the most
visible, highest-budget UI surface in the game — the player sees them at
peak emotional moments, so production discipline here matters more than
on most other assets.

The numeral is always the focal point — actual win amounts get composited
at runtime, so the banner generates with empty space reserved for them.

---

## Tier system — bet-ratio thresholds

Banner tiers are determined by **win ÷ bet ratio**, not by absolute coin
value. This is the industry-standard threshold table (condensed from
internal H5G win-banner research):

| Tier | Win / Bet ratio | Label |
|---|---|---|
| Small Win | < 5× | `"WIN"` (often silent — no banner) |
| Medium Win | 5× – 10× | `"NICE WIN"` |
| Big Win | 10× – 25× | `"BIG WIN"` |
| Mega Win | 25× – 50× | `"MEGA WIN"` |
| Epic Win | 50× + | `"EPIC WIN"` |

Most games ship 3 tiers (Big / Mega / Epic). Some ship 5 (Small / Medium /
Big / Mega / Epic). Always use what `brief.banners` specifies — the
distinct ratio bands are the contract.

---

## The 9-layer win-overlay stack (back to front)

Every win banner is built as a 9-layer composition, back to front. The
banner art generates layers 1-7 in a single image; runtime adds 8-9.

| # | Layer | Purpose |
|---|---|---|
| 1 | Full-screen radial vignette | Darkens periphery, focuses center |
| 2 | Sunburst rays radiating from center | Adds movement, signals celebration |
| 3 | God rays / light shafts | Volumetric depth |
| 4 | Warm gradient overlay (gold/amber wash) | Mood color cast |
| 5 | Themed ornate frame | Tier-specific complexity |
| 6 | Themed props (corner ornaments, side flourishes) | Tier-specific richness |
| 7 | Tier label text ("BIG WIN" etc.) — upper area, never center | Reads the tier |
| 8 | Win-amount numeral *(runtime)* | The actual coin number |
| 9 | Foreground sparkles, particles *(runtime)* | Real-time animation |

**The banner art must leave generous empty space in the center for layers
8-9.** Layer 7's tier label goes in the upper third — never compete with
the center where the numeral lives.

---

## The 7-layer numeral premium stack (for layer 8 at runtime)

The runtime numeral itself is a 7-layer composition built in this order
(back to front). Banner art doesn't render the numeral, but the **banner
must visually accommodate** all 7 layers — leave room for the drop shadow
and outer glow to breathe.

1. **Gold gradient fill** — top `#FFE066` → mid `#FFD700` → shadow
   `#C8960C` → deep `#8B6914` (5-7 stops)
2. **Specular band** — bright streak ~1/3 from top of cap height
3. **Dark outline** (50–70% opacity) — primary edge separation
4. **Secondary outline** — thinner, contrast color
5. **Upper-left bevel highlight** — dimensional pop
6. **Drop shadow** — 6-12 px offset, soft
7. **Outer glow** — warm radiance, ~10–20% of cap height

**Numeral sizing:** 40–60% of portrait width at Big Win; 50–70% at
Mega/Epic. The empty space the banner reserves should be at least 60% of
the banner's interior width to allow for Epic-tier numerals.

---

## Tier escalation guide

When generating multiple tiers, **at least 2 axes must differ visibly
between adjacent tiers**. Use the table below. Adjacent tiers (Big→Mega
or Mega→Epic) should feel categorically different, not just "the same
banner but more saturated."

| Axis | Big | Mega | Epic |
|---|---|---|---|
| Frame complexity | Simple ornate | Sculptural with corner ornaments | Maximalist, layered with corner props + side flourishes |
| Burst density | Medium ray count | Dense ray count | Radiant explosion — overlapping ray layers |
| Palette intensity | Warm gold | Gold + crimson accents | Gold + crimson + electric accents |
| Vignette darkness | Medium | Strong | Very strong, corners near pure black |
| Center clearance | 60% interior | 65% interior | 70% interior (Epic numerals are biggest) |
| Foreground props | None | Subtle corner ornaments | Corner ornaments + side flourishes |
| God rays | None | Subtle | Strong volumetric shafts |

A player (and the user reviewing) should be able to identify which tier
just hit at a glance, without reading the label.

---

## Bracketed-block prompt — single tier

Style Anchor (§9.2.1 of nb2_prompting.md) is prepended verbatim. The body:

```
[RENDER STYLE — LOCKED to <style_lock>]
Match the game's existing key-art rendering technique exactly. Painted
celebration overlay, mobile slot game UI, theatrical lighting, not
photorealistic.

[OVERLAY COMPOSITION — 9-layer build]
Full-screen radial vignette (corner darkness <tier-specific>). Sunburst
rays radiating from the center at <tier-specific density>. <Tier-specific
god rays if Mega/Epic>. Warm gradient overlay wash. Themed ornate frame
with <tier-specific complexity>. <Tier-specific corner props and side
flourishes>. Tier label text in the UPPER area only — never centered.
Center has a large empty space (~<tier-specific>% of interior width)
reserved for the runtime win-amount numeral.

[COLOR SYSTEM]
<Tier-specific palette: Big = warm gold; Mega = gold + crimson;
Epic = gold + crimson + electric accents>. Halo of warm gold light
radiates from behind the empty numeral zone — this is space that will
be filled by the runtime numeral and its drop shadow + outer glow.

[TIER LABEL — upper area]
"<TIER_LABEL>" text in premium gold lettering — gold gradient fill, dark
outline ~50-70% opacity, upper-left bevel highlight, soft drop shadow.
Positioned in the upper third of the banner — never competing with the
center numeral space.

[NO RUNTIME ELEMENTS]
Do not draw actual win-amount numerals — runtime composites the live
coin count. Do not draw foreground sparkle particles — those are
runtime overlay too. The banner art is everything BEHIND the numeral.

[MOBILE CONSTRAINTS]
9:16 portrait. High-contrast palette readable on small phone screens.
Center clearance is non-negotiable — the numeral and its outer glow
need breathing room.

high quality game asset, professional slot game art, premium celebration
overlay.
```

---

## Pre-gen quick checks

- [ ] Tier label is one of the brief's banner tier set (matches a bet-ratio band)
- [ ] Empty center space stated explicitly (~60-70% of interior width)
- [ ] "No actual numerals" stated — runtime adds them
- [ ] "No foreground sparkles" stated — runtime adds them
- [ ] Sunburst rays + radial vignette stated
- [ ] Tier-specific intensity matches the position in the escalation
- [ ] Tier label text positioned in upper area, not center
- [ ] At least 2 axes from the escalation table differ from the previous tier

## Post-gen quick checks

- [ ] Center has a clear empty space large enough for the runtime numeral + glow
- [ ] Tier label text is in the upper area, not central
- [ ] Frame complexity, burst density, or palette intensity visibly differs from sibling tiers (at least 2 axes)
- [ ] Vignette darkness escalates correctly relative to other tiers
- [ ] Palette is theme-consistent (uses `palette_leads`)
- [ ] No accidental numerals or particles drawn into the banner

## Generating the full set

When asked for "all banner tiers," generate them in order
(small → medium → big → mega → epic) and **pass each prior tier as a
reference image** so the escalation reads consistently. Save as
`Banner_small_NNN.png`, `Banner_medium_NNN.png`, `Banner_big_NNN.png`,
`Banner_mega_NNN.png`, `Banner_epic_NNN.png`.

After the full set is generated, review them as a strip side-by-side
(thumbnail comparison) before declaring the set done. The tier
escalation should read at a glance with no labels visible.
