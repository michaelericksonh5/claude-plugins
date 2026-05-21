#!/usr/bin/env python3
"""Phase 8 UI/system template policy helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

POLICY_PATH = Path(__file__).resolve().parents[1] / "assets" / "ui_system_template_policy.json"
EVIDENCE_INDEX_PATH = Path(__file__).resolve().parents[1] / "assets" / "compiler_evidence_index.json"
EVIDENCE_INDEX_SCHEMA = "claude_spine_compiler_evidence_index_v1"
REVIEW_BUCKET_ALIASES = {"unknown": "unknown_ui_or_system"}
REVIEW_BUCKET_EVIDENCE_KEYS = {
    "button": ("interface_popups", "overlay_panel_popup_modal"),
    "row_blocker": ("row_blocker", "reel_row_grid_blocker_row_expanding_row"),
    "background_parallax": ("interface_ambients",),
    "foreground_overlay": ("interface_ambients", "overlay_panel_popup_modal"),
    "vfx_only": ("vfx_only",),
    "unknown": ("unknown_ui_or_system",),
    "unknown_ui_or_system": ("unknown_ui_or_system",),
}
REVIEW_BUCKET_RECIPE_KEYS = {
    "row_blocker": "blocker_or_bonus_symbol",
}


def load_policy(path: Path | None = None) -> dict:
    return json.loads((path or POLICY_PATH).read_text())


def load_evidence_index(path: Path | None = None) -> dict:
    return json.loads((path or EVIDENCE_INDEX_PATH).read_text())


def supported_template_families(policy: dict | None = None) -> set[str]:
    data = policy or load_policy()
    families = set()
    for template in data["supported_templates"].values():
        family = template.get("family")
        if family and family != "symbol_frame_glow":
            families.add(family)
    return families


def review_only_buckets(policy: dict | None = None) -> set[str]:
    data = policy or load_policy()
    return set(data["review_only_buckets"])


def evidence_index_status(evidence_index: dict | None) -> tuple[str, list[str]]:
    if not evidence_index:
        return "missing", ["assets/compiler_evidence_index.json is missing or unreadable"]
    issues = []
    if evidence_index.get("schema") != EVIDENCE_INDEX_SCHEMA:
        issues.append("compiler evidence index schema is not recognized")
    if not evidence_index.get("source_hash"):
        issues.append("compiler evidence index source_hash is missing")
    for name, source in evidence_index.get("sources", {}).items():
        if source.get("required") and (not source.get("exists") or source.get("status") != "ok"):
            issues.append(f"required evidence source {name!r} is not ok")
    return ("stale" if issues else "ok"), issues


def _load_evidence_index(path: Path | None) -> tuple[dict | None, str, list[str]]:
    try:
        evidence_index = load_evidence_index(path)
    except (OSError, json.JSONDecodeError):
        evidence_index = None
    status, issues = evidence_index_status(evidence_index)
    return evidence_index, status, issues


def _base_report(evidence_index: dict | None, status: str, issues: list[str]) -> dict[str, Any]:
    return {
        "evidence_index_path": "assets/compiler_evidence_index.json",
        "evidence_index_source_hash": evidence_index.get("source_hash") if evidence_index else None,
        "evidence_index_status": status,
        "ui_system_evidence_index_validation": {
            "status": status,
            "issues": list(issues),
        },
    }


def _recipe_evidence(evidence_index: dict | None, family: str) -> tuple[dict | None, list[str]]:
    recipe = (
        (evidence_index or {})
        .get("query_indexes", {})
        .get("recipes_by_family", {})
        .get(family)
    )
    issues = []
    if not recipe:
        issues.append(f"missing query_indexes.recipes_by_family.{family}")
        return None, issues
    if recipe.get("readiness") != "proof-ready":
        issues.append(f"recipe {family!r} readiness is {recipe.get('readiness')!r}")
    if recipe.get("compiler") not in {"implemented", "implemented_proof"}:
        issues.append(f"recipe {family!r} compiler is {recipe.get('compiler')!r}")
    return recipe, issues


def _ui_bucket_evidence(evidence_index: dict | None, bucket: str) -> tuple[dict | None, list[str]]:
    ui_bucket = (
        (evidence_index or {})
        .get("query_indexes", {})
        .get("ui_buckets_by_bucket", {})
        .get(bucket)
    )
    if not ui_bucket:
        return None, [f"missing query_indexes.ui_buckets_by_bucket.{bucket}"]
    return ui_bucket, []


def _policy_source_metadata(entry: dict) -> dict[str, Any]:
    return {
        "policy_evidence": list(entry.get("evidence", [])),
        "original_evidence": list(entry.get("original_evidence", [])),
        "original_source_paths": list(entry.get("original_source_paths", [])),
    }


def _supported_evidence(
    evidence_index: dict | None,
    family: str,
    recipe: dict | None,
    ui_bucket: dict | None,
    ui_bucket_key: str | None = None,
) -> list[str]:
    index_status, _issues = evidence_index_status(evidence_index)
    evidence = [
        "assets/compiler_evidence_index.json: "
        + f"source_hash={(evidence_index or {}).get('source_hash')} status={index_status}"
    ]
    if recipe:
        evidence.append(
            "assets/compiler_evidence_index.json: "
            + f"query_indexes.recipes_by_family.{family} "
            + f"readiness={recipe.get('readiness')} compiler={recipe.get('compiler')}"
        )
    if ui_bucket:
        bucket_key = ui_bucket_key or family
        evidence.append(
            "assets/compiler_evidence_index.json: "
            + f"query_indexes.ui_buckets_by_bucket.{bucket_key} "
            + f"bucket_count={ui_bucket.get('bucket_count')} "
            + f"animation_count={ui_bucket.get('animation_count')} "
            + f"asset_count={ui_bucket.get('asset_count')} "
            + f"compendium_linked_count={ui_bucket.get('compendium_linked_count')}"
        )
    return evidence


def _review_evidence(
    evidence_index: dict | None,
    canonical_family: str,
    buckets: tuple[str, ...],
) -> list[str]:
    index_status, _issues = evidence_index_status(evidence_index)
    evidence = [
        "assets/compiler_evidence_index.json: "
        + f"source_hash={(evidence_index or {}).get('source_hash')} status={index_status}"
    ]
    for bucket in buckets:
        ui_bucket, _issues = _ui_bucket_evidence(evidence_index, bucket)
        if ui_bucket:
            evidence.append(
                "assets/compiler_evidence_index.json: "
                + f"query_indexes.ui_buckets_by_bucket.{bucket} "
                + f"bucket_count={ui_bucket.get('bucket_count')} "
                + f"animation_count={ui_bucket.get('animation_count')} "
                + f"asset_count={ui_bucket.get('asset_count')} "
                + f"compendium_linked_count={ui_bucket.get('compendium_linked_count')}"
            )
    recipe_family = REVIEW_BUCKET_RECIPE_KEYS.get(canonical_family, canonical_family)
    recipe, _issues = _recipe_evidence(evidence_index, recipe_family)
    if recipe and recipe.get("compiler") == "unsupported":
        evidence.append(
            "assets/compiler_evidence_index.json: "
            + f"query_indexes.recipes_by_family.{recipe_family} "
            + f"readiness={recipe.get('readiness')} compiler={recipe.get('compiler')}"
        )
    return evidence


def _review_bucket_for_family(review_only: dict, family: str) -> tuple[str, dict] | tuple[None, None]:
    if family in review_only:
        return family, review_only[family]
    canonical = REVIEW_BUCKET_ALIASES.get(family)
    if canonical and canonical in review_only:
        return canonical, review_only[canonical]
    return None, None


def _detected_symbol_frame_glow_slots(layout: dict | None) -> list[str]:
    if not layout:
        return []
    roles = set(load_policy()["supported_templates"]["symbol_frame_glow"]["source_layer_roles"])
    return [
        slot["name"]
        for slot in layout.get("slots", [])
        if slot.get("semantic_role") in roles
    ]


def build_ui_system_report(
    family: str,
    layout: dict | None = None,
    compiler_supported: bool = True,
    policy: dict | None = None,
    evidence_index_path: Path | None = None,
) -> dict[str, Any]:
    policy = policy or load_policy()
    evidence_index, index_status, index_issues = _load_evidence_index(evidence_index_path)
    review_only = policy["review_only_buckets"]
    supported = policy["supported_templates"]
    base_report = _base_report(evidence_index, index_status, index_issues)

    review_key, bucket = _review_bucket_for_family(review_only, family)
    if bucket:
        canonical_family = REVIEW_BUCKET_ALIASES.get(family, family)
        evidence_buckets = REVIEW_BUCKET_EVIDENCE_KEYS.get(family, REVIEW_BUCKET_EVIDENCE_KEYS.get(canonical_family, (canonical_family,)))
        evidence_issues = list(index_issues)
        if bucket.get("status") != "review_only":
            evidence_issues.append(f"review-only bucket {review_key!r} has status {bucket.get('status')!r}")
        for evidence_bucket in evidence_buckets:
            _ui_bucket, bucket_issues = _ui_bucket_evidence(evidence_index, evidence_bucket)
            evidence_issues.extend(bucket_issues)
        evidence_status = "ok" if not evidence_issues else "missing"
        base_report["ui_system_evidence_index_validation"] = {
            "status": evidence_status if index_status == "ok" else index_status,
            "issues": evidence_issues,
        }
        return {
            **base_report,
            "ui_system_template": family,
            "ui_system_review_required": True,
            "ui_system_evidence": _review_evidence(evidence_index, canonical_family, evidence_buckets),
            "ui_system_evidence_source_metadata": _policy_source_metadata(bucket),
            "ui_system_unsupported_reason": bucket["unsupported_reason"],
        }

    if not compiler_supported:
        unknown = review_only["unknown_ui_or_system"]
        evidence_buckets = REVIEW_BUCKET_EVIDENCE_KEYS["unknown_ui_or_system"]
        evidence_issues = list(index_issues)
        for evidence_bucket in evidence_buckets:
            _ui_bucket, bucket_issues = _ui_bucket_evidence(evidence_index, evidence_bucket)
            evidence_issues.extend(bucket_issues)
        base_report["ui_system_evidence_index_validation"] = {
            "status": "ok" if not evidence_issues else index_status if index_status != "ok" else "missing",
            "issues": evidence_issues,
        }
        return {
            **base_report,
            "ui_system_template": "unknown_ui_or_system",
            "ui_system_review_required": True,
            "ui_system_evidence": _review_evidence(evidence_index, "unknown_ui_or_system", evidence_buckets),
            "ui_system_evidence_source_metadata": _policy_source_metadata(unknown),
            "ui_system_unsupported_reason": (
                f"Family {family!r} has no deterministic compiler template; "
                + unknown["unsupported_reason"]
            ),
        }

    for template_name, template in supported.items():
        if template.get("family") == family:
            recipe, recipe_issues = _recipe_evidence(evidence_index, family)
            ui_bucket, bucket_issues = _ui_bucket_evidence(evidence_index, family)
            evidence_issues = list(index_issues) + recipe_issues + bucket_issues
            validation_status = "ok" if not evidence_issues else index_status if index_status != "ok" else "missing"
            base_report["ui_system_evidence_index_validation"] = {
                "status": validation_status,
                "issues": evidence_issues,
            }
            evidence = _supported_evidence(evidence_index, family, recipe, ui_bucket)
            if evidence_issues:
                return {
                    **base_report,
                    "ui_system_template": template_name,
                    "ui_system_review_required": True,
                    "ui_system_evidence": evidence,
                    "ui_system_evidence_source_metadata": _policy_source_metadata(template),
                    "ui_system_unsupported_reason": (
                        f"Family {family!r} cannot be proof-compiled because "
                        "assets/compiler_evidence_index.json did not validate: "
                        + "; ".join(evidence_issues)
                    ),
                }
            return {
                **base_report,
                "ui_system_template": template_name,
                "ui_system_review_required": False,
                "ui_system_evidence": evidence,
                "ui_system_evidence_source_metadata": _policy_source_metadata(template),
                "ui_system_unsupported_reason": None,
            }

    symbol_template = supported["symbol_frame_glow"]
    if family in symbol_template["applies_to_families"]:
        detected_slots = _detected_symbol_frame_glow_slots(layout)
        if detected_slots:
            recipe, recipe_issues = _recipe_evidence(evidence_index, family)
            ui_bucket, bucket_issues = _ui_bucket_evidence(evidence_index, "symbol_family_reference")
            evidence_issues = list(index_issues) + recipe_issues + bucket_issues
            validation_status = "ok" if not evidence_issues else index_status if index_status != "ok" else "missing"
            base_report["ui_system_evidence_index_validation"] = {
                "status": validation_status,
                "issues": evidence_issues,
            }
            evidence = _supported_evidence(
                evidence_index,
                family,
                recipe,
                ui_bucket,
                ui_bucket_key="symbol_family_reference",
            )
            evidence.append("detected source slots: " + ", ".join(detected_slots))
            if evidence_issues:
                return {
                    **base_report,
                    "ui_system_template": "symbol_frame_glow",
                    "ui_system_review_required": True,
                    "ui_system_evidence": evidence,
                    "ui_system_evidence_source_metadata": _policy_source_metadata(symbol_template),
                    "ui_system_unsupported_reason": (
                        f"Family {family!r} symbol frame/glow evidence did not validate: "
                        + "; ".join(evidence_issues)
                    ),
                }
            return {
                **base_report,
                "ui_system_template": "symbol_frame_glow",
                "ui_system_review_required": False,
                "ui_system_evidence": evidence,
                "ui_system_evidence_source_metadata": _policy_source_metadata(symbol_template),
                "ui_system_unsupported_reason": None,
            }

    return {
        **base_report,
        "ui_system_template": None,
        "ui_system_review_required": False,
        "ui_system_evidence": [],
        "ui_system_evidence_source_metadata": {},
        "ui_system_unsupported_reason": None,
    }
