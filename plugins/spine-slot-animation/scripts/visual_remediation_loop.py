#!/usr/bin/env python3
"""Create and apply structured visual remediation reports for Spine packages.

This is the bridge between "Claude can see the preview" and deterministic
compiler changes. The script does not pretend to judge art by itself. It gives
Claude or an animator a closed vocabulary for visual findings, maps safe
findings to bounded recipe controls, and blocks issues that need rig/compiler
work instead of smuggling them into unsupported controls.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from source_art_guard import ensure_safe_write_path

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA = "spine_slot_animation_visual_remediation_report_v1"
PACKET_SCHEMA = "spine_slot_animation_visual_remediation_packet_v1"

CONTROL_DEFAULTS = {
    "bounce_strength": 1.0,
    "land_duration_scale": 1.0,
    "idle_duration_scale": 1.0,
    "glow_intensity": 1.0,
    "sparkle_intensity": 1.0,
    "premium_intensity": 1.0,
    "motion_strength": 1.0,
    "feature_active_intensity": 1.0,
}

CONTROL_RANGES = {
    "bounce_strength": (0.0, 2.0),
    "land_duration_scale": (0.25, 3.0),
    "idle_duration_scale": (0.25, 3.0),
    "glow_intensity": (0.0, 2.0),
    "sparkle_intensity": (0.0, 2.0),
    "premium_intensity": (0.0, 2.0),
    "motion_strength": (0.0, 2.0),
    "feature_active_intensity": (0.0, 2.0),
}

CONTROL_FIXES = {
    "too_flashy": {"glow_intensity": -0.25, "sparkle_intensity": -0.25, "premium_intensity": -0.2},
    "not_flashy_enough": {"glow_intensity": 0.2, "sparkle_intensity": 0.2, "premium_intensity": 0.15},
    "too_bouncy": {"bounce_strength": -0.25, "land_duration_scale": -0.1, "motion_strength": -0.15},
    "not_bouncy_enough": {"bounce_strength": 0.25, "land_duration_scale": 0.1, "motion_strength": 0.15},
    "idle_too_fast": {"idle_duration_scale": 0.2},
    "idle_too_slow": {"idle_duration_scale": -0.2},
    "motion_too_strong": {"motion_strength": -0.2, "bounce_strength": -0.1},
    "motion_too_subtle": {"motion_strength": 0.2, "bounce_strength": 0.1},
    "feature_active_too_strong": {"feature_active_intensity": -0.2},
    "feature_active_too_subtle": {"feature_active_intensity": 0.2},
}

BLOCKING_CODES = {
    "missing_attachment": "Fix package validation or atlas packing before visual remediation.",
    "broken_preview": "Fix preview/runtime loading before judging motion.",
    "off_center": "Fix source-layer placement, doc dimensions, or rig layout; controls cannot recenter art safely.",
    "wrong_z_order": "Fix layer order or slot ordering; controls cannot repair draw order.",
    "expression_visible_at_rest": "Fix overlay setup alpha/attachment polarity in the compiler or source layers.",
    "expression_wrong_timing": "Requires expression timeline/compiler work or a reviewed event/timing plan.",
    "mesh_tearing": "Requires reviewed mesh topology/weights; do not hide with motion controls.",
    "rubbery_weights": "Requires weight-painting or auto-weight policy review.",
    "deform_needed": "Requires a reviewed mesh/deform decision; deform remains gated.",
    "linked_mesh_needed": "Requires a reviewed linked-mesh/skin variant implementation.",
    "path_constraint_needed": "Requires reviewed path-constraint support; not a bounded control fix.",
    "bad_silhouette": "Usually a rig/layout/mesh issue; requires visual review before controls.",
    "style_mismatch": "Requires art direction or recipe/template change; bounded controls may be insufficient.",
}

VISUAL_REVIEW_TEMPLATE = {
    "schema": "spine_slot_animation_visual_review_v1",
    "reviewer": "claude_or_artist",
    "package": "<path to compiled package>",
    "issues": [
        {
            "code": "too_flashy",
            "severity": "warn",
            "animation": "win",
            "evidence": "Glow overwhelms the symbol at win peak.",
        }
    ],
}

RUBRIC = [
    "Open preview.html and inspect setup/default, idle/breathe, land, win/smart, and any __mesh_weight_test animation.",
    "Check centering, missing parts, slot order, expression overlays hidden at rest, and readable silhouette.",
    "Check whether motion is too strong/subtle, too flashy/dull, too bouncy/flat, or idle timing feels wrong.",
    "For mesh/weights, look for tearing, rubbery bends, collapsing silhouettes, or vertices lagging the wrong bone.",
    "Record findings using the closed issue codes so safe fixes become controls and unsafe fixes stay blocked.",
]


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _clamp_control(name: str, value: float) -> float:
    low, high = CONTROL_RANGES[name]
    return round(max(low, min(high, value)), 3)


def _load_base_controls(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("base controls must be a JSON object")
    return data


def build_packet(package_dir: Path, out_dir: Path, *, render_frames: bool = False) -> dict[str, Any]:
    package_dir = package_dir.resolve()
    out_dir = ensure_safe_write_path(out_dir.resolve(), "visual remediation output directory")
    out_dir.mkdir(parents=True, exist_ok=True)

    if render_frames:
        frame_dir = out_dir / "frames"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "render_preview_frames.py"),
                str(package_dir),
                "--out-dir",
                str(frame_dir),
            ],
            check=True,
        )

    validation_report = _read_json_if_exists(package_dir / "validation_report.json")
    qa_report = _read_json_if_exists(out_dir / "frames" / "qa_report.json")
    packet = {
        "schema": PACKET_SCHEMA,
        "package_dir": str(package_dir),
        "preview_html": str(package_dir / "preview.html") if (package_dir / "preview.html").is_file() else None,
        "validation_report": str(package_dir / "validation_report.json")
        if (package_dir / "validation_report.json").is_file()
        else None,
        "qa_report": str(out_dir / "frames" / "qa_report.json")
        if (out_dir / "frames" / "qa_report.json").is_file()
        else None,
        "frames": qa_report.get("frames", []),
        "animations": qa_report.get("animations_in_package")
        or list(_read_json_if_exists(package_dir / "shared_symbols.json").get("animations", {}).keys()),
        "mesh_review_required": bool(validation_report.get("weighted_mesh_review_required")),
        "mesh_review_reason": validation_report.get("weighted_mesh_review_required_reason"),
        "rubric": RUBRIC,
        "supported_control_issue_codes": sorted(CONTROL_FIXES),
        "blocking_issue_codes": sorted(BLOCKING_CODES),
        "visual_review_template": VISUAL_REVIEW_TEMPLATE,
        "next_step": (
            "Claude or the animator should inspect preview.html/frames, write a visual_review JSON "
            "with the closed issue codes, then run this script with --review."
        ),
    }
    (out_dir / "visual_remediation_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (out_dir / "VISUAL_REMEDIATION_PROMPT.md").write_text(_prompt_text(packet), encoding="utf-8")
    return packet


def _prompt_text(packet: dict[str, Any]) -> str:
    codes = "\n".join(f"- `{code}`" for code in packet["supported_control_issue_codes"])
    blockers = "\n".join(f"- `{code}`" for code in packet["blocking_issue_codes"])
    return f"""# Visual Remediation Review

Open the preview and inspect the package visually. Do not answer pass/fail only.
Record concrete issues in `visual_review.json`, then run `visual_remediation_loop.py --review`.

Preview: `{packet.get("preview_html")}`
Frames/report: `{packet.get("qa_report")}`

## Safe Control Issue Codes

These can become bounded compiler controls:

{codes}

## Blocking Issue Codes

These require rig/compiler/source-art work and must not be hidden with controls:

{blockers}

## Review JSON Template

```json
{json.dumps(VISUAL_REVIEW_TEMPLATE, indent=2)}
```
"""


def remediate_review(review_path: Path, out_dir: Path, *, base_controls: Path | None = None) -> dict[str, Any]:
    out_dir = ensure_safe_write_path(out_dir.resolve(), "visual remediation output directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    issues = review.get("issues")
    if not isinstance(issues, list):
        raise ValueError("visual review must contain an issues array")

    controls = _load_base_controls(base_controls)
    suggestions = {k: float(controls.get(k, v)) for k, v in CONTROL_DEFAULTS.items()}
    blocking: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []

    for issue in issues:
        if not isinstance(issue, dict):
            unknown.append({"issue": issue, "reason": "issue must be an object"})
            continue
        code = str(issue.get("code", ""))
        if code in CONTROL_FIXES:
            deltas = CONTROL_FIXES[code]
            before = {name: suggestions[name] for name in deltas}
            for name, delta in deltas.items():
                suggestions[name] = _clamp_control(name, suggestions[name] + delta)
            applied.append({
                "code": code,
                "animation": issue.get("animation"),
                "severity": issue.get("severity", "warn"),
                "evidence": issue.get("evidence", ""),
                "before": before,
                "after": {name: suggestions[name] for name in deltas},
            })
        elif code in BLOCKING_CODES:
            blocking.append({
                "code": code,
                "animation": issue.get("animation"),
                "severity": issue.get("severity", "fail"),
                "evidence": issue.get("evidence", ""),
                "required_action": BLOCKING_CODES[code],
            })
        else:
            unknown.append({
                "code": code,
                "animation": issue.get("animation"),
                "evidence": issue.get("evidence", ""),
                "reason": "unknown visual issue code; update the remediation taxonomy before acting",
            })

    controls_out = {
        key: value
        for key, value in suggestions.items()
        if key in CONTROL_RANGES and abs(value - CONTROL_DEFAULTS[key]) > 0.0001
    }
    if review.get("recipe_type"):
        controls_out["recipe_type"] = review["recipe_type"]

    if blocking or unknown:
        status = "blocked"
    elif applied:
        status = "controls_ready_for_recompile"
    else:
        status = "no_visual_issues_reported"

    report = {
        "schema": SCHEMA,
        "status": status,
        "review": str(review_path),
        "applied_control_fixes": applied,
        "blocking_issues": blocking,
        "unknown_issues": unknown,
        "suggested_controls": controls_out,
        "controls_file": str(out_dir / "visual_remediation.controls.json") if controls_out else None,
        "next_step": _next_step(status),
        "approval_boundary": (
            "This is Claude/artist visual QA remediation, not final production art approval. "
            "Chris or an assigned art owner still owns final signoff."
        ),
    }

    if controls_out:
        (out_dir / "visual_remediation.controls.json").write_text(
            json.dumps(controls_out, indent=2),
            encoding="utf-8",
        )
    (out_dir / "visual_remediation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _next_step(status: str) -> str:
    if status == "controls_ready_for_recompile":
        return "Recompile with visual_remediation.controls.json, rebuild preview, then create a new packet/review iteration."
    if status == "blocked":
        return "Fix blocking rig/compiler/source-art issues first, then rerender before applying cosmetic controls."
    return "No remediation controls are required from the submitted visual review."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or apply a visual remediation loop for a Spine package.")
    parser.add_argument("--package-dir", type=Path, help="Compiled package directory.")
    parser.add_argument("--review", type=Path, help="Structured visual_review JSON to convert into remediation.")
    parser.add_argument("--base-controls", type=Path, help="Optional existing controls JSON to adjust.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory for packet/report/controls.")
    parser.add_argument("--render-frames", action="store_true", help="Run render_preview_frames.py into the packet folder.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if bool(args.package_dir) == bool(args.review):
        raise SystemExit("provide exactly one of --package-dir or --review")
    if args.package_dir:
        packet = build_packet(args.package_dir, args.out_dir, render_frames=args.render_frames)
        print(json.dumps(packet, indent=2))
    else:
        report = remediate_review(args.review, args.out_dir, base_controls=args.base_controls)
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
