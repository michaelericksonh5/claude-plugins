# Visual Remediation Loop

Claude can use vision to review previews. The production gap was not "Claude cannot see"; it was that the skill had no deterministic loop for turning visual observations into safe compiler actions.

The loop is:

```text
compile -> build preview -> create visual packet -> Claude/artist reviews -> remediation report -> recompile -> repeat
```

## Tool

Use:

```powershell
python scripts/visual_remediation_loop.py `
  --package-dir <compiled_package_dir> `
  --out-dir <review_dir> `
  --render-frames
```

This writes:

- `visual_remediation_packet.json`
- `VISUAL_REMEDIATION_PROMPT.md`
- optional `frames/qa_report.json` and setup PNGs from `render_preview_frames.py`

Claude or the artist then inspects `preview.html` and the frame packet and writes a structured `visual_review.json`:

```json
{
  "schema": "spine_slot_animation_visual_review_v1",
  "reviewer": "claude_or_artist",
  "recipe_type": "hp_symbol",
  "package": "path/to/package",
  "issues": [
    {
      "code": "too_flashy",
      "severity": "warn",
      "animation": "win",
      "evidence": "Glow overwhelms the character at the win peak."
    }
  ]
}
```

Apply the review:

```powershell
python scripts/visual_remediation_loop.py `
  --review <visual_review.json> `
  --out-dir <review_dir>
```

If safe control fixes exist, the tool writes `visual_remediation.controls.json`. Recompile with that controls file, rebuild the preview, and run another visual review iteration.

## Safe Control Fixes

These visual findings can map to bounded compiler controls:

- `too_flashy`
- `not_flashy_enough`
- `too_bouncy`
- `not_bouncy_enough`
- `idle_too_fast`
- `idle_too_slow`
- `motion_too_strong`
- `motion_too_subtle`
- `feature_active_too_strong`
- `feature_active_too_subtle`

The generated controls stay inside `assets/recipe_controls_schema.json`. The script never writes Spine JSON or keyframes by hand.

## Blocking Visual Findings

These findings block remediation instead of becoming fake controls:

- `missing_attachment`
- `broken_preview`
- `off_center`
- `wrong_z_order`
- `expression_visible_at_rest`
- `expression_wrong_timing`
- `mesh_tearing`
- `rubbery_weights`
- `deform_needed`
- `linked_mesh_needed`
- `path_constraint_needed`
- `bad_silhouette`
- `style_mismatch`

Blocking findings require a compiler, rig, source-layer, mesh-plan, or animator fix. For example, mesh tearing needs reviewed topology/weights, not a lower `motion_strength`; wrong z-order needs draw-order/layer correction, not lower sparkle.

## Approval Boundary

This is an AI visual QA and remediation loop. It can reject bad previews, suggest bounded fixes, and prevent unsafe issues from being hidden by cosmetic controls.

It is not final production art approval. Chris or an assigned art owner still owns final signoff for acting, style, timing, mesh weights, and production export.

## Relation To Runtime Proof

`preview.html` and the browser runtime acceptance probe prove the package loads in Spine Player. The visual remediation loop evaluates whether the loaded result looks right enough to keep iterating.

Both are needed:

- Runtime proof catches blank canvas, missing runtime assets, and loader/runtime errors.
- Visual remediation catches bad poses, bad timing, overdone glow, mesh tearing, expression polarity, and art-direction issues.
