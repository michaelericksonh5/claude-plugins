#!/usr/bin/env python3
"""Reviewed unweighted mesh plan validation and layout application."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import auto_bind_weights as abw


DEFAULT_MAX_VERTEX_BUDGET = 48
AUTO_GUESS_FIELDS = {"auto", "auto_guess", "auto_trace", "automatic", "guess", "trace"}
EXPECTED_SCHEMA = "spine_slot_animation_mesh_plan_v1"
EXPECTED_WEIGHT_POLICY_SCHEMA = "spine_slot_animation_weight_binding_policy_v1"
ROOT_FIELDS = {"schema", "max_vertex_budget", "attachments", "weight_binding_policy", "auto_generated", "review_required", "generation"}
ROOT_REQUIRED_FIELDS = {"schema", "max_vertex_budget", "attachments"}
ATTACHMENT_FIELDS = {
    "reviewed",
    "auto_generated",
    "review_required",
    "generation_method",
    "source_layer",
    "target_slot",
    "path",
    "hull_vertices",
    "interior_vertices",
    "triangles",
    "uvs",
    "hull_count",
    "max_vertex_budget",
    "edges",
    "color",
    "vertices",
    "allowed_bones",
}
MESH_CANDIDATE_REPORT_SCHEMA = "spine_slot_animation_mesh_candidate_report_v1"
AUTO_MESH_PLAN_REPORT_SCHEMA = "spine_slot_animation_auto_mesh_plan_report_v1"
CANDIDATE_ROLES = {"hair", "cape", "cloak", "tails", "antennae", "earrings", "dangling_jewelry"}
BODY_CANDIDATE_ROLES = {"character_body"}
REVIEW_ONLY_ROLES = {"beard", "mustache", "dress", "skirt", "robe", "sleeve", "scarf", "ribbon", "chain", "necklace", "wings"}
REGION_ONLY_ROLES = {
    "letter", "tier_text", "value_text", "glow", "sparkle", "shimmer", "shine", "frame", "frame_glow",
    "back_frame", "front_frame", "glass", "hat_top", "hat_base", "cap_top", "crown_top", "helmet_top",
    "head", "hand", "hand_left", "hand_right", "hand_detail", "background", "boilerplate",
}
ATTACHMENT_REQUIRED_FIELDS = {
    "reviewed",
    "source_layer",
    "target_slot",
    "hull_vertices",
    "interior_vertices",
    "triangles",
    "uvs",
    "hull_count",
    "max_vertex_budget",
}
POLICY_FIELDS = {
    "schema",
    "max_bones_per_vertex",
    "weight_epsilon",
    "influence_threshold",
    "smoothing_iterations",
    "max_estimated_vertex_transforms",
    "allowed_bones_by_slot",
    "review_required",
    "bind_position_mode",
}
POLICY_REQUIRED_FIELDS = {
    "schema",
    "max_bones_per_vertex",
    "weight_epsilon",
    "influence_threshold",
    "smoothing_iterations",
    "max_estimated_vertex_transforms",
    "review_required",
    "bind_position_mode",
}


def load_mesh_plan(path: Path) -> dict:
    return json.loads(path.read_text())


def load_weight_binding_policy(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_and_apply_mesh_plan(
    layout: dict,
    plan: dict,
    layer_dir: Path,
) -> tuple[dict, dict]:
    """Validate a reviewed Phase 2 mesh plan and convert matching layout attachments."""
    issues: list[str] = []
    if not isinstance(plan, dict):
        return layout, _report({}, ["mesh_plan must be an object"], 0)
    _validate_closed_object(plan, "mesh_plan", ROOT_FIELDS, ROOT_REQUIRED_FIELDS, issues)
    if plan.get("schema") != EXPECTED_SCHEMA:
        issues.append(f"mesh_plan.schema must be {EXPECTED_SCHEMA!r}")
    attachments = plan.get("attachments")
    if not isinstance(attachments, list):
        issues.append("mesh_plan.attachments must be a list")
        attachments = []

    global_budget = plan.get("max_vertex_budget", DEFAULT_MAX_VERTEX_BUDGET)
    if not _is_int(global_budget) or global_budget < 3:
        issues.append("mesh_plan.max_vertex_budget must be an integer >= 3")
        global_budget = DEFAULT_MAX_VERTEX_BUDGET

    layout_by_slot = {
        att.get("slot"): att for att in layout.get("attachments", [])
    }
    slots = {slot.get("name") for slot in layout.get("slots", [])}
    layers_by_stem = {
        Path(att.get("layer_name", "")).stem: att for att in layout.get("attachments", [])
    }
    layers_by_name = {
        att.get("layer_name"): att for att in layout.get("attachments", [])
    }
    planned_by_slot: dict[str, dict] = {}

    for idx, entry in enumerate(attachments):
        prefix = f"mesh_plan.attachments[{idx}]"
        if not isinstance(entry, dict):
            issues.append(f"{prefix} must be an object")
            continue
        _validate_closed_object(entry, prefix, ATTACHMENT_FIELDS, ATTACHMENT_REQUIRED_FIELDS, issues)
        for field in AUTO_GUESS_FIELDS:
            if entry.get(field):
                issues.append(f"{prefix} uses unsupported automatic mesh guessing field {field!r}")
        auto_generated = entry.get("auto_generated") is True
        if entry.get("reviewed") is not True and not auto_generated:
            issues.append(f"{prefix}.reviewed must be true unless auto_generated is true")
        if auto_generated and entry.get("review_required") is not True:
            issues.append(f"{prefix}.review_required must be true for automatic draft mesh plans")

        source_layer = entry.get("source_layer")
        target_slot = entry.get("target_slot")
        if not isinstance(source_layer, str) or not source_layer:
            issues.append(f"{prefix}.source_layer is required")
        if not isinstance(target_slot, str) or not target_slot:
            issues.append(f"{prefix}.target_slot is required")
            continue
        if target_slot not in slots:
            issues.append(f"{prefix}.target_slot {target_slot!r} is not in the rig layout")
            continue
        if target_slot in planned_by_slot:
            issues.append(f"{prefix}.target_slot {target_slot!r} is planned more than once")
            continue

        source_key = Path(str(source_layer)).stem if source_layer else ""
        source_att = layers_by_stem.get(source_key) or layers_by_name.get(source_layer)
        target_att = layout_by_slot.get(target_slot)
        if source_att is None:
            issues.append(f"{prefix}.source_layer {source_layer!r} is not in the rig layout")
            continue
        if target_att is None:
            issues.append(f"{prefix}.target_slot {target_slot!r} has no attachment")
            continue
        if source_att.get("slot") != target_slot:
            issues.append(
                f"{prefix}.source_layer {source_layer!r} does not belong to target_slot {target_slot!r}"
            )

        source_image = _find_source_image(layer_dir, str(source_layer), source_att)
        if source_image is None:
            issues.append(f"{prefix}.source_layer {source_layer!r} has no source PNG in {layer_dir}")

        hull_vertices = _point_list(entry.get("hull_vertices"), f"{prefix}.hull_vertices", issues)
        interior_vertices = _point_list(entry.get("interior_vertices", []), f"{prefix}.interior_vertices", issues)
        vertices = hull_vertices + interior_vertices
        uvs = _point_list(entry.get("uvs"), f"{prefix}.uvs", issues)
        triangles = _int_list(entry.get("triangles"), f"{prefix}.triangles", issues)
        hull_count = entry.get("hull_count", entry.get("hull"))
        if not _is_int(hull_count):
            issues.append(f"{prefix}.hull_count must be an integer")
            hull_count = len(hull_vertices)
        if hull_count != len(hull_vertices):
            issues.append(f"{prefix}.hull_count must equal the number of hull_vertices")
        if hull_count < 3:
            issues.append(f"{prefix}.hull_count must be at least 3")
        if hull_count > len(vertices):
            issues.append(f"{prefix}.hull_count must not exceed vertex count")
        if len(uvs) != len(vertices):
            issues.append(f"{prefix}.uvs must contain one x/y pair per mesh vertex")
        for uv_idx, uv in enumerate(uvs):
            if not (0.0 <= uv[0] <= 1.0 and 0.0 <= uv[1] <= 1.0):
                issues.append(f"{prefix}.uvs[{uv_idx}] must be in the [0, 1] range")
        if "vertices" in entry and _flat_len(entry.get("vertices")) > (len(uvs) * 2):
            issues.append(f"{prefix}.vertices uses weighted mesh encoding, which is Phase 3")
        if len(triangles) % 3 != 0:
            issues.append(f"{prefix}.triangles length must be a multiple of 3")
        for tri_idx in triangles:
            if tri_idx < 0 or tri_idx >= len(vertices):
                issues.append(f"{prefix}.triangles index {tri_idx} is out of range")
                break
        for tri in range(0, len(triangles), 3):
            if tri + 2 >= len(triangles):
                break
            if _degenerate_triangle(vertices, triangles[tri:tri + 3]):
                issues.append(f"{prefix}.triangles[{tri // 3}] must not be degenerate")
                break
        if _self_intersects(hull_vertices):
            issues.append(f"{prefix}.hull_vertices must not self-intersect")

        budget = entry.get("max_vertex_budget", global_budget)
        if not _is_int(budget) or budget < 3:
            issues.append(f"{prefix}.max_vertex_budget must be an integer >= 3")
            budget = global_budget
        if len(vertices) > budget:
            issues.append(f"{prefix} has {len(vertices)} vertices, over budget {budget}")

        path = entry.get("path", target_att.get("path"))
        if path != target_att.get("path"):
            issues.append(f"{prefix}.path must match the existing atlas attachment path {target_att.get('path')!r}")

        if not any(issue.startswith(prefix) for issue in issues):
            mesh = {
                "slot": target_slot,
                "name": target_att["name"],
                "path": target_att["path"],
                "type": "mesh",
                "uvs": _flatten_points(uvs),
                "triangles": triangles,
                "vertices": _flatten_points(vertices),
                "hull": hull_count,
                "width": target_att["width"],
                "height": target_att["height"],
                "layer_name": target_att["layer_name"],
                "mesh_plan_source_layer": source_layer,
            }
            edges = _edges(entry.get("edges"), f"{prefix}.edges", issues)
            for edge_idx in edges:
                if edge_idx < 0 or edge_idx >= len(vertices):
                    issues.append(f"{prefix}.edges index {edge_idx} is out of range")
                    break
            if edges:
                mesh["edges"] = edges
            if entry.get("color"):
                mesh["color"] = entry["color"]
            if auto_generated:
                mesh["mesh_plan_auto_generated"] = True
                mesh["mesh_plan_review_required"] = True
            if not any(issue.startswith(prefix) for issue in issues):
                planned_by_slot[target_slot] = mesh

    if issues:
        return layout, _report(plan, issues, 0)

    new_layout = dict(layout)
    new_layout["attachments"] = [
        planned_by_slot.get(att.get("slot"), att)
        for att in layout.get("attachments", [])
    ]
    new_layout["mesh_plan"] = {
        "schema": plan.get("schema", EXPECTED_SCHEMA),
        "planned_slots": sorted(planned_by_slot),
    }
    return new_layout, _report(plan, [], len(planned_by_slot))


def validate_atlas_paths(layout: dict, atlas_records: list[dict], mesh_report: dict) -> dict:
    if not mesh_report.get("enabled"):
        return mesh_report
    region_names = {record["name"] for record in atlas_records}
    issues = list(mesh_report.get("issues", []))
    for att in layout.get("attachments", []):
        if att.get("type") == "mesh" and att.get("path") not in region_names:
            issues.append(f"mesh attachment {att.get('name')!r} path {att.get('path')!r} missing from atlas")
    out = dict(mesh_report)
    out["issues"] = issues
    out["issue_count"] = len(issues)
    return out


def build_mesh_candidate_report(
    layout: dict,
    layer_dir: Path,
    controls: dict | None = None,
    enabled: bool = False,
) -> dict:
    entries: list[dict] = []
    for att in layout.get("attachments", []):
        slot = _slot_for_attachment(layout, att)
        bone = _bone_for_slot(layout, (slot or {}).get("bone", ""))
        role = (slot or {}).get("semantic_role") or bone.get("semantic_role")
        source_image = _find_source_image(layer_dir, str(att.get("layer_name", "")), att)
        metrics = _alpha_metrics(source_image)
        status, reason = _candidate_status(role, metrics, controls or {})
        entries.append({
            "source_layer": att.get("layer_name"),
            "target_slot": att.get("slot"),
            "semantic_role": role,
            "status": status,
            "reason": reason,
            "alpha_coverage": metrics.get("alpha_coverage"),
            "visible_bbox": metrics.get("visible_bbox"),
            "image_size": metrics.get("image_size"),
            "allowed_bones": derive_allowed_bones(layout, att.get("slot", ""), role),
            "helper_bones_added": 0,
        })
    counts = {
        "mesh_candidate": sum(1 for item in entries if item["status"] == "mesh_candidate"),
        "region_only": sum(1 for item in entries if item["status"] == "region_only"),
        "review_only": sum(1 for item in entries if item["status"] == "review_only"),
    }
    return {
        "schema": MESH_CANDIDATE_REPORT_SCHEMA,
        "enabled": enabled,
        "review_required": True,
        "candidate_count": counts["mesh_candidate"],
        "counts": counts,
        "helper_bone_policy": "existing_bones_only",
        "entries": entries,
        "note": "Automatic mesh candidates are deterministic first-pass proposals; animator review remains required.",
    }


def generate_auto_mesh_plan(layout: dict, layer_dir: Path, candidate_report: dict) -> tuple[dict, dict]:
    attachments: list[dict] = []
    issues: list[str] = []
    layout_by_slot = {att.get("slot"): att for att in layout.get("attachments", [])}
    for candidate in candidate_report.get("entries", []):
        if candidate.get("status") != "mesh_candidate":
            continue
        target_slot = candidate.get("target_slot")
        att = layout_by_slot.get(target_slot)
        if not att:
            issues.append(f"candidate target_slot {target_slot!r} has no attachment")
            continue
        try:
            attachments.append(_auto_mesh_plan_attachment(att, candidate, layer_dir))
        except ValueError as exc:
            issues.append(str(exc))
    plan = {
        "schema": EXPECTED_SCHEMA,
        "max_vertex_budget": DEFAULT_MAX_VERTEX_BUDGET,
        "auto_generated": True,
        "review_required": True,
        "generation": {
            "schema": AUTO_MESH_PLAN_REPORT_SCHEMA,
            "method": "alpha_bbox_hull_with_role_interiors",
            "first_pass_only": True,
            "spine_auto_parity_claimed": False,
        },
        "attachments": attachments,
    }
    return plan, {
        "schema": AUTO_MESH_PLAN_REPORT_SCHEMA,
        "enabled": True,
        "status": "ok" if not issues else "failed",
        "planned_count": len(attachments),
        "issues": issues,
        "review_required": True,
    }


def derive_allowed_bones(layout: dict, slot_name: str, semantic_role: str | None) -> list[str]:
    slots = {slot.get("name"): slot for slot in layout.get("slots", [])}
    bones = {bone.get("name"): bone for bone in layout.get("bones", [])}
    slot = slots.get(slot_name, {})
    bone_name = slot.get("bone")
    out: list[str] = []

    def add(name: str | None) -> None:
        if isinstance(name, str) and name in bones and name not in out:
            out.append(name)

    bone = bones.get(bone_name)
    add((bone or {}).get("parent"))
    add(bone_name)
    if semantic_role in BODY_CANDIDATE_ROLES:
        for child in layout.get("bones", []):
            if child.get("parent") == bone_name and child.get("semantic_role") in {"head", "tails", "wings"}:
                add(child.get("name"))
    return out


def apply_auto_bind_weights(
    layout: dict,
    plan: dict,
    base_policy: dict,
    mesh_report: dict,
) -> tuple[dict, dict]:
    issues: list[str] = list(mesh_report.get("issues", []))
    policy = _merge_weight_policy(base_policy, plan.get("weight_binding_policy"))
    _validate_weight_policy(policy, "weight_binding_policy", issues)
    if issues:
        return layout, _weight_report(mesh_report, policy, issues, [])

    bone_indices = {bone.get("name"): idx for idx, bone in enumerate(layout.get("bones", []))}
    bone_world, bone_issues = _bone_world_positions(layout.get("bones", []))
    issues.extend(bone_issues)
    slots = {slot.get("name"): slot for slot in layout.get("slots", [])}
    plan_by_slot = {
        entry.get("target_slot"): entry
        for entry in plan.get("attachments", [])
        if isinstance(entry, dict)
    }
    policy_allowed = policy.get("allowed_bones_by_slot", {})
    weighted_attachments = []
    summaries: list[dict] = []

    for att in layout.get("attachments", []):
        if att.get("type") != "mesh":
            weighted_attachments.append(att)
            continue
        slot_name = att.get("slot")
        entry = plan_by_slot.get(slot_name)
        prefix = f"mesh attachment {att.get('name')!r} (slot {slot_name!r})"
        allowed = None
        if isinstance(entry, dict) and "allowed_bones" in entry:
            allowed = entry.get("allowed_bones")
        elif isinstance(policy_allowed, dict) and slot_name in policy_allowed:
            allowed = policy_allowed.get(slot_name)
        if not isinstance(allowed, list) or not allowed or not all(isinstance(name, str) and name for name in allowed):
            issues.append(f"{prefix} requires explicit allowed_bones for --auto-bind-weights")
            weighted_attachments.append(att)
            continue

        slot = slots.get(slot_name)
        if not slot or slot.get("bone") not in bone_world:
            issues.append(f"{prefix} target slot bone is missing from layout")
            weighted_attachments.append(att)
            continue
        slot_world = bone_world[slot["bone"]]
        bones_for_binding = []
        missing = [name for name in allowed if name not in bone_indices]
        if missing:
            issues.append(f"{prefix} allowed_bones reference missing bones: {missing}")
            weighted_attachments.append(att)
            continue
        for name in allowed:
            bone = next(b for b in layout["bones"] if b.get("name") == name)
            if float(bone.get("rotation", 0) or 0) != 0.0:
                issues.append(f"{prefix} cannot auto-bind rotated setup bone {name!r}")
            bx, by = bone_world[name]
            bones_for_binding.append({
                "name": name,
                "index": bone_indices[name],
                "x": bx - slot_world[0],
                "y": by - slot_world[1],
            })
        if any(issue.startswith(prefix) for issue in issues):
            weighted_attachments.append(att)
            continue

        vertices = _points_from_flat(att.get("vertices", []), f"{prefix}.vertices", issues)
        triangles = att.get("triangles", [])
        weights = abw.auto_bind_weights(
            vertices,
            bones_for_binding,
            max_bones_per_vertex=policy["max_bones_per_vertex"],
            weight_threshold=policy["influence_threshold"],
            smooth_iterations=policy["smoothing_iterations"],
            triangles=triangles,
        )
        weighted_vertices = _weights_to_spine_vertices(vertices, weights, bones_for_binding)
        validation_issues, summary = validate_weighted_vertices_block(
            weighted_vertices,
            len(att.get("uvs", [])) // 2,
            len(layout.get("bones", [])),
            policy["max_bones_per_vertex"],
            policy["weight_epsilon"],
            prefix,
        )
        issues.extend(validation_issues)
        summary["slot"] = slot_name
        summary["attachment"] = att.get("name")
        summary["bound_bones"] = [bone["name"] for bone in bones_for_binding]
        summary["endpoint_locked_vertices"] = _endpoint_locked_vertex_count(weights)
        summary["topology_smoothing_iterations"] = policy["smoothing_iterations"]
        summary["prune_threshold"] = policy["influence_threshold"]
        out = dict(att)
        out["vertices"] = weighted_vertices
        weighted_attachments.append(out)
        summaries.append(summary)

    estimated_transforms = sum(int(summary["estimated_vertex_transforms"]) for summary in summaries)
    if estimated_transforms > policy["max_estimated_vertex_transforms"]:
        issues.append(
            f"aggregate estimated vertex transforms {estimated_transforms} exceed policy "
            f"max_estimated_vertex_transforms {policy['max_estimated_vertex_transforms']}"
        )

    if issues:
        return layout, _weight_report(mesh_report, policy, issues, summaries)

    new_layout = dict(layout)
    new_layout["attachments"] = weighted_attachments
    return new_layout, _weight_report(mesh_report, policy, issues, summaries)


def validate_weighted_vertices_block(
    vertices: list,
    vertex_count: int,
    skeleton_bone_count: int,
    max_bones_per_vertex: int,
    epsilon: float,
    prefix: str,
) -> tuple[list[str], dict]:
    issues: list[str] = []
    influence_count = 0
    max_influences = 0
    cursor = 0
    for vertex_idx in range(vertex_count):
        if cursor >= len(vertices):
            issues.append(f"{prefix} weighted vertices ended before vertex {vertex_idx}")
            break
        count = vertices[cursor]
        cursor += 1
        if not _is_int(count):
            issues.append(f"{prefix} vertex {vertex_idx} influence count must be an integer")
            break
        if count < 1:
            issues.append(f"{prefix} vertex {vertex_idx} must have at least one influence")
        if count > max_bones_per_vertex:
            issues.append(f"{prefix} vertex {vertex_idx} has {count} influences over max {max_bones_per_vertex}")
        max_influences = max(max_influences, int(count))
        total = 0.0
        for influence_idx in range(int(count)):
            if cursor + 3 >= len(vertices):
                issues.append(f"{prefix} vertex {vertex_idx} influence {influence_idx} is truncated")
                cursor = len(vertices)
                break
            bone_idx, bind_x, bind_y, weight = vertices[cursor:cursor + 4]
            cursor += 4
            if not _is_int(bone_idx) or bone_idx < 0 or bone_idx >= skeleton_bone_count:
                issues.append(f"{prefix} vertex {vertex_idx} bone index {bone_idx!r} is out of range")
            if not _is_number(bind_x) or not _is_number(bind_y):
                issues.append(f"{prefix} vertex {vertex_idx} bind position must be finite")
            if not _is_number(weight) or not (0.0 <= float(weight) <= 1.0):
                issues.append(f"{prefix} vertex {vertex_idx} weight must be finite and in [0, 1]")
            else:
                total += float(weight)
            influence_count += 1
        if abs(total - 1.0) > epsilon:
            issues.append(f"{prefix} vertex {vertex_idx} weights sum to {total:.6f}, outside epsilon {epsilon}")
    if cursor != len(vertices):
        issues.append(f"{prefix} weighted vertices have trailing values")
    avg = influence_count / vertex_count if vertex_count else 0.0
    return issues, {
        "vertex_count": vertex_count,
        "influence_count": influence_count,
        "max_bones_per_vertex": max_influences,
        "avg_bones_per_vertex": avg,
        "estimated_vertex_transforms": influence_count,
    }


def _report(plan: dict, issues: list[str], emitted: int) -> dict:
    return {
        "enabled": True,
        "schema": plan.get("schema"),
        "planned_count": len(plan.get("attachments", [])) if isinstance(plan.get("attachments"), list) else 0,
        "emitted_count": emitted,
        "issue_count": len(issues),
        "issues": issues,
    }


def _weight_report(mesh_report: dict, policy: dict, issues: list[str], summaries: list[dict]) -> dict:
    out = dict(mesh_report)
    out["issues"] = issues
    out["issue_count"] = len(issues)
    emitted = 0 if issues else len(summaries)
    influence_count = sum(int(summary["influence_count"]) for summary in summaries)
    vertex_count = sum(int(summary["vertex_count"]) for summary in summaries)
    out["weight_binding"] = {
        "enabled": True,
        "schema": policy.get("schema"),
        "algorithm": "topology_aware_first_pass_projection_smooth_prune",
        "weighted_mesh_attachments_emitted": emitted,
        "weighted_influence_count": influence_count if not issues else 0,
        "max_bones_per_vertex": max((int(summary["max_bones_per_vertex"]) for summary in summaries), default=0) if not issues else 0,
        "avg_bones_per_vertex": (influence_count / vertex_count) if vertex_count and not issues else 0.0,
        "estimated_vertex_transforms": influence_count if not issues else 0,
        "policy": {
            "max_bones_per_vertex": policy.get("max_bones_per_vertex"),
            "weight_epsilon": policy.get("weight_epsilon"),
            "influence_threshold": policy.get("influence_threshold"),
            "smoothing_iterations": policy.get("smoothing_iterations"),
            "max_estimated_vertex_transforms": policy.get("max_estimated_vertex_transforms"),
            "bind_position_mode": policy.get("bind_position_mode"),
        },
        "review_required": True,
        "review_required_reason": (
            "First-pass topology-aware automatic binding only; bindX/bindY use approximate local offsets "
            "and animator weight review/final weight painting is required."
        ),
        "attachment_summaries": summaries if not issues else [],
    }
    return out


def _merge_weight_policy(base_policy: dict, override: Any) -> dict:
    merged = dict(base_policy) if isinstance(base_policy, dict) else {}
    if override is None:
        return merged
    if isinstance(override, dict):
        merged.update(override)
    else:
        merged["_invalid_override"] = override
    return merged


def _validate_weight_policy(policy: dict, name: str, issues: list[str]) -> None:
    if not isinstance(policy, dict):
        issues.append(f"{name} must be an object")
        return
    _validate_closed_object(policy, name, POLICY_FIELDS, POLICY_REQUIRED_FIELDS, issues)
    if "_invalid_override" in policy:
        issues.append(f"{name} override must be an object")
    if policy.get("schema") != EXPECTED_WEIGHT_POLICY_SCHEMA:
        issues.append(f"{name}.schema must be {EXPECTED_WEIGHT_POLICY_SCHEMA!r}")
    if not _is_int(policy.get("max_bones_per_vertex")) or not (1 <= policy.get("max_bones_per_vertex", 0) <= 8):
        issues.append(f"{name}.max_bones_per_vertex must be an integer in [1, 8]")
    if not _is_number(policy.get("weight_epsilon")) or not (0.0 < float(policy.get("weight_epsilon", 0)) <= 0.01):
        issues.append(f"{name}.weight_epsilon must be a number in (0, 0.01]")
    if not _is_number(policy.get("influence_threshold")) or not (0.0 <= float(policy.get("influence_threshold", -1)) < 1.0):
        issues.append(f"{name}.influence_threshold must be a number in [0, 1)")
    if not _is_int(policy.get("smoothing_iterations")) or policy.get("smoothing_iterations", -1) < 0:
        issues.append(f"{name}.smoothing_iterations must be an integer >= 0")
    if not _is_int(policy.get("max_estimated_vertex_transforms")) or policy.get("max_estimated_vertex_transforms", 0) < 1:
        issues.append(f"{name}.max_estimated_vertex_transforms must be an integer >= 1")
    if policy.get("review_required") is not True:
        issues.append(f"{name}.review_required must be true")
    if policy.get("bind_position_mode") != "approximate_local_offset":
        issues.append(f"{name}.bind_position_mode must be 'approximate_local_offset'")
    allowed = policy.get("allowed_bones_by_slot", {})
    if allowed is None:
        return
    if not isinstance(allowed, dict):
        issues.append(f"{name}.allowed_bones_by_slot must be an object")
        return
    for slot, bones in allowed.items():
        if not isinstance(slot, str) or not slot:
            issues.append(f"{name}.allowed_bones_by_slot keys must be non-empty strings")
        if not isinstance(bones, list) or not bones or not all(isinstance(b, str) and b for b in bones):
            issues.append(f"{name}.allowed_bones_by_slot[{slot!r}] must be a non-empty list of bone names")


def _bone_world_positions(bones: list[dict]) -> tuple[dict[str, tuple[float, float]], list[str]]:
    by_name = {bone.get("name"): bone for bone in bones}
    world: dict[str, tuple[float, float]] = {}
    issues: list[str] = []

    def resolve(name: str, stack: set[str]) -> tuple[float, float]:
        if name in world:
            return world[name]
        bone = by_name.get(name)
        if not bone:
            issues.append(f"bone {name!r} is missing from layout")
            return 0.0, 0.0
        if name in stack:
            issues.append(f"bone hierarchy cycle at {name!r}")
            return 0.0, 0.0
        parent = bone.get("parent")
        px, py = resolve(parent, stack | {name}) if parent else (0.0, 0.0)
        world[name] = (px + float(bone.get("x", 0) or 0), py + float(bone.get("y", 0) or 0))
        return world[name]

    for bone in bones:
        if isinstance(bone.get("name"), str):
            resolve(bone["name"], set())
    return world, issues


def _points_from_flat(value: Any, field: str, issues: list[str]) -> list[tuple[float, float]]:
    if not isinstance(value, list) or len(value) % 2 != 0 or not all(_is_number(v) for v in value):
        issues.append(f"{field} must be a flat even numeric list")
        return []
    return [(float(value[i]), float(value[i + 1])) for i in range(0, len(value), 2)]


def _weights_to_spine_vertices(
    vertices: list[tuple[float, float]],
    weights: list[list[tuple[int, float]]],
    bones: list[dict],
) -> list[float]:
    flat: list[float] = []
    for vertex, influences in zip(vertices, weights):
        flat.append(len(influences))
        for local_idx, weight in influences:
            bone = bones[local_idx]
            flat.extend([
                int(bone["index"]),
                vertex[0] - float(bone["x"]),
                vertex[1] - float(bone["y"]),
                float(weight),
            ])
    return flat


def _slot_for_attachment(layout: dict, att: dict) -> dict:
    slot_name = att.get("slot")
    return next((slot for slot in layout.get("slots", []) if slot.get("name") == slot_name), {})


def _bone_for_slot(layout: dict, bone_name: str) -> dict:
    return next((bone for bone in layout.get("bones", []) if bone.get("name") == bone_name), {})


def _candidate_status(role: str | None, metrics: dict, controls: dict) -> tuple[str, str]:
    if not metrics.get("visible_bbox"):
        return "region_only", "no visible alpha hull found"
    if role in CANDIDATE_ROLES:
        return "mesh_candidate", f"{role} is a conservative weighted-mesh candidate"
    if role in BODY_CANDIDATE_ROLES:
        if _body_deformation_requested(controls):
            return "mesh_candidate", "character_body has explicit bending/squash-style controls"
        return "region_only", "character_body stays region-only without explicit deformation request"
    if role in REVIEW_ONLY_ROLES:
        return "review_only", f"{role} can deform, but needs reviewed mesh authoring"
    if role in REGION_ONLY_ROLES:
        return "region_only", f"{role} should remain a region by default"
    return "region_only", "unrecognized or static role stays region-only"


def _body_deformation_requested(controls: dict) -> bool:
    for field in ("bounce_strength", "motion_strength"):
        value = controls.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) > 1.0:
            return True
    return bool(controls.get("mesh_deformation_requested"))


def _alpha_metrics(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {"image_size": None, "visible_bbox": None, "alpha_coverage": 0.0}
    from PIL import Image

    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        bbox = alpha.getbbox()
        visible = sum(1 for value in alpha.getdata() if value > 0)
        total = rgba.size[0] * rgba.size[1]
    return {
        "image_size": list(rgba.size),
        "visible_bbox": list(bbox) if bbox else None,
        "alpha_coverage": visible / total if total else 0.0,
    }


def _auto_mesh_plan_attachment(att: dict, candidate: dict, layer_dir: Path) -> dict:
    source_layer = str(candidate.get("source_layer") or att.get("layer_name"))
    source_image = _find_source_image(layer_dir, source_layer, att)
    metrics = _alpha_metrics(source_image)
    bbox = metrics.get("visible_bbox")
    if not bbox:
        raise ValueError(f"cannot generate mesh plan for {source_layer!r}: no visible alpha hull")
    width = float(att.get("width", metrics["image_size"][0]))
    height = float(att.get("height", metrics["image_size"][1]))
    x0, y0, x1, y1 = [float(v) for v in bbox]
    left = x0 - width / 2.0
    right = x1 - width / 2.0
    top = height / 2.0 - y0
    bottom = height / 2.0 - y1
    hull = [(left, bottom), (right, bottom), (right, top), (left, top)]
    interior: list[tuple[float, float]] = []
    role = candidate.get("semantic_role")
    if role in BODY_CANDIDATE_ROLES:
        interior.append(((left + right) / 2.0, (bottom + top) / 2.0))
    vertices = hull + interior
    if interior:
        center_idx = len(vertices) - 1
        triangles = [0, 1, center_idx, 1, 2, center_idx, 2, 3, center_idx, 3, 0, center_idx]
    else:
        triangles = [0, 1, 2, 0, 2, 3]
    return {
        "reviewed": False,
        "auto_generated": True,
        "review_required": True,
        "generation_method": "alpha_bbox_hull_with_role_interiors",
        "source_layer": source_layer,
        "target_slot": candidate["target_slot"],
        "hull_vertices": [[round(x, 3), round(y, 3)] for x, y in hull],
        "interior_vertices": [[round(x, 3), round(y, 3)] for x, y in interior],
        "triangles": triangles,
        "uvs": [[round((x + width / 2.0) / width, 6), round((y + height / 2.0) / height, 6)] for x, y in vertices],
        "hull_count": len(hull),
        "max_vertex_budget": _role_vertex_budget(role),
        "edges": [[0, 1], [1, 2], [2, 3], [3, 0]],
        "allowed_bones": candidate.get("allowed_bones", []),
    }


def _role_vertex_budget(role: str | None) -> int:
    if role in BODY_CANDIDATE_ROLES:
        return 24
    if role in {"cape", "cloak", "tails", "hair"}:
        return 16
    return 12


def _endpoint_locked_vertex_count(weights: list[list[tuple[int, float]]]) -> int:
    return sum(1 for vertex_weights in weights if len(vertex_weights) == 1 and abs(vertex_weights[0][1] - 1.0) <= 0.000001)


def _find_source_image(layer_dir: Path, source_layer: str, source_att: dict) -> Path | None:
    if _unsafe_relative_path(source_layer):
        return None
    candidates = [
        layer_dir / source_layer,
        layer_dir / f"{Path(source_layer).stem}.png",
        layer_dir / str(source_att.get("layer_name", "")),
        layer_dir / f"{Path(str(source_att.get('layer_name', ''))).stem}.png",
    ]
    root = layer_dir.resolve()
    safe_candidates = [candidate for candidate in candidates if _is_under(candidate, root)]
    return next((candidate for candidate in safe_candidates if candidate.is_file()), None)


def _point_list(value: Any, field: str, issues: list[str]) -> list[tuple[float, float]]:
    if not isinstance(value, list):
        issues.append(f"{field} must be a list of [x, y] pairs")
        return []
    out: list[tuple[float, float]] = []
    for idx, point in enumerate(value):
        if (
            not isinstance(point, list)
            or len(point) != 2
            or not all(_is_number(v) for v in point)
        ):
            issues.append(f"{field}[{idx}] must be an [x, y] numeric pair")
            continue
        out.append((float(point[0]), float(point[1])))
    return out


def _int_list(value: Any, field: str, issues: list[str]) -> list[int]:
    if not isinstance(value, list):
        issues.append(f"{field} must be a flat integer list")
        return []
    out: list[int] = []
    for idx, item in enumerate(value):
        if not _is_int(item):
            issues.append(f"{field}[{idx}] must be an integer")
            continue
        out.append(item)
    return out


def _edges(value: Any, field: str, issues: list[str]) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        issues.append(f"{field} must be a flat integer list or list of index pairs")
        return []
    if all(_is_int(item) for item in value):
        if len(value) % 2 != 0:
            issues.append(f"{field} length must be even")
        return [int(item) for item in value]
    out: list[int] = []
    for idx, pair in enumerate(value):
        if not isinstance(pair, list) or len(pair) != 2 or not all(_is_int(item) for item in pair):
            issues.append(f"{field}[{idx}] must be an integer index pair")
            continue
        out.extend([int(pair[0]), int(pair[1])])
    return out


def _flat_len(value: Any) -> int:
    if not isinstance(value, list):
        return 0
    total = 0
    for item in value:
        if isinstance(item, list):
            total += len(item)
        else:
            total += 1
    return total


def _flatten_points(points: list[tuple[float, float]]) -> list[float]:
    return [coord for point in points for coord in point]


def _self_intersects(points: list[tuple[float, float]]) -> bool:
    if len(points) < 3:
        return False
    seen: dict[tuple[float, float], int] = {}
    for idx, point in enumerate(points):
        if point in seen and idx - seen[point] > 1:
            return True
        seen[point] = idx
    edges = list(zip(points, points[1:] + points[:1]))
    if points[0] == points[-1]:
        return True
    for a1, a2 in edges:
        if a1 == a2:
            return True
    for i, (a1, a2) in enumerate(edges):
        for j, (b1, b2) in enumerate(edges):
            if abs(i - j) <= 1 or {i, j} == {0, len(edges) - 1}:
                continue
            if _segments_intersect(a1, a2, b1, b2):
                return True
    return False


def _segments_intersect(
    a1: tuple[float, float],
    a2: tuple[float, float],
    b1: tuple[float, float],
    b2: tuple[float, float],
) -> bool:
    def orient(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    o1 = orient(a1, a2, b1)
    o2 = orient(a1, a2, b2)
    o3 = orient(b1, b2, a1)
    o4 = orient(b1, b2, a2)
    if o1 == 0 and _on_segment(a1, b1, a2):
        return True
    if o2 == 0 and _on_segment(a1, b2, a2):
        return True
    if o3 == 0 and _on_segment(b1, a1, b2):
        return True
    if o4 == 0 and _on_segment(b1, a2, b2):
        return True
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


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


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _unsafe_relative_path(value: str) -> bool:
    path = Path(value)
    return path.is_absolute() or any(part == ".." for part in path.parts)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def _on_segment(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> bool:
    return (
        min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
        and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
    )


def _degenerate_triangle(vertices: list[tuple[float, float]], triangle: list[int]) -> bool:
    if len(set(triangle)) < 3:
        return True
    try:
        a, b, c = (vertices[idx] for idx in triangle)
    except IndexError:
        return False
    return _triangle_area2(a, b, c) == 0


def _triangle_area2(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
