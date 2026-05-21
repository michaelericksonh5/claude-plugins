#!/usr/bin/env python3
"""Compare a candidate weighted mesh against a Chris-approved Spine export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path

SCHEMA = "spine_slot_animation_mesh_weight_parity_report_v1"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _default_attachments(skel: dict[str, Any]) -> dict[str, dict[str, Any]]:
    skins = skel.get("skins") or []
    if not skins:
        return {}
    for skin in skins:
        if isinstance(skin, dict) and skin.get("name") == "default":
            return skin.get("attachments") or {}
    first = skins[0]
    return first.get("attachments") if isinstance(first, dict) else {}


def _mesh_attachments(skel: dict[str, Any]) -> dict[str, dict[str, Any]]:
    meshes: dict[str, dict[str, Any]] = {}
    for slot, attachments in _default_attachments(skel).items():
        if not isinstance(attachments, dict):
            continue
        for name, attachment in attachments.items():
            if isinstance(attachment, dict) and attachment.get("type") == "mesh":
                meshes[f"{slot}/{name}"] = attachment
    return meshes


def _parse_weighted_vertices(mesh: dict[str, Any]) -> list[list[tuple[int, float]]]:
    uvs = mesh.get("uvs") or []
    vertices = mesh.get("vertices") or []
    vertex_count = len(uvs) // 2
    if len(vertices) <= len(uvs):
        return []
    parsed: list[list[tuple[int, float]]] = []
    index = 0
    for _ in range(vertex_count):
        if index >= len(vertices):
            raise ValueError("weighted vertices ended before all UV vertices were parsed")
        influence_count = int(vertices[index])
        index += 1
        influences: list[tuple[int, float]] = []
        for _ in range(influence_count):
            if index + 3 >= len(vertices):
                raise ValueError("weighted vertex influence block is truncated")
            bone_index = int(vertices[index])
            weight = float(vertices[index + 3])
            influences.append((bone_index, weight))
            index += 4
        parsed.append(influences)
    return parsed


def _weight_errors(approved: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    approved_weights = _parse_weighted_vertices(approved)
    candidate_weights = _parse_weighted_vertices(candidate)
    max_sum_error = 0.0
    max_bones_per_vertex = 0
    for influences in candidate_weights:
        max_bones_per_vertex = max(max_bones_per_vertex, len(influences))
        max_sum_error = max(max_sum_error, abs(1.0 - sum(weight for _, weight in influences)))
    return {
        "approved_weighted": bool(approved_weights),
        "candidate_weighted": bool(candidate_weights),
        "max_weight_sum_error": round(max_sum_error, 6),
        "max_bones_per_vertex": max_bones_per_vertex,
    }


def compare(approved: dict[str, Any], candidate: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    approved_meshes = _mesh_attachments(approved)
    candidate_meshes = _mesh_attachments(candidate)
    errors: list[str] = []
    comparisons: list[dict[str, Any]] = []

    for key, approved_mesh in sorted(approved_meshes.items()):
        candidate_mesh = candidate_meshes.get(key)
        if candidate_mesh is None:
            errors.append(f"missing candidate mesh: {key}")
            continue
        approved_vertex_count = len(approved_mesh.get("uvs", [])) // 2
        candidate_vertex_count = len(candidate_mesh.get("uvs", [])) // 2
        approved_triangle_count = len(approved_mesh.get("triangles", [])) // 3
        candidate_triangle_count = len(candidate_mesh.get("triangles", [])) // 3
        weights = _weight_errors(approved_mesh, candidate_mesh)
        comparison = {
            "mesh": key,
            "approved_vertex_count": approved_vertex_count,
            "candidate_vertex_count": candidate_vertex_count,
            "approved_triangle_count": approved_triangle_count,
            "candidate_triangle_count": candidate_triangle_count,
            **weights,
        }
        comparisons.append(comparison)
        if thresholds.get("require_exact_vertex_count", True) and approved_vertex_count != candidate_vertex_count:
            errors.append(f"{key}: vertex count mismatch")
        if thresholds.get("require_exact_triangle_count", True) and approved_triangle_count != candidate_triangle_count:
            errors.append(f"{key}: triangle count mismatch")
        if weights["max_weight_sum_error"] > float(thresholds.get("max_weight_sum_error", 0.001)):
            errors.append(f"{key}: weight sum error exceeds threshold")
        if weights["max_bones_per_vertex"] > int(thresholds.get("max_bones_per_vertex", 4)):
            errors.append(f"{key}: bones per vertex exceeds threshold")

    for key in sorted(set(candidate_meshes) - set(approved_meshes)):
        errors.append(f"extra candidate mesh: {key}")

    return {
        "schema": SCHEMA,
        "status": "ok" if not errors else "blocked",
        "approved_mesh_count": len(approved_meshes),
        "candidate_mesh_count": len(candidate_meshes),
        "comparisons": comparisons,
        "errors": errors,
        "claim_boundary": (
            "Passing this comparator is fixture evidence only; production mesh/weight approval still needs "
            "Chris review and visual/runtime acceptance."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare candidate mesh weights to an approved Spine export.")
    parser.add_argument("--approved", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--thresholds", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    thresholds = _load_json(args.thresholds) if args.thresholds else {
        "require_exact_vertex_count": True,
        "require_exact_triangle_count": True,
        "max_weight_sum_error": 0.001,
        "max_bones_per_vertex": 4,
    }
    report = compare(_load_json(args.approved), _load_json(args.candidate), thresholds)
    out = ensure_safe_write_path(args.out, "mesh weight parity report")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
