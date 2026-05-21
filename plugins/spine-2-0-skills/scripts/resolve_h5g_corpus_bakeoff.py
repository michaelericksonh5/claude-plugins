#!/usr/bin/env python3
"""Resolve H5G corpus/bakeoff evidence sources without writing source art."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESEARCH_ROOT = Path(r"C:\Users\merickson\Desktop\Claude Spine\research")
DEFAULT_NETWORK_BAKEOFF_ROOT = Path(r"G:\artSource\_spineResources\H5G_Corpus_Bakeoff")
SNAPSHOT_PATH = PLUGIN_ROOT / "assets" / "h5g_corpus_evidence_snapshot.json"
DISTILLED_EVIDENCE_PATH = PLUGIN_ROOT / "assets" / "h5g_corpus_distilled_evidence.json"
FULL_BAKEOFF_TOOL = "full_deep_animation_bakeoff.py"
GAP_BAKEOFF_TOOL = "compiler_gap_bakeoff.py"
NETWORK_REPORT = "H5G_CORPUS_BAKEOFF_CONSOLIDATED_REPORT.md"
NETWORK_INDEX = "H5G_CORPUS_BAKEOFF_CONSOLIDATED_INDEX.json"
NETWORK_MANIFEST = "report_pack_manifest.json"


def _path_from_env(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else default


def _safe_children(root: Path, limit: int = 25) -> list[str]:
    if not root.is_dir():
        return []
    try:
        return sorted(child.name for child in root.iterdir())[:limit]
    except OSError:
        return []


def _existing_path_map(root: Path, relative_paths: dict[str, str]) -> dict[str, str]:
    existing: dict[str, str] = {}
    if not root.is_dir():
        return existing
    for key, relative_path in relative_paths.items():
        candidate = root / relative_path
        if candidate.exists():
            existing[key] = str(candidate)
    return existing


def detect_sources(
    *,
    research_root: Path | None = None,
    network_root: Path | None = None,
    plugin_root: Path = PLUGIN_ROOT,
) -> dict[str, Any]:
    resolved_research = research_root or _path_from_env("H5G_RESEARCH_ROOT", DEFAULT_RESEARCH_ROOT)
    resolved_network = network_root or _path_from_env("H5G_CORPUS_BAKEOFF_ROOT", DEFAULT_NETWORK_BAKEOFF_ROOT)
    snapshot = plugin_root / "assets" / "h5g_corpus_evidence_snapshot.json"
    distilled = plugin_root / "assets" / "h5g_corpus_distilled_evidence.json"

    full_tool = resolved_research / FULL_BAKEOFF_TOOL
    gap_tool = resolved_research / GAP_BAKEOFF_TOOL
    research_available = full_tool.is_file() and gap_tool.is_file()
    network_available = resolved_network.is_dir()
    network_children = _safe_children(resolved_network)
    network_artifacts = _existing_path_map(
        resolved_network,
        {
            "consolidated_report": NETWORK_REPORT,
            "consolidated_index": NETWORK_INDEX,
            "report_pack_manifest": NETWORK_MANIFEST,
            "coverage_report": "coverage/animation_family_coverage.md",
            "coverage_index": "coverage/animation_family_coverage.json",
            "family_recipe_specs": "family_recipe_specs/family_recipe_specs.md",
            "family_recipe_specs_index": "family_recipe_specs/family_recipe_specs.json",
            "contextual_layer_interpretation": "contextual_layer_interpretation/contextual_layer_interpretation.md",
            "contextual_layer_interpretation_index": "contextual_layer_interpretation/contextual_layer_interpretation.json",
            "latest_motion_profile": "compiler_motion_profiles/latest_exact_motion_profile.json",
            "full_deep_bakeoff_report": (
                "full_deep_animation_bakeoff/closure_full_20260506_225908/"
                "full_deep_animation_bakeoff.md"
            ),
            "full_deep_bakeoff_index": (
                "full_deep_animation_bakeoff/closure_full_20260506_225908/"
                "full_deep_animation_bakeoff.json"
            ),
            "compiler_gap_bakeoff_report": (
                "compiler_gap_bakeoff/closure_full_20260506_225908/"
                "compiler_gap_bakeoff.md"
            ),
            "compiler_gap_bakeoff_index": (
                "compiler_gap_bakeoff/closure_full_20260506_225908/"
                "compiler_gap_bakeoff.json"
            ),
        },
    )
    network_report_pack_available = all(
        key in network_artifacts
        for key in ("consolidated_report", "consolidated_index", "report_pack_manifest")
    )
    snapshot_available = snapshot.is_file() and distilled.is_file()

    if research_available:
        status = "full_h5g_research_workspace_available"
        evidence_tier = "full_research"
    elif network_report_pack_available:
        status = "network_h5g_corpus_bakeoff_report_pack_available"
        evidence_tier = "network_report_pack"
    elif network_available:
        status = "network_h5g_corpus_bakeoff_available"
        evidence_tier = "network_bakeoff_resource"
    elif snapshot_available:
        status = "bundled_snapshot_only"
        evidence_tier = "bundled_snapshot"
    else:
        status = "missing"
        evidence_tier = "none"

    return {
        "schema": "spine_slot_animation_h5g_corpus_bakeoff_resolution_v1",
        "status": status,
        "evidence_tier": evidence_tier,
        "fresh_full_bakeoff_proof": research_available,
        "advisory_snapshot_only": evidence_tier == "bundled_snapshot",
        "paths": {
            "research_root": str(resolved_research),
            "network_bakeoff_root": str(resolved_network),
            "snapshot": str(snapshot),
            "distilled_evidence": str(distilled),
        },
        "preferred_read_order": [
            "network_bakeoff_artifacts.consolidated_report",
            "network_bakeoff_artifacts.consolidated_index",
            "network_bakeoff_artifacts.coverage_report",
            "network_bakeoff_artifacts.family_recipe_specs",
            "network_bakeoff_artifacts.contextual_layer_interpretation",
            "network_bakeoff_artifacts.latest_motion_profile",
            "bundled distilled evidence",
        ],
        "availability": {
            "full_research_workspace": research_available,
            "network_bakeoff_resource": network_available,
            "network_report_pack": network_report_pack_available,
            "network_bakeoff_resource_empty": network_available and not network_children,
            "bundled_snapshot": snapshot_available,
        },
        "network_bakeoff_preview": network_children,
        "network_bakeoff_artifacts": network_artifacts,
        "commands": {
            "smoke_bakeoff": [
                sys.executable,
                str(full_tool),
                "--limit",
                "25",
                "--include-ui",
                "--include-review-buckets",
                "--progress",
            ] if research_available else [],
            "full_bakeoff": [
                sys.executable,
                str(full_tool),
                "--include-ui",
                "--include-review-buckets",
                "--progress",
            ] if research_available else [],
        },
        "claim_boundary": (
            "Fresh full bakeoff proof is available only when the full H5G research workspace is present. "
            "Network resources and bundled snapshots are references; they do not replace Chris approval or target runtime proof."
        ),
        "write_policy": "read_only_for_g_artsource; outputs must use safe non-source-art paths",
    }


def run_smoke_bakeoff(report: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    command = report["commands"].get("smoke_bakeoff") or []
    if not command:
        report["run"] = {
            "status": "skipped",
            "reason": "full H5G research workspace is not available",
        }
        return report

    safe_out_dir = ensure_safe_write_path(out_dir, "bakeoff output directory")
    safe_out_dir.mkdir(parents=True, exist_ok=True)
    command = command + ["--output-dir", str(safe_out_dir)]
    result = subprocess.run(command, capture_output=True, text=True)
    report["run"] = {
        "status": "ok" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "command": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve H5G corpus/bakeoff evidence sources.")
    parser.add_argument("--research-root", type=Path)
    parser.add_argument("--network-root", type=Path)
    parser.add_argument("--run-smoke-bakeoff", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=PLUGIN_ROOT / "generated" / "h5g_bakeoff_smoke")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = detect_sources(research_root=args.research_root, network_root=args.network_root)
    if args.run_smoke_bakeoff:
        report = run_smoke_bakeoff(report, args.out_dir)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] != "missing" else 2


if __name__ == "__main__":
    raise SystemExit(main())
