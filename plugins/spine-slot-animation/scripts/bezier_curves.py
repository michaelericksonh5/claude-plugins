#!/usr/bin/env python3
"""Opt-in 4.x Bezier curve policy for supported numeric timelines."""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any


PROFILE_NAME = "spine_43_bezier"
LEGACY_PROFILE_NAME = "spine_42_bezier"
SUPPORTED_PRESETS = {
    "ease_in": (0.42, 0.0, 1.0, 1.0),
    "ease_out": (0.0, 0.0, 0.58, 1.0),
    "ease_in_out": (0.42, 0.0, 0.58, 1.0),
    "overshoot": (0.34, 0.0, 0.64, 1.35),
    "settle": (0.20, 0.90, 0.30, 1.0),
}

_BONE_CHANNELS = {
    "rotate": ("value",),
    "translate": ("x", "y"),
    "scale": ("x", "y"),
}


def apply_bezier_profile(animations: dict[str, dict], preset_name: str) -> dict[str, Any]:
    """Add numeric Bezier curve arrays to supported timelines in-place."""
    if preset_name not in SUPPORTED_PRESETS:
        raise ValueError(f"unknown Bezier preset {preset_name!r}")
    before = _snapshot_timing_and_values(animations)
    curve_count = 0
    preset = SUPPORTED_PRESETS[preset_name]

    for anim in animations.values():
        for tracks in anim.get("bones", {}).values():
            for timeline_name, keys in tracks.items():
                channels = _BONE_CHANNELS.get(timeline_name)
                if channels:
                    curve_count += _apply_to_timeline(keys, channels, preset)
        for tracks in anim.get("slots", {}).values():
            rgba_keys = tracks.get("rgba")
            if isinstance(rgba_keys, list):
                curve_count += _apply_to_timeline(rgba_keys, ("r", "g", "b", "a"), preset)
            alpha_keys = tracks.get("alpha")
            if isinstance(alpha_keys, list):
                curve_count += _apply_to_timeline(alpha_keys, ("alpha",), preset)

    issues = validate_curve_application_stability(before, animations)
    if issues:
        raise ValueError("; ".join(issues))
    return {
        "profile": PROFILE_NAME,
        "preset": preset_name,
        "curves_emitted": curve_count,
        "supported_timelines": ["bone.rotate", "bone.translate", "bone.scale", "slot.rgba", "slot.alpha"],
        "key_times_preserved": True,
        "source_durations_preserved": True,
        "endpoint_values_preserved": True,
        "source_durations": {
            timeline_id: data["duration"]
            for timeline_id, data in sorted(before.items())
        },
        "source_key_times": {
            timeline_id: data["times"]
            for timeline_id, data in sorted(before.items())
        },
    }


def validate_curve_application_stability(before: dict[str, Any], animations: dict[str, dict]) -> list[str]:
    """Validate Bezier decoration did not move keys or change endpoint values."""
    after = _snapshot_timing_and_values(animations)
    issues: list[str] = []
    for timeline_id, before_data in before.items():
        after_data = after.get(timeline_id)
        if after_data is None:
            issues.append(f"{timeline_id} disappeared during Bezier application")
            continue
        if after_data["times"] != before_data["times"]:
            issues.append(f"{timeline_id} key times changed during Bezier application")
        if after_data["duration"] != before_data["duration"]:
            issues.append(f"{timeline_id} source duration changed during Bezier application")
        if after_data["first"] != before_data["first"] or after_data["last"] != before_data["last"]:
            issues.append(f"{timeline_id} endpoint values changed during Bezier application")
        if (
            len(before_data["times"]) > 1
            and before_data["first"] == before_data["last"]
            and after_data["first"] != after_data["last"]
        ):
            issues.append(f"{timeline_id} no longer closes its loop after Bezier application")
    for timeline_id in after:
        if timeline_id not in before:
            issues.append(f"{timeline_id} was added during Bezier application")
    return issues


def validate_timeline_curves(skel: dict, export_profile: str | None = None) -> list[str]:
    """Validate emitted curve fields against the supported local policy."""
    errors: list[str] = []
    for anim_name, anim in skel.get("animations", {}).items():
        for bone_name, tracks in anim.get("bones", {}).items():
            for timeline_name, keys in tracks.items():
                channel_count = len(_BONE_CHANNELS.get(timeline_name, ()))
                path = f"animation {anim_name!r} bone {bone_name} {timeline_name}"
                errors.extend(_validate_keys(path, keys, channel_count, export_profile))
        for slot_name, tracks in anim.get("slots", {}).items():
            for timeline_name, keys in tracks.items():
                path = f"animation {anim_name!r} slot {slot_name} {timeline_name}"
                if timeline_name in {"attachment", "sequence"}:
                    errors.extend(_validate_no_curve_fields(path, keys))
                    continue
                channel_count = {"rgba": 4, "alpha": 1}.get(timeline_name, 0)
                errors.extend(_validate_keys(path, keys, channel_count, export_profile))
        for timeline_name in ("events", "drawOrder", "draw_order"):
            path = f"animation {anim_name!r} {timeline_name}"
            errors.extend(_validate_no_curve_fields(path, anim.get(timeline_name)))
        for constraint_type in ("ik", "transform", "path", "physics"):
            for constraint_name, keys in anim.get(constraint_type, {}).items():
                path = f"animation {anim_name!r} {constraint_type} {constraint_name}"
                errors.extend(_validate_keys(path, keys, 0, export_profile))
    return errors


def _apply_to_timeline(keys: list[dict], channels: tuple[str, ...], preset: tuple[float, float, float, float]) -> int:
    applied = 0
    if not isinstance(keys, list) or len(keys) < 2:
        return applied
    for idx, key in enumerate(keys[:-1]):
        next_key = keys[idx + 1]
        if not isinstance(key, dict) or not isinstance(next_key, dict):
            continue
        key["curve"] = _absolute_curve(key, next_key, channels, preset)
        applied += 1
    return applied


def _absolute_curve(
    key: dict,
    next_key: dict,
    channels: tuple[str, ...],
    preset: tuple[float, float, float, float],
) -> list[float]:
    x1, y1, x2, y2 = preset
    t0 = float(key.get("time", 0.0))
    t1 = float(next_key.get("time", t0))
    dt = t1 - t0
    out: list[float] = []
    for channel in channels:
        v0 = _channel_value(key, channel)
        v1 = _channel_value(next_key, channel)
        dv = v1 - v0
        out.extend([
            t0 + x1 * dt,
            v0 + y1 * dv,
            t0 + x2 * dt,
            v0 + y2 * dv,
        ])
    return out


def _snapshot_timing_and_values(animations: dict[str, dict]) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for anim_name, anim in animations.items():
        for bone_name, tracks in anim.get("bones", {}).items():
            for timeline_name, keys in tracks.items():
                channels = _BONE_CHANNELS.get(timeline_name)
                if channels:
                    snapshot[f"{anim_name}.bones.{bone_name}.{timeline_name}"] = _timeline_snapshot(keys, channels)
        for slot_name, tracks in anim.get("slots", {}).items():
            if "rgba" in tracks:
                snapshot[f"{anim_name}.slots.{slot_name}.rgba"] = _timeline_snapshot(
                    tracks["rgba"],
                    ("r", "g", "b", "a"),
                )
            if "alpha" in tracks:
                snapshot[f"{anim_name}.slots.{slot_name}.alpha"] = _timeline_snapshot(
                    tracks["alpha"],
                    ("alpha",),
                )
    return deepcopy(snapshot)


def _timeline_snapshot(keys: list[dict], channels: tuple[str, ...]) -> dict[str, Any]:
    times = [key.get("time", 0) for key in keys]
    values = [tuple(_channel_value(key, channel) for channel in channels) for key in keys]
    return {
        "times": times,
        "duration": times[-1] if times else 0,
        "first": values[0] if values else (),
        "last": values[-1] if values else (),
    }


def _channel_value(key: dict, channel: str) -> float:
    if channel in {"r", "g", "b", "a"}:
        rgba = _parse_rgba(key.get("color", "ffffffff"))
        return rgba[{"r": 0, "g": 1, "b": 2, "a": 3}[channel]]
    value = key.get(channel)
    if value is None and channel == "alpha":
        value = key.get("value")
    return float(value if value is not None else 0.0)


def _parse_rgba(color: str) -> tuple[float, float, float, float]:
    if not isinstance(color, str) or len(color) != 8:
        return (1.0, 1.0, 1.0, 1.0)
    return tuple(int(color[idx:idx + 2], 16) / 255.0 for idx in range(0, 8, 2))  # type: ignore[return-value]


def _validate_keys(path: str, keys: Any, channel_count: int, export_profile: str | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(keys, list):
        return errors
    for idx, key in enumerate(keys):
        if not isinstance(key, dict) or "curve" not in key:
            continue
        curve = key["curve"]
        if export_profile not in {PROFILE_NAME, LEGACY_PROFILE_NAME}:
            errors.append(f"{path} has curve but export_profile must be {PROFILE_NAME!r}")
            continue
        if isinstance(curve, str):
            errors.append(f"{path} has unsupported curve string {curve!r}")
            continue
        if not isinstance(curve, list):
            errors.append(f"{path} curve must be a numeric array")
            continue
        if channel_count <= 0:
            errors.append(f"{path} does not support Bezier curve arrays")
            continue
        expected = channel_count * 4
        if len(curve) != expected:
            errors.append(f"{path} curve array length {len(curve)} must be {expected}")
            continue
        if not all(_strict_number(value) for value in curve):
            errors.append(f"{path} curve array must contain only finite numbers")
            continue
        if idx + 1 >= len(keys) or not isinstance(keys[idx + 1], dict):
            errors.append(f"{path} curve has no next key interval")
            continue
        t0 = key.get("time", 0)
        t1 = keys[idx + 1].get("time", 0)
        if not _strict_number(t0) or not _strict_number(t1):
            errors.append(f"{path} key times must be finite numbers")
            continue
        t0 = float(t0)
        t1 = float(t1)
        if t1 < t0:
            errors.append(f"{path} next key time {t1} must be >= current key time {t0}")
            continue
        for channel_idx in range(channel_count):
            offset = channel_idx * 4
            handle_1_time = float(curve[offset])
            handle_2_time = float(curve[offset + 2])
            if not (t0 <= handle_1_time <= t1):
                errors.append(
                    f"{path} curve handle time {handle_1_time} is outside key interval [{t0}, {t1}]"
                )
            if not (t0 <= handle_2_time <= t1):
                errors.append(
                    f"{path} curve handle time {handle_2_time} is outside key interval [{t0}, {t1}]"
                )
            if handle_1_time > handle_2_time:
                errors.append(
                    f"{path} curve handle times must be monotonic within key interval [{t0}, {t1}]"
                )
    return errors


def _validate_no_curve_fields(path: str, keys: Any) -> list[str]:
    errors: list[str] = []
    for key in keys if isinstance(keys, list) else []:
        if isinstance(key, dict) and "curve" in key:
            errors.append(f"{path} must not contain curve fields")
    return errors


def _strict_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
