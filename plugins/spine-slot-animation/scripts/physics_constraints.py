#!/usr/bin/env python3
"""Policy-gated Spine 4.2 physics candidates and constraints."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[1] / "assets" / "physics_policy.json"
SLIDER_FIELDS = ("x", "y", "rotate", "scaleX", "shearX")
DEFAULT_VALUES = {
    "fps": 60,
    "x": 0,
    "y": 0,
    "rotate": 0,
    "scaleX": 0,
    "shearX": 0,
    "limit": 500,
    "inertia": 80,
    "strength": 85,
    "damping": 55,
    "mass": 80,
    "wind": 0,
    "gravity": 0,
    "mix": 1.0,
}
PLAN_META_FIELDS = {"bone", "preset", "overrides", "role", "candidate_role", "name", "order", "reviewed", "force"}

KEYWORD_TO_ROLE = [
    ("dangling_jewelry", "dangling_jewelry"),
    ("dangly_jewelry", "dangling_jewelry"),
    ("dangling", "dangling_jewelry"),
    ("earrings", "earrings"),
    ("earring", "earrings"),
    ("antennae", "antennae"),
    ("antenna", "antennae"),
    ("mustache", "mustache"),
    ("moustache", "mustache"),
    ("necklace", "necklace"),
    ("ponytail", "hair"),
    ("braid", "hair"),
    ("beard", "beard"),
    ("dress", "dress"),
    ("skirt", "skirt"),
    ("cloak", "cloak"),
    ("cape", "cape"),
    ("sleeve", "sleeve"),
    ("scarf", "scarf"),
    ("ribbon", "ribbon"),
    ("chain", "chain"),
    ("belt", "belt"),
    ("tails", "tails"),
    ("tail", "tails"),
    ("wings", "wings"),
    ("wing", "wings"),
    ("robe", "robe"),
    ("hair", "hair"),
]


def load_policy(path: Path | None = None) -> dict:
    """Load the closed local policy used for candidate reporting and emission."""
    return json.loads((path or DEFAULT_POLICY_PATH).read_text())


def _keyword_matches(text: str, keyword: str) -> bool:
    pattern = rf"(^|[^a-z0-9]){re.escape(keyword)}([^a-z0-9]|$)"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _clamp_number(value: Any, low: float, high: float) -> float | int:
    numeric = float(value)
    clamped = min(max(numeric, low), high)
    if isinstance(value, int) and not isinstance(value, bool):
        return int(round(clamped))
    return clamped


def normalize_preset(values: dict, policy: dict) -> dict:
    """Clamp physics values to the local Spine 4.2 policy scale."""
    ranges = policy.get("normalized_field_ranges", {})
    out = dict(values)
    for key, default in DEFAULT_VALUES.items():
        out.setdefault(key, default)
    for key, limits in ranges.items():
        if key in out and _strict_number(out[key]):
            out[key] = _clamp_number(out[key], float(limits[0]), float(limits[1]))
    return out


def _active_sliders(values: dict) -> list[str]:
    return [
        field
        for field in SLIDER_FIELDS
        if _strict_number(values.get(field, 0)) and float(values.get(field, 0)) > 0
    ]


def _strict_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _role_decision(role: str, policy: dict) -> str:
    if role in set(policy.get("default_on_roles", [])):
        return "default_on"
    if role in set(policy.get("review_only_roles", [])):
        return "review_only"
    return "disallowed"


def _candidate_decision(role: str, policy: dict, trusted: bool) -> str:
    decision = _role_decision(role, policy)
    if decision == "default_on" and not trusted:
        return "review_only"
    return decision


def _candidate_for_bone(bone: dict, policy: dict) -> dict | None:
    fields = {
        "semantic_role": str(bone.get("semantic_role") or ""),
        "rig_role": str(bone.get("rig_role") or ""),
        "layer_name": str(bone.get("layer_name") or ""),
        "bone": str(bone.get("name") or ""),
    }
    for keyword, role in KEYWORD_TO_ROLE:
        for source_field, value in fields.items():
            if _keyword_matches(value.replace("-", "_").lower(), keyword):
                preset_key = policy["role_presets"][role]
                preset = normalize_preset(policy["presets"][preset_key], policy)
                active = _active_sliders(preset)
                trusted = source_field in {"semantic_role", "rig_role"}
                return {
                    "bone": fields["bone"],
                    "candidate_role": role,
                    "recommended_physics_preset": preset_key,
                    "policy_decision": _candidate_decision(role, policy, trusted),
                    "source_layer": bone.get("layer_name"),
                    "semantic_role": bone.get("semantic_role"),
                    "active_sliders": active,
                    "trusted_evidence": trusted,
                    "evidence_source": source_field,
                    "evidence": [f"{source_field} matched keyword {keyword!r}"],
                }
    return None


def detect_physics_candidates(layout: dict, policy: dict | None = None) -> list[dict]:
    """Return physics candidates supported by explicit layer or role evidence."""
    policy = policy or load_policy()
    candidates: list[dict] = []
    seen_bones: set[str] = set()
    for b in layout.get("bones", []):
        candidate = _candidate_for_bone(b, policy)
        if candidate and candidate["bone"] not in seen_bones:
            candidates.append(candidate)
            seen_bones.add(candidate["bone"])
    return candidates


def _allowed_plan_fields(policy: dict) -> set[str]:
    return PLAN_META_FIELDS | set(policy.get("normalized_field_ranges", {}))


def _validate_numeric_field(path: str, field: str, value: Any, policy: dict, issues: list[str]) -> None:
    ranges = policy.get("normalized_field_ranges", {})
    if field not in ranges:
        issues.append(f"{path}.{field} is not allowed")
        return
    if not _strict_number(value):
        issues.append(f"{path}.{field} must be a finite number")
        return
    low, high = float(ranges[field][0]), float(ranges[field][1])
    if not low <= float(value) <= high:
        issues.append(f"{path}.{field} must be in range [{low:g}, {high:g}]")


def _validate_plan_entry(entry: Any, index: int, policy: dict) -> list[str]:
    issues: list[str] = []
    path = f"physics plan[{index}]"
    if not isinstance(entry, dict):
        return [f"{path} must be an object"]
    allowed_fields = _allowed_plan_fields(policy)
    for key in entry:
        if key not in allowed_fields:
            issues.append(f"{path}.{key} is not allowed")
    if not isinstance(entry.get("bone"), str) or not entry.get("bone"):
        issues.append(f"{path}.bone is required")
    for key in ("role", "candidate_role", "preset", "name"):
        if key in entry and not isinstance(entry[key], str):
            issues.append(f"{path}.{key} must be a string")
    if "order" in entry and not _strict_int(entry["order"]):
        issues.append(f"{path}.order must be an integer")
    for key in ("reviewed", "force"):
        if key in entry and not isinstance(entry[key], bool):
            issues.append(f"{path}.{key} must be a boolean")
    if entry.get("force") and not entry.get("reviewed"):
        issues.append(f"{path}.force requires reviewed=true")
    preset_key = entry.get("preset")
    if preset_key and preset_key != "custom" and preset_key not in policy.get("presets", {}):
        issues.append(f"{path}.preset {preset_key!r} is not allowed")
    overrides = entry.get("overrides", {})
    if "overrides" in entry and not isinstance(overrides, dict):
        issues.append(f"{path}.overrides must be an object")
        overrides = {}
    for key, value in entry.items():
        if key in policy.get("normalized_field_ranges", {}):
            _validate_numeric_field(path, key, value, policy, issues)
    for key, value in overrides.items():
        _validate_numeric_field(f"{path}.overrides", key, value, policy, issues)
    return issues


def _plan_policy_decision(role: str, policy: dict, reviewed: bool, forced: bool) -> str:
    decision = _role_decision(role, policy)
    if reviewed and forced and role in set(policy.get("allowed_wardrobe_semantics", [])):
        return "default_on"
    if decision == "default_on" and reviewed:
        return "default_on"
    if decision == "default_on":
        return "review_only"
    return decision


def _planned_entries(user_plan: Any, policy: dict, plan_supplied: bool = False) -> list[dict]:
    if user_plan is None:
        if plan_supplied:
            return [{
                "validation_issues": ["physics plan must be a list of objects"],
                "evidence": ["invalid physics plan top-level shape"],
            }]
        return []
    if not isinstance(user_plan, list):
        return [{
            "validation_issues": ["physics plan must be a list of objects"],
            "evidence": ["invalid physics plan top-level shape"],
        }]
    entries = []
    for index, entry in enumerate(user_plan):
        issues = _validate_plan_entry(entry, index, policy)
        if issues:
            entries.append({
                "validation_issues": issues,
                "evidence": ["invalid physics plan entry"],
            })
            continue
        role = entry.get("candidate_role") or entry.get("role")
        preset_key = entry.get("preset")
        if not role and preset_key:
            for policy_role, mapped_preset in policy.get("role_presets", {}).items():
                if mapped_preset == preset_key:
                    role = policy_role
                    break
        if not role:
            role = "custom"
        if not preset_key and role in policy.get("role_presets", {}):
            preset_key = policy["role_presets"][role]
        if not preset_key or preset_key not in policy.get("presets", {}):
            preset_key = "custom"
        base = dict(policy.get("presets", {}).get(preset_key, {}))
        base.update({k: v for k, v in entry.items() if k in policy.get("normalized_field_ranges", {})})
        base.update(entry.get("overrides", {}))
        preset = normalize_preset(base, policy)
        reviewed = bool(entry.get("reviewed"))
        forced = bool(entry.get("force"))
        entries.append({
            "bone": entry.get("bone"),
            "name": entry.get("name"),
            "order": entry.get("order"),
            "candidate_role": role,
            "recommended_physics_preset": preset_key,
            "policy_decision": _plan_policy_decision(role, policy, reviewed, forced),
            "plan_reviewed": reviewed,
            "plan_forced": forced,
            "trusted_evidence": reviewed,
            "evidence_source": "reviewed_physics_plan" if reviewed else "physics_plan",
            "active_sliders": _active_sliders(preset),
            "preset_values": preset,
            "evidence": ["reviewed physics plan entry" if reviewed else "physics plan entry"],
        })
    return entries


def validate_emitted_constraints(constraints: list[dict], policy: dict, bone_names: set[str] | None = None) -> list[str]:
    """Validate emitted Spine physics constraints against the local closed policy."""
    issues: list[str] = []
    ranges = policy.get("normalized_field_ranges", {})
    allowed_fields = {"name", "order", "bone"} | set(ranges)
    for index, constraint in enumerate(constraints):
        path = f"physics[{index}]"
        if not isinstance(constraint, dict):
            issues.append(f"{path} must be an object")
            continue
        for key in constraint:
            if key not in allowed_fields:
                issues.append(f"{path}.{key} is not allowed")
        if not isinstance(constraint.get("name"), str) or not constraint.get("name"):
            issues.append(f"{path}.name is required")
        if not isinstance(constraint.get("bone"), str) or not constraint.get("bone"):
            issues.append(f"{path}.bone is required")
        elif bone_names is not None and constraint["bone"] not in bone_names:
            issues.append(f"{path}.bone references unknown bone {constraint['bone']!r}")
        if "order" in constraint and not _strict_int(constraint["order"]):
            issues.append(f"{path}.order must be an integer")
        for field in ranges:
            if field in constraint:
                _validate_numeric_field(path, field, constraint[field], policy, issues)
    return issues


def build_physics_constraints_with_report(
    layout: dict,
    user_plan: Any = None,
    policy: dict | None = None,
    emit_enabled: bool = True,
    plan_supplied: bool = False,
) -> dict:
    """Build policy-gated constraints plus validation/reporting metadata."""
    policy = policy or load_policy()
    bone_by_name = {b["name"]: b for b in layout.get("bones", []) if b.get("name")}
    errors: list[str] = []
    warnings: list[str] = []
    zero_length_warnings: list[dict] = []
    max_violations: list[str] = []
    candidates = detect_physics_candidates(layout, policy)
    by_bone = {c["bone"]: c for c in candidates}

    for entry in _planned_entries(user_plan, policy, plan_supplied=plan_supplied):
        if entry.get("validation_issues"):
            errors.extend(entry["validation_issues"])
            continue
        bone = entry.get("bone")
        if not bone or bone not in bone_by_name:
            errors.append(f"physics plan references unknown bone {bone!r}")
            continue
        candidate = dict(entry)
        candidate["source_layer"] = bone_by_name[bone].get("layer_name")
        candidate["semantic_role"] = bone_by_name[bone].get("semantic_role")
        by_bone[bone] = candidate

    candidates = list(by_bone.values())
    for candidate in candidates:
        bone = candidate["bone"]
        preset_key = candidate["recommended_physics_preset"]
        values = candidate.get("preset_values") or normalize_preset(policy["presets"][preset_key], policy)
        active = _active_sliders(values)
        candidate["active_sliders"] = active
        candidate["preview_required"] = bool(policy.get("preview_required", True))
        if candidate["policy_decision"] != "default_on":
            candidate["review_required"] = True
            candidate["review_reason"] = f"policy decision is {candidate['policy_decision']}"
        else:
            candidate["review_required"] = False
        if not candidate.get("trusted_evidence", False):
            candidate["review_required"] = True
            candidate["review_reason"] = "raw keyword evidence requires semantic evidence or reviewed physics plan"
        if not emit_enabled:
            candidate["review_required"] = True
            candidate["review_reason"] = "physics emission disabled; candidate recorded for review"
        length = float(bone_by_name.get(bone, {}).get("length", 0) or 0)
        review_sliders = set(policy.get("zero_length_review_sliders", []))
        blocked_sliders = [slider for slider in active if slider in review_sliders]
        if length <= 0 and blocked_sliders:
            warning = {
                "bone": bone,
                "candidate_role": candidate["candidate_role"],
                "active_sliders": blocked_sliders,
                "message": (
                    f"physics candidate {bone!r} uses {blocked_sliders} on a zero-length bone; "
                    "Spine Editor review must set a bone length or adjust sliders"
                ),
            }
            zero_length_warnings.append(warning)
            warnings.append(warning["message"])
            candidate["review_required"] = True
            candidate["review_reason"] = "zero-length bone with rotate/scale/shear physics"

    constraints: list[dict] = []
    if emit_enabled:
        emittable = [c for c in candidates if c["policy_decision"] == "default_on"]
        max_constraints = int(policy["max_constraints_per_symbol"])
        if len(emittable) > max_constraints:
            msg = f"physics constraints requested {len(emittable)} exceeds max_constraints_per_symbol {max_constraints}"
            errors.append(msg)
            max_violations.append(msg)
        else:
            next_order = 10
            for candidate in emittable:
                preset_key = candidate["recommended_physics_preset"]
                values = candidate.get("preset_values") or normalize_preset(policy["presets"][preset_key], policy)
                constraint = {
                    "name": candidate.get("name") or f"{candidate['bone']}_physics",
                    "order": candidate.get("order") or next_order,
                    "bone": candidate["bone"],
                    **values,
                }
                constraints.append(constraint)
                next_order = max(next_order, int(constraint["order"])) + 1
            errors.extend(validate_emitted_constraints(constraints, policy, set(bone_by_name)))

    return {
        "constraints": constraints,
        "candidates": candidates,
        "errors": errors,
        "warnings": warnings,
        "zero_length_bone_warnings": zero_length_warnings,
        "max_constraint_violations": max_violations,
        "review_required": any(c.get("review_required") for c in candidates),
        "active_sliders": {c["bone"]: c.get("active_sliders", []) for c in candidates},
        "policy": {
            "schema": policy.get("schema"),
            "max_constraints_per_symbol": policy.get("max_constraints_per_symbol"),
            "preview_required": policy.get("preview_required"),
            "default_on_roles": policy.get("default_on_roles", []),
            "review_only_roles": policy.get("review_only_roles", []),
            "allowed_wardrobe_semantics": policy.get("allowed_wardrobe_semantics", []),
            "normalized_field_ranges": policy.get("normalized_field_ranges", {}),
        },
    }


def build_physics_constraints(layout: dict, user_plan: list[dict] | None = None) -> list[dict]:
    return build_physics_constraints_with_report(layout, user_plan, emit_enabled=True)["constraints"]


def main() -> int:
    p = argparse.ArgumentParser(description="Emit Spine 4.2 physics constraint definitions.")
    p.add_argument("--layout", required=True, help="Path to rig_layout.json")
    p.add_argument("--plan", help="Optional user plan JSON for custom physics setup.")
    p.add_argument("--out", required=True, help="Output path for the physics-constraints JSON array.")
    args = p.parse_args()

    layout = json.loads(Path(args.layout).read_text())
    plan = json.loads(Path(args.plan).read_text()) if args.plan else None
    result = build_physics_constraints_with_report(layout, plan, emit_enabled=True, plan_supplied=bool(args.plan))
    constraints = result["constraints"]

    Path(args.out).write_text(json.dumps(constraints, indent=2))
    print(f"wrote {args.out}")
    print(f"  emitted {len(constraints)} physics constraints")
    if result["errors"]:
        for error in result["errors"]:
            print(f"  ERROR: {error}")
        return 2
    for c in constraints:
        print(f"    {c['name']:40s} bone={c['bone']}  y={c.get('y')}  rotate={c.get('rotate')}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
