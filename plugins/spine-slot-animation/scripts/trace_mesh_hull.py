#!/usr/bin/env python3
"""Trace a mesh hull from a layer PNG's alpha channel.

This bridges the gap between "you have an art asset" and "you have mesh
vertices ready to bind to bones." It approximates Spine Editor's Trace tool,
exposing the same conceptual parameters: alpha threshold, detail (vertex
count target), padding, and concavity preference.

ALGORITHM
  1. Read the PNG's alpha channel.
  2. Threshold to a binary mask at the given alpha cutoff.
  3. Extract the outer contour (the visible hull) — discards interior holes
     since Spine meshes cannot have holes.
  4. Simplify the contour with Douglas-Peucker (cv2.approxPolyDP) to the
     requested vertex count.
  5. Optionally expand the hull outward by `padding` pixels so the mesh
     doesn't clip the visible art.
  6. Convert from doc-relative pixel coords to mesh-attachment-local coords
     (relative to layer's visual center).

The Spine team's blog "Mesh creation tips: vertex placement" emphasizes:
  - "start with the least number of vertices possible"
  - "follow natural folds and edges"
  - "symmetrical vertex placement helps believable deformation"

This tracer hits the first two. Symmetric distribution is a placement choice
for interior vertices; this script only places the hull. Interior vertex
placement is in scripts/place_mesh_features.py.

USE
  python trace_mesh_hull.py <layer.png> \
      --target-vertices 12 --padding 1 --alpha-threshold 20 \
      --out hull.json

OUTPUT
  {
    "schema": "spine_slot_animation_mesh_hull_v1",
    "source_png": "<path>",
    "vertex_count": 12,
    "vertices_pixel_doc": [[x0,y0], ...],     # doc-relative pixel coords
    "vertices_mesh_local": [x0, y0, x1, y1, ...],  # flat, mesh-local
    "image_size": [width, height],
    "hull_bbox": {"x": 0, "y": 0, "width": 0, "height": 0}
  }
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from source_art_guard import ensure_safe_write_path

try:
    import cv2
    import numpy as np
except ImportError:
    import subprocess
    print("installing numpy + opencv-python...", file=sys.stderr)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--break-system-packages", "--quiet",
        "numpy", "opencv-python-headless",
    ])
    import cv2  # type: ignore
    import numpy as np  # type: ignore


def trace_hull(
    png_path: Path,
    target_vertices: int = 12,
    padding: int = 1,
    alpha_threshold: int = 20,
) -> dict:
    """Trace the mesh hull and return the vertex spec."""
    img = cv2.imread(str(png_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit(f"cannot read PNG: {png_path}")
    if img.shape[2] != 4:
        raise SystemExit(f"PNG must have alpha channel: {png_path}")
    h, w = img.shape[:2]
    alpha = img[:, :, 3]

    # Binary mask of visible pixels
    _, mask = cv2.threshold(alpha, alpha_threshold, 255, cv2.THRESH_BINARY)

    # Optional padding: dilate the mask to expand hull by `padding` pixels
    if padding > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * padding + 1, 2 * padding + 1))
        mask = cv2.dilate(mask, kernel)

    # Find outer contours (RETR_EXTERNAL — discard interior holes)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise SystemExit(f"no visible pixels above alpha threshold in {png_path}")
    # Pick the largest contour by area (handles multiple disconnected blobs by keeping the main one)
    contour = max(contours, key=cv2.contourArea)

    # Douglas-Peucker simplification — tune epsilon to hit target_vertices
    # Binary search on epsilon
    perimeter = cv2.arcLength(contour, True)
    lo, hi = 0.0001 * perimeter, 0.1 * perimeter
    best = contour
    for _ in range(20):
        mid = (lo + hi) / 2.0
        approx = cv2.approxPolyDP(contour, mid, True)
        n = len(approx)
        if abs(n - target_vertices) < abs(len(best) - target_vertices):
            best = approx
        if n > target_vertices:
            lo = mid
        elif n < target_vertices:
            hi = mid
        else:
            best = approx
            break

    # Doc-relative pixel coordinates
    pts_doc = [(int(p[0][0]), int(p[0][1])) for p in best]

    # Convert to mesh-local: relative to the layer's visual center
    # bbox of the contour determines the visual center
    xs = [p[0] for p in pts_doc]
    ys = [p[1] for p in pts_doc]
    bbox_x, bbox_y = min(xs), min(ys)
    bbox_w, bbox_h = max(xs) - bbox_x, max(ys) - bbox_y
    cx, cy = bbox_x + bbox_w / 2.0, bbox_y + bbox_h / 2.0
    # Mesh-local coords with Y flipped from PSD top-left to Spine bottom-up
    mesh_local: list[float] = []
    for px, py in pts_doc:
        mesh_local.extend([float(px) - cx, cy - float(py)])

    return {
        "schema": "spine_slot_animation_mesh_hull_v1",
        "source_png": str(png_path),
        "vertex_count": len(pts_doc),
        "vertices_pixel_doc": pts_doc,
        "vertices_mesh_local": mesh_local,
        "image_size": [w, h],
        "hull_bbox": {"x": bbox_x, "y": bbox_y, "width": bbox_w, "height": bbox_h},
        "params": {
            "target_vertices": target_vertices,
            "padding": padding,
            "alpha_threshold": alpha_threshold,
        },
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Trace mesh hull from a PNG's alpha channel.")
    p.add_argument("png", help="Path to the PNG layer.")
    p.add_argument("--target-vertices", type=int, default=12,
                   help="Approximate target vertex count (default 12). Fewer = simpler mesh.")
    p.add_argument("--padding", type=int, default=1,
                   help="Pixels to expand the hull outward (default 1).")
    p.add_argument("--alpha-threshold", type=int, default=20,
                   help="Alpha cutoff for visible pixels (0-255, default 20).")
    p.add_argument("--out", required=True, help="Path to write hull JSON.")
    args = p.parse_args()

    out_path = ensure_safe_write_path(Path(args.out).resolve(), "mesh hull output")
    spec = trace_hull(Path(args.png), args.target_vertices, args.padding, args.alpha_threshold)
    out_path.write_text(json.dumps(spec, indent=2))
    print(f"wrote {args.out}")
    print(f"  vertices: {spec['vertex_count']} (target {args.target_vertices})")
    print(f"  bbox: {spec['hull_bbox']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
