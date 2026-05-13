# LP — Low-Pay Symbol Templates

LP is the coolest, simplest, least ornamented tier. There are usually 5–6
in a set (LP1–LP6). The LP family is locked in `brief.tier_plan.lp_family`
and can be one of: `card_royals`, `suits`, `themed_objects`, `gems`. **Never
mix families** within one set.

These templates use the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1) is
prepended to every prompt verbatim — it lives in `project.json.style_anchor.text`.

## Universal LP rules (all families)

- **Background:** flat solid white, no gradients
- **Palette:** cool muted only — soft cyans, silvers, pale theme accents
- **Light:** flat or very subtle; no rim glow
- **Size phrase:** "small and understated, generous empty space"
- **Tier hierarchy:** clearly the simplest, coolest, least ornamented in the set
- **No HP-style plaque.** LP is just the subject on a flat field.

## ⛔ LP forbidden words (hard gate)

These words must NEVER appear in an LP prompt. If any is present, rewrite
before calling `nb2_generate`:

- `gold`
- `amber`
- `warm`
- `detailed`
- `ornate`
- `rich`
- `glowing`

This is enforced in `shared/qa_preflight.md` Gate 1 — pre-generation
validation will reject the prompt before NB2 sees it.

## LP family — `card_royals` (A K Q J 10 9)

This is the most common LP family. Each LP is one card royal letter/number.

```
[RENDER STYLE — LOCKED to <style_lock>]
Flat vector game icon design. Letter shape reads first. No drawn outlines
on the letter. No painterly modeling. No metallic surface. Do not pull
any warmth or trim from any HP reference — LP exists outside the HP
palette entirely.

[BADGE SHAPE — minimal]
Generous empty space around the letter. No ornate frame, no plaque, no
metal — a simple flat field. The card letter is the entire visual content.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: low-pay (LP<N>).
- Palette: cool muted only — soft cyan, pale silver, dusty blue. NO
  warm gold, NO amber, NO crimson, NO warm trim anywhere, not even as
  accents.
- Theme decoration: subtle and behind the letter — never competing
  with the letter for legibility.

[SUBJECT INSIDE — letter "<letter>"]
The letter "<letter>" as a low-pay slot symbol. Small and understated.

[MOBILE CONSTRAINTS]
Clear silhouette at tiny thumbnail size. Flat solid white background, no
gradients. Generous empty space. Sharp clean edges.

professional slot game art. (Do not use the word "detailed".)
```

## LP family — `themed_objects`

Small theme-relevant objects (e.g., feathers, beads, scarabs, runes — never
the same category as HP/MP).

```
[RENDER STYLE — LOCKED to <style_lock>]
Flat vector game icon design. Bold simple silhouette. No painterly
modeling. No metallic surface. No warmth carried down from HP.

[BADGE SHAPE — minimal]
Generous empty space. No plaque, no frame. The object alone on a flat
white field.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: low-pay (LP<N>).
- Palette: cool muted <theme> palette only. NO warm gold, NO amber.

[SUBJECT INSIDE — <subject>]
<subject> as a low-pay slot symbol. Small and understated.

[MOBILE CONSTRAINTS]
Clear silhouette at thumbnail size. Flat solid white background, no
gradients. Generous empty space. Sharp clean edges.

professional slot game art. (Do not use the word "detailed".)
```

## LP family — `gems`

Faceted gemstones in cool colors only.

```
[RENDER STYLE — LOCKED to <style_lock>]
Flat vector game icon design. 2 to 3 clean specular points only — not
8 micro-facets. No painterly modeling.

[BADGE SHAPE — minimal]
The gem alone on a flat white field. No plaque, no metal setting.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: low-pay (LP<N>).
- Palette: cool muted <gem_color> faceted gem only. NO warm gold or
  amber on the stone or any setting.

[SUBJECT INSIDE — <gem_type>]
A <gem_color> <gem_type> gemstone as a low-pay slot symbol. Small.

[MOBILE CONSTRAINTS]
Clear silhouette at thumbnail size. Flat solid white background, no
gradients. Generous empty space. Sharp clean edges.

professional slot game art. (Do not use the word "detailed".)
```

## LP family — `suits` (♠ ♥ ♦ ♣)

Stylized card suit icons themed to the game.

```
[RENDER STYLE — LOCKED to <style_lock>]
Flat vector game icon design. Bold simple suit silhouette.

[BADGE SHAPE — minimal]
Suit icon centered on flat white field, no frame.

[COLOR SYSTEM FOR THIS SYMBOL]
- Pay tier: low-pay (LP<N>).
- Palette: cool muted — silver and pale theme color. NO warm gold or amber.

[SUBJECT INSIDE — <suit_name>]
<suit_name> playing card suit icon as a low-pay slot symbol.

[MOBILE CONSTRAINTS]
Clear silhouette at thumbnail size. Flat solid white background, no
gradients. Generous empty space. Sharp clean edges.

professional slot game art.
```

## Pre-gen quick checks

- [ ] `style_anchor.text` (from `project.json.style_anchor.text`) is prepended to the prompt verbatim
- [ ] Prompt contains ZERO forbidden words (see list above)
- [ ] `[RENDER STYLE — LOCKED]` block present with explicit "no HP warmth carry-down" clause
- [ ] Background is `flat solid white background, no gradients`
- [ ] Palette is cool and muted only
- [ ] LP family matches `brief.tier_plan.lp_family` (no mixing)
- [ ] If card_royal: subject is a letter/number, not a themed object
- [ ] Subject is described as "small and understated"

## Post-gen quick checks

- [ ] Zero gold / amber / warm trim visible (any → BLOCK, auto-regenerate)
- [ ] Background is flat white (no off-white, no gradient)
- [ ] Cooler and simpler than every other tier in the set
- [ ] If card_royal: the letter/number reads first, decoration is subtle behind
- [ ] Family is consistent with sibling LPs (no mixing card royals with gems, etc.)
