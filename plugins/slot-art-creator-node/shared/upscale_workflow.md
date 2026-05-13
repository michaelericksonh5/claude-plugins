# NB2 Upscaling — Path A (vision-LLM in the loop)

This is the proven workflow for upscaling slot art from ~1K to 4K **without
repainting it**. NB2 has a strong bias toward regenerating rather than
upscaling an input image. The whole battle is prompting it out of regenerate
mode.

Path A puts a vision-capable LLM in the loop: it inspects the source, writes
a bespoke preservation prompt, sends to NB2, reviews the output against an
8-axis rubric, and iterates. This is the only approach in our experience that
reliably preserves identity-heavy assets.

---

## The loop

```
1. Source image
2. Vision-LLM inspects → builds a concrete visual inventory
3. Vision-LLM writes a bespoke prompt using the 6-part template
4. NB2 generates a 4K upscale
5. Vision-LLM reviews against the 8-axis rubric
   ├── pass → ship it
   └── fail → diagnose drift, patch the prompt, return to step 4
```

---

## Step 2: Visual inventory

Before any prompt is written, enumerate these from the source image.
Vague inventory → vague prompt → drifted upscale.

| Category | What to capture | Why |
|---|---|---|
| **Subject identity** | "green translucent gummy bear", "Día de los Muertos marigold flower" | Anchors NB2 against subject swap. |
| **Pose / composition** | "front-facing, arms at sides, sitting on haunches" | Prevents pose drift. |
| **Silhouette / proportions** | "chubby round body, short limbs, oversized head" | Protects character identity. |
| **Rendering style** | "stylized 3D illustration, NOT photoreal" / "flat vector" / "painterly digital art" | **Single most important bullet.** Without this NB2 photorealizes everything. |
| **Material(s)** | "translucent gummy candy"; "glossy varnished wood with teal folk-art scrollwork" | Concrete visual term, not abstract. |
| **Lighting** | "glossy spec on upper-left, soft internal subsurface glow" | NB2 re-lights the scene if you don't pin this. |
| **Color palette** | "lime green body, white highlights, magenta background" — **named colors only**, no hex | Named colors survive the round-trip; hex codes don't. |
| **Decorative elements** | "three petal clusters, two teal vine curls on the lower bout" | Otherwise NB2 simplifies or multiplies them. |
| **Background** | "soft cast shadow, otherwise flat magenta / solid white / transparent" | NB2 is opinionated about backgrounds; call it out. |
| **Framing** | "1:1 square, subject centered, ~80% of canvas" | Prevents crop or scale drift. |

---

## Step 3: The 6-part prompt template

Every working upscale prompt follows this exact structure.

```
1. Opening verb + task:
   "Upscale this image to 4K resolution. Preserve exactly:"

2. Bulleted preservation list (5–7 bullets, in this order):
   - pose / proportions / facial expression / silhouette
   - primary material (with concrete visual term)
   - lighting behavior (specular highlights, subsurface, shadows)
   - RENDERING STYLE (with explicit "NOT photorealistic" if stylized)
   - decorative / color details
   - background (named: "solid white", "flat magenta", "transparent")
   - [optional] framing / camera angle

3. One-sentence material restatement:
   "The subject is rendered in translucent gummy candy..."

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

### Worked example (gummy bear, the canonical winning prompt)

```
Upscale this image to 4K resolution. Preserve exactly:
- the subject's pose, proportions, facial expression, and silhouette
- the vibrant lime-green translucent gummy material
- the glossy specular highlights and internal subsurface glow
- the soft cast shadow and transparent background
Enhance only: edge sharpness, highlight crispness, subtle micro-surface
detail on the gummy (tiny air bubbles, faint sugar-dust sheen). Do NOT
add new objects, do NOT change colors, do NOT restyle. Maintain a clean
isolated asset suitable for a mobile slot symbol. 1:1 square canvas,
transparent background preserved.
```

---

## Step 5: The 8-axis review rubric

After NB2 returns the upscale, grade it on these axes. Any **FAIL** sends it
back to step 3 with a prompt patch.

| Axis | PASS looks like | FAIL looks like |
|---|---|---|
| **Identity match** | Same character/object, recognizable instantly. | Different character, different species, restyled toy. |
| **Pose / silhouette** | Same stance, outline within a few %. | Arms repositioned, head tilt changed, body reshaped. |
| **Rendering style** | Still stylized 3D / flat vector / painterly — whatever the source was. | Became photorealistic, became flatter, became painted when it was vector. |
| **Color palette** | Same named colors, same saturation band. | Lime → forest green; desaturated; warmer/cooler cast. |
| **Detail parity** | Same *amount* of detail — highlights/petals/bubbles roughly match. | Invented new highlights, added texture, multiplied decorative elements. |
| **Background** | Matches the prompt's background instruction exactly. | Transparent checkerboard leaked through; gradient appeared; scene added. |
| **Micro-quality** | Edges crisp, no aliasing, no jpeg artifacts, looks genuinely upscaled. | Blown up / pixelated, soft, or visibly re-rendered from text alone. |
| **Framing** | 1:1 square, subject at same scale and position. | Cropped, zoomed, re-framed, off-center. |

**Mental check:** "Would I notice the swap if the two images were placed
next to each other in a slot symbol carousel?" If yes — it failed.

### Diagnose → patch playbook

| Failure | Patch the prompt by… |
|---|---|
| Photorealized | Strengthen the rendering-style bullet ("**stylized 3D illustration, NOT photorealistic, NOT a real-world photograph**"). Add to negative constraints. |
| Color drift | Restate named colors twice — once in preservation list, once in the material restatement. Avoid hex codes. |
| Background changed | Move background bullet earlier in the preservation list and add to closing deliverable framing. |
| Subject swap | Lengthen identity description (species, key visual signature). Add "preserve subject identity exactly" as bullet 1. |
| Detail multiplied | Add explicit count to preservation ("three petal clusters — exactly three") and to negative constraints. |
| Pose drift | Describe pose in two ways (verbal + spatial: "left arm raised at 45°"). |
| Soft / pixelated | Add a concrete enhance-only item ("crisp edge sharpness, no anti-alias halos"). |

---

## When to use Path A vs simpler options

| Scenario | Use |
|---|---|
| Final hero art, approved symbols, customer-facing | **Path A** |
| Identity-heavy subject (faces, characters, mascots) | **Path A** |
| Bulk batches where small drift is acceptable (decorative props, BG details) | A planner-LLM shortcut is OK |
| Anything below 1K input | Re-author at higher resolution; don't upscale 512×512 art |

---

## Limitations (be honest with users)

- **Cost per image.** Each upscale is one NB2 call + however many vision-LLM
  reviews you do. Budget several cents per final image.
- **Stochastic.** Run N=4 of the winning prompt and pick the best.
- **Reviewer variance.** The template is what standardizes the result; the
  specific reviewer model matters less than following the template.
- **Human sanity check** is still recommended for hero assets — vision LLMs
  can miss subtle identity drift (eye placement, logo shapes).
