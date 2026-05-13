# Upscale prompt template

The 6-part structure. Claude fills it in per source image after the visual
inventory.

---

## Visual inventory checklist (do this BEFORE writing the prompt)

Look at the source image and answer all ten:

| # | Field | Example answer |
|---|---|---|
| 1 | **Subject identity** | "green translucent gummy bear" |
| 2 | **Pose / composition** | "front-facing, arms at sides, sitting on haunches" |
| 3 | **Silhouette / proportions** | "chubby round body, short limbs, oversized head" |
| 4 | **Rendering style** | "stylized 3D illustration, NOT photoreal" |
| 5 | **Material(s)** | "translucent gummy candy" |
| 6 | **Lighting** | "glossy spec on upper-left, soft internal subsurface glow" |
| 7 | **Color palette** | "lime green body, white highlights, magenta background" — NAMED colors only |
| 8 | **Decorative elements** | "three petal clusters, two teal vine curls on lower bout" |
| 9 | **Background** | "soft cast shadow, otherwise flat magenta" |
| 10 | **Framing** | "1:1 square, subject centered, ~80% of canvas" |

If you can't answer one, look harder before writing the prompt.

---

## The 6-part template

```
1. Opening verb + task:
   "Upscale this image to 4K resolution. Preserve exactly:"

2. Bulleted preservation list (5–7 bullets, IN THIS ORDER):
   - pose / proportions / facial expression / silhouette
   - primary material (with concrete visual term)
   - lighting behavior (specular highlights, subsurface, shadows)
   - RENDERING STYLE (with explicit "NOT photorealistic" if stylized)
   - decorative / color details
   - background (named: "solid white", "flat magenta", "transparent")
   - [optional] framing / camera angle

3. One-sentence material restatement:
   "The subject is rendered in <material>..."

4. Enhance-only allowance (2–4 items, tightly scoped):
   "Enhance only: edge sharpness, highlight crispness, subtle
    micro-surface detail (tiny air bubbles, faint sugar-dust sheen)."

5. Hard negative constraints:
   "Do NOT add new objects, do NOT change colors, do NOT restyle,
    do NOT photorealize."

6. Closing deliverable framing:
   "Maintain a clean isolated asset suitable for a mobile slot symbol.
    1:1 square canvas, solid white background."
```

---

## Worked example (the canonical winning prompt — gummy bear)

```
Upscale this image to 4K resolution. Preserve exactly:
- the subject's pose, proportions, facial expression, and silhouette
- the vibrant lime-green translucent gummy material
- the glossy specular highlights and internal subsurface glow
- the soft cast shadow and transparent background

The subject is rendered in translucent gummy candy with a soft internal
glow.

Enhance only: edge sharpness, highlight crispness, subtle micro-surface
detail on the gummy (tiny air bubbles, faint sugar-dust sheen).

Do NOT add new objects, do NOT change colors, do NOT restyle, do NOT
photorealize.

Maintain a clean isolated asset suitable for a mobile slot symbol.
1:1 square canvas, transparent background preserved.
```

---

## Worked example (slot HP character)

```
Upscale this image to 4K resolution. Preserve exactly:
- the phoenix character's pose, wing position, and head tilt
- the warm crimson plumage with antique gold rim lighting
- the soft inner-glow effect around the body and the cast shadow on the
  flat black background
- the stylized semi-realistic slot game art rendering, NOT photorealistic
- the three-tail-feather configuration and the gold beak detail

The subject is rendered as a stylized semi-realistic slot game character,
warm-leaning palette, soft inner rim glow.

Enhance only: edge sharpness on the wing feathers, highlight crispness
on the beak and gold accents, subtle micro-surface detail on the
plumage (faint individual feather suggestion at the silhouette edge).

Do NOT add new objects, do NOT add stars or particles, do NOT change
the palette, do NOT restyle, do NOT photorealize.

Maintain a clean isolated slot symbol asset. 1:1 square canvas, flat
solid black background preserved, no gradients.
```
