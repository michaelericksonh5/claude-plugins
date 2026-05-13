# Blocker / Dead / Obstacle Template (`BL`, `BL1`, `BL2`+)

`BL` symbols **do not pay**. They block clusters or paylines, fill
reels in specific modes as placeholders, or create friction in
cluster-pay and grid-clear games. They're meant to feel like an
obstacle (or absence) — not a reward.

A game may ship a single `BL` or multiple numbered variants
(`BL1`, `BL2`, …). The catalog of 26 H5G GDDs shows two common
multi-variant patterns:

- **Mode-specific blockers** — `BL1` fills bonus reels, `BL2`
  fills base-boost reels (Dodge pattern). Both are non-paying
  but they may render slightly differently to signal which mode
  they belong to.
- **Damage / clearable tiers** — `BL1` clearable in 1 hit, `BL2`
  clearable in 2 hits, escalating "damage" visual.

Read the brief's `mechanic` field on each `BL<N>` to decide which
pattern this game uses.

Common in: cluster-pay slots, grid-clear / "remove blockers"
mechanics, match-3-style slots, mode-specific placeholders, certain
bonus games where blockers must be cleared to win.

These templates use the **bracketed-block prompt format** from
`shared/nb2_prompting.md` §9.2. The game's **Style Anchor** (§9.2.1)
is prepended to every prompt verbatim — it lives in
`project.json.style_anchor.text`.

## Universal rules

- **Background:** flat solid black, no gradients
- **Aesthetic:** **dead, dark, decorative** — broken stone, rusted gear,
  obsidian shard, ash pile, cracked artifact
- **Reads as "not a pay symbol":** must not look like an HP, MP, LP,
  or any special — visually clearly a non-paying obstacle
- **Sizing:** "fills the cell with normal padding, similar to LP/MP scale"
- **Color:** muted, desaturated — even if the theme is warm, the BL skews
  cool / gray / dark

## Common BL visual treatments

| Theme | BL subject |
|---|---|
| Egyptian | broken stone fragment, cracked sarcophagus shard |
| Fantasy | obsidian shard, cursed runestone, broken sword |
| Sci-fi | scrap metal, dead circuit board, ash pile |
| Pirate | broken barrel staves, rusted chain link |
| Ocean | barnacle-crusted debris, sunken cracked stone |
| Norse | broken Mjolnir fragment, cracked rune stone |
| Generic | rusted gear, weathered wood plank, ash heap |

## Prompt — Blocker

```
<blocker.subject> as a slot blocker symbol — does not pay,
dead, dark, weathered aesthetic — clearly an obstacle, not a reward,
muted desaturated palette skewing cool and gray,
<style_lock>,
centered on flat solid black background no gradients,
fills the cell with normal padding,
clear silhouette, sharp clean edges, professional slot game art,
only one symbol in the frame.
```

Substitute `<blocker.subject>` from the brief.

## Pre-gen quick checks

- [ ] `style_anchor` (from `project.json.style_anchor.text`) is prepended verbatim
- [ ] Subject is something dead / broken / weathered
- [ ] Palette is muted and desaturated (NOT the brief's saturated primary)
- [ ] "Does not pay" intent is in the prompt
- [ ] Subject is NOT something a player would want to land
- [ ] Background is `flat solid black background, no gradients`
- [ ] When generating multiple `BL<N>` variants, the brief's `mechanic` per variant clearly states whether they're mode-specific or damage-tier variants — different visual escalation for each pattern

## Post-gen quick checks

- [ ] Reads as an obstacle, NOT a reward
- [ ] Visibly less saturated and less ornamented than even the LP symbols
- [ ] Could not be confused with any HP, MP, LP, or special symbol
- [ ] Theme-appropriate but feels broken / dead within that theme

## Anti-patterns

- ❌ Making the BL pretty or ornamented — players might think it pays
- ❌ Using warm / gold / saturated colors
- ❌ Making it more interesting than the LP symbols
- ❌ Adding any text label like "BLOCKER" — players don't read text on
  the reels; the visual must do the work

## Multiple BL variants — pick the pattern from the brief

### Pattern A: damage tiers (escalating clearable hits)

When `BL1` = clearable in 1 hit, `BL2` = 2 hits, etc., escalate the
"damage / cracks" visual:

- `BL1`: lightly weathered / surface cracks
- `BL2`: heavily weathered / partially shattered
- `BL3`: maximally damaged / barely holding together

Generate in escalation order so each can reference the prior; pass
the prior BL as `references`.

### Pattern B: mode-specific placeholders

When `BL1` is the bonus-mode placeholder and `BL2` is the base-boost
placeholder (Dodge pattern), each variant gets a subtle visual cue
tying it to its mode — e.g. `BL1` in a bonus-game color band,
`BL2` in a base-game color band — but both stay muted enough to read
as obstacles. The brief's per-variant `mechanic` says which mode each
belongs to.

### Choosing between patterns

If the brief's `mechanic` text describes hits / damage / clearing,
use Pattern A. If it describes "fills bonus reels" / "placeholder
in mode X" / "blank symbol", use Pattern B. When the brief is
ambiguous, ask the user before generating — these patterns produce
visibly different art.
