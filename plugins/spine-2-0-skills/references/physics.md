# Spine 4.2 Physics Constraints

Physics constraints simulate spring-like behavior on bones so secondary motion (capes, hair, dangly jewelry, big bellies, antennae) reacts naturally to bone motion. New in Spine 4.2 — Esoteric Software called it "the physics revolution." Local presets are bounded starting points based on the official Spine User Guide page on Physics constraints, not empirical runtime proof.

## When to reach for physics in slot work

Physics earns its complexity for natural-motion parts. For slot symbols, the cases that benefit:

- **Character HP bellies that jiggle on land** — Santa, viking, sumo, anything with a substantial torso. Land impact compresses the body bone; physics on the belly produces a few frames of jiggle that reads as soft weight.
- **Capes, cloaks, robes** — kings, queens, wizards. Body movement pulls the cape; physics drags it behind realistically.
- **Hair, ponytails, braids** — flexes from the base when the head bobs in idle.
- **Tails** — creatures, dragons, foxes. Flicks naturally during win celebrations.
- **Earrings, dangly jewelry** — jackpot tier badges with hanging gems swing convincingly.
- **Antennae** — bug, alien, robot symbols.
- **Chains** — necklaces, ropes on pirate symbols.

When NOT to use physics: static frame art, decorative glow, regular hands and arms (those are FK or IK), letter symbols, badge bodies. Physics earns complexity only when the user can see *natural-motion-without-keyframing*.

## Properties (verified from official doc)

| Property | Range / Default | What it does |
|---|---|---|
| `fps` | 30–60 (good range), default 60 | Update rate. Lower = jumpier physics. |
| `x` | 0–100 | Translate X slider — how much bone's X is physics-affected. |
| `y` | 0–100 | Translate Y slider. |
| `rotate` | 0–100 | Rotation slider. |
| `scaleX` | 0–100 | Scale X slider — bone tip resists movement, body compresses/stretches. |
| `shearX` | 0–100 | Shear X slider. |
| `limit` | default 5000 | Max speed of translation that affects physics. |
| `inertia` | 0–100, default 100 | Degree of bone movement transferred to physics offset. |
| `strength` | default 100 | Force returning the bone to unconstrained pose. |
| `damping` | default 60 | Reduces high-velocity oscillation. |
| `mass` | default 100 | Resistance to acceleration. |
| `wind` | default 0 | Constant force along world X axis. |
| `gravity` | default 0 | Constant force along world Y axis. |
| `mix` | 0.0–1.0, default 1.0 | Constraint influence. |

## JSON shape

Top-level `"physics"` array in the skeleton:

```json
"physics": [
  {
    "name": "santa_belly_jiggle",
    "order": 10,
    "bone": "santa_belly_bone",
    "fps": 60,
    "x": 30,
    "y": 80,
    "rotate": 30,
    "scaleX": 40,
    "shearX": 0,
    "limit": 5000,
    "inertia": 100,
    "strength": 90,
    "damping": 70,
    "mass": 130,
    "wind": 0,
    "gravity": 0,
    "mix": 1.0
  }
]
```

Animation timeline for keyed properties (per-frame mix changes, for example):

```json
"physics": {
  "santa_belly_jiggle": {
    "mix": [
      { "time": 0, "value": 0 },
      { "time": 0.1, "value": 1.0 }
    ]
  }
}
```

## The skill's physics emission

`scripts/physics_constraints.py` does policy-gated candidate detection and emission. The bundled policy lives at `assets/physics_policy.json` and defines max constraints per symbol, default-on roles, review-only roles, allowed wardrobe semantics, normalized field ranges, and the preview-required flag.

- Default-on roles currently emit constraints only when `--enable-physics` is present: `hair`, `cape`, `cloak`, `tails`, `antennae`, `earrings`, and `dangling_jewelry`.
- Review-only roles are reported as candidates but do not emit constraints: `beard`, `mustache`, `dress`, `skirt`, `robe`, `sleeve`, `scarf`, `ribbon`, `belt`, `chain`, `necklace`, and `wings`.
- Presets are normalized to the policy's Spine 4.2 ranges (`fps` 30-60, sliders 0-100, `mix` 0-1, bounded force/mass values). They are policy seeds and starting points, not empirically tuned simulation values.

### Auto-detection

The driver walks the rig layout looking for bones whose trusted semantic role contains explicit wardrobe/natural-motion keywords. Each match becomes a candidate with evidence, a candidate role, a recommended preset, policy decision, active sliders, and preview requirement. Raw layer-name or bone-name keyword matches are recorded as review-only candidates unless a reviewed physics plan explicitly forces emission. It does not infer physics from visual style alone.

```
hair, beard, mustache, dress, skirt, robe, cloak, cape,
sleeve, scarf, ribbon, belt, chain, necklace, earrings,
dangling_jewelry, tails, wings, antennae
```

If no auto-detected candidates exist, supply a custom plan via `--physics-plan plan.json`:

```json
[
  {
    "bone": "JP1_grand_earring_bone",
    "preset": "earring",
    "name": "grand_earring_swing",
    "reviewed": true
  },
  {
    "bone": "DRAGON_tail_tip_bone",
    "preset": "tail",
    "reviewed": true,
    "overrides": {
      "strength": 70,
      "damping": 30
    }
  }
]
```

User entries override any auto-detected entry for the same bone.

### Enable in the driver

```
python scripts/build_spine_package.py \
    --layer-dir <layers> --family hp_symbol --rank 1 \
    --doc-width 178 --doc-height 178 \
    --enable-physics --physics-plan <plan.json> \
    --out-dir <out>
```

Default is **off** — physics is opt-in. Without `--enable-physics`, candidates are recorded for review but no top-level `"physics"` block is emitted. With `--enable-physics`, only trusted semantic default-on roles or reviewed forced plan entries emit constraints, invalid bone references and over-budget constraint counts fail validation, and review-only roles remain candidates.

`validation_report.json` records `physics_candidates`, `physics_review_required`, `physics_constraints_emitted`, `zero_length_bone_warnings`, `physics_max_constraint_violations`, `physics_active_sliders`, `physics_policy_snapshot`, and runtime/preview requirement fields. A clean structural report is not runtime proof or art approval.

## Reference scale (avoid the silent gotcha)

The official doc calls out a gotcha: when the entire skeleton is scaled (e.g., during Import Data), most values scale to match, but physics values like `gravity` and `wind` are forces — they don't scale automatically. If you scale a skeleton to 10% size, you also need to set the skeleton's `referenceScale` from 100 to 10 to keep physics behaving identically. The bundled emitter assumes 100% reference scale (default 100). For current 4.x runtimes loading a scaled skeleton, set the skeleton's `referenceScale` in the editor.

## Warnings to watch for

The official doc lists three warnings that may surface in Spine Editor:

1. **Zero-length bone** — physics constraints with `rotate`, `scaleX`, or `shearX` > 0 on a zero-length bone do nothing. Set the bone's length in the editor.
2. **Nothing is active** — all of `x`, `y`, `rotate`, `scaleX`, `shearX` set to 0 means the constraint is a no-op. Either remove it or activate at least one slider.
3. **Constraint not in a skin affecting a skin bone** — for multi-skin rigs, constraints have to live in the same skin as the bones they affect.

The skill's emitter prevents (2) by default (all presets activate at least one slider). It now detects (1) for generated zero-length bones when `rotate`, `scaleX`, or `shearX` are active and marks the package as review-required. Skin-specific constraint membership (3) still needs Spine Editor review.

## Performance

Physics is real-time simulation. Cost per skeleton scales with the number of physics constraints, the FPS update rate, and the bone count affected. For slot games with ~30 symbols on screen:

- 1–3 physics constraints per symbol is fine on mid-range mobile.
- 5+ per symbol starts to compete for CPU with other systems (mesh deform, IK).
- FPS 60 is the conventional default; FPS 30 cuts cost in half if the slot's overall motion is gentle.

The bundled presets start at the lighter end of this range; adjust `fps` and `mass` during visual review.

## What the skill bundles vs what stays in the editor

**Bundled:**

- Auto-detection of trusted semantic physics candidates, plus review-only raw keyword candidates.
- 11 bounded preset seeds for common slot-motion archetypes.
- Closed-schema, type/range-validated custom-plan overrides via `--physics-plan`.
- JSON emission that passes the strict Spine 4.x compatibility checks.
- Animation-timeline keying support (e.g., mix from 0 → 1.0 over the win's first 0.15s so physics activates with the action).

**Editor-side:**

- Visual tuning of strength / damping / mass while watching the simulation play. The official doc is explicit that animators iterate the sliders against a test animation. The bundled defaults are starting points, not final values.
- Skin-specific physics constraints (constraints that activate only when a specific skin is active).
- Deterministic mode (editor-only; runtime is always non-deterministic by default).

## Sources

- [Spine: Physics constraints (official)](http://en.esotericsoftware.com/spine-physics-constraints) — properties, behavior, warnings, limitations.
- [Spine blog: 4.2 — The physics revolution](https://esotericsoftware.com/blog/Spine-4.2-The-physics-revolution) — design rationale, examples.
- [spine-runtimes 4.2 CHANGELOG](https://github.com/EsotericSoftware/spine-runtimes/blob/4.2/CHANGELOG.md) — release notes for the 4.2 physics features.
