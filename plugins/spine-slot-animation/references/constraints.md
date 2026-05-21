# Constraints: IK, Transform, Path

When and why to use each Spine constraint type in slot animation, with the JSON contract verified against the official documentation and the H5G 4.x compatibility checks. The skill emits constraints only when explicitly opted in (`--enable-ik`, `--enable-transform-constraints`); defaults stay constraint-free because slot symbols generally don't need them.

## What a constraint is

A constraint is a rule the runtime applies after the setup pose, every frame. It reads the world transform of one or more "source" bones and writes new values into one or more "target" bones. Three flavors ship with Spine:

- **IK constraint** — set bone rotations so a chain reaches at a target. "Where should the elbow be, given the hand is here?"
- **Transform constraint** — copy world translation/rotation/scale/shear from one bone to another, with adjustable mix per channel. "This bone tracks that bone's pose, partially."
- **Path constraint** — move bones along a path attachment. "Slide along this curve."

All three are policy-gated in the H5G project (per `advanced_spine_contracts.py`) because they interact with mesh weights, deform, and runtime behavior in ways that need a rigger's sign-off. The skill respects this gating by default. When opted in, the emission matches the official JSON contract exactly and passes the 4.x compatibility checks.

## IK constraints

### When to reach for IK

The official doc lays out the canonical case: "to control limbs by moving a hand or foot." For slot machines, the cases that earn IK are:

- An HP character's hand that has to land precisely on a falling coin / present / wand during a win animation, no matter how the body lifts.
- An avatar's foot that should stay planted on a stage / podium across an idle while the body shifts.
- A pointing gesture where the fingertip's screen-space position matters but the elbow angle doesn't.

If the answer to "why don't you just keyframe the elbow rotation?" is "because the body is also moving and the target position is what the user cares about," then IK is the right tool. Otherwise it isn't.

For most slot symbols (LP, JP, WD, SC, MP, value, meter, transition, celebration), there are no limbs and no IK to add. For HP character symbols, IK becomes interesting only when the win choreography demands hand placement precision. The skill flags hand_L + arm_L (or hand_R + arm_R) pairs as IK candidates when the `--enable-ik` flag is set; otherwise hands are FK and bone translate keys drive the motion.

### One-bone vs two-bone IK

The official doc:

> Spine IK's can constrain one or two bones. Constraining three or more bones is not supported because it is nondeterministic and would be difficult to control. Instead, use multiple IK constraints or FK.

- **One bone** — the constrained bone rotates to point at the target. Used for "look at" behaviors (an eye-stalk that tracks the cursor, a turret that follows a target).
- **Two bone** — the parent and an immediate child both rotate so the child's tip reaches the target. Used for arms (shoulder + forearm), legs (thigh + shin).

Two-bone IK has structural requirements (verified from the limitations section):

- The child must be an immediate child of the parent.
- The target cannot be a descendant of the constrained bones.
- The child's local Y translation is zeroed when stretch is on or when the parent has non-uniform scale.

### Properties that actually matter for slot work

`mix` — the FK/IK blend. 0 = pure FK (animation drives bone rotation directly), 1.0 = pure IK (the target bone's position fully drives the chain). Slot wins typically mix from 0 → 1.0 over a few frames at the start of the win and back to 0 at the end. The official doc notes: "Often mixing FK and IK is only necessary briefly to transition to or from 0 (only FK) and 100 (only IK) during an animation."

`softness` (two-bone only) — slows the bones as they approach maximum reach. The official doc shows the importance: with softness 0, the chain straightens sharply when the target moves far from the rig, which reads as a snap. With non-zero softness, the chain eases into the limit. For slot work, softness is usually small (5–10 units) and exists to avoid the snap.

`bendPositive` (two-bone only) — counterclockwise bend direction. The animator picks the "elbow points down" or "elbow points up" choice once and it stays.

`compress` (one-bone only) — when target is closer than bone length, scale the bone smaller to reach. Useful for "look at" with depth (a head that tilts down when something is close).

`stretch` (one- and two-bone) — when target is past max reach, scale the bones larger. Slot wins occasionally stretch hands to dramatic positions; the docs note limitations when softness > 0 or parent has non-uniform scale.

### IK JSON contract

Setup (under top-level `"ik"` array):

```json
"ik": [
  {
    "name": "hand_R_ik",
    "order": 2,
    "bones": ["arm_R_bone", "forearm_R_bone"],
    "target": "hand_R_ik_target_bone",
    "mix": 0,
    "bendPositive": false,
    "softness": 5,
    "stretch": false,
    "compress": false,
    "uniform": false
  }
]
```

Animation timeline (under animation's `"ik"`):

```json
"ik": {
  "hand_R_ik": [
    { "time": 0, "mix": 0, "bendPositive": false },
    { "time": 0.2, "mix": 1.0, "bendPositive": false },
    { "time": 1.8, "mix": 1.0, "bendPositive": false },
    { "time": 2.0, "mix": 0, "bendPositive": false }
  ]
}
```

The target bone is a normal bone that the animator (or the controls JSON) drives via translate keys. The IK constraint solves the chain rotations every frame to reach it.

### The skill's IK emission

`build_spine_package.py --enable-ik` walks the rig layout for hand_L+arm_L and hand_R+arm_R pairs and, when both are present, emits:

- A target bone at the hand's setup position (so the chain starts in setup pose).
- A two-bone IK constraint with `mix: 0` in setup.
- Animation timeline keys on the win animation that mix from 0 → 1 over 0.15s, hold, then mix back.

Default is **off**. The rigger reviews the result, decides whether to keep it, tunes the target's animation, and either approves the package or rolls back.

## Transform constraints

### When to reach for transform constraints

A transform constraint copies world transform from one bone (target) to one or more bones (constrained), with per-channel mix that decides how strongly. Slot uses:

- **"This jewel sways with the head, but less."** Constrained bone = jewel; target = head; mix `rotateMix: 0.5`, others 0.
- **"This shadow translates with the body, doesn't rotate or scale."** Constrained bone = shadow; target = body; `translateMix: 1.0`, `rotateMix: 0`, `scaleMix: 0`.
- **"This pair of accessories should mirror each other."** Constrain accessory B to accessory A with `scaleMix: 1.0`. When the animator scales accessory A in a key, B follows.
- **"This bone sits halfway between two reference points."** Set up two reference bones at the endpoints, parent a midpoint bone to one, transform-constrain it to the other with `translateMix: 0.5`.

### Properties

`local` — when checked, the constrained bone's *local* transform is modified to match the target (the constraint runs in the parent's space). When unchecked, the world transform is modified directly. World is the common default for slot work because it makes "follow this regardless of where my parent sits" intuitive.

`relative` — when checked, the target's transform is *added* to the constrained bone's existing transform. When unchecked, the target's transform replaces the constrained bone's transform at mix=1. Additive (relative) is unusual; most slot uses are absolute.

`offset` — per-channel additive offset on top of the target. "Track the head's rotation but always 30° more." Saved as `rotation`, `x`, `y`, `scaleX`, `scaleY`, `shearY` in the constraint definition.

`mix` — per-channel blend. `rotateMix` 0.5 means 50% of the target's rotation feeds through; `translateMix` 0.0 means translation is ignored.

### Transform constraint JSON contract

Setup (top-level `"transform"`):

```json
"transform": [
  {
    "name": "jewel_to_head",
    "order": 1,
    "bones": ["jewel_bone"],
    "target": "head_bone",
    "rotation": 0,
    "x": 0, "y": 0,
    "scaleX": 0, "scaleY": 0,
    "shearY": 0,
    "rotateMix": 0.5,
    "translateMix": 0,
    "scaleMix": 0,
    "shearMix": 0,
    "local": false,
    "relative": false
  }
]
```

Animation timeline:

```json
"transform": {
  "jewel_to_head": [
    { "time": 0, "rotateMix": 0.5, "translateMix": 0, "scaleMix": 0, "shearMix": 0 },
    { "time": 1.0, "rotateMix": 0.8, "translateMix": 0, "scaleMix": 0, "shearMix": 0 }
  ]
}
```

### The skill's transform constraint emission

Not auto-applied. With `--enable-transform-constraints`, the user supplies a JSON description of which constraints to add (which bones constrain which, with what mix), and the skill emits them into the package. The most common case the skill auto-detects is "this body part has a layer named `*_shadow` parented under it" — for a shadow, a 100% translate + 0% rotate constraint is a sane default. Other constraints stay in the user's hands.

## Path constraints

Path constraints move bones along a path attachment (a cubic spline). The classic use cases:

- A worm or snake whose body bones slide along a path.
- Text or icons that follow a curve.
- A coin or sparkle that flies along a predetermined trajectory during a celebration.

For most slot animation, path constraints are unnecessary. The cases where they earn complexity are decorative motion paths during celebrations or transitions, and even there a simple translate keyframe sequence is often equivalent.

### Path constraint properties (verified from the format doc)

```json
"path": [
  {
    "name": "coin_along_arc",
    "order": 0,
    "bones": ["coin_bone"],
    "target": "celebration_path_slot",
    "positionMode": "percent",
    "spacingMode": "length",
    "rotateMode": "tangent",
    "rotation": 0,
    "position": 0,
    "spacing": 10,
    "rotateMix": 0,
    "translateMix": 1.0
  }
]
```

- `target` — the slot holding the path attachment (note: target is a slot here, not a bone, because the path itself lives in a slot).
- `positionMode` — `fixed` or `percent`. Percent means `position` is 0–100 along the path; fixed means literal distance.
- `spacingMode` — how spacing between constrained bones is measured (`length`, `fixed`, `percent`).
- `rotateMode` — how bones rotate along the path (`tangent` follows the curve direction, `chain` keeps each bone aligned with the previous, `chain scale` scales bones to maintain spacing).

Animation timelines per channel:

```json
"path": {
  "coin_along_arc": {
    "position": [
      { "time": 0, "position": 0 },
      { "time": 1.5, "position": 100 }
    ],
    "mix": [
      { "time": 0, "rotateMix": 0, "translateMix": 1.0 }
    ]
  }
}
```

### The skill and path constraints

Not auto-emitted. If a user needs a coin to fly along a curve during a celebration, the path attachment is itself a creative decision (where does the curve go, how long is it, is it open or closed). With `--enable-path-constraints` and a user-supplied path definition, the skill emits the constraint and animation timeline; without it, the bundled celebration recipe uses simple translate keyframes.

## Constraint application order

The official doc on transform constraints (and a parallel note on the format spec) mentions that all constraints have an `order` field. Constraints are applied in ascending `order`. Why this matters:

- An IK constraint and a transform constraint on the same bone produce different results depending on which runs first.
- A path constraint that positions a bone, followed by an IK constraint that points it at a target, is the documented "moving along a path while pointing at something" pattern.

The skill emits constraints with sensible `order` values: transform constraints first (order 1), IK constraints next (order 2), path constraints last (order 3). This is the conventional Spine ordering and matches the official examples.

## Constraints and weights

Mesh weights run *after* constraints in the runtime pipeline. So an IK constraint that bends an arm chain into a new pose feeds into the weighted mesh attached to that chain, and the mesh deforms correctly. There's nothing special to opt into; the contract is automatic.

## The "do I need a constraint?" decision tree

1. Can the motion be expressed by keyframing the bone's own translate / rotate / scale? **Stay FK.** This covers 95% of slot animation.
2. Does the user-visible motion describe an *endpoint* (where a hand lands, where a foot rests) rather than a *path* (how the elbow rotates)? **Two-bone IK.**
3. Does one bone need to track another bone's pose with some mixing? **Transform constraint.**
4. Does a bone need to follow a curve? **Path constraint** (with a path attachment in a slot).
5. Otherwise, animate directly. The simpler the rig, the cheaper it is at runtime and the less there is to debug.

## What the strict 4.x compatibility checks validate for constraints

The H5G checker walks the JSON and verifies:

- Every IK constraint's `bones` list references real bone names.
- Every IK target is not a descendant of the constrained bones.
- Two-bone IK has exactly two bones with a parent-child relationship.
- Transform constraints reference real bones for `bones` and `target`.
- Path constraints reference a real slot for `target` (because a path is a slot attachment, not a bone).
- Animation constraint timelines key only fields the constraint actually has.

The skill's emitter respects each of these. A package generated with `--enable-ik` for an HP3 rig that includes hand_L + arm_L + a target bone passes the strict 4.x checks by construction.

## What's bundled and what isn't

| Capability | Bundled? | Notes |
|---|---|---|
| IK constraint emission (one- or two-bone) | Yes, gated `--enable-ik` | Skill auto-detects arm + hand pairs and emits two-bone IK with mix-keyed win animations. |
| Transform constraint emission | Yes, gated `--enable-transform-constraints` | User supplies which bones / which mix; skill emits the JSON. Skill auto-applies the conventional "shadow follows body" case when a `*_shadow` layer is detected. |
| Path constraint emission | Yes, gated `--enable-path-constraints` | User supplies the path attachment and the constrained bone list. |
| Constraint animation timelines (mix keys, position keys, etc.) | Yes, when the matching enable flag is set | Default animations stay FK; constraint timelines added on top. |
| IK target tuning (where the hand should reach) | No | Animator's job. The skill places the target at the hand's setup position. |
| Path attachment authoring | No | Path geometry is a creative decision. |
| Weight painting (related to but not part of constraints) | No | Animator's job. See `meshes_and_deform.md`. |
