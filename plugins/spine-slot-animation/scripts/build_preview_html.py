#!/usr/bin/env python3
"""Generate a preview.html that loads the package via the Spine Web Player.

The configured Spine Web Player is the authoritative WebGL preview for generated packages. This script emits a
self-contained HTML file that:

  - Loads the configured @esotericsoftware/spine-player from CDN.
  - Embeds shared_symbols.json / shared_symbols.atlas / shared_symbols.png
    as Spine Player rawDataURIs so double-click file:// review can work.
  - Enables Spine Player controls and configures the initial animation and
    available skin names for preview.
  - Renders with `premultipliedAlpha: false` (straight alpha — matches
    the H5G atlas contract).

USE
  python build_preview_html.py <package_dir>

After running, open <package_dir>/preview.html in a browser. If the browser
blocks loading the Spine Player script from the CDN, serve the folder:

  python -m http.server 8000 --directory <package_dir>

Then open http://localhost:8000/preview.html.

OUTPUT
  <package_dir>/preview.html

The HTML embeds the package data, but still loads Spine Player from
the CDN. Refresh the page after each rebuild to see new motion.
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import spine_version_policy as spine_versions

SPINE_PLAYER_VERSION = spine_versions.DEFAULT_SPINE_PLAYER_VERSION
SPINE_PLAYER_JS_CDN = f"https://unpkg.com/@esotericsoftware/spine-player@{SPINE_PLAYER_VERSION}/dist/iife/spine-player.js"
SPINE_PLAYER_CSS_CDN = f"https://unpkg.com/@esotericsoftware/spine-player@{SPINE_PLAYER_VERSION}/dist/spine-player.css"
JSON_NAME = "shared_symbols.json"
ATLAS_NAME = "shared_symbols.atlas"
PNG_NAME = "shared_symbols.png"


class PreviewBuildError(ValueError):
    """Raised when a preview cannot be built from a complete package."""


def _file_as_data_uri(path: Path, mime: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _atlas_page_name(atlas_path: Path) -> str:
    for line in atlas_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    raise PreviewBuildError(f"atlas is empty: {atlas_path}")


def _raw_data_uris(package_dir: Path) -> dict[str, str]:
    json_path = package_dir / JSON_NAME
    atlas_path = package_dir / ATLAS_NAME
    for path in (json_path, atlas_path):
        if not path.is_file():
            raise PreviewBuildError(f"missing required preview file: {path}")
    atlas_page = _atlas_page_name(atlas_path)
    png_path = package_dir / atlas_page
    if not png_path.is_file():
        raise PreviewBuildError(
            f"atlas page {atlas_page!r} is missing next to {atlas_path.name}; "
            "Spine Editor import and preview require the PNG beside the atlas."
        )
    return {
        JSON_NAME: _file_as_data_uri(json_path, "application/json"),
        ATLAS_NAME: _file_as_data_uri(atlas_path, "application/octet-stream"),
        atlas_page: _file_as_data_uri(png_path, "image/png"),
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Preview — {project_title}</title>
<link rel="stylesheet" href="{spine_player_css}" />
<style>
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background: #1e1e1e; color: #ddd; }}
  header {{ padding: 12px 20px; background: #2a2a2a; border-bottom: 1px solid #333; }}
  header h1 {{ font-size: 14px; margin: 0; font-weight: 600; }}
  header .meta {{ font-size: 11px; color: #999; margin-top: 4px; }}
  #player {{ width: 100vw; height: calc(100vh - 80px); display: block; background: #111; }}
  #preview-status {{ padding: 8px 20px; background: #111827; color: #dbeafe; font-size: 12px; border-bottom: 1px solid #333; }}
  .info {{ padding: 6px 20px; background: #222; font-size: 11px; color: #888; border-top: 1px solid #333; }}
  .info a {{ color: #4a9eff; }}
  .info code {{ color: #ccc; }}
</style>
</head>
<body>
<header>
  <h1>{project_title}</h1>
  <div class="meta">Spine Web Player {player_version} · {anim_count} animations: {anim_list}</div>
  {skin_notice}
  {physics_notice}
  {expression_notice}
</header>
<div id="preview-status">Loading Spine Web Player {player_version}...</div>
<div id="player"></div>
<div class="info">
  Local preview. Reload after each rebuild. If <code>file://</code> XHR is blocked,
  run <code>python -m http.server 8000</code> in this folder and open
  <a href="http://localhost:8000/preview.html">http://localhost:8000/preview.html</a>.
</div>
<script src="{spine_player_js}"></script>
<script>
window.__h5gSpinePreviewState = {{
  status: "initializing",
  playerVersion: "{player_version}",
  constructedAt: new Date().toISOString(),
  error: null
}};
window.__h5gSpinePlayerConfig = {{
  skeleton: "shared_symbols.json",
  atlas: "shared_symbols.atlas",
  jsonUrl: "shared_symbols.json",
  atlasUrl: "shared_symbols.atlas",
  rawDataURIs: {raw_data_uris_js},
  premultipliedAlpha: false,
  alpha: true,
  backgroundColor: "#111111",
  showControls: true,
  preserveDrawingBuffer: false,
  animation: {default_anim_js},
  skin: {initial_skin_js},
  skins: {skin_list_js},
  showLoading: true,
  defaultMix: 0.2,
  success: function(player) {{
    window.__h5gSpinePlayer = player || window.__h5gSpinePlayer;
    window.__h5gSpinePreviewState.status = "loaded";
    document.getElementById("preview-status").textContent = "Spine Web Player loaded: " + window.__h5gSpinePlayerConfig.animation;
  }},
  error: function(player, reason) {{
    window.__h5gSpinePreviewState.status = "error";
    window.__h5gSpinePreviewState.error = String(reason || "unknown Spine Player error");
    document.getElementById("preview-status").textContent = "Spine Web Player error: " + window.__h5gSpinePreviewState.error;
  }}
}};
try {{
  if (!window.spine || !window.spine.SpinePlayer) {{
    throw new Error("Spine Player runtime script did not load. Check network access to the CDN or serve a cached runtime.");
  }}
  window.__h5gSpinePlayer = new spine.SpinePlayer("player", window.__h5gSpinePlayerConfig);
  if (window.__h5gSpinePreviewState.status === "initializing") {{
    window.__h5gSpinePreviewState.status = "constructed";
  }}
}} catch (error) {{
  window.__h5gSpinePreviewState.status = "error";
  window.__h5gSpinePreviewState.error = String(error && error.message ? error.message : error);
  document.getElementById("preview-status").textContent = "Preview failed: " + window.__h5gSpinePreviewState.error;
  throw error;
}}
</script>
</body>
</html>
"""


def build_preview_html(package_dir: Path, project_title: str | None = None) -> Path:
    json_path = package_dir / "shared_symbols.json"
    if not json_path.is_file():
        raise SystemExit(f"missing shared_symbols.json in {package_dir}")
    skel = json.loads(json_path.read_text())
    raw_data_uris_js = json.dumps(_raw_data_uris(package_dir))
    animations = list(skel.get("animations", {}).keys())
    skins = [
        skin.get("name")
        for skin in skel.get("skins", [])
        if isinstance(skin, dict) and isinstance(skin.get("name"), str)
    ]
    initial_skin = "default" if "default" in skins else (skins[0] if skins else None)
    physics_count = len(skel.get("physics", []))
    report_path = package_dir / "validation_report.json"
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}
    expression_qa = report.get("expression_composite_visual_qa", {})
    title = project_title or package_dir.name
    default_anim = animations[0] if animations else None
    default_anim_js = json.dumps(default_anim) if default_anim else "undefined"
    initial_skin_js = json.dumps(initial_skin) if initial_skin else "undefined"
    skin_list_js = json.dumps(skins)
    skin_notice = ""
    if len(skins) > 1:
        skin_notice = (
            f'<div class="meta">Skins available for preview: {", ".join(skins)}. '
            "Initial skin is default; this file configures the Spine Player skin list but "
            "does not runtime-prove interactive skin switching.</div>"
        )
    physics_notice = ""
    if physics_count:
        physics_notice = (
            f'<div class="meta">Physics constraints: {physics_count}. '
            "The Spine Player runtime updates physics at runtime; preview playback is required "
            "before any motion approval.</div>"
        )
    expression_notice = ""
    if expression_qa.get("enabled"):
        expression_notice = (
            f'<div class="meta">Expression atlas variants: deterministic PNG QA '
            f'{"passed" if expression_qa.get("passed") else "failed"}; '
            f'browser/runtime executed: {str(expression_qa.get("browser_runtime_executed", False)).lower()}. '
            "Open this Spine Player preview and get art review before facial acting approval.</div>"
        )

    html = HTML_TEMPLATE.format(
        project_title=title,
        player_version=SPINE_PLAYER_VERSION,
        anim_count=len(animations),
        anim_list=", ".join(animations) or "(none)",
        skin_notice=skin_notice,
        physics_notice=physics_notice,
        expression_notice=expression_notice,
        spine_player_js=SPINE_PLAYER_JS_CDN,
        spine_player_css=SPINE_PLAYER_CSS_CDN,
        default_anim_js=default_anim_js,
        initial_skin_js=initial_skin_js,
        skin_list_js=skin_list_js,
        raw_data_uris_js=raw_data_uris_js,
    )
    out_path = package_dir / "preview.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(description="Generate preview.html for a Spine package.")
    p.add_argument("package_dir", help="Folder containing shared_symbols.{json,atlas,png}.")
    p.add_argument("--title", help="Project title shown in the preview header.")
    args = p.parse_args()
    path = build_preview_html(Path(args.package_dir), args.title)
    print(f"wrote {path}")
    print(f"  Spine Web Player {SPINE_PLAYER_VERSION}")
    print(f"  Open: open {path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
