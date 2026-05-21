#!/usr/bin/env python3
"""Create a native .spine project through the official Spine CLI.

This script does not write the proprietary .spine format itself. It validates a
compiled package, then invokes Spine's documented CLI import path:

    Spine.com -u 4.3.04 -i shared_symbols.json -o output.spine -r SkeletonName
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path
import spine_version_policy as spine_versions

JSON_NAME = "shared_symbols.json"
ATLAS_NAME = "shared_symbols.atlas"
PNG_NAME = "shared_symbols.png"
REPORT_NAME = "spine_project_report.json"
DEFAULT_SPINE_VERSION = spine_versions.DEFAULT_SPINE_EDITOR_VERSION


class SpineProjectError(ValueError):
    """Raised when the package cannot be converted through Spine CLI."""


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_skeleton_name(package_dir: Path, spine_json: dict[str, Any]) -> str:
    animations = spine_json.get("animations") or {}
    if isinstance(animations, dict):
        base_candidates = [
            name for name in animations
            if not name.lower().endswith(("idle", "breathe", "land", "win", "smart"))
        ]
        if base_candidates:
            return sorted(base_candidates, key=len)[0]
    return package_dir.name.replace("_spine", "").replace(" ", "_")


def validate_package(package_dir: Path) -> dict[str, Any]:
    missing = [
        name for name in (JSON_NAME, ATLAS_NAME, PNG_NAME)
        if not (package_dir / name).is_file()
    ]
    if missing:
        raise SpineProjectError(f"missing required package files: {', '.join(missing)}")
    validation = read_json(package_dir / "validation_report.json") if (package_dir / "validation_report.json").is_file() else {}
    if validation and validation.get("status") != "ok":
        raise SpineProjectError(
            f"validation_report.json status is {validation.get('status')!r}; fix validation first"
        )
    return read_json(package_dir / JSON_NAME)


def skeleton_spine_version(spine_json: dict[str, Any]) -> str:
    skeleton = spine_json.get("skeleton")
    if not isinstance(skeleton, dict) or not isinstance(skeleton.get("spine"), str) or not skeleton["spine"]:
        raise SpineProjectError("shared_symbols.json is missing skeleton.spine")
    return skeleton["spine"]


def candidate_spine_paths() -> list[Path]:
    names = ("Spine.com", "Spine")
    candidates: list[Path] = []
    env_path = os.environ.get("SPINE_CLI")
    if env_path:
        candidates.append(Path(env_path))
    for name in names:
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    for root_env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        root = os.environ.get(root_env)
        if root:
            candidates.extend([
                Path(root) / "Spine" / "Spine.com",
                Path(root) / "Esoteric Software" / "Spine" / "Spine.com",
            ])
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = os.path.normcase(str(path))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def find_spine_cli(explicit: Path | None = None) -> Path:
    candidates = [explicit] if explicit else candidate_spine_paths()
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    searched = ", ".join(str(path) for path in candidates if path) or "PATH, SPINE_CLI, common install folders"
    raise SpineProjectError(f"Spine CLI not found. Searched: {searched}")


def build_import_command(
    spine_cli: Path,
    package_dir: Path,
    output_project: Path,
    skeleton_name: str,
    spine_version: str,
) -> list[str]:
    return [
        str(spine_cli),
        "-u",
        spine_version,
        "-i",
        str(package_dir / JSON_NAME),
        "-o",
        str(output_project),
        "-r",
        skeleton_name,
    ]


def write_report(package_dir: Path, report: dict[str, Any]) -> None:
    report_path = ensure_safe_write_path(package_dir / REPORT_NAME, "spine project report")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def create_spine_project(
    package_dir: Path,
    output_project: Path | None = None,
    spine_cli: Path | None = None,
    spine_version: str | None = None,
    skeleton_name: str | None = None,
    dry_run: bool = False,
    probe_project: bool = True,
) -> dict[str, Any]:
    package_dir = package_dir.resolve()
    ensure_safe_write_path(package_dir / REPORT_NAME, "spine project report")
    spine_json = validate_package(package_dir)
    json_spine_version = skeleton_spine_version(spine_json)
    resolved_spine_version = spine_version or json_spine_version
    if resolved_spine_version != json_spine_version:
        raise SpineProjectError(
            "Spine data import must use the same editor version recorded in shared_symbols.json. "
            f"JSON version is {json_spine_version!r}, requested CLI version is {resolved_spine_version!r}. "
            "Regenerate the package for the target version or import with the JSON version first and then "
            "open the resulting .spine project in the newer editor."
        )
    resolved_spine_cli = find_spine_cli(spine_cli)
    resolved_output = (output_project or (package_dir / f"{default_skeleton_name(package_dir, spine_json)}.spine")).resolve()
    ensure_safe_write_path(resolved_output, "spine project output")
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_skeleton_name = skeleton_name or default_skeleton_name(package_dir, spine_json)
    command = build_import_command(
        resolved_spine_cli,
        package_dir,
        resolved_output,
        resolved_skeleton_name,
        resolved_spine_version,
    )
    report: dict[str, Any] = {
        "schema": "spine_slot_animation_native_spine_project_report_v1",
        "status": "dry_run" if dry_run else "pending",
        "package_dir": str(package_dir),
        "spine_cli": str(resolved_spine_cli),
        "spine_version": resolved_spine_version,
        "json_spine_version": json_spine_version,
        "output_project": str(resolved_output),
        "skeleton_name": resolved_skeleton_name,
        "command": command,
        "official_cli_import": True,
        "hand_authored_spine_file": False,
    }
    if dry_run:
        write_report(package_dir, report)
        return report

    result = subprocess.run(command, cwd=package_dir, capture_output=True, text=True)
    report.update({
        "import_exit_code": result.returncode,
        "import_stdout": result.stdout,
        "import_stderr": result.stderr,
    })
    if result.returncode != 0:
        report["status"] = "failed"
        report["errors"] = [f"Spine CLI import failed with exit code {result.returncode}"]
        write_report(package_dir, report)
        return report
    if not resolved_output.is_file():
        report["status"] = "failed"
        report["errors"] = ["Spine CLI reported success but did not create the .spine file"]
        write_report(package_dir, report)
        return report

    if probe_project:
        probe = subprocess.run(
            [str(resolved_spine_cli), "-i", str(resolved_output)],
            cwd=package_dir,
            capture_output=True,
            text=True,
        )
        report.update({
            "probe_exit_code": probe.returncode,
            "probe_stdout": probe.stdout,
            "probe_stderr": probe.stderr,
        })
        if probe.returncode != 0:
            report["status"] = "failed"
            report["errors"] = [f"Spine CLI project info probe failed with exit code {probe.returncode}"]
            write_report(package_dir, report)
            return report

    report["status"] = "ok"
    report["errors"] = []
    write_report(package_dir, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a .spine project via the official Spine CLI import.")
    parser.add_argument("package_dir", type=Path, help="Folder containing shared_symbols.json/atlas/png.")
    parser.add_argument("--output-project", type=Path, help="Output .spine path. Defaults inside package_dir.")
    parser.add_argument("--spine-cli", type=Path, help="Path to Spine.com/Spine executable. Defaults to SPINE_CLI/PATH.")
    parser.add_argument("--spine-version", help="Override CLI import version. Must match shared_symbols.json skeleton.spine.")
    parser.add_argument("--skeleton-name")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and write the planned command only.")
    parser.add_argument("--skip-probe", action="store_true", help="Do not run Spine -i output.spine after import.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = create_spine_project(
            args.package_dir,
            output_project=args.output_project,
            spine_cli=args.spine_cli,
            spine_version=args.spine_version,
            skeleton_name=args.skeleton_name,
            dry_run=args.dry_run,
            probe_project=not args.skip_probe,
        )
    except (OSError, SpineProjectError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(json.dumps({
        "status": report["status"],
        "output_project": report["output_project"],
        "report": str((args.package_dir / REPORT_NAME).resolve()),
    }, indent=2))
    return 0 if report["status"] in {"ok", "dry_run"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
