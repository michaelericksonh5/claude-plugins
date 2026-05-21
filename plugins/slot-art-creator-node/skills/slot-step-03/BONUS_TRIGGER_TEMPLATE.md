# Bonus Trigger Template (`BO`)

`BO` is a dedicated bonus-game launcher, distinct from a scatter (`SC`)
and from coins (`WY`). Some games use `BO` instead of a scatter; some
games use both, where each triggers a different feature (the scatter
might launch free spins while `BO` launches a pick-me).

## How `BO` differs from scatter and coin

| Feature | `SC` (scatter) | `BO` (bonus trigger) | `WY` (coin) |
|---|---|---|---|
| Shape | circular badge | non-circular themed object OR distinct badge | circular coin / medallion |
| Carries currency | no | no | yes (runtime overlay) |
| Mechanic | triggers free spins / bonus | triggers a SPECIFIC bonus game | hold-and-spin / collector |
| Visual aim | radiant, attention-grabbing | unique, theme-deep | metallic, currency-feel |

If the brief lists both `SC` and `BO`, they MUST be visually
distinguishable so players can tell at a glance which one they hit.

This template uses the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`. The `<style_lock>` placeholder
below is substituted with the same text at prompt-assembly time.

## Universal rules

- **Background:** flat solid black, no gradients
- **Shape:** non-circular when possible (lets it stand apart from coins and scatters)
- **Theme:** deeply theme-rooted — not a generic burst
- **Label:** the word "BONUS" or `brief.bonus.label` is part of the symbol
- **Sizing:** "prominent, fills the cell with a small border"

## Prompt — Bonus trigger

```
"<bonus.label>" themed bonus trigger symbol,
<bonus.subject> as the central thematic element rendered prominently,
fills the cell with a small border, deeply <theme_summary>-themed,
distinct from any scatter or coin symbol in this game —
not a circular burst, not a coin medallion,
<palette_leads.primary> palette with rich detail,
<style_lock>,
centered on flat solid black background no gradients,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Substitute:
- `<bonus.label>` from `brief.bonus.label` (e.g., `"BONUS"`, `"FEATURE"`, `"START"`)
- `<bonus.subject>` from `brief.bonus.subject` (e.g., `"ancient scroll"`, `"crystal ball"`, `"map fragment"`)

## Common BO subjects by genre

| Genre | Suggested BO subject |
|---|---|
| Egyptian | sealed scroll, scarab cartouche, golden ankh |
| Asian / Oriental | jade dragon medallion, lucky cat statuette, ornate fan |
| Fantasy | spellbook, runestone, crystal orb |
| Norse / Viking | rune-carved horn, Mjolnir pendant |
| Pirate | treasure map, compass with glow |
| Steampunk | brass key, gear assembly |
| Holiday Christmas | wrapped present with bow |
| Holiday Halloween | jack-o-lantern with glow |
| Sci-fi | data crystal, alien artifact |

These are starting points — the brief should specify.

## Pre-gen quick checks

- [ ] `BO` is described as DIFFERENT from any scatter / coin in this game
- [ ] Shape is non-circular OR has clear visual cues that distinguish it from coins
- [ ] Theme subject is theme-rooted (not a generic burst)
- [ ] Bonus label text is in the prompt
- [ ] Background is `flat solid black background, no gradients`

## Post-gen quick checks

- [ ] Reads as a bonus-game launcher, not as a scatter or coin
- [ ] If the game also has SC or WY symbols, this BO is visually distinct
  side-by-side
- [ ] Theme element is unmistakable
- [ ] Label text is readable at thumbnail size

## When BO IS scatter

Some older games use `BO` as the scatter (single special trigger
symbol). In that case, fall back to `SCATTER_TEMPLATE.md` and use the
circular badge convention. The brief should disambiguate; if it
doesn't, ask the user before generating.
