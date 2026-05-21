# Intake: PSD and PNG → Compiler Input

How a Photoshop source becomes a clean folder of per-layer PNGs plus an `h5g_layer_manifest.json` that the compiler can consume. This file is the layer-naming contract, the boilerplate filtering rule, the visible-vs-hidden rule, the parent-local bone math, and the overlay polarity contract.

## Two intake paths

Both produce the same downstream contract (`h5g_layer_manifest.json` + per-layer PNGs).

### A. PSD-native intake (preferred)

Read the `.psd` directly via `psd-tools`. Best when the build machine can reach the PSD over the network and live effects / smart-object fidelity is acceptable.

```powershell
uv run python research/psd_native_intake.py `
  "G:\artSource\<game>\working\<sku>\psd" `
  "research\generated\psd_native_intake_runs\<batch_name>"
```

Outputs one `<symbol>/h5g_layer_manifest.json` + `layers/` + `psd_composite.png` per PSD. Skips invisible layers automatically. Network-drive I/O is slow (~5 min for 17 PSDs).

### B. Photoshop JSX export

Run an ExtendScript inside Photoshop that walks the layer tree and writes per-layer PNGs plus the manifest. Use when:

- The `.psd` lives on a network share unreachable from the build machine.
- Live effects, smart-object fidelity, adjustment / fill layers, text, or clipping mask compositing matters.
- `psd-tools` can't faithfully rasterise the source.

The H5G reference scripts:

```text
photoshop2spine/run_photoshop_export.bat
photoshop2spine/run_batch_export_santa_pop_win.bat
photoshop2spine/export_h5g_layers_to_spine_source.jsx
photoshop2spine/batch_export_psd_folder.jsx
```

For arbitrary studios, write an equivalent JSX that emits the same manifest schema described below.

## The layer manifest schema

```json
{
  "schema": "h5g_photoshop_layer_manifest_v1",
  "source_psd": "...HP1.psd",
  "document": { "name": "HP1.psd", "width": 178, "height": 178, "resolution": 72, "mode": "DocumentMode.RGB" },
  "layer_count": 14,
  "layers": [
    {
      "index": 0,
      "name": "HP1_BG",
      "safe_name": "HP1_3_art_layer_HP1_BG",
      "file": "layers/HP1_3_art_layer_HP1_BG.png",
      "layer_kind": "LayerKind.SMARTOBJECT",
      "visible": true,
      "opacity": 100,
      "blend_mode": "BlendMode.NORMAL",
      "bounds": {
        "left": 18, "top": 18, "right": 157, "bottom": 156,
        "width": 139, "height": 138,
        "center_x": 87.5, "center_y": 87
      },
      "z": 2
    }
  ]
}
```

- `bounds.left/top/right/bottom` are doc-relative (PSD origin top-left).
- `bounds.center_x` / `center_y` is the doc-relative layer center used downstream for bone placement.
- `z` is the layer's draw order (lower = bottom).
- `safe_name` is the file-safe layer name used for the PNG filename.

## Layer naming contract

Artists encode the rig role in the layer name. The pipeline infers semantic role from the name, not from layer index.

Canonical patterns (H5G convention; adapt for other studios with the same role semantics):

| Layer name pattern | Semantic role | Rig role | Notes |
|---|---|---|---|
| `<sym>_BG` | `background` | inner background gradient/glow | Inside the frame |
| `<sym>_frame_glow` | `frame_glow` | frame glow | Soft outer glow around the frame |
| `<sym>_frame` | `frame` | outer decorative frame | Gold / decorative border |
| `<sym>_santa`, `<sym>_<character>_body` | `character_body` | character | Main body of a character symbol |
| `<sym>_head` | `head` | head | Head with the **default expression baked in** (open eyes, neutral mouth) |
| `<sym>_head_eyes_blink` | `eyes` | eye-blink overlay | Closed-eye art; **hidden at rest**, flashes during blink |
| `<sym>_head_eyes_side` | `eyes` | eye-look overlay | Sideways-look art; rarely used; often invisible in PSD |
| `<sym>_<character>_laugh` | `mouth/laugh` | mouth-O overlay | Open-mouth art; **hidden at rest**, flashes during win |
| `<sym>_<character>_hat_top` | `accessory_top` | hat top | Hat piece that pops above the frame |
| `<sym>_<character>_hat` | `accessory` | hat base | Hat base, parented to head |
| `<sym>_hand_L`, `<sym>_hand_R` | `hand` | left/right hand | Hands |
| `<sym>_hand_pinky_R` | `hand_detail` | finger | Finger detail layers |
| `<sym>_arm_L`, `<sym>_arm_R` | `arm` | left/right arm | Arms |
| `<sym>_<vfx>_001`..`_NNN` | `vfx` | numbered VFX sequence | Group into one slot with attachment-swap timeline |
| `<sym>_key`, `<sym>_key_sheen_<N>` | `body` + `sheen` | base + sheen layers | Multiple highlight layers over a base |

For unfamiliar PSDs, run a contextual layer interpreter (e.g., the H5G `contextual_layer_interpreter.py`) before defining rigs. It returns semantic role + rig role + parent hint + pivot hint + animation uses + confidence per layer. Don't rely on exact-name matching alone — use the interpreter to handle naming variation.

## Boilerplate filtering

Photoshop auto-generates two kinds of layers that are NOT real art:

- `Background` — the default opaque solid Photoshop adds to every new document.
- `Layer N` (where N is a digit) — auto-named empty / scratch layers from rasterisation or unnamed adjustments.

Both must be filtered at intake. A layer is boilerplate iff its name matches `^background$` or `^layer\s*\d+$` (case-insensitive). Real symbol layers always carry the symbol-code prefix (e.g., `HP1_*`).

The intake step writes the list of skipped boilerplate names to its log. If these aren't filtered, they render as opaque black/grey rectangles behind the symbol.

## Visible vs invisible layers

PSDs often include hidden reference layers (master composites, alternate states, artist notes). **Skip invisible layers at intake** unless explicitly directed to include them.

In the H5G reference PSDs:

- `HP1_all` — invisible smart-object backup of the whole symbol. Skip.
- `HP1_head_eyes_side` — invisible alternate-look state. Skip unless an animation uses it.

## Sidecar JSON

A Photoshop-to-Spine export script may emit a sidecar `<symbol>.json` alongside the per-layer PNGs, describing slots / skins / attachments. Treat it as **hint data, not placement truth**.

Specifically:

- Sidecar `attachment.x` / `attachment.y` is the AUTHORED SPINE ATTACHMENT OFFSET, not the PSD layer center. Using it as layer placement causes off-center symbols.
- Use the Photoshop manifest's `bounds.center_x` / `bounds.center_y` as the doc-relative layer center.
- Then parent-localise during rig construction (see below).

## Parent-local bone placement (critical)

A bone's `x` and `y` are LOCAL to its parent bone, not absolute to the document. Spine computes `bone.world = parent.world × local`. If intake writes each layer's doc-relative center as the local x/y for a bone whose parent is also offset, the parent's offset is double-counted on every nested child and the rig explodes off-center.

Correct intake algorithm:

```text
For each part with a parent:
    parent_doc_x = parent_part.bounds.center_x
    parent_doc_y = parent_part.bounds.center_y
    this_doc_x   = this_part.bounds.center_x
    this_doc_y   = this_part.bounds.center_y
    bone.x = this_doc_x - parent_doc_x
    bone.y = (doc_height - this_doc_y) - (doc_height - parent_doc_y)
           = parent_doc_y - this_doc_y  # Y-flip from PSD top-left to Spine bottom-up
```

(Spine's Y axis points up; PSD's Y axis points down. Flip when converting.)

Symptom of getting this wrong: "Picasso" rest pose — parts scattered off-center at rest even though the per-frame animation looks reasonable in isolation.

## Required vs optional layers per family

Per-family contracts live in `references/families.md`. As a general guide:

- **HP / character symbols:** require `*_head`. Optional: `*_eyes_blink`, `*_<character>_laugh`, `*_hand_*`, `*_arm_*`, `*_hat_top`, `*_BG`, `*_frame`, `*_frame_glow`.
- **LP / letter symbols:** require the letter body. Optional: shadow, highlight.
- **JP / jackpot symbols:** require the star/badge body. Optional: tier text overlay, sheen.
- **WD / wild symbols:** require the body. Optional: shimmer, sparkle.
- **Meter:** require base + state-stop pairs.
- **Transition / celebration:** require the relevant frames; treat as VFX sequences.

If a required layer is missing, the compiler should fail the per-package validation report with a clear message identifying the missing layer. Don't fabricate a missing layer; ask the user to provide it.

## What the compiler reads vs what intake produces

The compiler reads only the per-layer PNGs and the layer manifest from the intake output. It does NOT read Perforce, `G:\artSource`, or production export paths. The intake step is the boundary between source art and pipeline output.

This separation means: intake can run from a network share, compile runs from a local fast disk, and source art is never modified.

## Overlay polarity at intake

The intake step is where the overlay polarity decision is recorded for the compiler. For each detected overlay layer (eye-blink, mouth-O, hat-top in some cases), write into the manifest or a sidecar that the layer's slot should have setup `color: "ffffff00"` (alpha 0).

If intake doesn't flag overlay polarity, the compiler defaults overlay slots to visible — and the symbol shows closed eyes / open mouth at rest, which is the opposite of what's intended.

Detection heuristic: layer name contains `blink`, `laugh`, or `eyes`; or semantic role from the layer interpreter is `eyes` or `mouth/laugh`.

## When to skip PSD intake entirely

If the user already has per-layer PNGs from a previous export and the manifest schema looks right, skip intake and run the compiler directly. The signal: a folder of `*.png` files alongside a `h5g_layer_manifest.json`. Just confirm:

- Layer count matches PNG count.
- No boilerplate layers slipped through.
- Document `width` / `height` looks plausible (typically 178×178, 200×200, or similar for slot symbols).

## What NOT to do at intake

- Do not write to source-art directories (`G:\artSource\` in H5G). Artists own that workspace.
- Do not modify the source PSD.
- Do not silently include invisible layers — surface them and let the user decide.
- Do not invent rig roles for layers whose names don't match the contract — flag them as `unknown` and let the user reclassify.
- Do not run intake against PSDs that haven't been approved by the source-layer manifest review process (the H5G reference treats PSD/PSB rows as review-gated by default).
