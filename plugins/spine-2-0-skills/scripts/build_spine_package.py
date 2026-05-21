#!/usr/bin/env python3
"""End-to-end Spine package builder.

ONE COMMAND that takes a folder of per-layer PNGs (with optional manifest)
plus a recipe family, and emits a complete Spine package:

  shared_symbols.json
  shared_symbols.atlas
  shared_symbols.png
  validation_report.json
  rig_layout.json
  layer_interpretation.json

USE
  # Layered HP character with bounded controls:
  python build_spine_package.py \
      --layer-dir ./HP3_layers \
      --family hp_symbol --rank 3 \
      --doc-width 178 --doc-height 178 \
      --controls more_bouncy.controls.json \
      --out-dir ./HP3_out

  # Layered HP character with IK on win + events:
  python build_spine_package.py \
      --layer-dir ./HP3_layers \
      --family hp_symbol --rank 3 \
      --doc-width 178 --doc-height 178 \
      --enable-ik \
      --enable-events ./events_plan.json \
      --out-dir ./HP3_out_advanced

  # Avatar with state graph:
  python build_spine_package.py --layer-dir ./MyAvatar --family avatar \
      --doc-width 178 --doc-height 178 --out-dir ./MyAvatar_out

PIPELINE
  1. interpret_layers — semantic roles, alpha polarity, animation uses
  2. build_rig_layout — parent-local bones, slot order, attachments
  3. compose_animations / compose_avatar_animations — 4.x timelines
  4. build_atlas — alpha-trim, RGB bleed, 1-px edge extrusion
  5. (gated) build_advanced_features — IK / transform / clipping / events
  6. assemble shared_symbols.json — current 4.x contract by construction
  7. validate — strict 4.x checks (skins array, rotate value, rgba, etc.)

DEPENDENCIES
  Pillow (auto-installed on first run for the atlas builder).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

# Make sibling imports work whether called directly or as a module
sys.path.insert(0, str(Path(__file__).resolve().parent))

from interpret_layers import interpret_layers  # noqa: E402
from build_rig_layout import build_rig_layout  # noqa: E402
from compose_animations import FAMILY_TIERS, compose_animations_for_family, _validate_controls  # noqa: E402
from build_avatar_states import avatar_expected_events, build_avatar_state_manifest, compose_avatar_animations  # noqa: E402
import build_atlas  # noqa: E402
import build_advanced_features as adv  # noqa: E402
import project_context as pc  # noqa: E402
import learning_log as ll  # noqa: E402
import physics_constraints as physics  # noqa: E402
import build_preview_html as preview_html  # noqa: E402
import detect_topology as topology_mod  # noqa: E402
import compose_topology_motion as topology_motion  # noqa: E402
import sequence_attachments as seqattr  # noqa: E402
import mesh_plan as meshplan  # noqa: E402
import skin_plan as skinplan  # noqa: E402
import bezier_curves  # noqa: E402
import ui_system_policy as ui_policy  # noqa: E402
import production_export_gate as peg  # noqa: E402
import create_spine_project as native_spine  # noqa: E402
import loop_validation  # noqa: E402
import package_spine_editor_handoff as handoff  # noqa: E402
import spine_version_policy as spine_versions  # noqa: E402
from source_art_guard import write_guard_error  # noqa: E402

SPINE_VERSION = spine_versions.DEFAULT_SPINE_EDITOR_VERSION
FPS = 24
PAGE_NAME = "shared_symbols.png"
ATLAS_NAME = "shared_symbols.atlas"
JSON_NAME = "shared_symbols.json"
REPORT_NAME = "validation_report.json"
AVATAR_MANIFEST_NAME = "avatar_state_manifest.json"


def output_file_status(out_dir: Path) -> dict:
    required = [JSON_NAME, ATLAS_NAME, PAGE_NAME]
    files = {}
    missing = []
    for name in required:
        path = out_dir / name
        exists = path.is_file()
        files[name] = {
            "exists": exists,
            "bytes": path.stat().st_size if exists else 0,
        }
        if not exists:
            missing.append(name)
    return {
        "schema": "spine_slot_animation_output_files_v1",
        "required": required,
        "files": files,
        "missing": missing,
        "status": "ok" if not missing else "failed",
    }


def assemble_skeleton_json(
    layout: dict,
    animations: dict,
    doc_w: float,
    doc_h: float,
    ik_constraints: list[dict] | None = None,
    extra_ik_bones: list[dict] | None = None,
    transform_constraints: list[dict] | None = None,
    clip_slots: list[dict] | None = None,
    clip_attachments: list[dict] | None = None,
    event_defs: dict | None = None,
    physics_constraints_list: list[dict] | None = None,
    skin_plan_data: dict | None = None,
    spine_version: str = SPINE_VERSION,
) -> dict:
    """Assemble the full shared_symbols.json structure for Spine 4.x.

    Critical 4.x contract points enforced here:
      - skins is an ARRAY of skin objects, not a 3.8 object form
      - rotate keys use "value" (composed by animation builders)
      - slot color timelines use "rgba" (composed by animation builders)
      - rgba2 is omitted unless slot has setup "dark" (we don't emit dark)
      - skeleton.width/height = DOC size, not atlas page size
      - spine version is an approved 4.x target line
      - blend defaults to omitted/"normal"
      - root bone is named "root"
    """
    bones_out: list[dict] = []
    for b in layout["bones"]:
        out: dict[str, Any] = {"name": b["name"]}
        if b.get("parent"):
            out["parent"] = b["parent"]
            if b.get("x") not in (None, 0):
                out["x"] = b["x"]
            if b.get("y") not in (None, 0):
                out["y"] = b["y"]
            if b.get("rotation"):
                out["rotation"] = b["rotation"]
        bones_out.append(out)
    # Add IK target bones (if any)
    for b in (extra_ik_bones or []):
        out = {"name": b["name"]}
        if b.get("parent"):
            out["parent"] = b["parent"]
        if b.get("x"):
            out["x"] = b["x"]
        if b.get("y"):
            out["y"] = b["y"]
        if b.get("rotation"):
            out["rotation"] = b["rotation"]
        bones_out.append(out)

    slots_out: list[dict] = []
    for s in layout["slots"]:
        out = {
            "name": s["name"],
            "bone": s["bone"],
        }
        if s.get("attachment") is not None:
            out["attachment"] = s["attachment"]
        if s.get("setup_color", "ffffffff") != "ffffffff":
            out["color"] = s["setup_color"]
        # H5G 4.x contract: never emit "blend"; every slot is normal.
        slots_out.append(out)
    # Insert clipping slots before their end_slot in draw order.
    # Setup attachment is omitted (slot has no default attachment); animations
    # toggle the clipping via the slot's attachment timeline. This matches the
    # official "Toggling clipping on/off in an animation" pattern and keeps
    # the strict compatibility checker (which only fully validates region attachments)
    # from misreading the clipping attachment as a missing region.
    if clip_slots and clip_attachments:
        att_by_slot = {ca["slot"]: ca for ca in clip_attachments}
        for cs in clip_slots:
            end_slot = att_by_slot[cs["name"]]["end"]
            end_idx = next(
                (i for i, s in enumerate(slots_out) if s["name"] == end_slot),
                len(slots_out),
            )
            slots_out.insert(end_idx, {
                "name": cs["name"],
                "bone": cs["bone"],
            })

    # Skins ARRAY form (4.x requirement)
    default_attachments: dict[str, dict] = {}
    for att in layout["attachments"]:
        if att.get("type") == "mesh":
            attachment = {
                "type": "mesh",
                "path": att["path"],
                "uvs": att["uvs"],
                "triangles": att["triangles"],
                "vertices": att["vertices"],
                "hull": att["hull"],
                "width": att["width"],
                "height": att["height"],
            }
            if att.get("edges"):
                attachment["edges"] = att["edges"]
            if att.get("color"):
                attachment["color"] = att["color"]
        else:
            attachment = {
                "type": att.get("type", "region"),
                "path": att["path"],
                "x": att.get("x", 0),
                "y": att.get("y", 0),
                "width": att["width"],
                "height": att["height"],
            }
        if att.get("sequence"):
            attachment["sequence"] = att["sequence"]
        default_attachments.setdefault(att["slot"], {})[att["name"]] = attachment
    for ca in (clip_attachments or []):
        default_attachments.setdefault(ca["slot"], {})[ca["name"]] = {
            "type": "clipping",
            "end": ca["end"],
            "vertexCount": ca["vertexCount"],
            "vertices": ca["vertices"],
        }
    skins = [{"name": "default", "attachments": default_attachments}]
    if skin_plan_data:
        for planned_skin in skin_plan_data.get("skins", []):
            skin_attachments: dict[str, dict] = {}
            for att in planned_skin.get("attachments", []):
                skin_attachments.setdefault(att["slot"], {})[att["key"]] = {
                    "type": "region",
                    "path": att["path"],
                    "x": att.get("x", 0),
                    "y": att.get("y", 0),
                    "width": att["width"],
                    "height": att["height"],
                }
            skin_out: dict[str, Any] = {
                "name": planned_skin["name"],
                "attachments": skin_attachments,
            }
            if planned_skin.get("bones"):
                skin_out["bones"] = planned_skin["bones"]
            constraints = planned_skin.get("constraints", {})
            for constraint_type in ("ik", "transform", "path", "physics"):
                if constraints.get(constraint_type):
                    skin_out[constraint_type] = constraints[constraint_type]
            skins.append(skin_out)

    skel: dict = {
        "skeleton": {
            "hash": "spine-slot-animation-portable",
            "spine": spine_version,
            "x": 0,
            "y": 0,
            "width": int(doc_w),
            "height": int(doc_h),
            "fps": FPS,
            "images": "./",
            "audio": "",
        },
        "bones": bones_out,
        "slots": slots_out,
        "skins": skins,
        "animations": animations,
    }
    if ik_constraints:
        skel["ik"] = ik_constraints
    if transform_constraints:
        skel["transform"] = transform_constraints
    if physics_constraints_list:
        skel["physics"] = physics_constraints_list
    if event_defs:
        skel["events"] = event_defs
    return skel


def validate_skeleton(skel: dict, atlas_records: list[dict], export_profile: str | None = None) -> dict:
    """Strict 4.x contract checks mirroring the H5G compatibility checker."""
    errors: list[str] = []
    warnings: list[str] = []

    if not spine_versions.is_supported_editor_version(skel["skeleton"]["spine"]):
        errors.append(
            "skeleton.spine must target an approved Spine editor line "
            f"{spine_versions.SUPPORTED_SPINE_EDITOR_PREFIXES}: {skel['skeleton']['spine']!r}"
        )
    if not isinstance(skel["skins"], list):
        errors.append("skins must be an array (4.x), not an object (3.8)")
    else:
        seen_skin_names: set[str] = set()
        for idx, skin in enumerate(skel["skins"]):
            if not isinstance(skin, dict) or "name" not in skin or "attachments" not in skin:
                errors.append(f"skin object missing required fields: {skin}")
                continue
            name = skin.get("name")
            if not isinstance(name, str) or not name:
                errors.append(f"skin[{idx}] name must be a non-empty string")
            elif name in seen_skin_names:
                errors.append(f"skin name {name!r} is duplicated")
            else:
                seen_skin_names.add(name)
            if idx == 0 and name != "default":
                errors.append("default skin must be first")
        if "default" not in seen_skin_names:
            errors.append("skins must include a default skin")

    bone_names = {b["name"] for b in skel["bones"]}
    if "root" not in bone_names:
        errors.append("bones list missing required root bone named 'root'")
    for b in skel["bones"]:
        if b.get("parent") and b["parent"] not in bone_names:
            errors.append(f"bone {b['name']} references unknown parent {b['parent']}")

    slot_names = {s["name"] for s in skel["slots"]}
    for s in skel["slots"]:
        if s["bone"] not in bone_names:
            errors.append(f"slot {s['name']} references unknown bone {s['bone']}")
        if "blend" in s:
            errors.append(f"slot {s['name']} emits non-normal blend; H5G contract requires omitting blend")

    # IK targets exist and aren't descendants of constrained bones (basic check)
    for ik in skel.get("ik", []):
        for b in ik.get("bones", []):
            if b not in bone_names:
                errors.append(f"ik constraint {ik['name']!r} references unknown bone {b!r}")
        if ik.get("target") not in bone_names:
            errors.append(f"ik constraint {ik['name']!r} target {ik.get('target')!r} not in bones")

    # Transform constraints reference real bones
    for tc in skel.get("transform", []):
        for b in tc.get("bones", []):
            if b not in bone_names:
                errors.append(f"transform constraint {tc['name']!r} references unknown bone {b!r}")
        if tc.get("target") not in bone_names:
            errors.append(f"transform constraint {tc['name']!r} target {tc.get('target')!r} not in bones")

    # Physics constraints reference one real bone by name.
    for pc in skel.get("physics", []):
        if pc.get("bone") not in bone_names:
            errors.append(f"physics constraint {pc.get('name')!r} references unknown bone {pc.get('bone')!r}")
    errors.extend(physics.validate_emitted_constraints(
        skel.get("physics", []),
        physics.load_policy(),
        bone_names,
    ))

    # Attachment paths exist in atlas across every skin.
    region_names = {r["name"] for r in atlas_records}
    default_skin = skel["skins"][0] if isinstance(skel["skins"], list) and skel["skins"] else {}
    default_attachments = default_skin.get("attachments", {}) if isinstance(default_skin, dict) else {}
    for slot in skel["slots"]:
        setup_attachment = slot.get("attachment")
        if setup_attachment and setup_attachment not in default_attachments.get(slot["name"], {}):
            errors.append(
                f"default skin missing setup attachment {setup_attachment!r} for slot {slot['name']!r}"
            )
    if isinstance(skel.get("skins"), list):
        for skin in skel["skins"]:
            skin_name = skin.get("name", "(unnamed)") if isinstance(skin, dict) else "(invalid)"
            errors.extend(_validate_skin_memberships(skel, skin))
            for slot_name, atts in skin.get("attachments", {}).items():
                if slot_name not in slot_names:
                    errors.append(f"skin {skin_name!r} references unknown slot {slot_name!r}")
                    continue
                if skin_name != "default":
                    for att_name in atts:
                        if att_name not in default_attachments.get(slot_name, {}):
                            errors.append(
                                f"skin {skin_name!r} attachment key {att_name!r} for slot {slot_name!r} has no default fallback"
                            )
                for att_name, att in atts.items():
                    if not isinstance(att, dict):
                        errors.append(f"skin {skin_name!r} attachment {att_name!r} must be an object")
                        continue
                    att_type = att.get("type", "region")
                    if att_type in {"linkedmesh", "linked_mesh"}:
                        errors.append(
                            f"skin {skin_name!r} attachment {att_name!r} uses linkedmesh, which is not implemented"
                        )
                        continue
                    if att_type == "clipping":
                        continue  # clipping attachments have no atlas region
                    path = att.get("path", att_name)
                    sequence = att.get("sequence")
                    if sequence:
                        start = int(sequence.get("start", 1))
                        count = int(sequence["count"])
                        digits = int(sequence.get("digits", 0))
                        for idx in range(start, start + count):
                            frame_path = f"{path}{idx:0{digits}d}" if digits else f"{path}{idx}"
                            if frame_path not in region_names:
                                errors.append(
                                    f"sequence attachment {path!r} (skin {skin_name}, slot {slot_name}) missing atlas frame {frame_path!r}"
                                )
                        continue
                    if path not in region_names:
                        errors.append(
                            f"attachment {path!r} (skin {skin_name}, slot {slot_name}) not in atlas regions"
                        )
                    if att_type == "mesh":
                        errors.extend(_validate_mesh_attachment(slot_name, att_name, att, len(skel["bones"])))

    # Animation timeline name 4.x compliance
    for anim_name, anim in skel.get("animations", {}).items():
        for bone_name, tracks in anim.get("bones", {}).items():
            for tl_name, keys in tracks.items():
                if tl_name not in {"translate", "rotate", "scale", "shear"}:
                    errors.append(
                        f"animation {anim_name!r} bone {bone_name} has unknown timeline {tl_name!r}"
                    )
                if tl_name == "rotate":
                    for k in keys:
                        if "angle" in k:
                            errors.append(
                                f"animation {anim_name!r} bone {bone_name} rotate uses legacy 'angle' (must be 'value')"
                            )
        for slot_name, tracks in anim.get("slots", {}).items():
            for tl_name, keys in tracks.items():
                if tl_name == "sequence":
                    errors.append(
                        f"animation {anim_name} slot {slot_name} uses legacy slot sequence timeline; "
                        "4.3 sequence timelines belong under animations.attachments.<skin>.<slot>.<attachment>.sequence"
                    )
                    continue
                if tl_name == "color":
                    errors.append(
                        f"animation {anim_name!r} slot {slot_name} uses legacy 'color' timeline (must be 'rgba')"
                    )
                if tl_name == "twoColor":
                    errors.append(
                        f"animation {anim_name!r} slot {slot_name} uses legacy 'twoColor' timeline (must be 'rgba2')"
                    )
    errors.extend(bezier_curves.validate_timeline_curves(skel, export_profile))

    return {
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "warnings": warnings,
        "bones_count": len(skel["bones"]),
        "slots_count": len(skel["slots"]),
        "animations_count": len(skel.get("animations", {})),
        "animations": list(skel.get("animations", {}).keys()),
        "atlas_regions": len(atlas_records),
        "spine_version": skel["skeleton"]["spine"],
    }


def _validate_skin_memberships(skel: dict, skin: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(skin, dict):
        return errors
    skin_name = skin.get("name", "(unnamed)")
    bone_names = {b["name"] for b in skel.get("bones", [])}
    for bone_name in skin.get("bones", []):
        if bone_name not in bone_names:
            errors.append(f"skin {skin_name!r} references unknown bone {bone_name!r}")

    constraint_sources = {
        "ik": {item.get("name") for item in skel.get("ik", [])},
        "transform": {item.get("name") for item in skel.get("transform", [])},
        "path": {item.get("name") for item in skel.get("path", [])},
        "physics": {item.get("name") for item in skel.get("physics", [])},
    }
    for constraint_type, known_names in constraint_sources.items():
        value = skin.get(constraint_type, [])
        if value is None:
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            errors.append(f"skin {skin_name!r} {constraint_type} membership must be a list of names")
            continue
        for constraint_name in value:
            if constraint_name not in known_names:
                errors.append(
                    f"skin {skin_name!r} references unknown {constraint_type} constraint {constraint_name!r}"
                )
    return errors


def _validate_mesh_attachment(slot_name: str, att_name: str, att: dict, bone_count: int) -> list[str]:
    errors: list[str] = []
    prefix = f"mesh attachment {att_name!r} (slot {slot_name})"
    uvs = att.get("uvs")
    vertices = att.get("vertices")
    triangles = att.get("triangles")
    hull = att.get("hull")
    edges = att.get("edges", [])

    if not _flat_number_list(uvs):
        errors.append(f"{prefix} uvs must be a flat numeric list")
        uvs = []
    if not _flat_number_list(vertices):
        errors.append(f"{prefix} vertices must be a flat numeric list")
        vertices = []
    if not _flat_int_list(triangles):
        errors.append(f"{prefix} triangles must be a flat integer list")
        triangles = []
    if edges and not _flat_int_list(edges):
        errors.append(f"{prefix} edges must be a flat integer list")
        edges = []
    if not _strict_int(hull):
        errors.append(f"{prefix} hull must be an integer")
        hull = 0

    unweighted = len(vertices) == len(uvs)
    vertex_count = len(uvs) // 2
    if len(uvs) % 2 != 0:
        errors.append(f"{prefix} uvs length must be even")
    if unweighted:
        vertex_count = len(vertices) // 2
        if len(vertices) % 2 != 0:
            errors.append(f"{prefix} vertices length must be even")
    else:
        errors.extend(_validate_weighted_mesh_vertices(prefix, vertices, vertex_count, bone_count))
    for idx, uv in enumerate(uvs):
        if uv < 0 or uv > 1:
            errors.append(f"{prefix} uvs[{idx}] must be in the [0, 1] range")
            break
    if hull > vertex_count:
        errors.append(f"{prefix} hull must not exceed vertex count")
    if len(triangles) % 3 != 0:
        errors.append(f"{prefix} triangles length must be a multiple of 3")
    for idx in triangles:
        if idx < 0 or idx >= vertex_count:
            errors.append(f"{prefix} triangle index {idx} is out of range")
            break
    if unweighted:
        points = [(float(vertices[i]), float(vertices[i + 1])) for i in range(0, len(vertices) - 1, 2)]
        for tri in range(0, len(triangles), 3):
            if tri + 2 >= len(triangles):
                break
            a, b, c = triangles[tri:tri + 3]
            if len({a, b, c}) < 3:
                errors.append(f"{prefix} triangle {tri // 3} must not be degenerate")
                break
            if a < vertex_count and b < vertex_count and c < vertex_count:
                if _mesh_triangle_area2(points[a], points[b], points[c]) == 0:
                    errors.append(f"{prefix} triangle {tri // 3} must not be degenerate")
                    break
    if len(edges) % 2 != 0:
        errors.append(f"{prefix} edges length must be even")
    for idx in edges:
        if idx < 0 or idx >= vertex_count:
            errors.append(f"{prefix} edge index {idx} is out of range")
            break
    return errors


def _validate_weighted_mesh_vertices(prefix: str, vertices: list, vertex_count: int, bone_count: int) -> list[str]:
    errors: list[str] = []
    cursor = 0
    epsilon = 0.001
    for vertex_idx in range(vertex_count):
        if cursor >= len(vertices):
            errors.append(f"{prefix} weighted vertices ended before vertex {vertex_idx}")
            return errors
        influence_count = vertices[cursor]
        cursor += 1
        if not _strict_int(influence_count):
            errors.append(f"{prefix} vertex {vertex_idx} influence count must be an integer")
            return errors
        if influence_count < 1:
            errors.append(f"{prefix} vertex {vertex_idx} must have at least one influence")
        total = 0.0
        for influence_idx in range(influence_count):
            if cursor + 3 >= len(vertices):
                errors.append(f"{prefix} vertex {vertex_idx} influence {influence_idx} is truncated")
                return errors
            bone_idx, bind_x, bind_y, weight = vertices[cursor:cursor + 4]
            cursor += 4
            if not _strict_int(bone_idx) or bone_idx < 0 or bone_idx >= bone_count:
                errors.append(f"{prefix} vertex {vertex_idx} bone index {bone_idx!r} is out of range")
            if not _strict_number(bind_x) or not _strict_number(bind_y):
                errors.append(f"{prefix} vertex {vertex_idx} bind position must be finite")
            if not _strict_number(weight) or not (0.0 <= float(weight) <= 1.0):
                errors.append(f"{prefix} vertex {vertex_idx} weight must be finite and in [0, 1]")
            else:
                total += float(weight)
        if abs(total - 1.0) > epsilon:
            errors.append(f"{prefix} vertex {vertex_idx} weights sum to {total:.6f}")
    if cursor != len(vertices):
        errors.append(f"{prefix} weighted vertices have trailing values")
    return errors


def _strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _strict_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _source_art_write_guard_error(path: Path) -> str | None:
    error = write_guard_error(path, "project context or learning log path")
    if error:
        return f"refusing to write PROJECT_CONTEXT.json or LEARNING_LOG.jsonl: {error}"
    return None


def _package_output_guard_error(path: Path) -> str | None:
    error = write_guard_error(path, "package output path")
    if error:
        if "prohibited source-art root" in error:
            return f"refusing to write package outputs under prohibited source-art root: {path}"
        return f"refusing to write package outputs: {error}"
    return None


def _flat_int_list(value: Any) -> bool:
    return isinstance(value, list) and all(_strict_int(item) for item in value)


def _flat_number_list(value: Any) -> bool:
    return isinstance(value, list) and all(_strict_number(item) for item in value)


def _mesh_triangle_area2(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _apply_sequence_attachments(layout: dict, sequences: dict[str, dict]) -> dict:
    """Collapse numbered VFX frame layers into Sequence attachments.

    The atlas still packs every numbered frame as its own region, but the
    skeleton exposes a single attachment whose path is the runtime frame prefix.
    """
    if not sequences:
        return layout

    frame_to_base: dict[str, str] = {}
    first_frame_for_base: dict[str, str] = {}
    for base, info in sequences.items():
        frames = [Path(name).stem for name in info.get("frames", [])]
        if not frames:
            continue
        first_frame_for_base[base] = frames[0]
        for frame in frames:
            frame_to_base[frame] = base

    if not frame_to_base:
        return layout

    keep_frames = set(first_frame_for_base.values())
    remove_frames = set(frame_to_base) - keep_frames

    new_layout = dict(layout)
    new_layout["bones"] = [
        b for b in layout["bones"]
        if Path(b.get("layer_name", "")).stem not in remove_frames
    ]

    slots = []
    for s in layout["slots"]:
        stem = Path(s.get("attachment", "")).name
        base = frame_to_base.get(stem)
        if stem in remove_frames:
            continue
        out = dict(s)
        if base and stem == first_frame_for_base[base]:
            out["attachment"] = f"parts/{base}"
            out["sequence"] = seqattr.build_sequence_timeline(2.0, mode="once")
        slots.append(out)
    new_layout["slots"] = slots

    attachments = []
    for att in layout["attachments"]:
        stem = Path(att.get("layer_name", "")).stem
        base = frame_to_base.get(stem)
        if stem in remove_frames:
            continue
        out = dict(att)
        if base and stem == first_frame_for_base[base]:
            out["name"] = f"parts/{base}"
            out["path"] = f"parts/{base}_"
            out["sequence"] = seqattr.build_sequence_spec(base, sequences[base])
            out["sequence_frames"] = sequences[base]["frames"]
        attachments.append(out)
    new_layout["attachments"] = attachments
    new_layout["sequences"] = sequences
    return new_layout


def _add_sequence_timelines(animations: dict, layout: dict) -> None:
    """Add 4.3 attachment.sequence timelines to win-like animations."""
    sequence_slots = [s for s in layout.get("slots", []) if s.get("sequence")]
    if not sequence_slots:
        return
    for anim_name, anim in animations.items():
        lower = anim_name.lower()
        if not any(token in lower for token in ("win", "smart", "explode", "celebration", "burst")):
            continue
        attachments = anim.setdefault("attachments", {}).setdefault("default", {})
        for slot in sequence_slots:
            attachment_name = slot.get("attachment")
            if not attachment_name:
                continue
            attachments.setdefault(slot["name"], {}).setdefault(attachment_name, {})["sequence"] = list(slot["sequence"])


EXPRESSION_ROLE_TO_NAME = {
    "eyes_blink": "blink",
    "eyes_closed": "blink",
    "eyes_side": "side_eye",
    "mouth_smile": "smile",
    "mouth_laugh": "laugh",
    "mouth_open": "mouth_open",
    "mouth_closed": "mouth_closed",
}

EXPRESSION_PRIORITY = {
    "neutral": 0,
    "blink": 1,
    "side_eye": 1,
    "smile": 2,
    "mouth_closed": 2,
    "mouth_open": 3,
    "laugh": 4,
}


def _expression_composite_report(enabled: bool = False) -> dict:
    return {
        "schema": "spine_slot_animation_expression_composite_validation_v1",
        "enabled": enabled,
        "review_required": False,
        "issues": [],
        "duplicate_canonical_expression_layers": [],
        "composite_order": {},
    }


def _apply_expression_composites(
    layout: dict,
    interpretation: dict,
    layer_dir: Path,
    out_dir: Path,
) -> tuple[dict, int, list[str], dict]:
    """Pre-bake available expression overlays and splice them into the head slot."""
    report = _expression_composite_report(False)
    head_layer = next(
        (L for L in interpretation["layers"] if L.get("semantic_role") == "head"),
        None,
    )
    if not head_layer:
        return layout, 0, [], report

    head_stem = Path(head_layer["name"]).stem
    head_png = layer_dir / f"{head_stem}.png"
    if not head_png.exists():
        return layout, 0, [], report

    head_slot = next(
        (s for s in layout.get("slots", []) if s.get("semantic_role") == "head"),
        None,
    )
    head_attachment = next(
        (a for a in layout.get("attachments", []) if a.get("slot") == head_slot.get("name")),
        None,
    ) if head_slot else None
    if not head_slot or not head_attachment:
        return layout, 0, [], report

    overlays: dict[str, list[Path]] = {}
    overlay_slot_to_expression: dict[str, str] = {}
    for layer in interpretation["layers"]:
        expression = EXPRESSION_ROLE_TO_NAME.get(layer.get("semantic_role"))
        if not expression:
            continue
        stem = Path(layer["name"]).stem
        overlay_png = layer_dir / f"{stem}.png"
        if not overlay_png.exists():
            continue
        overlays.setdefault(expression, []).append(overlay_png)
        overlay_slot_to_expression[f"{stem}_slot"] = expression

    if not overlays:
        return layout, 0, [], report

    import composite_expression_heads as ceh  # noqa: E402
    from PIL import Image  # noqa: E402

    report = _expression_composite_report(True)
    report["duplicate_canonical_expression_layers"] = [
        {
            "expression": expression,
            "source_overlays": [str(path) for path in paths],
            "strategy": "composite_in_layer_order",
        }
        for expression, paths in sorted(overlays.items())
        if len(paths) > 1
    ]
    report["composite_order"] = {
        expression: [str(path) for path in paths]
        for expression, paths in sorted(overlays.items())
    }

    with Image.open(head_png) as img:
        head_size = img.size
    for expression, paths in sorted(overlays.items()):
        for overlay_png in paths:
            with Image.open(overlay_png) as img:
                overlay_size = img.size
            if overlay_size != head_size:
                report["issues"].append({
                    "code": "expression_overlay_canvas_mismatch",
                    "expression": expression,
                    "overlay": str(overlay_png),
                    "overlay_size": list(overlay_size),
                    "head": str(head_png),
                    "head_size": list(head_size),
                    "message": (
                        "Expression overlays must be full-canvas aligned; "
                        "placement metadata is required before mismatched overlays can be composited."
                    ),
                })
    if report["issues"]:
        report["review_required"] = True
        return layout, 0, [], report

    composited_dir = out_dir / "composited_expressions"
    manifest = ceh.composite_expressions(head_png, overlays, composited_dir, head_stem)

    new_layout = dict(layout)
    slots: list[dict] = []
    attachments = [
        dict(a)
        for a in layout["attachments"]
        if a.get("slot") not in overlay_slot_to_expression
    ]

    neutral_name = manifest["attachments"]["neutral"]["head_slot_attachment_name"]
    for slot in layout["slots"]:
        if slot["name"] in overlay_slot_to_expression:
            continue
        out_slot = dict(slot)
        if out_slot["name"] == head_slot["name"]:
            out_slot["attachment"] = neutral_name
        slots.append(out_slot)

    for expression, info in manifest["attachments"].items():
        image_path = Path(info["file"])
        with Image.open(image_path) as img:
            width, height = img.size
        attachments.append({
            "slot": head_slot["name"],
            "name": info["head_slot_attachment_name"],
            "path": info["head_slot_attachment_name"],
            "type": "region",
            "x": head_attachment.get("x", 0),
            "y": head_attachment.get("y", 0),
            "width": width,
            "height": height,
            "layer_name": image_path.name,
            "image_path": str(image_path),
            "expression": expression,
        })

    new_layout["slots"] = slots
    new_layout["attachments"] = attachments
    new_layout["expression_composites"] = {
        "head_slot": head_slot["name"],
        "neutral_attachment": neutral_name,
        "overlay_slot_to_expression": overlay_slot_to_expression,
        "attachments": manifest["attachments"],
        "validation": report,
    }
    return new_layout, len(manifest["attachments"]), sorted(manifest["attachments"].keys()), report


def _evaluate_expression_composite_visual_qa(layout: dict) -> dict:
    info = layout.get("expression_composites")
    if not info:
        return {
            "schema": "spine_slot_animation_expression_visual_qa_v1",
            "enabled": False,
            "local_eval_executed": False,
            "browser_runtime_executed": False,
            "preview_html_generated": False,
            "preview_required": False,
            "art_approval_claimed": False,
            "checks": [],
        }

    from PIL import Image, ImageChops  # noqa: E402

    attachments = info["attachments"]
    neutral = attachments["neutral"]
    head = Image.open(neutral["file"]).convert("RGBA")
    checks: list[dict] = []
    passed = True
    for expression, attachment in sorted(attachments.items()):
        img = Image.open(attachment["file"]).convert("RGBA")
        alpha = img.getchannel("A")
        bbox = alpha.getbbox()
        check = {
            "expression": expression,
            "file": attachment["file"],
            "dimensions_match_neutral": img.size == head.size,
            "alpha_bounds": list(bbox) if bbox else None,
            "alpha_in_bounds": bbox is not None and bbox[0] >= 0 and bbox[1] >= 0 and bbox[2] <= img.size[0] and bbox[3] <= img.size[1],
            "pixel_integration_changed_head": False,
        }
        if expression != "neutral":
            diff = ImageChops.difference(head.convert("RGB"), img.convert("RGB"))
            check["pixel_integration_changed_head"] = diff.getbbox() is not None
        else:
            check["pixel_integration_changed_head"] = True
        passed = passed and all(
            bool(check[name])
            for name in ("dimensions_match_neutral", "alpha_in_bounds", "pixel_integration_changed_head")
        )
        checks.append(check)

    return {
        "schema": "spine_slot_animation_expression_visual_qa_v1",
        "enabled": True,
        "local_eval_executed": True,
        "browser_runtime_executed": False,
        "preview_html_generated": False,
        "preview_required": True,
        "art_approval_claimed": False,
        "passed": passed,
        "checks": checks,
        "note": "Deterministic composite PNG checks only; runtime atlas pixels, Spine Player preview, and art review remain required for facial acting approval.",
    }


def _build_mesh_weight_test_animation(mesh_report: dict) -> dict:
    weight_binding = mesh_report.get("weight_binding", {})
    bone_names = sorted({
        bone_name
        for summary in weight_binding.get("attachment_summaries", [])
        for bone_name in summary.get("bound_bones", [])
        if bone_name != "root"
    })
    return {
        "bones": {
            bone_name: {
                "translate": [
                    {"time": 0.0, "x": 0, "y": 0},
                    {"time": 0.25, "x": 0, "y": 4},
                    {"time": 0.5, "x": 0, "y": -4},
                    {"time": 0.75, "x": 0, "y": 0},
                ]
            }
            for bone_name in bone_names
        }
    }


def _mesh_deformation_qa_report(mesh_report: dict, animations: dict) -> dict:
    weight_binding = mesh_report.get("weight_binding", {})
    weighted_count = int(weight_binding.get("weighted_mesh_attachments_emitted", 0) or 0)
    summaries = weight_binding.get("attachment_summaries", [])
    no_deform_timelines = not any("deform" in animation for animation in animations.values())
    checks = [
        {"name": "weighted_meshes_present", "passed": weighted_count > 0},
        {"name": "test_animation_emitted", "passed": "__mesh_weight_test" in animations},
        {"name": "no_deform_timelines_emitted", "passed": no_deform_timelines},
        {
            "name": "estimated_vertex_transforms_within_policy",
            "passed": weight_binding.get("estimated_vertex_transforms", 0) <= (weight_binding.get("policy") or {}).get("max_estimated_vertex_transforms", 0),
        },
    ]
    return {
        "schema": "spine_slot_animation_mesh_deformation_qa_v1",
        "enabled": weighted_count > 0,
        "local_eval_executed": weighted_count > 0,
        "browser_runtime_executed": False,
        "preview_required": weighted_count > 0,
        "art_approval_claimed": False,
        "review_required": weighted_count > 0,
        "test_animation": "__mesh_weight_test" if weighted_count > 0 else None,
        "weighted_mesh_count": weighted_count,
        "attachment_summaries": summaries,
        "checks": checks,
        "passed": all(check["passed"] for check in checks) if weighted_count > 0 else True,
        "note": "Deterministic structural QA only; open preview.html or the Spine project and review first-pass weights before approval.",
    }


def _splice_expression_attachment_timelines(animations: dict, layout: dict) -> dict:
    """Move expression overlay attachment swaps onto the composited head slot."""
    report = {
        "schema": "spine_slot_animation_expression_timeline_merge_v1",
        "enabled": False,
        "review_required": False,
        "issues": [],
        "merges": [],
        "strategy": "priority_by_expression",
    }
    info = layout.get("expression_composites")
    if not info:
        return report
    report["enabled"] = True

    head_slot = info["head_slot"]
    neutral_attachment = info["neutral_attachment"]
    expression_attachments = {
        expression: attachment["head_slot_attachment_name"]
        for expression, attachment in info["attachments"].items()
    }
    overlay_slot_to_expression = info["overlay_slot_to_expression"]

    for anim_name, anim in animations.items():
        slots = anim.setdefault("slots", {})
        existing_head_timeline = slots.get(head_slot, {}).get("attachment")
        if existing_head_timeline:
            report["review_required"] = True
            report["issues"].append({
                "code": "existing_head_attachment_timeline",
                "animation": anim_name,
                "head_slot": head_slot,
                "message": "Expression splicing did not overwrite an existing head-slot attachment timeline.",
            })
            continue
        events: dict[float, list[tuple[str, str, bool]]] = {}
        saw_active_event = False
        for overlay_slot, expression in overlay_slot_to_expression.items():
            tracks = slots.get(overlay_slot)
            if not tracks:
                continue
            timeline = tracks.pop("attachment", None)
            slots.pop(overlay_slot, None)
            if not timeline:
                continue
            expression_attachment = expression_attachments.get(expression)
            if not expression_attachment:
                continue
            for key in timeline:
                time = float(key.get("time", 0))
                is_active = bool(key.get("name"))
                saw_active_event = saw_active_event or is_active
                events.setdefault(time, []).append((overlay_slot, expression, is_active))

        if saw_active_event:
            active_expressions: dict[str, str] = {}
            head_timeline: list[dict] = []
            current_attachment: str | None = None
            for time in sorted(events):
                for overlay_slot, expression, is_active in events[time]:
                    if is_active:
                        active_expressions[overlay_slot] = expression
                    else:
                        active_expressions.pop(overlay_slot, None)

                if active_expressions:
                    active_expression_names = sorted(set(active_expressions.values()))
                    expression = max(
                        active_expression_names,
                        key=lambda name: EXPRESSION_PRIORITY.get(name, 1),
                    )
                    if len(active_expression_names) > 1:
                        report["review_required"] = True
                        report["merges"].append({
                            "animation": anim_name,
                            "time": time,
                            "active_expressions": active_expression_names,
                            "selected_expression": expression,
                            "strategy": "priority_by_expression",
                            "priority": {
                                name: EXPRESSION_PRIORITY.get(name, 1)
                                for name in active_expression_names
                            },
                        })
                    attachment = expression_attachments[expression]
                else:
                    attachment = neutral_attachment

                if attachment != current_attachment:
                    head_timeline.append({"time": time, "name": attachment})
                    current_attachment = attachment

            if head_timeline and head_timeline[0]["time"] != 0.0:
                head_timeline.insert(0, {"time": 0.0, "name": neutral_attachment})
            slots.setdefault(head_slot, {})["attachment"] = [
                {"time": key["time"], "name": key["name"]}
                for key in head_timeline
            ]
    return report


def _validate_avatar_event_plan(events_plan: dict, avatar_manifest: dict) -> None:
    manifest_names = set(avatar_manifest.get("event_names", []))
    expected = avatar_expected_events(avatar_manifest)
    plan_event_names = set((events_plan.get("events") or {}).keys())
    timeline_event_names = {
        key.get("name")
        for keys in (events_plan.get("animations") or {}).values()
        for key in keys
        if isinstance(key, dict)
    }
    avatar_names = {
        name
        for name in plan_event_names | timeline_event_names
        if isinstance(name, str) and name.startswith("avatar/")
    }
    if not avatar_names:
        return

    unknown = sorted(avatar_names - manifest_names)
    if unknown:
        raise ValueError(f"avatar event plan references events not declared by avatar_state_manifest.json: {unknown}")

    for anim_name, keys in (events_plan.get("animations") or {}).items():
        for key in keys:
            name = key.get("name")
            if not isinstance(name, str) or not name.startswith("avatar/"):
                continue
            event_key = (anim_name, name)
            if event_key not in expected:
                raise ValueError(
                    f"avatar event {name!r} is not declared for animation {anim_name!r} in avatar_state_manifest.json"
                )
            plan_time = float(key.get("time", 0))
            expected_time = expected[event_key]
            if abs(plan_time - expected_time) > 0.000001:
                raise ValueError(
                    f"avatar event {name!r} in {anim_name!r} has time {plan_time}, expected {expected_time}"
                )


def _validate_event_plan_shape(events_plan: Any) -> None:
    if not isinstance(events_plan, dict):
        raise ValueError("events plan must be a JSON object")
    events = events_plan.get("events", {})
    if not isinstance(events, dict):
        raise ValueError("events plan 'events' must be an object")
    for event_name, defaults in events.items():
        if not isinstance(event_name, str):
            raise ValueError("events plan event names must be strings")
        if not isinstance(defaults, dict):
            raise ValueError(f"events plan event {event_name!r} defaults must be an object")
    animations = events_plan.get("animations", {})
    if not isinstance(animations, dict):
        raise ValueError("events plan 'animations' must be an object")
    for anim_name, keys in animations.items():
        if not isinstance(anim_name, str):
            raise ValueError("events plan animation names must be strings")
        if not isinstance(keys, list):
            raise ValueError(f"events plan animation {anim_name!r} must be a list of event keys")
        for idx, key in enumerate(keys):
            if not isinstance(key, dict):
                raise ValueError(f"events plan animation {anim_name!r} key {idx} must be an object")
            if "time" not in key:
                raise ValueError(f"events plan animation {anim_name!r} key {idx} missing required time")
            if not _strict_number(key["time"]):
                raise ValueError(f"events plan animation {anim_name!r} key {idx} time must be a finite number")
            if not isinstance(key.get("name"), str) or not key["name"]:
                raise ValueError(f"events plan animation {anim_name!r} key {idx} name must be a non-empty string")


def _write_ui_system_failure_report(
    out_dir: Path,
    family: str,
    rank: int,
    ui_system_report: dict,
) -> None:
    reason = ui_system_report["ui_system_unsupported_reason"]
    report = {
        "status": "failed",
        "errors": [reason],
        "warnings": [],
        "family": family,
        "rank": rank,
        **ui_system_report,
    }
    (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))


def main() -> int:
    p = argparse.ArgumentParser(description="End-to-end Spine package builder.")
    p.add_argument("--layer-dir", required=True)
    p.add_argument("--manifest", help="Optional h5g_layer_manifest.json with bounds.")
    p.add_argument("--family", required=True)
    p.add_argument("--rank", type=int, default=1)
    p.add_argument("--controls", help="Optional bounded controls JSON path.")
    p.add_argument("--doc-width", type=float)
    p.add_argument("--doc-height", type=float)
    p.add_argument("--out-dir", required=True)
    # Advanced (review-gated) features
    p.add_argument("--enable-ik", action="store_true",
                   help="Emit two-bone IK for arm+hand pairs and key the mix on win animations.")
    p.add_argument("--enable-transform-constraints", action="store_true",
                   help="Auto-emit shadow-follows-body transform constraints.")
    p.add_argument("--transform-constraints-plan",
                   help="Path to JSON with user-supplied transform constraint definitions.")
    p.add_argument("--enable-clipping",
                   help="Path to a clipping plan JSON (see references/clipping.md).")
    p.add_argument("--enable-events",
                   help="Path to an events plan JSON (see references/events.md).")
    # Vision bridges (gated)
    p.add_argument("--composite-expressions", action="store_true",
                   help="Pre-bake head_default/head_blink/head_laugh attachments to eliminate the WebGL overlay-alpha-matte seam.")
    p.add_argument("--render-qa-frames", action="store_true",
                   help="Render setup-pose snapshot to <out-dir>/qa/setup.png for vision-driven QA.")
    # Project context (learned defaults across builds)
    p.add_argument("--no-context", action="store_true",
                   help="Ignore any nearby PROJECT_CONTEXT.json; use only CLI-supplied values.")
    p.add_argument("--project-context-path", help="Explicit path to PROJECT_CONTEXT.json (overrides search).")
    p.add_argument("--bootstrap-context", action="store_true",
                   help="If no PROJECT_CONTEXT.json is found, create a default one next to the layer dir.")
    # Spine 4.x advanced (iteration 6)
    p.add_argument("--enable-physics", action="store_true",
                   help="Auto-detect physics-candidate bones (capes/hair/dangles/etc.) and emit physics constraints.")
    p.add_argument("--physics-plan", help="Optional JSON file with custom physics-constraint overrides.")
    p.add_argument("--enable-sequences", action="store_true",
                   help="Collapse numbered VFX frames (foo_001..foo_NNN) into Sequence attachments.")
    p.add_argument("--mesh-plan",
                   help="Path to a reviewed Phase 2 unweighted mesh plan JSON.")
    p.add_argument("--report-mesh-candidates", action="store_true",
                   help="Write deterministic mesh_candidate_report.json without changing package output.")
    p.add_argument("--auto-mesh-plan", action="store_true",
                   help="Generate and apply an automatic draft mesh plan for conservative candidates; review required.")
    p.add_argument("--auto-bind-weights", action="store_true",
                   help="Opt-in first-pass weights for --mesh-plan or --auto-mesh-plan mesh attachments.")
    p.add_argument("--skin-plan",
                   help="Path to a reviewed Phase 6 multi-skin region variant plan JSON.")
    p.add_argument("--build-preview", action="store_true",
                   help=f"Generate preview.html with the @esotericsoftware/spine-player@{preview_html.SPINE_PLAYER_VERSION} embedded for offline review.")
    p.add_argument("--spine-editor-zip", action="store_true",
                   help="Write spine_editor_handoff.zip containing json/atlas/png, README, and audit manifest.")
    p.add_argument("--create-spine-project", action="store_true",
                   help="Use an installed Spine CLI to create a native .spine project via official import.")
    p.add_argument("--spine-cli", help="Path to Spine.com/Spine executable for --create-spine-project.")
    p.add_argument("--spine-version",
                   help="Optional CLI import version override. Must match shared_symbols.json skeleton.spine.")
    p.add_argument("--target-spine-version", default=SPINE_VERSION,
                   help="Skeleton JSON Spine editor version to emit. Defaults to the shared H5G target.")
    p.add_argument("--spine-project-output", help="Output .spine path for --create-spine-project.")
    p.add_argument("--production-export-profile",
                   help="Phase 10 production export gate profile. Checks approvals only; never invokes Spine CLI.")
    p.add_argument("--check-production-export-gate", action="store_true",
                   help="Write production_export_gate_report.json and fail if export approvals/evidence are incomplete.")
    p.add_argument("--run-runtime-acceptance-probe", action="store_true",
                   help="When checking the production export gate, run the browser runtime probe before trusting runtime evidence.")
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    output_guard_error = _package_output_guard_error(out_dir)
    if output_guard_error:
        report = {
            "status": "failed",
            "errors": [output_guard_error],
            "warnings": [],
            "family": args.family,
            "rank": args.rank,
            "out_dir": str(out_dir),
        }
        print(json.dumps(report, indent=2), file=sys.stderr)
        print(f"    ERROR: {output_guard_error}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    layer_dir = Path(args.layer_dir)
    if args.auto_bind_weights and not (args.mesh_plan or args.auto_mesh_plan):
        report = {
            "status": "failed",
            "errors": ["--auto-bind-weights requires --mesh-plan or --auto-mesh-plan"],
            "warnings": [],
            "family": args.family,
            "rank": args.rank,
            "mesh_attachments_emitted": 0,
            "weighted_mesh_attachments_emitted": 0,
        }
        (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
        print("    ERROR: --auto-bind-weights requires --mesh-plan or --auto-mesh-plan", file=sys.stderr)
        return 2

    # 0. Project context — load learned defaults if available, then apply to args.
    project_ctx: dict | None = None
    ctx_path: Path | None = None
    context_applied: dict = {}
    if not args.no_context:
        if args.project_context_path:
            ctx_path = Path(args.project_context_path)
        else:
            ctx_path = pc.find_context(layer_dir)
        if ctx_path is None and args.bootstrap_context:
            bootstrap_dir = layer_dir.parent
            guard_error = _source_art_write_guard_error(bootstrap_dir)
            if guard_error:
                report = {
                    "status": "failed",
                    "errors": [guard_error],
                    "warnings": [],
                    "family": args.family,
                    "rank": args.rank,
                }
                (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
                print(f"    ERROR: {guard_error}", file=sys.stderr)
                return 2
            ctx_path = pc.bootstrap_context(bootstrap_dir)
        if ctx_path and ctx_path.exists():
            project_ctx = pc.load_context(ctx_path)
            context_applied = pc.apply_to_args(project_ctx, args)
            if context_applied:
                print(f"  applied context defaults from {ctx_path}: {context_applied}")

    # 1. Layer interpretation
    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text())
        doc = manifest.get("document", {})
        doc_w = float(doc.get("width", args.doc_width or 256))
        doc_h = float(doc.get("height", args.doc_height or 256))
        layer_names = [Path(L.get("file", L.get("name", ""))).stem for L in manifest.get("layers", [])]
        manifest_layers = manifest.get("layers", [])
    else:
        layer_names = [p.name for p in sorted(layer_dir.iterdir())
                       if p.is_file() and p.suffix.lower() == ".png"]
        doc_w = float(args.doc_width or 256)
        doc_h = float(args.doc_height or 256)
        manifest_layers = None

    interps = interpret_layers(layer_names, manifest_layers)
    interpretation = {
        "schema": "spine_slot_animation_layer_interpretation_v1",
        "input_count": len(layer_names),
        "layers": [asdict(i) for i in interps],
    }
    (out_dir / "layer_interpretation.json").write_text(json.dumps(interpretation, indent=2))

    # 2. Rig layout
    layout = build_rig_layout(interpretation, doc_w, doc_h)
    sequence_specs: dict[str, dict] = {}
    if args.enable_sequences:
        sequence_specs = seqattr.detect_sequences(layer_dir)
        layout = _apply_sequence_attachments(layout, sequence_specs)
    (out_dir / "rig_layout.json").write_text(json.dumps(layout, indent=2))
    if sequence_specs:
        (out_dir / "sequences.json").write_text(json.dumps(sequence_specs, indent=2))

    compiler_supported = args.family in FAMILY_TIERS or args.family == "avatar"
    ui_system_report = ui_policy.build_ui_system_report(
        args.family,
        layout,
        compiler_supported=compiler_supported,
    )
    if ui_system_report["ui_system_review_required"]:
        _write_ui_system_failure_report(out_dir, args.family, args.rank, ui_system_report)
        print(f"    ERROR: {ui_system_report['ui_system_unsupported_reason']}", file=sys.stderr)
        return 2

    # 2b. Topology detection — informs animation overlays for non-humanoid creatures
    topology_result = topology_mod.detect_topology(interpretation)
    print(f"  topology: {topology_result['topology']}"
          + (f" + {','.join(topology_result['modifiers'])}" if topology_result.get('modifiers') else "")
          + f"  (legs={topology_result['limb_counts']['legs']}, "
          + f"tentacles={topology_result['limb_counts']['tentacles']}, "
          + f"wings={topology_result['limb_counts']['wings']}, "
          + f"segments={topology_result['limb_counts']['body_segments']})")
    (out_dir / "topology.json").write_text(json.dumps(topology_result, indent=2))

    # 3. Animations — start from project-context family defaults, then overlay --controls
    ctrls: dict = {}
    if project_ctx:
        ctrls = pc.family_default_controls(project_ctx, args.family)
        if ctrls:
            print(f"  applied family defaults from context: {ctrls}")
    if args.controls:
        user_ctrls = json.loads(Path(args.controls).read_text())
        ctrls.update(user_ctrls)
    bounded = _validate_controls(ctrls)
    export_profile = ctrls.get("export_profile")
    bezier_preset = ctrls.get("bezier_preset", "ease_in_out")
    if export_profile == "v10_linear":
        error = (
            "export_profile 'v10_linear' is only supported by the legacy proof compiler; "
            "build_spine_package.py emits supported 4.x packages. Omit export_profile "
            "for default output, or use 'spine_43_bezier' to opt into validated Bezier curves."
        )
        report = {
            "status": "failed",
            "errors": [error],
            "warnings": [],
            "family": args.family,
            "rank": args.rank,
            "controls_applied": bounded,
            "export_profile": export_profile,
            "bezier_profile": {
                "enabled": False,
                "profile": export_profile,
                "preset": None,
                "curves_emitted": 0,
                "supported_timelines": [],
            },
        }
        (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
        print(f"    ERROR: {error}", file=sys.stderr)
        return 2
    if args.family == "avatar":
        animations = compose_avatar_animations(layout, bounded)
    else:
        animations = compose_animations_for_family(layout, args.family, args.rank, bounded)
    _add_sequence_timelines(animations, layout)

    # 3b. Apply topology-aware motion overlays (quadruped gait, wing flap,
    # serpentine undulation, many-legged wave). For humanoid + prop the
    # default composer already does the right thing; this is a no-op.
    topology_motion.apply_topology_motion(animations, layout, topology_result, bounded)

    expression_composite_count = 0
    expression_composite_names: list[str] = []
    expression_composite_validation = _expression_composite_report(False)
    expression_timeline_merge = _splice_expression_attachment_timelines({}, {})
    expression_visual_qa = _evaluate_expression_composite_visual_qa({})
    if args.composite_expressions:
        layout, expression_composite_count, expression_composite_names, expression_composite_validation = _apply_expression_composites(
            layout,
            interpretation,
            layer_dir,
            out_dir,
        )
        expression_visual_qa = _evaluate_expression_composite_visual_qa(layout)
        expression_timeline_merge = _splice_expression_attachment_timelines(animations, layout)
        (out_dir / "rig_layout.json").write_text(json.dumps(layout, indent=2))
        if expression_composite_count:
            print(f"  composited expressions: {expression_composite_names}")

    mesh_report = {
        "enabled": bool(args.mesh_plan or args.auto_mesh_plan),
        "schema": None,
        "planned_count": 0,
        "emitted_count": 0,
        "issue_count": 0,
        "issues": [],
        "weight_binding": {"enabled": False},
    }
    mesh_candidate_report = meshplan.build_mesh_candidate_report(
        layout,
        layer_dir,
        bounded,
        enabled=bool(args.report_mesh_candidates or args.auto_mesh_plan),
    )
    auto_mesh_plan_report = {
        "schema": "spine_slot_animation_auto_mesh_plan_report_v1",
        "enabled": bool(args.auto_mesh_plan),
        "status": "not_requested",
        "planned_count": 0,
        "issues": [],
        "review_required": False,
    }
    if args.report_mesh_candidates or args.auto_mesh_plan:
        (out_dir / "mesh_candidate_report.json").write_text(json.dumps(mesh_candidate_report, indent=2))
    mesh_plan_data: dict | None = None
    if args.mesh_plan:
        mesh_plan_data = meshplan.load_mesh_plan(Path(args.mesh_plan))
        if args.auto_mesh_plan:
            auto_mesh_plan_report.update({
                "status": "skipped_reviewed_plan_override",
                "review_required": True,
                "note": "Reviewed --mesh-plan was supplied; automatic draft plan was not applied.",
            })
    elif args.auto_mesh_plan:
        mesh_plan_data, auto_mesh_plan_report = meshplan.generate_auto_mesh_plan(
            layout,
            layer_dir,
            mesh_candidate_report,
        )
        (out_dir / "auto_mesh_plan.json").write_text(json.dumps(mesh_plan_data, indent=2))
    if mesh_plan_data is not None:
        layout, mesh_report = meshplan.validate_and_apply_mesh_plan(
            layout,
            mesh_plan_data,
            layer_dir,
        )
        if args.auto_bind_weights and not mesh_report["issues"]:
            weight_policy = meshplan.load_weight_binding_policy(
                Path(__file__).resolve().parents[1] / "assets" / "weight_binding_policy.json"
            )
            layout, mesh_report = meshplan.apply_auto_bind_weights(
                layout,
                mesh_plan_data,
                weight_policy,
                mesh_report,
            )
        (out_dir / "rig_layout.json").write_text(json.dumps(layout, indent=2))
        if mesh_report["issues"]:
            report = {
                "status": "failed",
                "errors": mesh_report["issues"],
                "warnings": [],
                "family": args.family,
                "rank": args.rank,
                "mesh_attachments_emitted": 0,
                "weighted_mesh_attachments_emitted": 0,
                "weighted_influence_count": 0,
                "estimated_vertex_transforms": 0,
                "mesh_plan": mesh_report,
                "mesh_candidate_report": mesh_candidate_report,
                "auto_mesh_plan": auto_mesh_plan_report,
            }
            (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
            for issue in mesh_report["issues"]:
                print(f"    ERROR: {issue}", file=sys.stderr)
            return 2
        if mesh_report["emitted_count"]:
            print(f"  mesh attachments: {mesh_report['emitted_count']}")
        if mesh_report.get("weight_binding", {}).get("weighted_mesh_attachments_emitted"):
            animations["__mesh_weight_test"] = _build_mesh_weight_test_animation(mesh_report)
    mesh_deformation_qa = _mesh_deformation_qa_report(mesh_report, animations)
    if mesh_deformation_qa["enabled"]:
        (out_dir / "mesh_deformation_qa.json").write_text(json.dumps(mesh_deformation_qa, indent=2))

    skin_plan_data: dict | None = None
    skin_report = {
        "enabled": bool(args.skin_plan),
        "schema": None,
        "planned_count": 0,
        "emitted_count": 0,
        "skin_names": [],
        "issue_count": 0,
        "issues": [],
        "linkedmesh_supported": False,
        "review_required": bool(args.skin_plan),
    }
    if args.skin_plan:
        skin_plan_input = skinplan.load_skin_plan(Path(args.skin_plan))
        skin_plan_data, skin_report = skinplan.validate_and_build_skin_plan(
            layout,
            skin_plan_input,
            layer_dir,
        )
        if skin_report["issues"]:
            report = {
                "status": "failed",
                "errors": skin_report["issues"],
                "warnings": [],
                "family": args.family,
                "rank": args.rank,
                "skin_variants_emitted": 0,
                "skin_plan": skin_report,
            }
            (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
            for issue in skin_report["issues"]:
                print(f"    ERROR: {issue}", file=sys.stderr)
            return 2
        print(f"  skin variants: {skin_report['skin_names']}")

    # 4. Atlas
    from PIL import Image  # noqa: E402
    regions = []
    for att in layout["attachments"]:
        frame_names = att.get("sequence_frames") or [att["layer_name"]]
        for frame_name in frame_names:
            frame_stem = Path(frame_name).stem
            candidates = []
            if att.get("image_path"):
                candidates.append(Path(att["image_path"]))
            candidates.extend([layer_dir / f"{frame_stem}.png", layer_dir / frame_name])
            png_path = next((c for c in candidates if c.exists()), None)
            if png_path is None:
                print(f"warning: PNG missing for {frame_name}; skipped", file=sys.stderr)
                continue
            img = Image.open(png_path).convert("RGBA")
            trimmed, _ = build_atlas.alpha_trim(img)
            bled = build_atlas.rgb_bleed(trimmed, iterations=4)
            region_name = f"parts/{frame_stem}" if att.get("sequence") else att["name"]
            regions.append((region_name, bled, (0, 0)))
    for att in skinplan.skin_atlas_attachments(skin_plan_data):
        png_path = Path(att["source_path"])
        img = Image.open(png_path).convert("RGBA")
        trimmed, _ = build_atlas.alpha_trim(img)
        bled = build_atlas.rgb_bleed(trimmed, iterations=4)
        regions.append((att["path"], bled, (0, 0)))
    atlas_img, records, atlas_size = build_atlas.pack_atlas(regions, page_name=PAGE_NAME)
    atlas_img.save(out_dir / PAGE_NAME, "PNG")
    build_atlas.write_atlas_file(records, atlas_size, PAGE_NAME, out_dir / ATLAS_NAME)
    mesh_report = meshplan.validate_atlas_paths(layout, records, mesh_report)

    # 5. Advanced features (gated)
    ik_constraints: list[dict] = []
    extra_ik_bones: list[dict] = []
    transform_constraints: list[dict] = []
    clip_slots: list[dict] = []
    clip_attachments: list[dict] = []
    event_defs: dict | None = None

    if args.enable_ik:
        ik_constraints, extra_ik_bones = adv.build_ik_constraints(layout)
        ik_anim_tls = adv.build_ik_animation_timelines(ik_constraints, list(animations.keys()))
        for anim_name, extra in ik_anim_tls.items():
            animations[anim_name].setdefault("ik", {}).update(extra.get("ik", {}))

    if args.enable_transform_constraints or args.transform_constraints_plan:
        user_plan = []
        if args.transform_constraints_plan:
            user_plan = json.loads(Path(args.transform_constraints_plan).read_text())
        transform_constraints = adv.build_transform_constraints(layout, user_plan)

    physics_constraints_list: list[dict] = []
    physics_plan_supplied = bool(args.physics_plan)
    physics_plan = json.loads(Path(args.physics_plan).read_text()) if physics_plan_supplied else None
    physics_policy = physics.load_policy()
    physics_report = physics.build_physics_constraints_with_report(
        layout,
        physics_plan,
        physics_policy,
        emit_enabled=args.enable_physics,
        plan_supplied=physics_plan_supplied,
    )
    physics_constraints_list = physics_report["constraints"]
    avatar_manifest: dict | None = None
    avatar_manifest_issues: list[str] = []
    avatar_event_timelines_emitted = False
    event_plan_errors: list[str] = []
    if args.family == "avatar":
        ik_candidates = adv.detect_ik_candidates(layout)
        avatar_manifest, avatar_manifest_issues = build_avatar_state_manifest(
            layout,
            animations,
            expression_support={
                "enabled": bool(expression_composite_count),
                "expressions": expression_composite_names,
                "preview_required": bool(expression_visual_qa.get("preview_required")),
            },
            physics_candidates=physics_report["candidates"],
            physics_constraints_emitted=len(physics_constraints_list),
            physics_preview_required=bool(physics_report["candidates"] or physics_constraints_list),
            physics_enabled=bool(args.enable_physics),
            ik_candidates_count=len(ik_candidates),
            ik_constraints_emitted=len(ik_constraints),
            ik_enabled=bool(args.enable_ik),
            event_timelines_emitted=False,
        )

    if args.enable_clipping:
        clip_plan = json.loads(Path(args.enable_clipping).read_text())
        clip_slots, clip_attachments = adv.build_clipping_attachments(layout, clip_plan)

    if args.enable_events:
        events_plan = json.loads(Path(args.enable_events).read_text())
        anim_durations = {}
        for name, anim in animations.items():
            max_t = 0.0
            for tracks in (anim.get("bones", {}).values(), anim.get("slots", {}).values()):
                if isinstance(tracks, dict):
                    for keys in tracks.values():
                        if isinstance(keys, list):
                            for k in keys:
                                t = k.get("time", 0)
                                if isinstance(t, (int, float)) and t > max_t:
                                    max_t = float(t)
            anim_durations[name] = max(max_t, 5.0)
        try:
            _validate_event_plan_shape(events_plan)
            if avatar_manifest:
                _validate_avatar_event_plan(events_plan, avatar_manifest)
                avatar_event_timelines_emitted = any(
                    isinstance(key.get("name"), str) and key["name"].startswith("avatar/")
                    for keys in (events_plan.get("animations") or {}).values()
                    for key in keys
                    if isinstance(key, dict)
                )
            adv.validate_event_plan(events_plan, animations, anim_durations)
        except ValueError as exc:
            event_plan_errors.append(str(exc))
        if not event_plan_errors:
            event_defs = adv.build_event_definitions(events_plan)
            adv.splice_event_timelines(animations, events_plan)
            if avatar_manifest:
                avatar_manifest["event_timelines_emitted"] = avatar_event_timelines_emitted

    if avatar_manifest:
        (out_dir / AVATAR_MANIFEST_NAME).write_text(json.dumps(avatar_manifest, indent=2))

    bezier_report = {
        "enabled": False,
        "profile": export_profile,
        "preset": None,
        "curves_emitted": 0,
        "supported_timelines": [],
    }
    if export_profile in {bezier_curves.PROFILE_NAME, bezier_curves.LEGACY_PROFILE_NAME}:
        bezier_report = {
            "enabled": True,
            **bezier_curves.apply_bezier_profile(animations, bezier_preset),
        }

    # 6. Assemble shared_symbols.json
    skel = assemble_skeleton_json(
        layout, animations, doc_w, doc_h,
        ik_constraints=ik_constraints,
        extra_ik_bones=extra_ik_bones,
        transform_constraints=transform_constraints,
        clip_slots=clip_slots,
        clip_attachments=clip_attachments,
        event_defs=event_defs,
        physics_constraints_list=physics_constraints_list,
        skin_plan_data=skin_plan_data,
        spine_version=args.target_spine_version,
    )
    (out_dir / JSON_NAME).write_text(json.dumps(skel, indent=2))
    loop_report = loop_validation.validate_animation_loops(skel, args.family)

    # 7. Validate
    report = validate_skeleton(skel, records, export_profile=export_profile)
    report["family"] = args.family
    report["rank"] = args.rank
    report.update(ui_system_report)
    report["controls_applied"] = bounded
    report["export_profile"] = export_profile or "spine_43_linear"
    report["bezier_profile"] = bezier_report
    report["animation_loop_validation"] = loop_report
    report["animation_loop_intents"] = {
        name: item["intent"]
        for name, item in loop_report["animations"].items()
    }
    report["loop_validation_status"] = loop_report["status"]
    report["ik_constraints_emitted"] = len(ik_constraints)
    report["transform_constraints_emitted"] = len(transform_constraints)
    report["clipping_attachments_emitted"] = len(clip_attachments)
    report["events_defined"] = len(event_defs or {})
    report["event_plan_errors"] = event_plan_errors
    report["avatar_manifest_emitted"] = avatar_manifest is not None
    report["avatar_runtime_required"] = bool(avatar_manifest.get("runtime_required")) if avatar_manifest else False
    report["avatar_runtime_consumer_verified"] = False
    report["avatar_events_declared"] = avatar_manifest.get("event_names", []) if avatar_manifest else []
    report["avatar_persistent_state_claimed"] = bool(
        avatar_manifest.get("persistent_state_claimed_in_spine")
    ) if avatar_manifest else False
    report["avatar_state_count"] = len(avatar_manifest.get("states", [])) if avatar_manifest else 0
    report["avatar_transition_count"] = len(avatar_manifest.get("transitions", [])) if avatar_manifest else 0
    report["avatar_event_timelines_emitted"] = avatar_event_timelines_emitted
    report["avatar_expression_support"] = avatar_manifest.get("expression_support") if avatar_manifest else {
        "status": "not_requested",
        "composite_expressions_enabled": False,
        "composited_expressions": [],
        "preview_required": False,
        "art_approval_required": False,
        "art_approval_claimed": False,
    }
    report["avatar_physics_support"] = avatar_manifest.get("physics_support") if avatar_manifest else {
        "status": "not_requested",
        "enabled": False,
        "candidate_count": 0,
        "constraints_emitted": 0,
        "preview_required": False,
        "art_approval_required": False,
        "art_approval_claimed": False,
    }
    report["avatar_ik_support"] = avatar_manifest.get("ik_support") if avatar_manifest else {
        "status": "not_requested",
        "enabled": False,
        "candidate_count": 0,
        "constraints_emitted": 0,
        "art_approval_required": False,
        "production_approval_claimed": False,
    }
    report["physics_constraints_emitted"] = len(physics_constraints_list)
    report["physics_candidates"] = physics_report["candidates"]
    report["physics_review_required"] = physics_report["review_required"]
    report["zero_length_bone_warnings"] = physics_report["zero_length_bone_warnings"]
    report["physics_max_constraint_violations"] = physics_report["max_constraint_violations"]
    report["physics_active_sliders"] = physics_report["active_sliders"]
    report["physics_policy_snapshot"] = physics_report["policy"]
    physics_has_preview_subject = bool(physics_report["candidates"] or physics_constraints_list)
    report["physics_preview_required"] = bool(
        physics_has_preview_subject and physics_report["policy"].get("preview_required")
    )
    report["physics_preview_html_generated"] = False
    report["physics_runtime_requirements"] = {
        "runtime": "spine-player",
        "version": preview_html.SPINE_PLAYER_VERSION,
        "required_when_physics_present": f"Open preview.html in Spine Web Player {preview_html.SPINE_PLAYER_VERSION} and visually approve simulated secondary motion.",
        "preview_required": report["physics_preview_required"],
        "local_runtime_executed": False,
        "art_approval_claimed": False,
    }
    report["sequence_attachments_emitted"] = len(sequence_specs)
    report["expression_composite_attachments_emitted"] = expression_composite_count
    report["expression_composite_expressions"] = expression_composite_names
    report["expression_composite_validation"] = expression_composite_validation
    report["expression_timeline_merge"] = expression_timeline_merge
    report["expression_composite_visual_qa"] = expression_visual_qa
    report["mesh_attachments_emitted"] = mesh_report["emitted_count"]
    weight_binding = mesh_report.get("weight_binding", {})
    report["weighted_mesh_attachments_emitted"] = weight_binding.get("weighted_mesh_attachments_emitted", 0)
    report["weighted_influence_count"] = weight_binding.get("weighted_influence_count", 0)
    report["max_bones_per_vertex"] = weight_binding.get("max_bones_per_vertex", 0)
    report["avg_bones_per_vertex"] = weight_binding.get("avg_bones_per_vertex", 0.0)
    report["estimated_vertex_transforms"] = weight_binding.get("estimated_vertex_transforms", 0)
    report["weight_binding_policy"] = weight_binding.get("policy")
    report["weighted_mesh_review_required"] = weight_binding.get("review_required", False)
    report["weighted_mesh_review_required_reason"] = weight_binding.get("review_required_reason")
    report["mesh_plan"] = mesh_report
    report["mesh_candidate_report"] = mesh_candidate_report
    report["auto_mesh_plan"] = auto_mesh_plan_report
    report["mesh_deformation_qa"] = mesh_deformation_qa
    report["skin_variants_emitted"] = skin_report["emitted_count"]
    report["skin_plan"] = skin_report
    report["output_files"] = output_file_status(out_dir)
    if report["output_files"]["missing"]:
        report["errors"].extend(
            f"missing required output file for handoff: {name}"
            for name in report["output_files"]["missing"]
        )
        report["status"] = "failed"
    if physics_report["warnings"]:
        report["warnings"].extend(physics_report["warnings"])
    if physics_report["errors"]:
        report["errors"].extend(physics_report["errors"])
        report["status"] = "failed"
    if mesh_report["issues"]:
        report["errors"].extend(mesh_report["issues"])
        report["status"] = "failed"
    if skin_report["issues"]:
        report["errors"].extend(skin_report["issues"])
        report["status"] = "failed"
    if avatar_manifest_issues:
        report["errors"].extend(avatar_manifest_issues)
        report["status"] = "failed"
    if event_plan_errors:
        report["errors"].extend(event_plan_errors)
        report["status"] = "failed"
    if loop_report["issues"]:
        report["errors"].extend(issue["message"] for issue in loop_report["issues"])
        report["status"] = "failed"
    if expression_visual_qa.get("enabled") and not expression_visual_qa.get("passed"):
        report["errors"].append("expression composite visual QA failed deterministic PNG checks")
        report["status"] = "failed"
    if mesh_deformation_qa.get("enabled") and not mesh_deformation_qa.get("passed"):
        report["errors"].append("mesh deformation QA failed deterministic structural checks")
        report["status"] = "failed"
    expression_issues = expression_composite_validation.get("issues", [])
    if expression_issues:
        report["errors"].extend(
            issue.get("message", str(issue))
            for issue in expression_issues
        )
        report["status"] = "failed"
    timeline_issues = expression_timeline_merge.get("issues", [])
    if timeline_issues:
        report["errors"].extend(
            issue.get("message", str(issue))
            for issue in timeline_issues
        )
        report["status"] = "failed"
    (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))

    # 7c. (Optional) Render QA frames for vision-driven review.
    if args.render_qa_frames:
        import render_preview_frames as rpf  # noqa: E402
        from PIL import Image  # type: ignore
        qa_dir = out_dir / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        regions_for_qa = rpf.parse_atlas(out_dir / ATLAS_NAME)
        atlas_image = Image.open(out_dir / PAGE_NAME).convert("RGBA")
        setup_img = rpf.render_setup_pose(skel, atlas_image, regions_for_qa)
        setup_img.save(qa_dir / "setup.png", "PNG")
        print(f"  QA frame: {qa_dir / 'setup.png'}")

    # 7e. (Optional) Generate preview.html with Spine Web Player.
    if args.build_preview:
        preview_path = preview_html.build_preview_html(out_dir, args.layer_dir)
        if physics_has_preview_subject:
            report["physics_preview_html_generated"] = True
            report["physics_runtime_requirements"]["preview_html"] = str(preview_path)
        if expression_visual_qa["enabled"]:
            expression_visual_qa["preview_html_generated"] = True
            expression_visual_qa["preview_html"] = str(preview_path)
            report["expression_composite_visual_qa"] = expression_visual_qa
        (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
        print(f"  preview.html: {preview_path}")

    if args.spine_editor_zip:
        handoff_path = handoff.package_handoff(out_dir)
        report["spine_editor_handoff"] = {
            "enabled": True,
            "zip": str(handoff_path),
            "status": "ok",
        }
        (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
        print(f"  Spine Editor handoff ZIP: {handoff_path}")

    if args.create_spine_project:
        try:
            spine_project_report = native_spine.create_spine_project(
                out_dir,
                output_project=Path(args.spine_project_output) if args.spine_project_output else None,
                spine_cli=Path(args.spine_cli) if args.spine_cli else None,
                spine_version=args.spine_version,
            )
        except (OSError, ValueError, native_spine.SpineProjectError) as exc:
            spine_project_report = {
                "status": "failed",
                "output_project": str(Path(args.spine_project_output).resolve()) if args.spine_project_output else "",
                "errors": [str(exc)],
            }
        report["native_spine_project"] = {
            "enabled": True,
            "status": spine_project_report["status"],
            "output_project": spine_project_report["output_project"],
            "report": str(out_dir / native_spine.REPORT_NAME),
        }
        if spine_project_report["status"] != "ok":
            report["status"] = "failed"
            report["errors"].extend(
                spine_project_report.get("errors", ["native .spine project creation failed"])
            )
        (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
        if spine_project_report["status"] == "ok":
            print(f"  native .spine project: {spine_project_report['output_project']}")

    # 7d. Append a learning-log entry capturing this build.
    project_dir_for_log = ctx_path.parent if ctx_path else layer_dir.parent
    learning_log_guard_error = _source_art_write_guard_error(project_dir_for_log)
    if learning_log_guard_error:
        report["warnings"].append(learning_log_guard_error)
        report["learning_log_skipped"] = True
        report["learning_log_skip_reason"] = learning_log_guard_error
        (out_dir / REPORT_NAME).write_text(json.dumps(report, indent=2))
    else:
        report["learning_log_skipped"] = False
    flags_enabled: list[str] = []
    for flag_attr in (
        "composite_expressions", "render_qa_frames",
        "enable_ik", "enable_transform_constraints",
        "enable_sequences", "enable_physics", "mesh_plan", "report_mesh_candidates", "auto_mesh_plan", "auto_bind_weights",
        "skin_plan", "build_preview", "spine_editor_zip", "create_spine_project",
        "production_export_profile", "check_production_export_gate", "run_runtime_acceptance_probe",
    ):
        if getattr(args, flag_attr, False):
            flags_enabled.append(flag_attr)
    if args.enable_clipping:
        flags_enabled.append("enable_clipping")
    if args.enable_events:
        flags_enabled.append("enable_events")
    build_payload = {
        "layer_dir": str(layer_dir),
        "family": args.family,
        "rank": args.rank,
        "controls_applied": bounded,
        "flags_enabled": flags_enabled,
        "out_dir": str(out_dir.resolve()),
        "validation_status": report["status"],
        "bones_count": report["bones_count"],
        "slots_count": report["slots_count"],
        "animations": report["animations"],
        "context_applied": context_applied,
    }
    if not learning_log_guard_error:
        ll.log_build(project_dir_for_log, build_payload, ctx_path)
        if report["status"] != "ok":
            ll.log_validation_failure(project_dir_for_log, {
                "package_dir": str(out_dir.resolve()),
                "errors": report["errors"],
                "warnings": report["warnings"],
            }, ctx_path)

    production_gate_report: dict | None = None
    production_gate_exit_code = 0
    if args.check_production_export_gate or args.production_export_profile:
        production_gate_report, production_gate_exit_code = peg.run_gate(
            out_dir,
            Path(args.production_export_profile) if args.production_export_profile else None,
            run_runtime_probe=args.run_runtime_acceptance_probe,
        )

    # 8. Summary
    print(f"=== Spine package built ({skel['skeleton']['spine']}): {out_dir} ===")
    print(f"  family={args.family}, rank={args.rank}")
    print(f"  doc: {int(doc_w)}x{int(doc_h)}  atlas: {atlas_size[0]}x{atlas_size[1]}")
    print(f"  bones: {report['bones_count']}, slots: {report['slots_count']}, animations: {report['animations']}")
    if ik_constraints:
        print(f"  IK constraints: {[c['name'] for c in ik_constraints]}")
    if transform_constraints:
        print(f"  transform constraints: {[c['name'] for c in transform_constraints]}")
    if physics_constraints_list:
        print(f"  physics constraints: {[c['name'] for c in physics_constraints_list]}")
    if sequence_specs:
        print(f"  sequence attachments: {list(sequence_specs.keys())}")
    if mesh_report["emitted_count"]:
        print(f"  mesh attachments: {mesh_report['emitted_count']}")
    if report["weighted_mesh_attachments_emitted"]:
        print(f"  weighted mesh attachments: {report['weighted_mesh_attachments_emitted']}")
    if report["skin_variants_emitted"]:
        print(f"  skin variants: {skin_report['skin_names']}")
    if clip_attachments:
        print(f"  clipping: {[c['name'] for c in clip_attachments]}")
    if event_defs:
        print(f"  events: {list(event_defs.keys())}")
    if ctx_path and not learning_log_guard_error:
        print(f"  learning log: {project_dir_for_log / ll.LOG_FILENAME}")
    print(f"  validation: {report['status']}")
    if report["errors"]:
        for e in report["errors"]:
            print(f"    ERROR: {e}")
        return 2
    if production_gate_report:
        print(f"  production export gate: {production_gate_report['status']}")
        if production_gate_exit_code != 0:
            for e in production_gate_report["errors"]:
                print(f"    EXPORT GATE: {e}")
            return production_gate_exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
