# Vision Bridges — Closing the Animator Gap

Earlier iterations of this skill declared mesh vertex placement, expression compositing, weight binding, IK target tuning, and visual QA as "animator-only" work — things that require eyes on pixels and creative judgment. That framing was honest but incomplete. **Claude has vision.** Some of those "eyes on pixels" tasks decompose into *pattern recognition (vision)* plus *deterministic algorithm (Python + Pillow + OpenCV)*. The skill bundles helper tools and reviewed opt-in mesh/weight automation, but first-pass automation is not the same as final production weight painting or art-direction approval.

This file documents what each bridge does, what algorithm sits behind it, what's verified against the official Spine documentation, and where genuine human judgment still lives.

## Bridge 1: Mesh hull tracing — `scripts/trace_mesh_hull.py`

**What it does.** Given a PNG layer's alpha channel, produces a vertex list approximating Spine Editor's Trace tool.

**Algorithm** (verified against the Spine team's "Mesh creation tips: vertex placement" blog):

1. Alpha-threshold the image to a binary mask (Spine's "Alpha threshold" parameter).
2. Extract the outer contour with OpenCV `findContours` (RETR_EXTERNAL — Spine meshes cannot have holes; the Spine docs are explicit: "Meshes can be concave but cannot have holes.").
3. Optionally dilate by `padding` pixels (Spine's "Padding" parameter — pushes the hull outward so the mesh doesn't clip visible art).
4. Simplify the contour with Douglas-Peucker (`cv2.approxPolyDP`) via binary search on epsilon to hit the requested vertex count (Spine's "Detail" parameter, inverted: higher detail = more vertices).
5. Convert from doc-relative pixel coords to mesh-local coords (with PSD → Spine Y-flip).

**Spine team's principles that this respects:**

- "Always start with the least number of vertices possible." The default `--target-vertices 12` is the minimum that produces a usable hull for a typical slot symbol body.
- "To create the outer hull of a mesh, start from a corner in the image and place as few vertices as possible to approximate the general outline." Douglas-Peucker with a moderate epsilon does exactly this.
- "Mesh hull cuts off non-transparent pixels with aliasing unless MSAA is on." The padding parameter softens this by pushing the hull outward by a configurable margin.

**What remains an animator's call.**

The tracer produces the hull. Reviewed mesh plans and the `--auto-mesh-plan` draft path can wire that hull into `shared_symbols.json` as a mesh attachment, but **interior vertex placement** — where to add vertices that isolate features (nose, eyes, joints, fold lines) — is still a creative decision. The Spine docs say: "outline features with vertices: start by outlining each feature of the face — nose, eyes, eyebrows, mouth, etc. — by placing at least one vertex on each side of every feature." For symbol bodies that aren't faces, the equivalent is placing vertices at joints / bend points the artist intends to animate. The automatic draft adds conservative role-specific interior vertices for review; it does not know every feature the artist may want.

A future iteration could add a Claude-vision step: "look at this hull plus the source PNG; where are the natural fold lines?" The answer becomes interior vertices to add.

## Bridge 2: Expression compositing — `scripts/composite_expression_heads.py`

**What it does.** Pre-bakes expression overlays into full-canvas head attachments to eliminate the WebGL overlay-alpha-matte seam documented in [references/pitfalls.md](pitfalls.md#overlay-alpha-matte-seam).

**Algorithm.** Pure Pillow alpha-compositing — no vision needed once the overlays exist:

```
head_neutral      = head.png                     (as-is)
head_blink        = head.png + eyes_blink.png    (composited via alpha_composite)
head_laugh        = head.png + laugh.png         (composited via alpha_composite)
head_mouth_open   = head.png + mouth_open.png    (only when source layer exists)
head_mouth_closed = head.png + mouth_closed.png  (only when source layer exists)
head_side_eye     = head.png + side_eye.png      (only when source layer exists)
```

At animate time, the head slot's attachment timeline switches between the available composited head attachments. WebGL renders one image per frame; there's no live overlay layer over a base head, so the hard alpha matte never produces a visible boundary against the base head's pixels.

**Cost trade.** Approximately 3x the head's pixel data in the atlas (4 pre-baked head attachments instead of 1 head + 3 overlay slots). For production quality on character HP symbols this is worth it. The bundled `--composite-expressions` flag triggers the bake at compile time and the animation composer drives the resulting head-attachment-swap timeline.

**Status.** Structurally supported behind `--composite-expressions` with deterministic PNG integration checks and preview metadata. Spine Player preview and artist review are still required before final facial acting approval.

**What remains an animator's call.** Whether to use this at all — it's a quality/cost trade. The stepped attachment timeline approach (overlay slot toggled on/off) is cheaper and works for most slot symbols; the pre-composited approach is what to reach for when the seam shows in the final live preview.

## Bridge 3: Auto weight binding — `scripts/auto_bind_weights.py`

**What it does.** Computes first-pass per-vertex bone weights for a mesh given a set of bones. It uses projection, endpoint locks, triangle-neighbor smoothing, and prune; it is not Spine Editor `Auto` parity.

**Algorithm** (informed by the Spine team's "Mesh weight workflows" blog and the official `Weights view` doc):

1. **Project along the bone chain.** For each vertex, estimate where it sits between allowed bones on the mesh's main axis, so endpoints can lock cleanly to their nearest controlling bones.
2. **Seed local influence.** Blend axis projection with local distance so nearby bones still dominate vertices around their control area.
3. **Normalize.** Per-vertex weights sum to 1.0 (Spine guarantees this).
4. **Smooth** (multiple iterations). Average each vertex's weights with its triangle neighbors. The Spine docs call out smoothing as the key operation that "spreads the weight of bones and can result in smoother deformations." Repeat `--smooth-iterations` times (default 2).
5. **Prune.** Cap each vertex to top-N bones (default 2). Drop weights below threshold (default 0.05). Renormalize. The docs note: "Prune removes weights below a threshold... limit the number of bones that can affect a vertex" — this both improves performance and matches Spine's emission shape.
6. **Emit in Spine's weighted-vertex format.** The flat array `[bone_count, bone_idx, bind_x, bind_y, weight, ...]` per vertex, concatenated. Spine's runtime detects weighted meshes by `vertices.length > 2 * uv_count`.

**Spine team's principles that this respects:**

- "Start from extremes — vertices on the extreme opposite ends get 100% weight to one bone." Endpoint locks enforce this for the first-pass mesh review animation.
- "Spine will automatically calculate weights for you based on the surrounding vertices." Smoothing iterations are the realization.
- "Prune unnecessary weights." Top-N + threshold is the explicit prune step.
- "Use weights instead of deform keys." The skill emits weights; it never emits deform keys.

**Comparison to Spine's actual algorithm.** Spine's docs describe their auto-weights as using "mesh topography" — geodesic distance on the mesh surface, not raw euclidean distance. The bundled approximation uses available triangle adjacency and bone-axis projection as a deterministic first pass. For complex character meshes (a torso with an arm tucked behind it), Spine Editor's Auto plus direct painting can produce better weights. Final tuning still happens in Spine Editor with `Smooth` / `Prune` / direct paint.

**Smoke test.** A 9-vertex grid with 2 bones at the top and bottom produces sensible monotonic weight gradients (top vertices favor the top bone, bottom vertices favor the bottom, middle row is balanced). Package emission is opt-in with `--mesh-plan --auto-bind-weights` or `--auto-mesh-plan --auto-bind-weights` and remains review-required.

## Bridge 4: Vision-driven QA — `scripts/render_preview_frames.py`

**What it does.** Renders deterministic PNG snapshots of the rig at the setup pose, intended for Claude to *look at* (vision) and for the artist to scrub.

**Algorithm.**

1. Parse the atlas to map region names → atlas (x, y, width, height).
2. Walk the bone tree top-down to compute world positions.
3. Walk slots in draw order; for each slot:
   - Check the setup color's alpha — if < 0.01 (hidden-at-rest overlay), skip.
   - Crop the atlas region.
   - Composite at the slot's bone world position, centered.

**The vision-driven QA loop.**

After rendering, Claude looks at the setup PNG and asks:

- Is the rig centered, or off in a corner?
- Are the eyes-blink and laugh overlays hidden, or visible at rest?
- Is the hat above the head, or behind the frame?
- Are there any visible seams, halos, or transparent rectangles where art should be?

If Claude sees an issue, the next step is a diagnostic question: is the issue in the package (compiler fix needed) or in the render script (the render is a triage tool, not authoritative)? The way to disambiguate is the same way an animator does — open the Spine Web Player preview HTML. If the WebGL render looks correct, the issue is in the render script; if WebGL looks wrong too, the package has a bug.

**Honest limitation.** The bundled render is a simple approximation. It does **not** apply full Spine matrix composition (parent-to-child rotation cascades, scale propagation, IK / transform / path constraint resolution). For animation playback, the Spine Web Player remains authoritative. The bundled render is intended for setup-pose triage and offline review, not for replacing the live player.

Future iteration could add: full bone matrix composition matching the Spine Web Player's algorithm, frame extraction at multiple times of each animation, motion APNG rendering. Each is a straightforward extension of the existing parent-walk loop.

## Bridge 5: IK target keyframes from a reference image (planned)

**What it would do.** When the user supplies a reference image marked with "the hand should land here on frame N," Claude reads the position and emits IK target translate keyframes.

**Status.** Documented but not yet bundled as a script. The current pattern: Claude looks at the user's reference image, computes target translate keys for each beat, and outputs them as a JSON snippet the animator can paste into the win animation's `transform` block. A future iteration would automate this into `scripts/animate_ik_target.py`.

## What still genuinely requires human review

These things remain outside what vision + algorithms can automate or what the current builder emits:

- **Production Spine CLI export and licensing.** This is a contractual / runtime-version gate, not a technical one. Even if the JSON is perfect, production export requires Spine CLI + license approval + runtime acceptance tests.
- **Persistent avatar state across spins.** This is game code, not Spine data. The skill emits the state graph; the game's runtime decides when to transition between states based on player actions.
- **Final visual approval.** Art direction is a creative judgment about whether the result matches the intended feel. Even with a clean package, the art lead makes the "ship it" call.
- **Production mesh and weight emission.** Reviewed mesh-plan emission and first-pass auto binding are proof outputs. Final production meshes and weights still require animator review and weight painting in Spine Editor.
- **Bezier curve emission and complex multi-skin authoring.** `spine_43_bezier` is available only as an opt-in profile for supported numeric bone/slot timelines. Broader Bezier coverage, linked meshes, and complex skin-specific constraints are not implemented. Reviewed multi-skin region variants are available only through `--skin-plan`.

Layer interpretation, rig layout, animation composition, atlas packing, opt-in IK/transform/clipping/events/physics, mesh hull tracing, expression compositing, auto weight binding, and setup-pose QA are bundled at different readiness levels. Check `capability_status.md` before claiming a feature is production-ready.

## How Claude should use this when invoked

Claude can SEE images via the Read tool. When working through the pipeline:

1. **Before classifying a folder of layers** — read each PNG (or the manifest's preview composite) and confirm the semantic roles match what the names suggest.
2. **After running `--render-qa-frames`** — read `<out_dir>/qa/setup.png` and verify the rig looks correct. If something looks wrong, list the visible issues and propose a fix.
3. **When the user supplies a reference image** — read it and translate visible positions / motions into bounded controls or IK target keys.
4. **When `--composite-expressions` ran** — read the composited heads to confirm the expressions look right (the blink head should have closed eyes; the laugh head should have an open mouth).

The vision capability is the unlock. The deterministic algorithms are the leverage. Together, they close the gap between "an artist with eyes and judgment" and "a portable pipeline that ships."

## References

- [Spine: Meshes documentation](http://en.esotericsoftware.com/spine-meshes) — Trace algorithm parameters, hull rules, deformation, linked meshes.
- [Spine: Weights view](http://en.esotericsoftware.com/spine-weights) — Auto weighting, Smooth, Prune, brushes.
- [Spine blog: Mesh creation tips — vertex placement](https://esotericsoftware.com/blog/Mesh-creation-tips-vertex-placement) — Natural folds, hull principles, harmonious symmetric structures.
- [Spine blog: Mesh weight workflows](http://esotericsoftware.com/blog/Mesh-weight-workflows) — Start from extremes, group weights, parent-first hierarchy, deform-keys-are-the-devil.
- [references/pitfalls.md](pitfalls.md) — The overlay alpha-matte seam (which the expression compositor fixes).
