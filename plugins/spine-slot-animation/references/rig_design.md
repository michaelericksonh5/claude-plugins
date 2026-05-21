# Rig Design

Spine's rig design philosophy as it applies to slot-machine animation work. This file synthesizes the official Spine documentation with the H5G project's verified contract and explains *when* to reach for each Spine feature, not just *how* it's spelled in JSON.

The deeper "what is each feature for" lives in the dedicated references: `meshes_and_deform.md`, `constraints.md`, `events.md`, `clipping.md`. Read those for individual feature contracts. Read this one for the design judgement that ties them together.

## The mental model

A Spine rig is a **skeleton** plus the **art it draws plus the rules for how that art responds to time and state**.

- The **skeleton** is bones and slots: a tree of transforms (`root → body → head → eyes`) with a draw order (slot index = z-position).
- The **art** is attachments: region (single image), mesh (image stretched across a polygon you control), bounding box (hit test), path (curve), point (rotation+position), clipping (polygon mask). Most slot art is region; only character animation needs mesh.
- The **rules** are animations (timelines of deltas), constraints (IK / transform / path that compute one bone's pose from another's), and events (named triggers your game code listens for).

Every authoring decision is a choice about which of these three layers to push the behavior into. The skill enforces a single rule: **automate the parts that are deterministic from layer names and bounds; surface clearly the parts that need an animator's judgement.**

## When to use what (slot-machine perspective)

### Region attachment — the default

Use a region for every layer in every slot-symbol family unless the layer needs to deform. Region attachments are:

- The cheapest at runtime (one quad, four vertices, one matrix transform per slot).
- Trivially atlas-packable (the bundled `build_atlas.py` does it).
- All you ever need for LP letters, JP badges, value text, decorative frames, glows, sparkles, hats, hands, and most symbol bodies.

A region's bone sits at the layer's visual center; the attachment offset is `(0, 0)`. The bone moves, the rectangle moves with it. No vertex-level work.

### Mesh attachment — only when art must bend or stretch

Reach for a mesh when an asset will be physically deformed by animation: a flag waving, a tail curling, a balloon inflating, a face squashing/stretching. **Do not mesh decorative slot art that only translates / rotates / scales.** Meshing a static rectangle wastes vertex transforms with no visible benefit.

A mesh is also the right tool when the art has a lot of empty pixels you want to trim from the atlas: `Trace` in Spine Editor (or the equivalent in your asset prep) places vertices around the visible hull so transparent pixels never render. For a giant decorative frame_glow that's 90% blank, mesh-trimming the hull beats the region rectangle for fill rate.

Key tradeoffs (verified from the official mesh / weights docs):

- Each mesh vertex costs one *vertex transform* per frame. A mesh with 100 vertices needs 100 transforms; if each vertex is bound to 2 bones via weights, 200.
- The number of vertices is the lever to pull when frame budget gets tight. Run `Prune` on weights to cap bones-per-vertex; remove unnecessary vertices.
- Deform keys (per-vertex animation) are a last resort. Weighted deformation driven by bone motion is the preferred path. The official guide is explicit: "Deform keys should generally be avoided and weights used instead."

The default package builder keeps regions unless an explicit mesh flag is supplied. `--report-mesh-candidates` writes a deterministic candidate report, and `--auto-mesh-plan` can generate a conservative draft plan for roles such as cape, hair, tail, antennae, earrings, and dangling jewelry. Character bodies become candidates only when deformation-style controls request extra bending/squash. Mesh hulls, interior vertices, and final weights still need animator review. See `meshes_and_deform.md` for the contract and decision rules.

### IK constraint — for limb pinning during win choreography

Reach for IK when the user-visible motion is "the hand is at this point, work out the elbow." Classic case: an HP character whose hand needs to land precisely on a falling coin during the win animation, no matter how the body lifts. Without IK, the animator would have to manually keyframe the elbow rotation for every body lift; with IK, they animate the target bone and the chain solves itself.

Verified IK limitations from the official doc:

- One- or two-bone chains only. Three+ bones is "nondeterministic and difficult to control" per the docs — use multiple two-bone IKs or stay on FK.
- Target bone cannot be a descendant of the constrained bones.
- For two-bone IK, the child must be an immediate child of the parent.
- `softness` slows bones near the limit of reach (prevents the snap-straight-then-jitter problem; the official doc shows this as the recommended setting).
- `mix` lets you crossfade between FK and IK, which is how transitions in/out of a win pose are usually handled.

For most slot symbols, IK is overkill. Restrained idle motion is FK. **Where IK earns its complexity is in featured HP character wins** (a wave gesture that has to land precisely, a bow that touches the frame, a hand grabbing a falling object). The skill flags IK as a candidate when an HP character has both arm and hand layers — but it stays gated behind `--enable-ik` so the rigger reviews before it ships.

### Transform constraint — for "this bone follows that bone, partially"

A transform constraint copies world rotation / translation / scale / shear from one bone to another, with a mix that decides how strongly. Slot-machine uses:

- A jewel that should follow the head's rotation 50% (so it sways but less dramatically). Constrain the jewel bone, target the head, mix rotate at 0.5.
- A reflection or "ghost" bone that should sit halfway between two real bones. Constrain the ghost, target one of the reals, set offset to half the distance.
- Equipped accessories that should detach cleanly when a hat-flies-off win plays. Use a transform constraint with a mix that animates from 1.0 (attached) to 0.0 (detached); during the detach phase the hat follows the head with strength 1.0; when it should fly free, the mix animates down to 0 and a separate animation drives the hat alone.

The official doc calls out the most common pitfall: when `Local` is unchecked and `Relative` is checked, flipping a target via negative scale produces a 180° rotation jump on the constrained bone. Avoid that combination unless the rig is explicitly stress-tested for it.

### Path constraint — rare in slot work

Path constraints move bones along a curve. The classic use is a worm crawling along a path or text wrapping around a curve. Slot animation occasionally uses paths for sparkles tracing a frame border or coins flowing along a curve during a celebration. Not a default; reach for it only when the motion is genuinely curvilinear.

### Clipping attachment — only for unavoidable masking

Clipping is **expensive on the CPU** (the official doc is explicit: "can be a very expensive operation, especially when using mesh attachments with many vertices"). Slot machines have many symbols on screen at once and any clipping cost multiplies.

Rules of thumb verified from the docs:

- Use 3 vertices when possible (the minimum allowed). A triangular clip is cheaper than a complex polygon.
- Keep the polygon convex. The runtime decomposes non-convex polygons into convex ones; fewer pieces = less work.
- Set the `End slot` tightly so the clip applies to as few slots as possible.
- Never let the polygon self-intersect.
- "The size of the clipping polygon does not affect performance" — only vertex count and slot count matter.

For slot work, prefer alpha-masked art over clipping. Most "this should only show inside the frame" effects can be done with an alpha mask baked into the source PNG. Reserve runtime clipping for genuinely dynamic shapes (a meter fill that changes width every frame, a transition wipe that travels across the screen).

### Events — for game-code triggers, not for visual effects

Events fire named triggers at specific times in an animation. They're not visual — the game code listens for them and decides what to do. Examples:

- `win/jackpot_reveal` at the moment the jackpot symbol's win animation hits its peak — game code plays the jackpot SFX, starts the credit counter.
- `bonus/trigger` at the moment a bonus symbol lands — game code starts the bonus mode transition.
- `scatter/land` for scatter symbols that the math engine needs to count.
- `feature/start`, `feature/end` for free-spin entry / exit transitions.

The official doc and the runtime guide make the contract clear: events carry optional `int` / `float` / `string` payloads; they're queued by `AnimationState.update` and delivered to listeners just before `apply` returns; multiple events can fire in one frame; folder paths in the editor become slash-prefixed event names at runtime (`folder/event_name`).

The skill does not invent events. It does emit a documented event timeline when the user opts in with `--enable-events` and supplies an `events.json` payload describing which events fire on which animations at which times. The runtime listener side is owned by the game team — the skill never claims to wire up listeners.

## Rig hierarchy patterns for slot symbols

The portable pipeline already implements the common patterns. The pattern key is what you keep in mind when reasoning about a rig.

### Pattern A: single-body proof (LP, JP, WD, SC, value, meter state, transition frame)

```
root
└── <symbol>_bone        (slot: <symbol>_slot → parts/<symbol>)
    └── (optional) <symbol>_sheen_bone    (slot above body, alpha-pulsed in idle)
    └── (optional) <symbol>_glow_bone     (slot below body or above, additive-feel via alpha)
```

One body, optional shimmer / sheen / glow / sparkle decorations parented to body. Idle is a single scale pulse on body + alpha pulse on decorations. Land is a brief squash + scale flash on body. Win is a stronger version of land plus a hold.

### Pattern B: layered character (HP, sometimes special-feature)

```
root
├── <sym>_BG_bone                       (always-visible background)
├── <sym>_frame_bone                    (decorative frame)
│   └── <sym>_frame_glow_bone           (glow parented under frame, alpha-pulsed)
├── <sym>_head_bone                     (head with default expression baked in)
│   ├── <sym>_head_eyes_blink_bone      (hidden-at-rest overlay, stepped attachment in idle/win)
│   ├── <sym>_<character>_laugh_bone    (hidden-at-rest overlay, stepped attachment in win)
│   └── <sym>_<character>_hat_top_bone  (visible accessory parented above head)
├── <sym>_hand_L_bone                   (parented to root for proof; arm if rig has one)
└── <sym>_hand_R_bone
```

Idle, breathe, land, and win compose on a **shared timeline** so body breath, head bob, eye blinks, mouth swaps, hand sway, frame pulse, frame-glow shimmer all coordinate. The skill's `compose_animations.py` enforces this. The pitfall the docs warn about (12 disconnected per-part animations playing simultaneously) is the most common cause of mechanical-looking output.

Overlay polarity is non-negotiable. `_eyes_blink` and `_laugh` overlays sit on top of a head where the default expression (open eyes, neutral mouth) is **already baked into the head image**. If those overlays are visible at rest, the rig shows the opposite of the intended expression. The skill sets their setup slot color to `ffffff00` (fully transparent) and drives them via stepped attachment timelines during the action moment.

### Pattern C: avatar state machine (multi-state acting content)

```
root
├── State0Idle_bone     (slot, full canvas; visible only during State0Idle and Avatar default)
├── State0to1_bone      (slot, full canvas; visible only during State0to1 transition)
├── State1Idle_bone     (slot, full canvas; visible only during State1Idle, *Awarded, *Close beats with masking)
├── State1Awarded_bone  ...
└── (one slot per state-graph frame)
```

Per-state-graph-frame slots, all parented to root, all alpha-0 at setup. Each animation (`State<N>Idle`, `State<N>to<M>`, `State<N>Awarded`, `State<N>Close`, top-level `Avatar`) turns exactly one state's slot to alpha 1.0 and holds the others at 0.0. The skill's `build_avatar_states.py` produces this graph.

What this pattern explicitly does *not* try to do today: real expression-layer compositing within a state, IK on avatar limbs, mesh deformation on the avatar body, persistent state across spins (that lives in game code). Each of those is a separate review pass.

## Pivot placement

A bone's pivot is the point around which rotation and scale happen. For slot art:

- `center` — the default. Region attachment offset stays `(0, 0)`. Good for most body parts.
- `bottom_edge` — for hats, jewels, anything attached to a parent surface. Rotating around the bottom keeps the contact point fixed.
- `top_edge` — for hanging things (a banner from a pole, a lantern from a hook).
- `wrist` / `shoulder` — for limbs. The hand bone pivots at the wrist so the fingers don't shear; the arm pivots at the shoulder.

The skill's `interpret_layers.py` records a `pivot_hint` per layer based on semantic role. Today the rig layout builder doesn't move the bone away from layer center even when a pivot hint says otherwise — it's a hint for animator review, not an automated offset. Future work: drive bone position from `pivot_hint` and trim the attachment's `x`/`y` to compensate.

## Why this matters for slot games specifically

Slot games run many symbols on screen simultaneously, often on mid-range mobile hardware. Three principles fall out of that:

1. **Lean rigs ship.** Region attachments cost nothing; mesh attachments cost vertex transforms; weights multiply that cost; clipping multiplies it again. Only use complexity where the user can see the benefit.
2. **Shared timelines look choreographed.** Per-part animations look mechanical even at the same duration because keyframe phase drifts. The shared-timeline rule from the docs is the single biggest visual-quality lever for character symbols.
3. **The art team owns judgement; the pipeline owns determinism.** Vertex placement, weight painting, exact rotation amplitudes, expression timing — these are creative decisions. Atlas packing, JSON contract, validation gates, family classification — these are deterministic and the skill automates them. Don't ask the skill to make creative decisions, and don't ask the artist to type JSON.

## What the skill bundles vs what the artist still owns

| Capability | Skill bundles? | Notes |
|---|---|---|
| Layer → semantic role mapping | Yes | `interpret_layers.py` |
| Bone tree with parent-local placement | Yes | `build_rig_layout.py` |
| Idle / breathe / land / win on shared timeline | Yes | `compose_animations.py` |
| Avatar state graph (idle / transitions / awarded / close) | Yes | `build_avatar_states.py` |
| Atlas packing with alpha-trim + RGB bleed + edge extrusion | Yes | `build_atlas.py` |
| Events emission (when user supplies the event plan) | Yes (gated `--enable-events`) | See `events.md` |
| IK constraint emission (one- or two-bone) | Yes (gated `--enable-ik`) | See `constraints.md` |
| Transform constraint emission | Yes (gated `--enable-transform-constraints`) | See `constraints.md` |
| Clipping attachment emission (when user supplies polygon) | Yes (gated `--enable-clipping`) | See `clipping.md` |
| Mesh attachment emission with vertex positions | Yes (gated `--mesh-plan` or review-required `--auto-mesh-plan`) | Reviewed plans override automatic draft plans. |
| Mesh weights | Yes (gated `--auto-bind-weights` with a mesh plan) | First-pass topology-aware binding only; final weights need animator iteration. |
| Deform keys | No (and shouldn't — the official guide says avoid) | Use weights driven by bone motion instead. |
| Expression-layer compositing (pre-baked head_with_blink etc.) | No | Authoring decision; requires art pass for each state. |
| Persistent avatar state across spins | No | Game code, not Spine data. |
| Production Spine export (CLI / license) | No | Runtime acceptance tests own this gate. |

That delineation is honest and reflects the verified Spine documentation. Anything the skill claims to automate, it actually automates and validates.
