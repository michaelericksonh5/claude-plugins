# Pitfalls and Common Errors

The errors a slot-animation pipeline trips on most often, with the cause and the fix for each. Use this as the first lookup when the user reports a broken preview, a runtime error, a visual artifact, or an unexpected outcome.

## The error → cause → fix table

| Error / symptom | Cause | Fix |
|---|---|---|
| Live Spine canvas blank, no console error | `skins` emitted as 3.8 object form | Emit array form (`references/spine_42_contract.md#skins-array-form-in-4x`) |
| Live Spine animation has no rotation | Rotate keys use `angle` instead of `value` | Emit `value` (`references/spine_42_contract.md#bones-and-bone-timelines`) |
| Live Spine eye-blink overlay always visible / closed at rest | Overlay slot setup `color` not set to `ffffff00` | Set overlay slot setup color to `ffffff00`; use stepped attachment timeline during action (`references/spine_42_contract.md#overlay-polarity-critical-for-character-symbols`) |
| Live Spine mouth permanently in "O" | Mouth/laugh overlay slot setup color not `ffffff00` | Same as above |
| Live Spine player console: `Cannot read properties of null (reading 'r')` | `rgba2` emitted without setup `dark` color | Remove `rgba2` or add slot `dark` (`references/spine_42_contract.md#two-color-timelines`) |
| Page scrolls to 75,000 px tall | `#player` container uses aspect-ratio + grid auto-tracks, interacts with player's `height: 100%` | Set `#player` to fixed pixel `height: 480px` and `display: block` |
| Symbol off-center, very small | `skeleton.width/height` set to atlas page size | Use PSD document size (`references/spine_43_contract.md#current-required-shape`) |
| Live Spine player CORS errors on `file://` URLs | Browser blocks XHR for local files | Use HTTP server (`python -m http.server`) or embed assets as `rawDataURIs` |
| APNG looks correct, live Spine looks wrong | Compiler emitted legacy field names; APNG parser accepts both, current Spine Player only reads current 4.x data | Audit field names against `references/spine_43_contract.md` |
| Picasso: parts scattered off-center at rest | Bone setup x/y written as doc-absolute instead of parent-local | Subtract parent's doc-relative position (`references/intake.md#parent-local-bone-placement-critical`) |
| Picasso during animation only, rest pose correct | Animation translate/rotate keys written as absolute values instead of deltas | Emit deltas (`references/spine_43_contract.md#current-required-shape`) |
| Black or grey rectangle appears behind symbol | PSD-default `Background` / `Layer N` layers compiled as real parts | Filter boilerplate at intake (`references/intake.md#boilerplate-filtering`) |
| APNG previews show parts detached / jittery | APNG renderer treats translate/rotate as absolute instead of additive to setup | Apply deltas on top of setup pose in the renderer |
| Hat seam where white fur meets forehead | `*_hat_top` overlay duplicates art baked into `*_head`; both layers draw the same hat in WebGL | Graded duplicate-art erase at compile time (see "duplicate-art overlay rule" below) |
| Hat positioned behind frame | `*_hat_top` overlay dropped from rig; only the head's baked-in hat draws, behind the frame | Keep the overlay (it draws AFTER the frame in z-order); erase the head's duplicate pixels only |
| Rectangular halo around eyes during blink | Hard alpha matte on overlay layer rendered at high resolution | Stepped attachment timeline (see "overlay alpha matte seam" below) |
| Spine version string is `3.8.x` or otherwise mismatched in a current H5G package | Old `SPINE_VERSION` constant or CLI `-u` target in compiler/handoff script | Set the package target to `"4.3.04"` and regenerate the `.spine` project with the matching Spine CLI |
| Generated symbol mechanical-looking even though every part has motion | Per-part animations, not shared timeline | Compose all parts on one shared timeline (`references/spine_42_contract.md#shared-timeline-composition-rule`) |
| Region halo / colored bleed at edges in WebGL | Transparent atlas pixels carry garbage RGB; WebGL bilinear samples them | RGB-bleed transparent pixels at compile time; 1-px edge extrusion in atlas |
| Pixel stair-stepping during animation | Atlas `filter: Nearest,Nearest` instead of Linear | Use `filter: Linear,Linear` |
| Validation checker complains about every field | Running the current 4.x checker on a v10_linear (3.8) package | Use the right gate for the profile (`references/validation.md`) |

## Overlay alpha matte seam

**Symptom:** In the live Spine Web Player, a thin visible line appears at the edge of expression overlays (eye-blink rectangle, mouth-O bottom edge, hat-top bottom edge). The deterministic APNG renders the same source data without this seam.

**Cause:** The overlay layers' alpha channels are roughly rectangular hard-edged mattes. When the Spine Web Player renders the overlay at native device pixel ratio (~1200 px), WebGL's bilinear filter preserves the hard alpha boundary, and the boundary is visible against the underlying head's pixels.

The APNG renderer composites at the same native resolution but then LANCZOS-downscales the final frame to ≤720 px before writing. LANCZOS averages the matte boundary into the surrounding pixels and visually hides it.

This is NOT a rendering bug — both renderers correctly render the same source pixels.

**Failed fix (don't try):** Gaussian-blur the overlay's alpha channel in the atlas PNG, softening the matte boundary. This kills the Spine seam, but in the APNG renderer the feathered overlay alpha now allows the head's open-eye pixels to partially show through the closed-eye overlay during the blink, producing visible ghosting (double-vision). Both renderers eat the same atlas; an atlas-pixel hack that softens the Spine boundary equally softens the APNG, and the APNG was already clean.

**The clean fix (deferred / production-only):** Pre-composite each expression state into a full-head attachment. Generate `head_with_blink`, `head_with_laugh`, `head_with_hat` as separate full-canvas region attachments. The animation swaps the HEAD slot's attachment between these instead of layering an overlay on top of a base head. WebGL renders one image per frame; no runtime overlay compositing means no overlay edge to seam.

Cost: ~3× the head's pixel data in the atlas. Worth it for production quality.

**Interim mitigation:** Stepped attachment timelines for expression overlays (see `references/spine_42_contract.md#slots-and-slot-timelines`) keep the overlay either fully drawn or not drawn; no partial-alpha boundary appears during the action. The hard-edge seam still exists *while* the overlay is drawn, but it's brief enough that most viewers don't see it.

## WebGL vs APNG rendering differences

WebGL renders with bilinear texture sampling at native DPR. Pillow's APNG renderer composites at integer-pixel precision then LANCZOS-downsamples. Subtle differences:

| Aspect | WebGL | Pillow APNG |
|---|---|---|
| Resolution | Native DPR, ~1200 px in a 480px CSS-sized card | Composites at world bounds (~180px), upscales to 720px max via LANCZOS |
| Filtering | Bilinear texture sample | Integer paste + alpha_composite |
| Anti-aliasing of hard edges | Preserves | LANCZOS softens during downscale |
| Sub-pixel transforms | Native | Quantized to integer pixels |

**Diagnostic rule:** When the APNG looks clean and Spine doesn't, the seam is real and is in the source pixels. When Spine looks clean and the APNG doesn't, the APNG renderer has a bug — usually treating an animation delta as absolute, or sampling the wrong field name.

## Blend modes are stripped

PSD layers often use additive blend modes (LINEARDODGE, Screen, etc.) for sheen and glow layers. Spine supports `additive` / `multiply` / `screen` slot blend modes, and the live player will render them faithfully.

**However**, the H5G contract strips non-normal blend modes at compile time. Reason: at full resolution, an additive sheen layer over a colored body becomes much brighter than the artist's Photoshop thumbnail suggests, producing a runaway halo effect that art rejected.

The compiled output emits `blend: normal` for every slot, even when the source PSD used additive blending. Reactivating additive requires an explicit art-direction decision and visual review against the original thumbnail.

If the user asks why their sheen layer doesn't shimmer as brightly as the Photoshop thumbnail, this is why. Explain the contract; don't quietly re-enable additive.

## Duplicate-art overlay rule

**Symptom:** A `*_hat_top` overlay layer on top of a `*_head` layer that already shows the full hat creates a visible seam where the overlay's soft alpha edge meets the head's hat pixels.

**Cause:** Both layers draw the same hat in WebGL. The overlay's anti-aliased outer edge against the head's hat outline creates an alpha-doubled boundary line.

**Fix:** At compile time, detect such overlays (layers named `*_hat_top`, `*_cap_top`, `*_crown_top`, `*_helmet_top` whose parent is `head`), compute the overlap region in image space, and erase the parent's pixels where the overlay covers them. The overlay becomes the sole source of art in its region. Apply this as a graded erase (parent alpha *= 1 − overlay alpha) so the boundary stays smooth across the overlay's soft edge.

**Don't apply this to hidden expression overlays.** Erasing the head's open-eye pixels would leave a hole when the blink overlay is hidden. The duplicate-art rule applies only to always-visible accessory overlays where the parent's baked-in art is redundant.

## PSD smart-object rasterisation differences

When reading PSDs directly via `psd-tools`, smart-object layers are rasterised by `psd-tools`' own renderer, which may produce slightly different pixels than Photoshop's native renderer (which the JSX export uses). At the pixel level, these are different — typically tiny differences in soft alpha edges from sub-pixel resampling. End-to-end the visual result is equivalent (no human-visible difference in the compiled Spine output).

**Don't use exact pixel diff between PSD-native and JSX exports as a quality metric.** Use visual review.

## Path validation gotchas

The current Spine Player needs:

- Atlas page filename matches actual PNG filename.
- Every attachment `path` matches an atlas region name.
- The PNG referenced by the atlas exists and is readable.

If the package fails to load and the console says "region not found", run the compatibility/import-version gates — they enumerate exactly which attachment references which missing region.

## When a user reports something not in this table

1. Reproduce: get the exact error message or describe the visual artifact precisely.
2. Run the compatibility/import-version gates for current packages — most issues come from contract violations or editor-version mismatches.
3. Inspect `validation_report.json` for compiler-side complaints.
4. Inspect `preview_validation_report.json` for preview-side complaints.
5. Open the APNG and the live preview side by side — divergence between the two is itself a diagnostic.

If none of those surface the problem, the issue may be in the source PSD or in a pipeline stage upstream of compile. Ask the user to share the relevant validation reports verbatim before guessing.
