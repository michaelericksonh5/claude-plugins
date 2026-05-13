# Background Designer — Prompt Templates

## Base game (9:16 portrait — default)

```
A mobile slot game background, <theme_summary> environment, <style_lock>,
three-layer composition with foreground crop framing, midground story scene,
and distant sky for atmospheric perspective,
upper-left key light at 10 o'clock,
<palette_leads.primary> palette with <palette_leads.accents> accents,
bottom third of the canvas darkest for UI controls — luminance drops
noticeably from the upper two thirds to the bottom third,
center column dimmed by roughly fifteen percent compared to surroundings
to serve as the reel zone,
corners about thirty percent darker than center for a soft vignette,
mostly mid-dark values with small bright accents in the upper midground,
no UI mockup, no reels, no paylines, no spin buttons, no HUD, no text,
not photorealistic, professional slot game art, mobile slot background.
```

## Free-spins variant

```
A mobile slot game free spins background based on the base game's
<theme_summary> environment, <style_lock>,
same composition and key elements as the base game but graded with a warm overlay,
hue rotated slightly toward warm, saturation increased by roughly fifteen percent,
stronger vignette than the base game with corners darker,
bottom third still dark for UI, reel zone still dimmed,
three-layer parallax-ready composition intact,
<palette_leads.primary> palette intensified with extra warm accents,
upper-left key light at 10 o'clock,
no UI mockup, no reels, no paylines, no text,
professional slot game art, mobile slot background.
```

## Bonus round variant

```
A mobile slot game bonus round background, <theme_summary> environment
intensified for the bonus moment, <style_lock>,
richer saturation and more drama than the base game, stronger vignette,
darker edges, maximum warm accents,
no reel grid will be overlaid so the composition can be fuller and
more detailed in the center,
<palette_leads.primary> palette with intensified <palette_leads.accents> accents,
upper-left key light at 10 o'clock,
no UI mockup, no reels, no paylines, no text,
professional slot game art, mobile slot background.
```

## Pick-me bonus variant

```
A mobile slot game pick-me bonus background, <theme_summary> environment,
<style_lock>,
a full-screen themed scene with a clear central area where 6 to 8 pickable
objects will be overlaid — that center area is calmer and slightly darker
than its surroundings so the picks will read clearly,
no reel grid, richer saturation than the base game, stronger vignette,
<palette_leads.primary> palette intensified,
upper-left key light at 10 o'clock,
no UI mockup, no text, professional slot game art, mobile slot background.
```

## Wheel bonus variant

```
A mobile slot game wheel bonus background, <theme_summary> environment,
<style_lock>,
a full-screen themed backdrop with a clear central circular area where a
bonus wheel will be overlaid — that center area is calmer and slightly
darker than its surroundings so the wheel will read clearly,
no reel grid,
<palette_leads.primary> palette with intensified <palette_leads.accents> accents,
dramatic atmospheric lighting from the upper left,
no UI mockup, no text, professional slot game art, mobile slot background.
```

## Landscape (desktop/tablet)

```
[Use base game template. Do NOT mention any aspect ratio in the prompt
text — pass the landscape ratio via the `aspect_ratio` API arg.
Adjust composition only: three-layer composition with focal content
left-of-center or top-left, reel zone occupies center 60% of canvas,
bottom 20% (not 30%) reserved for controls.]
```

---

## The four hard rules (non-negotiable for base-game backgrounds)

1. **Bottom 30% stays dark** — luminance drops noticeably in the bottom third for UI controls.
2. **Reel zone is dimmed** — center column ~10–20% darker than surroundings.
3. **Three-layer composition** — foreground → midground → distant sky.
4. **Vignette** — corners 20–40% darker than center.

## What to push back on

| Request | Response |
|---|---|
| "Make the reels visible in the background" | No. Backgrounds never contain reels. |
| "Bright sky behind the reels" | Only with a 60–80% dark frosted panel between BG and reels. |
| "Center the hero in the BG" | No. The reel grid is center; put focal content to edges or top third. |
| "Photorealistic background" | Only if the entire game uses photorealism. |

## Variant comparison

| Variant | Saturation | Vignette | Reel zone | Notes |
|---|---|---|---|---|
| `base` | L* 10–30, cool-leaning | 20–40% darker corners | Dimmed ~15% | Default |
| `free-spins` | +10–20% warmer | Stronger | Still dimmed | Hue rotate 20–40° warm |
| `bonus` | Maximum | Strongest | Relaxed | Full center allowed |
| `pickme` | High | Strong | Not needed | Calm central zone for picks |
| `wheel` | High | Strong | Not needed | Calm circular zone for wheel |
