#!/usr/bin/env python3
"""Portable rig layout generator.

Takes per-layer interpretations (from interpret_layers.py) plus PNG-derived
bounds (or a Photoshop manifest) and emits a rig_layout.json that the layered
rig compiler — or the bundled portable compose_animations.py + build_atlas.py
— can consume to assemble a Spine 4.2 skeleton.

The layout encodes:
  - bone tree with parent-local placement (Y-flipped from PSD top-left to
    Spine bottom-up), per references/intake.md
  - one slot per visible layer in z-order (lower z = drawn first = back)
  - region attachment metadata (the actual width/height + offset stays at 0
    once the bone sits at the layer's visual center)
  - setup slot color: "ffffff00" for layers flagged alpha_polarity=hidden_at_rest
  - blend mode (always "normal" per H5G policy; source blend recorded but stripped)
  - per-layer animation_uses, so compose_animations.py knows which timelines
    touch which bones

USE
  python build_rig_layout.py \
      --interpretation <interpret_layers.json> \
      --doc-width 178 --doc-height 178 \
      --out <rig_layout.json>

  python build_rig_layout.py \
      --manifest <h5g_layer_manifest.json> \
      --out <rig_layout.json>

If a manifest is given, doc-width / doc-height come from the manifest's
document section and per-layer bounds come from the manifest. Otherwise the
caller must supply doc-width / doc-height; bounds fall back to "place at
document center" which produces a working rig that still needs adjustment.

The output schema is:

{
  "schema": "spine_slot_animation_rig_layout_v1",
  "doc": { "width": 178, "height": 178 },
  "root_bone": "root",
  "bones": [
    {
      "name": "root"
    },
    {
      "name": "HP3_BG_bone",
      "parent": "root",
      "x": 0.5, "y": -0.5,
      "rotation": 0,
      "layer_name": "HP3_BG",
      "semantic_role": "background",
      "rig_role": "root_static",
      "pivot_hint": "center"
    },
    ...
  ],
  "slots": [
    {
      "name": "HP3_BG_slot",
      "bone": "HP3_BG_bone",
      "attachment": "parts/HP3_BG",
      "setup_color": "ffffffff",
      "blend": "normal",
      "z": 0,
      "alpha_polarity": "visible_at_rest",
      "animation_uses": ["idle"]
    },
    ...
  ],
  "attachments": [
    {
      "slot": "HP3_BG_slot",
      "name": "parts/HP3_BG",
      "path": "parts/HP3_BG",
      "type": "region",
      "x": 0, "y": 0,
      "width": 139, "height": 138
    },
    ...
  ]
}
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _parent_role_to_layer(parent_hint: str, layers_by_role: dict[str, list[dict]]) -> str | None:
    """Resolve a parent_hint like 'head' / 'arm_L_or_body' / 'body_or_root' to
    an actual layer name present in the rig. Returns None if no match (caller
    falls back to root)."""
    # Direct semantic-role matches
    direct = {
        "head": ["head", "character_body"],
        "frame": ["frame", "back_frame", "front_frame"],
        "frame_or_root": ["frame", "back_frame"],
        "front_frame_or_root": ["front_frame", "frame"],
        "body_or_root": ["character_body", "symbol_body"],
        "body_part": ["character_body", "symbol_body", "body_part"],
        "arm_L_or_body": ["arm_left", "character_body", "symbol_body"],
        "arm_R_or_body": ["arm_right", "character_body", "symbol_body"],
        "hand": ["hand_left", "hand_right", "hand"],
    }
    if parent_hint in direct:
        for sem in direct[parent_hint]:
            if layers_by_role.get(sem):
                return layers_by_role[sem][0]["name"]
        return None
    if parent_hint == "root" or parent_hint == "none":
        return None
    if parent_hint in layers_by_role and layers_by_role[parent_hint]:
        return layers_by_role[parent_hint][0]["name"]
    return None


def _bone_name(layer_name: str) -> str:
    """Stem with _bone suffix."""
    return f"{Path(layer_name).stem}_bone"


def _slot_name(layer_name: str) -> str:
    return f"{Path(layer_name).stem}_slot"


def _attachment_name(layer_name: str) -> str:
    return f"parts/{Path(layer_name).stem}"


def _doc_center(bounds: dict[str, float] | None, doc_w: float, doc_h: float) -> tuple[float, float]:
    """Return doc-relative center (x, y) for a layer. Falls back to doc center
    if bounds aren't supplied."""
    if bounds and "center_x" in bounds and "center_y" in bounds:
        return float(bounds["center_x"]), float(bounds["center_y"])
    if bounds and "left" in bounds and "right" in bounds:
        return (
            (float(bounds["left"]) + float(bounds["right"])) / 2,
            (float(bounds["top"]) + float(bounds["bottom"])) / 2,
        )
    return doc_w / 2.0, doc_h / 2.0


def _layer_size(bounds: dict[str, float] | None, doc_w: float, doc_h: float) -> tuple[int, int]:
    if bounds and "width" in bounds and "height" in bounds:
        return int(round(float(bounds["width"]))), int(round(float(bounds["height"])))
    if bounds and "left" in bounds and "right" in bounds:
        return (
            int(round(float(bounds["right"]) - float(bounds["left"]))),
            int(round(float(bounds["bottom"]) - float(bounds["top"]))),
        )
    return int(doc_w), int(doc_h)


def build_rig_layout(
    interpretation: dict,
    doc_w: float,
    doc_h: float,
) -> dict:
    """Construct the rig_layout dict.

    interpretation: output of interpret_layers.py (a dict containing 'layers').
    """
    raw_layers = [L for L in interpretation.get("layers", []) if L.get("visible", True)]
    raw_layers = [L for L in raw_layers if L.get("rig_role") != "filtered"]

    # Stable sort: lower z first (draws at bottom). If z absent, fall back to
    # the input order.
    indexed = list(enumerate(raw_layers))
    indexed.sort(key=lambda pair: (pair[1].get("z") if pair[1].get("z") is not None else pair[0]))
    layers = [L for _, L in indexed]

    # Index by semantic_role for parent resolution
    by_role: dict[str, list[dict]] = {}
    for L in layers:
        by_role.setdefault(L["semantic_role"], []).append(L)

    bones: list[dict[str, Any]] = [{"name": "root"}]
    slots: list[dict[str, Any]] = []
    attachments: list[dict[str, Any]] = []

    # Compute doc-relative centers for parent localisation
    centers: dict[str, tuple[float, float]] = {}
    for L in layers:
        cx, cy = _doc_center(L.get("bounds"), doc_w, doc_h)
        centers[L["name"]] = (cx, cy)

    for L in layers:
        layer_name = L["name"]
        bone_name = _bone_name(layer_name)
        slot_name = _slot_name(layer_name)
        att_name = _attachment_name(layer_name)

        parent_layer = _parent_role_to_layer(L.get("parent_hint", "root"), by_role)
        parent_bone = _bone_name(parent_layer) if parent_layer else "root"

        # Parent-local placement: child_doc - parent_doc, with Y flip
        child_x, child_y = centers[layer_name]
        if parent_layer and parent_layer in centers:
            parent_x, parent_y = centers[parent_layer]
        else:
            parent_x, parent_y = doc_w / 2.0, doc_h / 2.0
        local_x = child_x - parent_x
        # PSD Y points down; Spine Y points up. Flip when localising.
        local_y = parent_y - child_y

        bones.append({
            "name": bone_name,
            "parent": parent_bone,
            "x": round(local_x, 3),
            "y": round(local_y, 3),
            "rotation": 0,
            "layer_name": layer_name,
            "semantic_role": L["semantic_role"],
            "rig_role": L["rig_role"],
            "pivot_hint": L.get("pivot_hint", "center"),
        })

        setup_color = "ffffff00" if L.get("alpha_polarity") == "hidden_at_rest" else "ffffffff"

        slots.append({
            "name": slot_name,
            "bone": bone_name,
            "attachment": att_name,
            "setup_color": setup_color,
            "blend": "normal",
            "z": L.get("z"),
            "alpha_polarity": L.get("alpha_polarity", "visible_at_rest"),
            "animation_uses": list(L.get("animation_uses", [])),
            "semantic_role": L["semantic_role"],
            "rig_role": L["rig_role"],
        })

        w, h = _layer_size(L.get("bounds"), doc_w, doc_h)
        attachments.append({
            "slot": slot_name,
            "name": att_name,
            "path": att_name,
            "type": "region",
            "x": 0,
            "y": 0,
            "width": w,
            "height": h,
            "layer_name": layer_name,
        })

    return {
        "schema": "spine_slot_animation_rig_layout_v1",
        "doc": {"width": float(doc_w), "height": float(doc_h)},
        "root_bone": "root",
        "bones": bones,
        "slots": slots,
        "attachments": attachments,
    }


def _load_manifest(path: Path) -> tuple[dict, float, float]:
    """Load a Photoshop layer manifest and return (interpretation-shape dict,
    doc_w, doc_h)."""
    data = json.loads(path.read_text())
    doc = data.get("document", {})
    doc_w = float(doc.get("width", 256))
    doc_h = float(doc.get("height", 256))
    # We need to run interpret on the manifest layers ourselves. Do it inline
    # to avoid requiring two CLI calls.
    from interpret_layers import interpret_layers as _interpret  # type: ignore
    names = [Path(L.get("file", L.get("name", ""))).stem for L in data.get("layers", [])]
    interps = _interpret(names, data.get("layers", []))
    from dataclasses import asdict
    return {"layers": [asdict(i) for i in interps]}, doc_w, doc_h


def main() -> int:
    p = argparse.ArgumentParser(description="Build a rig_layout.json from layer interpretations.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--interpretation", help="Path to interpret_layers.py JSON output.")
    g.add_argument("--manifest", help="Path to h5g_layer_manifest.json (will be interpreted internally).")
    p.add_argument("--doc-width", type=float, help="Document width (required if --interpretation lacks bounds).")
    p.add_argument("--doc-height", type=float, help="Document height (required if --interpretation lacks bounds).")
    p.add_argument("--out", required=True, help="Where to write rig_layout.json")
    args = p.parse_args()

    if args.manifest:
        # Make sibling import work
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        interp, doc_w, doc_h = _load_manifest(Path(args.manifest))
    else:
        interp = json.loads(Path(args.interpretation).read_text())
        if args.doc_width is None or args.doc_height is None:
            # Try to infer from any bounds present
            doc_w, doc_h = 256.0, 256.0
            for L in interp.get("layers", []):
                b = L.get("bounds")
                if b and "right" in b and "bottom" in b:
                    doc_w = max(doc_w, float(b["right"]))
                    doc_h = max(doc_h, float(b["bottom"]))
            print(f"warning: --doc-width/--doc-height not supplied; inferred {doc_w}x{doc_h} from bounds", file=sys.stderr)
        else:
            doc_w, doc_h = float(args.doc_width), float(args.doc_height)

    layout = build_rig_layout(interp, doc_w, doc_h)
    Path(args.out).write_text(json.dumps(layout, indent=2))
    print(f"wrote {args.out}")
    print(f"  doc {doc_w}x{doc_h}, {len(layout['bones'])-1} bones, {len(layout['slots'])} slots, {len(layout['attachments'])} attachments")
    return 0


if __name__ == "__main__":
    sys.exit(main())
