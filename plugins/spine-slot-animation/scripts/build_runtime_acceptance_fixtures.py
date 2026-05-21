#!/usr/bin/env python3
"""Build representative preview packages for browser runtime acceptance."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path

from source_art_guard import ensure_safe_write_path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = PLUGIN_ROOT / "scripts" / "build_spine_package.py"
DEFAULT_OUTPUT_ROOT = PLUGIN_ROOT / "generated" / "runtime_acceptance"


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, color: tuple[int, int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    pixel = bytes(color)
    for _ in range(height):
        rows.append(b"\x00" + pixel * width)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def run_builder(layer_dir: Path, out_dir: Path, *extra_args: str, family: str, rank: int = 3) -> None:
    cmd = [
        sys.executable,
        str(BUILD_SCRIPT),
        "--layer-dir",
        str(layer_dir),
        "--family",
        family,
        "--rank",
        str(rank),
        "--doc-width",
        "64",
        "--doc-height",
        "64",
        "--no-context",
        "--out-dir",
        str(out_dir),
        "--build-preview",
        *extra_args,
    ]
    result = subprocess.run(cmd, cwd=PLUGIN_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"builder failed for {out_dir.name} with {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def build_advanced_hp(root: Path) -> Path:
    layer_dir = root / "inputs" / "advanced_hp_symbol"
    out_dir = root / "packages" / "advanced_hp_symbol"
    variants_dir = layer_dir / "variants"
    write_rgba_png(layer_dir / "HP3_body.png", 24, 24, (120, 80, 40, 255))
    write_rgba_png(layer_dir / "HP3_head.png", 18, 18, (230, 190, 140, 255))
    write_rgba_png(layer_dir / "HP3_hair.png", 16, 16, (40, 20, 10, 255))
    write_rgba_png(layer_dir / "HP3_glow.png", 26, 26, (255, 240, 120, 150))
    write_rgba_png(layer_dir / "HP3_head_eyes_blink.png", 18, 18, (0, 0, 0, 180))
    write_rgba_png(layer_dir / "HP3_santa_laugh.png", 18, 18, (180, 20, 20, 180))
    write_rgba_png(layer_dir / "HP3_santa_smile.png", 18, 18, (220, 80, 120, 180))
    write_rgba_png(layer_dir / "HP3_head_mouth_open.png", 18, 18, (120, 0, 0, 180))
    write_rgba_png(layer_dir / "HP3_head_mouth_closed.png", 18, 18, (70, 0, 0, 180))
    write_rgba_png(layer_dir / "HP3_head_eyes_side.png", 18, 18, (0, 40, 80, 180))
    for index, alpha in enumerate((120, 170, 220), start=1):
        write_rgba_png(layer_dir / f"HP3_sparkle_{index:03d}.png", 8, 8, (255, 255, 255, alpha))
    write_rgba_png(variants_dir / "HP3_body_gold.png", 24, 24, (240, 190, 40, 255))

    controls_path = root / "inputs" / "advanced_hp_symbol.controls.json"
    skin_plan_path = root / "inputs" / "advanced_hp_symbol.skin_plan.json"
    write_json(controls_path, {
        "export_profile": "spine_43_bezier",
        "bezier_preset": "ease_in_out",
        "bounce_strength": 1.15,
        "sparkle_intensity": 1.1,
        "premium_intensity": 1.1,
    })
    write_json(skin_plan_path, {
        "schema": "spine_slot_animation_skin_plan_v1",
        "skins": [{
            "name": "gold",
            "attachments": [{
                "layer_file": "variants/HP3_body_gold.png",
                "target_slot": "HP3_body_slot",
                "attachment_key": "parts/HP3_body",
                "attachment_name": "parts/HP3_body_gold",
                "path": "parts/HP3_body_gold",
            }],
            "bones": ["HP3_body_bone"],
        }],
    })
    run_builder(
        layer_dir,
        out_dir,
        "--enable-sequences",
        "--enable-physics",
        "--composite-expressions",
        "--skin-plan",
        str(skin_plan_path),
        "--controls",
        str(controls_path),
        family="hp_symbol",
    )
    return out_dir


def build_avatar(root: Path) -> Path:
    layer_dir = root / "inputs" / "avatar_state"
    out_dir = root / "packages" / "avatar_state"
    for name, color in (
        ("State0Idle.png", (40, 80, 140, 255)),
        ("State0to1.png", (80, 120, 180, 255)),
        ("State1Idle.png", (100, 160, 80, 255)),
        ("State1Awarded.png", (220, 190, 60, 255)),
        ("State1Close.png", (120, 90, 50, 255)),
    ):
        write_rgba_png(layer_dir / name, 16, 16, color)
    run_builder(layer_dir, out_dir, family="avatar")
    return out_dir


def build_winframe(root: Path) -> Path:
    layer_dir = root / "inputs" / "winframe_explode"
    out_dir = root / "packages" / "winframe_explode"
    write_rgba_png(layer_dir / "WinFrame_frame.png", 24, 24, (80, 60, 140, 255))
    write_rgba_png(layer_dir / "WinFrame_glow.png", 24, 24, (180, 220, 255, 180))
    run_builder(layer_dir, out_dir, family="winframe_explode")
    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Build representative packages for runtime acceptance probing.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    args = parser.parse_args()

    output_root = ensure_safe_write_path(Path(args.output_root).resolve(), "output_root")
    if not output_root.is_relative_to(PLUGIN_ROOT.resolve()):
        raise SystemExit(f"output_root must stay inside the plugin repo: {PLUGIN_ROOT}")
    output_root.mkdir(parents=True, exist_ok=True)

    packages = [
        build_advanced_hp(output_root),
        build_avatar(output_root),
        build_winframe(output_root),
    ]
    manifest = {
        "schema": "spine_slot_animation_runtime_acceptance_fixture_manifest_v1",
        "packages": [str(path) for path in packages],
    }
    write_json(output_root / "runtime_acceptance_fixtures.json", manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
