#!/usr/bin/env python3
"""Portable layer interpreter for slot-machine Spine animation work.

Given a folder of per-layer PNG files (optionally a Photoshop layer manifest
with bounds) for a single symbol, infer for each layer:

  - semantic_role: what this art represents (head, eyes, mouth/laugh, hand,
    frame, frame_glow, BG, sparkle, glow, body, sheen, accessory_top, ...)
  - rig_role: how Spine should treat the layer (root_static, character_part,
    body_part, accessory, overlay, vfx, frame_part, ...)
  - parent_hint: which other layer's bone should be the parent
  - pivot_hint: where the bone should sit relative to the layer ("center",
    "top_edge", "bottom_edge", "left_edge", "right_edge", or a semantic anchor
    like "wrist", "shoulder")
  - blend_hint: "normal" (default — H5G strips additive). Records the suspected
    source blend so a future art-direction-approved pass can re-enable.
  - alpha_polarity: "visible_at_rest" (default) or "hidden_at_rest" for
    expression overlays (blink, laugh, side-eyes). Drives setup slot color.
  - animation_uses: list of standard animation slots this layer participates
    in (idle, breathe, land, win, smart). Used by the animation composer.
  - confidence: 0.0-1.0 score for the assignment
  - evidence: human-readable list of why this assignment was made

USE
  python interpret_layers.py --layer-dir <path>
  python interpret_layers.py --manifest <h5g_layer_manifest.json>
  python interpret_layers.py --names HP1_head HP1_head_eyes_blink ...

Combines with `classify_family.py` to pick a recipe family and pass through to
`build_rig_layout.py` which emits the rig_layout.json the compiler reads.

The interpreter is deterministic — same inputs always produce same output. It
never guesses pixel content; everything is name-and-bounds-driven.

EXIT
  0 on successful interpretation.
  2 on unparseable / empty input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Boilerplate Photoshop layers to filter at intake — see references/intake.md.
BOILERPLATE_PATTERNS = [
    re.compile(r"^background$", re.IGNORECASE),
    re.compile(r"^layer\s*\d+$", re.IGNORECASE),
]


# --- Semantic role patterns ---------------------------------------------------
# Each pattern: (regex against the per-layer suffix after stripping symbol code,
# semantic_role, rig_role, parent_hint, pivot_hint, alpha_polarity,
# blend_hint, animation_uses, confidence)
SEMANTIC_PATTERNS = [
    # ---- Character symbol composition ----
    (r"^(head_)?eyes?_(blink|blinking)$", "eyes_blink", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["idle", "win"], 0.95),
    (r"^(head_)?blink$", "eyes_blink", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["idle", "win"], 0.95),
    (r"^(head_)?eyes?_(side|side_eye|sideeye|side_eyes|sideeyes)$", "eyes_side", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["win"], 0.85),
    (r"^(head_)?(side_eye|sideeye)$", "eyes_side", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["win"], 0.85),
    (r"^(head_)?eyes?_(closed|close|shut)$", "eyes_closed", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["idle", "win"], 0.85),
    (r"^head$", "head", "character_part", "body_or_root", "center",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.95),
    (r"^.*_(laugh|laughing)$", "mouth_laugh", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["win"], 0.95),
    (r"^.*_(smile|smiling|grin)$", "mouth_smile", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["idle", "win"], 0.85),
    (r"^.*_(mouth_)?(open|talk|talking|sing|singing|mouth_open)$", "mouth_open", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["win"], 0.85),
    (r"^.*_(mouth_)?(closed|close|shut|mouth_closed)$", "mouth_closed", "overlay", "head", "center",
     "hidden_at_rest", "normal", ["idle", "win"], 0.8),
    (r"^.*_mouth$", "mouth", "character_part", "head", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.7),
    (r"^.*_hat_top$", "hat_top", "accessory_top", "head", "bottom_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.9),
    (r"^.*_hat$", "hat_base", "accessory", "head", "bottom_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^.*_cap_top$", "cap_top", "accessory_top", "head", "bottom_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.9),
    (r"^.*_crown_top$", "crown_top", "accessory_top", "head", "bottom_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.9),
    (r"^.*_helmet_top$", "helmet_top", "accessory_top", "head", "bottom_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.9),
    (r"^.*_(ponytail|braid|hair)$", "hair", "wardrobe", "head", "top_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.9),
    (r"^(ponytail|braid|hair)$", "hair", "wardrobe", "head", "top_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.9),
    (r"^(.+_)?beard$", "beard", "wardrobe", "head", "center",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^(.+_)?(mustache|moustache)$", "mustache", "wardrobe", "head", "center",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^(.+_)?dress$", "dress", "wardrobe", "body_or_root", "top_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^(.+_)?skirt$", "skirt", "wardrobe", "body_or_root", "top_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^(.+_)?robe$", "robe", "wardrobe", "body_or_root", "top_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^(.+_)?cloak$", "cloak", "wardrobe", "body_or_root", "top_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^(.+_)?cape$", "cape", "wardrobe", "body_or_root", "top_edge",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^(.+_)?sleeve$", "sleeve", "wardrobe", "arm_L_or_body", "shoulder",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.8),
    (r"^(.+_)?scarf$", "scarf", "wardrobe", "body_or_root", "center",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.8),
    (r"^(.+_)?ribbon$", "ribbon", "wardrobe", "body_or_root", "center",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.8),
    (r"^(.+_)?belt$", "belt", "wardrobe", "body_or_root", "center",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.8),
    (r"^(.+_)?chain$", "chain", "wardrobe", "body_or_root", "top_edge",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.8),
    (r"^(.+_)?necklace$", "necklace", "wardrobe", "head", "top_edge",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.85),
    (r"^(.+_)?(earring|earrings)$", "earrings", "wardrobe", "head", "top_edge",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.85),
    (r"^(.+_)?(dangling_jewelry|dangly_jewelry|dangling|dangle)$", "dangling_jewelry",
     "wardrobe", "body_or_root", "top_edge", "visible_at_rest", "normal", ["idle", "land", "win"], 0.85),
    (r"^(.+_)?(tail|tails)$", "tails", "character_part", "body_or_root", "top_edge",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.85),
    (r"^(.+_)?(wing|wings)$", "wings", "character_part", "body_or_root", "shoulder",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.85),
    (r"^(.+_)?(antenna|antennae)$", "antennae", "character_part", "head", "bottom_edge",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.85),
    (r"^hand_L$", "hand_left", "character_part", "arm_L_or_body", "wrist",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.9),
    (r"^hand_R$", "hand_right", "character_part", "arm_R_or_body", "wrist",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.9),
    (r"^hand_(pinky|index|thumb|finger)_[LR]?$", "hand_detail", "character_part",
     "hand", "center", "visible_at_rest", "normal", ["win"], 0.7),
    (r"^hand$", "hand", "character_part", "body_or_root", "wrist",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.7),
    (r"^arm_L$", "arm_left", "character_part", "body_or_root", "shoulder",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.85),
    (r"^arm_R$", "arm_right", "character_part", "body_or_root", "shoulder",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.85),
    (r"^arm$", "arm", "character_part", "body_or_root", "shoulder",
     "visible_at_rest", "normal", ["idle", "win"], 0.7),
    (r"^(.+_)?body$", "character_body", "character_part", "root", "center",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    (r"^(santa|elf|bear|tiger|lion|owl|fox|wolf|cat|dog|panda|monkey|rabbit|" +
     r"buffalo|eagle|king|queen|prince|princess|hero|villain|pirate|wizard|" +
     r"dragon|phoenix|unicorn|fairy|mermaid|knight|warrior|samurai|ninja|" +
     r"cowboy|sheriff|witch|vampire|zombie|ghost|alien|robot|cyborg|" +
     r"sphinx|pharaoh|geisha|sumo|leprechaun|gnome|troll|ogre|" +
     r"chef|farmer|miner|sailor|fisherman|hunter|gambler|jester|" +
     r"jaguar|panther|cheetah|leopard|cobra|viper|shark|whale|" +
     r"reindeer|polar|penguin|hippo|elephant|rhino|kangaroo|koala|" +
     r"flamingo|peacock|parrot|toucan|owl|stork|crane|hawk|falcon)$",
     "character_body", "character_part", "root", "center",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.85),
    # ---- Frame and background ----
    (r"^frame_glow$", "frame_glow", "frame_part", "frame_or_root", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.95),
    (r"^frame$", "frame", "frame_part", "root", "center",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.95),
    (r"^back_frame$", "back_frame", "frame_part", "root", "center",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.9),
    (r"^front_frame$", "front_frame", "frame_part", "root", "center",
     "visible_at_rest", "normal", ["idle", "land", "win"], 0.9),
    (r"^glass$", "glass", "frame_part", "front_frame_or_root", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.9),
    (r"^BG$", "background", "root_static", "root", "center",
     "visible_at_rest", "normal", ["idle"], 0.95),
    (r"^bg$", "background", "root_static", "root", "center",
     "visible_at_rest", "normal", ["idle"], 0.95),
    (r"^background$", "background", "root_static", "root", "center",
     "visible_at_rest", "normal", ["idle"], 0.95),
    # ---- Effects ----
    (r"^glow$", "glow", "effect", "root", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.9),
    (r"^sparkle.*$", "sparkle", "effect", "root", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.9),
    (r"^shimmer.*$", "shimmer", "effect", "root", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.9),
    (r"^shine.*$", "shine", "effect", "root", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.85),
    (r"^lit$", "lit", "effect", "root", "center",
     "visible_at_rest", "normal", ["win"], 0.85),
    (r"^.*_sheen(_\d+)?$", "sheen", "effect", "root", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.85),
    (r"^sheen(_\d+)?$", "sheen", "effect", "root", "center",
     "visible_at_rest", "normal", ["idle", "win"], 0.85),
    (r"^symbol_(shadow|highlight)$", "highlight", "effect", "root", "center",
     "visible_at_rest", "normal", ["idle"], 0.9),
    (r"^symbol_body$", "symbol_body", "body_part", "root", "center",
     "visible_at_rest", "normal", ["idle", "breathe", "land", "win"], 0.95),
    # ---- LP letter cards ----
    (r"^(A|K|Q|J|10|9|letter|card)$", "letter", "body_part", "root", "center",
     "visible_at_rest", "normal", ["idle", "land"], 0.9),
    # ---- Jackpot tier text ----
    (r"^(GRAND|MAJOR|MINOR|MINI|tier_?\d+|tier_?text)$", "tier_text",
     "body_part", "root", "center", "visible_at_rest", "normal",
     ["idle", "win"], 0.85),
    # ---- Value text ----
    (r"^(value(_text)?|cash(_text)?|amount|wys)$", "value_text",
     "body_part", "root", "center", "visible_at_rest", "normal",
     ["idle", "win"], 0.85),
    # ---- Meter elements ----
    (r"^meter_bar$", "meter_bar", "body_part", "root", "center",
     "visible_at_rest", "normal", ["idle", "land"], 0.9),
    (r"^state_?(\d+)_?(collect|fill|stop)?$", "meter_state", "state_part",
     "root", "center", "visible_at_rest", "normal", ["state"], 0.85),
    # ---- Avatar state layers (single-layer state proof). Always parented root. ----
    (r"^state\d+(idle|to\d+|awarded|close)?$", "avatar_state", "state_part",
     "root", "center", "visible_at_rest", "normal", ["state"], 0.85),
    # ---- VFX sequences ----
    (r"^(.+)_\d{2,4}$", "vfx_frame", "vfx", "root", "center",
     "visible_at_rest", "normal", ["win"], 0.7),
]


@dataclass
class LayerInterpretation:
    name: str
    semantic_role: str
    rig_role: str
    parent_hint: str
    pivot_hint: str
    alpha_polarity: str
    blend_hint: str
    animation_uses: list[str]
    confidence: float
    evidence: list[str] = field(default_factory=list)
    bounds: dict[str, float] | None = None
    z: int | None = None
    blend_mode_source: str | None = None
    visible: bool = True


def _is_boilerplate(name: str) -> bool:
    stem = Path(name).stem
    return any(p.match(stem) for p in BOILERPLATE_PATTERNS)


def _strip_symbol_prefix(name: str) -> str:
    """Strip the leading symbol-code prefix to get the role suffix.

    HP3_head_eyes_blink → head_eyes_blink
    HP1_santa_laugh    → santa_laugh
    LP1                → ''  (empty -> the layer IS the symbol body)
    """
    stem = Path(name).stem
    # Match common slot/symbol code prefixes
    m = re.match(
        r"^(HP|MP|LP|WD|SC|SF|JP|WYS|WY|CASH|BO|BL|TIER|JACKPOT|WINFRAME|"
        r"FB|SB|METER|AVATAR|FRAME)\d*[_-]?",
        stem, re.IGNORECASE,
    )
    if m:
        return stem[m.end():]
    return stem


def _match_semantic(safe_suffix: str) -> tuple[dict, str] | None:
    """Try every semantic pattern and return the first match."""
    for pattern, sem, rig, parent, pivot, polarity, blend, uses, conf in SEMANTIC_PATTERNS:
        if re.match(pattern, safe_suffix, re.IGNORECASE):
            return {
                "semantic_role": sem,
                "rig_role": rig,
                "parent_hint": parent,
                "pivot_hint": pivot,
                "alpha_polarity": polarity,
                "blend_hint": blend,
                "animation_uses": list(uses),
                "confidence": conf,
            }, pattern
    return None


def _fallback_role(safe_suffix: str) -> dict:
    """For unmatched names, return a conservative root_static placement."""
    return {
        "semantic_role": "unknown",
        "rig_role": "root_static",
        "parent_hint": "root",
        "pivot_hint": "center",
        "alpha_polarity": "visible_at_rest",
        "blend_hint": "normal",
        "animation_uses": ["idle"],
        "confidence": 0.3,
    }


def interpret_layer(name: str, manifest_entry: dict | None = None) -> LayerInterpretation:
    """Interpret a single layer name (optionally with manifest bounds/z)."""
    if _is_boilerplate(name):
        return LayerInterpretation(
            name=name,
            semantic_role="boilerplate",
            rig_role="filtered",
            parent_hint="none",
            pivot_hint="center",
            alpha_polarity="visible_at_rest",
            blend_hint="normal",
            animation_uses=[],
            confidence=1.0,
            evidence=["matches photoshop boilerplate pattern (Background or Layer N)"],
            visible=False,
        )

    suffix = _strip_symbol_prefix(name)
    if not suffix:
        # The layer name was just the symbol code — treat as the symbol body.
        result = {
            "semantic_role": "symbol_body",
            "rig_role": "body_part",
            "parent_hint": "root",
            "pivot_hint": "center",
            "alpha_polarity": "visible_at_rest",
            "blend_hint": "normal",
            "animation_uses": ["idle", "breathe", "land", "win"],
            "confidence": 0.85,
        }
        evidence = [f"layer name '{name}' matches symbol-code prefix only — treated as symbol body"]
    else:
        match = _match_semantic(suffix)
        if match:
            result, pattern = match
            evidence = [
                f"layer suffix '{suffix}' matched semantic pattern {pattern}",
                f"semantic_role={result['semantic_role']}, rig_role={result['rig_role']}",
            ]
        else:
            result = _fallback_role(suffix)
            evidence = [
                f"layer suffix '{suffix}' did not match any known pattern",
                "assigned conservative root_static placement; manual review recommended",
            ]

    interp = LayerInterpretation(
        name=name,
        evidence=evidence,
        **result,
    )

    if manifest_entry:
        if "bounds" in manifest_entry:
            interp.bounds = dict(manifest_entry["bounds"])
        if "z" in manifest_entry:
            interp.z = int(manifest_entry["z"])
        if not manifest_entry.get("visible", True):
            interp.visible = False
            interp.evidence.append("manifest says visible=False; filtered from rig")
        bm = manifest_entry.get("blend_mode")
        if bm and bm.upper() != "BLENDMODE.NORMAL":
            interp.blend_mode_source = bm
            interp.evidence.append(
                f"source blend mode {bm} stripped to 'normal' per H5G atlas policy; "
                "re-enable only with explicit art-direction approval"
            )

    return interp


def interpret_layers(names: list[str], manifest_layers: list[dict] | None = None) -> list[LayerInterpretation]:
    by_name = {entry.get("name"): entry for entry in (manifest_layers or [])}
    results: list[LayerInterpretation] = []
    for n in names:
        results.append(interpret_layer(n, by_name.get(Path(n).stem)))
    return results


def _collect_inputs(args: argparse.Namespace) -> tuple[list[str], list[dict] | None]:
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            raise SystemExit(f"manifest not found: {manifest_path}")
        manifest = json.loads(manifest_path.read_text())
        layers = manifest.get("layers", [])
        names = [Path(L.get("file", L.get("name", ""))).stem for L in layers]
        return names, layers
    if args.layer_dir:
        d = Path(args.layer_dir)
        if not d.is_dir():
            raise SystemExit(f"layer-dir not found: {d}")
        names = [p.name for p in sorted(d.iterdir())
                 if p.is_file() and p.suffix.lower() == ".png"]
        return names, None
    if args.names:
        return list(args.names), None
    raise SystemExit("provide --layer-dir, --manifest, or --names")


def main() -> int:
    p = argparse.ArgumentParser(description="Interpret per-layer roles for slot-symbol Spine rigging.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--layer-dir", help="Folder of per-layer PNG files.")
    g.add_argument("--manifest", help="h5g_layer_manifest.json from PSD-native or JSX intake.")
    g.add_argument("--names", nargs="+", help="List of layer/asset names.")
    p.add_argument("--out", help="Write JSON output to this path; otherwise prints to stdout.")
    args = p.parse_args()

    names, manifest_layers = _collect_inputs(args)
    interpretations = interpret_layers(names, manifest_layers)
    result = {
        "schema": "spine_slot_animation_layer_interpretation_v1",
        "input_count": len(names),
        "interpreted_count": len([i for i in interpretations if i.semantic_role != "boilerplate"]),
        "filtered_boilerplate": [i.name for i in interpretations if i.semantic_role == "boilerplate"],
        "layers": [asdict(i) for i in interpretations],
    }

    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
