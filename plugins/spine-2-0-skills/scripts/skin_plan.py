#!/usr/bin/env python3
"""Reviewed multi-skin region variant plan validation."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "spine_slot_animation_skin_plan_v1"
ROOT_FIELDS = {"schema", "skins"}
ROOT_REQUIRED_FIELDS = {"schema", "skins"}
SKIN_FIELDS = {"name", "attachments", "bones", "constraints"}
SKIN_REQUIRED_FIELDS = {"name", "attachments"}
ATTACHMENT_FIELDS = {
    "source_layer",
    "layer_file",
    "target_slot",
    "attachment_key",
    "attachment_name",
    "path",
    "type",
    "x",
    "y",
    "width",
    "height",
}
ATTACHMENT_REQUIRED_FIELDS = {"target_slot", "attachment_key", "path"}
CONSTRAINT_FIELDS = {"ik", "transform", "path", "physics"}


def load_skin_plan(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_and_build_skin_plan(
    layout: dict,
    plan: dict,
    layer_dir: Path,
) -> tuple[dict | None, dict]:
    issues: list[str] = []
    if not isinstance(plan, dict):
        return None, _report({}, ["skin_plan must be an object"], 0)
    _validate_closed_object(plan, "skin_plan", ROOT_FIELDS, ROOT_REQUIRED_FIELDS, issues)
    if plan.get("schema") != EXPECTED_SCHEMA:
        issues.append(f"skin_plan.schema must be {EXPECTED_SCHEMA!r}")

    skins = plan.get("skins")
    if not isinstance(skins, list):
        issues.append("skin_plan.skins must be a list")
        skins = []
    elif not skins:
        issues.append("skin_plan.skins must not be empty")

    slot_names = {slot.get("name") for slot in layout.get("slots", [])}
    default_attachment_keys: dict[str, set[str]] = {}
    for att in layout.get("attachments", []):
        slot = att.get("slot")
        name = att.get("name")
        if isinstance(slot, str) and isinstance(name, str):
            default_attachment_keys.setdefault(slot, set()).add(name)
    atlas_paths_seen = {
        att.get("path")
        for att in layout.get("attachments", [])
        if isinstance(att.get("path"), str)
    }
    names_seen = {"default"}
    built_skins: list[dict] = []

    for skin_idx, skin in enumerate(skins):
        skin_prefix = f"skin_plan.skins[{skin_idx}]"
        if not isinstance(skin, dict):
            issues.append(f"{skin_prefix} must be an object")
            continue
        _validate_closed_object(skin, skin_prefix, SKIN_FIELDS, SKIN_REQUIRED_FIELDS, issues)

        name = skin.get("name")
        if not isinstance(name, str) or not name:
            issues.append(f"{skin_prefix}.name must be a non-empty string")
            continue
        if name in names_seen:
            issues.append(f"{skin_prefix}.name {name!r} duplicates another skin name")
            continue
        names_seen.add(name)

        attachments = skin.get("attachments")
        if not isinstance(attachments, list):
            issues.append(f"{skin_prefix}.attachments must be a list")
            attachments = []
        if not attachments:
            issues.append(f"{skin_prefix}.attachments must not be empty")

        built_attachments: list[dict] = []
        planned_keys: set[tuple[str, str]] = set()
        for att_idx, entry in enumerate(attachments):
            prefix = f"{skin_prefix}.attachments[{att_idx}]"
            if not isinstance(entry, dict):
                issues.append(f"{prefix} must be an object")
                continue
            _validate_closed_object(entry, prefix, ATTACHMENT_FIELDS, ATTACHMENT_REQUIRED_FIELDS, issues)
            if _uses_linked_mesh(entry):
                issues.append(f"{prefix} linkedmesh is not implemented for Phase 6 skin variants")
                continue
            att_type = entry.get("type", "region")
            if att_type != "region":
                issues.append(f"{prefix}.type must be 'region'; linked meshes and mesh variants are not implemented")
                continue

            target_slot = entry.get("target_slot")
            attachment_key = entry.get("attachment_key")
            path = entry.get("path")
            if not isinstance(target_slot, str) or not target_slot:
                issues.append(f"{prefix}.target_slot must be a non-empty string")
                continue
            if target_slot not in slot_names:
                issues.append(f"{prefix}.target_slot {target_slot!r} is not in the rig layout")
                continue
            if not isinstance(attachment_key, str) or not attachment_key:
                issues.append(f"{prefix}.attachment_key must be a non-empty string")
                continue
            if attachment_key not in default_attachment_keys.get(target_slot, set()):
                issues.append(
                    f"{prefix}.attachment_key {attachment_key!r} must match a default attachment for slot {target_slot!r}"
                )
                continue
            if not isinstance(path, str) or not path:
                issues.append(f"{prefix}.path must be a non-empty atlas path")
                continue
            if path in atlas_paths_seen:
                issues.append(f"{prefix}.path {path!r} duplicates an existing atlas path")
                continue
            atlas_paths_seen.add(path)
            key = (target_slot, attachment_key)
            if key in planned_keys:
                issues.append(f"{prefix} duplicates slot/key {target_slot!r}/{attachment_key!r} in skin {name!r}")
                continue
            planned_keys.add(key)

            source_path = _resolve_source_path(layer_dir, entry)
            if source_path is None:
                issues.append(f"{prefix} has no source PNG under {layer_dir}")
                continue

            width, height = _image_size(source_path, prefix, issues)
            width = _positive_number(entry.get("width", width), f"{prefix}.width", issues)
            height = _positive_number(entry.get("height", height), f"{prefix}.height", issues)
            x = _number(entry.get("x", 0), f"{prefix}.x", issues)
            y = _number(entry.get("y", 0), f"{prefix}.y", issues)
            attachment_name = entry.get("attachment_name", attachment_key)
            if not isinstance(attachment_name, str) or not attachment_name:
                issues.append(f"{prefix}.attachment_name must be a non-empty string when supplied")
                continue

            if not any(issue.startswith(prefix) for issue in issues):
                built_attachments.append({
                    "slot": target_slot,
                    "key": attachment_key,
                    "name": attachment_name,
                    "path": path,
                    "type": "region",
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "source_path": str(source_path),
                    "source_layer": entry.get("source_layer"),
                    "layer_file": entry.get("layer_file"),
                })

        bones = _string_list(skin.get("bones", []), f"{skin_prefix}.bones", issues)
        constraints = _constraints(skin.get("constraints", {}), f"{skin_prefix}.constraints", issues)
        if not any(issue.startswith(skin_prefix) for issue in issues):
            built_skins.append({
                "name": name,
                "attachments": built_attachments,
                "bones": bones,
                "constraints": constraints,
            })

    if issues:
        return None, _report(plan, issues, 0)

    return {
        "schema": EXPECTED_SCHEMA,
        "skins": built_skins,
    }, _report(plan, [], len(built_skins))


def skin_atlas_attachments(skin_data: dict | None) -> list[dict]:
    if not skin_data:
        return []
    return [
        attachment
        for skin in skin_data.get("skins", [])
        for attachment in skin.get("attachments", [])
    ]


def _report(plan: dict, issues: list[str], emitted_count: int) -> dict:
    skin_names = []
    if isinstance(plan, dict) and isinstance(plan.get("skins"), list):
        skin_names = [
            skin.get("name")
            for skin in plan.get("skins", [])
            if isinstance(skin, dict) and isinstance(skin.get("name"), str)
        ]
    return {
        "enabled": bool(plan),
        "schema": plan.get("schema") if isinstance(plan, dict) else None,
        "planned_count": len(skin_names),
        "emitted_count": emitted_count,
        "skin_names": skin_names,
        "issue_count": len(issues),
        "issues": issues,
        "linkedmesh_supported": False,
        "review_required": bool(plan),
    }


def _resolve_source_path(layer_dir: Path, entry: dict) -> Path | None:
    source_layer = entry.get("source_layer")
    layer_file = entry.get("layer_file")
    if bool(source_layer) == bool(layer_file):
        return None
    source = str(layer_file or source_layer)
    if _unsafe_relative_path(source):
        return None
    candidates = [layer_dir / source]
    if source_layer:
        candidates.append(layer_dir / f"{Path(source).stem}.png")
    root = layer_dir.resolve()
    safe_candidates = [candidate for candidate in candidates if _is_under(candidate, root)]
    return next((candidate for candidate in safe_candidates if candidate.is_file()), None)


def _image_size(path: Path, prefix: str, issues: list[str]) -> tuple[float, float]:
    try:
        from PIL import Image  # noqa: E402

        with Image.open(path) as img:
            return float(img.width), float(img.height)
    except Exception as exc:  # pragma: no cover - defensive for corrupt fixture files
        issues.append(f"{prefix} source PNG {path} could not be read: {exc}")
        return 0.0, 0.0


def _uses_linked_mesh(entry: dict) -> bool:
    return (
        entry.get("type") in {"linkedmesh", "linked_mesh"}
        or "linkedmesh" in entry
        or "linked_mesh" in entry
        or "parent" in entry
        or "skin" in entry
    )


def _constraints(value: Any, field: str, issues: list[str]) -> dict[str, list[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        issues.append(f"{field} must be an object")
        return {}
    _validate_closed_object(value, field, CONSTRAINT_FIELDS, set(), issues)
    out: dict[str, list[str]] = {}
    for key in sorted(CONSTRAINT_FIELDS):
        if key in value:
            out[key] = _string_list(value.get(key), f"{field}.{key}", issues)
    return out


def _string_list(value: Any, field: str, issues: list[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        issues.append(f"{field} must be a list of names")
        return []
    out: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item:
            issues.append(f"{field}[{idx}] must be a non-empty string")
            continue
        out.append(item)
    return out


def _number(value: Any, field: str, issues: list[str]) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        issues.append(f"{field} must be a finite number")
        return 0.0
    return float(value)


def _positive_number(value: Any, field: str, issues: list[str]) -> float:
    number = _number(value, field, issues)
    if number <= 0:
        issues.append(f"{field} must be greater than 0")
    return number


def _validate_closed_object(
    value: dict,
    name: str,
    allowed: set[str],
    required: set[str],
    issues: list[str],
) -> None:
    for field in sorted(set(value) - allowed):
        issues.append(f"{name}.{field} is not allowed")
    for field in sorted(required - set(value)):
        issues.append(f"{name}.{field} is required")


def _unsafe_relative_path(value: str) -> bool:
    path = Path(value)
    return path.is_absolute() or any(part == ".." for part in path.parts)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    return True
