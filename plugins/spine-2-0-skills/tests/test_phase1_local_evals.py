#!/usr/bin/env python3
"""Local Phase 1 evals with self-contained PNG fixtures."""

from __future__ import annotations

import json
import hashlib
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
BUILD_SCRIPT = SCRIPTS_DIR / "build_spine_package.py"
EVAL_17_NAME = "eval-17-sequence-auto-emission"
EVAL_18_NAME = "eval-18-mesh-plan-emission"
EVAL_19_NAME = "eval-19-auto-bind-weighted-mesh"
EVAL_20_NAME = "eval-20-multi-skin-variants"
EVAL_21_NAME = "eval-21-bezier-modern-profile"
EVAL_22_NAME = "eval-22-ui-frame-ambient-loop"
EVAL_23_NAME = "eval-23-background-parallax-ambient"
EVAL_24_NAME = "eval-24-character-wardrobe-physics"
EVAL_25_NAME = "eval-25-expression-atlas-variants"
EVAL_26_NAME = "eval-26-avatar-state-manifest"
EVAL_27_NAME = "eval-27-phase-9-safety"
EVAL_28_NAME = "eval-28-production-export-gate"
EVAL_29_NAME = "eval-29-loop-closure-validation"
EVAL_30_NAME = "eval-30-automatic-weighted-mesh"
EVAL_31_NAME = "eval-31-spine-cli-reference"
EVAL_32_NAME = "eval-32-autonomous-rigging-proposals"
EVAL_33_NAME = "eval-33-bundled-corpus-evidence-pack"
EVAL_34_NAME = "eval-34-h5g-corpus-bakeoff-resolver"
EVAL_35_NAME = "eval-35-visual-remediation-loop"
EVAL_36_NAME = "eval-36-mesh-weight-parity-fixtures"
EVAL_37_NAME = "eval-37-avatar-runtime-contract"

sys.path.insert(0, str(SCRIPTS_DIR))


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, color: tuple[int, int, int, int]) -> None:
    rows = []
    pixel = bytes(color)
    for _ in range(height):
        rows.append(b"\x00" + pixel * width)
    data = b"".join(rows)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(data))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def run_builder(layer_dir: Path, out_dir: Path, *extra_args: str, family: str = "hp_symbol") -> subprocess.CompletedProcess[str]:
    result = run_builder_raw(layer_dir, out_dir, *extra_args, family=family)
    if result.returncode != 0:
        raise AssertionError(
            f"builder failed with {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def run_builder_raw(layer_dir: Path, out_dir: Path, *extra_args: str, family: str = "hp_symbol") -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(BUILD_SCRIPT),
        "--layer-dir",
        str(layer_dir),
        "--family",
        family,
        "--rank",
        "3",
        "--doc-width",
        "64",
        "--doc-height",
        "64",
        "--no-context",
        "--out-dir",
        str(out_dir),
        *extra_args,
    ]
    return subprocess.run(cmd, cwd=PLUGIN_ROOT, capture_output=True, text=True)


def load_package(out_dir: Path) -> tuple[dict, str, dict]:
    skel = json.loads((out_dir / "shared_symbols.json").read_text())
    atlas = (out_dir / "shared_symbols.atlas").read_text()
    report = json.loads((out_dir / "validation_report.json").read_text())
    return skel, atlas, report


def skin_attachments(skel: dict) -> dict:
    return skel["skins"][0]["attachments"]


def mesh_plan_attachment(**overrides: object) -> dict:
    attachment = {
        "reviewed": True,
        "source_layer": "HP3_body.png",
        "target_slot": "HP3_body_slot",
        "hull_vertices": [[-8, -8], [8, -8], [8, 8], [-8, 8]],
        "interior_vertices": [],
        "triangles": [0, 1, 2, 0, 2, 3],
        "uvs": [[0, 0], [1, 0], [1, 1], [0, 1]],
        "hull_count": 4,
        "max_vertex_budget": 8,
    }
    attachment.update(overrides)
    return attachment


def write_mesh_plan(path: Path, **overrides: object) -> None:
    attachment = mesh_plan_attachment(**overrides)
    path.write_text(json.dumps({
        "schema": "spine_slot_animation_mesh_plan_v1",
        "max_vertex_budget": 8,
        "attachments": [attachment],
    }, indent=2))


def read_mesh_plan(path: Path) -> dict:
    return json.loads(path.read_text())


def write_skin_plan(path: Path, skins: list[dict]) -> None:
    path.write_text(json.dumps({
        "schema": "spine_slot_animation_skin_plan_v1",
        "skins": skins,
    }, indent=2))


def skin_by_name(skel: dict, name: str) -> dict:
    return next(skin for skin in skel["skins"] if skin["name"] == name)


def write_physics_plan(path: Path, entries: list[dict]) -> None:
    path.write_text(json.dumps(entries, indent=2))


def write_controls(path: Path, controls: dict) -> None:
    path.write_text(json.dumps(controls, indent=2))


def write_event_plan(path: Path, plan: dict) -> None:
    path.write_text(json.dumps(plan, indent=2))


def write_production_gate_validation_report(path: Path, **overrides: object) -> None:
    report = {
        "status": "ok",
        "skin_variants_emitted": 0,
        "physics_constraints_emitted": 0,
        "sequence_attachments_emitted": 0,
        "clipping_attachments_emitted": 0,
        "events_defined": 0,
    }
    report.update(overrides)
    path.write_text(json.dumps(report, indent=2))


def production_gate_package_identity(package_dir: Path) -> dict:
    identity = {}
    for name in ("shared_symbols.json", "shared_symbols.atlas", "shared_symbols.png"):
        identity[name] = {"sha256": hashlib.sha256((package_dir / name).read_bytes()).hexdigest()}
    return identity


def write_production_gate_package_artifacts(package_dir: Path) -> None:
    (package_dir / "shared_symbols.json").write_text(json.dumps({
        "skeleton": {"spine": "4.3.04"},
        "bones": [{"name": "root"}],
        "slots": [],
        "skins": [{"name": "default", "attachments": {}}],
        "animations": {},
    }, indent=2))
    (package_dir / "shared_symbols.atlas").write_text("shared_symbols.png\nsize: 16,16\nformat: RGBA8888\n")
    write_rgba_png(package_dir / "shared_symbols.png", 16, 16, (120, 80, 40, 255))


def write_runtime_acceptance_evidence(
    path: Path,
    package_identity: dict | None = None,
    provenance: dict | None = None,
    **feature_overrides: bool,
) -> None:
    features = {
        "skins": True,
        "physics": False,
        "sequences": False,
        "clipping": False,
        "events": False,
        "blends": False,
    }
    features.update(feature_overrides)
    path.write_text(json.dumps({
        "schema": "spine_slot_animation_runtime_acceptance_evidence_v1",
        "runtime_name": "@esotericsoftware/spine-player",
        "runtime_version": "4.3.1",
        "provenance": provenance or {
            "method": "runtime_probe",
            "tool": "h5g-runtime-acceptance-probe",
            "tool_version": "runtime-acceptance-probe-v1",
            "execution_mode": "browser_runtime",
            "execution_id": "local-eval-runtime-probe-001",
            "executed_at": "2026-05-18T12:20:00-04:00",
        },
        "package_loaded": True,
        "features_loaded": features,
        "package_identity": package_identity,
    }, indent=2))


def production_export_profile(**overrides: object) -> dict:
    profile = {
        "schema": "spine_slot_animation_production_export_profile_v1",
        "spine_editor_version": "4.3.04",
        "spine_cli_version": "4.3.04",
        "runtime": {
            "name": "@esotericsoftware/spine-player",
            "version": "4.3.1",
        },
        "output_format": {
            "decision": "json",
            "rationale": "Keep handoff review in readable JSON until production export is approved.",
        },
        "license_posture": {
            "approved": True,
            "approval_ticket": "ART-EXPORT-10",
            "approved_by": "Tools Lead",
            "approved_at": "2026-05-18T12:00:00-04:00",
        },
        "write_policy": {
            "perforce_writes": False,
            "source_art_writes": False,
        },
        "advanced_features": {
            "claimed_counts": {
                "skins": 0,
                "physics": 0,
                "sequences": 0,
                "clipping": 0,
                "events": 0,
                "blends": 0,
            },
        },
        "runtime_acceptance_evidence": "runtime_acceptance.json",
        "approver": {
            "name": "Christian",
            "role": "Art Director",
            "approved_at": "2026-05-18T12:10:00-04:00",
            "approval_ticket": "ART-EXPORT-10",
        },
        "production_export_approval": {
            "manual_export_approved": True,
            "cli_invocation_approved": False,
        },
    }
    profile.update(overrides)
    return profile


def write_avatar_state_layers(layer_dir: Path) -> None:
    for name, color in (
        ("State0Idle.png", (40, 80, 140, 255)),
        ("State0to1.png", (80, 120, 180, 255)),
        ("State1Idle.png", (100, 160, 80, 255)),
        ("State1Awarded.png", (220, 190, 60, 255)),
        ("State1Close.png", (120, 90, 50, 255)),
    ):
        write_rgba_png(layer_dir / name, 16, 16, color)


def iter_curve_entries(skel: dict):
    for anim in skel.get("animations", {}).values():
        for tracks in anim.get("bones", {}).values():
            for timeline_name, keys in tracks.items():
                for key in keys:
                    if "curve" in key:
                        yield timeline_name, key["curve"]
        for tracks in anim.get("slots", {}).values():
            for timeline_name, keys in tracks.items():
                for key in keys:
                    if "curve" in key:
                        yield timeline_name, key["curve"]


def atlas_records_from_skeleton(skel: dict) -> list[dict]:
    records = []
    for slot_attachments in skin_attachments(skel).values():
        for att_name, att in slot_attachments.items():
            path = att.get("path", att_name)
            if "sequence" not in att:
                records.append({"name": path})
    return records


def assert_portable_ui_evidence(test_case: unittest.TestCase, report: dict) -> None:
    test_case.assertEqual(report["evidence_index_status"], "ok")
    test_case.assertRegex(report["evidence_index_source_hash"], r"^[0-9a-f]{64}$")
    test_case.assertEqual(report["ui_system_evidence_index_validation"]["status"], "ok")
    for evidence in report["ui_system_evidence"]:
        if evidence.startswith("detected source slots:"):
            continue
        test_case.assertTrue(
            evidence.startswith("assets/compiler_evidence_index.json:"),
            evidence,
        )


def assert_weighted_vertices(
    test_case: unittest.TestCase,
    vertices: list,
    vertex_count: int,
    bones: list[dict],
    expected_bone_names_by_vertex: list[list[str]],
) -> None:
    bone_names = [bone["name"] for bone in bones]
    cursor = 0
    test_case.assertEqual(len(expected_bone_names_by_vertex), vertex_count)
    for vertex_idx in range(vertex_count):
        test_case.assertLess(cursor, len(vertices), f"missing weighted block for vertex {vertex_idx}")
        influence_count = vertices[cursor]
        cursor += 1
        test_case.assertIs(type(influence_count), int)
        expected_bone_names = expected_bone_names_by_vertex[vertex_idx]
        test_case.assertEqual(influence_count, len(expected_bone_names))
        weight_total = 0.0
        actual_bone_names = []
        for influence_idx in range(influence_count):
            test_case.assertLessEqual(cursor + 3, len(vertices) - 1, f"truncated influence {influence_idx}")
            bone_idx, _bind_x, _bind_y, weight = vertices[cursor:cursor + 4]
            cursor += 4
            test_case.assertIs(type(bone_idx), int)
            test_case.assertGreaterEqual(bone_idx, 0)
            test_case.assertLess(bone_idx, len(bone_names))
            actual_bone_names.append(bone_names[bone_idx])
            weight_total += float(weight)
        test_case.assertEqual(actual_bone_names, expected_bone_names)
        test_case.assertAlmostEqual(weight_total, 1.0, places=6)
    test_case.assertEqual(cursor, len(vertices), "weighted vertices have trailing data")


class Phase1LocalEvals(unittest.TestCase):
    def test_phase_11_eval_coverage_registry_is_complete(self) -> None:
        import eval_coverage

        report = eval_coverage.build_report(PLUGIN_ROOT)

        self.assertEqual(report["status"], "ok", "\n".join(report["issues"]))
        self.assertGreaterEqual(report["local_eval_count"], 82)
        for entry in report["entries"]:
            with self.subTest(eval_id=entry["eval_id"]):
                self.assertGreater(entry["positive_test_count"], 0)
                self.assertGreater(entry["guard_test_count"], 0)
                self.assertTrue(entry["promoted"])
                self.assertTrue(entry["docs_path"])
                self.assertTrue(entry["required_feature_gates"])

    def test_eval_17_sequence_auto_emission(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_17_NAME + "-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            for idx, color in enumerate(((255, 0, 0, 255), (255, 180, 0, 255), (255, 255, 0, 255)), start=1):
                write_rgba_png(layer_dir / f"HP3_sparkle_{idx:03d}.png", 8, 8, color)

            out_dir = root / "with_sequences"
            run_builder(layer_dir, out_dir, "--enable-sequences")
            skel, atlas, report = load_package(out_dir)

            sequence_attachments = [
                att
                for slot_attachments in skin_attachments(skel).values()
                for att in slot_attachments.values()
                if "sequence" in att
            ]
            self.assertGreater(len(sequence_attachments), 0)
            self.assertEqual(sequence_attachments[0]["path"], "parts/HP3_sparkle_")
            self.assertGreater(report["sequence_attachments_emitted"], 0)
            self.assertIn("parts/HP3_sparkle_001", atlas)
            self.assertIn("parts/HP3_sparkle_002", atlas)
            self.assertIn("parts/HP3_sparkle_003", atlas)

            sequence_timeline_count = 0
            for animation in skel["animations"].values():
                for skin_tracks in animation.get("attachments", {}).values():
                    for slot_tracks in skin_tracks.values():
                        for attachment_tracks in slot_tracks.values():
                            if "sequence" in attachment_tracks:
                                sequence_timeline_count += 1
            self.assertGreater(sequence_timeline_count, 0)

    def test_eval_17_sequence_guard_without_flag(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_17_NAME + "-guard-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            write_rgba_png(layer_dir / "HP3_sparkle_001.png", 8, 8, (255, 0, 0, 255))
            write_rgba_png(layer_dir / "HP3_sparkle_002.png", 8, 8, (255, 180, 0, 255))

            out_dir = root / "without_sequences"
            run_builder(layer_dir, out_dir)
            skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["sequence_attachments_emitted"], 0)
            for slot_attachments in skin_attachments(skel).values():
                for att in slot_attachments.values():
                    self.assertNotIn("sequence", att)
            for animation in skel["animations"].values():
                for slot_tracks in animation.get("slots", {}).values():
                    self.assertNotIn("sequence", slot_tracks)
                self.assertNotIn("attachments", animation)

    def test_eval_18_mesh_plan_emits_reviewed_unweighted_mesh(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, edges=[[0, 1], [1, 2], [2, 3], [3, 0]])

            out_dir = root / "with_mesh"
            run_builder(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            skel, _atlas, report = load_package(out_dir)

            mesh = skin_attachments(skel)["HP3_body_slot"]["parts/HP3_body"]
            self.assertEqual(mesh["type"], "mesh")
            self.assertEqual(mesh["path"], "parts/HP3_body")
            self.assertEqual(mesh["hull"], 4)
            self.assertEqual(mesh["vertices"], [-8.0, -8.0, 8.0, -8.0, 8.0, 8.0, -8.0, 8.0])
            self.assertEqual(mesh["uvs"], [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0])
            self.assertEqual(mesh["triangles"], [0, 1, 2, 0, 2, 3])
            self.assertEqual(mesh["edges"], [0, 1, 1, 2, 2, 3, 3, 0])
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["mesh_attachments_emitted"], 1)
            self.assertEqual(report["mesh_plan"]["issue_count"], 0)

    def test_eval_18_mesh_plan_rejects_bad_triangle_index(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-bad-triangle-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, triangles=[0, 1, 8])

            out_dir = root / "bad_triangle"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("out of range", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_18_mesh_plan_rejects_closed_schema_violations(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-schema-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path)
            plan = read_mesh_plan(plan_path)
            plan["schema"] = "wrong_schema_v0"
            plan["unexpected"] = True
            del plan["attachments"][0]["target_slot"]
            plan["attachments"][0]["unknown_attachment_field"] = 1
            plan_path.write_text(json.dumps(plan, indent=2))

            out_dir = root / "schema"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            issues = "\n".join(report["mesh_plan"]["issues"])
            self.assertEqual(report["status"], "failed")
            self.assertIn("mesh_plan.schema", issues)
            self.assertIn("unexpected is not allowed", issues)
            self.assertIn("target_slot is required", issues)
            self.assertIn("unknown_attachment_field is not allowed", issues)

    def test_eval_18_mesh_plan_rejects_bool_triangle_value(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-bool-triangle-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, triangles=[0, True, 2])

            out_dir = root / "bool_triangle"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("triangles[1] must be an integer", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_18_mesh_plan_rejects_bad_uv_range(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-bad-uv-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, uvs=[[0, 0], [1.2, 0], [1, 1], [0, 1]])

            out_dir = root / "bad_uv"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("[0, 1] range", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_18_mesh_plan_rejects_degenerate_triangle(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-degenerate-triangle-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, triangles=[0, 1, 1])

            out_dir = root / "degenerate_triangle"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("degenerate", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_18_mesh_plan_rejects_bad_edge_index(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-bad-edge-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, edges=[0, 8])

            out_dir = root / "bad_edge"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("edges index 8 is out of range", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_18_mesh_plan_rejects_source_path_escape(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-source-escape-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            outside_dir = root / "outside"
            outside_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            write_rgba_png(outside_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, source_layer=str(outside_dir / "HP3_body.png"))

            out_dir = root / "source_escape"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("has no source PNG", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_18_mesh_plan_rejects_hull_degeneracy(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-hull-degenerate-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(
                plan_path,
                hull_vertices=[[-8, -8], [8, -8], [8, -8], [-8, 8]],
                uvs=[[0, 0], [1, 0], [1, 0], [0, 1]],
            )

            out_dir = root / "hull_degenerate"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("self-intersect", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_18_mesh_plan_rejects_self_intersecting_hull(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-self-intersect-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(
                plan_path,
                hull_vertices=[[-8, -8], [8, 8], [8, -8], [-8, 8]],
                uvs=[[0, 0], [1, 1], [1, 0], [0, 1]],
            )

            out_dir = root / "self_intersect"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("self-intersect", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_18_mesh_plan_rejects_over_budget_vertices(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_18_NAME + "-over-budget-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(
                plan_path,
                interior_vertices=[[0, 0]],
                uvs=[[0, 0], [1, 0], [1, 1], [0, 1], [0.5, 0.5]],
                triangles=[0, 1, 4, 1, 2, 4, 2, 3, 4, 3, 0, 4],
                max_vertex_budget=4,
            )

            out_dir = root / "over_budget"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path))
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("over budget", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_19_auto_bind_weighted_mesh(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_19_NAME + "-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, allowed_bones=["root", "HP3_body_bone"])

            out_dir = root / "with_weighted_mesh"
            run_builder(layer_dir, out_dir, "--mesh-plan", str(plan_path), "--auto-bind-weights")
            skel, _atlas, report = load_package(out_dir)

            mesh = skin_attachments(skel)["HP3_body_slot"]["parts/HP3_body"]
            self.assertEqual(mesh["type"], "mesh")
            self.assertGreater(len(mesh["vertices"]), len(mesh["uvs"]))
            assert_weighted_vertices(
                self,
                mesh["vertices"],
                len(mesh["uvs"]) // 2,
                skel["bones"],
                [["root", "HP3_body_bone"]] * 4,
            )
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["weighted_mesh_attachments_emitted"], 1)
            self.assertGreater(report["weighted_influence_count"], 0)
            self.assertGreater(report["estimated_vertex_transforms"], 0)
            self.assertEqual(report["weight_binding_policy"]["max_bones_per_vertex"], 2)
            self.assertTrue(report["weighted_mesh_review_required"])

    def test_eval_19_auto_bind_rejects_missing_mesh_plan(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_19_NAME + "-missing-plan-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))

            out_dir = root / "missing_plan"
            result = run_builder_raw(layer_dir, out_dir, "--auto-bind-weights")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("--auto-bind-weights requires --mesh-plan or --auto-mesh-plan", "\n".join(report["errors"]))

    def test_eval_19_auto_bind_rejects_missing_bone_name(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_19_NAME + "-missing-bone-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, allowed_bones=["root", "missing_bone"])

            out_dir = root / "missing_bone"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path), "--auto-bind-weights")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("missing bones", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_19_auto_bind_rejects_transform_budget(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_19_NAME + "-transform-budget-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, allowed_bones=["root", "HP3_body_bone"])
            plan = read_mesh_plan(plan_path)
            plan["weight_binding_policy"] = {
                "schema": "spine_slot_animation_weight_binding_policy_v1",
                "max_bones_per_vertex": 2,
                "weight_epsilon": 0.001,
                "influence_threshold": 0.05,
                "smoothing_iterations": 0,
                "max_estimated_vertex_transforms": 3,
                "review_required": True,
                "bind_position_mode": "approximate_local_offset",
            }
            plan_path.write_text(json.dumps(plan, indent=2))

            out_dir = root / "transform_budget"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path), "--auto-bind-weights")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("estimated vertex transforms", "\n".join(report["mesh_plan"]["issues"]))

    def test_eval_19_auto_bind_rejects_aggregate_transform_budget(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_19_NAME + "-aggregate-budget-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            write_rgba_png(layer_dir / "HP3_glow.png", 16, 16, (200, 240, 80, 180))
            plan_path = root / "mesh_plan.json"
            plan = {
                "schema": "spine_slot_animation_mesh_plan_v1",
                "max_vertex_budget": 8,
                "attachments": [
                    mesh_plan_attachment(allowed_bones=["root", "HP3_body_bone"]),
                    mesh_plan_attachment(
                        source_layer="HP3_glow.png",
                        target_slot="HP3_glow_slot",
                        allowed_bones=["root", "HP3_glow_bone"],
                    ),
                ],
                "weight_binding_policy": {
                    "schema": "spine_slot_animation_weight_binding_policy_v1",
                    "max_bones_per_vertex": 2,
                    "weight_epsilon": 0.001,
                    "influence_threshold": 0.05,
                    "smoothing_iterations": 0,
                    "max_estimated_vertex_transforms": 12,
                    "review_required": True,
                    "bind_position_mode": "approximate_local_offset",
                },
            }
            plan_path.write_text(json.dumps(plan, indent=2))

            out_dir = root / "aggregate_budget"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path), "--auto-bind-weights")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            issues = "\n".join(report["mesh_plan"]["issues"])
            self.assertEqual(report["status"], "failed")
            self.assertIn("aggregate estimated vertex transforms 16", issues)
            self.assertIn("max_estimated_vertex_transforms 12", issues)

    def test_eval_19_auto_bind_rejects_bad_policy(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_19_NAME + "-bad-policy-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, allowed_bones=["root", "HP3_body_bone"])
            plan = read_mesh_plan(plan_path)
            plan["weight_binding_policy"] = {
                "schema": "spine_slot_animation_weight_binding_policy_v1",
                "max_bones_per_vertex": 0,
                "weight_epsilon": 0.001,
                "influence_threshold": 0.05,
                "smoothing_iterations": 0,
                "max_estimated_vertex_transforms": 8,
                "review_required": False,
                "bind_position_mode": "exact_inverse_setup",
            }
            plan_path.write_text(json.dumps(plan, indent=2))

            out_dir = root / "bad_policy"
            result = run_builder_raw(layer_dir, out_dir, "--mesh-plan", str(plan_path), "--auto-bind-weights")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())
            self.assertEqual(report["status"], "failed")
            issues = "\n".join(report["mesh_plan"]["issues"])
            self.assertIn("max_bones_per_vertex", issues)
            self.assertIn("review_required", issues)

    def test_eval_30_auto_mesh_plan_generates_weighted_review_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_30_NAME + "-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            write_rgba_png(layer_dir / "HP3_cape.png", 16, 16, (120, 40, 180, 255))

            out_dir = root / "auto_weighted"
            run_builder(
                layer_dir,
                out_dir,
                "--report-mesh-candidates",
                "--auto-mesh-plan",
                "--auto-bind-weights",
                "--render-qa-frames",
            )
            skel, _atlas, report = load_package(out_dir)
            auto_plan = json.loads((out_dir / "auto_mesh_plan.json").read_text())
            candidate_report = json.loads((out_dir / "mesh_candidate_report.json").read_text())
            qa_report = json.loads((out_dir / "mesh_deformation_qa.json").read_text())

            self.assertEqual(report["status"], "ok")
            self.assertEqual(candidate_report["counts"]["mesh_candidate"], 1)
            self.assertEqual(auto_plan["attachments"][0]["target_slot"], "HP3_cape_slot")
            self.assertFalse(auto_plan["attachments"][0]["reviewed"])
            self.assertTrue(auto_plan["attachments"][0]["auto_generated"])
            self.assertTrue(auto_plan["attachments"][0]["review_required"])
            self.assertEqual(report["mesh_attachments_emitted"], 1)
            self.assertEqual(report["weighted_mesh_attachments_emitted"], 1)
            self.assertEqual(report["mesh_plan"]["weight_binding"]["algorithm"], "topology_aware_first_pass_projection_smooth_prune")
            self.assertIn("__mesh_weight_test", skel["animations"])
            self.assertTrue(report["mesh_deformation_qa"]["enabled"])
            self.assertTrue(report["mesh_deformation_qa"]["passed"])
            self.assertEqual(qa_report["test_animation"], "__mesh_weight_test")
            self.assertTrue((out_dir / "qa" / "setup.png").is_file())
            self.assertTrue(report["weighted_mesh_review_required"])
            self.assertIn("First-pass", report["weighted_mesh_review_required_reason"])

    def test_eval_30_reviewed_mesh_plan_overrides_auto_draft_plan(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_30_NAME + "-override-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            write_rgba_png(layer_dir / "HP3_cape.png", 16, 16, (120, 40, 180, 255))
            plan_path = root / "mesh_plan.json"
            write_mesh_plan(plan_path, allowed_bones=["root", "HP3_body_bone"])

            out_dir = root / "reviewed_override"
            run_builder(layer_dir, out_dir, "--mesh-plan", str(plan_path), "--auto-mesh-plan", "--auto-bind-weights")
            skel, _atlas, report = load_package(out_dir)

            mesh_slots = {
                slot_name
                for slot_name, atts in skin_attachments(skel).items()
                for att in atts.values()
                if att.get("type") == "mesh"
            }
            self.assertFalse((out_dir / "auto_mesh_plan.json").exists())
            self.assertEqual(report["auto_mesh_plan"]["status"], "skipped_reviewed_plan_override")
            self.assertEqual(report["mesh_attachments_emitted"], 1)
            self.assertIn("HP3_body_slot", mesh_slots)
            self.assertNotIn("HP3_cape_slot", mesh_slots)

    def test_eval_30_conservative_auto_mesh_keeps_static_layers_regions(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_30_NAME + "-conservative-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_head.png", 16, 16, (40, 180, 60, 255))
            write_rgba_png(layer_dir / "HP3_frame.png", 16, 16, (120, 40, 180, 255))
            write_rgba_png(layer_dir / "HP3_glow.png", 16, 16, (240, 240, 80, 180))

            out_dir = root / "region_only"
            run_builder(layer_dir, out_dir, "--report-mesh-candidates", "--auto-mesh-plan")
            skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["mesh_candidate_report"]["counts"]["mesh_candidate"], 0)
            self.assertEqual(report["mesh_attachments_emitted"], 0)
            self.assertEqual(report["weighted_mesh_attachments_emitted"], 0)
            for attachments in skin_attachments(skel).values():
                for attachment in attachments.values():
                    self.assertEqual(attachment["type"], "region")

    def test_eval_20_multi_skin_variants_emit_default_plus_two_variants(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_20_NAME + "-positive-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            variants_dir = layer_dir / "variants"
            variants_dir.mkdir(parents=True)
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 12, 12, (220, 180, 120, 255))
            write_rgba_png(variants_dir / "HP3_body_gold.png", 16, 16, (240, 190, 40, 255))
            write_rgba_png(variants_dir / "HP3_body_blue.png", 16, 16, (40, 80, 220, 255))
            plan_path = root / "skin_plan.json"
            write_skin_plan(plan_path, [
                {
                    "name": "gold",
                    "attachments": [{
                        "layer_file": "variants/HP3_body_gold.png",
                        "target_slot": "HP3_body_slot",
                        "attachment_key": "parts/HP3_body",
                        "attachment_name": "parts/HP3_body_gold",
                        "path": "parts/HP3_body_gold",
                    }],
                    "bones": ["HP3_body_bone"],
                },
                {
                    "name": "blue",
                    "attachments": [{
                        "layer_file": "variants/HP3_body_blue.png",
                        "target_slot": "HP3_body_slot",
                        "attachment_key": "parts/HP3_body",
                        "attachment_name": "parts/HP3_body_blue",
                        "path": "parts/HP3_body_blue",
                    }],
                },
            ])

            out_dir = root / "with_skins"
            run_builder(layer_dir, out_dir, "--skin-plan", str(plan_path), "--build-preview")
            skel, atlas, report = load_package(out_dir)
            preview = (out_dir / "preview.html").read_text()

            self.assertEqual(report["status"], "ok")
            self.assertEqual([skin["name"] for skin in skel["skins"]], ["default", "gold", "blue"])
            default_skin = skin_by_name(skel, "default")
            gold_skin = skin_by_name(skel, "gold")
            blue_skin = skin_by_name(skel, "blue")
            self.assertEqual(default_skin["attachments"]["HP3_body_slot"]["parts/HP3_body"]["path"], "parts/HP3_body")
            self.assertEqual(gold_skin["attachments"]["HP3_body_slot"]["parts/HP3_body"]["path"], "parts/HP3_body_gold")
            self.assertEqual(blue_skin["attachments"]["HP3_body_slot"]["parts/HP3_body"]["path"], "parts/HP3_body_blue")
            self.assertEqual(gold_skin["bones"], ["HP3_body_bone"])
            self.assertNotIn("HP3_head_slot", gold_skin["attachments"])
            self.assertIn("parts/HP3_body_gold", atlas)
            self.assertIn("parts/HP3_body_blue", atlas)
            self.assertEqual(report["skin_variants_emitted"], 2)
            self.assertEqual(report["skin_plan"]["skin_names"], ["gold", "blue"])
            self.assertIn('skins: ["default", "gold", "blue"]', preview)
            self.assertIn("window.__h5gSpinePlayerConfig", preview)
            self.assertIn("window.__h5gSpinePlayer", preview)
            self.assertIn("window.__h5gSpinePreviewState", preview)
            self.assertIn("does not runtime-prove interactive skin switching", preview)

    def test_eval_20_skin_plan_default_fallback_for_unplanned_slots(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_20_NAME + "-fallback-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            variants_dir = layer_dir / "variants"
            variants_dir.mkdir(parents=True)
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 12, 12, (220, 180, 120, 255))
            write_rgba_png(variants_dir / "HP3_body_gold.png", 16, 16, (240, 190, 40, 255))
            plan_path = root / "skin_plan.json"
            write_skin_plan(plan_path, [{
                "name": "gold",
                "attachments": [{
                    "layer_file": "variants/HP3_body_gold.png",
                    "target_slot": "HP3_body_slot",
                    "attachment_key": "parts/HP3_body",
                    "path": "parts/HP3_body_gold",
                }],
            }])

            out_dir = root / "fallback"
            run_builder(layer_dir, out_dir, "--skin-plan", str(plan_path))
            skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            gold_skin = skin_by_name(skel, "gold")
            self.assertNotIn("HP3_head_slot", gold_skin["attachments"])
            self.assertIn("parts/HP3_head", skin_by_name(skel, "default")["attachments"]["HP3_head_slot"])

    def test_eval_20_skin_plan_accepts_any_default_attachment_key_for_slot(self) -> None:
        from skin_plan import validate_and_build_skin_plan

        with tempfile.TemporaryDirectory(prefix=EVAL_20_NAME + "-multi-default-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            variants_dir = layer_dir / "variants"
            variants_dir.mkdir(parents=True)
            write_rgba_png(variants_dir / "HP3_face_smile_gold.png", 12, 12, (240, 190, 40, 255))
            layout = {
                "slots": [{"name": "HP3_face_slot"}],
                "attachments": [
                    {"slot": "HP3_face_slot", "name": "parts/HP3_face_neutral", "path": "parts/HP3_face_neutral"},
                    {"slot": "HP3_face_slot", "name": "parts/HP3_face_smile", "path": "parts/HP3_face_smile"},
                ],
            }
            plan = {
                "schema": "spine_slot_animation_skin_plan_v1",
                "skins": [{
                    "name": "gold",
                    "attachments": [{
                        "layer_file": "variants/HP3_face_smile_gold.png",
                        "target_slot": "HP3_face_slot",
                        "attachment_key": "parts/HP3_face_smile",
                        "path": "parts/HP3_face_smile_gold",
                    }],
                }],
            }

            built, report = validate_and_build_skin_plan(layout, plan, layer_dir)

            self.assertEqual(report["issues"], [])
            self.assertEqual(built["skins"][0]["attachments"][0]["key"], "parts/HP3_face_smile")

    def test_eval_20_no_skin_plan_keeps_single_default_skin(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_20_NAME + "-no-plan-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))

            out_dir = root / "no_plan"
            run_builder(layer_dir, out_dir)
            skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual([skin["name"] for skin in skel["skins"]], ["default"])
            self.assertEqual(report["skin_variants_emitted"], 0)

    def test_eval_20_skin_plan_guard_cases(self) -> None:
        cases = {
            "empty-skins": {
                "skins": [],
                "expected": "skin_plan.skins must not be empty",
            },
            "missing-source": {
                "skin": {
                    "name": "gold",
                    "attachments": [{
                        "layer_file": "variants/missing.png",
                        "target_slot": "HP3_body_slot",
                        "attachment_key": "parts/HP3_body",
                        "path": "parts/HP3_body_gold",
                    }],
                },
                "expected": "has no source PNG",
            },
            "duplicate-skin": {
                "skins": [
                    {
                        "name": "gold",
                        "attachments": [{
                            "layer_file": "variants/HP3_body_gold.png",
                            "target_slot": "HP3_body_slot",
                            "attachment_key": "parts/HP3_body",
                            "path": "parts/HP3_body_gold",
                        }],
                    },
                    {
                        "name": "gold",
                        "attachments": [{
                            "layer_file": "variants/HP3_body_gold.png",
                            "target_slot": "HP3_body_slot",
                            "attachment_key": "parts/HP3_body",
                            "path": "parts/HP3_body_gold",
                        }],
                    },
                ],
                "expected": "duplicates another skin name",
            },
            "invalid-slot": {
                "skin": {
                    "name": "gold",
                    "attachments": [{
                        "layer_file": "variants/HP3_body_gold.png",
                        "target_slot": "missing_slot",
                        "attachment_key": "parts/HP3_body",
                        "path": "parts/HP3_body_gold",
                    }],
                },
                "expected": "is not in the rig layout",
            },
            "linkedmesh": {
                "skin": {
                    "name": "gold",
                    "attachments": [{
                        "layer_file": "variants/HP3_body_gold.png",
                        "target_slot": "HP3_body_slot",
                        "attachment_key": "parts/HP3_body",
                        "path": "parts/HP3_body_gold",
                        "type": "linkedmesh",
                    }],
                },
                "expected": "linkedmesh is not implemented",
            },
        }
        for label, case in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(prefix=EVAL_20_NAME + "-" + label + "-") as tmp:
                root = Path(tmp)
                layer_dir = root / "layers"
                variants_dir = layer_dir / "variants"
                variants_dir.mkdir(parents=True)
                write_rgba_png(layer_dir / "HP3_body.png", 16, 16, (40, 180, 60, 255))
                write_rgba_png(variants_dir / "HP3_body_gold.png", 16, 16, (240, 190, 40, 255))
                plan_path = root / "skin_plan.json"
                skins = case["skins"] if "skins" in case else [case["skin"]]
                write_skin_plan(plan_path, skins)

                out_dir = root / "out"
                result = run_builder_raw(layer_dir, out_dir, "--skin-plan", str(plan_path))
                self.assertNotEqual(result.returncode, 0)
                report = json.loads((out_dir / "validation_report.json").read_text())

                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["skin_variants_emitted"], 0)
                self.assertIn(case["expected"], "\n".join(report["skin_plan"]["issues"]))

    def test_default_animation_is_rest_pose_and_family_names_remain(self) -> None:
        from compose_animations import (
            FAMILY_ANIMATION_NAMES,
            NON_SYMBOL_FAMILIES,
            _validate_controls,
            compose_animations_for_family,
        )

        layout = {
            "bones": [
                {"name": "root"},
                {"name": "HP3_body_bone", "semantic_role": "symbol_body"},
            ],
            "slots": [],
            "attachments": [],
        }
        animations = compose_animations_for_family(layout, "hp_symbol", 3, _validate_controls({}))

        self.assertEqual(set(animations), {"HP3", "HP3idle", "HP3breathe", "HP3land", "HP3win"})
        self.assertEqual(animations["HP3"], {"bones": {}, "slots": {}})
        self.assertNotEqual(animations["HP3"], animations["HP3win"])
        self.assertIn("HP3_body_bone", animations["HP3win"]["bones"])

        for family, (prefix, suffixes) in FAMILY_ANIMATION_NAMES.items():
            family_animations = compose_animations_for_family(layout, family, 2, _validate_controls({}))
            self.assertEqual(set(family_animations), {f"{prefix}2{suffix}" for suffix in suffixes})
            self.assertEqual(family_animations[f"{prefix}2"], {"bones": {}, "slots": {}})
        for family, names in NON_SYMBOL_FAMILIES.items():
            family_animations = compose_animations_for_family(layout, family, 2, _validate_controls({}))
            self.assertEqual(set(family_animations), set(names))

    def test_eval_29_loop_validation_reports_hp_symbol_intents(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_29_NAME + "-hp-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_frame_glow.png", 20, 20, (255, 240, 120, 180))

            out_dir = root / "hp"
            run_builder(layer_dir, out_dir)
            _skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["loop_validation_status"], "ok")
            self.assertEqual(report["animation_loop_intents"]["HP3idle"], "loop")
            self.assertEqual(report["animation_loop_intents"]["HP3breathe"], "loop")
            self.assertEqual(report["animation_loop_intents"]["HP3land"], "settle_to_setup")
            self.assertEqual(report["animation_loop_intents"]["HP3win"], "settle_to_setup")
            self.assertEqual(report["animation_loop_validation"]["issues"], [])

    def test_eval_29_loop_validation_reports_winframe_intents(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_29_NAME + "-winframe-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "WinFrame_frame.png", 24, 24, (80, 60, 140, 255))
            write_rgba_png(layer_dir / "WinFrame_glow.png", 24, 24, (180, 220, 255, 180))

            out_dir = root / "winframe"
            run_builder(layer_dir, out_dir, family="winframe_explode")
            _skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["loop_validation_status"], "ok")
            self.assertEqual(report["animation_loop_intents"]["WinFrameidle"], "loop")
            self.assertEqual(report["animation_loop_intents"]["WinFrame"], "transition")
            self.assertEqual(report["animation_loop_intents"]["WinFrameExplode"], "transition")

    def test_eval_29_loop_validation_reports_avatar_intents(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_29_NAME + "-avatar-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_avatar_state_layers(layer_dir)

            out_dir = root / "avatar"
            run_builder(layer_dir, out_dir, family="avatar")
            _skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["loop_validation_status"], "ok")
            self.assertEqual(report["animation_loop_intents"]["State0Idle"], "loop")
            self.assertEqual(report["animation_loop_intents"]["State1Idle"], "loop")
            self.assertEqual(report["animation_loop_intents"]["Avatar"], "loop")
            self.assertEqual(report["animation_loop_intents"]["State0to1"], "transition")
            self.assertEqual(report["animation_loop_intents"]["State1Awarded"], "settle_to_setup")

    def test_eval_29_loop_validation_rejects_bad_idle_endpoint(self) -> None:
        from loop_validation import validate_animation_loops

        with tempfile.TemporaryDirectory(prefix=EVAL_29_NAME + "-bad-idle-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))

            out_dir = root / "hp"
            run_builder(layer_dir, out_dir)
            skel, _atlas, _report = load_package(out_dir)
            skel["animations"]["HP3idle"]["bones"]["HP3_body_bone"]["translate"][-1]["y"] = 3

            loop_report = validate_animation_loops(skel, "hp_symbol")

            self.assertEqual(loop_report["status"], "failed")
            self.assertIn("loop_endpoint_mismatch", {issue["code"] for issue in loop_report["issues"]})
            self.assertEqual(loop_report["issues"][0]["animation"], "HP3idle")

    def test_eval_29_loop_validation_rejects_bad_settle_endpoint(self) -> None:
        from loop_validation import validate_animation_loops

        with tempfile.TemporaryDirectory(prefix=EVAL_29_NAME + "-bad-settle-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))

            out_dir = root / "hp"
            run_builder(layer_dir, out_dir)
            skel, _atlas, _report = load_package(out_dir)
            skel["animations"]["HP3land"]["bones"]["HP3_body_bone"]["translate"][-1]["y"] = 3

            loop_report = validate_animation_loops(skel, "hp_symbol")

            self.assertEqual(loop_report["status"], "failed")
            self.assertIn("settle_endpoint_mismatch", {issue["code"] for issue in loop_report["issues"]})
            self.assertEqual(loop_report["issues"][0]["animation"], "HP3land")

    def test_handoff_zip_contains_complete_spine_editor_import_set(self) -> None:
        with tempfile.TemporaryDirectory(prefix="handoff-zip-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 18, 18, (120, 60, 30, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 12, 12, (220, 180, 120, 255))

            out_dir = root / "package"
            run_builder(layer_dir, out_dir, "--build-preview", "--spine-editor-zip")
            _skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["output_files"]["status"], "ok")
            for name in ("shared_symbols.json", "shared_symbols.atlas", "shared_symbols.png"):
                self.assertTrue(report["output_files"]["files"][name]["exists"])
                self.assertGreater(report["output_files"]["files"][name]["bytes"], 0)

            preview = (out_dir / "preview.html").read_text(encoding="utf-8")
            self.assertIn("rawDataURIs", preview)
            self.assertIn("data:image/png;base64,", preview)
            self.assertIn('skeleton: "shared_symbols.json"', preview)

            zip_path = out_dir / "spine_editor_handoff.zip"
            self.assertTrue(zip_path.is_file())
            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
                self.assertIn("shared_symbols.json", names)
                self.assertIn("shared_symbols.atlas", names)
                self.assertIn("shared_symbols.png", names)
                self.assertIn("preview.html", names)
                self.assertIn("README_FOR_SPINE_EDITOR.md", names)
                self.assertIn("audit_manifest.json", names)
                self.assertIn("CREATE_SPINE_PROJECT.ps1", names)
                self.assertIn("editor_images/parts/HP3_body.png", names)
                self.assertIn("editor_images/parts/HP3_head.png", names)
                readme = archive.read("README_FOR_SPINE_EDITOR.md").decode("utf-8")
                self.assertIn("File -> Import Data", readme)
                self.assertIn("CREATE_SPINE_PROJECT.ps1", readme)
                self.assertIn("Images", readme)
                self.assertIn("editor_images", readme)
                create_script = archive.read("CREATE_SPINE_PROJECT.ps1").decode("utf-8")
                self.assertIn("Spine.com", create_script)
                self.assertIn("-i $json -o $out -r", create_script)
                self.assertIn("$skeletonName = 'HP3'", create_script)
                self.assertIn("$outputProject = 'HP3.spine'", create_script)
                self.assertIn("-r $skeletonName", create_script)
                audit = json.loads(archive.read("audit_manifest.json").decode("utf-8"))
                self.assertEqual(audit["mesh_attachments_emitted"], 0)
                self.assertEqual(audit["weighted_mesh_attachments_emitted"], 0)
                self.assertEqual(audit["editor_images_root"], "editor_images")
                self.assertGreaterEqual(audit["editor_images_count"], 2)
                self.assertEqual(audit["spine_project_script"], "CREATE_SPINE_PROJECT.ps1")

    def test_create_spine_project_dry_run_writes_official_cli_command(self) -> None:
        import create_spine_project

        with tempfile.TemporaryDirectory(prefix="native-spine-dry-run-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 18, 18, (120, 60, 30, 255))

            out_dir = root / "package"
            run_builder(layer_dir, out_dir)
            built_skeleton = json.loads((out_dir / "shared_symbols.json").read_text(encoding="utf-8"))
            self.assertEqual(built_skeleton["skeleton"]["spine"], "4.3.04")

            report = create_spine_project.create_spine_project(
                out_dir,
                output_project=root / "HP3.spine",
                spine_cli=Path(sys.executable),
                dry_run=True,
                probe_project=False,
            )

            self.assertEqual(report["status"], "dry_run")
            self.assertTrue(report["official_cli_import"])
            self.assertFalse(report["hand_authored_spine_file"])
            self.assertEqual(report["skeleton_name"], "HP3")
            self.assertIn("-u", report["command"])
            self.assertIn("4.3.04", report["command"])
            self.assertIn("-r", report["command"])
            self.assertTrue((out_dir / "spine_project_report.json").is_file())

    def test_create_spine_project_rejects_cli_version_mismatch(self) -> None:
        import create_spine_project

        with tempfile.TemporaryDirectory(prefix="native-spine-mismatch-") as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            (package_dir / "shared_symbols.json").write_text(json.dumps({
                "skeleton": {"spine": "3.8.99"},
                "bones": [{"name": "root"}],
                "slots": [],
                "skins": [{"name": "default", "attachments": {}}],
                "animations": {},
            }), encoding="utf-8")
            (package_dir / "shared_symbols.atlas").write_text("shared_symbols.png\n", encoding="utf-8")
            write_rgba_png(package_dir / "shared_symbols.png", 2, 2, (0, 0, 0, 0))

            with self.assertRaisesRegex(create_spine_project.SpineProjectError, "must use the same editor version"):
                create_spine_project.create_spine_project(
                    package_dir,
                    output_project=root / "HP3.spine",
                    spine_cli=Path(sys.executable),
                    spine_version="4.3.04",
                    dry_run=True,
                    probe_project=False,
                )

    def test_handoff_packager_rejects_missing_texture_page(self) -> None:
        import package_spine_editor_handoff as handoff

        with tempfile.TemporaryDirectory(prefix="handoff-missing-png-") as tmp:
            package_dir = Path(tmp)
            (package_dir / "shared_symbols.json").write_text(json.dumps({
                "skeleton": {"spine": "4.3.04"},
                "bones": [{"name": "root"}],
                "slots": [],
                "skins": [{"name": "default", "attachments": {}}],
                "animations": {},
            }), encoding="utf-8")
            (package_dir / "shared_symbols.atlas").write_text(
                "shared_symbols.png\nsize: 16,16\nformat: RGBA8888\n",
                encoding="utf-8",
            )
            (package_dir / "validation_report.json").write_text(
                json.dumps({"status": "ok"}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(handoff.HandoffPackageError, "shared_symbols.png"):
                handoff.package_handoff(package_dir)

    def test_handoff_packager_rejects_unsafe_editor_image_entries(self) -> None:
        import package_spine_editor_handoff as handoff

        self.assertEqual(
            handoff._safe_editor_image_entry("parts/HP3_body"),
            "editor_images/parts/HP3_body.png",
        )
        for region_name in ("../evil", "/absolute", "C:/evil", r"parts\evil", "parts/evil;rm", "parts//evil", "parts/"):
            with self.subTest(region_name=region_name):
                with self.assertRaisesRegex(handoff.HandoffPackageError, "unsafe|absolute|backslash|drive|empty"):
                    handoff._safe_editor_image_entry(region_name)

    def test_handoff_create_project_script_rejects_unsafe_skeleton_name(self) -> None:
        import package_spine_editor_handoff as handoff

        audit = {"animations": ["HP3'; Remove-Item x; '"]}
        with self.assertRaisesRegex(handoff.HandoffPackageError, "skeleton name"):
            handoff.build_create_project_script(Path("package"), audit)

    def test_helper_outputs_refuse_protected_destinations(self) -> None:
        import auto_bind_weights
        import create_spine_project
        import package_spine_editor_handoff as handoff

        with tempfile.TemporaryDirectory(prefix="helper-write-guards-") as tmp:
            root = Path(tmp)
            protected = root / "p4_guard"

            with self.assertRaisesRegex(ValueError, "prohibited write root marker"):
                handoff.package_handoff(root / "missing-package", protected / "handoff.zip")

            mesh_path = root / "mesh.json"
            bones_path = root / "bones.json"
            mesh_path.write_text(json.dumps({"vertices": [[0, 0]], "triangles": []}), encoding="utf-8")
            bones_path.write_text(json.dumps([{"name": "root", "x": 0, "y": 0}]), encoding="utf-8")
            old_argv = sys.argv[:]
            try:
                sys.argv = [
                    "auto_bind_weights.py",
                    "--mesh",
                    str(mesh_path),
                    "--bones",
                    str(bones_path),
                    "--out",
                    str(protected / "weights.json"),
                ]
                with self.assertRaisesRegex(ValueError, "prohibited write root marker"):
                    auto_bind_weights.main()
            finally:
                sys.argv = old_argv

            package_dir = protected / "package"
            package_dir.mkdir(parents=True)
            (package_dir / "shared_symbols.json").write_text(json.dumps({
                "skeleton": {"spine": "4.3.04"},
                "bones": [{"name": "root"}],
                "slots": [],
                "skins": [{"name": "default", "attachments": {}}],
                "animations": {},
            }), encoding="utf-8")
            (package_dir / "shared_symbols.atlas").write_text("shared_symbols.png\n", encoding="utf-8")
            write_rgba_png(package_dir / "shared_symbols.png", 2, 2, (0, 0, 0, 0))

            with self.assertRaisesRegex(ValueError, "prohibited write root marker"):
                create_spine_project.create_spine_project(
                    package_dir,
                    output_project=root / "safe.spine",
                    spine_cli=Path(sys.executable),
                    dry_run=True,
                    probe_project=False,
                )

    def test_write_guard_resolves_existing_symlink_targets(self) -> None:
        import source_art_guard

        with tempfile.TemporaryDirectory(prefix="write-guard-symlink-") as tmp:
            root = Path(tmp)
            protected_target = root / "protected_target"
            protected_target.mkdir()
            alias = root / "alias_to_protected"
            try:
                os.symlink(protected_target, alias, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                if os.name != "nt":
                    self.skipTest(f"symlink creation unavailable: {exc}")
                result = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(alias), str(protected_target)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    self.skipTest(
                        "symlink and junction creation unavailable: "
                        f"{exc}; mklink stderr={result.stderr.strip()}"
                    )

            old_roots = source_art_guard.PROHIBITED_WRITE_ROOTS
            try:
                source_art_guard.PROHIBITED_WRITE_ROOTS = (protected_target,)
                with self.assertRaisesRegex(ValueError, "prohibited source-art root"):
                    source_art_guard.ensure_safe_write_path(alias / "out.json", "out")
            finally:
                source_art_guard.PROHIBITED_WRITE_ROOTS = old_roots

    def test_weighted_mesh_docs_match_automatic_support(self) -> None:
        meshes_doc = (PLUGIN_ROOT / "references" / "meshes_and_deform.md").read_text(encoding="utf-8")
        skill_doc = (PLUGIN_ROOT / "skills" / "spine-slot-animation" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("__mesh_weight_test", meshes_doc)
        self.assertIn("--auto-mesh-plan", skill_doc)
        self.assertIn("topology-aware", skill_doc)
        self.assertNotIn('doesn\'t auto-generate a "weight test" animation today', meshes_doc)
        self.assertNotIn("This is first-pass inverse-distance binding", skill_doc)

    def test_eval_31_spine_cli_reference_covers_official_command_families(self) -> None:
        cli_doc = (PLUGIN_ROOT / "references" / "spine_cli.md").read_text(encoding="utf-8").lower()

        for family in ("editor", "export", "import", "clean", "pack", "unpack", "info"):
            self.assertIn(family, cli_doc)
        for flag in (
            "-h",
            "--help",
            "--advanced",
            "--version",
            "--logout",
            "--update",
            "--force",
            "--proxy",
            "--notimeout",
            "--clean",
            "--clean-all",
            "-xmx",
            "--trace",
            "--server",
            "--ignore-unknown",
        ):
            self.assertIn(flag, cli_doc)
        for platform_term in ("spine.com", "spine.exe", "app bundle", "spine.sh"):
            self.assertIn(platform_term, cli_doc)
        self.assertIn("multiple commands", cli_doc)
        self.assertIn("non-zero exit", cli_doc)

    def test_eval_31_spine_cli_reference_preserves_policy_boundaries(self) -> None:
        cli_doc = (PLUGIN_ROOT / "references" / "spine_cli.md").read_text(encoding="utf-8").lower()
        skill_doc = (PLUGIN_ROOT / "skills" / "spine-slot-animation" / "SKILL.md").read_text(encoding="utf-8").lower()
        capability_doc = (PLUGIN_ROOT / "references" / "capability_status.md").read_text(encoding="utf-8").lower()

        for status in ("supported / automated", "documented but policy-gated", "unsupported / not automated"):
            self.assertIn(status, cli_doc)
        for supported_term in ("-i -o -r", "project info", "spine_project_report.json"):
            self.assertIn(supported_term, cli_doc + skill_doc)
        for gated_term in ("json", "binary", ".skel", "clean", "pack", "unpack", "advanced flags"):
            self.assertIn(gated_term, cli_doc)
        for blocked_term in ("license activation", "perforce", "source-art writes", "production export remains gated"):
            self.assertIn(blocked_term, cli_doc)
        self.assertIn("references/spine_cli.md", skill_doc)
        self.assertIn("spine cli reference layer", capability_doc)

    def test_eval_32_rig_proposal_generator_reports_region_and_mesh_decisions(self) -> None:
        import generate_rig_proposal

        evidence_index = json.loads((PLUGIN_ROOT / "assets" / "h5g_corpus_distilled_evidence.json").read_text(encoding="utf-8"))
        proposal = generate_rig_proposal.build_proposal(
            family="avatar",
            layers=[
                {"name": "Avatar_body", "semantic_role": "character_body", "confidence": 0.86},
                {"name": "Avatar_frame", "semantic_role": "frame", "confidence": 0.91},
            ],
            evidence_index=evidence_index,
        )

        self.assertEqual(proposal["schema"], "spine_slot_animation_rig_proposal_v1")
        self.assertEqual(proposal["proposal_mode"], "report_only")
        self.assertFalse(proposal["production_output_claimed"])
        self.assertEqual(proposal["region_decisions"][0]["layer"], "Avatar_frame")
        self.assertEqual(proposal["mesh_decisions"][0]["layer"], "Avatar_body")
        self.assertTrue(proposal["mesh_decisions"][0]["review_required"])
        self.assertEqual(proposal["evidence_support"]["evidence_index"], "assets/h5g_corpus_distilled_evidence.json")
        self.assertIn(
            "assets/h5g_corpus_distilled_evidence.json:families",
            proposal["evidence_support"]["evidence_ids"],
        )
        self.assertEqual(
            proposal["policy_gates"]["final_autonomous_rigger_claim"]["status"],
            "blocked",
        )

    def test_eval_32_autonomous_rigging_artifacts_preserve_claim_boundaries(self) -> None:
        schema = json.loads((PLUGIN_ROOT / "assets" / "rig_proposal_schema.json").read_text(encoding="utf-8"))
        evidence_index = json.loads((PLUGIN_ROOT / "assets" / "autonomous_rigging_evidence_index.json").read_text(encoding="utf-8"))
        research_doc = (PLUGIN_ROOT / "references" / "autonomous_rigging_research.md").read_text(encoding="utf-8").lower()
        proposal_doc = (PLUGIN_ROOT / "references" / "rig_proposal.md").read_text(encoding="utf-8").lower()
        external_doc = (PLUGIN_ROOT / "references" / "external_avatar_rigging_review.md").read_text(encoding="utf-8").lower()
        skill_doc = (PLUGIN_ROOT / "skills" / "spine-slot-animation" / "SKILL.md").read_text(encoding="utf-8").lower()
        cli_doc = (PLUGIN_ROOT / "references" / "spine_cli.md").read_text(encoding="utf-8").lower()

        self.assertEqual(schema["properties"]["proposal_mode"]["const"], "report_only")
        self.assertIs(schema["properties"]["production_output_claimed"]["const"], False)
        self.assertEqual(evidence_index["coverage"]["status"], "not_autonomous_production_rigger")
        self.assertIn("fully autonomous production rigger", research_doc)
        self.assertIn("cannot by itself justify", proposal_doc)
        self.assertIn("polyform noncommercial", external_doc)
        self.assertIn("conceptual prior art", external_doc)
        self.assertIn("report-only proposal support", skill_doc)
        self.assertIn("cannot enable `.skel`", cli_doc)
        self.assertIn("g:/artsource", json.dumps(evidence_index).lower())
        self.assertIn("perforce", json.dumps(evidence_index).lower())

    def test_eval_33_bundled_corpus_pack_covers_required_sections(self) -> None:
        evidence = json.loads((PLUGIN_ROOT / "assets" / "h5g_corpus_distilled_evidence.json").read_text(encoding="utf-8"))
        knowledge_doc = (PLUGIN_ROOT / "references" / "h5g_corpus_distilled_knowledge.md").read_text(encoding="utf-8").lower()

        expected_families = {
            "hp_symbol",
            "lp_symbol",
            "mp_symbol",
            "bo_special_symbol",
            "wild_symbol",
            "special_feature_symbol",
            "bonus_symbol",
            "jackpot_symbol",
            "value_symbol",
            "scatter_symbol",
            "winframe_explode",
            "meter",
            "transition",
            "celebration",
            "avatar",
        }
        self.assertEqual({family["family"] for family in evidence["families"]}, expected_families)
        self.assertEqual(evidence["summary"]["families_covered"], 15)
        for required_key in (
            "animation_intents",
            "rig_slot_layer_evidence",
            "ui_system_buckets",
            "mesh_weight_deform_findings",
            "production_export_runtime_boundaries",
            "known_gaps",
        ):
            self.assertIn(required_key, evidence)
        self.assertIn("avatar", evidence["query_indexes"]["families_by_family"])
        self.assertIn("deform_observations", evidence["families"][evidence["query_indexes"]["families_by_family"]["avatar"]]["evidence"])
        for required_phrase in (
            "bundled, portable knowledge pack",
            "animation intents",
            "ui/system buckets",
            "mesh/weight/deform findings",
            "production export/runtime boundaries",
            "known gaps",
        ):
            self.assertIn(required_phrase, knowledge_doc)

    def test_eval_33_bundled_corpus_pack_has_no_absolute_research_dependency(self) -> None:
        import generate_rig_proposal

        evidence_text = (PLUGIN_ROOT / "assets" / "h5g_corpus_distilled_evidence.json").read_text(encoding="utf-8")
        knowledge_text = (PLUGIN_ROOT / "references" / "h5g_corpus_distilled_knowledge.md").read_text(encoding="utf-8")
        autonomous_text = (PLUGIN_ROOT / "assets" / "autonomous_rigging_evidence_index.json").read_text(encoding="utf-8")

        absolute_research_paths = (
            r"C:\Users\merickson\Desktop\Claude Spine\research",
            "C:/Users/merickson/Desktop/Claude Spine/research",
        )
        for absolute_path in absolute_research_paths:
            self.assertNotIn(absolute_path, evidence_text)
            self.assertNotIn(absolute_path, knowledge_text)
            self.assertNotIn(absolute_path, autonomous_text)

        self.assertEqual(
            generate_rig_proposal.DEFAULT_EVIDENCE_INDEX,
            PLUGIN_ROOT / "assets" / "h5g_corpus_distilled_evidence.json",
        )

    def test_eval_34_bakeoff_resolver_detects_network_resource_and_snapshot(self) -> None:
        import resolve_h5g_corpus_bakeoff

        snapshot = json.loads((PLUGIN_ROOT / "assets" / "h5g_corpus_evidence_snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["schema"], "spine_slot_animation_h5g_corpus_evidence_snapshot_v1")
        self.assertEqual(snapshot["optional_network_bakeoff_resource"]["default_path"], "G:/artSource/_spineResources/H5G_Corpus_Bakeoff")
        self.assertEqual(snapshot["optional_network_bakeoff_resource"]["write_policy"], "read_only_reference_only")

        with tempfile.TemporaryDirectory(prefix=EVAL_34_NAME + "-") as tmp:
            root = Path(tmp)
            fake_plugin = root / "plugin"
            assets_dir = fake_plugin / "assets"
            assets_dir.mkdir(parents=True)
            (assets_dir / "h5g_corpus_evidence_snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")
            (assets_dir / "h5g_corpus_distilled_evidence.json").write_text("{}", encoding="utf-8")
            network_root = root / "H5G_Corpus_Bakeoff"
            network_root.mkdir()
            (network_root / "README.md").write_text("fixture", encoding="utf-8")

            report = resolve_h5g_corpus_bakeoff.detect_sources(
                research_root=root / "missing_research",
                network_root=network_root,
                plugin_root=fake_plugin,
            )

            self.assertEqual(report["status"], "network_h5g_corpus_bakeoff_available")
            self.assertEqual(report["evidence_tier"], "network_bakeoff_resource")
            self.assertFalse(report["fresh_full_bakeoff_proof"])
            self.assertFalse(report["advisory_snapshot_only"])
            self.assertTrue(report["availability"]["network_bakeoff_resource"])
            self.assertFalse(report["availability"]["network_report_pack"])
            self.assertIn("README.md", report["network_bakeoff_preview"])

            (network_root / "H5G_CORPUS_BAKEOFF_CONSOLIDATED_REPORT.md").write_text("# report", encoding="utf-8")
            (network_root / "H5G_CORPUS_BAKEOFF_CONSOLIDATED_INDEX.json").write_text("{}", encoding="utf-8")
            (network_root / "report_pack_manifest.json").write_text("{}", encoding="utf-8")

            report_pack = resolve_h5g_corpus_bakeoff.detect_sources(
                research_root=root / "missing_research",
                network_root=network_root,
                plugin_root=fake_plugin,
            )

            self.assertEqual(report_pack["status"], "network_h5g_corpus_bakeoff_report_pack_available")
            self.assertEqual(report_pack["evidence_tier"], "network_report_pack")
            self.assertFalse(report_pack["advisory_snapshot_only"])
            self.assertTrue(report_pack["availability"]["network_report_pack"])
            self.assertIn("consolidated_report", report_pack["network_bakeoff_artifacts"])
            self.assertIn("consolidated_index", report_pack["network_bakeoff_artifacts"])
            self.assertIn("report_pack_manifest", report_pack["network_bakeoff_artifacts"])
            self.assertEqual(
                report_pack["preferred_read_order"][0],
                "network_bakeoff_artifacts.consolidated_report",
            )

    def test_eval_34_bakeoff_snapshot_and_docs_preserve_read_only_boundaries(self) -> None:
        snapshot_text = (PLUGIN_ROOT / "assets" / "h5g_corpus_evidence_snapshot.json").read_text(encoding="utf-8").lower()
        usage_doc = (PLUGIN_ROOT / "references" / "h5g_corpus_bakeoff_usage.md").read_text(encoding="utf-8").lower()
        skill_doc = (PLUGIN_ROOT / "skills" / "spine-slot-animation" / "SKILL.md").read_text(encoding="utf-8").lower()
        validation_doc = (PLUGIN_ROOT / "references" / "validation.md").read_text(encoding="utf-8").lower()

        for text in (snapshot_text, usage_doc, skill_doc, validation_doc):
            self.assertIn("h5g_corpus_bakeoff", text)
        self.assertIn("read_only_reference_only", snapshot_text)
        self.assertIn("must not populate, update, or mutate", usage_doc)
        self.assertIn("advisory_snapshot_not_full_bakeoff_proof", snapshot_text)
        self.assertIn("do not claim fresh full-bakeoff proof", validation_doc)
        self.assertIn("g:/artsource", snapshot_text)

    def test_eval_35_visual_remediation_packet_guides_review_loop(self) -> None:
        import visual_remediation_loop

        with tempfile.TemporaryDirectory(prefix=EVAL_35_NAME + "-packet-") as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            (package_dir / "preview.html").write_text("<html></html>", encoding="utf-8")
            (package_dir / "shared_symbols.json").write_text(
                json.dumps({"animations": {"idle": {}, "land": {}, "win": {}}}),
                encoding="utf-8",
            )
            (package_dir / "validation_report.json").write_text(
                json.dumps({
                    "status": "ok",
                    "weighted_mesh_review_required": True,
                    "weighted_mesh_review_required_reason": "first-pass auto weights require visual review",
                }),
                encoding="utf-8",
            )

            out_dir = root / "visual"
            packet = visual_remediation_loop.build_packet(package_dir, out_dir)

            self.assertEqual(packet["schema"], "spine_slot_animation_visual_remediation_packet_v1")
            self.assertEqual(packet["animations"], ["idle", "land", "win"])
            self.assertTrue(packet["mesh_review_required"])
            self.assertIn("too_flashy", packet["supported_control_issue_codes"])
            self.assertIn("mesh_tearing", packet["blocking_issue_codes"])
            self.assertTrue((out_dir / "visual_remediation_packet.json").is_file())
            self.assertTrue((out_dir / "VISUAL_REMEDIATION_PROMPT.md").is_file())

    def test_eval_35_visual_remediation_maps_safe_controls_and_blocks_rig_issues(self) -> None:
        import visual_remediation_loop

        with tempfile.TemporaryDirectory(prefix=EVAL_35_NAME + "-review-") as tmp:
            root = Path(tmp)
            review_path = root / "visual_review.json"
            review_path.write_text(
                json.dumps({
                    "schema": "spine_slot_animation_visual_review_v1",
                    "recipe_type": "hp_symbol",
                    "issues": [
                        {
                            "code": "too_flashy",
                            "severity": "warn",
                            "animation": "win",
                            "evidence": "Glow overwhelms the symbol.",
                        },
                        {
                            "code": "not_bouncy_enough",
                            "severity": "warn",
                            "animation": "land",
                            "evidence": "Land does not read as impact.",
                        },
                        {
                            "code": "mesh_tearing",
                            "severity": "fail",
                            "animation": "__mesh_weight_test",
                            "evidence": "Cape tears near the shoulder.",
                        },
                    ],
                }),
                encoding="utf-8",
            )

            out_dir = root / "remediation"
            report = visual_remediation_loop.remediate_review(review_path, out_dir)
            controls = json.loads((out_dir / "visual_remediation.controls.json").read_text(encoding="utf-8"))

            self.assertEqual(report["schema"], "spine_slot_animation_visual_remediation_report_v1")
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(controls["recipe_type"], "hp_symbol")
            self.assertLess(controls["glow_intensity"], 1.0)
            self.assertLess(controls["sparkle_intensity"], 1.0)
            self.assertGreater(controls["bounce_strength"], 1.0)
            self.assertEqual(report["blocking_issues"][0]["code"], "mesh_tearing")
            self.assertIn("reviewed mesh topology/weights", report["blocking_issues"][0]["required_action"])
            self.assertIn("not final production art approval", report["approval_boundary"])

    def test_eval_36_mesh_weight_parity_comparator_accepts_matching_fixture(self) -> None:
        import compare_mesh_weight_parity

        weighted_mesh = {
            "skeleton": {"spine": "4.3.04"},
            "skins": [
                {
                    "name": "default",
                    "attachments": {
                        "cape_slot": {
                            "cape": {
                                "type": "mesh",
                                "uvs": [0, 0, 1, 0, 1, 1, 0, 1],
                                "triangles": [0, 1, 2, 0, 2, 3],
                                "vertices": [
                                    1, 0, -1, -1, 1.0,
                                    1, 0, 1, -1, 1.0,
                                    1, 0, 1, 1, 1.0,
                                    1, 0, -1, 1, 1.0,
                                ],
                                "hull": 4,
                                "width": 8,
                                "height": 8,
                            }
                        }
                    },
                }
            ],
        }

        report = compare_mesh_weight_parity.compare(
            weighted_mesh,
            weighted_mesh,
            {
                "require_exact_vertex_count": True,
                "require_exact_triangle_count": True,
                "max_weight_sum_error": 0.001,
                "max_bones_per_vertex": 1,
            },
        )

        self.assertEqual(report["schema"], "spine_slot_animation_mesh_weight_parity_report_v1")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["approved_mesh_count"], 1)
        self.assertEqual(report["candidate_mesh_count"], 1)
        self.assertEqual(report["comparisons"][0]["max_weight_sum_error"], 0.0)

    def test_eval_36_mesh_weight_parity_comparator_blocks_bad_weights(self) -> None:
        import copy
        import compare_mesh_weight_parity

        approved = {
            "skins": [
                {
                    "name": "default",
                    "attachments": {
                        "cape_slot": {
                            "cape": {
                                "type": "mesh",
                                "uvs": [0, 0, 1, 0],
                                "triangles": [0, 1, 1],
                                "vertices": [1, 0, -1, -1, 1.0, 1, 0, 1, -1, 1.0],
                                "hull": 2,
                                "width": 8,
                                "height": 8,
                            }
                        }
                    },
                }
            ]
        }
        candidate = copy.deepcopy(approved)
        candidate["skins"][0]["attachments"]["cape_slot"]["cape"]["vertices"][-1] = 0.5

        report = compare_mesh_weight_parity.compare(
            approved,
            candidate,
            {
                "require_exact_vertex_count": True,
                "require_exact_triangle_count": True,
                "max_weight_sum_error": 0.001,
                "max_bones_per_vertex": 1,
            },
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("weight sum error exceeds threshold", "\n".join(report["errors"]))

    def test_eval_37_avatar_runtime_contract_blocks_unverified_runtime(self) -> None:
        import validate_avatar_runtime_contract

        report = validate_avatar_runtime_contract.validate_contract({
            "schema": "spine_slot_animation_avatar_runtime_contract_v1",
            "avatar_id": "safe_avatar",
            "runtime_owner": {"team": "game", "approver": "runtime owner"},
            "default_state": 0,
            "states": [{"id": 0, "idle_animation": "State0Idle"}],
            "events": [{"name": "avatar_awarded", "animation": "State0Idle", "time": 0.1, "consumer": "game"}],
            "runtime_acceptance": {"target_runtime": "target game", "verified": False},
        })

        self.assertEqual(report["schema"], "spine_slot_animation_avatar_runtime_contract_report_v1")
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["runtime_consumer_verified"])
        self.assertIn("runtime_acceptance.verified must be true", "\n".join(report["errors"]))

    def test_eval_37_avatar_runtime_contract_accepts_verified_contract(self) -> None:
        import validate_avatar_runtime_contract

        report = validate_avatar_runtime_contract.validate_contract({
            "schema": "spine_slot_animation_avatar_runtime_contract_v1",
            "avatar_id": "safe_avatar",
            "runtime_owner": {"team": "game", "approver": "runtime owner"},
            "default_state": 0,
            "states": [
                {"id": 0, "idle_animation": "State0Idle"},
                {"id": 1, "idle_animation": "State1Idle", "awarded_animation": "State1Awarded"},
            ],
            "transitions": [{"from": 0, "to": 1, "animation": "State0to1"}],
            "events": [{"name": "avatar_awarded", "animation": "State1Awarded", "time": 0.1, "consumer": "game"}],
            "runtime_acceptance": {"target_runtime": "target game", "verified": True, "evidence": "target_runtime.json"},
        })

        self.assertEqual(report["status"], "ok")
        self.assertTrue(report["runtime_consumer_verified"])
        self.assertEqual(report["state_count"], 2)
        self.assertEqual(report["event_count"], 1)

    def test_expression_composites_no_expression_layers_do_not_fabricate_variants(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_25_NAME + "-no-overlays-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 16, 16, (230, 190, 140, 255))

            out_dir = root / "with_flag_no_overlays"
            run_builder(layer_dir, out_dir, "--composite-expressions")
            skel, atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["expression_composite_attachments_emitted"], 0)
            self.assertEqual(report["expression_composite_expressions"], [])
            self.assertFalse(report["expression_composite_visual_qa"]["enabled"])
            self.assertNotIn("parts/HP3_head_neutral", atlas)
            self.assertNotIn("parts/HP3_head_blink", atlas)
            self.assertEqual(set(skin_attachments(skel)["HP3_head_slot"]), {"parts/HP3_head"})

    def test_expression_overlays_are_not_composited_without_flag(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_25_NAME + "-flag-off-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 16, 16, (230, 190, 140, 255))
            write_rgba_png(layer_dir / "HP3_head_eyes_blink.png", 16, 16, (0, 0, 0, 180))
            write_rgba_png(layer_dir / "HP3_santa_laugh.png", 16, 16, (180, 20, 20, 180))

            out_dir = root / "without_expression_flag"
            run_builder(layer_dir, out_dir)
            skel, atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["expression_composite_attachments_emitted"], 0)
            self.assertEqual(report["expression_composite_expressions"], [])
            self.assertFalse(report["expression_composite_visual_qa"]["enabled"])
            self.assertNotIn("parts/HP3_head_neutral", atlas)
            self.assertNotIn("parts/HP3_head_laugh", atlas)

            attachments = skin_attachments(skel)
            self.assertEqual(set(attachments["HP3_head_slot"]), {"parts/HP3_head"})
            self.assertEqual(set(attachments["HP3_head_eyes_blink_slot"]), {"parts/HP3_head_eyes_blink"})
            self.assertEqual(set(attachments["HP3_santa_laugh_slot"]), {"parts/HP3_santa_laugh"})

            saw_overlay_timeline = False
            for animation in skel["animations"].values():
                slots = animation.get("slots", {})
                self.assertNotIn("attachment", slots.get("HP3_head_slot", {}))
                saw_overlay_timeline = saw_overlay_timeline or (
                    "attachment" in slots.get("HP3_head_eyes_blink_slot", {})
                    or "attachment" in slots.get("HP3_santa_laugh_slot", {})
                )
            self.assertTrue(saw_overlay_timeline)

    def test_expression_detection_supports_canonical_variants(self) -> None:
        from interpret_layers import interpret_layer

        cases = {
            "HP3_head_blink.png": "eyes_blink",
            "HP3_eye_blink.png": "eyes_blink",
            "HP3_head_eyes_closed.png": "eyes_closed",
            "HP3_side_eye.png": "eyes_side",
            "HP3_head_sideeye.png": "eyes_side",
            "HP3_santa_smiling.png": "mouth_smile",
            "HP3_santa_laughing.png": "mouth_laugh",
            "HP3_head_mouth_open.png": "mouth_open",
            "HP3_head_open.png": "mouth_open",
            "HP3_head_mouth_closed.png": "mouth_closed",
            "HP3_head_closed.png": "mouth_closed",
        }
        for name, role in cases.items():
            with self.subTest(name=name):
                interp = interpret_layer(name)
                self.assertEqual(interp.semantic_role, role)
                self.assertEqual(interp.rig_role, "overlay")
                self.assertEqual(interp.alpha_polarity, "hidden_at_rest")

    def test_expression_composites_do_not_fabricate_absent_states(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_25_NAME + "-absent-states-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 16, 16, (230, 190, 140, 255))
            write_rgba_png(layer_dir / "HP3_head_blink.png", 16, 16, (0, 0, 0, 180))

            out_dir = root / "with_one_expression"
            run_builder(layer_dir, out_dir, "--composite-expressions")
            skel, atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(
                set(report["expression_composite_expressions"]),
                {"neutral", "blink"},
            )
            head_slot = next(slot for slot in skel["slots"] if slot["name"] == "HP3_head_slot")
            self.assertEqual(head_slot["attachment"], "parts/HP3_head_neutral")
            self.assertEqual(
                set(skin_attachments(skel)["HP3_head_slot"]),
                {"parts/HP3_head", "parts/HP3_head_neutral", "parts/HP3_head_blink"},
            )
            for absent in ("smile", "laugh", "mouth_open", "mouth_closed", "side_eye"):
                self.assertNotIn(f"parts/HP3_head_{absent}", atlas)

    def test_expression_composites_splice_into_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_25_NAME + "-positive-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 16, 16, (230, 190, 140, 255))
            write_rgba_png(layer_dir / "HP3_head_eyes_blink.png", 16, 16, (0, 0, 0, 180))
            write_rgba_png(layer_dir / "HP3_santa_laugh.png", 16, 16, (180, 20, 20, 180))
            write_rgba_png(layer_dir / "HP3_santa_smile.png", 16, 16, (220, 80, 120, 180))
            write_rgba_png(layer_dir / "HP3_head_mouth_open.png", 16, 16, (120, 0, 0, 180))
            write_rgba_png(layer_dir / "HP3_head_mouth_closed.png", 16, 16, (70, 0, 0, 180))
            write_rgba_png(layer_dir / "HP3_head_eyes_side.png", 16, 16, (0, 40, 80, 180))

            out_dir = root / "with_expressions"
            run_builder(layer_dir, out_dir, "--composite-expressions", "--build-preview")
            skel, atlas, report = load_package(out_dir)
            preview = (out_dir / "preview.html").read_text()

            head_slot = next(slot for slot in skel["slots"] if slot["name"] == "HP3_head_slot")
            self.assertEqual(head_slot["attachment"], "parts/HP3_head_neutral")
            head_attachments = skin_attachments(skel)["HP3_head_slot"]
            for expression in ("neutral", "blink", "smile", "laugh", "mouth_open", "mouth_closed", "side_eye"):
                name = f"parts/HP3_head_{expression}"
                self.assertIn(name, head_attachments)
                self.assertIn(name, atlas)

            self.assertGreaterEqual(report["expression_composite_attachments_emitted"], 7)
            self.assertEqual(
                set(report["expression_composite_expressions"]),
                {"neutral", "blink", "smile", "laugh", "mouth_open", "mouth_closed", "side_eye"},
            )
            self.assertTrue(report["expression_composite_visual_qa"]["enabled"])
            self.assertTrue(report["expression_composite_visual_qa"]["local_eval_executed"])
            self.assertTrue(report["expression_composite_visual_qa"]["passed"])
            self.assertFalse(report["expression_composite_visual_qa"]["browser_runtime_executed"])
            self.assertTrue(report["expression_composite_visual_qa"]["preview_html_generated"])
            self.assertIn("browser/runtime executed: false", preview)

            head_swap_count = 0
            overlay_slots = {
                "HP3_head_eyes_blink_slot",
                "HP3_santa_laugh_slot",
                "HP3_santa_smile_slot",
                "HP3_head_mouth_open_slot",
                "HP3_head_mouth_closed_slot",
                "HP3_head_eyes_side_slot",
            }
            emitted_slot_names = {slot["name"] for slot in skel["slots"]}
            for animation in skel["animations"].values():
                slots = animation.get("slots", {})
                if "attachment" in slots.get("HP3_head_slot", {}):
                    head_swap_count += 1
                for overlay_slot in overlay_slots:
                    self.assertNotIn(overlay_slot, slots)
                    self.assertNotIn(overlay_slot, emitted_slot_names)
                    self.assertNotIn(overlay_slot, skin_attachments(skel))
            self.assertGreater(head_swap_count, 0)

    def test_expression_composites_preserve_duplicate_canonical_layers_in_order(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_25_NAME + "-duplicate-canonical-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 16, 16, (230, 190, 140, 255))
            write_rgba_png(layer_dir / "HP3_head_eyes_blink.png", 16, 16, (0, 0, 0, 120))
            write_rgba_png(layer_dir / "HP3_head_eyes_closed.png", 16, 16, (20, 20, 20, 120))

            out_dir = root / "with_duplicate_blink"
            run_builder(layer_dir, out_dir, "--composite-expressions")
            report = json.loads((out_dir / "validation_report.json").read_text())
            manifest = json.loads((out_dir / "composited_expressions" / "composite_manifest.json").read_text())

            self.assertEqual(report["status"], "ok")
            duplicate = report["expression_composite_validation"]["duplicate_canonical_expression_layers"][0]
            self.assertEqual(duplicate["expression"], "blink")
            self.assertEqual(duplicate["strategy"], "composite_in_layer_order")
            self.assertEqual(
                [Path(path).name for path in manifest["attachments"]["blink"]["source_overlays"]],
                ["HP3_head_eyes_blink.png", "HP3_head_eyes_closed.png"],
            )

    def test_expression_composites_reject_mismatched_overlay_canvas(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_25_NAME + "-mismatched-canvas-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_head.png", 16, 16, (230, 190, 140, 255))
            write_rgba_png(layer_dir / "HP3_head_eyes_blink.png", 8, 8, (0, 0, 0, 180))

            out_dir = root / "with_mismatch"
            result = run_builder_raw(layer_dir, out_dir, "--composite-expressions")
            report = json.loads((out_dir / "validation_report.json").read_text())

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            issue = report["expression_composite_validation"]["issues"][0]
            self.assertEqual(issue["code"], "expression_overlay_canvas_mismatch")
            self.assertTrue(report["expression_composite_validation"]["review_required"])
            self.assertEqual(issue["overlay_size"], [8, 8])
            self.assertEqual(issue["head_size"], [16, 16])

    def test_expression_splicing_preserves_future_overlapping_expression(self) -> None:
        from build_spine_package import _splice_expression_attachment_timelines

        animations = {
            "HP3win": {
                "slots": {
                    "HP3_head_eyes_blink_slot": {
                        "attachment": [
                            {"time": 0, "name": None},
                            {"time": 0.10, "name": "parts/HP3_head_eyes_blink"},
                            {"time": 0.30, "name": None},
                        ]
                    },
                    "HP3_santa_laugh_slot": {
                        "attachment": [
                            {"time": 0, "name": None},
                            {"time": 0.20, "name": "parts/HP3_santa_laugh"},
                            {"time": 0.40, "name": None},
                        ]
                    },
                }
            }
        }
        layout = {
            "expression_composites": {
                "head_slot": "HP3_head_slot",
                "neutral_attachment": "parts/HP3_head_neutral",
                "overlay_slot_to_expression": {
                    "HP3_head_eyes_blink_slot": "blink",
                    "HP3_santa_laugh_slot": "laugh",
                },
                "attachments": {
                    "neutral": {"head_slot_attachment_name": "parts/HP3_head_neutral"},
                    "blink": {"head_slot_attachment_name": "parts/HP3_head_blink"},
                    "laugh": {"head_slot_attachment_name": "parts/HP3_head_laugh"},
                },
            }
        }

        report = _splice_expression_attachment_timelines(animations, layout)

        self.assertEqual(
            animations["HP3win"]["slots"]["HP3_head_slot"]["attachment"],
            [
                {"time": 0.0, "name": "parts/HP3_head_neutral"},
                {"time": 0.10, "name": "parts/HP3_head_blink"},
                {"time": 0.20, "name": "parts/HP3_head_laugh"},
                {"time": 0.40, "name": "parts/HP3_head_neutral"},
            ],
        )
        self.assertNotIn("HP3_head_eyes_blink_slot", animations["HP3win"]["slots"])
        self.assertNotIn("HP3_santa_laugh_slot", animations["HP3win"]["slots"])
        self.assertTrue(report["review_required"])
        self.assertEqual(report["merges"][0]["strategy"], "priority_by_expression")
        self.assertEqual(report["merges"][0]["active_expressions"], ["blink", "laugh"])
        self.assertEqual(report["merges"][0]["selected_expression"], "laugh")

    def test_expression_splicing_preserves_simple_non_overlapping_output(self) -> None:
        from build_spine_package import _splice_expression_attachment_timelines

        animations = {
            "HP3idle": {
                "slots": {
                    "HP3_head_eyes_blink_slot": {
                        "attachment": [
                            {"time": 0, "name": None},
                            {"time": 1.16, "name": "parts/HP3_head_eyes_blink"},
                            {"time": 1.22, "name": None},
                        ]
                    }
                }
            }
        }
        layout = {
            "expression_composites": {
                "head_slot": "HP3_head_slot",
                "neutral_attachment": "parts/HP3_head_neutral",
                "overlay_slot_to_expression": {
                    "HP3_head_eyes_blink_slot": "blink",
                },
                "attachments": {
                    "neutral": {"head_slot_attachment_name": "parts/HP3_head_neutral"},
                    "blink": {"head_slot_attachment_name": "parts/HP3_head_blink"},
                },
            }
        }

        report = _splice_expression_attachment_timelines(animations, layout)

        self.assertEqual(
            animations["HP3idle"]["slots"]["HP3_head_slot"]["attachment"],
            [
                {"time": 0.0, "name": "parts/HP3_head_neutral"},
                {"time": 1.16, "name": "parts/HP3_head_blink"},
                {"time": 1.22, "name": "parts/HP3_head_neutral"},
            ],
        )
        self.assertFalse(report["review_required"])

    def test_expression_splicing_reports_existing_head_attachment_timeline(self) -> None:
        from build_spine_package import _splice_expression_attachment_timelines

        animations = {
            "HP3idle": {
                "slots": {
                    "HP3_head_slot": {
                        "attachment": [
                            {"time": 0, "name": "parts/HP3_head"},
                            {"time": 0.5, "name": "parts/HP3_head_alt"},
                        ]
                    },
                    "HP3_head_eyes_blink_slot": {
                        "attachment": [
                            {"time": 0, "name": None},
                            {"time": 1.16, "name": "parts/HP3_head_eyes_blink"},
                            {"time": 1.22, "name": None},
                        ]
                    },
                }
            }
        }
        layout = {
            "expression_composites": {
                "head_slot": "HP3_head_slot",
                "neutral_attachment": "parts/HP3_head_neutral",
                "overlay_slot_to_expression": {
                    "HP3_head_eyes_blink_slot": "blink",
                },
                "attachments": {
                    "neutral": {"head_slot_attachment_name": "parts/HP3_head_neutral"},
                    "blink": {"head_slot_attachment_name": "parts/HP3_head_blink"},
                },
            }
        }

        report = _splice_expression_attachment_timelines(animations, layout)

        self.assertTrue(report["review_required"])
        self.assertEqual(report["issues"][0]["code"], "existing_head_attachment_timeline")
        self.assertEqual(
            animations["HP3idle"]["slots"]["HP3_head_slot"]["attachment"],
            [
                {"time": 0, "name": "parts/HP3_head"},
                {"time": 0.5, "name": "parts/HP3_head_alt"},
            ],
        )

    def test_eval_21_bezier_profile_emits_numeric_arrays_and_preserves_timing(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_21_NAME + "-positive-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_glow.png", 20, 20, (255, 240, 120, 180))
            controls_path = root / "bezier.controls.json"
            write_controls(controls_path, {
                "export_profile": "spine_43_bezier",
                "bezier_preset": "ease_in_out",
            })

            linear_out = root / "linear"
            bezier_out = root / "bezier"
            run_builder(layer_dir, linear_out)
            run_builder(layer_dir, bezier_out, "--controls", str(controls_path))
            linear_skel, _linear_atlas, linear_report = load_package(linear_out)
            bezier_skel, _bezier_atlas, bezier_report = load_package(bezier_out)

            curves = list(iter_curve_entries(bezier_skel))
            self.assertEqual(linear_report["status"], "ok")
            self.assertEqual(linear_report["export_profile"], "spine_43_linear")
            self.assertEqual(list(iter_curve_entries(linear_skel)), [])
            self.assertEqual(bezier_report["status"], "ok")
            self.assertEqual(bezier_report["export_profile"], "spine_43_bezier")
            self.assertEqual(bezier_report["bezier_profile"]["profile"], "spine_43_bezier")
            self.assertEqual(bezier_report["bezier_profile"]["preset"], "ease_in_out")
            self.assertGreater(bezier_report["bezier_profile"]["curves_emitted"], 0)
            self.assertTrue(bezier_report["bezier_profile"]["key_times_preserved"])
            self.assertTrue(bezier_report["bezier_profile"]["source_durations_preserved"])
            self.assertTrue(bezier_report["bezier_profile"]["endpoint_values_preserved"])
            self.assertGreater(len(bezier_report["bezier_profile"]["source_durations"]), 0)
            self.assertGreater(len(bezier_report["bezier_profile"]["source_key_times"]), 0)
            self.assertTrue(all(isinstance(curve, list) for _name, curve in curves))
            self.assertTrue(all(all(isinstance(value, (int, float)) for value in curve) for _name, curve in curves))
            self.assertTrue(any(name == "translate" and len(curve) == 8 for name, curve in curves))
            self.assertTrue(any(name == "rgba" and len(curve) == 16 for name, curve in curves))

            linear_idle = linear_skel["animations"]["HP3idle"]["bones"]["HP3_body_bone"]["translate"]
            bezier_idle = bezier_skel["animations"]["HP3idle"]["bones"]["HP3_body_bone"]["translate"]
            self.assertEqual([key["time"] for key in bezier_idle], [key["time"] for key in linear_idle])
            self.assertEqual(bezier_idle[0]["y"], linear_idle[0]["y"])
            self.assertEqual(bezier_idle[-1]["y"], linear_idle[-1]["y"])
            self.assertEqual(bezier_idle[0]["y"], bezier_idle[-1]["y"])

    def test_eval_21_v10_linear_is_rejected_by_current_builder(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_21_NAME + "-v10-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            controls_path = root / "v10.controls.json"
            write_controls(controls_path, {"export_profile": "v10_linear"})

            out_dir = root / "v10"
            result = run_builder_raw(layer_dir, out_dir, "--controls", str(controls_path))
            report = json.loads((out_dir / "validation_report.json").read_text())

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["export_profile"], "v10_linear")
            self.assertIn("legacy proof compiler", "\n".join(report["errors"]))
            self.assertIn("Omit export_profile", result.stderr + result.stdout)

    def test_eval_21_unsupported_profile_and_preset_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_21_NAME + "-controls-guard-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            cases = [
                ("old-profile", {"export_profile": "spine_modern_bezier"}, "export_profile 'spine_modern_bezier' is not implemented"),
                ("bad-preset", {"export_profile": "spine_43_bezier", "bezier_preset": "fast"}, "bezier_preset 'fast' is not implemented"),
                ("preset-without-profile", {"bezier_preset": "ease_in"}, "bezier_preset requires export_profile 'spine_43_bezier'"),
            ]
            for label, controls, expected in cases:
                with self.subTest(label=label):
                    controls_path = root / f"{label}.controls.json"
                    write_controls(controls_path, controls)
                    result = run_builder_raw(layer_dir, root / label, "--controls", str(controls_path))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stderr + result.stdout)

    def test_eval_21_curve_validator_rejects_invalid_curves(self) -> None:
        from build_spine_package import validate_skeleton

        with tempfile.TemporaryDirectory(prefix=EVAL_21_NAME + "-validator-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))

            out_dir = root / "base"
            run_builder(layer_dir, out_dir)
            skel, _atlas, _report = load_package(out_dir)
            records = atlas_records_from_skeleton(skel)

            cases = {
                "default-curve": (None, ["export_profile must be 'spine_43_bezier'"], ("bones", "HP3_body_bone", "translate", [0, 0, 0, 0, 0, 0, 0, 0])),
                "v10-curve": ("v10_linear", ["export_profile must be 'spine_43_bezier'"], ("bones", "HP3_body_bone", "translate", [0, 0, 0, 0, 0, 0, 0, 0])),
                "unknown-string": ("spine_43_bezier", ["unsupported curve string 'ease_in'"], ("bones", "HP3_body_bone", "translate", "ease_in")),
                "stepped-string": ("spine_43_bezier", ["unsupported curve string 'stepped'"], ("bones", "HP3_body_bone", "translate", "stepped")),
                "wrong-length": ("spine_43_bezier", ["curve array length 4 must be 8"], ("bones", "HP3_body_bone", "translate", [0, 0, 0, 0])),
                "nonnumeric": ("spine_43_bezier", ["curve array must contain only finite numbers"], ("bones", "HP3_body_bone", "translate", [0, 0, 0, "x", 0, 0, 0, 0])),
                "bool": ("spine_43_bezier", ["curve array must contain only finite numbers"], ("bones", "HP3_body_bone", "translate", [True, 0, 0, 0, 0, 0, 0, 0])),
                "nan": ("spine_43_bezier", ["curve array must contain only finite numbers"], ("bones", "HP3_body_bone", "translate", [float("nan"), 0, 0, 0, 0, 0, 0, 0])),
                "infinity": ("spine_43_bezier", ["curve array must contain only finite numbers"], ("bones", "HP3_body_bone", "translate", [float("inf"), 0, 0, 0, 0, 0, 0, 0])),
                "out-of-segment": ("spine_43_bezier", ["outside key interval"], ("bones", "HP3_body_bone", "translate", [-1, 0, 0, 0, 0, 0, 0, 0])),
                "nonmonotonic": ("spine_43_bezier", ["curve handle times must be monotonic"], ("bones", "HP3_body_bone", "translate", [0.5, 0, 0.25, 0, 0, 0, 0, 0])),
                "attachment": (None, ["attachment must not contain curve fields"], ("slots", "HP3_body_slot", "attachment", [0, 0, 0, 0])),
                "sequence": (None, ["sequence must not contain curve fields"], ("slots", "HP3_body_slot", "sequence", [0, 0, 0, 0])),
                "event": (None, ["events must not contain curve fields"], ("animation", None, "events", [0, 0, 0, 0])),
                "draw-order": (None, ["drawOrder must not contain curve fields"], ("animation", None, "drawOrder", [0, 0, 0, 0])),
                "draw-order-snake": (None, ["draw_order must not contain curve fields"], ("animation", None, "draw_order", [0, 0, 0, 0])),
            }
            for label, (profile, expected_parts, target) in cases.items():
                with self.subTest(label=label):
                    mutated = json.loads(json.dumps(skel))
                    block_name, item_name, timeline_name, curve = target
                    anim = mutated["animations"]["HP3idle"]
                    if block_name == "bones":
                        keys = anim["bones"][item_name][timeline_name]
                    elif block_name == "slots":
                        keys = anim.setdefault("slots", {}).setdefault(item_name, {}).setdefault(
                            timeline_name,
                            [{"time": 0, "name": None}],
                        )
                    else:
                        keys = anim.setdefault(timeline_name, [{"time": 0, "name": "land"}])
                    keys[0]["curve"] = curve
                    report = validate_skeleton(mutated, records, export_profile=profile)
                    issues = "\n".join(report["errors"])
                    for expected in expected_parts:
                        self.assertIn(expected, issues)

    def test_eval_21_curve_application_stability_guard(self) -> None:
        import bezier_curves

        animations = {
            "Loop": {
                "bones": {
                    "body": {
                        "translate": [
                            {"time": 0, "x": 0, "y": 0},
                            {"time": 1, "x": 0, "y": 4},
                            {"time": 2, "x": 0, "y": 0},
                        ]
                    }
                },
                "slots": {
                    "glow": {
                        "rgba": [
                            {"time": 0, "color": "ffffff80"},
                            {"time": 1, "color": "ffffffff"},
                            {"time": 2, "color": "ffffff80"},
                        ],
                        "attachment": [
                            {"time": 0, "name": "parts/glow"},
                            {"time": 1, "name": None},
                        ],
                    }
                },
            }
        }

        report = bezier_curves.apply_bezier_profile(animations, "overshoot")
        self.assertEqual(report["curves_emitted"], 4)
        self.assertEqual(len(animations["Loop"]["bones"]["body"]["translate"][0]["curve"]), 8)
        self.assertEqual(len(animations["Loop"]["slots"]["glow"]["rgba"][0]["curve"]), 16)
        self.assertNotIn("curve", animations["Loop"]["slots"]["glow"]["attachment"][0])
        self.assertEqual(animations["Loop"]["bones"]["body"]["translate"][0]["time"], 0)
        self.assertEqual(animations["Loop"]["bones"]["body"]["translate"][-1]["time"], 2)
        self.assertEqual(animations["Loop"]["bones"]["body"]["translate"][0]["y"], 0)
        self.assertEqual(animations["Loop"]["bones"]["body"]["translate"][-1]["y"], 0)

        before = bezier_curves._snapshot_timing_and_values(animations)
        animations["Loop"]["bones"]["body"]["translate"][1]["time"] = 1.25
        animations["Loop"]["bones"]["body"]["translate"][-1]["y"] = 1
        issues = bezier_curves.validate_curve_application_stability(before, animations)
        self.assertTrue(any("key times changed" in issue for issue in issues))
        self.assertTrue(any("endpoint values changed" in issue for issue in issues))

    def test_eval_22_symbol_frame_glow_uses_available_slots_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_22_NAME + "-frame-glow-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_frame.png", 24, 24, (80, 60, 140, 255))
            write_rgba_png(layer_dir / "HP3_frame_glow.png", 24, 24, (180, 220, 255, 180))
            write_rgba_png(layer_dir / "HP3_sparkle.png", 8, 8, (255, 255, 140, 180))

            out_dir = root / "with_frame_glow"
            run_builder(layer_dir, out_dir)
            skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["ui_system_template"], "symbol_frame_glow")
            self.assertFalse(report["ui_system_review_required"])
            self.assertIsNone(report["ui_system_unsupported_reason"])
            self.assertIn("detected source slots", "\n".join(report["ui_system_evidence"]))
            self.assertIn("HP3_frame_bone", skel["animations"]["HP3idle"]["bones"])
            self.assertIn("HP3_frame_glow_slot", skel["animations"]["HP3idle"]["slots"])
            self.assertIn("HP3_sparkle_slot", skel["animations"]["HP3win"]["slots"])
            self.assertNotIn("HP3_glow_slot", skel["skins"][0]["attachments"])

    def test_eval_22_non_symbol_ui_family_reports_supported_policy(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_22_NAME + "-winframe-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "WinFrame_frame.png", 24, 24, (80, 60, 140, 255))
            write_rgba_png(layer_dir / "WinFrame_glow.png", 24, 24, (180, 220, 255, 180))

            out_dir = root / "winframe"
            run_builder(layer_dir, out_dir, family="winframe_explode")
            skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["ui_system_template"], "winframe_explode")
            self.assertFalse(report["ui_system_review_required"])
            self.assertEqual(set(skel["animations"]), {"WinFrame", "WinFrameidle", "WinFrameExplode"})
            self.assertIn("WinFrame_frame_bone", skel["animations"]["WinFrame"]["bones"])
            assert_portable_ui_evidence(self, report)

    def test_eval_22_all_supported_ui_families_are_evidence_backed(self) -> None:
        from compose_animations import NON_SYMBOL_FAMILIES
        import ui_system_policy

        policy = ui_system_policy.load_policy()
        policy_ui_families = {
            template["family"]
            for template in policy["supported_templates"].values()
            if template.get("family") in NON_SYMBOL_FAMILIES
        }
        self.assertEqual(policy_ui_families, set(NON_SYMBOL_FAMILIES))
        for family, animation_names in NON_SYMBOL_FAMILIES.items():
            self.assertEqual(policy["supported_templates"][family]["animation_names"], animation_names)
            with self.subTest(family=family), tempfile.TemporaryDirectory(prefix=EVAL_22_NAME + "-" + family + "-") as tmp:
                root = Path(tmp)
                layer_dir = root / "layers"
                layer_dir.mkdir()
                write_rgba_png(layer_dir / f"{family}_body.png", 24, 24, (80, 60, 140, 255))

                out_dir = root / family
                run_builder(layer_dir, out_dir, family=family)
                skel, _atlas, report = load_package(out_dir)

                self.assertEqual(report["status"], "ok")
                self.assertEqual(report["ui_system_template"], family)
                self.assertFalse(report["ui_system_review_required"])
                self.assertIsNone(report["ui_system_unsupported_reason"])
                self.assertEqual(set(skel["animations"]), set(animation_names))
                assert_portable_ui_evidence(self, report)

    def test_eval_22_policy_evidence_primary_refs_are_portable(self) -> None:
        import ui_system_policy

        policy = ui_system_policy.load_policy()
        self.assertEqual(policy["source_policy"]["allowed_evidence_roots"], ["assets/compiler_evidence_index.json"])
        self.assertTrue(policy["source_policy"]["original_source_paths_are_metadata"])
        for section_name in ("supported_templates", "review_only_buckets"):
            for key, entry in policy[section_name].items():
                with self.subTest(section=section_name, key=key):
                    self.assertTrue(entry["evidence"])
                    for evidence in entry["evidence"]:
                        self.assertTrue(evidence.startswith("assets/compiler_evidence_index.json:"), evidence)
                    self.assertTrue(entry.get("original_source_paths"))
        self.assertIn("unknown", policy["review_only_buckets"])

    def test_eval_22_missing_evidence_index_blocks_supported_policy(self) -> None:
        import ui_system_policy

        with tempfile.TemporaryDirectory(prefix=EVAL_22_NAME + "-missing-evidence-") as tmp:
            missing_index = Path(tmp) / "missing_compiler_evidence_index.json"
            report = ui_system_policy.build_ui_system_report(
                "meter",
                evidence_index_path=missing_index,
            )

            self.assertEqual(report["ui_system_template"], "meter")
            self.assertTrue(report["ui_system_review_required"])
            self.assertEqual(report["evidence_index_status"], "missing")
            self.assertIsNone(report["evidence_index_source_hash"])
            self.assertIn("assets/compiler_evidence_index.json did not validate", report["ui_system_unsupported_reason"])

    def test_eval_22_stale_evidence_index_blocks_supported_policy(self) -> None:
        import ui_system_policy

        with tempfile.TemporaryDirectory(prefix=EVAL_22_NAME + "-stale-evidence-") as tmp:
            stale_index = Path(tmp) / "compiler_evidence_index.json"
            stale_index.write_text(json.dumps({
                "schema": "claude_spine_compiler_evidence_index_v1",
                "sources": {
                    "family_recipe_specs": {
                        "required": True,
                        "exists": False,
                        "status": "missing",
                    }
                },
                "query_indexes": {
                    "recipes_by_family": {},
                    "ui_buckets_by_bucket": {},
                },
            }))
            report = ui_system_policy.build_ui_system_report(
                "meter",
                evidence_index_path=stale_index,
            )

            self.assertEqual(report["evidence_index_status"], "stale")
            self.assertTrue(report["ui_system_review_required"])
            issues = "\n".join(report["ui_system_evidence_index_validation"]["issues"])
            self.assertIn("source_hash is missing", issues)
            self.assertIn("family_recipe_specs", issues)

    def test_eval_23_background_parallax_stays_review_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_23_NAME + "-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "BG_far.png", 32, 32, (10, 20, 60, 255))
            write_rgba_png(layer_dir / "BG_near.png", 32, 32, (20, 40, 100, 180))

            out_dir = root / "background_review_only"
            result = run_builder_raw(layer_dir, out_dir, family="background_parallax")
            report = json.loads((out_dir / "validation_report.json").read_text())

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["ui_system_template"], "background_parallax")
            self.assertTrue(report["ui_system_review_required"])
            self.assertIn("no deterministic background layer", report["ui_system_unsupported_reason"])
            assert_portable_ui_evidence(self, report)
            self.assertIn("generated/ui_animation_coverage", "\n".join(report["ui_system_evidence_source_metadata"]["original_source_paths"]))
            self.assertFalse((out_dir / "shared_symbols.json").exists())

    def test_eval_23_unknown_alias_stays_review_only_with_unknown_bucket_evidence(self) -> None:
        import ui_system_policy

        report = ui_system_policy.build_ui_system_report("unknown")

        self.assertEqual(report["ui_system_template"], "unknown")
        self.assertTrue(report["ui_system_review_required"])
        self.assertIn("Unknown UI/system records", report["ui_system_unsupported_reason"])
        self.assertIn("ui_buckets_by_bucket.unknown_ui_or_system", "\n".join(report["ui_system_evidence"]))
        assert_portable_ui_evidence(self, report)

    def test_eval_24_policy_permitted_physics_emits_with_preview_hook(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_24_NAME + "-permitted-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_hair.png", 12, 12, (40, 20, 10, 255))

            out_dir = root / "with_physics"
            run_builder(layer_dir, out_dir, "--enable-physics", "--build-preview")
            skel, _atlas, report = load_package(out_dir)
            preview = (out_dir / "preview.html").read_text()

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["physics_constraints_emitted"], 1)
            self.assertEqual(len(skel.get("physics", [])), 1)
            self.assertEqual(skel["physics"][0]["bone"], "HP3_hair_bone")
            self.assertEqual(report["physics_candidates"][0]["candidate_role"], "hair")
            self.assertEqual(report["physics_candidates"][0]["policy_decision"], "default_on")
            self.assertTrue(report["physics_preview_required"])
            self.assertTrue(report["physics_preview_html_generated"])
            self.assertNotIn("physics_runtime_proof", report)
            requirements = report["physics_runtime_requirements"]
            self.assertTrue(requirements["preview_required"])
            self.assertFalse(requirements["local_runtime_executed"])
            self.assertFalse(requirements["art_approval_claimed"])
            self.assertIn("updates physics at runtime", preview)

    def test_eval_24_review_only_candidate_does_not_emit(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_24_NAME + "-review-only-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_dress.png", 18, 24, (180, 40, 120, 255))

            out_dir = root / "review_only"
            run_builder(layer_dir, out_dir, "--enable-physics")
            skel, _atlas, report = load_package(out_dir)

            self.assertNotIn("physics", skel)
            self.assertEqual(report["physics_constraints_emitted"], 0)
            self.assertEqual(report["physics_candidates"][0]["candidate_role"], "dress")
            self.assertEqual(report["physics_candidates"][0]["policy_decision"], "review_only")
            self.assertTrue(report["physics_review_required"])

    def test_eval_24_raw_keyword_candidate_is_review_only(self) -> None:
        import physics_constraints

        layout = {
            "bones": [
                {"name": "root"},
                {
                    "name": "HP3_hair_bone",
                    "parent": "root",
                    "layer_name": "HP3_hair",
                    "semantic_role": "unknown",
                    "rig_role": "root_static",
                },
            ],
            "slots": [],
            "attachments": [],
        }

        result = physics_constraints.build_physics_constraints_with_report(
            layout,
            emit_enabled=True,
        )

        self.assertEqual(result["constraints"], [])
        self.assertEqual(result["candidates"][0]["candidate_role"], "hair")
        self.assertEqual(result["candidates"][0]["policy_decision"], "review_only")
        self.assertEqual(result["candidates"][0]["evidence_source"], "layer_name")
        self.assertFalse(result["candidates"][0]["trusted_evidence"])
        self.assertTrue(result["review_required"])

    def test_eval_24_invalid_physics_plan_fields_fail_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_24_NAME + "-invalid-plan-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_mystery.png", 12, 12, (40, 20, 10, 255))
            plan_path = root / "physics_plan.json"
            write_physics_plan(plan_path, [{
                "bone": "HP3_mystery_bone",
                "role": "hair",
                "reviewed": True,
                "overrides": {
                    "rotate": "fast",
                    "stretch": 12,
                },
            }])

            out_dir = root / "invalid_plan"
            result = run_builder_raw(
                layer_dir,
                out_dir,
                "--enable-physics",
                "--physics-plan",
                str(plan_path),
            )
            self.assertNotEqual(result.returncode, 0)
            _skel, _atlas, report = load_package(out_dir)
            issues = "\n".join(report["errors"])
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["physics_constraints_emitted"], 0)
            self.assertIn("overrides.rotate must be a finite number", issues)
            self.assertIn("overrides.stretch is not allowed", issues)

    def test_eval_24_invalid_physics_plan_top_level_shapes_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_24_NAME + "-invalid-plan-shape-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))

            for label, raw_plan in (("object", "{}"), ("null", "null")):
                with self.subTest(label=label):
                    plan_path = root / f"physics_plan_{label}.json"
                    plan_path.write_text(raw_plan)
                    out_dir = root / f"invalid_plan_{label}"
                    result = run_builder_raw(
                        layer_dir,
                        out_dir,
                        "--enable-physics",
                        "--physics-plan",
                        str(plan_path),
                    )
                    self.assertNotEqual(result.returncode, 0)
                    _skel, _atlas, report = load_package(out_dir)
                    self.assertEqual(report["status"], "failed")
                    self.assertEqual(report["physics_constraints_emitted"], 0)
                    self.assertIn("physics plan must be a list of objects", "\n".join(report["errors"]))

    def test_eval_24_no_physics_package_has_no_physics_preview_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_24_NAME + "-no-physics-preview-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))

            out_dir = root / "no_physics"
            run_builder(layer_dir, out_dir, "--build-preview")
            _skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["physics_candidates"], [])
            self.assertEqual(report["physics_constraints_emitted"], 0)
            self.assertFalse(report["physics_preview_required"])
            self.assertFalse(report["physics_preview_html_generated"])
            self.assertFalse(report["physics_runtime_requirements"]["preview_required"])
            self.assertFalse(report["physics_runtime_requirements"]["local_runtime_executed"])

    def test_eval_24_zero_length_bone_warning_for_active_rotate_slider(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_24_NAME + "-zero-length-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            write_rgba_png(layer_dir / "HP3_cape.png", 18, 24, (80, 20, 160, 255))

            out_dir = root / "zero_length"
            run_builder(layer_dir, out_dir, "--enable-physics")
            _skel, _atlas, report = load_package(out_dir)

            self.assertEqual(report["physics_constraints_emitted"], 1)
            self.assertEqual(report["zero_length_bone_warnings"][0]["bone"], "HP3_cape_bone")
            self.assertIn("rotate", report["zero_length_bone_warnings"][0]["active_sliders"])
            self.assertIn("rotate", report["physics_active_sliders"]["HP3_cape_bone"])
            self.assertTrue(report["physics_review_required"])

    def test_eval_24_over_max_constraints_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_24_NAME + "-over-max-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
            for name, color in (
                ("HP3_hair.png", (40, 20, 10, 255)),
                ("HP3_cape.png", (80, 20, 160, 255)),
                ("HP3_tail.png", (120, 40, 20, 255)),
                ("HP3_antennae.png", (20, 180, 160, 255)),
            ):
                write_rgba_png(layer_dir / name, 12, 12, color)

            out_dir = root / "over_max"
            result = run_builder_raw(layer_dir, out_dir, "--enable-physics")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((out_dir / "validation_report.json").read_text())

            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["physics_constraints_emitted"], 0)
            self.assertEqual(len(report["physics_candidates"]), 4)
            self.assertIn("max_constraints_per_symbol", "\n".join(report["physics_max_constraint_violations"]))

    def test_eval_24_wardrobe_keyword_semantics(self) -> None:
        from interpret_layers import interpret_layer
        import physics_constraints

        expected_roles = {
            "HP3_hair": "hair",
            "HP3_beard": "beard",
            "HP3_mustache": "mustache",
            "HP3_dress": "dress",
            "HP3_skirt": "skirt",
            "HP3_robe": "robe",
            "HP3_cloak": "cloak",
            "HP3_cape": "cape",
            "HP3_sleeve": "sleeve",
            "HP3_scarf": "scarf",
            "HP3_ribbon": "ribbon",
            "HP3_belt": "belt",
            "HP3_chain": "chain",
            "HP3_necklace": "necklace",
            "HP3_earrings": "earrings",
            "HP3_dangling_jewelry": "dangling_jewelry",
            "HP3_tail": "tails",
            "HP3_wings": "wings",
            "HP3_antennae": "antennae",
        }
        layers = []
        for name, expected_role in expected_roles.items():
            interp = interpret_layer(name)
            self.assertEqual(interp.semantic_role, expected_role)
            layers.append({
                "name": f"{name}_bone",
                "layer_name": name,
                "semantic_role": interp.semantic_role,
                "rig_role": interp.rig_role,
            })

        candidates = physics_constraints.detect_physics_candidates({"bones": layers})
        candidate_roles = {candidate["candidate_role"] for candidate in candidates}
        self.assertEqual(candidate_roles, set(expected_roles.values()))

    def test_eval_26_avatar_state_manifest_declares_graph_without_event_timelines(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + "-positive-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            for name, color in (
                ("State0Idle.png", (40, 80, 140, 255)),
                ("State0to1.png", (80, 120, 180, 255)),
                ("State1Idle.png", (100, 160, 80, 255)),
                ("State1Awarded.png", (220, 190, 60, 255)),
                ("State1Close.png", (120, 90, 50, 255)),
            ):
                write_rgba_png(layer_dir / name, 16, 16, color)

            out_dir = root / "avatar"
            run_builder(layer_dir, out_dir, family="avatar")
            skel, _atlas, report = load_package(out_dir)
            manifest = json.loads((out_dir / "avatar_state_manifest.json").read_text())

            self.assertEqual(report["status"], "ok")
            self.assertTrue(report["avatar_manifest_emitted"])
            self.assertTrue(report["avatar_runtime_required"])
            self.assertFalse(report["avatar_runtime_consumer_verified"])
            self.assertEqual(report["avatar_state_count"], 2)
            self.assertEqual(report["avatar_transition_count"], 1)
            self.assertEqual(manifest["schema"], "spine_slot_animation_avatar_state_manifest_v1")
            self.assertEqual(manifest["default_state"], "state_0")
            self.assertEqual(manifest["persistent_state_owner"], "game_runtime")
            self.assertFalse(manifest["persistent_state_claimed_in_spine"])
            self.assertFalse(manifest["runtime_consumer_verified"])
            self.assertFalse(manifest["event_timelines_emitted"])
            self.assertEqual(
                set(manifest["event_names"]),
                {
                    "avatar/state_0_to_1",
                    "avatar/state_1_awarded",
                    "avatar/state_1_close",
                },
            )
            self.assertEqual(set(report["avatar_events_declared"]), set(manifest["event_names"]))
            self.assertNotIn("events", skel)
            self.assertFalse(any("events" in anim for anim in skel["animations"].values()))

    def test_eval_26_avatar_event_plan_must_match_manifest_names_and_times(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + "-events-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            for name, color in (
                ("State0Idle.png", (40, 80, 140, 255)),
                ("State0to1.png", (80, 120, 180, 255)),
                ("State1Idle.png", (100, 160, 80, 255)),
                ("State1Awarded.png", (220, 190, 60, 255)),
                ("State1Close.png", (120, 90, 50, 255)),
            ):
                write_rgba_png(layer_dir / name, 16, 16, color)
            plan_path = root / "avatar_events.json"
            write_event_plan(plan_path, {
                "events": {
                    "avatar/state_0_to_1": {},
                    "avatar/state_1_awarded": {},
                    "avatar/state_1_close": {},
                },
                "animations": {
                    "State0to1": [{"time": 0.2, "name": "avatar/state_0_to_1"}],
                    "State1Awarded": [{"time": 0.6, "name": "avatar/state_1_awarded"}],
                    "State1Close": [{"time": 0.4, "name": "avatar/state_1_close"}],
                },
            })

            out_dir = root / "avatar_events"
            run_builder(layer_dir, out_dir, "--enable-events", str(plan_path), family="avatar")
            skel, _atlas, report = load_package(out_dir)
            manifest = json.loads((out_dir / "avatar_state_manifest.json").read_text())

            self.assertEqual(report["status"], "ok")
            self.assertTrue(report["avatar_event_timelines_emitted"])
            self.assertTrue(manifest["event_timelines_emitted"])
            self.assertEqual(set(skel["events"]), set(manifest["event_names"]))
            self.assertEqual(
                skel["animations"]["State1Awarded"]["events"],
                [{"time": 0.6, "name": "avatar/state_1_awarded"}],
            )

    def test_eval_26_avatar_event_plan_rejects_wrong_manifest_time(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + "-bad-event-time-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            for name, color in (
                ("State0Idle.png", (40, 80, 140, 255)),
                ("State0to1.png", (80, 120, 180, 255)),
                ("State1Idle.png", (100, 160, 80, 255)),
            ):
                write_rgba_png(layer_dir / name, 16, 16, color)
            plan_path = root / "avatar_events_bad_time.json"
            write_event_plan(plan_path, {
                "events": {
                    "avatar/state_0_to_1": {},
                },
                "animations": {
                    "State0to1": [{"time": 0.3, "name": "avatar/state_0_to_1"}],
                },
            })

            out_dir = root / "avatar_bad_event_time"
            result = run_builder_raw(layer_dir, out_dir, "--enable-events", str(plan_path), family="avatar")
            skel, _atlas, report = load_package(out_dir)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            self.assertIn("expected 0.2", "\n".join(report["event_plan_errors"]))
            self.assertFalse(report["avatar_event_timelines_emitted"])
            self.assertNotIn("events", skel)
            self.assertFalse(any("events" in anim for anim in skel["animations"].values()))

    def test_eval_26_avatar_rejects_malformed_state_layer_names(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + "-malformed-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "State0Idle.png", 16, 16, (40, 80, 140, 255))
            write_rgba_png(layer_dir / "StateOneIdle.png", 16, 16, (100, 160, 80, 255))

            out_dir = root / "avatar_malformed"
            result = run_builder_raw(layer_dir, out_dir, family="avatar")
            report = json.loads((out_dir / "validation_report.json").read_text())
            manifest = json.loads((out_dir / "avatar_state_manifest.json").read_text())

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(report["avatar_manifest_emitted"])
            self.assertIn("StateOneIdle", "\n".join(report["errors"]))
            self.assertIn("StateOneIdle", "\n".join(manifest["issues"]))

    def test_eval_26_avatar_rejects_missing_default_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + "-missing-default-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "State1Idle.png", 16, 16, (100, 160, 80, 255))
            write_rgba_png(layer_dir / "State1Awarded.png", 16, 16, (220, 190, 60, 255))

            out_dir = root / "avatar_missing_default"
            result = run_builder_raw(layer_dir, out_dir, family="avatar")
            report = json.loads((out_dir / "validation_report.json").read_text())
            manifest = json.loads((out_dir / "avatar_state_manifest.json").read_text())

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["avatar_state_count"], 1)
            self.assertIsNone(manifest["default_state"])
            self.assertIn("default state requires State0Idle", "\n".join(report["errors"]))

    def test_eval_26_avatar_rejects_orphan_transition_references(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + "-orphan-transition-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "State0Idle.png", 16, 16, (40, 80, 140, 255))
            write_rgba_png(layer_dir / "State0to2.png", 16, 16, (80, 120, 180, 255))

            out_dir = root / "avatar_orphan_transition"
            result = run_builder_raw(layer_dir, out_dir, family="avatar")
            report = json.loads((out_dir / "validation_report.json").read_text())
            manifest = json.loads((out_dir / "avatar_state_manifest.json").read_text())
            errors = "\n".join(report["errors"])

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            self.assertIn("State0to2 references missing to_state state_2", errors)
            self.assertIn("State0to2 references missing to_state state_2", "\n".join(manifest["issues"]))

    def test_eval_26_avatar_rejects_orphan_awarded_and_close_references(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + "-orphan-beats-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "State0Idle.png", 16, 16, (40, 80, 140, 255))
            write_rgba_png(layer_dir / "State2Awarded.png", 16, 16, (220, 190, 60, 255))
            write_rgba_png(layer_dir / "State2Close.png", 16, 16, (120, 90, 50, 255))

            out_dir = root / "avatar_orphan_beats"
            result = run_builder_raw(layer_dir, out_dir, family="avatar")
            report = json.loads((out_dir / "validation_report.json").read_text())
            errors = "\n".join(report["errors"])

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            self.assertIn("State2Awarded references missing state state_2", errors)
            self.assertIn("State2Close references missing state state_2", errors)

    def test_eval_26_avatar_rejects_duplicate_state_ids(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + "-duplicate-state-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "State0Idle.png", 16, 16, (40, 80, 140, 255))
            write_rgba_png(layer_dir / "State0.png", 16, 16, (100, 160, 80, 255))

            out_dir = root / "avatar_duplicate_state"
            result = run_builder_raw(layer_dir, out_dir, family="avatar")
            report = json.loads((out_dir / "validation_report.json").read_text())

            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "failed")
            self.assertIn("duplicate avatar state id 'state_0'", "\n".join(report["errors"]))

    def test_eval_26_avatar_event_plan_shape_errors_are_reported_without_traceback(self) -> None:
        malformed_plans = {
            "non_dict_key": {
                "events": {"avatar/state_0_to_1": {}},
                "animations": {"State0to1": ["avatar/state_0_to_1"]},
            },
            "non_list_animation": {
                "events": {"avatar/state_0_to_1": {}},
                "animations": {"State0to1": {"time": 0.2, "name": "avatar/state_0_to_1"}},
            },
            "missing_time": {
                "events": {"avatar/state_0_to_1": {}},
                "animations": {"State0to1": [{"name": "avatar/state_0_to_1"}]},
            },
            "non_numeric_time": {
                "events": {"avatar/state_0_to_1": {}},
                "animations": {"State0to1": [{"time": "0.2", "name": "avatar/state_0_to_1"}]},
            },
        }
        for label, plan in malformed_plans.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(prefix=EVAL_26_NAME + f"-malformed-event-{label}-") as tmp:
                    root = Path(tmp)
                    layer_dir = root / "layers"
                    layer_dir.mkdir()
                    write_avatar_state_layers(layer_dir)
                    plan_path = root / "avatar_events.json"
                    write_event_plan(plan_path, plan)

                    out_dir = root / "avatar_malformed_event"
                    result = run_builder_raw(layer_dir, out_dir, "--enable-events", str(plan_path), family="avatar")
                    report = json.loads((out_dir / "validation_report.json").read_text())
                    output = result.stdout + result.stderr

                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(report["status"], "failed")
                    self.assertTrue(report["event_plan_errors"])
                    self.assertNotIn("Traceback", output)

    def test_eval_26_source_art_project_write_guard_blocks_prohibited_roots(self) -> None:
        import build_spine_package as bsp

        blocked = bsp._source_art_write_guard_error(Path(r"G:\artSource\game\layers").parent)
        allowed = bsp._source_art_write_guard_error(Path(r"C:\safe\game\layers").parent)

        self.assertIsNotNone(blocked)
        self.assertIn("PROJECT_CONTEXT.json or LEARNING_LOG.jsonl", blocked)
        self.assertIsNone(allowed)

    def test_eval_27_package_output_guard_rejects_source_art_out_dir_before_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_27_NAME + "-out-dir-guard-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))

            out_dir = Path(r"G:\artSource\claude_spine_generator_eval_out")
            result = run_builder_raw(layer_dir, out_dir)
            output = result.stdout + result.stderr

            self.assertEqual(result.returncode, 2)
            self.assertIn("refusing to write package outputs under prohibited source-art root", output)
            self.assertIn('"status": "failed"', output)
            self.assertNotIn("Traceback", output)

    def test_eval_27_event_payload_errors_are_reported_without_traceback(self) -> None:
        cases = {
            "default-volume": (
                {"volume": 1.5},
                {},
                "volume must be a finite number in [0, 1]",
            ),
            "key-balance": (
                {},
                {"balance": -1.5},
                "balance must be a finite number in [-1, 1]",
            ),
            "default-string": (
                {"string": 123},
                {},
                "string must be a string",
            ),
            "key-audio": (
                {},
                {"audio": ""},
                "audio must be a non-empty string",
            ),
            "key-int": (
                {},
                {"int": 1.5},
                "int must be an integer",
            ),
            "default-float": (
                {"float": "0.5"},
                {},
                "float must be a finite number",
            ),
        }
        for label, (defaults, key_payload, expected) in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(prefix=EVAL_27_NAME + f"-event-{label}-") as tmp:
                    root = Path(tmp)
                    layer_dir = root / "layers"
                    layer_dir.mkdir()
                    write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))
                    plan_path = root / "events.json"
                    key = {"time": 0.2, "name": "fx/test", **key_payload}
                    write_event_plan(plan_path, {
                        "events": {"fx/test": defaults},
                        "animations": {"HP3win": [key]},
                    })

                    out_dir = root / "out"
                    result = run_builder_raw(layer_dir, out_dir, "--enable-events", str(plan_path))
                    report = json.loads((out_dir / "validation_report.json").read_text())
                    output = result.stdout + result.stderr

                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(report["status"], "failed")
                    self.assertIn(expected, "\n".join(report["event_plan_errors"]))
                    self.assertNotIn("Traceback", output)

    def test_eval_28_missing_profile_blocks_production_export_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-missing-profile-") as tmp:
            package_dir = Path(tmp)
            write_production_gate_validation_report(package_dir / "validation_report.json")

            report, exit_code = production_export_gate.run_gate(package_dir, None)

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "blocked")
            self.assertFalse(report["export_invoked"])
            self.assertFalse(report["cli_invocation_allowed"])
            self.assertIn("production export profile is required", "\n".join(report["errors"]))
            self.assertTrue((package_dir / "production_export_gate_report.json").exists())

    def test_eval_28_incomplete_profile_blocks_missing_approvals(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-incomplete-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(
                package_dir / "runtime_acceptance.json",
                production_gate_package_identity(package_dir),
            )
            profile = production_export_profile()
            profile.pop("license_posture")
            profile["approver"] = {"name": "", "role": "Art Director"}
            profile_path.write_text(json.dumps(profile, indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)
            errors = "\n".join(report["errors"])

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "blocked")
            self.assertIn("profile.license_posture is required", errors)
            self.assertIn("profile.approver.name is required", errors)
            self.assertFalse(report["export_invoked"])

    def test_eval_28_unsafe_perforce_or_source_art_write_request_blocks_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-unsafe-write-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(
                package_dir / "runtime_acceptance.json",
                production_gate_package_identity(package_dir),
            )
            profile = production_export_profile(write_policy={
                "perforce_writes": True,
                "source_art_writes": True,
            })
            profile_path.write_text(json.dumps(profile, indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)
            errors = "\n".join(report["errors"])

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "blocked")
            self.assertIn("perforce_writes must be false", errors)
            self.assertIn("source_art_writes must be false", errors)
            self.assertFalse(report["cli_invocation_allowed"])

    def test_eval_28_approved_provenance_profile_is_ready_for_manual_export_only(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-ready-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(
                package_dir / "validation_report.json",
                skin_variants_emitted=1,
                sequence_attachments_emitted=1,
                events_defined=1,
            )
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(
                package_dir / "runtime_acceptance.json",
                production_gate_package_identity(package_dir),
                skins=True,
                sequences=True,
                events=True,
            )
            profile = production_export_profile(advanced_features={
                "claimed_counts": {
                    "skins": 1,
                    "physics": 0,
                    "sequences": 1,
                    "clipping": 0,
                    "events": 1,
                    "blends": 0,
                },
            })
            profile_path.write_text(json.dumps(profile, indent=2))

            report, exit_code = production_export_gate.run_gate(
                package_dir,
                profile_path,
                runtime_probe_executed_by_gate=True,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(report["status"], "ready_for_manual_export")
            self.assertTrue(report["manual_export_ready"])
            self.assertFalse(report["export_invoked"])
            self.assertFalse(report["cli_invocation_allowed"])
            self.assertEqual(report["runtime_acceptance_status"], "verified_browser_runtime")
            self.assertFalse(report["runtime_acceptance_provenance"]["report_only"])
            self.assertEqual(report["runtime_acceptance_required_features"], ["skins", "sequences", "events"])

    def test_eval_28_browser_runtime_evidence_file_blocks_without_gate_probe(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-self-attested-browser-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(
                package_dir / "runtime_acceptance.json",
                production_gate_package_identity(package_dir),
            )
            profile_path.write_text(json.dumps(production_export_profile(), indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)
            errors = "\n".join(report["errors"])

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["runtime_acceptance_status"], "browser_runtime_evidence_file_unverified")
            self.assertIn("must run the runtime acceptance probe", errors)

    def test_eval_28_report_only_runtime_fixture_blocks_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-report-only-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(
                package_dir / "runtime_acceptance.json",
                production_gate_package_identity(package_dir),
                provenance={
                    "method": "runtime_probe",
                    "tool": "h5g-runtime-acceptance-probe",
                    "tool_version": "report-only-fixture-v1",
                    "execution_mode": "report_only_fixture",
                    "execution_id": "local-eval-runtime-probe-001",
                    "executed_at": "2026-05-18T12:20:00-04:00",
                },
            )
            profile_path.write_text(json.dumps(production_export_profile(), indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)
            errors = "\n".join(report["errors"])

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "blocked")
            self.assertFalse(report["manual_export_ready"])
            self.assertEqual(report["runtime_acceptance_status"], "report_only_unverified")
            self.assertTrue(report["runtime_acceptance_provenance"]["report_only"])
            self.assertIn("runtime evidence.provenance.tool_version must be 'runtime-acceptance-probe-v1'", errors)
            self.assertIn("runtime evidence.provenance.execution_mode must be 'browser_runtime'", errors)

    def test_eval_28_static_runtime_evidence_without_approved_provenance_blocks_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-static-evidence-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(
                package_dir / "runtime_acceptance.json",
                production_gate_package_identity(package_dir),
                provenance={
                    "method": "static_review",
                    "tool": "manual-checklist",
                    "tool_version": "1",
                    "execution_mode": "manual",
                    "execution_id": "self-attested",
                    "executed_at": "2026-05-18T12:20:00-04:00",
                },
            )
            profile_path.write_text(json.dumps(production_export_profile(), indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)
            errors = "\n".join(report["errors"])

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "blocked")
            self.assertFalse(report["manual_export_ready"])
            self.assertEqual(report["runtime_acceptance_status"], "static_unverified")
            self.assertIn("runtime evidence.provenance.method must be 'runtime_probe'", errors)
            self.assertIn("runtime evidence.provenance.tool must be 'h5g-runtime-acceptance-probe'", errors)

    def test_eval_28_extra_profile_schema_fields_block_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-profile-extra-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(
                package_dir / "runtime_acceptance.json",
                production_gate_package_identity(package_dir),
            )
            profile = production_export_profile(unreviewed_top_level=True)
            profile["runtime"]["unreviewed_nested"] = True
            profile["advanced_features"]["claimed_counts"]["skins"] = True
            profile_path.write_text(json.dumps(profile, indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)
            errors = "\n".join(report["errors"])

            self.assertEqual(exit_code, 2)
            self.assertIn("profile.unreviewed_top_level is not allowed", errors)
            self.assertIn("profile.runtime.unreviewed_nested is not allowed", errors)
            self.assertIn("profile.advanced_features.claimed_counts.skins must be a non-negative integer", errors)

    def test_eval_28_extra_runtime_evidence_fields_block_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-runtime-extra-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            evidence_path = package_dir / "runtime_acceptance.json"
            write_runtime_acceptance_evidence(evidence_path, production_gate_package_identity(package_dir))
            evidence = json.loads(evidence_path.read_text())
            evidence["extra"] = True
            evidence["features_loaded"]["extra"] = True
            evidence["features_loaded"]["skins"] = "yes"
            evidence_path.write_text(json.dumps(evidence, indent=2))
            profile_path.write_text(json.dumps(production_export_profile(), indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)
            errors = "\n".join(report["errors"])

            self.assertEqual(exit_code, 2)
            self.assertIn("runtime evidence.extra is not allowed", errors)
            self.assertIn("runtime evidence.features_loaded.extra is not allowed", errors)
            self.assertIn("runtime evidence.features_loaded.skins must be boolean", errors)

    def test_eval_28_stale_runtime_evidence_package_identity_blocks_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-stale-identity-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            stale_identity = production_gate_package_identity(package_dir)
            (package_dir / "shared_symbols.atlas").write_text("shared_symbols.png\nsize: 32,32\nformat: RGBA8888\n")
            write_runtime_acceptance_evidence(package_dir / "runtime_acceptance.json", stale_identity)
            profile_path.write_text(json.dumps(production_export_profile(), indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "runtime evidence package_identity must match current package artifact hashes",
                "\n".join(report["errors"]),
            )

    def test_eval_28_count_mismatch_blocks_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-count-mismatch-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json", skin_variants_emitted=1)
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(package_dir / "runtime_acceptance.json", production_gate_package_identity(package_dir))
            profile_path.write_text(json.dumps(production_export_profile(), indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)

            self.assertEqual(exit_code, 2)
            self.assertIn("advanced feature count mismatch for skins", "\n".join(report["errors"]))

    def test_eval_28_required_runtime_feature_missing_blocks_gate(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-feature-missing-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            write_production_gate_validation_report(package_dir / "validation_report.json", events_defined=1)
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(
                package_dir / "runtime_acceptance.json",
                production_gate_package_identity(package_dir),
                events=False,
            )
            profile = production_export_profile(advanced_features={
                "claimed_counts": {
                    "skins": 0,
                    "physics": 0,
                    "sequences": 0,
                    "clipping": 0,
                    "events": 1,
                    "blends": 0,
                },
            })
            profile_path.write_text(json.dumps(profile, indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path)

            self.assertEqual(exit_code, 2)
            self.assertIn("runtime evidence must show events loaded", "\n".join(report["errors"]))

    def test_eval_28_policy_tampering_cannot_enable_cli_export(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-policy-tamper-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            policy_path = package_dir / "policy.json"
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(package_dir / "runtime_acceptance.json", production_gate_package_identity(package_dir))
            profile = production_export_profile(production_export_approval={
                "manual_export_approved": True,
                "cli_invocation_approved": True,
            })
            profile_path.write_text(json.dumps(profile, indent=2))
            policy = json.loads((PLUGIN_ROOT / "assets" / "production_export_policy.json").read_text())
            policy["cli_invocation_allowed"] = True
            policy["manual_export_only"] = False
            policy_path.write_text(json.dumps(policy, indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path, policy_path)
            errors = "\n".join(report["errors"])

            self.assertEqual(exit_code, 2)
            self.assertFalse(report["cli_invocation_allowed"])
            self.assertIn("policy.cli_invocation_allowed must be false", errors)
            self.assertIn("policy.manual_export_only must be true", errors)

    def test_eval_28_builder_gate_flag_blocks_without_profile(self) -> None:
        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-builder-flag-") as tmp:
            root = Path(tmp)
            layer_dir = root / "layers"
            out_dir = root / "out"
            layer_dir.mkdir()
            write_rgba_png(layer_dir / "HP3_body.png", 20, 20, (120, 80, 40, 255))

            result = run_builder_raw(layer_dir, out_dir, "--check-production-export-gate")
            gate_report = json.loads((out_dir / "production_export_gate_report.json").read_text())

            self.assertEqual(result.returncode, 2)
            self.assertEqual(gate_report["status"], "blocked")
            self.assertIn("production export profile is required", "\n".join(gate_report["errors"]))
            self.assertTrue((out_dir / "shared_symbols.json").exists())

    def test_eval_28_prohibited_report_path_blocks_without_writing(self) -> None:
        import production_export_gate

        with tempfile.TemporaryDirectory(prefix=EVAL_28_NAME + "-prohibited-report-") as tmp:
            package_dir = Path(tmp)
            profile_path = package_dir / "production_export_profile.json"
            out_report = Path("G:/artSource/production_export_gate_report.json")
            write_production_gate_validation_report(package_dir / "validation_report.json")
            write_production_gate_package_artifacts(package_dir)
            write_runtime_acceptance_evidence(package_dir / "runtime_acceptance.json", production_gate_package_identity(package_dir))
            profile_path.write_text(json.dumps(production_export_profile(), indent=2))

            report, exit_code = production_export_gate.run_gate(package_dir, profile_path, out_report=out_report)

            self.assertEqual(exit_code, 2)
            self.assertIn("out_report is under prohibited source-art root", "\n".join(report["errors"]))
            self.assertFalse((package_dir / "production_export_gate_report.json").exists())

    def test_eval_27_shared_source_art_write_guard_blocks_standalone_helpers(self) -> None:
        import build_avatar_states
        import build_atlas
        import learning_log
        import project_context

        blocked_dir = Path("G:/artSource/ClaudeSpineGuardFixture")
        blocked_file = blocked_dir / "out.json"

        with self.assertRaisesRegex(ValueError, "prohibited source-art root"):
            project_context.bootstrap_context(blocked_dir)
        with self.assertRaisesRegex(ValueError, "prohibited source-art root"):
            learning_log.log_entry(blocked_dir, "build", {})
        with self.assertRaisesRegex(ValueError, "prohibited source-art root"):
            build_avatar_states.ensure_safe_write_path(blocked_file, "out")
        with self.assertRaisesRegex(ValueError, "prohibited source-art root"):
            build_atlas.write_atlas_file([], (1, 1), "shared_symbols.png", blocked_dir / "shared_symbols.atlas")

    def test_eval_27_compiler_evidence_index_blocks_prohibited_output_path(self) -> None:
        import argparse
        import build_compiler_evidence_index

        args = argparse.Namespace(
            research_root=PLUGIN_ROOT,
            out=Path("G:/artSource/compiler_evidence_index.json"),
            stamp=False,
        )

        _index, errors, _warnings = build_compiler_evidence_index.build_index(args)

        self.assertTrue(any("output path is under prohibited source-art root" in error for error in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
