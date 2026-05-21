#!/usr/bin/env python3
"""Pre-composite expression-overlay heads into full-face attachments.

This is the "deferred clean fix" from references/pitfalls.md for the overlay
alpha-matte seam. Instead of layering hidden-at-rest overlays on top of a
base head at runtime (which produces visible WebGL boundaries against the
hard alpha mattes), we pre-bake each expression into a full-canvas head:

  head_neutral      = head.png                      (always available)
  head_with_blink   = head.png + eyes_blink overlay  (composited)
  head_with_laugh   = head.png + laugh overlay       (composited)
  head_with_hat     = head.png + hat overlay         (composited, optional)

The compose_animations.py then targets the HEAD slot's attachment timeline
instead of toggling overlay-slot alphas. At runtime WebGL renders one image
per frame; no live overlay compositing means no overlay edge to seam.

COST
  ~3x head pixel data in the atlas (4 pre-baked heads instead of 1 head +
  3 overlay slots). The benefit: visually clean WebGL rendering at native
  device pixel ratio.

USE
  python composite_expression_heads.py \
      --head HP3_head.png \
      --overlay eyes_blink=HP3_head_eyes_blink.png \
      --overlay laugh=HP3_santa_laugh.png \
      --out-dir composited/

OUTPUT
  composited/HP3_head_neutral.png   (the head as-is)
  composited/HP3_head_blink.png     (head + eyes_blink composited)
  composited/HP3_head_laugh.png     (head + laugh composited)
  composited/composite_manifest.json (records which overlays produced which)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    import subprocess
    print("installing Pillow...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "--quiet", "Pillow"])
    from PIL import Image  # type: ignore


def composite_head_with_overlay(head: Image.Image, overlay: Image.Image) -> Image.Image:
    """Composite an overlay on top of the head using standard alpha-over."""
    if head.size != overlay.size:
        raise ValueError(
            f"expression overlay canvas {overlay.size} does not match head canvas {head.size}; "
            "full-canvas aligned overlays are required without placement metadata"
        )
    if head.mode != "RGBA":
        head = head.convert("RGBA")
    if overlay.mode != "RGBA":
        overlay = overlay.convert("RGBA")
    result = head.copy()
    result.alpha_composite(overlay)
    return result


def _overlay_paths(value: Path | list[Path]) -> list[Path]:
    if isinstance(value, list):
        return value
    return [value]


def composite_expressions(
    head_png: Path,
    overlays: dict[str, Path | list[Path]],
    out_dir: Path,
    prefix: str | None = None,
) -> dict:
    """Composite each overlay onto the head and write the results."""
    out_dir.mkdir(parents=True, exist_ok=True)
    head = Image.open(head_png).convert("RGBA")
    head_base = head_png.stem
    if prefix is None:
        prefix = head_base

    # Always write the neutral head so the animation has a base attachment.
    neutral_path = out_dir / f"{prefix}_neutral.png"
    head.save(neutral_path, "PNG")

    manifest: dict = {
        "schema": "spine_slot_animation_expression_composite_v1",
        "head_source": str(head_png),
        "out_dir": str(out_dir),
        "attachments": {
            "neutral": {
                "source_overlay": None,
                "source_overlays": [],
                "file": str(neutral_path),
                "head_slot_attachment_name": f"parts/{prefix}_neutral",
            }
        },
    }

    for expression, overlay_value in overlays.items():
        overlay_paths = _overlay_paths(overlay_value)
        composited = head
        for overlay_path in overlay_paths:
            overlay = Image.open(overlay_path).convert("RGBA")
            composited = composite_head_with_overlay(composited, overlay)
        out_path = out_dir / f"{prefix}_{expression}.png"
        composited.save(out_path, "PNG")
        manifest["attachments"][expression] = {
            "source_overlay": str(overlay_paths[0]) if len(overlay_paths) == 1 else None,
            "source_overlays": [str(path) for path in overlay_paths],
            "file": str(out_path),
            "head_slot_attachment_name": f"parts/{prefix}_{expression}",
        }

    manifest_path = out_dir / "composite_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    p = argparse.ArgumentParser(description="Pre-composite expression overlays onto a head image.")
    p.add_argument("--head", required=True, help="Path to the base head PNG.")
    p.add_argument("--overlay", action="append", default=[],
                   help="<expression_name>=<path_to_overlay.png>. May be repeated.")
    p.add_argument("--prefix", help="Output filename prefix (defaults to head stem).")
    p.add_argument("--out-dir", required=True, help="Folder for composited PNGs.")
    args = p.parse_args()

    overlays: dict[str, list[Path]] = {}
    for spec in args.overlay:
        if "=" not in spec:
            raise SystemExit(f"--overlay expects expression=path, got {spec!r}")
        name, path_str = spec.split("=", 1)
        overlays.setdefault(name, []).append(Path(path_str))

    manifest = composite_expressions(Path(args.head), overlays, Path(args.out_dir), args.prefix)
    print(f"wrote {len(manifest['attachments'])} composited heads to {args.out_dir}")
    for exp, info in manifest["attachments"].items():
        print(f"  {exp:12s} → {info['file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
