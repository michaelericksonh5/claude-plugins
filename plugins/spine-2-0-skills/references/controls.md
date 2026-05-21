# Bounded Controls Schema

The bounded numerical schema the compiler accepts for deterministic timeline changes. Use this to translate natural-language revision notes ("more bouncy", "less flashy") into a JSON object the compiler validates and applies — without freehand timeline editing.

## Output contract

For revision notes, emit ONE JSON object and nothing else. No prose, no markdown fences, no Spine JSON, no timelines, no keyframes, no raw curve arrays.

```json
{
  "recipe_type": "hp_symbol",
  "bounce_strength": 1.0,
  "land_duration_scale": 1.0,
  "idle_duration_scale": 1.0,
  "glow_intensity": 1.0,
  "sparkle_intensity": 1.0,
  "premium_intensity": 1.0,
  "motion_strength": 1.0,
  "feature_active_intensity": 1.0
}
```

All numeric fields are optional. Missing fields default to `1.0`, preserving the base recipe strength. Missing `recipe_type` defaults to `hp_symbol`. For the current 4.3 path emit no `export_profile` unless intentionally opting into `spine_43_bezier`; the portable builder rejects `v10_linear` because that profile belongs to the legacy proof compiler.

**Unknown fields fail compilation by design.** The schema is closed so creative direction stays inside the documented contract. Don't invent new control names — if a behavior isn't covered, surface it as a note for future contract work, not as a smuggled control.

The machine-readable version lives at `assets/recipe_controls_schema.json`. Reference it when validating a user-supplied controls file.

## Recipe types

`recipe_type` is one of (must match the compiler enum exactly):

```
hp_symbol            mp_symbol               lp_symbol
wild_symbol          scatter_symbol          bonus_symbol
bo_special_symbol    jackpot_symbol          special_feature_symbol
value_symbol         winframe_explode        meter
transition           celebration             avatar
```

For the per-family contract (purpose, naming, source layers, generated animations), see `references/families.md`.

## Export profiles

| Profile | Status | Meaning |
|---|---|---|
| (default, omit field) | Default for new work | Portable builder emits JSON for the current configured Spine target, now Spine Editor 4.3.04. Validated by the package compatibility checks. |
| `v10_linear` | Legacy proof only | H5G/V10-safe Spine 3.8 JSON. Numeric timelines must remain linear: no Bezier curve arrays, no non-linear `curve` values. Used by `hp_symbol_proof_compiler.py`; rejected by `scripts/build_spine_package.py`. |
| `spine_43_bezier` | Opt-in 4.3 profile | Emits numeric Bezier arrays on supported numeric timelines only: bone `rotate` / `translate` / `scale` and slot `rgba` / `alpha` when present. Attachment, sequence, animation-level events, and draw-order timelines stay curve-free. |
| `spine_42_bezier` | Legacy alias | Accepted for older controls, but new instructions should use `spine_43_bezier`. |
| `spine_modern_bezier` | Rejected | Old placeholder name. It is not a valid schema value. Use `spine_43_bezier` for the implemented opt-in profile. |

Pick one and stick to it; don't mix profiles in a single package. See `references/spine_42_contract.md#38-fallback-profile-v10_linear` for the migration story.

When `export_profile` is `spine_43_bezier`, `bezier_preset` may be one of `ease_in`, `ease_out`, `ease_in_out`, `overshoot`, or `settle`. If omitted, the compiler uses `ease_in_out`. Presets are intent names only in controls; emitted Spine JSON contains numeric absolute handle arrays, never unsupported named curve strings.

## Control fields

| Control | Range | Applies | Meaning |
|---|---:|---|---|
| `bounce_strength` | `0.0`–`2.0` | Always | Scales symbol land y-impact and x squash/overshoot magnitude. |
| `land_duration_scale` | `0.25`–`3.0` | Always | Multiplies land settle key times and total duration. |
| `idle_duration_scale` | `0.25`–`3.0` | Always | Multiplies idle loop duration and nonzero idle key times. |
| `glow_intensity` | `0.0`–`2.0` | When glow slot exists | Scales glow slot alpha in win and idle. |
| `sparkle_intensity` | `0.0`–`2.0` | When sparkle slot exists | Scales sparkle slot alpha in win and idle. |
| `premium_intensity` | `0.0`–`2.0` | Always | Scales lit / glass alpha; combines with glow, sparkle, and win pulse strength. |
| `motion_strength` | `0.0`–`2.0` | Always | Scales pulse magnitude; combines with `bounce_strength` for land. |
| `feature_active_intensity` | `0.0`–`2.0` | When smart/feature loop exists | Scales smart/feature-active loop intensity (BO/SF/JP/SC smart loops). |

Out-of-range values fail compilation. Stay inside the documented ranges.

Controls that target a missing slot become no-ops (recorded as `unsupported_noop_controls` in `validation_report.json`). That's fine — emit the control and let the compiler decide whether it applies. Don't second-guess by omitting it; the compiler is the source of truth for what applies.

## Natural-language mapping

These are the canonical mappings. Stay moderate; values near 1.0 unless the user asks for a strong change.

| Direction | Suggested controls |
|---|---|
| "more bouncy" | Increase `bounce_strength`; optionally increase `land_duration_scale` slightly for a longer settle and `motion_strength` for a more pronounced pulse. |
| "less bouncy" | Decrease `bounce_strength`; optionally decrease `land_duration_scale` for a snappier settle and `motion_strength`. |
| "stronger land" | Increase `bounce_strength` AND `motion_strength`. |
| "weaker land" | Decrease both. |
| "slower idle" | Increase `idle_duration_scale`. |
| "faster idle" | Decrease `idle_duration_scale`. |
| "more glow" | Increase `glow_intensity`; optionally increase `premium_intensity`. |
| "less glow" | Decrease `glow_intensity`. |
| "more sparkle" | Increase `sparkle_intensity`; optionally increase `premium_intensity`. |
| "less sparkle" | Decrease `sparkle_intensity`. |
| "more flashy" | Increase `glow_intensity`, `sparkle_intensity`, AND `premium_intensity`. |
| "less flashy" | Decrease `glow_intensity`, `sparkle_intensity`, AND `premium_intensity`. |
| "more premium" | Increase `premium_intensity` with moderate `glow_intensity` and `sparkle_intensity`. |
| "stronger movement" | Increase `motion_strength`; for land specifically also increase `bounce_strength`. |
| "less movement" | Decrease `motion_strength` and `bounce_strength`. |
| "more feature-active" | Increase `feature_active_intensity` for families that emit a smart loop (BO/SF/JP/SC). |

### Combination notes

Users often combine directions. Common cases:

- **"more bouncy but less flashy"** — increase `bounce_strength`, `land_duration_scale`, `motion_strength`; decrease `glow_intensity`, `sparkle_intensity`, `premium_intensity`.
- **"slower idle and more premium"** — increase `idle_duration_scale` and `premium_intensity`; leave land controls at 1.0.
- **"stronger land but keep the idle the same"** — increase `bounce_strength` and `motion_strength`; leave `idle_duration_scale` at default (omit the field).

### Typical strong / moderate / subtle steps

| Adjective | Multiplier offset |
|---|---|
| "slightly", "a touch", "a hair" | ±0.05 to ±0.15 |
| Default ("more bouncy", "less flashy") | ±0.25 to ±0.40 |
| "much", "significantly", "a lot" | ±0.50 to ±0.75 |
| "way", "really", "very" | ±0.75 to ±1.00 |

These are heuristics, not laws. The compiler will accept any value in range; pick a number that feels right for the recipe family.

## Examples

### "Make it more bouncy."

```json
{
  "bounce_strength": 1.6,
  "land_duration_scale": 1.15,
  "motion_strength": 1.2,
  "glow_intensity": 1.1,
  "sparkle_intensity": 1.1,
  "premium_intensity": 1.1
}
```

(Sympathetic small bump on glow/sparkle/premium because bounce sells better against a slightly brighter symbol.)

### "Make it less flashy."

```json
{
  "glow_intensity": 0.35,
  "sparkle_intensity": 0.2,
  "premium_intensity": 0.45,
  "motion_strength": 0.8,
  "bounce_strength": 0.8
}
```

(Less flashy also pulls in less motion, which reads as a calmer symbol overall.)

### "Make the idle faster."

```json
{
  "idle_duration_scale": 0.65,
  "glow_intensity": 1.05,
  "sparkle_intensity": 1.05,
  "premium_intensity": 1.0
}
```

(A faster idle reads as slightly more energetic, so a tiny glow/sparkle bump.)

### "Make it more bouncy but less flashy."

```json
{
  "bounce_strength": 1.35,
  "land_duration_scale": 1.1,
  "motion_strength": 1.0,
  "glow_intensity": 0.45,
  "sparkle_intensity": 0.3,
  "premium_intensity": 0.55
}
```

### LP symbol default

```json
{
  "recipe_type": "lp_symbol",
  "bounce_strength": 0.85,
  "land_duration_scale": 1.0,
  "idle_duration_scale": 1.0,
  "glow_intensity": 0.75,
  "sparkle_intensity": 0.6,
  "premium_intensity": 0.7,
  "motion_strength": 0.8
}
```

### BO / special symbol default

```json
{
  "recipe_type": "bo_special_symbol",
  "bounce_strength": 1.25,
  "land_duration_scale": 1.0,
  "idle_duration_scale": 1.0,
  "glow_intensity": 1.25,
  "sparkle_intensity": 1.2,
  "premium_intensity": 1.15,
  "motion_strength": 1.15,
  "feature_active_intensity": 1.25
}
```

## What to NEVER emit

When responding to a revision note, do NOT include any of:

- Prose narration ("Here's the controls JSON: ...").
- Markdown code fences around the JSON (the consumer parses raw JSON).
- Spine JSON timelines, keyframes, slot timelines, atlas metadata, bone tree.
- Raw curve arrays (`[0.5, 0.0, 0.5, 1.0]`) or unsupported named curve strings. Use `export_profile: "spine_43_bezier"` plus an approved `bezier_preset` when curves are intentionally requested.
- Inline comments inside the JSON (JSON does not support comments).
- Fields outside the schema.

The compiler is the source of timeline truth. The skill's job at this step is just the controls object.

## When a control is not enough

Some directions can't be expressed in the bounded schema. Examples:

- "Add a wink animation in the middle of the win cycle."
- "Make the hat fly off during land."
- "Switch the symbol from gold to silver on jackpot."

For these, the right response is: surface the gap, explain that the bounded schema doesn't cover this behavior today, and either (a) point the user to where the recipe contract for that family would need to be extended, or (b) suggest a controls-only approximation if one exists ("we can't add a wink, but we can make the existing motion more energetic"). Don't invent fields.

If the note comes from looking at a preview, use `scripts/visual_remediation_loop.py` instead of guessing. It maps safe visual findings to these bounded controls and blocks structural issues such as mesh tearing, wrong z-order, missing attachments, deform needs, linked mesh needs, or path-constraint needs.

## When the user has no rig yet

If the user gives a direction note but doesn't have a compiled rig in hand, controls JSON alone isn't enough — they also need a recipe and source layers. Ask once: "Is there an existing rig you'd like to adjust, or do you want me to walk through compiling one from PNGs / PSD first?"

Then route to Workflow B or C in the top-level SKILL.md.
