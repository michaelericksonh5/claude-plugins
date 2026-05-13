# HUD Chrome Template

The HUD is the bottom strip on a portrait phone screen — spin button,
balance, bet, win display, multiplier indicator. Spin button is the
single dominant CTA. Everything else is secondary.

## Surface rules

- **Spin button:** the dominant CTA — circular primary, 80–120 pt diameter
- **All controls:** at least 44 pt minimum touch target
- **Panels:** transparent dark, 40–70% opacity with slight blur
- **Color conventions:**
  - Balance: white / silver
  - Bet: white or amber
  - Win: gold / yellow
  - Multiplier: gold / orange
- **Background:** flat dark themed panel (not the full game background — this is just the HUD strip)

## Prompt — HUD chrome

```
A mobile slot game HUD bar for the bottom of a portrait phone screen,
<theme_summary>-themed, <style_lock>,
transparent dark panel at moderate opacity with slight blur, thin or no borders,
spin button as a circular primary CTA at the center,
larger than all other controls, breaks the bar vertically,
smaller stepper buttons for bet adjustment to one side,
balance display in white, win display in warm gold,
<palette_leads.primary> palette,
no reels above, no symbols, only the HUD strip.
```

## Pre-gen quick checks

- [ ] Spin button described as the single dominant CTA
- [ ] Touch target language present ("at least 44 pt", "circular primary CTA at the center")
- [ ] Color conventions match: balance=white, bet=white/amber, win=gold/yellow
- [ ] Transparent panel with blur stated
- [ ] No symbols or reels in the HUD

## Post-gen quick checks

- [ ] Spin button is unmistakably the dominant element
- [ ] Stepper buttons are visibly secondary
- [ ] Panel reads as semi-transparent (a darker game BG would show through)
- [ ] Win display is gold/yellow (not white or generic)
- [ ] Touch targets look generously sized
