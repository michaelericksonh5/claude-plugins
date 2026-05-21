#!/usr/bin/env python3
"""Portable Spine atlas packer.

Reads per-layer PNG files and packs them into a single straight-alpha atlas
page with the texture-quality steps the WebGL Spine runtime needs:

  - alpha-trim each cropped layer to its tight visible bounding box (we record
    the trim offset so the assembler can place the bone correctly)
  - RGB-bleed transparent pixels inside each cropped image so the WebGL
    bilinear filter doesn't sample garbage RGB at the visible-pixel boundary
  - 1-px edge extrusion in the atlas page so bilinear sampling at the region
    edge doesn't blend with neighbouring transparent atlas pixels
  - emit Linear,Linear filter and pma:false (straight alpha)

USE
  python build_atlas.py --layer-dir <path> --layout <rig_layout.json> \
      --out-png shared_symbols.png --out-atlas shared_symbols.atlas

Skip layers whose layout entry is missing (filtered).

REQUIRES
  Pillow. The script tries to install it via `pip install --break-system-packages
  Pillow` if missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path

try:
    from PIL import Image
except ImportError:
    import subprocess
    print("installing Pillow...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "--quiet", "Pillow"])
    from PIL import Image  # type: ignore


def alpha_trim(img: Image.Image) -> tuple[Image.Image, tuple[int, int]]:
    """Crop to the visible alpha bounding box. Returns (cropped, (offset_x, offset_y))
    where offset is the trim from the original top-left."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    bbox = img.getbbox()
    if bbox is None:
        return img.copy(), (0, 0)
    cropped = img.crop(bbox)
    return cropped, (bbox[0], bbox[1])


def rgb_bleed(img: Image.Image, iterations: int = 4) -> Image.Image:
    """Replace RGB of transparent pixels with the average RGB of nearby visible
    pixels. Alpha stays at 0. Repeat several times so RGB bleeds outward into
    the transparent margin."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for _ in range(iterations):
        new_px = []
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a > 0:
                    new_px.append((r, g, b, a))
                    continue
                # 3x3 neighbourhood average of visible pixels
                ar = ag = ab = 0
                n = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            nr, ng, nb, na = px[nx, ny]
                            if na > 0:
                                ar += nr
                                ag += ng
                                ab += nb
                                n += 1
                if n > 0:
                    new_px.append((ar // n, ag // n, ab // n, 0))
                else:
                    new_px.append((r, g, b, 0))
        img.putdata(new_px)
        px = img.load()
    return img


def extrude_edges(atlas: Image.Image, x: int, y: int, region: Image.Image) -> None:
    """Duplicate the region's outer-edge pixel row/column into the 1-px padding
    around it in the atlas page."""
    w, h = region.size
    # left col
    if x > 0:
        atlas.paste(region.crop((0, 0, 1, h)), (x - 1, y))
    # right col
    atlas.paste(region.crop((w - 1, 0, w, h)), (x + w, y))
    # top row
    if y > 0:
        atlas.paste(region.crop((0, 0, w, 1)), (x, y - 1))
    # bottom row
    atlas.paste(region.crop((0, h - 1, w, h)), (x, y + h))
    # corners
    px = region.load()
    apx = atlas.load()
    if x > 0 and y > 0:
        apx[x - 1, y - 1] = px[0, 0]
    if y > 0:
        apx[x + w, y - 1] = px[w - 1, 0]
    if x > 0:
        apx[x - 1, y + h] = px[0, h - 1]
    apx[x + w, y + h] = px[w - 1, h - 1]


def pack_atlas(
    regions: list[tuple[str, Image.Image, tuple[int, int]]],
    page_name: str = "shared_symbols.png",
    padding: int = 2,
) -> tuple[Image.Image, list[dict], tuple[int, int]]:
    """Simple row packer: stack regions vertically, padding on all sides.

    Returns (atlas_image, region_records, (atlas_w, atlas_h)).
    """
    # Width of atlas = max region width + 2*padding
    if not regions:
        return Image.new("RGBA", (1, 1)), [], (1, 1)
    max_w = max(r[1].size[0] for r in regions) + 2 * padding
    total_h = sum(r[1].size[1] + 2 * padding for r in regions)
    atlas = Image.new("RGBA", (max_w, total_h), (0, 0, 0, 0))

    records: list[dict] = []
    cur_y = padding
    for name, region_img, trim_offset in regions:
        rw, rh = region_img.size
        rx = padding
        atlas.paste(region_img, (rx, cur_y))
        extrude_edges(atlas, rx, cur_y, region_img)
        records.append({
            "name": name,
            "x": rx,
            "y": cur_y,
            "width": rw,
            "height": rh,
            "trim_offset": trim_offset,
        })
        cur_y += rh + 2 * padding

    return atlas, records, atlas.size


def write_atlas_file(records: list[dict], atlas_size: tuple[int, int], page_name: str, out_path: Path) -> None:
    # H5G 4.2 atlas format: page name on line 0 (no leading blank), metadata
    # lines immediately after, then region entries.
    lines: list[str] = []
    lines.append(page_name)
    lines.append(f"size: {atlas_size[0]},{atlas_size[1]}")
    lines.append("format: RGBA8888")
    lines.append("filter: Linear,Linear")
    lines.append("repeat: none")
    for r in records:
        lines.append(r["name"])
        lines.append("  rotate: false")
        lines.append(f"  xy: {r['x']}, {r['y']}")
        lines.append(f"  size: {r['width']}, {r['height']}")
        lines.append(f"  orig: {r['width']}, {r['height']}")
        lines.append("  offset: 0, 0")
        lines.append("  index: -1")
    ensure_safe_write_path(out_path, "out_atlas")
    out_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Build a Spine atlas + page from per-layer PNGs and a rig_layout.")
    p.add_argument("--layer-dir", required=True, help="Folder of per-layer PNG files.")
    p.add_argument("--layout", required=True, help="Path to rig_layout.json")
    p.add_argument("--out-png", required=True, help="Output atlas PNG path.")
    p.add_argument("--out-atlas", required=True, help="Output atlas metadata path.")
    p.add_argument("--bleed-iterations", type=int, default=4, help="RGB bleed iterations (default 4).")
    args = p.parse_args()

    layer_dir = Path(args.layer_dir)
    layout = json.loads(Path(args.layout).read_text())

    # Walk the layout's attachments in order and pull each PNG from disk
    regions: list[tuple[str, Image.Image, tuple[int, int]]] = []
    for att in layout["attachments"]:
        layer_name = att["layer_name"]
        candidates = [layer_dir / f"{layer_name}.png", layer_dir / layer_name]
        png_path = next((c for c in candidates if c.exists()), None)
        if png_path is None:
            print(f"warning: PNG missing for {layer_name}; skipped", file=sys.stderr)
            continue
        img = Image.open(png_path).convert("RGBA")
        trimmed, trim_off = alpha_trim(img)
        bled = rgb_bleed(trimmed, iterations=args.bleed_iterations)
        regions.append((att["name"], bled, trim_off))

    out_png = Path(args.out_png)
    out_atlas = Path(args.out_atlas)
    ensure_safe_write_path(out_png, "out_png")
    ensure_safe_write_path(out_atlas, "out_atlas")
    atlas_img, records, atlas_size = pack_atlas(regions, page_name=out_png.name)
    atlas_img.save(out_png, "PNG")
    write_atlas_file(records, atlas_size, out_png.name, out_atlas)
    print(f"wrote {args.out_png} ({atlas_size[0]}x{atlas_size[1]}, {len(records)} regions)")
    print(f"wrote {args.out_atlas}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
