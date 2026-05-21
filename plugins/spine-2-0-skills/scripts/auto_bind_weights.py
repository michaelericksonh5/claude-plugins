#!/usr/bin/env python3
"""First-pass topology-aware weight binding for a mesh.

This is not Spine Editor Auto parity. The official Spine docs describe their
algorithm as using "mesh topography" rather than naive distance. The Spine
team's blogs ("Mesh weight workflows", "Mesh creation tips") describe the
conceptual workflow:

  - "start by assigning a value of 100% to the vertices that are on the
    extreme opposite ends of the movement the mesh needs to make"
  - "work on getting the vertices in between to balance the mix of weights"
  - "Spine will automatically calculate the weights for you based on the
    surrounding vertices"
  - "Prune removes weights below a threshold... cap maximum bones per vertex"
  - "Smooth averages the weights of the selected vertices with their neighbors"

This portable implementation uses:

  1. INVERSE-DISTANCE + AXIS PROJECTION: combine local distance with a
     bone-axis projection when at least two distinct bones are available.
  2. ENDPOINT LOCKS: vertices beyond the first/last projected bone endpoint
     stay fully bound to the endpoint bone.
  3. SMOOTH: average each vertex's weights with its triangle neighbors,
     repeated `--smooth-iterations` times.
  4. PRUNE: cap to top-N bones (default 2), zero out below-threshold weights.
  5. NORMALIZE: weights for each vertex sum to 1.0.

For most slot-symbol meshes (bodies, arms, sleeves, banners), this produces
believable deformation without manual tuning. Animators can refine afterward.

INPUT
  Mesh JSON: {"vertices": [[x0,y0], ...], "triangles": [...]}
  Bones JSON: [{"name": "...", "x": ..., "y": ...}, ...] (positions in mesh-local coords)

OUTPUT
  Weighted vertices in Spine's binary-vertex format:
    [num_bones, bone_idx, bind_x, bind_y, weight, ...] per vertex,
  concatenated into a flat list. Spine's runtime auto-detects this format
  because vertices.length > 2 * uv_count.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from source_art_guard import ensure_safe_write_path


def _euclidean(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def auto_bind_weights(
    vertices: list[tuple[float, float]],
    bones: list[dict],
    max_bones_per_vertex: int = 2,
    weight_threshold: float = 0.05,
    smooth_iterations: int = 2,
    triangles: list[int] | None = None,
) -> list[list[tuple[int, float]]]:
    """Compute per-vertex (bone_idx, weight) lists.

    Returns: a list of length len(vertices), each entry is a list of
    (bone_idx, weight) tuples summing to 1.0 with at most max_bones_per_vertex.
    """
    n = len(vertices)
    m = len(bones)
    bone_pos = [(b["x"], b["y"]) for b in bones]

    # 1. Inverse-distance weights to every bone
    raw = [[0.0] * m for _ in range(n)]
    for i, v in enumerate(vertices):
        for j, bp in enumerate(bone_pos):
            d = _euclidean(v, bp)
            raw[i][j] = 1.0 / (d + 1e-3)

    # 2. Normalize so each vertex's weights sum to 1
    def _normalize_row(row):
        s = sum(row)
        if s <= 0:
            return [1.0 / m] * m
        return [x / s for x in row]

    raw = [_normalize_row(r) for r in raw]
    projection, endpoint_locks = _projection_weights(vertices, bone_pos)
    if projection is not None:
        for i in range(n):
            if endpoint_locks[i]:
                raw[i] = projection[i]
            else:
                raw[i] = _normalize_row([
                    (raw[i][j] * 0.45) + (projection[i][j] * 0.55)
                    for j in range(m)
                ])

    # 3. Smooth — average with triangle neighbors while preserving endpoint locks.
    if triangles and smooth_iterations > 0:
        adj: list[set] = [set() for _ in range(n)]
        for t in range(0, len(triangles), 3):
            a, b, c = triangles[t], triangles[t + 1], triangles[t + 2]
            adj[a].update([b, c])
            adj[b].update([a, c])
            adj[c].update([a, b])
        for _ in range(smooth_iterations):
            new_raw = [list(r) for r in raw]
            for i in range(n):
                if not adj[i] or endpoint_locks[i]:
                    continue
                for j in range(m):
                    neighbour_sum = sum(raw[k][j] for k in adj[i])
                    new_raw[i][j] = (raw[i][j] + neighbour_sum / len(adj[i])) / 2.0
            raw = [_normalize_row(r) for r in new_raw]

    # 4. Prune to top-N bones per vertex, threshold low weights, renormalize
    out: list[list[tuple[int, float]]] = []
    for r in raw:
        idxs = sorted(range(m), key=lambda j: -r[j])[:max_bones_per_vertex]
        weights = [(j, r[j]) for j in idxs if r[j] >= weight_threshold]
        if not weights:
            # Force at least one bone (the strongest) so vertex isn't unbound
            j = idxs[0]
            weights = [(j, 1.0)]
        s = sum(w for _, w in weights)
        weights = [(j, w / s) for j, w in weights]
        out.append(weights)
    return out


def _projection_weights(
    vertices: list[tuple[float, float]],
    bone_pos: list[tuple[float, float]],
) -> tuple[list[list[float]], list[bool]] | tuple[None, list[bool]]:
    if len(bone_pos) < 2:
        return None, [False] * len(vertices)
    first = bone_pos[0]
    last = bone_pos[-1]
    axis_x = last[0] - first[0]
    axis_y = last[1] - first[1]
    axis_len2 = axis_x * axis_x + axis_y * axis_y
    if axis_len2 <= 1e-6:
        return None, [False] * len(vertices)

    projected_bones = [
        ((bp[0] - first[0]) * axis_x + (bp[1] - first[1]) * axis_y) / axis_len2
        for bp in bone_pos
    ]
    ordered = sorted((t, idx) for idx, t in enumerate(projected_bones))
    rows: list[list[float]] = []
    locks: list[bool] = []
    for vertex in vertices:
        t = ((vertex[0] - first[0]) * axis_x + (vertex[1] - first[1]) * axis_y) / axis_len2
        row = [0.0] * len(bone_pos)
        if t <= ordered[0][0]:
            row[ordered[0][1]] = 1.0
            rows.append(row)
            locks.append(True)
            continue
        if t >= ordered[-1][0]:
            row[ordered[-1][1]] = 1.0
            rows.append(row)
            locks.append(True)
            continue

        for (left_t, left_idx), (right_t, right_idx) in zip(ordered, ordered[1:]):
            if left_t <= t <= right_t:
                span = right_t - left_t
                if span <= 1e-6:
                    row[left_idx] = 0.5
                    row[right_idx] = 0.5
                else:
                    mix = (t - left_t) / span
                    row[left_idx] = 1.0 - mix
                    row[right_idx] = mix
                break
        rows.append(row)
        locks.append(False)
    return rows, locks


def weights_to_spine_vertices(
    vertices: list[tuple[float, float]],
    weights: list[list[tuple[int, float]]],
    bones: list[dict],
) -> list[float]:
    """Convert to Spine's flat weighted-vertex array:
      [count, bone_idx, bind_x, bind_y, weight, ...] per vertex, all concatenated.
    """
    flat: list[float] = []
    for v, w in zip(vertices, weights):
        flat.append(len(w))
        for bone_idx, weight in w:
            # Bind position is the vertex position in the bone's local coords.
            # For a single-bone-per-vertex case this would be vertex - bone_origin,
            # but Spine accepts world-space coords and transforms internally; we
            # pass the vertex position directly.
            bx = v[0] - bones[bone_idx]["x"]
            by = v[1] - bones[bone_idx]["y"]
            flat.extend([bone_idx, bx, by, weight])
    return flat


def main() -> int:
    p = argparse.ArgumentParser(description="Auto-bind mesh weights to bones.")
    p.add_argument("--mesh", required=True, help="Mesh JSON with vertices[, triangles].")
    p.add_argument("--bones", required=True, help="JSON array of {name,x,y} bone positions.")
    p.add_argument("--out", required=True, help="Where to write the weighted-vertices JSON.")
    p.add_argument("--max-bones-per-vertex", type=int, default=2)
    p.add_argument("--weight-threshold", type=float, default=0.05)
    p.add_argument("--smooth-iterations", type=int, default=2)
    args = p.parse_args()
    out_path = ensure_safe_write_path(Path(args.out).resolve(), "weighted vertices output")

    mesh = json.loads(Path(args.mesh).read_text())
    bones = json.loads(Path(args.bones).read_text())
    verts = [tuple(v) for v in mesh["vertices"]]
    tris = mesh.get("triangles")

    weights = auto_bind_weights(
        verts, bones,
        max_bones_per_vertex=args.max_bones_per_vertex,
        weight_threshold=args.weight_threshold,
        smooth_iterations=args.smooth_iterations,
        triangles=tris,
    )
    flat = weights_to_spine_vertices(verts, weights, bones)

    out = {
        "schema": "spine_slot_animation_weighted_vertices_v1",
        "vertex_count": len(verts),
        "bone_count": len(bones),
        "max_bones_per_vertex": args.max_bones_per_vertex,
        "vertices_weighted": flat,
        "per_vertex_summary": [
            {"v": i, "bones": [{"idx": j, "w": round(w, 3)} for j, w in weights[i]]}
            for i in range(len(verts))
        ],
    }
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {args.out}")
    print(f"  vertices={len(verts)} bones={len(bones)} max_per_vertex={args.max_bones_per_vertex}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
