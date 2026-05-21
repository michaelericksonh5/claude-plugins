#!/usr/bin/env python3
"""Create a Spine Editor handoff ZIP from a compiled package.

The ZIP is the artifact to send to an animator. It contains the complete import
set (`shared_symbols.json`, `shared_symbols.atlas`, `shared_symbols.png`) plus a
short README and an audit manifest. The packager refuses incomplete packages so
an archive cannot silently omit the texture page again.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import textwrap
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from source_art_guard import ensure_safe_write_path
import spine_version_policy as spine_versions

REQUIRED_FILES = ("shared_symbols.json", "shared_symbols.atlas", "shared_symbols.png")
OPTIONAL_FILES = ("preview.html", "validation_report.json", "rig_layout.json", "layer_interpretation.json")
DEFAULT_ZIP_NAME = "spine_editor_handoff.zip"
EDITOR_IMAGES_ROOT = "editor_images"
CREATE_SPINE_PROJECT_SCRIPT = "CREATE_SPINE_PROJECT.ps1"
SPINE_VERSION = spine_versions.DEFAULT_SPINE_EDITOR_VERSION
SAFE_ZIP_COMPONENT_RE = re.compile(r"^[A-Za-z0-9._ -]+$")
SAFE_SPINE_NAME_RE = re.compile(r"^[A-Za-z0-9._ -]+$")


class HandoffPackageError(ValueError):
    """Raised when a package is not complete enough for Spine Editor handoff."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _powershell_single_quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _safe_spine_name(value: str, label: str) -> str:
    if not value or value in {".", ".."}:
        raise HandoffPackageError(f"{label} is empty or reserved")
    if "/" in value or "\\" in value or ":" in value:
        raise HandoffPackageError(f"{label} contains an unsafe path separator or drive prefix: {value!r}")
    if not SAFE_SPINE_NAME_RE.fullmatch(value):
        raise HandoffPackageError(f"{label} contains unsafe characters: {value!r}")
    return value


def _safe_editor_image_entry(region_name: str) -> str:
    if not region_name:
        raise HandoffPackageError("atlas region name is empty")
    if "\\" in region_name:
        raise HandoffPackageError(f"atlas region {region_name!r} contains a backslash")
    if ":" in region_name:
        raise HandoffPackageError(f"atlas region {region_name!r} contains a drive prefix or unsafe character")
    if region_name.startswith("/"):
        raise HandoffPackageError(f"atlas region {region_name!r} is an absolute path")
    if any(part == "" for part in region_name.split("/")):
        raise HandoffPackageError(f"atlas region {region_name!r} contains an empty path component")
    posix = PurePosixPath(region_name)
    safe_parts: list[str] = []
    for part in posix.parts:
        if part in {"", ".", ".."}:
            raise HandoffPackageError(f"atlas region {region_name!r} contains an unsafe path component")
        if not SAFE_ZIP_COMPONENT_RE.fullmatch(part):
            raise HandoffPackageError(f"atlas region {region_name!r} contains unsafe characters")
        safe_parts.append(part)
    return f"{EDITOR_IMAGES_ROOT}/{'/'.join(safe_parts)}.png"


def _atlas_page(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    raise HandoffPackageError(f"atlas is empty: {path}")


def _parse_pair(value: str, field_name: str, region_name: str) -> tuple[int, int]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2:
        raise HandoffPackageError(f"atlas region {region_name!r} has invalid {field_name}: {value!r}")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise HandoffPackageError(
            f"atlas region {region_name!r} has non-integer {field_name}: {value!r}"
        ) from exc


def _parse_atlas_regions(atlas_path: Path) -> list[dict[str, Any]]:
    lines = [line.rstrip() for line in atlas_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise HandoffPackageError(f"atlas is empty: {atlas_path}")
    regions: list[dict[str, Any]] = []
    current_name: str | None = None
    current_fields: dict[str, str] = {}

    def finish_region() -> None:
        nonlocal current_name, current_fields
        if current_name is None:
            return
        missing = [field for field in ("rotate", "xy", "size") if field not in current_fields]
        if missing:
            raise HandoffPackageError(
                f"atlas region {current_name!r} is missing fields: {', '.join(missing)}"
            )
        rotate = current_fields["rotate"].strip().lower()
        regions.append({
            "name": current_name,
            "rotate": rotate in {"true", "90"},
            "xy": _parse_pair(current_fields["xy"], "xy", current_name),
            "size": _parse_pair(current_fields["size"], "size", current_name),
        })
        current_name = None
        current_fields = {}

    for line in lines[1:]:
        stripped = line.strip()
        if line.startswith((" ", "\t")) and ":" in stripped and current_name is not None:
            key, value = stripped.split(":", 1)
            current_fields[key.strip()] = value.strip()
            continue
        if ":" in stripped:
            continue
        finish_region()
        current_name = stripped
        current_fields = {}
    finish_region()
    return regions


def build_editor_images(package_dir: Path) -> dict[str, bytes]:
    from PIL import Image

    atlas_path = package_dir / "shared_symbols.atlas"
    page_path = package_dir / _atlas_page(atlas_path)
    page = Image.open(page_path).convert("RGBA")
    images: dict[str, bytes] = {}
    for region in _parse_atlas_regions(atlas_path):
        x, y = region["xy"]
        width, height = region["size"]
        crop = page.crop((x, y, x + width, y + height))
        if region["rotate"]:
            crop = crop.rotate(90, expand=True)
        buffer = io.BytesIO()
        crop.save(buffer, format="PNG")
        images[_safe_editor_image_entry(region["name"])] = buffer.getvalue()
    if not images:
        raise HandoffPackageError("atlas has no regions to unpack for Spine Editor images")
    return images


def validate_package_dir(package_dir: Path) -> list[str]:
    missing = [name for name in REQUIRED_FILES if not (package_dir / name).is_file()]
    if missing:
        raise HandoffPackageError(
            f"missing required Spine Editor import files: {', '.join(missing)}"
        )
    atlas_page = _atlas_page(package_dir / "shared_symbols.atlas")
    if atlas_page != "shared_symbols.png":
        raise HandoffPackageError(
            f"atlas page is {atlas_page!r}, expected 'shared_symbols.png' for portable handoff"
        )
    report = _read_json(package_dir / "validation_report.json")
    if report and report.get("status") != "ok":
        raise HandoffPackageError(
            f"validation_report.json status is {report.get('status')!r}; fix validation before handoff"
        )
    return [name for name in OPTIONAL_FILES if (package_dir / name).is_file()]


def build_audit_manifest(package_dir: Path, included_files: list[str]) -> dict[str, Any]:
    spine_json = _read_json(package_dir / "shared_symbols.json")
    report = _read_json(package_dir / "validation_report.json")
    animations = sorted((spine_json.get("animations") or {}).keys())
    return {
        "schema": "spine_slot_animation_handoff_audit_v1",
        "package_dir": str(package_dir.resolve()),
        "review_only": True,
        "spine_version": (spine_json.get("skeleton") or {}).get("spine"),
        "animations": animations,
        "bones_count": len(spine_json.get("bones") or []),
        "slots_count": len(spine_json.get("slots") or []),
        "mesh_attachments_emitted": report.get("mesh_attachments_emitted", 0),
        "weighted_mesh_attachments_emitted": report.get("weighted_mesh_attachments_emitted", 0),
        "weighted_mesh_review_required": report.get("weighted_mesh_review_required", False),
        "weighted_mesh_review_required_reason": report.get("weighted_mesh_review_required_reason"),
        "mesh_deformation_qa": report.get("mesh_deformation_qa", {}),
        "validation_status": report.get("status"),
        "loop_validation_status": report.get("loop_validation_status"),
        "editor_images_root": EDITOR_IMAGES_ROOT,
        "editor_images_count": len([name for name in included_files if name.startswith(f"{EDITOR_IMAGES_ROOT}/")]),
        "spine_project_script": CREATE_SPINE_PROJECT_SCRIPT,
        "files": {
            name: {
                "sha256": _sha256(package_dir / name),
                "bytes": (package_dir / name).stat().st_size,
            }
            for name in included_files
            if not name.startswith(f"{EDITOR_IMAGES_ROOT}/")
            and name != CREATE_SPINE_PROJECT_SCRIPT
        },
    }


def default_skeleton_name(package_dir: Path, audit: dict[str, Any]) -> str:
    animations = audit.get("animations") or []
    base_candidates = [
        name for name in animations
        if not str(name).lower().endswith(("idle", "breathe", "land", "win", "smart"))
    ]
    if base_candidates:
        return sorted(base_candidates, key=len)[0]
    return package_dir.name.replace("_spine", "").replace(" ", "_")


def build_create_project_script(package_dir: Path, audit: dict[str, Any]) -> str:
    skeleton_name = _safe_spine_name(default_skeleton_name(package_dir, audit), "skeleton name")
    output_project = _safe_spine_name(f"{skeleton_name}.spine", "output project")
    spine_version = str(audit.get("spine_version") or SPINE_VERSION)
    skeleton_literal = _powershell_single_quoted(skeleton_name)
    output_literal = _powershell_single_quoted(output_project)
    spine_version_literal = _powershell_single_quoted(spine_version)
    return textwrap.dedent(
        f"""\
        $ErrorActionPreference = 'Stop'
        $here = Split-Path -Parent $MyInvocation.MyCommand.Path
        $skeletonName = {skeleton_literal}
        $outputProject = {output_literal}
        $spineVersion = {spine_version_literal}
        $spine = $null

        if ($env:SPINE_CLI -and (Test-Path -LiteralPath $env:SPINE_CLI)) {{
            $spine = $env:SPINE_CLI
        }}

        if (-not $spine) {{
            $cmd = Get-Command Spine.com -ErrorAction SilentlyContinue
            if ($cmd) {{ $spine = $cmd.Source }}
        }}

        if (-not $spine) {{
            $cmd = Get-Command Spine -ErrorAction SilentlyContinue
            if ($cmd) {{ $spine = $cmd.Source }}
        }}

        if (-not $spine) {{
            $candidates = @(
                "$env:ProgramFiles\\Spine\\Spine.com",
                "$env:ProgramFiles\\Esoteric Software\\Spine\\Spine.com",
                "${{env:ProgramFiles(x86)}}\\Spine\\Spine.com",
                "${{env:ProgramFiles(x86)}}\\Esoteric Software\\Spine\\Spine.com",
                "$env:LOCALAPPDATA\\Spine\\Spine.com",
                "$env:LOCALAPPDATA\\Esoteric Software\\Spine\\Spine.com"
            )
            foreach ($candidate in $candidates) {{
                if ($candidate -and (Test-Path -LiteralPath $candidate)) {{
                    $spine = $candidate
                    break
                }}
            }}
        }}

        if (-not $spine) {{
            throw "Could not find Spine.com. Install Spine, add it to PATH, or set SPINE_CLI to the full Spine.com path."
        }}

        $json = Join-Path $here "shared_symbols.json"
        $out = Join-Path $here $outputProject
        $jsonVersion = (Get-Content -LiteralPath $json -Raw | ConvertFrom-Json).skeleton.spine
        if ($jsonVersion -ne $spineVersion) {{
            throw "Package JSON version '$jsonVersion' does not match import version '$spineVersion'. Regenerate the package or import with the JSON version first."
        }}

        Write-Host "Using Spine CLI: $spine"
        Write-Host "Using Spine version: $spineVersion"
        Write-Host "Creating Spine project: $out"
        & $spine -u $spineVersion -i $json -o $out -r $skeletonName
        if ($LASTEXITCODE -ne 0) {{
            throw "Spine CLI import failed with exit code $LASTEXITCODE"
        }}

        Write-Host ""
        Write-Host "Created $out"
        Write-Host "If images show as MISSING in Spine, set the Images path to:"
        Write-Host "  $(Join-Path $here "{EDITOR_IMAGES_ROOT}")"
        """
    )


def build_readme(package_dir: Path, audit: dict[str, Any]) -> str:
    mesh_note = "Region attachments only; no mesh or weighted mesh attachments were emitted."
    if audit.get("mesh_attachments_emitted"):
        mesh_note = (
            f"{audit['mesh_attachments_emitted']} mesh attachment(s), "
            f"{audit.get('weighted_mesh_attachments_emitted', 0)} weighted mesh attachment(s). "
            "Automatic weights are first-pass only; animator review/final weight painting is still required."
        )
    qa = audit.get("mesh_deformation_qa") or {}
    qa_note = "No weighted mesh deformation QA was required."
    if qa.get("enabled"):
        qa_note = (
            f"Mesh deformation QA emitted `{qa.get('test_animation')}` with "
            f"{qa.get('weighted_mesh_count')} weighted mesh attachment(s). "
            "Open the animation in Spine and inspect endpoint behavior, stretching, and silhouette drift."
        )
    return textwrap.dedent(
        f"""\
        # Spine Editor Import

        This ZIP was generated by the `spine-slot-animation` Claude plugin.
        The skeleton data is tagged for Spine {audit.get("spine_version") or SPINE_VERSION}.

        This is not a native `.spine` project file and Spine does not import the
        ZIP directly. It is a review bundle containing exported skeleton data,
        atlas runtime files, and unpacked editor images.

        ## Required Files

        - `shared_symbols.json` - skeleton data ({audit.get("bones_count")} bones,
          {audit.get("slots_count")} slots, {len(audit.get("animations") or [])} animations).
        - `shared_symbols.atlas` - atlas descriptor.
        - `shared_symbols.png` - texture page referenced by the atlas.
        - `editor_images/` - unpacked PNGs for Spine Editor's Images path.

        Keep the unzipped folder intact.

        ## One-command `.spine` Project Creation

        If Spine is installed on this machine, right-click `CREATE_SPINE_PROJECT.ps1`
        and run it with PowerShell, or run:

        ```powershell
        powershell -ExecutionPolicy Bypass -File .\\CREATE_SPINE_PROJECT.ps1
        ```

        The script uses Spine's official CLI import command to create a `.spine`
        project next to these files. It does not hand-write the `.spine` format.

        ## Official Editor Import Steps

        1. Unzip this archive.
        2. Open the same Spine Editor version shown in `shared_symbols.json`.
        3. Choose **File -> Import Data...**.
        4. Select `shared_symbols.json`.
        5. Import it into a new project.
        6. If the images show as `MISSING`, select the **Images** node in Spine's Tree
           and set its path to the unzipped `editor_images` folder.
        7. Save the result as a `.spine` project if you did not use the script above.
        8. Review the setup pose in Setup mode and the emitted animations in Animate mode.

        Spine requires imported JSON data to be opened with the same version that wrote
        `skeleton.spine`. If that version does not match Chris's current editor, run
        `CREATE_SPINE_PROJECT.ps1` first so Spine imports with the data version and creates
        a `.spine` project. Then open the `.spine` project in the newer editor.

        `shared_symbols.atlas` and `shared_symbols.png` are included for runtime preview
        and game/export validation. The `editor_images/` folder is included because Spine's
        documented reconstruction workflow uses unpacked atlas images for editor image lookup.

        ## Preview

        If `preview.html` is included, open it in a browser. It embeds the JSON,
        atlas, and PNG for `file://` review, but it still needs network access to
        load Spine Player {spine_versions.DEFAULT_SPINE_PLAYER_VERSION} from the CDN unless your browser has it cached.

        ## Rig Notes

        - Animations: {", ".join(audit.get("animations") or [])}
        - Validation status: {audit.get("validation_status")}
        - Loop validation status: {audit.get("loop_validation_status")}
        - Editor images: {audit.get("editor_images_count")} unpacked PNGs under `editor_images/`
        - Mesh status: {mesh_note}
        - Mesh QA: {qa_note}
        - This is a review package, not a production `.spine` or `.skel` export.
        """
    )


def package_handoff(package_dir: Path, zip_path: Path | None = None) -> Path:
    package_dir = package_dir.resolve()
    output = ensure_safe_write_path((zip_path or (package_dir / DEFAULT_ZIP_NAME)).resolve(), "handoff ZIP output")
    optional_files = validate_package_dir(package_dir)
    editor_images = build_editor_images(package_dir)
    included_files = [*REQUIRED_FILES, *optional_files, *sorted(editor_images), CREATE_SPINE_PROJECT_SCRIPT]
    audit = build_audit_manifest(package_dir, included_files)
    readme = build_readme(package_dir, audit)
    create_project_script = build_create_project_script(package_dir, audit)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in included_files:
            if name.startswith(f"{EDITOR_IMAGES_ROOT}/"):
                archive.writestr(name, editor_images[name])
            elif name == CREATE_SPINE_PROJECT_SCRIPT:
                archive.writestr(name, create_project_script)
            else:
                archive.write(package_dir / name, arcname=name)
        archive.writestr("README_FOR_SPINE_EDITOR.md", readme)
        archive.writestr("audit_manifest.json", json.dumps(audit, indent=2))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Package a compiled Spine proof for animator handoff.")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--zip", type=Path, help=f"Output ZIP path. Defaults to {DEFAULT_ZIP_NAME}.")
    args = parser.parse_args()
    try:
        path = package_handoff(args.package_dir, args.zip)
    except (HandoffPackageError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
