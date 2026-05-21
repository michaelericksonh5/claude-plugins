#!/usr/bin/env python3
"""Portable 4.x animation composer.

Takes a rig_layout.json (from build_rig_layout.py) plus a recipe family and an
optional bounded controls dict, and emits 4.x-compliant animation JSON:

  - shared-timeline composition (every part on the same idle / breathe / land
    / win timeline, not 12 disconnected per-part animations)
  - bone timelines as DELTAS on top of setup (translate x/y, rotate value, scale x/y)
  - slot rgba timelines and stepped attachment timelines for expression overlays
  - per-family motion amplitudes by tier (restrained / medium / energetic)
  - bounded controls applied: bounce_strength, land_duration_scale,
    idle_duration_scale, glow_intensity, sparkle_intensity, premium_intensity,
    motion_strength, feature_active_intensity

Output is a JSON dict that an assembler (build_spine_package.py) merges into
the full shared_symbols.json.

USE
  python compose_animations.py \
      --layout <rig_layout.json> \
      --family hp_symbol \
      --rank 3 \
      --controls <controls.json> \
      --out <animations.json>

CONTRACT
  4.x field names are used everywhere:
    - rotate keys use "value" (not "angle")
    - slot color timelines use "rgba" (not "color")
    - two-color timelines use "rgba2" (not "twoColor") — only emitted if slot
      has setup "dark", which the proof composer never sets, so rgba2 is never
      emitted
    - attachment timelines use "name" with null = clear
    - translate/rotate are deltas; scale is absolute at full mix

This script never writes raw shared_symbols.json. The output is a JSON fragment
the assembler splices into the skeleton's "animations" block.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import ui_system_policy as ui_policy

FPS = 24

# Motion amplitude tiers, in pixels / degrees / scale factor
TIER_PROFILES = {
    "restrained": {
        "translate_px": 2.0,
        "rotate_deg": 4.0,
        "scale_factor": 1.03,
        "land_translate_px": 4.0,
        "land_rotate_deg": 4.0,
        "land_scale": 1.05,
        "land_squash": 0.95,
    },
    "medium": {
        "translate_px": 4.0,
        "rotate_deg": 6.0,
        "scale_factor": 1.05,
        "land_translate_px": 6.0,
        "land_rotate_deg": 6.0,
        "land_scale": 1.07,
        "land_squash": 0.93,
    },
    "energetic": {
        "translate_px": 7.0,
        "rotate_deg": 9.0,
        "scale_factor": 1.08,
        "land_translate_px": 10.0,
        "land_rotate_deg": 10.0,
        "land_scale": 1.10,
        "land_squash": 0.90,
    },
}

FAMILY_TIERS = {
    "hp_symbol": "restrained",
    "mp_symbol": "restrained",
    "lp_symbol": "restrained",
    "wild_symbol": "medium",
    "scatter_symbol": "medium",
    "value_symbol": "medium",
    "bonus_symbol": "energetic",
    "bo_special_symbol": "energetic",
    "jackpot_symbol": "energetic",
    "special_feature_symbol": "energetic",
    "celebration": "energetic",
    "winframe_explode": "medium",
    "meter": "restrained",
    "transition": "medium",
    "avatar": "medium",
}

# Family → animation naming pattern for proof animations
FAMILY_ANIMATION_NAMES = {
    "hp_symbol":              ("HP", ["", "idle", "breathe", "land", "win"]),
    "mp_symbol":              ("MP", ["", "idle", "breathe", "land"]),
    "lp_symbol":              ("LP", ["", "idle", "land"]),
    "wild_symbol":            ("WD", ["", "idle", "land", "win"]),
    "scatter_symbol":         ("SC", ["", "idle", "land", "smart"]),
    "value_symbol":           ("WYS", ["", "idle", "land"]),
    "bonus_symbol":           ("BO", ["", "idle", "land", "smart"]),
    "bo_special_symbol":      ("BO", ["", "idle", "land", "smart"]),
    "jackpot_symbol":         ("JP", ["", "idle", "land", "smart"]),
    "special_feature_symbol": ("SF", ["", "idle", "land", "smart"]),
}

# Non-symbol families use entirely different naming patterns.
# Per references/families.md these are the canonical animation names.
NON_SYMBOL_FAMILIES = {
    "meter": [
        "MeterIdle",
        "State1Collect", "State2Collect", "State3Collect",
        "State4Collect", "State5Collect",
    ],
    "transition": [
        "intro", "TransitionIdle", "outro",
        "FB_Transition", "SB_Transition",
    ],
    "celebration": [
        "grandJackpot", "celebration_loop",
        "tier_1", "tier_2", "tier_3",
        "celebration_fx_1", "celebration_fx_2", "celebration_fx_3", "burst",
    ],
    "winframe_explode": [
        "WinFrame", "WinFrameidle", "WinFrameExplode",
    ],
}

CONTROL_DEFAULTS = {
    "bounce_strength": 1.0,
    "land_duration_scale": 1.0,
    "idle_duration_scale": 1.0,
    "glow_intensity": 1.0,
    "sparkle_intensity": 1.0,
    "premium_intensity": 1.0,
    "motion_strength": 1.0,
    "feature_active_intensity": 1.0,
}

DEFAULT_DURATIONS = {
    "idle": 4.0,
    "breathe": 2.0,
    "land": 0.4,
    "win": 2.0,
    "smart": 1.0,
    "state": 1.2,
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _validate_controls(controls: dict[str, Any]) -> dict[str, float]:
    """Pull bounded controls (with ranges) into a clean float dict."""
    out = dict(CONTROL_DEFAULTS)
    metadata_keys = {"recipe_type", "export_profile", "bezier_preset"}
    recipe_types = set(FAMILY_ANIMATION_NAMES) | set(NON_SYMBOL_FAMILIES) | {"avatar"}
    export_profile = (controls or {}).get("export_profile")
    bezier_preset = (controls or {}).get("bezier_preset")
    if export_profile is not None and export_profile not in {"v10_linear", "spine_43_bezier", "spine_42_bezier"}:
        raise ValueError(f"export_profile {export_profile!r} is not implemented")
    if bezier_preset is not None:
        valid_presets = {"ease_in", "ease_out", "ease_in_out", "overshoot", "settle"}
        if bezier_preset not in valid_presets:
            raise ValueError(f"bezier_preset {bezier_preset!r} is not implemented")
        if export_profile not in {"spine_43_bezier", "spine_42_bezier"}:
            raise ValueError("bezier_preset requires export_profile 'spine_43_bezier'")
    ranges = {
        "bounce_strength": (0.0, 2.0),
        "land_duration_scale": (0.25, 3.0),
        "idle_duration_scale": (0.25, 3.0),
        "glow_intensity": (0.0, 2.0),
        "sparkle_intensity": (0.0, 2.0),
        "premium_intensity": (0.0, 2.0),
        "motion_strength": (0.0, 2.0),
        "feature_active_intensity": (0.0, 2.0),
    }
    for k, v in (controls or {}).items():
        if k in metadata_keys:
            if k == "recipe_type" and v not in recipe_types:
                raise ValueError(f"recipe_type {v!r} is not a supported family")
            continue
        if k not in out:
            raise ValueError(f"unknown control field {k!r}")
        if not isinstance(v, (int, float)):
            raise ValueError(f"control {k} must be numeric")
        lo, hi = ranges[k]
        if v < lo or v > hi:
            raise ValueError(f"control {k}={v} out of range [{lo}, {hi}]")
        out[k] = float(v)
    return out


def _find_slot_by_role(layout: dict, *roles: str) -> dict | None:
    """Find the first slot whose semantic_role matches any of roles."""
    for s in layout["slots"]:
        if s.get("semantic_role") in roles:
            return s
    return None


def _find_slots_by_role(layout: dict, *roles: str) -> list[dict]:
    return [s for s in layout["slots"] if s.get("semantic_role") in roles]


def _find_bone_by_role(layout: dict, *roles: str) -> dict | None:
    for b in layout["bones"]:
        if b.get("semantic_role") in roles:
            return b
    return None


def _find_bones_by_role(layout: dict, *roles: str) -> list[dict]:
    return [b for b in layout["bones"] if b.get("semantic_role") in roles]


# ---------------------------------------------------------------------------
# Idle / breathe / land / win composers
# ---------------------------------------------------------------------------

def _compose_setup(layout: dict) -> tuple[dict, float]:
    """Stable setup/rest animation: no keyed motion, so the rig resolves to setup pose."""
    return {"bones": {}, "slots": {}}, 0.0


def _compose_idle(
    layout: dict, tier: dict, ctrls: dict[str, float]
) -> tuple[dict, float]:
    """Build the idle animation: vertical breath on body/head, gentle bob, blinks,
    frame pulse, frame-glow shimmer. Shared timeline."""
    dur = DEFAULT_DURATIONS["idle"] * ctrls["idle_duration_scale"]
    motion = ctrls["motion_strength"]
    bones: dict[str, dict] = {}
    slots: dict[str, dict] = {}

    # Body / head breath (1-2 px vertical, full duration)
    body_amp = tier["translate_px"] * 0.5 * motion
    head_amp = tier["translate_px"] * 0.75 * motion
    head_rot = tier["rotate_deg"] * 0.3 * motion

    for b in _find_bones_by_role(layout, "character_body", "symbol_body", "body_part"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.5, "x": 0, "y": body_amp},
                {"time": dur, "x": 0, "y": 0},
            ]
        }

    for b in _find_bones_by_role(layout, "head"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.55, "x": 0, "y": head_amp},
                {"time": dur, "x": 0, "y": 0},
            ],
            "rotate": [
                {"time": 0, "value": 0},
                {"time": dur * 0.3, "value": head_rot},
                {"time": dur * 0.7, "value": -head_rot},
                {"time": dur, "value": 0},
            ],
        }

    # Hand sway
    hand_amp = tier["translate_px"] * 1.0 * motion
    for i, b in enumerate(_find_bones_by_role(layout, "hand_left", "hand_right", "hand")):
        sign = 1 if i % 2 == 0 else -1
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.5, "x": sign * hand_amp, "y": 0},
                {"time": dur, "x": 0, "y": 0},
            ]
        }

    # Frame subtle scale pulse
    frame_scale = 1.0 + (tier["scale_factor"] - 1.0) * 0.5 * motion
    for b in _find_bones_by_role(layout, "frame", "back_frame", "front_frame"):
        bones[b["name"]] = {
            "scale": [
                {"time": 0, "x": 1, "y": 1},
                {"time": dur * 0.5, "x": frame_scale, "y": frame_scale},
                {"time": dur, "x": 1, "y": 1},
            ]
        }

    # Frame glow alpha pulse (0.8 -> 1.0 -> 0.8)
    glow_slots = _find_slots_by_role(layout, "frame_glow", "glow", "shimmer")
    glow_intensity = ctrls["glow_intensity"]
    if glow_slots and glow_intensity > 0:
        # 0.8 -> 1.0 -> 0.8 scaled by glow_intensity (clamped to 0..1)
        lo = _clamp(0.8 * glow_intensity, 0, 1)
        hi = _clamp(1.0 * glow_intensity, 0, 1)
        for s in glow_slots:
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": f"ffffff{int(lo*255):02x}"},
                    {"time": dur * 0.5, "color": f"ffffff{int(hi*255):02x}"},
                    {"time": dur, "color": f"ffffff{int(lo*255):02x}"},
                ]
            }

    # Sparkle slow pulse
    sparkle_slots = _find_slots_by_role(layout, "sparkle", "sheen", "shine")
    sparkle_intensity = ctrls["sparkle_intensity"]
    if sparkle_slots and sparkle_intensity > 0:
        lo = _clamp(0.4 * sparkle_intensity, 0, 1)
        hi = _clamp(1.0 * sparkle_intensity, 0, 1)
        for s in sparkle_slots:
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": f"ffffff{int(lo*255):02x}"},
                    {"time": dur * 0.7, "color": f"ffffff{int(hi*255):02x}"},
                    {"time": dur, "color": f"ffffff{int(lo*255):02x}"},
                ]
            }

    # Premium / lit / glass
    premium_slots = _find_slots_by_role(layout, "lit", "glass", "highlight")
    premium_intensity = ctrls["premium_intensity"]
    if premium_slots and premium_intensity > 0:
        lo = _clamp(0.7 * premium_intensity, 0, 1)
        hi = _clamp(1.0 * premium_intensity, 0, 1)
        for s in premium_slots:
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": f"ffffff{int(lo*255):02x}"},
                    {"time": dur * 0.5, "color": f"ffffff{int(hi*255):02x}"},
                    {"time": dur, "color": f"ffffff{int(lo*255):02x}"},
                ]
            }

    # Eye blinks - two stepped attachment swaps, ~60ms each, at 1.16 and 3.16 s
    eyes_slots = _find_slots_by_role(layout, "eyes_blink", "eyes_closed", "eyes_side")
    if eyes_slots and dur >= 2.0:
        blink_times = [1.16 * ctrls["idle_duration_scale"], 3.16 * ctrls["idle_duration_scale"]]
        for s in eyes_slots:
            attachment_path = "parts/" + s["attachment"].split("/")[-1] if "/" in s["attachment"] else s["attachment"]
            timeline = [{"time": 0, "name": None}]
            for t in blink_times:
                if t + 0.06 < dur:
                    timeline.append({"time": t, "name": attachment_path})
                    timeline.append({"time": t + 0.06, "name": None})
            slots.setdefault(s["name"], {})["attachment"] = timeline

    return {"bones": bones, "slots": slots}, dur


def _compose_breathe(layout: dict, tier: dict, ctrls: dict[str, float]) -> tuple[dict, float]:
    """A shorter, calmer loop: body breath + head bob + frame pulse only."""
    dur = DEFAULT_DURATIONS["breathe"] * ctrls["idle_duration_scale"]
    motion = ctrls["motion_strength"]
    bones: dict[str, dict] = {}
    slots: dict[str, dict] = {}

    body_amp = tier["translate_px"] * 0.4 * motion
    head_amp = tier["translate_px"] * 0.6 * motion

    for b in _find_bones_by_role(layout, "character_body", "symbol_body", "body_part"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.5, "x": 0, "y": body_amp},
                {"time": dur, "x": 0, "y": 0},
            ]
        }
    for b in _find_bones_by_role(layout, "head"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.5, "x": 0, "y": head_amp},
                {"time": dur, "x": 0, "y": 0},
            ]
        }
    frame_scale = 1.0 + (tier["scale_factor"] - 1.0) * 0.4 * motion
    for b in _find_bones_by_role(layout, "frame", "back_frame", "front_frame"):
        bones[b["name"]] = {
            "scale": [
                {"time": 0, "x": 1, "y": 1},
                {"time": dur * 0.5, "x": frame_scale, "y": frame_scale},
                {"time": dur, "x": 1, "y": 1},
            ]
        }

    return {"bones": bones, "slots": slots}, dur


def _compose_land(layout: dict, tier: dict, ctrls: dict[str, float]) -> tuple[dict, float]:
    """0.4s impact: squash, stretch, settle on body; head follow-through; frame flash."""
    dur = DEFAULT_DURATIONS["land"] * ctrls["land_duration_scale"]
    bounce = ctrls["bounce_strength"] * ctrls["motion_strength"]
    bones: dict[str, dict] = {}
    slots: dict[str, dict] = {}

    land_y_impact = tier["land_translate_px"] * bounce
    squash = 1.0 - (1.0 - tier["land_squash"]) * bounce
    stretch = 1.0 + (tier["land_scale"] - 1.0) * bounce

    for b in _find_bones_by_role(layout, "character_body", "symbol_body", "body_part"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": -land_y_impact},
                {"time": dur * 0.125, "x": 0, "y": 0},
                {"time": dur, "x": 0, "y": 0},
            ],
            "scale": [
                {"time": 0, "x": 1.0, "y": 1.0},
                {"time": dur * 0.125, "x": 1.0, "y": squash},
                {"time": dur * 0.25, "x": stretch, "y": 1.0 + (stretch - 1.0) * 0.5},
                {"time": dur, "x": 1.0, "y": 1.0},
            ],
        }

    head_rot = tier["land_rotate_deg"] * bounce
    for b in _find_bones_by_role(layout, "head"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.2, "x": 0, "y": -land_y_impact * 0.4},
                {"time": dur, "x": 0, "y": 0},
            ],
            "rotate": [
                {"time": 0, "value": 0},
                {"time": dur * 0.2, "value": head_rot * 0.5},
                {"time": dur * 0.5, "value": -head_rot * 0.3},
                {"time": dur, "value": 0},
            ],
        }

    # Frame glow alpha flash
    glow_slots = _find_slots_by_role(layout, "frame_glow", "glow")
    glow_intensity = ctrls["glow_intensity"]
    if glow_slots and glow_intensity > 0:
        peak = _clamp(1.0 * glow_intensity, 0, 1)
        rest = _clamp(0.6 * glow_intensity, 0, 1)
        for s in glow_slots:
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": "ffffff00"},
                    {"time": dur * 0.5, "color": f"ffffff{int(peak*255):02x}"},
                    {"time": dur, "color": f"ffffff{int(rest*255):02x}"},
                ]
            }

    return {"bones": bones, "slots": slots}, dur


def _compose_win(layout: dict, tier: dict, ctrls: dict[str, float]) -> tuple[dict, float]:
    """2s celebration: body pulse + lift, head emphasis bob, hand wave, mouth/eyes Ho-Ho-Ho."""
    dur = DEFAULT_DURATIONS["win"]
    motion = ctrls["motion_strength"]
    premium = ctrls["premium_intensity"]
    bones: dict[str, dict] = {}
    slots: dict[str, dict] = {}

    # Body pulse + lift
    pulse_scale = 1.0 + (tier["scale_factor"] - 1.0) * 1.5 * motion
    lift_y = tier["translate_px"] * 0.5 * motion
    for b in _find_bones_by_role(layout, "character_body", "symbol_body", "body_part"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.5, "x": 0, "y": lift_y},
                {"time": dur, "x": 0, "y": 0},
            ],
            "scale": [
                {"time": 0, "x": 1, "y": 1},
                {"time": dur * 0.5, "x": pulse_scale, "y": pulse_scale},
                {"time": dur, "x": 1, "y": 1},
            ],
        }

    # Head emphasis bob
    head_amp = tier["translate_px"] * 1.0 * motion
    head_rot = tier["rotate_deg"] * 1.3 * motion
    for b in _find_bones_by_role(layout, "head"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.5, "x": 0, "y": head_amp},
                {"time": dur, "x": 0, "y": 0},
            ],
            "rotate": [
                {"time": 0, "value": 0},
                {"time": dur * 0.25, "value": head_rot},
                {"time": dur * 0.75, "value": -head_rot},
                {"time": dur, "value": 0},
            ],
        }

    # Hand wave
    wave_amp = tier["translate_px"] * 1.5 * motion
    for i, b in enumerate(_find_bones_by_role(layout, "hand_left", "hand_right", "hand")):
        sign = 1 if i % 2 == 0 else -1
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.3, "x": sign * wave_amp, "y": 0},
                {"time": dur * 0.7, "x": -sign * wave_amp, "y": 0},
                {"time": dur, "x": 0, "y": 0},
            ]
        }

    # Frame scale pulse stronger
    frame_scale = 1.0 + (tier["scale_factor"] - 1.0) * 1.5 * motion
    for b in _find_bones_by_role(layout, "frame", "back_frame", "front_frame"):
        bones[b["name"]] = {
            "scale": [
                {"time": 0, "x": 1, "y": 1},
                {"time": dur * 0.5, "x": frame_scale, "y": frame_scale},
                {"time": dur, "x": 1, "y": 1},
            ]
        }

    # Frame glow shimmer (0.6 -> 1.0 -> 0.6)
    glow_intensity = ctrls["glow_intensity"]
    glow_slots = _find_slots_by_role(layout, "frame_glow", "glow")
    if glow_slots and glow_intensity > 0:
        lo = _clamp(0.6 * glow_intensity, 0, 1)
        hi = _clamp(1.0 * glow_intensity, 0, 1)
        for s in glow_slots:
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": f"ffffff{int(lo*255):02x}"},
                    {"time": dur * 0.5, "color": f"ffffff{int(hi*255):02x}"},
                    {"time": dur, "color": f"ffffff{int(lo*255):02x}"},
                ]
            }

    # Sparkle / sheen burst
    sparkle_intensity = ctrls["sparkle_intensity"]
    sparkle_slots = _find_slots_by_role(layout, "sparkle", "sheen", "shine")
    if sparkle_slots and sparkle_intensity > 0:
        hi = _clamp(1.0 * sparkle_intensity, 0, 1)
        for s in sparkle_slots:
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": "ffffff00"},
                    {"time": dur * 0.3, "color": f"ffffff{int(hi*255):02x}"},
                    {"time": dur * 0.7, "color": f"ffffff{int(hi*255):02x}"},
                    {"time": dur, "color": "ffffff00"},
                ]
            }

    # Premium / lit / glass swell
    premium_slots = _find_slots_by_role(layout, "lit", "glass", "highlight")
    if premium_slots and premium > 0:
        hi = _clamp(1.0 * premium, 0, 1)
        for s in premium_slots:
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": "ffffff00"},
                    {"time": dur * 0.5, "color": f"ffffff{int(hi*255):02x}"},
                    {"time": dur, "color": "ffffff00"},
                ]
            }

    # Ho-Ho-Ho beats: synchronized mouth + eye-blink stepped attachments
    laugh_slots = _find_slots_by_role(layout, "mouth_laugh", "mouth_open")
    eye_slots = _find_slots_by_role(layout, "eyes_blink", "eyes_closed")
    beat_times = [0.36, 0.92, 1.48]
    beat_dur = 0.06
    if laugh_slots:
        for s in laugh_slots:
            attachment_path = "parts/" + s["attachment"].split("/")[-1] if "/" in s["attachment"] else s["attachment"]
            timeline = [{"time": 0, "name": None}]
            for t in beat_times:
                if t + beat_dur < dur:
                    timeline.append({"time": t, "name": attachment_path})
                    timeline.append({"time": t + beat_dur, "name": None})
            slots.setdefault(s["name"], {})["attachment"] = timeline
    if eye_slots:
        for s in eye_slots:
            attachment_path = "parts/" + s["attachment"].split("/")[-1] if "/" in s["attachment"] else s["attachment"]
            timeline = [{"time": 0, "name": None}]
            for t in beat_times:
                if t + beat_dur < dur:
                    timeline.append({"time": t, "name": attachment_path})
                    timeline.append({"time": t + beat_dur, "name": None})
            slots.setdefault(s["name"], {})["attachment"] = timeline

    return {"bones": bones, "slots": slots}, dur


def _compose_smart(layout: dict, tier: dict, ctrls: dict[str, float]) -> tuple[dict, float]:
    """A short smart / feature-active loop for BO/SF/JP/SC."""
    dur = DEFAULT_DURATIONS["smart"] * ctrls["idle_duration_scale"]
    intensity = ctrls["feature_active_intensity"] * ctrls["motion_strength"]
    bones: dict[str, dict] = {}
    slots: dict[str, dict] = {}

    body_amp = tier["translate_px"] * 0.6 * intensity
    body_scale = 1.0 + (tier["scale_factor"] - 1.0) * 0.6 * intensity

    for b in _find_bones_by_role(layout, "character_body", "symbol_body", "body_part"):
        bones[b["name"]] = {
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.5, "x": 0, "y": body_amp},
                {"time": dur, "x": 0, "y": 0},
            ],
            "scale": [
                {"time": 0, "x": 1, "y": 1},
                {"time": dur * 0.5, "x": body_scale, "y": body_scale},
                {"time": dur, "x": 1, "y": 1},
            ],
        }

    glow_slots = _find_slots_by_role(layout, "frame_glow", "glow")
    if glow_slots and ctrls["glow_intensity"] > 0:
        lo = _clamp(0.5 * ctrls["glow_intensity"] * intensity, 0, 1)
        hi = _clamp(1.0 * ctrls["glow_intensity"] * intensity, 0, 1)
        for s in glow_slots:
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": f"ffffff{int(lo*255):02x}"},
                    {"time": dur * 0.5, "color": f"ffffff{int(hi*255):02x}"},
                    {"time": dur, "color": f"ffffff{int(lo*255):02x}"},
                ]
            }

    return {"bones": bones, "slots": slots}, dur


# ---------------------------------------------------------------------------
# Family-specific entry points and naming
# ---------------------------------------------------------------------------


def _compose_meter_state(layout: dict, tier: dict, ctrls: dict[str, float], state_idx: int) -> tuple[dict, float]:
    """A 0.4s collect beat for meter State<N>Collect: brief scale-up + alpha-flash on body, settle to idle."""
    dur = 0.4 * ctrls.get("land_duration_scale", 1.0)
    motion = ctrls.get("motion_strength", 1.0)
    bones: dict[str, dict] = {}
    slots: dict[str, dict] = {}
    scale_peak = 1.0 + (tier["scale_factor"] - 1.0) * 1.2 * motion
    for b in _find_bones_by_role(layout, "body_part", "symbol_body", "character_body", "meter_bar"):
        bones[b["name"]] = {
            "scale": [
                {"time": 0, "x": 1, "y": 1},
                {"time": dur * 0.3, "x": scale_peak, "y": scale_peak},
                {"time": dur, "x": 1, "y": 1},
            ]
        }
    for s in _find_slots_by_role(layout, "glow", "sparkle", "frame_glow"):
        slots[s["name"]] = {
            "rgba": [
                {"time": 0, "color": "ffffff80"},
                {"time": dur * 0.3, "color": "ffffffff"},
                {"time": dur, "color": "ffffff80"},
            ]
        }
    return {"bones": bones, "slots": slots}, dur


def _compose_transition_beat(layout: dict, tier: dict, ctrls: dict[str, float], beat: str) -> tuple[dict, float]:
    """Composes intro/outro/FB_Transition/SB_Transition/TransitionIdle.

    Intros sweep in (alpha 0→1 + scale 0.95→1.0). Outros sweep out. FB/SB are
    feature/bonus transitions with stronger motion."""
    dur = 0.8 * ctrls.get("land_duration_scale", 1.0)
    bones: dict[str, dict] = {}
    slots: dict[str, dict] = {}
    if beat in ("intro", "FB_Transition", "SB_Transition"):
        for b in _find_bones_by_role(layout, "body_part", "symbol_body", "character_body"):
            bones[b["name"]] = {
                "scale": [
                    {"time": 0, "x": 0.95, "y": 0.95},
                    {"time": dur, "x": 1.0, "y": 1.0},
                ]
            }
        for s in layout.get("slots", []):
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": "ffffff00"},
                    {"time": dur, "color": "ffffffff"},
                ]
            }
    elif beat == "outro":
        for b in _find_bones_by_role(layout, "body_part", "symbol_body", "character_body"):
            bones[b["name"]] = {
                "scale": [
                    {"time": 0, "x": 1.0, "y": 1.0},
                    {"time": dur, "x": 0.95, "y": 0.95},
                ]
            }
        for s in layout.get("slots", []):
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": "ffffffff"},
                    {"time": dur, "color": "ffffff00"},
                ]
            }
    else:  # TransitionIdle: subtle alpha pulse
        dur = 1.0
        for s in layout.get("slots", []):
            slots[s["name"]] = {
                "rgba": [
                    {"time": 0, "color": "ffffffdd"},
                    {"time": dur * 0.5, "color": "ffffffff"},
                    {"time": dur, "color": "ffffffdd"},
                ]
            }
    return {"bones": bones, "slots": slots}, dur


def _compose_celebration_beat(layout: dict, tier: dict, ctrls: dict[str, float], beat: str) -> tuple[dict, float]:
    """Composes grandJackpot/celebration_loop/tier_1..3/celebration_fx_1..3/burst.

    grandJackpot is the biggest tier — most aggressive pulse. tier_N scales down."""
    motion = ctrls.get("motion_strength", 1.0)
    premium = ctrls.get("premium_intensity", 1.0)
    if beat == "grandJackpot":
        dur, scale_peak = 3.0, 1.0 + (tier["scale_factor"] - 1.0) * 2.5 * motion
    elif beat == "tier_1":
        dur, scale_peak = 2.5, 1.0 + (tier["scale_factor"] - 1.0) * 2.2 * motion
    elif beat == "tier_2":
        dur, scale_peak = 2.0, 1.0 + (tier["scale_factor"] - 1.0) * 1.8 * motion
    elif beat == "tier_3":
        dur, scale_peak = 1.5, 1.0 + (tier["scale_factor"] - 1.0) * 1.4 * motion
    elif beat == "celebration_loop":
        dur, scale_peak = 2.0, 1.0 + (tier["scale_factor"] - 1.0) * 1.5 * motion
    elif beat == "burst":
        dur, scale_peak = 0.6, 1.0 + (tier["scale_factor"] - 1.0) * 3.0 * motion
    else:  # celebration_fx_1..3
        dur, scale_peak = 1.0, 1.0 + (tier["scale_factor"] - 1.0) * 1.8 * motion

    bones: dict[str, dict] = {}
    slots: dict[str, dict] = {}
    for b in _find_bones_by_role(layout, "body_part", "symbol_body", "character_body"):
        bones[b["name"]] = {
            "scale": [
                {"time": 0, "x": 1, "y": 1},
                {"time": dur * 0.4, "x": scale_peak, "y": scale_peak},
                {"time": dur, "x": 1, "y": 1},
            ],
            "translate": [
                {"time": 0, "x": 0, "y": 0},
                {"time": dur * 0.4, "x": 0, "y": tier["translate_px"] * 0.5 * motion},
                {"time": dur, "x": 0, "y": 0},
            ],
        }
    # Burst: sparkle/glow flash
    intensity = _clamp(premium, 0, 1)
    for s in _find_slots_by_role(layout, "glow", "sparkle", "shine", "lit", "frame_glow"):
        slots[s["name"]] = {
            "rgba": [
                {"time": 0, "color": "ffffff00"},
                {"time": dur * 0.3, "color": f"ffffff{int(intensity*255):02x}"},
                {"time": dur * 0.7, "color": f"ffffff{int(intensity*255):02x}"},
                {"time": dur, "color": "ffffff00"},
            ]
        }
    return {"bones": bones, "slots": slots}, dur


def _compose_winframe_beat(layout: dict, tier: dict, ctrls: dict[str, float], beat: str) -> tuple[dict, float]:
    """Composes WinFrame/WinFrameidle/WinFrameExplode.

    WinFrame is the entry pulse; idle is the loop; Explode is the burst-and-vanish."""
    motion = ctrls.get("motion_strength", 1.0)
    if beat == "WinFrame":
        dur = 0.6
        scale_peak = 1.0 + (tier["scale_factor"] - 1.0) * 2.0 * motion
        bones = {}
        for b in _find_bones_by_role(layout, "frame", "frame_part", "back_frame", "front_frame", "body_part"):
            bones[b["name"]] = {
                "scale": [
                    {"time": 0, "x": 0.9, "y": 0.9},
                    {"time": dur * 0.3, "x": scale_peak, "y": scale_peak},
                    {"time": dur, "x": 1.0, "y": 1.0},
                ]
            }
        slots = {}
        for s in layout.get("slots", []):
            slots[s["name"]] = {"rgba": [{"time": 0, "color": "ffffff00"}, {"time": dur, "color": "ffffffff"}]}
        return {"bones": bones, "slots": slots}, dur
    if beat == "WinFrameidle":
        dur = 2.0
        bones = {}
        scale_peak = 1.0 + (tier["scale_factor"] - 1.0) * 0.3 * motion
        for b in _find_bones_by_role(layout, "frame", "frame_part", "back_frame", "front_frame", "body_part"):
            bones[b["name"]] = {
                "scale": [
                    {"time": 0, "x": 1, "y": 1},
                    {"time": dur * 0.5, "x": scale_peak, "y": scale_peak},
                    {"time": dur, "x": 1, "y": 1},
                ]
            }
        return {"bones": bones, "slots": {}}, dur
    # WinFrameExplode: scale up + fade out
    dur = 0.5
    bones = {}
    scale_peak = 1.0 + (tier["scale_factor"] - 1.0) * 3.5 * motion
    for b in _find_bones_by_role(layout, "frame", "frame_part", "back_frame", "front_frame", "body_part"):
        bones[b["name"]] = {
            "scale": [
                {"time": 0, "x": 1, "y": 1},
                {"time": dur, "x": scale_peak, "y": scale_peak},
            ]
        }
    slots = {}
    for s in layout.get("slots", []):
        slots[s["name"]] = {"rgba": [{"time": 0, "color": "ffffffff"}, {"time": dur, "color": "ffffff00"}]}
    return {"bones": bones, "slots": slots}, dur



def _compose_non_symbol_family(layout, family, tier, ctrls):
    beats = NON_SYMBOL_FAMILIES[family]
    out = {}
    for beat in beats:
        if family == "meter":
            if beat == "MeterIdle":
                out[beat], _ = _compose_idle(layout, tier, ctrls)
            else:
                idx = int(beat.replace("State", "").replace("Collect", "") or 1)
                out[beat], _ = _compose_meter_state(layout, tier, ctrls, idx)
        elif family == "transition":
            out[beat], _ = _compose_transition_beat(layout, tier, ctrls, beat)
        elif family == "celebration":
            out[beat], _ = _compose_celebration_beat(layout, tier, ctrls, beat)
        elif family == "winframe_explode":
            out[beat], _ = _compose_winframe_beat(layout, tier, ctrls, beat)
    return out


def compose_animations_for_family(layout, family, rank, ctrls):
    """Return {animation_name: animation_dict} for the family."""
    if family not in FAMILY_ANIMATION_NAMES and family not in NON_SYMBOL_FAMILIES:
        raise ValueError(f"family {family!r} does not have a deterministic animation template")
    tier_name = FAMILY_TIERS.get(family, "restrained")
    tier = TIER_PROFILES[tier_name]
    if family in NON_SYMBOL_FAMILIES:
        return _compose_non_symbol_family(layout, family, tier, ctrls)
    name_prefix, suffixes = FAMILY_ANIMATION_NAMES.get(
        family, (family.upper(), ["", "idle", "land"])
    )
    base_name = f"{name_prefix}{rank}"
    animations = {}
    for suffix in suffixes:
        anim_name = base_name + suffix
        if suffix == "":
            anim, _ = _compose_setup(layout)
        elif suffix == "win":
            anim, _ = _compose_win(layout, tier, ctrls)
        elif suffix == "idle":
            anim, _ = _compose_idle(layout, tier, ctrls)
        elif suffix == "breathe":
            anim, _ = _compose_breathe(layout, tier, ctrls)
        elif suffix == "land":
            anim, _ = _compose_land(layout, tier, ctrls)
        elif suffix == "smart":
            anim, _ = _compose_smart(layout, tier, ctrls)
        else:
            anim = {"bones": {}, "slots": {}}
        animations[anim_name] = anim
    return animations


def main():
    p = argparse.ArgumentParser(description="Compose Spine 4.x animations from a rig_layout.")
    p.add_argument("--layout", required=True)
    p.add_argument("--family", required=True, choices=list(FAMILY_TIERS.keys()))
    p.add_argument("--rank", type=int, default=1)
    p.add_argument("--controls")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    layout = json.loads(Path(args.layout).read_text())
    ctrls = json.loads(Path(args.controls).read_text()) if args.controls else {}
    bounded = _validate_controls(ctrls)
    animations = compose_animations_for_family(layout, args.family, args.rank, bounded)
    ui_system_report = ui_policy.build_ui_system_report(args.family, layout)
    out = {
        "schema": "spine_slot_animation_animations_v1",
        "family": args.family, "rank": args.rank,
        **ui_system_report,
        "controls_applied": bounded, "fps": FPS,
        "animations": animations,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"wrote {args.out}; animations: {list(animations.keys())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
