# Multiplier Badge Template

Multiplier badges are circular medallions that show during a win.
Different denominations get different metallic finishes to communicate
value at a glance.

## Surface rules

- **Shape:** circular medallion with sunburst behind the number
- **Background:** flat solid black, no gradients
- **Bevel:** highlight from upper-left
- **Minimum size:** 48×48 device px (state in prompt)

## Metallic finish per denomination

| Multiplier | Metallic finish |
|---|---|
| ×2, ×3 | bronze / copper |
| ×5, ×10 | silver / blue |
| ×15, ×25 | gold ornate |
| ×50+ | platinum / diamond |

## Prompt — multiplier badge

```
A "×<value>" multiplier badge for a mobile slot,
circular medallion with sunburst behind the number,
<tier_metallic> finish
(bronze for ×2–×3, silver for ×5–×10, gold for ×15–×25, platinum or diamond for ×50+),
thick outlined badge with bevel highlight from upper-left, <style_lock>,
centered on flat solid black background no gradients,
sharp clean edges.
```

## Pre-gen quick checks

- [ ] Value (×N) is in the prompt
- [ ] Metallic finish matches the denomination tier
- [ ] Background is `flat solid black background, no gradients`
- [ ] Bevel from upper-left stated

## Post-gen quick checks

- [ ] The number is clearly readable
- [ ] Metallic finish is distinguishable per tier (bronze ≠ silver ≠ gold ≠ platinum)
- [ ] Sunburst behind the number is visible but doesn't drown out the value
- [ ] Differentiable from jackpot medallions (jackpots have tier labels like "MAJOR"; multipliers have ×N)

## Generating a series

When asked for "all multipliers used in this game," check `brief` for the
denomination set. Generate in ascending order (×2 → ×100), passing each
prior badge as a reference so the metallic progression reads consistently.
Save as `Multiplier_x2_NNN.png`, `Multiplier_x5_NNN.png`, etc.
