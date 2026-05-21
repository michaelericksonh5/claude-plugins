# Spine 4.2 JSON Contract

Legacy reference only. New work defaults to `references/spine_43_contract.md`; use this document to diagnose older 4.2 packages or migrate 3.8/v10 output.

The exact field-by-field shape that Spine Editor 4.2 Enterprise and `@esotericsoftware/spine-player@4.2.43` accept. The 4.2 player silently ignores legacy 3.8 field names; getting any of these wrong produces a blank canvas, a frozen animation, or a runtime crash — usually with no console error.

This document is the contract a compiler must emit. The skill never writes raw Spine JSON in chat — it ensures the compiler honours every rule below.

## Table of contents

1. [Skeleton header](#skeleton-header)
2. [Bones and bone timelines (translate / rotate / scale)](#bones-and-bone-timelines)
3. [Slots and slot timelines (rgba / rgba2 / attachment)](#slots-and-slot-timelines)
4. [Skins (array form in 4.x)](#skins-array-form-in-4x)
5. [Sequence attachments](#sequence-attachments)
6. [Draw order](#draw-order)
7. [Atlas format](#atlas-format)
8. [The four standard animations](#the-four-standard-animations)
9. [Shared-timeline composition rule](#shared-timeline-composition-rule)
10. [3.8 fallback profile: v10_linear](#38-fallback-profile-v10_linear)

---

## Skeleton header

```json
"skeleton": {
  "spine": "4.2.0",
  "width": <PSD_doc_width>,
  "height": <PSD_doc_height>,
  "fps": 24,
  "images": "./",
  "audio": ""
}
```

- `spine` MUST start with `"4.2"`.
- `width` / `height` MUST equal the PSD document size, **not** the atlas page size. The runtime camera uses skeleton dimensions for viewport bounds; an atlas-sized skeleton makes the rig look like a sub-pixel speck.
- `fps` is conventionally 24 for slot animation.

---

## Bones and bone timelines

One bone per art part, plus a root bone (`_rig`) that has no parent. Bones form a tree: each non-root bone has exactly one parent.

```json
"bones": [
  { "name": "_rig" },
  { "name": "body", "parent": "_rig", "x": 0, "y": 0, "rotation": 0 },
  { "name": "head", "parent": "body", "x": 12, "y": 1, "rotation": 0 },
  { "name": "eyes", "parent": "head", "x": -2, "y": 22, "rotation": 0 }
]
```

A bone's `x` and `y` are LOCAL to its parent bone, not absolute to the document. See `references/intake.md` for the parent-local placement math.

### Translate, rotate, scale timelines

| 4.2 field name | 3.8 legacy name | Inner field | Semantics |
|---|---|---|---|
| `translate` | `translate` | `x`, `y` | DELTA added to setup pose at full mix |
| `rotate` | `rotate` | `value` | **NOT `angle`** — DELTA added to setup rotation at full mix |
| `scale` | `scale` | `x`, `y` | REPLACES setup scale at full mix |

Translate and rotate are **deltas**. A key of `{ x: 0, y: 0, value: 0 }` means "no change at this time relative to setup". A key of `{ x: 0, y: 5 }` means "displaced 5 units up from setup".

If a compiler writes `{ time: 0, x: bone.x, y: bone.y }` for a bone whose setup is already `(bone.x, bone.y)`, the offset is doubled at runtime and the rig explodes off-center. Compilers must emit deltas, not absolutes.

Scale is absolute at full mix. Most parts have setup `scaleX = scaleY = 1`, so writing `{ x: 1, y: 1 }` for "no change" is correct in practice.

```json
"animations": {
  "idle": {
    "bones": {
      "head": {
        "translate": [
          { "time": 0,   "x": 0, "y": 0 },
          { "time": 2.0, "x": 0, "y": 2 },
          { "time": 4.0, "x": 0, "y": 0 }
        ],
        "rotate": [
          { "time": 0,   "value": 0 },
          { "time": 1.0, "value": 5 },
          { "time": 2.0, "value": 0 }
        ]
      }
    }
  }
}
```

If you see a rotate key with `"angle"` instead of `"value"`, that's a 3.8 emission and the 4.2 player will silently sample 0 — the rig has no rotation. Fix the compiler.

---

## Slots and slot timelines

One slot per bone that hosts visible art. Slot order in the array is the draw order: first → drawn first → bottom; last → drawn last → top.

```json
"slots": [
  { "name": "body_slot", "bone": "body", "attachment": "parts/body" },
  { "name": "head_slot", "bone": "head", "attachment": "parts/head" },
  { "name": "head_eyes_blink_slot",
    "bone": "eyes",
    "attachment": "parts/head_eyes_blink",
    "color": "ffffff00" }
]
```

### Slot timeline field names

| 4.2 field name | 3.8 legacy name | Used for |
|---|---|---|
| `rgba` | `color` | Slot tint + alpha |
| `rgb` | (rare) | Slot tint only |
| `alpha` | (rare) | Slot alpha only |
| `rgba2` | `twoColor` | Two-color tint (requires setup `dark`) |
| `rgb2` | (rare) | Two-color tint without alpha |
| `attachment` | `attachment` | Swap attachment by name; `null` clears |

```json
"slots": {
  "head_eyes_blink_slot": {
    "rgba": [
      { "time": 0,    "color": "ffffffff" },
      { "time": 0.36, "color": "ffffffff" }
    ],
    "attachment": [
      { "time": 0,    "name": null },
      { "time": 0.36, "name": "parts/HP1_head_eyes_blink" },
      { "time": 0.6,  "name": null }
    ]
  }
}
```

`name: null` is valid and clears the slot's attachment in Spine Player 4.2. **Prefer stepped attachment timelines for expression overlays over alpha fades**, because anti-aliased rectangular alpha mattes show as visible boundaries when partial-alpha rendered. See `references/pitfalls.md#overlay-alpha-matte-seam`.

### Two-color timelines

`rgba2` requires the slot's setup pose to define a `dark` color:

```json
"slots": [
  { "name": "slot", "bone": "bone", "attachment": "x", "dark": "000000" }
]

"rgba2": [
  { "time": 0,    "light": "ffffffff", "dark": "00000000" },
  { "time": 0.35, "light": "ffffffff", "dark": "00000018" }
]
```

Without setup `dark`, the 4.2 player crashes at apply time (writes to `slot.darkColor` which is null). Error: `Cannot read properties of null (reading 'r')`. If you don't need two-color tinting, omit `rgba2` entirely.

### Overlay polarity (critical for character symbols)

Character PSDs separate expression art into overlay layers that sit on top of a base face that already has the default expression baked in:

- `*_head` has open eyes and neutral mouth baked in. Always visible.
- `*_head_eyes_blink` has closed-eye art only. Hidden at rest.
- `*_<character>_laugh` has open-mouth art only. Hidden at rest.

If the compiler leaves these overlay slots visible by default, the symbol shows the OPPOSITE of the intended rest expression — closed eyes, laughing mouth. The fix: set the slot's setup `color` to `"ffffff00"` (alpha 0) for overlay slots. Then in animations, briefly switch to `"ffffffff"` (alpha 1) during the action moment — or, better, use the stepped attachment pattern above.

Detection heuristic: layer name contains `blink`, `laugh`, or `eyes`; or semantic role is `eyes` or `mouth/laugh`.

---

## Skins (array form in 4.x)

Spine 4.x requires `skins` as an array of skin objects:

```json
"skins": [
  {
    "name": "default",
    "attachments": {
      "head_slot": {
        "parts/HP1_head": { "type": "region", "path": "parts/HP1_head", "width": 108, "height": 143 }
      }
    }
  }
]
```

3.8 emitted this as a plain object keyed by skin name. The 4.2 player iterates `root.skins.length`; a plain object has no `.length`, so no skin loads, every slot's attachment is null, and the canvas is blank. **The compiler must emit array form.** This is the #1 cause of silent-blank-canvas reports.

The package builder may emit additional named skins only when a reviewed `--skin-plan` is provided. The default skin remains first and must contain the setup attachments for every setup slot so non-default skins can intentionally fall back for unplanned slots. Phase 6 skin plans support region variants only: alternate PNGs are packed into the atlas and keyed under an existing default slot attachment key. Linked meshes, placeholder fabrication, and new skin-specific constraint authoring are not implemented.

Non-default skins may include membership arrays for existing bones and existing top-level `ik`, `transform`, `path`, or `physics` constraints. The validator rejects unknown bone or constraint names and any linked mesh attachment.

### Region attachments

Region attachments are the common case. Each attachment has a `path` matching an atlas region, and `x`/`y`/`width`/`height` describing where the cropped image sits relative to the bone origin.

```json
"parts/HP1_head": {
  "type": "region",
  "path": "parts/HP1_head",
  "x": 0,
  "y": 0,
  "width": 108,
  "height": 143
}
```

Once the bone is placed at the layer's visual center, the attachment offset is `(0, 0)`. Do NOT use pivot hints from a layer-semantics interpreter as attachment offsets; pivot hints describe where the BONE should sit (rig-tuning guidance), not where the IMAGE should slide.

---

## Sequence attachments

Spine 4.2 supports `sequence` data on region and mesh attachments. Use this for numbered VFX frame runs such as `sparkle_001.png`, `sparkle_002.png`, etc. The attachment path is the unnumbered base; the atlas contains the numbered frames.

```json
"parts/sparkle": {
  "type": "region",
  "path": "parts/sparkle",
  "sequence": {
    "count": 12,
    "start": 1,
    "digits": 3,
    "setup": 0
  },
  "width": 64,
  "height": 64
}
```

The atlas must contain:

```text
parts/sparkle_001
parts/sparkle_002
...
parts/sparkle_012
```

A slot `sequence` timeline controls playback:

```json
"slots": {
  "sparkle_001_slot": {
    "sequence": [
      { "time": 0, "mode": "once", "index": 0, "delay": 0 },
      { "time": 2.0, "mode": "hold" }
    ]
  }
}
```

Valid modes include `hold`, `once`, `loop`, `pingpong`, and reverse variants supported by the 4.2 runtime. Validate every expected atlas frame exists before claiming the package is ready.

---

## Draw order

Static draw order is the slot array order. Dynamic per-animation overrides live in the animation's `drawOrder` timeline:

```json
"drawOrder": [
  { "time": 0, "offsets": [] },
  { "time": 0.35, "offsets": [{ "slot": "shine_slot", "offset": 0 }] }
]
```

Most symbols don't need dynamic draw order. Keep it conservative.

---

## Atlas format

```text
shared_symbols.png
size: <atlas_w>,<atlas_h>
format: RGBA8888
filter: Linear,Linear
repeat: none
parts/<region_name>
  rotate: false
  xy: <x>, <y>
  size: <w>, <h>
  orig: <orig_w>, <orig_h>
  offset: 0, 0
  index: -1
```

- Page filename in the header MUST match the actual PNG filename.
- Every attachment `path` MUST match a region name in the atlas.
- The atlas is straight (non-premultiplied) alpha. `preview.html` config uses `premultipliedAlpha: false`.
- DO NOT add `pma: true`. Our atlas is straight; the player defaults to `pma: false`, which matches.
- Use `filter: Linear,Linear`. Nearest-neighbour produces visible pixel stair-stepping when the symbol rotates or scales during animation.

Atlas packing details (alpha-trim, RGB bleed, 1-px edge extrusion) belong to the compiler. They're documented in the slot-animation reference; if the user asks why their region has a halo, point them at those steps.

---

## The four standard animations

Every symbol family gets at least these four animations. Per-family extensions add `smart`, `intro`, `outro`, state transitions, etc. (see `references/families.md`).

### `idle` — 4.0 s loop

Subtle, loopable, no abrupt cuts. The constant motion shown while the symbol sits on the reel.

Composition for a character symbol:

- Body: vertical breath, ±1–2 px over 4 s. Subtle scale pulse on the chest.
- Head: gentle bob, lagged from the body. 2–4° rotation amplitude.
- Eyes: two blinks at 1.16 s and 3.16 s. Stepped attachment timeline, ~60 ms each.
- Mouth/laugh: held neutral (overlay hidden) during idle.
- Hand: lateral sway, ±2–3 px.
- Frame: subtle scale pulse, 1.00 → 1.02 → 1.00.
- Frame-glow: alpha pulse, 0.8 → 1.0 → 0.8.

For non-character symbols (LP letters, JP badges, value symbols), idle is usually a single scale pulse + slot color sheen sweep on the body slot.

### `breathe` — 2.0 s loop

Shorter, calmer loop used when the symbol is "alive" but no other motion should distract. Usually a subset of `idle`: body breath + head bob + frame pulse only. No blinks, no hand sway.

### `land` — 0.4 s impact

Short, percussive, settles into rest pose.

Composition:

- Body: 0.05 s squash to 0.95 scale, 0.10 s stretch to 1.05, settle to 1.00 by 0.4 s.
- Head: 0.08 s delay then follow-through, ±4° rotation.
- Hand: 0.10 s catch-up motion.
- Mouth: brief 0.06 s squash.
- Frame-glow: alpha flash 0.0 → 1.0 → 0.6 over the 0.4 s.

For non-character symbols: scale pulse + slot color flash.

### `win` — 2.0 s feature

The celebration when the symbol participates in a winning combination.

Composition for a character symbol with a "laugh" overlay (Ho-Ho-Ho example):

- Body: subtle pulse and lift.
- Head: emphasis bob, 4–8° rotation.
- Hand: wave gesture, ±5–8 px horizontal.
- Arm: follow-through.
- Eyes + mouth: synchronized Ho-Ho-Ho beats at 0.36 s, 0.92 s, 1.48 s. Each beat is a stepped attachment swap (mouth becomes visible, eyes become closed) for ~60 ms, then back to hidden.
- Frame: stronger scale pulse, 1.00 → 1.06 → 1.00.
- Frame-glow: shimmer, alpha 0.6 → 1.0 → 0.6.

For non-character symbols: scale pulse to ~1.1×, slot color sheen, optional VFX attachment-swap sequence.

---

## Shared-timeline composition rule

A symbol's `idle`, `breathe`, `land`, and `win` animations are **composite performances**: every relevant part keys the SAME shared timeline. The body breathes, the head bobs, the eyes blink, the mouth pulses, the hands sway, the frame pulses, the frame-glow shimmers — all on the one `idle` timeline. They are not 12 separate per-part animations.

A naive per-part composition would create twelve disconnected idle animations that play simultaneously, with timing drift between them. Sharing the timeline forces coordinated motion and is what makes a generated rig look choreographed rather than mechanical.

When the user asks "why does my rig look mechanical even though every part has motion?" — check whether each part has its own animation name or whether they share a timeline.

---

## 3.8 fallback profile: v10_linear

The skill now defaults to Spine 4.3 output. The 3.8 v10_linear profile exists only as a fallback for legacy proof workflows (e.g., the H5G `hp_symbol_proof_compiler.py`) that have not been migrated.

### When to use v10_linear

- The user explicitly requests it (`--profile v10_linear` or "use the v10 linear profile").
- The reference compiler is the legacy proof compiler that only emits 3.8 with the v10_linear constraint.
- The downstream consumer cannot accept 4.2 JSON.

`scripts/build_spine_package.py` is not a v10 emitter and rejects `export_profile: "v10_linear"` with a validation error. Use the legacy proof compiler for v10 packages, or omit `export_profile` for default current 4.3 output.

### The v10_linear contract

- Spine version string is the compiler's 3.8 build (e.g., `"3.8.99"`).
- Timelines are strictly linear: no Bezier curve arrays, no non-linear `curve` values. Missing `curve` fields are treated as linear.
- Slot color timelines use the 3.8 `color` field, not 4.2 `rgba`.
- Rotate timelines use the 3.8 `angle` field, not 4.2 `value`.
- `skins` is emitted as a plain object keyed by skin name (3.8 form), not an array.
- Two-color timelines (`twoColor`) are accepted but discouraged.

Do NOT mix v10_linear emissions with 4.2 emissions in the same package. Pick one profile, validate against the matching gate, and ship.

## 4.2 Bezier profile: spine_42_bezier

`spine_43_bezier` is the current explicit opt-in curve profile. `spine_42_bezier` is accepted only as a legacy alias for older controls. The compiler expands `bezier_preset` values (`ease_in`, `ease_out`, `ease_in_out`, `overshoot`, `settle`) into numeric absolute handle arrays. Emitted JSON does not use unsupported named curve strings.

Current coverage is intentionally narrow: bone `rotate` / `translate` / `scale` and slot `rgba` / `alpha` timelines when present. Linear remains represented by omitting `curve`; this compiler emits and accepts numeric curve arrays only, not named curve strings. Attachment, sequence, animation-level events, and draw-order timelines must not receive curves. This profile does not imply global coverage for path constraints, deform, sequence timing, or every Spine timeline type.

### Validation

For v10_linear packages, the per-package `validation_report.json` is the gate. There is no v10_linear-specific strict checker beyond "no Bezier curves" and "supported animation names". Don't run the 4.2 compatibility checker against a v10_linear package — it will report dozens of false errors.

### When to migrate legacy v10 output

If the user is starting a new game / new symbol set, use the current 4.3 path in `references/spine_43_contract.md`. If they have an existing v10_linear package and an older runtime is moving to 4.2.43, the migration involves:

1. Switch the compiler to a 4.2-emitting path (e.g., the H5G `layered_rig_compiler.py`).
2. Re-validate with the 4.2 compatibility checker.
3. Re-preview against `@esotericsoftware/spine-player@4.2.43`.

Document the migration in the package's audit manifest.

---

## Single-source truth

The 4.2 contract above is the union of: Spine Editor 4.2 Enterprise emission, `@esotericsoftware/spine-player@4.2.43` runtime expectations, and the H5G reference compiler's regression-tested output. When the contract and a tutorial disagree, trust the contract — it's what the runtime actually parses.
