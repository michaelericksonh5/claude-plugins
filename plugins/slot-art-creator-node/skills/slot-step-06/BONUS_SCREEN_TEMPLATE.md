# Bonus Screen Templates

Bonus screens are full-canvas frames for non-base-game modes — free spins
intro, pick-me bonus, wheel bonus. They take more visual liberty than the
base game (no reel grid, more saturation, more drama).

## Universal bonus screen rules

- More saturation, more drama than the base game
- Stronger vignette than the base game
- No reel grid (this isn't a base-game frame)
- Theme-relevant decorative elements bigger and more prominent
- Aspect ratio: portrait `9:16` for mobile (passed via API arg)

---

## Free-spins intro

The screen players see when free spins trigger. Title, spin count, START button.

```
A free-spins intro screen for a <theme_summary>-themed mobile slot, <style_lock>,
title text "FREE SPINS" in the upper third in premium gold-and-themed lettering,
large empty space in the center for the spin count numeral,
START button at the bottom as the brightest CTA,
richer saturation than the base game with stronger vignette and warm overlays,
<palette_leads.primary> palette intensified,
mobile portrait composition,
no reels, no symbols, only the bonus chrome.
```

### Free-spins quick checks

- [ ] Title in upper third
- [ ] Empty space in center for runtime spin count
- [ ] START button is the brightest CTA
- [ ] No reels / symbols
- [ ] More saturated than the base game background

---

## Pick-me bonus

Player picks one of N hidden objects. 80×80 dp minimum touch targets.

```
A pick-me bonus screen for a <theme_summary>-themed mobile slot, <style_lock>,
a 3×2 grid of large interactive themed objects with clear unrevealed
pickable styling,
full-screen themed background more saturated than the base game,
each pickable object visually distinct from background decoration,
large enough to thumb-tap easily,
<palette_leads.primary> palette,
portrait composition,
no text labels on the pickable objects.
```

### Pick-me quick checks

- [ ] Grid count matches the brief (commonly 3×2 = 6 picks, 4×2 = 8 picks)
- [ ] Pickable objects are visually distinct from decoration
- [ ] Touch targets are visually generous
- [ ] No text labels on the pickables (they reveal at runtime)

---

## Wheel bonus

Circular bonus wheel with N segments and a pointer.

```
A bonus wheel screen for a <theme_summary>-themed mobile slot, <style_lock>,
a circular wheel with <segment_count> evenly-divided wedges,
wedges colored in a cool-to-hot pay-tier gradient ending in
<palette_leads.primary> gold for the jackpot segment,
pegs evenly placed around the rim, pointer at the 12 o'clock top position,
<theme_summary> themed background,
no value text on the wedges (runtime adds it).
```

### Wheel quick checks

- [ ] Segment count matches the brief (commonly 8, 12, or 16)
- [ ] Cool-to-hot gradient — lowest tier coolest, jackpot segment warmest gold
- [ ] Pegs around the rim
- [ ] Pointer at 12 o'clock (top)
- [ ] No value text on wedges
