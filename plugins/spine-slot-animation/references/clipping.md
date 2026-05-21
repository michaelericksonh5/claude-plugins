# Clipping Attachments

A clipping attachment is a polygon that masks the rendering of region and mesh attachments beneath it. Slot animation rarely needs runtime clipping — most "show only inside the frame" effects can be done with alpha-baked-in art — but a few cases earn the complexity. This file covers when and how, with the cost trade-offs verified against the official Spine documentation.

## What clipping does

A clipping attachment defines a polygon. At runtime, the slots in draw order between the clipping attachment's slot and its `end slot` (inclusive) are rendered only inside the polygon's bounds. Anything outside is clipped.

Visually, this is identical to drawing a regular slot, then masking the result. Internally, it's not — Spine implements clipping on the CPU, not as a GPU stencil. This is the central performance fact about clipping.

## When to use clipping (and when not to)

### Use clipping for

- **A meter fill** that grows from 0% to 100% as the player progresses. The bar art is a fixed image; the clipping polygon is sized at runtime to reveal only the filled portion.
- **A transition wipe** that sweeps across the screen revealing the new scene. The transition art is the static "before" image; a sliding clipping polygon reveals the underlying "after" content.
- **A coin counter** where individual digit slots reveal as the count rolls over.
- **A scratch reveal** where the player drags to expose what's underneath.

The common signal: the *shape of what's visible* changes dynamically, frame to frame, in a way that can't be pre-baked into the source art.

### Don't use clipping for

- **A symbol that should appear inside its frame.** Bake the alpha into the symbol's art so transparent pixels show the frame underneath. No runtime cost.
- **A glow that fades softly past the frame's edge.** Same — alpha gradient in the source.
- **Static masking of a sub-region.** Crop the source asset to the visible region; don't pay for runtime clipping.
- **Per-symbol decorations.** If 30 symbols on screen each have a clipping attachment, that's 30 CPU clipping operations per frame. The fill-rate cost of just drawing the un-clipped art is almost always cheaper.

The official doc opens with a warning: *"Clipping can be a very expensive operation and should be used judiciously."* The skill carries the same default — clipping is gated behind `--enable-clipping` and never auto-applied.

## Performance — verified facts

From the official clipping doc:

1. **CPU, not GPU.** "Clipping in the Spine Runtimes is implemented using the CPU [and] can be a very expensive operation, especially when using mesh attachments with many vertices."
2. **Vertex count is the cost driver, not polygon size.** "The size of the clipping polygon does not affect performance."
3. **Minimum vertex count is 3** (a triangle). Use the minimum that produces the needed shape.
4. **Convex is cheaper than concave.** "Arranging the clipping attachment vertices so they are convex can greatly reduce the CPU usage needed to perform clipping. This is because the clipping attachment vertices are first decomposed into convex polygons, then each resulting polygon is checked against all the clipped region and mesh attachment vertices."
5. **Slot range matters.** "Set the start and end slots to clip the fewest number of attachments." A clipping attachment with `end slot` set tightly clips only one slot; left at default, it clips every slot above it in the draw order.
6. **Clipped-attachment vertex count matters.** "Reduce both the number of vertices in the clipping attachment and the total number of vertices in all the clipped region and mesh attachments." If you're clipping a 200-vertex mesh, every clip operation traverses those 200 vertices.
7. **Self-intersection breaks it.** "Clipping will not work correctly if the clipping attachment polygon self-intersects."

### Mental model for cost

For each clipped slot, each frame, the runtime:

1. Decomposes the clipping polygon into convex sub-polygons (skipped if already convex).
2. For each clipped attachment's triangles, tests each triangle against each convex clip sub-polygon.
3. Produces new triangles for the clipped result.

Cost scales roughly as `(clip vertices) × (clipped attachment vertices) × (number of clipped slots)`. Doubling each multiplies the cost by 8. Hence the docs' insistence on minimizing all three.

## JSON contract

Verified from the official Spine JSON format documentation.

### Top-level skin attachment

```json
"skins": [
  {
    "name": "default",
    "attachments": {
      "meter_clip_slot": {
        "meter_clip": {
          "type": "clipping",
          "end": "meter_fill_slot",
          "vertexCount": 4,
          "vertices": [0, 0, 100, 0, 100, 50, 0, 50],
          "color": "ce3a3aff"
        }
      }
    }
  }
]
```

Field rules:

- `type: "clipping"` — required to distinguish from region / mesh.
- `end` — name of the slot at which clipping stops (inclusive). Slots between the clip's slot and the end slot, in draw order, are clipped.
- `vertexCount` — the number of polygon vertices. For non-weighted clipping (the common case), `vertices.length == vertexCount * 2`. For weighted clipping (which lets bones deform the polygon), `vertices` has the weighted format described in the format spec.
- `vertices` — flat array of x,y pairs.
- `color` — debug color in the editor; runtime ignores it.

### Slot setup

The slot that holds the clipping attachment is a normal slot with `attachment` set to the clipping's name:

```json
"slots": [
  ...
  { "name": "meter_clip_slot", "bone": "meter_root_bone", "attachment": "meter_clip" },
  { "name": "meter_fill_slot", "bone": "meter_root_bone", "attachment": "parts/meter_fill" }
]
```

Slot order matters: the clipping slot must come **before** the slots it should clip in the draw order.

### Animation — deforming the clipping polygon

Clipping vertices can be keyed in animations via deform timelines, just like mesh vertices. The official doc on deform timelines covers the JSON shape; for clipping, the slot key is the clipping slot's name and the attachment key is the clipping attachment's name:

```json
"deform": {
  "default": {
    "meter_clip_slot": {
      "meter_clip": [
        { "time": 0, "vertices": [0, 0, 0, 0, 0, 0, 0, 0] },
        { "time": 1.0, "vertices": [0, 0, 100, 0, 100, 50, 0, 50] }
      ]
    }
  }
}
```

(The `vertices` array contains *offsets* from setup, not absolute positions. So a meter fill that grows from 0 to 100 over 1 second keys the right-side vertices' x-offsets from 0 to +100.)

Alternative: animate the bone the clipping attachment is parented to. If the clipping polygon is a fixed shape and you just need to slide/scale it, animate the bone — same effect, no deform timeline needed.

### Toggling clipping on/off in an animation

Show/hide the clipping attachment via the slot's attachment timeline. Setting `attachment: null` clears it; setting it back to the clipping name re-enables.

```json
"slots": {
  "meter_clip_slot": {
    "attachment": [
      { "time": 0, "name": null },
      { "time": 0.5, "name": "meter_clip" },
      { "time": 2.5, "name": null }
    ]
  }
}
```

## Patterns for slot animation

### Pattern: meter fill that grows

```
slots in draw order:
  meter_bg_slot          (background bar, always visible)
  meter_fill_slot        (fill color, always present but clipped)
  meter_clip_slot        (clipping polygon, sized to current fill amount)
  meter_frame_slot       (frame on top)
```

The clipping polygon is sized via deform timeline (or bone scale) to match the current state's fill amount. Each `State<N>Collect` animation keys the clip polygon's right edge from the previous state's position to the current state's position.

Cost: 1 clip op per frame, ~4 vertices on clip, ~4 vertices on the fill (region). Cheap.

### Pattern: transition wipe

```
slots in draw order:
  before_slot            (the "before" scene)
  wipe_clip_slot         (clipping polygon, sized to fill the whole screen at start)
  after_slot             (the "after" scene, clipped to inverted clip)
  wipe_clip_slot_2       (second clipping polygon for inverted region)
```

This is more complex because you need both halves visible during the transition. Practically: animate the clip polygon position to slide across the screen.

Cost: 1 clip op per frame, but the clipped slot is the entire `after` scene. If `after` is a static region, fine. If `after` is a complex multi-mesh scene, very expensive.

### Pattern: digit rollover

```
slots:
  digit_position_clip    (clipping window for one digit position)
  digit_strip            (long strip of all digits 0-9 stacked vertically)
```

The clipping window is sized to one digit's height. The strip is translated up/down to put the right digit inside the window. Classic mechanical-counter look.

Cost: low. 3- or 4-vertex clip, region attachment for the strip.

## What the skill can and can't do

| Capability | Bundled? |
|---|---|
| Emit clipping attachment JSON when user supplies polygon vertices | Yes (gated `--enable-clipping`) |
| Auto-detect candidates for clipping (meter fills, transitions) | No — user supplies the intent |
| Author the clip polygon shape | No — creative decision |
| Set the `end slot` correctly | Yes (user specifies in the plan; skill validates the slot exists) |
| Animate the clip polygon via deform keys | No — the skill follows its own "don't emit deform timelines" rule |
| Animate the clip polygon via bone motion | Yes (the clip bone is a normal bone, normal translate/scale keys work) |
| Validate polygon is non-self-intersecting | Yes — the skill's clipping emitter rejects self-intersecting input |
| Validate `end slot` exists and comes after the clip slot in draw order | Yes |

## Validation

The strict 4.x compatibility checks accept clipping attachments. The skill's emitter additionally validates (before writing JSON):

- `vertexCount >= 3`.
- `len(vertices) == 2 * vertexCount` for non-weighted clipping.
- `end` references a real slot that exists in the package.
- The clipping slot comes before the end slot in the draw order.
- The polygon edges don't self-intersect (the skill runs a simple segment-intersection check).

## The honest summary

For 95% of slot work, clipping isn't needed and shouldn't be reached for. Alpha-baked art is cheaper and looks identical. Reserve clipping for the four or five UI elements per game that genuinely need dynamic shape masking (meter fills, transition wipes, digit rollovers, scratch reveals).

When you do reach for it: keep the polygon convex, keep it under 8 vertices if you can, set the end slot tightly, and don't clip mesh-heavy content. The runtime cost is real and visible on mid-range mobile.
