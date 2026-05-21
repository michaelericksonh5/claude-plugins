#!/usr/bin/env python3
"""Topology-aware motion overlays for non-humanoid creatures.

The default compose_animations.py applies humanoid motion primitives (head bob,
hand sway, body breath). For non-humanoid topologies, we overlay additional
motion that respects the creature's anatomy:

  - quadruped:   front legs alternate with back legs (gait), tail wag
  - many_legged: each leg/tentacle has a sinusoidal phase offset (wave motion)
  - serpentine: body segments undulate along the chain (sine wave through bones)
  - winged:      wings flap on a fast loop, body bobs gently

For humanoid + prop topologies, no overlay is applied — the default composer
already does the right thing.

USE
  After compose_animations.py emits the base animation set, call
  apply_topology_motion(animations, layout, topology_result, ctrls)
  to overlay topology-specific motion into idle/breathe/win/land.
"""

from __future__ import annotations

import math
import re

LEG_RE = re.compile(r"_leg_?(\d+)$", re.I)
TENTACLE_RE = re.compile(r"_tentacle_?(\d+)$", re.I)
BODY_SEG_RE = re.compile(r"_(?:body|segment)_(\d+)$", re.I)
WING_RE = re.compile(r"_wing_?([LR]?)$", re.I)
TAIL_RE = re.compile(r"_tail(?:_(\w+))?$", re.I)


def _find_bones_matching(layout: dict, regex) -> list[dict]:
    """Return bones whose layer_name (or name) matches the regex.

    Strips the .png suffix from layer_name and the _bone suffix from the bone
    name before matching, so regexes that expect to end at a number or letter
    (e.g. _leg_\\d+$, _wing_[LR]?$) still anchor correctly.
    """
    out = []
    for b in layout.get("bones", []):
        layer = (b.get("layer_name") or "").lower()
        if layer.endswith(".png"):
            layer = layer[:-4]
        bone = b.get("name", "").lower()
        if bone.endswith("_bone"):
            bone = bone[:-5]
        for candidate in (layer, bone):
            m = regex.search(candidate)
            if m:
                out.append((b, m))
                break
    return out


def _ensure_animation(animations: dict, name: str) -> dict:
    a = animations.setdefault(name, {"bones": {}, "slots": {}})
    a.setdefault("bones", {})
    a.setdefault("slots", {})
    return a


def _add_track(bones_block: dict, bone_name: str, tl_name: str, keys: list[dict]) -> None:
    """Merge a timeline track into a bone, preserving existing keys."""
    bone_block = bones_block.setdefault(bone_name, {})
    bone_block[tl_name] = keys


def apply_quadruped_gait(animations: dict, layout: dict, ctrls: dict) -> None:
    """Add a 4-beat alternating gait on the legs for idle/win.

    Front-left + back-right move forward while front-right + back-left move
    back, alternating every 0.5s. Tail (if present) wags side-to-side.
    """
    motion = ctrls.get("motion_strength", 1.0)
    idle_dur = 4.0 * ctrls.get("idle_duration_scale", 1.0)
    legs = _find_bones_matching(layout, LEG_RE)
    if not legs:
        return
    tails = _find_bones_matching(layout, TAIL_RE)

    for anim_name in ("idle", "breathe"):
        if anim_name == "breathe":
            dur = 2.0 * ctrls.get("idle_duration_scale", 1.0)
        else:
            dur = idle_dur
        anim = _ensure_animation(animations, _resolve_anim_name(animations, anim_name))
        for i, (bone, _m) in enumerate(legs):
            # Phase: legs 1 (FL), 4 (BR) lead; 2 (FR), 3 (BL) trail by half-cycle
            phase = (i % 2) * 0.5
            amp = 1.5 * motion  # px translate
            _add_track(anim["bones"], bone["name"], "translate", [
                {"time": 0,                            "x": 0, "y": 0},
                {"time": dur * (0.25 + phase) % dur,  "x": 0, "y": amp},
                {"time": dur * (0.75 + phase) % dur,  "x": 0, "y": -amp},
                {"time": dur,                          "x": 0, "y": 0},
            ])

        # Tail wag
        for bone, _m in tails:
            wag_amp = 4 * motion
            _add_track(anim["bones"], bone["name"], "rotate", [
                {"time": 0,         "value": 0},
                {"time": dur * 0.5, "value": wag_amp},
                {"time": dur,       "value": 0},
            ])


def apply_many_legged_wave(animations: dict, layout: dict, ctrls: dict) -> None:
    """Each tentacle/leg has a sinusoidal phase offset — wave motion across
    the creature's limbs."""
    motion = ctrls.get("motion_strength", 1.0)
    dur = 4.0 * ctrls.get("idle_duration_scale", 1.0)
    limbs = _find_bones_matching(layout, TENTACLE_RE) + _find_bones_matching(layout, LEG_RE)
    if not limbs:
        return
    anim = _ensure_animation(animations, _resolve_anim_name(animations, "idle"))
    n = len(limbs)
    for i, (bone, _m) in enumerate(limbs):
        # Phase offset by limb index — produces a wave traveling around the creature
        phase_fraction = i / n
        rot_amp = 6 * motion
        keys = [
            {"time": 0, "value": rot_amp * math.sin(2 * math.pi * phase_fraction)},
            {"time": dur * 0.25, "value": rot_amp * math.sin(2 * math.pi * (phase_fraction + 0.25))},
            {"time": dur * 0.5, "value": rot_amp * math.sin(2 * math.pi * (phase_fraction + 0.5))},
            {"time": dur * 0.75, "value": rot_amp * math.sin(2 * math.pi * (phase_fraction + 0.75))},
            {"time": dur, "value": rot_amp * math.sin(2 * math.pi * phase_fraction)},
        ]
        _add_track(anim["bones"], bone["name"], "rotate", keys)


def apply_serpentine_undulation(animations: dict, layout: dict, ctrls: dict) -> None:
    """Body segments undulate along a sine wave — snake/serpent motion."""
    motion = ctrls.get("motion_strength", 1.0)
    dur = 4.0 * ctrls.get("idle_duration_scale", 1.0)
    segments = _find_bones_matching(layout, BODY_SEG_RE)
    if not segments:
        return
    # Sort by segment index
    segments.sort(key=lambda pair: int(pair[1].group(1)))
    anim = _ensure_animation(animations, _resolve_anim_name(animations, "idle"))
    n = len(segments)
    for i, (bone, _m) in enumerate(segments):
        # Wave travels head-to-tail with progressive phase delay
        phase = i / max(1, n - 1)
        amp = 3 * motion
        keys = [
            {"time": 0,           "x": 0, "y": amp * math.sin(2 * math.pi * phase)},
            {"time": dur * 0.25,  "x": 0, "y": amp * math.sin(2 * math.pi * (phase + 0.25))},
            {"time": dur * 0.5,   "x": 0, "y": amp * math.sin(2 * math.pi * (phase + 0.5))},
            {"time": dur * 0.75,  "x": 0, "y": amp * math.sin(2 * math.pi * (phase + 0.75))},
            {"time": dur,         "x": 0, "y": amp * math.sin(2 * math.pi * phase)},
        ]
        _add_track(anim["bones"], bone["name"], "translate", keys)


def apply_wing_flap(animations: dict, layout: dict, ctrls: dict) -> None:
    """Wings flap on a 0.6s loop (idle is composed at 4.0s, so wings cycle
    multiple times). Faster flap during win."""
    motion = ctrls.get("motion_strength", 1.0)
    wings = _find_bones_matching(layout, WING_RE)
    if not wings:
        return

    for anim_name, dur, amp_mult in (("idle", 4.0 * ctrls.get("idle_duration_scale", 1.0), 1.0),
                                       ("win", 2.0, 1.6)):
        anim = _ensure_animation(animations, _resolve_anim_name(animations, anim_name))
        flap_amp = 20 * motion * amp_mult
        # 0.6s flap cycle within the animation
        flap_dur = 0.6
        cycles = max(1, int(dur / flap_dur))
        for i, (bone, _m) in enumerate(wings):
            sign = 1 if "L" in (_m.group(1) or "").upper() else -1
            keys = []
            for c in range(cycles):
                t0 = c * flap_dur
                keys.extend([
                    {"time": t0,                   "value": 0},
                    {"time": t0 + flap_dur * 0.25, "value": sign * flap_amp},
                    {"time": t0 + flap_dur * 0.5,  "value": 0},
                    {"time": t0 + flap_dur * 0.75, "value": -sign * flap_amp},
                ])
            keys.append({"time": dur, "value": 0})
            _add_track(anim["bones"], bone["name"], "rotate", keys)


def _resolve_anim_name(animations: dict, suffix: str) -> str:
    """Given a suffix like 'idle' or 'win', find the matching animation name
    in the (already-composed) animations dict. Returns the suffix itself if
    no match (animation will be created)."""
    for name in animations:
        if name.lower().endswith(suffix.lower()) and name != suffix:
            return name
    return suffix


def apply_topology_motion(
    animations: dict, layout: dict, topology_result: dict, ctrls: dict
) -> dict:
    """Overlay topology-appropriate motion onto the already-composed animations.

    Returns the modified animations dict (in-place mutation; return for chaining).
    """
    topology = topology_result.get("topology", "humanoid")
    if topology == "quadruped":
        apply_quadruped_gait(animations, layout, ctrls)
    elif topology == "many_legged":
        apply_many_legged_wave(animations, layout, ctrls)
    elif topology == "serpentine":
        apply_serpentine_undulation(animations, layout, ctrls)
    elif topology == "winged":
        apply_wing_flap(animations, layout, ctrls)
    # Tailed modifier: gentle tail rotation on idle (additive to whatever topology)
    if "tailed" in topology_result.get("modifiers", []):
        tails = _find_bones_matching(layout, TAIL_RE)
        if tails:
            dur = 4.0 * ctrls.get("idle_duration_scale", 1.0)
            motion = ctrls.get("motion_strength", 1.0)
            anim = _ensure_animation(animations, _resolve_anim_name(animations, "idle"))
            for bone, _m in tails:
                _add_track(anim["bones"], bone["name"], "rotate", [
                    {"time": 0,           "value": 0},
                    {"time": dur * 0.5,   "value": 3 * motion},
                    {"time": dur,         "value": 0},
                ])
    return animations
