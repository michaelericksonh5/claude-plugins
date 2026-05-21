#!/usr/bin/env python3
"""Generate report-only rig proposals from interpreted layer evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_INDEX = PLUGIN_ROOT / "assets" / "h5g_corpus_distilled_evidence.json"
DEFORMING_ROLES = {
    "antenna",
    "arm",
    "cape",
    "character_body",
    "cloth",
    "dress",
    "earring",
    "hair",
    "jewelry",
    "ribbon",
    "robe",
    "scarf",
    "sleeve",
    "tail",
    "tentacle",
    "wing",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a report-only rig proposal. This never emits Spine output."
    )
    parser.add_argument("--family", default="hp_symbol")
    parser.add_argument("--layer-interpretation", type=Path)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _first_string(record: dict[str, Any], keys: tuple[str, ...], default: str) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return default


def _confidence(record: dict[str, Any]) -> float:
    value = record.get("confidence")
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    return 0.5


def extract_layers(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("layers", "interpretations", "entries", "layer_interpretations"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    symbols = payload.get("symbols")
    if isinstance(symbols, list):
        layers: list[dict[str, Any]] = []
        for symbol in symbols:
            if isinstance(symbol, dict):
                layers.extend(extract_layers(symbol))
        return layers
    return []


def _gate(status: str, required_evidence: list[str]) -> dict[str, Any]:
    return {"status": status, "required_evidence": required_evidence}


def _evidence_id(evidence_index: dict[str, Any], key: str) -> str:
    indexes = evidence_index.get("query_indexes", {}) if isinstance(evidence_index, dict) else {}
    evidence_ids = indexes.get("evidence_ids", {}) if isinstance(indexes, dict) else {}
    value = evidence_ids.get(key) if isinstance(evidence_ids, dict) else None
    return value if isinstance(value, str) and value else "assets/h5g_corpus_distilled_evidence.json:unknown"


def _coverage_status(evidence_index: dict[str, Any]) -> str:
    if not isinstance(evidence_index, dict):
        return "unknown"
    coverage = evidence_index.get("coverage", {})
    if isinstance(coverage, dict) and isinstance(coverage.get("status"), str):
        return coverage["status"]
    return str(evidence_index.get("production_claim", evidence_index.get("status", "unknown")))


def build_proposal(
    *,
    family: str,
    layers: list[dict[str, Any]],
    evidence_index: dict[str, Any],
) -> dict[str, Any]:
    region_decisions: list[dict[str, Any]] = []
    mesh_decisions: list[dict[str, Any]] = []
    review_reasons: list[str] = [
        "Report-only proposal; deterministic compiler output and artist review are still required."
    ]
    confidence_basis = [
        "Layer semantic roles and confidence are treated as proposal evidence, not approval.",
        "H5G corpus evidence separates proof support from production rigging claims.",
    ]

    for idx, layer in enumerate(layers):
        name = _first_string(layer, ("layer", "name", "safe_name", "source_layer"), f"layer_{idx}")
        semantic_role = _first_string(layer, ("semantic_role", "role", "rig_role"), "unknown")
        confidence = _confidence(layer)
        if confidence < 0.7:
            review_reasons.append(f"{name}: low confidence semantic interpretation ({confidence:.2f}).")
        if semantic_role in DEFORMING_ROLES:
            mesh_decisions.append(
                {
                    "layer": name,
                    "attachment_type": "mesh_candidate",
                    "confidence": min(confidence, 0.65),
                    "review_required": True,
                    "review_reasons": [
                        f"{semantic_role} may need bending or secondary motion.",
                        "Topology, weights, prune settings, and extreme-pose behavior need Spine review.",
                    ],
                    "weight_strategy": "first_pass_review_only",
                    "deform_strategy": "avoid_deform_keys_until_reviewed_corrective_case",
                }
            )
        else:
            region_decisions.append(
                {
                    "layer": name,
                    "attachment_type": "region",
                    "confidence": confidence,
                    "reason": f"{semantic_role} can remain a region unless animator review proves deformation is needed.",
                }
            )

    if family == "avatar":
        review_reasons.append(
            "Avatar corpus evidence includes state graphs, attachment/color timelines, and deform-heavy references; current support is proof-only."
        )
    if mesh_decisions:
        review_reasons.append("Mesh candidates require Chris-approved topology and parity fixtures before production use.")
    if not layers:
        review_reasons.append("No layer interpretation was supplied; proposal contains only global gates.")

    coverage_status = _coverage_status(evidence_index)
    return {
        "schema": "spine_slot_animation_rig_proposal_v1",
        "proposal_mode": "report_only",
        "production_output_claimed": False,
        "asset": {
            "family": family,
            "source_summary": f"{len(layers)} interpreted layer(s); evidence coverage status: {coverage_status}",
        },
        "evidence_support": {
            "evidence_index": "assets/h5g_corpus_distilled_evidence.json",
            "support_status": coverage_status,
            "evidence_ids": [
                _evidence_id(evidence_index, "family_contracts"),
                _evidence_id(evidence_index, "role_motion"),
                _evidence_id(evidence_index, "rig_slot_layer_roles"),
                _evidence_id(evidence_index, "mesh_weight_deform"),
                _evidence_id(evidence_index, "production_boundaries"),
                _evidence_id(evidence_index, "known_gaps"),
            ],
        },
        "confidence": {
            "overall": 0.0 if not layers else round(sum(_confidence(layer) for layer in layers) / len(layers), 3),
            "basis": confidence_basis,
            "review_reasons": review_reasons,
        },
        "region_decisions": region_decisions,
        "mesh_decisions": mesh_decisions,
        "review": {
            "required": True,
            "reasons": review_reasons,
            "approved_by": None,
        },
        "policy_gates": {
            "spine_auto_weight_parity_fixture": _gate(
                "missing",
                ["Same source mesh compared against Spine Auto weights and plugin first-pass weights."],
            ),
            "chris_approved_mesh_fixture": _gate(
                "missing",
                ["Chris-approved topology, edges, weights, and extreme-pose screenshots."],
            ),
            "avatar_runtime_state_contract": _gate(
                "manual_review_required",
                ["Game-runtime owner verifies persistent avatar state and event consumption."],
            ),
            "production_export_policy": _gate(
                "blocked",
                ["Approved production export profile and browser-runtime evidence; CLI export still manual."],
            ),
            "target_runtime_acceptance": _gate(
                "missing",
                ["Target game runtime proof, not just Spine Player preview."],
            ),
            "final_autonomous_rigger_claim": _gate(
                "blocked",
                ["All parity fixtures, runtime proof, export policy, and art approval must be verified."],
            ),
        },
        "source_policy": {
            "allowed_inputs": ["approved manifests", "transparent PNG layers", "bundled distilled H5G corpus evidence"],
            "prohibited_writes": ["G:/artSource", "G:\\artSource", "Perforce"],
            "external_code_policy": "Genielabs concepts may inform review questions; PolyForm Noncommercial code must not be copied or embedded.",
        },
    }


def main() -> int:
    args = parse_args()
    layer_payload = load_json(args.layer_interpretation) if args.layer_interpretation else None
    evidence_index = load_json(args.evidence_index)
    proposal = build_proposal(
        family=args.family,
        layers=extract_layers(layer_payload),
        evidence_index=evidence_index,
    )
    out_path = ensure_safe_write_path(args.out, "rig proposal output path")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote report-only rig proposal to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
