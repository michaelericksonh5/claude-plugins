#!/usr/bin/env python3
"""Classify and validate animation loop/settle endpoints in emitted Spine JSON."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


SCHEMA = "spine_slot_animation_loop_validation_v1"
TOLERANCE = 0.000001

BONE_TIMELINE_FIELDS = {
    "translate": {"x": 0.0, "y": 0.0},
    "rotate": {"value": 0.0},
    "scale": {"x": 1.0, "y": 1.0},
    "shear": {"x": 0.0, "y": 0.0},
}

SYMBOL_SETUP_PATTERNS = {
    "hp_symbol": r"^HP\d+$",
    "mp_symbol": r"^MP\d+$",
    "lp_symbol": r"^LP\d+$",
    "wild_symbol": r"^WD\d+$",
    "scatter_symbol": r"^SC\d+$",
    "value_symbol": r"^WYS\d+$",
    "bonus_symbol": r"^BO\d+$",
    "bo_special_symbol": r"^BO\d+$",
    "jackpot_symbol": r"^JP\d+$",
    "special_feature_symbol": r"^SF\d+$",
}


def classify_animation_intent(animation_name: str, family: str | None = None) -> str:
    """Return setup, loop, settle_to_setup, transition, or burst for an animation."""
    lower = animation_name.lower()

    if family in SYMBOL_SETUP_PATTERNS and re.match(SYMBOL_SETUP_PATTERNS[family], animation_name):
        return "setup"

    if animation_name == "Avatar" or re.match(r"^State\d+Idle$", animation_name):
        return "loop"
    if lower in {"meteridle", "transitionidle", "winframeidle", "celebration_loop"}:
        return "loop"
    if lower.endswith(("idle", "breathe", "smart")):
        return "loop"

    if re.match(r"^State\d+Awarded$", animation_name) or re.match(r"^State\d+Collect$", animation_name):
        return "settle_to_setup"
    if family in SYMBOL_SETUP_PATTERNS and lower.endswith(("land", "win")):
        return "settle_to_setup"

    if (
        re.match(r"^State\d+to\d+$", animation_name)
        or re.match(r"^State\d+Close$", animation_name)
        or animation_name in {"intro", "outro", "FB_Transition", "SB_Transition", "WinFrame", "WinFrameExplode"}
    ):
        return "transition"

    if lower == "burst" or lower.startswith("celebration_fx_") or lower.startswith("tier_") or lower == "grandjackpot":
        return "burst"

    return "setup"


def validate_animation_loops(skel: dict[str, Any], family: str | None = None) -> dict[str, Any]:
    """Inspect final emitted Spine JSON and report clear loop/settle endpoint issues."""
    animations = skel.get("animations", {})
    animation_reports: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, Any]] = []

    for animation_name, animation in animations.items():
        intent = classify_animation_intent(animation_name, family)
        animation_issues: list[dict[str, Any]] = []
        if intent == "loop":
            animation_issues.extend(_validate_loop_animation(animation_name, animation))
        elif intent == "settle_to_setup":
            animation_issues.extend(_validate_settle_animation(animation_name, animation))
        issues.extend(animation_issues)
        animation_reports[animation_name] = {
            "intent": intent,
            "status": "ok" if not animation_issues else "failed",
            "issue_count": len(animation_issues),
        }

    return {
        "schema": SCHEMA,
        "status": "ok" if not issues else "failed",
        "animations": animation_reports,
        "loop_count": sum(1 for item in animation_reports.values() if item["intent"] == "loop"),
        "settle_count": sum(1 for item in animation_reports.values() if item["intent"] == "settle_to_setup"),
        "issues": issues,
    }


def _validate_loop_animation(animation_name: str, animation: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for bone_name, tracks in animation.get("bones", {}).items():
        if not isinstance(tracks, dict):
            continue
        for timeline_name, keys in tracks.items():
            if timeline_name not in BONE_TIMELINE_FIELDS or not _key_list(keys):
                continue
            first = keys[0]
            last = keys[-1]
            for field, default in BONE_TIMELINE_FIELDS[timeline_name].items():
                expected = first.get(field, default)
                actual = last.get(field, default)
                if not _values_equal(expected, actual):
                    issues.append(_issue(
                        "loop_endpoint_mismatch",
                        animation_name,
                        "loop",
                        "bone",
                        bone_name,
                        timeline_name,
                        field,
                        expected,
                        actual,
                    ))

    for slot_name, tracks in animation.get("slots", {}).items():
        if not isinstance(tracks, dict):
            continue
        for timeline_name, keys in tracks.items():
            if timeline_name not in {"rgba", "rgba2", "alpha", "attachment", "sequence"} or not _key_list(keys):
                continue
            first_state = _comparable_slot_state(keys[0])
            last_state = _comparable_slot_state(keys[-1])
            for field in sorted(set(first_state) | set(last_state)):
                expected = first_state.get(field)
                actual = last_state.get(field)
                if not _values_equal(expected, actual):
                    issues.append(_issue(
                        "loop_endpoint_mismatch",
                        animation_name,
                        "loop",
                        "slot",
                        slot_name,
                        timeline_name,
                        field,
                        expected,
                        actual,
                    ))
    return issues


def _validate_settle_animation(animation_name: str, animation: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for bone_name, tracks in animation.get("bones", {}).items():
        if not isinstance(tracks, dict):
            continue
        for timeline_name, keys in tracks.items():
            if timeline_name not in BONE_TIMELINE_FIELDS or not _key_list(keys):
                continue
            last = keys[-1]
            for field, expected in BONE_TIMELINE_FIELDS[timeline_name].items():
                actual = last.get(field, expected)
                if not _values_equal(expected, actual):
                    issues.append(_issue(
                        "settle_endpoint_mismatch",
                        animation_name,
                        "settle_to_setup",
                        "bone",
                        bone_name,
                        timeline_name,
                        field,
                        expected,
                        actual,
                    ))
    return issues


def _key_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(isinstance(item, dict) for item in value)


def _comparable_slot_state(key: dict[str, Any]) -> dict[str, Any]:
    return {
        field: value
        for field, value in key.items()
        if field not in {"time", "curve"}
    }


def _values_equal(expected: Any, actual: Any) -> bool:
    if _is_number(expected) and _is_number(actual):
        return abs(float(expected) - float(actual)) <= TOLERANCE
    return expected == actual


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _issue(
    code: str,
    animation_name: str,
    intent: str,
    scope: str,
    target: str,
    timeline: str,
    field: str,
    expected: Any,
    actual: Any,
) -> dict[str, Any]:
    return {
        "code": code,
        "animation": animation_name,
        "intent": intent,
        "scope": scope,
        "target": target,
        "timeline": timeline,
        "field": field,
        "expected": expected,
        "actual": actual,
        "message": (
            f"{animation_name} {scope} {target} {timeline}.{field} "
            f"ends at {actual!r}; expected {expected!r} for {intent}"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Spine animation loop and settle endpoints.")
    parser.add_argument("spine_json", help="Path to shared_symbols.json")
    parser.add_argument("--family", help="Recipe family key used for symbol setup/settle classification.")
    args = parser.parse_args()

    skel = json.loads(Path(args.spine_json).read_text())
    report = validate_animation_loops(skel, args.family)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
