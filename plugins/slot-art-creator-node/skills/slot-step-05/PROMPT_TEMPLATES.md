# Background Designer — Prompt Templates

## Base game (9:16 portrait — default)

```
A mobile slot game background, <theme_summary> environment, <style_lock>,
three-layer depth composition — foreground crop framing in the lower
corners and edges, midground story scene at mid-height, distant sky/horizon
at top for atmospheric perspective,
upper-left key light at 10 o'clock,
<palette_leads.primary> palette with <palette_leads.accents> accents,
overall darker tonality through the lower third of the canvas to support
overlaid UI controls — natural shadow falloff, not a hard band,
balanced naturalistic lighting across the rest of the scene — no special
central treatment, no painted shadow zone, no dark patch in the middle,
no dark oval, no dimmed reel area drawn into the scene (the game engine
applies reel-zone dimming at runtime — the background must be a coherent
naturally-lit painting),
corners gently darker than center for a soft vignette,
mostly mid-dark values with small bright accents in the upper midground,
no UI mockup, no reels, no paylines, no spin buttons, no HUD, no text,
no vertical bars, no panels, no rectangular reel frames painted into the scene,
no architectural columns standing in the center of the canvas,
not photorealistic, professional slot game art, mobile slot background.
```

## Free-spins variant

```
A mobile slot game free spins background based on the base game's
<theme_summary> environment, <style_lock>,
same composition and key elements as the base game but graded with a warm overlay,
hue rotated slightly toward warm, saturation increased by roughly fifteen percent,
stronger vignette than the base game with corners darker,
overall darker tonality through the lower third for UI overlay,
balanced naturalistic lighting across the rest of the scene — no special
central treatment, no painted shadow zone, no dark patch in the middle,
no dark oval, no dimmed reel area drawn into the scene,
three-layer depth composition (foreground / midground / distant background) intact,
<palette_leads.primary> palette intensified with extra warm accents,
upper-left key light at 10 o'clock,
no UI mockup, no reels, no paylines, no text, no vertical bars or panels,
no architectural columns standing in the center,
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

1. **Bottom third stays darker** — natural shadow falloff through the lower portion for UI overlay. NOT a hard horizontal band painted into the scene.
2. **DO NOT paint reel-zone darkening into the background.** The reel zone is dimmed by the **game engine at runtime** (a dimming overlay rectangle applied below the symbols). The background art must be a coherent naturally-lit painting with NO special central treatment. Past mistakes that produced bezel/oval artifacts: "center column dimmed", "soft elliptical atmospheric darkening through the vertical middle", "diffuse shadow where the reels will overlay" — **all of these phrases caused Gemini to paint a visible dark patch in the center.** Never describe a central shadow, dim zone, dark oval, dark column, dark panel, or anything similar. Just don't mention the reel zone.
3. **Three-layer depth** — foreground / midground / distant background. Depth via overlap and atmospheric perspective, NOT vertical or horizontal panels.
4. **Vignette** — corners gently darker than center. This is the only intentional darkening allowed (besides the natural bottom-third falloff).

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
| `base` | L* 10–30, cool-leaning | 20–40% darker corners | None — engine handles at runtime | Default |
| `free-spins` | +10–20% warmer | Stronger | None — engine handles at runtime | Hue rotate 20–40° warm |
| `bonus` | Maximum | Strongest | Relaxed | Full center allowed |
| `pickme` | High | Strong | Not needed | Calm central zone for picks |
| `wheel` | High | Strong | Not needed | Calm circular zone for wheel |
