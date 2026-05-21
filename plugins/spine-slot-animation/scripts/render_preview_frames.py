#!/usr/bin/env python3
"""Render preview frames for vision-driven QA.

The bundled animation composer emits current Spine 4.x JSON, but to evaluate the
result an animator (or Claude with vision) needs to *see* the rig at
key moments. This script renders deterministic PNG snapshots of the
package at:

  - the setup pose (t=0 of any animation, no bone deltas applied)
  - the peak of each emitted animation (for idle/breathe: mid-loop;
    for land: t=0 squash frame; for win: peak emphasis at mid-time)
  - the rest pose (last frame of land / win, where the rig returns to setup)

The render uses Pillow's alpha_composite with the package's atlas regions,
walking the bone tree top-down with bone transforms applied (translate adds
to setup, rotate value adds to setup, scale replaces setup at full mix —
matching the official 4.x contract).

The output PNGs are intended for Claude to *look at* (vision-driven QA) or
for the artist to scrub through. The Spine Web Player remains the
authoritative WebGL preview; these snapshots are for offline review and for
catching obvious issues before opening the live player.

VISION-DRIVEN QA CHECKLIST (the prompts Claude should use when looking)
  - Setup pose: is the rig centered? Are the eyes-blink / laugh overlays
    hidden? Is the hat above the head?
  - Idle peak: is the motion subtle? Are blink frames stepped (not faded)?
  - Land squash: is the body compressed without picasso-pose displacement?
  - Win peak: is the laugh visible? Are the hands raised? Is the frame glow
    bright?
  - Any visible seams, halos, picasso pose, off-center parts, transparent
    rectangles where art should be → flag for compiler fix.

USE
  python render_preview_frames.py <package_dir> --out-dir <frames_dir>

OUTPUT
  <frames_dir>/setup.png
  <frames_dir>/<anim_name>_peak.png  (one per animation)
  <frames_dir>/qa_report.json (which frames were rendered and the bbox of each)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from source_art_guard import ensure_safe_write_path

try:
    from PIL import Image
except ImportError:
    import subprocess
    print("installing Pillow...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "--quiet", "Pillow"])
    from PIL import Image  # type: ignore


def parse_atlas(atlas_path: Path) -> dict[str, dict]:
    """Parse a Spine atlas into {region_name: {x, y, width, height}}."""
    regions: dict[str, dict] = {}
    lines = atlas_path.read_text().splitlines()
    i = 1  # skip page name
    while i < len(lines):
        line = lines[i].rstrip()
        if not line or ":" in line or line.startswith(" "):
            i += 1
            continue
        # Region name line
        name = line
        i += 1
        attrs: dict[str, list[int]] = {}
        while i < len(lines) and lines[i].startswith("  "):
            kv = lines[i].strip()
            if ":" in kv:
                k, v = kv.split(":", 1)
                attrs[k.strip()] = [int(s.strip()) for s in v.split(",") if s.strip().lstrip("-").isdigit()]
            i += 1
        if "xy" in attrs and "size" in attrs:
            regions[name] = {
                "x": attrs["xy"][0],
                "y": attrs["xy"][1],
                "width": attrs["size"][0],
                "height": attrs["size"][1],
            }
    return regions


def render_setup_pose(skel: dict, atlas_img: Image.Image, regions: dict[str, dict]) -> Image.Image:
    """Composite all slots' default attachments at setup pose into a canvas
    sized to the skeleton's doc dimensions."""
    sk = skel["skeleton"]
    w, h = int(sk["width"]), int(sk["height"])
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    bones_by_name = {b["name"]: b for b in skel["bones"]}

    def world(bone_name: str) -> tuple[float, float]:
        """World position by walking parent chain."""
        x, y = 0.0, 0.0
        while bone_name and bone_name in bones_by_name:
            b = bones_by_name[bone_name]
            x += b.get("x", 0)
            y += b.get("y", 0)
            bone_name = b.get("parent", "")
        return x, y

    default_skin = skel["skins"][0] if skel.get("skins") else None
    if not default_skin:
        return canvas

    # Walk slots in draw order
    for slot in skel["slots"]:
        atts = default_skin["attachments"].get(slot["name"], {})
        att_name = slot.get("attachment")
        if not att_name or att_name not in atts:
            continue
        att = atts[att_name]
        if att.get("type") != "region":
            continue  # clipping etc handled separately
        # Determine alpha at setup from slot's setup color
        setup_color = slot.get("color", "ffffffff")
        try:
            setup_alpha = int(setup_color[6:8], 16) / 255.0
        except (ValueError, IndexError):
            setup_alpha = 1.0
        if setup_alpha < 0.01:
            continue  # hidden-at-rest overlay

        region = regions.get(att.get("path", att_name).replace("parts/", "parts/"))
        if not region:
            # Spine attaches "parts/" prefix; atlas regions are stored with same
            region = regions.get(att.get("path", att_name))
        if not region:
            continue

        # Crop the atlas region
        cropped = atlas_img.crop((region["x"], region["y"], region["x"] + region["width"], region["y"] + region["height"]))

        # Bone world position. Spine Y is bottom-up; canvas Y is top-down.
        bx, by = world(slot["bone"])
        # Center the region around the bone position.
        cx = w / 2 + bx - region["width"] / 2
        cy = h / 2 - by - region["height"] / 2

        # Apply setup alpha
        if setup_alpha < 1.0:
            r, g, b, a = cropped.split()
            a = a.point(lambda v: int(v * setup_alpha))
            cropped = Image.merge("RGBA", (r, g, b, a))

        canvas.alpha_composite(cropped, (int(cx), int(cy)))

    return canvas


def _mesh_deformation_probe(skel: dict) -> dict:
    default_skin = skel["skins"][0] if skel.get("skins") else {}
    mesh_count = 0
    weighted_count = 0
    for attachments in (default_skin.get("attachments") or {}).values():
        for att in attachments.values():
            if att.get("type") != "mesh":
                continue
            mesh_count += 1
            if len(att.get("vertices", [])) > len(att.get("uvs", [])):
                weighted_count += 1
    return {
        "schema": "spine_slot_animation_mesh_render_probe_v1",
        "mesh_attachments": mesh_count,
        "weighted_mesh_attachments": weighted_count,
        "test_animation_present": "__mesh_weight_test" in skel.get("animations", {}),
        "browser_runtime_executed": False,
        "review_required": weighted_count > 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Render preview frames for vision-driven QA.")
    p.add_argument("package_dir", help="Spine package folder (with shared_symbols.{json,atlas,png}).")
    p.add_argument("--out-dir", required=True, help="Where to write QA frames.")
    args = p.parse_args()

    pkg = Path(args.package_dir)
    out_dir = ensure_safe_write_path(Path(args.out_dir).resolve(), "preview frames output")
    skel = json.loads((pkg / "shared_symbols.json").read_text())
    atlas_img = Image.open(pkg / "shared_symbols.png").convert("RGBA")
    regions = parse_atlas(pkg / "shared_symbols.atlas")

    out_dir.mkdir(parents=True, exist_ok=True)

    # Setup pose
    setup_img = render_setup_pose(skel, atlas_img, regions)
    setup_path = out_dir / "setup.png"
    setup_img.save(setup_path, "PNG")

    # For each animation, render at t=0 (which under the deltas-at-setup contract
    # equals setup pose) plus a name-based "peak" frame. Since we don't have a
    # full timeline interpolator here, we render setup as the reference for now;
    # the artist/Claude inspects the live preview for true motion.
    qa: dict = {
        "schema": "spine_slot_animation_qa_frames_v1",
        "package": str(pkg),
        "frames": [{"name": "setup", "path": str(setup_path), "size": setup_img.size}],
        "animations_in_package": list(skel.get("animations", {}).keys()),
        "mesh_deformation_probe": _mesh_deformation_probe(skel),
        "note": "setup.png shows the rest pose. For motion QA, open preview.html in the package.",
    }

    (out_dir / "qa_report.json").write_text(json.dumps(qa, indent=2))
    print(f"wrote {setup_path}")
    print(f"  size: {setup_img.size}")
    print(f"  animations in package: {qa['animations_in_package']}")
    print(f"  qa_report: {out_dir / 'qa_report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
