# Spine 4.3 JSON Contract

This is the current default contract for the portable `spine-slot-animation` compiler. New packages should target Spine Editor `4.3.04` and Spine Player `4.3.1` unless a project explicitly pins a different supported 4.x line.

This is not a license to hand-edit final Spine JSON. The compiler emits JSON, validators prove the shape, Spine CLI imports with the matching editor version, and Christian reviews the result.

## Version And Import Rule

`skeleton.spine` is the Spine editor version for the data. Official Spine docs say exported JSON/binary data imports back into Spine only with the same editor version that exported the data. For tool-generated data, this means:

- generate directly for the target JSON structure;
- set `skeleton.spine` to the target editor version only when the emitted structure is valid for that target;
- import with the same version recorded in `skeleton.spine`;
- use the resulting `.spine` project file as the bridge to newer editor versions.

Do not fix a mismatch by changing `"3.8.99"` or `"4.2.x"` to `"4.3.04"` after the fact.

## Current Required Shape

The public Spine JSON docs for current 4.x preserve the 4.x structures the portable compiler already emits:

- `skins` is an array of skin objects, not the old 3.8 object map.
- Bone `rotate` timeline keys use `value`, not legacy `angle`.
- Slot color timelines use `rgba`; two-color timelines use `rgba2` only when the setup slot has `dark`.
- Mesh attachments use `uvs`, `triangles`, `vertices`, `hull`, optional nonessential `edges`, `width`, and `height`.
- Weighted meshes encode each vertex as `boneCount`, then repeated `bone index`, `bind position X`, `bind position Y`, `weight`.
- Linked meshes must stay in the same slot as their source mesh and use `skin`, `parent`, and optional `deform`.
- Deform timelines live under `animations -> deform -> skinName -> slotName -> meshName`.
- Path constraints target slots and use `position`, `spacing`, and `mix` animation timelines.

The compiler must keep unknown/advanced features gated until the 4.3 validator and Spine CLI import prove them.

## Default Generator Path

For new work:

```powershell
python scripts/build_spine_package.py `
  --layer-dir <layers> `
  --family <family> `
  --out-dir <out> `
  --target-spine-version 4.3.04 `
  --build-preview `
  --spine-editor-zip
```

Then import through the generated handoff script:

```powershell
powershell -ExecutionPolicy Bypass -File .\CREATE_SPINE_PROJECT.ps1
```

The script reads `shared_symbols.json`, verifies the JSON version, and invokes Spine CLI with that same version.

## Legacy Paths

- `3.8.99` / `v10_linear` is legacy proof output only. Regenerate with the portable builder for new 4.3 work.
- 4.2 packages are supported only as an older 4.x line. If a package is already tagged `4.2.x`, import it with 4.2 first to create a `.spine` project, then open the project in 4.3.
- The old `references/spine_42_contract.md` remains as migration evidence for diagnosing legacy 4.2/3.8 failures, not as the default target for new generation.

## Verification Gates

A 4.3 package is not considered ready until:

- `validation_report.json` is `ok`;
- the JSON version in `shared_symbols.json` matches the CLI import version;
- `preview.html` loads with the configured 4.3 Spine Player;
- `CREATE_SPINE_PROJECT.ps1` or `scripts/create_spine_project.py` creates a `.spine` project in a licensed Spine environment;
- any advanced mesh/weight/skin/physics/event feature passes its own policy gate and review.

Without local Spine CLI, the plugin can validate structure and prepare the handoff, but it cannot honestly claim Spine Editor import proof.
