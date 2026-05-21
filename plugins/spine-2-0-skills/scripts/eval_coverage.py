#!/usr/bin/env python3
"""Build and validate the local promoted-feature eval coverage report."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path("assets/eval_coverage_registry.json")
REPORT_PATH = Path("assets/eval_coverage_report.json")

REQUIRED_PHASE_11_EVAL_IDS = {
    "eval-17-sequence-auto-emission",
    "eval-18-mesh-plan-emission",
    "eval-19-auto-bind-weighted-mesh",
    "eval-20-multi-skin-variants",
    "eval-21-bezier-modern-profile",
    "eval-22-ui-frame-ambient-loop",
    "eval-23-background-parallax-ambient",
    "eval-24-character-wardrobe-physics",
    "eval-25-expression-atlas-variants",
    "eval-26-avatar-state-manifest",
    "eval-28-production-export-gate",
    "eval-30-automatic-weighted-mesh",
    "eval-31-spine-cli-reference",
    "eval-32-autonomous-rigging-proposals",
    "eval-33-bundled-corpus-evidence-pack",
    "eval-34-h5g-corpus-bakeoff-resolver",
}


def load_registry(root: Path) -> dict[str, Any]:
    return json.loads((root / REGISTRY_PATH).read_text())


def discover_local_test_names(root: Path) -> set[str]:
    names: set[str] = set()
    for test_path in sorted((root / "tests").glob("test_*.py")):
        module = ast.parse(test_path.read_text())
        for node in ast.walk(module):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                names.add(node.name)
    return names


def _docs_path_exists(root: Path, docs_path: str) -> bool:
    path = docs_path.split("#", 1)[0]
    return bool(path) and (root / path).exists()


def validate_registry(root: Path, registry: dict[str, Any], test_names: set[str]) -> list[str]:
    issues: list[str] = []
    if registry.get("schema") != "claude_spine_phase_11_eval_coverage_registry_v1":
        issues.append("registry.schema must be claude_spine_phase_11_eval_coverage_registry_v1")

    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        return issues + ["registry.entries must be a non-empty list"]

    eval_ids: set[str] = set()
    aliases: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"entries[{index}]"
        eval_id = entry.get("eval_id")
        if not isinstance(eval_id, str) or not eval_id:
            issues.append(f"{prefix}.eval_id must be a non-empty string")
            continue
        if eval_id in eval_ids:
            issues.append(f"{prefix}.eval_id duplicates {eval_id}")
        eval_ids.add(eval_id)

        for alias in entry.get("aliases", []):
            if not isinstance(alias, str) or not alias:
                issues.append(f"{prefix}.aliases must contain non-empty strings")
            elif alias in aliases:
                issues.append(f"{prefix}.aliases duplicates {alias}")
            else:
                aliases.add(alias)

        if entry.get("promoted") is not True:
            issues.append(f"{prefix}.promoted must be true")
        if not entry.get("feature"):
            issues.append(f"{prefix}.feature is required")
        if not entry.get("promoted_status"):
            issues.append(f"{prefix}.promoted_status is required")
        if not _docs_path_exists(root, str(entry.get("docs_path", ""))):
            issues.append(f"{prefix}.docs_path does not exist: {entry.get('docs_path')}")
        if not entry.get("required_feature_gates"):
            issues.append(f"{prefix}.required_feature_gates must not be empty")

        for field in ("positive_tests", "guard_tests"):
            tests = entry.get(field)
            if not isinstance(tests, list) or not tests:
                issues.append(f"{prefix}.{field} must be a non-empty list")
                continue
            for test_name in tests:
                if test_name not in test_names:
                    issues.append(f"{prefix}.{field} refers to missing test {test_name}")

    missing_required = sorted(REQUIRED_PHASE_11_EVAL_IDS - eval_ids)
    if missing_required:
        issues.append("missing required Phase 11 eval IDs: " + ", ".join(missing_required))

    return issues


def build_report(root: Path, test_result: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = load_registry(root)
    test_names = discover_local_test_names(root)
    issues = validate_registry(root, registry, test_names)
    entries = []
    for entry in registry["entries"]:
        positive_tests = entry["positive_tests"]
        guard_tests = entry["guard_tests"]
        entries.append({
            "eval_id": entry["eval_id"],
            "aliases": entry.get("aliases", []),
            "feature": entry["feature"],
            "promoted": entry["promoted"],
            "promoted_status": entry["promoted_status"],
            "docs_path": entry["docs_path"],
            "required_feature_gates": entry["required_feature_gates"],
            "positive_case": entry["positive_case"],
            "guard_case": entry["guard_case"],
            "positive_tests": positive_tests,
            "guard_tests": guard_tests,
            "positive_test_count": len(positive_tests),
            "guard_test_count": len(guard_tests),
        })

    report: dict[str, Any] = {
        "schema": "claude_spine_phase_11_eval_coverage_report_v1",
        "registry_path": str(REGISTRY_PATH).replace("\\", "/"),
        "status": "ok" if not issues else "failed",
        "phase_11_required_eval_ids": sorted(REQUIRED_PHASE_11_EVAL_IDS),
        "promoted_feature_count": len(entries),
        "local_eval_count": len(test_names),
        "entries": entries,
        "issues": issues,
    }
    if test_result is not None:
        report["test_result"] = test_result
    return report


def write_report(root: Path, test_result: dict[str, Any] | None = None) -> dict[str, Any]:
    report = build_report(root, test_result)
    report_path = root / REPORT_PATH
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = write_report(root)
    print(json.dumps({
        "status": report["status"],
        "promoted_feature_count": report["promoted_feature_count"],
        "local_eval_count": report["local_eval_count"],
        "issues": report["issues"],
        "report_path": str(REPORT_PATH).replace("\\", "/"),
    }, indent=2))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
