#!/usr/bin/env python3
"""Build the compiler evidence index from existing H5G research outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from source_art_guard import write_guard_error


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESEARCH_ROOT = Path(r"C:\Users\merickson\Desktop\Claude Spine\research")
DEFAULT_OUTPUT = PLUGIN_ROOT / "assets" / "compiler_evidence_index.json"
PROHIBITED_RESEARCH_ROOTS = (Path(r"G:\artSource"),)
PERFORCE_ROOT_MARKERS = {"perforce", "p4", ".p4"}

REQUIRED_SOURCES = {
    "family_recipe_specs": Path("generated/family_recipe_specs/family_recipe_specs.md"),
    "animation_family_coverage": Path("generated/coverage/animation_family_coverage.md"),
    "full_deep_bakeoff_findings": Path("FULL_DEEP_ANIMATION_BAKEOFF_FINDINGS.md"),
    "latest_exact_motion_profile": Path(
        "generated/compiler_motion_profiles/latest_exact_motion_profile.json"
    ),
    "contextual_layer_interpretation": Path("generated/contextual_layer_interpretation"),
    "symbol_compendium_runs": Path("generated/symbol_compendium_runs"),
    "ui_animation_coverage": Path("generated/ui_animation_coverage"),
    "advanced_spine_capability_plan": Path("ADVANCED_SPINE_CAPABILITY_IMPLEMENTATION_PLAN.md"),
}

OPTIONAL_SOURCES = {
    "family_recipe_specs_json": Path("generated/family_recipe_specs/family_recipe_specs.json"),
    "contextual_layer_interpretation_md": Path(
        "generated/contextual_layer_interpretation/contextual_layer_interpretation.md"
    ),
    "contextual_layer_interpretation_json": Path(
        "generated/contextual_layer_interpretation/contextual_layer_interpretation.json"
    ),
    "ui_animation_classification_md": Path(
        "generated/ui_animation_coverage/ui_animation_classification.md"
    ),
    "ui_animation_classification_json": Path(
        "generated/ui_animation_coverage/ui_animation_classification.json"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build assets/compiler_evidence_index.json from H5G research outputs."
    )
    parser.add_argument(
        "--research-root",
        type=Path,
        default=DEFAULT_RESEARCH_ROOT,
        help="H5G research directory. Defaults to the local Claude Spine research folder.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output JSON path inside the Claude_Spine_Generator plugin.",
    )
    parser.add_argument(
        "--stamp",
        action="store_true",
        help="Use the current wall-clock time for generated_at. Defaults to a deterministic source hash.",
    )
    return parser.parse_args()


def normalize_path(path: Path) -> Path:
    return path.expanduser().resolve()


def normalized_path_text(path: Path) -> str:
    return str(path).replace("\\", "/").rstrip("/").casefold()


def path_is_under(path: Path, root: Path) -> bool:
    path_text = normalized_path_text(path)
    root_text = normalized_path_text(root)
    return path_text == root_text or path_text.startswith(f"{root_text}/")


def validate_research_root(root: Path) -> None:
    for prohibited_root in PROHIBITED_RESEARCH_ROOTS:
        if path_is_under(root, normalize_path(prohibited_root)):
            raise ValueError(f"Refusing to read prohibited research root: {root}")
    for part in root.parts:
        marker = part.casefold()
        if marker in PERFORCE_ROOT_MARKERS or marker.startswith("p4_"):
            raise ValueError(f"Refusing to read Perforce-like research root: {root}")


def ensure_under(path: Path, root: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Refusing to read outside research root: {path}") from exc


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def hash_directory(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    entries = 0
    for child in sorted((p for p in path.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
        entries += 1
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(child.read_bytes())
        digest.update(b"\0")
    return entries, digest.hexdigest()


def source_record(
    root: Path,
    rel_path: Path,
    required: bool,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    path = normalize_path(root / rel_path)
    ensure_under(path, root)
    exists = path.exists()
    kind = "directory" if exists and path.is_dir() else "file"
    status = "ok" if exists else ("missing_required" if required else "missing_optional")
    record: dict[str, Any] = {
        "path": str(rel_path).replace("\\", "/"),
        "required": required,
        "kind": kind,
        "exists": exists,
        "status": status,
    }
    try:
        if exists and path.is_file():
            record["bytes"] = path.stat().st_size
            record["sha256"] = hash_file(path)
        if exists and path.is_dir():
            entries, tree_hash = hash_directory(path)
            record["entries"] = entries
            record["tree_sha256"] = tree_hash
    except OSError as exc:
        message = f"Could not hash {rel_path}: {exc}"
        if required:
            errors.append(message)
        else:
            warnings.append(message)
    return record


def read_text(root: Path, rel_path: Path, errors: list[str], required: bool = True) -> str:
    path = normalize_path(root / rel_path)
    ensure_under(path, root)
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        if required:
            errors.append(f"Could not read {rel_path}: {exc}")
        return ""


def read_json(root: Path, rel_path: Path, errors: list[str], required: bool) -> Any:
    path = normalize_path(root / rel_path)
    ensure_under(path, root)
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        message = f"Malformed JSON in {rel_path}: {exc}"
    except OSError as exc:
        message = f"Could not read {rel_path}: {exc}"
    if required:
        errors.append(message)
    return None


def clean_cell(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    return value.replace("`", "").strip()


def convert_scalar(value: str) -> Any:
    if not isinstance(value, str):
        return value
    value = clean_cell(value)
    if value.lower() in {"n/a", "missing", "none", ""}:
        return None if value.lower() != "none" else "none"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def extract_section(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)",
        flags=re.MULTILINE,
    )
    match = pattern.search(markdown)
    return match.group(1).strip() if match else ""


def parse_key_value_bullets(section: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for line in section.splitlines():
        match = re.match(r"^-\s+(.+?):\s+(.+?)\s*$", line.strip())
        if not match:
            continue
        key = clean_cell(match.group(1)).lower().replace(" ", "_").replace("/", "_")
        values[key] = convert_scalar(match.group(2))
    return values


def parse_bullet_list(section: str) -> list[str]:
    items: list[str] = []
    for line in section.splitlines():
        match = re.match(r"^-\s+(.+?)\s*$", line.strip())
        if match:
            items.append(clean_cell(match.group(1)))
    return items


def parse_numbered_list(section: str) -> list[str]:
    items: list[str] = []
    for line in section.splitlines():
        match = re.match(r"^\d+\.\s+(.+?)\s*$", line.strip())
        if match:
            items.append(clean_cell(match.group(1)))
    return items


def parse_table(section: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return []
    headers = [clean_cell(cell) for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = [clean_cell(cell) for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, (convert_scalar(cell) for cell in cells))))
    return rows


def parse_family_cell(value: str) -> tuple[str, str | None]:
    match = re.match(r"`?([a-z0-9_]+)`?\s*(.*)$", value.strip())
    if not match:
        return clean_cell(value), None
    label = clean_cell(match.group(2)) or None
    return match.group(1), label


def parse_family_specs(markdown: str, errors: list[str]) -> dict[str, Any]:
    summary = parse_key_value_bullets(extract_section(markdown, "Summary"))
    family_rows = parse_table(extract_section(markdown, "Families"))
    if not summary or not family_rows:
        errors.append("Malformed family_recipe_specs.md: missing summary or families table")
    families: list[dict[str, Any]] = []
    compiler_counts: Counter[str] = Counter()
    readiness_counts: Counter[str] = Counter()
    for row in family_rows:
        family_key, label = parse_family_cell(row["Family"])
        missing = [item.strip() for item in row["Missing evidence"].split(";") if item.strip()]
        compiler = row["Compiler"]
        readiness = row["Readiness"]
        compiler_counts[compiler] += 1
        readiness_counts[readiness] += 1
        families.append(
            {
                "family": family_key,
                "label": label,
                "readiness": readiness,
                "compiler": compiler,
                "corpus": convert_scalar(row["Corpus"]),
                "role_map": convert_scalar(row["Role map"]),
                "one_click": convert_scalar(row["One-click"]),
                "source_bodies": convert_scalar(row["Source bodies"]),
                "next_priority": row["Next priority"],
                "missing_evidence": [] if row["Missing evidence"] == "none" else missing,
            }
        )
    return {
        "summary": summary,
        "readiness_counts": dict(sorted(readiness_counts.items())),
        "compiler_counts": dict(sorted(compiler_counts.items())),
        "families": families,
        "evidence_sources": parse_key_value_bullets(
            extract_section(markdown, "Evidence Sources")
        ),
    }


def parse_coverage(markdown: str, errors: list[str]) -> dict[str, Any]:
    summary = parse_key_value_bullets(extract_section(markdown, "Summary"))
    tier_counts = parse_key_value_bullets(extract_section(markdown, "Tier Counts"))
    rows = parse_table(extract_section(markdown, "Coverage Rows"))
    if not summary or not rows:
        errors.append("Malformed animation_family_coverage.md: missing summary or coverage table")
    coverage_rows: list[dict[str, Any]] = []
    for row in rows:
        family_key, label = parse_family_cell(row["Family"])
        coverage_rows.append(
            {
                "family": family_key,
                "label": label,
                "tier": row["Tier"],
                "recipe_spec": row["Recipe spec"],
                "next_template": row["Next template"],
                "evidence": row["Evidence"],
                "compiler": row["Compiler"],
                "corpus_counts": None if row["Corpus counts"] == "n/a" else row["Corpus counts"],
                "role_map": convert_scalar(row["Role map"]),
                "one_click": convert_scalar(row["One-click"]),
                "source_bodies": convert_scalar(row["Source bodies"]),
                "representative_animations": [
                    item.strip()
                    for item in row["Representative animations"].split(",")
                    if item.strip()
                ],
                "gaps_next_action": row["Gaps / next action"],
            }
        )
    return {
        "summary": summary,
        "tier_counts": tier_counts,
        "coverage_rows": coverage_rows,
        "evidence_sources": parse_bullet_list(extract_section(markdown, "Evidence Sources")),
        "notes": parse_bullet_list(extract_section(markdown, "Notes")),
    }


def parse_bakeoff(markdown: str, errors: list[str]) -> dict[str, Any]:
    result = parse_key_value_bullets(extract_section(markdown, "Result"))
    biggest_gaps = parse_bullet_list(extract_section(markdown, "Biggest Compiler Gaps"))
    family_findings = parse_bullet_list(extract_section(markdown, "Family Findings"))
    validation_runs = [
        item
        for item in parse_bullet_list(markdown)
        if item.startswith("closure_") or item.startswith("Run:")
    ]
    layered_table = parse_table(extract_section(markdown, "Layered Performance Composition Pass (2026-05-08)"))
    if not result or not biggest_gaps:
        errors.append("Malformed FULL_DEEP_ANIMATION_BAKEOFF_FINDINGS.md: missing result or gaps")
    return {
        "run": re.search(r"Generated from run `([^`]+)`", markdown).group(1)
        if re.search(r"Generated from run `([^`]+)`", markdown)
        else None,
        "result": result,
        "biggest_compiler_gaps": biggest_gaps,
        "family_findings": family_findings,
        "focused_validation_runs": validation_runs,
        "layered_performance_delta": layered_table,
        "next_critical_path": parse_numbered_list(extract_section(markdown, "Next Critical Path")),
    }


def parse_advanced_plan(markdown: str, errors: list[str]) -> dict[str, Any]:
    current_status = parse_bullet_list(extract_section(markdown, "Current Status"))
    areas: list[dict[str, Any]] = []
    area_pattern = re.compile(
        r"^### (.+?)\s*$([\s\S]*?)(?=^### |^## |\Z)",
        flags=re.MULTILINE,
    )
    for match in area_pattern.finditer(markdown):
        name = clean_cell(match.group(1))
        body = match.group(2)
        ready_lines: list[str] = []
        blocked_lines: list[str] = []
        active = "ready"
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if line.startswith("Still "):
                active = "blocked"
                continue
            if not line.startswith("- "):
                continue
            if active == "ready":
                ready_lines.append(clean_cell(line[2:]))
            else:
                blocked_lines.append(clean_cell(line[2:]))
        if ready_lines or blocked_lines:
            areas.append(
                {
                    "area": name,
                    "ready_or_concrete": ready_lines,
                    "blocked_or_review_gated": blocked_lines,
                }
            )
    if not current_status or not areas:
        errors.append("Malformed ADVANCED_SPINE_CAPABILITY_IMPLEMENTATION_PLAN.md")
    return {
        "current_status_artifacts": current_status,
        "gate_areas": areas,
        "next_production_steps": parse_numbered_list(
            extract_section(markdown, "Next Production Steps")
        ),
    }


def parse_contextual_layers(markdown: str, errors: list[str]) -> dict[str, Any]:
    summary = parse_key_value_bullets(extract_section(markdown, "Summary"))
    if not summary:
        errors.append("Malformed contextual_layer_interpretation.md: missing summary")
    return {
        "summary": summary,
        "semantic_role_counts": parse_key_value_bullets(
            extract_section(markdown, "Semantic Role Counts")
        ),
        "rig_role_counts": parse_key_value_bullets(extract_section(markdown, "Rig Role Counts")),
        "animation_use_counts": parse_key_value_bullets(
            extract_section(markdown, "Animation Use Counts")
        ),
        "low_confidence_layers": parse_bullet_list(
            extract_section(markdown, "Low-Confidence Layers")
        ),
        "per_symbol_recommendations": parse_table(
            extract_section(markdown, "Per-Symbol Recommendations")
        ),
        "recommended_next_compiler_changes": parse_bullet_list(
            extract_section(markdown, "Recommended Next Compiler Changes")
        ),
    }


def parse_ui_coverage(markdown: str, errors: list[str]) -> dict[str, Any]:
    headline = parse_key_value_bullets(extract_section(markdown, "Headline Counts"))
    if not headline:
        errors.append("Malformed ui_animation_classification.md: missing headline counts")
    return {
        "generated": re.search(r"Generated: `([^`]+)`", markdown).group(1)
        if re.search(r"Generated: `([^`]+)`", markdown)
        else None,
        "headline_counts": headline,
        "bucket_counts": parse_key_value_bullets(extract_section(markdown, "Bucket Counts")),
        "asset_bucket_counts": parse_key_value_bullets(
            extract_section(markdown, "Asset Bucket Counts")
        ),
        "animation_bucket_counts": parse_key_value_bullets(
            extract_section(markdown, "Animation Bucket Counts")
        ),
        "compendium_linked_asset_animation_counts": parse_key_value_bullets(
            extract_section(markdown, "Compendium-Linked Asset Animation Counts")
        ),
        "confidence_bands": parse_key_value_bullets(extract_section(markdown, "Confidence Bands")),
        "top_unresolved_examples": parse_bullet_list(
            extract_section(markdown, "Top Unresolved Examples")
        )[:12],
        "limitations": parse_bullet_list(extract_section(markdown, "Limitations")),
    }


def latest_compendium_markdown(root: Path) -> Path | None:
    runs_root = root / "generated" / "symbol_compendium_runs"
    candidates = sorted(
        runs_root.glob("*/symbol_animation_compendium.md"),
        key=lambda path: path.parent.name,
        reverse=True,
    )
    return candidates[0] if candidates else None


def parse_symbol_compendium(markdown: str, errors: list[str]) -> dict[str, Any]:
    summary = parse_key_value_bullets(extract_section(markdown, "Summary"))
    if not summary:
        errors.append("Malformed symbol_animation_compendium.md: missing summary")
    return {
        "generated": re.search(r"Generated: `([^`]+)`", markdown).group(1)
        if re.search(r"Generated: `([^`]+)`", markdown)
        else None,
        "summary": summary,
        "asset_categories": parse_key_value_bullets(extract_section(markdown, "Asset Categories")),
        "symbol_roles": parse_key_value_bullets(extract_section(markdown, "Symbol Roles")),
        "subject_types": parse_key_value_bullets(extract_section(markdown, "Subject Types")),
        "behavior_buckets": parse_key_value_bullets(extract_section(markdown, "Behavior Buckets")),
        "largest_games_by_asset_count": parse_bullet_list(
            extract_section(markdown, "Largest Games By Asset Count")
        )[:10],
        "alerts": parse_key_value_bullets(extract_section(markdown, "Alerts")),
        "human_review_games": parse_bullet_list(extract_section(markdown, "Human Review Games")),
    }


def summarize_motion_profile(profile: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(profile, dict):
        errors.append("Malformed latest_exact_motion_profile.json: expected JSON object")
        return {}
    roles = profile.get("roles")
    sample_counts = profile.get("sample_counts")
    if not isinstance(roles, dict) or not isinstance(sample_counts, dict):
        errors.append("Malformed latest_exact_motion_profile.json: missing roles/sample_counts")
        return {}
    return {
        "available": True,
        "schema": profile.get("schema"),
        "generated_at": profile.get("generated_at"),
        "source": profile.get("source"),
        "roles": sorted(roles),
        "sample_counts": sample_counts,
        "ranges_by_role": roles,
    }


def source_hash(sources: dict[str, dict[str, Any]]) -> str:
    payload = json.dumps(sources, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_query_indexes(
    family_specs: dict[str, Any],
    coverage: dict[str, Any],
    ui_coverage: dict[str, Any],
    contextual_layers: dict[str, Any],
    compendium_summary: dict[str, Any],
    motion_profile: dict[str, Any],
) -> dict[str, Any]:
    families_by_family: dict[str, dict[str, Any]] = {}
    recipes_by_family: dict[str, dict[str, Any]] = {}

    for family in family_specs.get("families", []):
        family_key = family["family"]
        families_by_family[family_key] = {
            "label": family.get("label"),
            "readiness": family.get("readiness"),
            "compiler": family.get("compiler"),
            "corpus": family.get("corpus"),
            "role_map": family.get("role_map"),
            "one_click": family.get("one_click"),
            "source_bodies": family.get("source_bodies"),
            "next_priority": family.get("next_priority"),
            "missing_evidence": family.get("missing_evidence", []),
        }
        recipes_by_family[family_key] = {
            "compiler": family.get("compiler"),
            "readiness": family.get("readiness"),
            "missing_evidence": family.get("missing_evidence", []),
        }

    for row in coverage.get("coverage_rows", []):
        family_key = row["family"]
        family_entry = families_by_family.setdefault(family_key, {})
        family_entry["tier"] = row.get("tier")
        family_entry["recipe_spec"] = row.get("recipe_spec")
        family_entry["representative_animations"] = row.get("representative_animations", [])
        family_entry["gaps_next_action"] = row.get("gaps_next_action")
        recipe_entry = recipes_by_family.setdefault(family_key, {})
        recipe_entry["recipe_spec"] = row.get("recipe_spec")
        recipe_entry["next_template"] = row.get("next_template")
        recipe_entry["representative_animations"] = row.get("representative_animations", [])

    roles_by_role: dict[str, dict[str, Any]] = {}
    for role, count in compendium_summary.get("symbol_roles", {}).items():
        roles_by_role.setdefault(role, {})["symbol_count"] = count
    for role, ranges in motion_profile.get("ranges_by_role", {}).items():
        roles_by_role.setdefault(role, {})["motion_ranges"] = ranges
    for role, count in contextual_layers.get("semantic_role_counts", {}).items():
        roles_by_role.setdefault(role, {})["semantic_layer_count"] = count
    for role, count in contextual_layers.get("rig_role_counts", {}).items():
        roles_by_role.setdefault(role, {})["rig_layer_count"] = count

    ui_buckets_by_bucket: dict[str, dict[str, Any]] = {}
    for section_name, field_name in (
        ("bucket_counts", "bucket_count"),
        ("asset_bucket_counts", "asset_count"),
        ("animation_bucket_counts", "animation_count"),
        ("compendium_linked_asset_animation_counts", "compendium_linked_count"),
    ):
        for bucket, count in ui_coverage.get(section_name, {}).items():
            ui_buckets_by_bucket.setdefault(bucket, {})[field_name] = count

    return {
        "families_by_family": dict(sorted(families_by_family.items())),
        "recipes_by_family": dict(sorted(recipes_by_family.items())),
        "roles_by_role": dict(sorted(roles_by_role.items())),
        "ui_buckets_by_bucket": dict(sorted(ui_buckets_by_bucket.items())),
    }


def build_index(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str]]:
    research_root = normalize_path(args.research_root)
    output_path = normalize_path(args.out)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        validate_research_root(research_root)
    except ValueError as exc:
        errors.append(str(exc))
        return {"sources": {}}, errors, warnings

    output_guard_error = write_guard_error(output_path, "output path")
    if output_guard_error:
        errors.append(output_guard_error)
    try:
        output_path.relative_to(PLUGIN_ROOT)
    except ValueError:
        errors.append(f"Output must stay inside plugin root: {output_path}")

    sources: dict[str, dict[str, Any]] = {}
    for name, rel_path in REQUIRED_SOURCES.items():
        record = source_record(research_root, rel_path, required=True, errors=errors, warnings=warnings)
        sources[name] = record
        if not record["exists"]:
            errors.append(f"Missing required source: {rel_path}")
    for name, rel_path in OPTIONAL_SOURCES.items():
        record = source_record(research_root, rel_path, required=False, errors=errors, warnings=warnings)
        sources[name] = record
        if not record["exists"]:
            warnings.append(f"Missing optional source: {rel_path}")

    if errors:
        return {"sources": sources}, errors, warnings

    family_specs_md = read_text(
        research_root, REQUIRED_SOURCES["family_recipe_specs"], errors
    )
    coverage_md = read_text(
        research_root, REQUIRED_SOURCES["animation_family_coverage"], errors
    )
    bakeoff_md = read_text(
        research_root, REQUIRED_SOURCES["full_deep_bakeoff_findings"], errors
    )
    advanced_md = read_text(
        research_root, REQUIRED_SOURCES["advanced_spine_capability_plan"], errors
    )
    motion_profile = read_json(
        research_root, REQUIRED_SOURCES["latest_exact_motion_profile"], errors, required=True
    )

    contextual_md = (
        read_text(
            research_root,
            OPTIONAL_SOURCES["contextual_layer_interpretation_md"],
            errors,
            required=False,
        )
        if sources["contextual_layer_interpretation_md"]["exists"]
        else None
    )
    ui_md = (
        read_text(
            research_root,
            OPTIONAL_SOURCES["ui_animation_classification_md"],
            errors,
            required=False,
        )
        if sources["ui_animation_classification_md"]["exists"]
        else None
    )

    compendium_path = latest_compendium_markdown(research_root)
    if compendium_path is None:
        warnings.append("Missing optional symbol compendium markdown summary")
        compendium_summary = {"available": False}
    else:
        ensure_under(compendium_path, research_root)
        compendium_rel = compendium_path.relative_to(research_root)
        sources["latest_symbol_compendium_md"] = {
            "path": str(compendium_rel).replace("\\", "/"),
            "required": False,
            "kind": "file",
            "exists": True,
            "status": "ok",
            "bytes": compendium_path.stat().st_size,
            "sha256": hash_file(compendium_path),
        }
        compendium_summary = parse_symbol_compendium(
            compendium_path.read_text(encoding="utf-8"), errors
        )

    family_specs = parse_family_specs(family_specs_md, errors)
    coverage = parse_coverage(coverage_md, errors)
    bakeoff = parse_bakeoff(bakeoff_md, errors)
    advanced_plan = parse_advanced_plan(advanced_md, errors)
    ui_coverage = (
        parse_ui_coverage(ui_md, errors)
        if ui_md is not None
        else {"available": False}
    )
    contextual_layers = (
        parse_contextual_layers(contextual_md, errors)
        if contextual_md is not None
        else {"available": False}
    )
    motion_profile_summary = summarize_motion_profile(motion_profile, errors)
    index_source_hash = source_hash(sources)

    index = {
        "schema": "claude_spine_compiler_evidence_index_v1",
        "generated_at": datetime.now(timezone.utc).isoformat()
        if args.stamp
        else f"source-sha256:{index_source_hash[:16]}",
        "source_hash": index_source_hash,
        "plugin_root": str(PLUGIN_ROOT),
        "research_root": str(research_root),
        "source_policy": {
            "allowed_roots": [str(research_root)],
            "prohibited_roots": ["G:/artSource", "G:\\artSource", "Perforce"],
            "rule": "Read only existing documented/generated H5G research outputs; never inspect artSource or write Perforce.",
        },
        "sources": sources,
        "warnings": warnings,
        "family_specs_summary": family_specs,
        "coverage_summary": coverage,
        "bakeoff_gap_summary": bakeoff,
        "advanced_gate_summary": advanced_plan,
        "ui_system_evidence_summary": ui_coverage,
        "contextual_layer_evidence_summary": contextual_layers,
        "symbol_compendium_summary": compendium_summary,
        "motion_profile_availability": motion_profile_summary,
        "query_indexes": build_query_indexes(
            family_specs,
            coverage,
            ui_coverage,
            contextual_layers,
            compendium_summary,
            motion_profile_summary,
        ),
    }
    return index, errors, warnings


def main() -> int:
    args = parse_args()
    index, errors, warnings = build_index(args)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        return 1

    output_path = normalize_path(args.out)
    output_guard_error = write_guard_error(output_path, "output path")
    if output_guard_error:
        print(f"ERROR: {output_guard_error}", file=sys.stderr)
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
