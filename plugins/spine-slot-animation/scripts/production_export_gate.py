#!/usr/bin/env python3
"""Phase 10 production export approval/report gate.

This gate does not invoke Spine CLI and does not write to Perforce or source art.
It only validates explicit approvals and runtime evidence, then writes
production_export_gate_report.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from source_art_guard import write_guard_error


REPORT_NAME = "production_export_gate_report.json"
PROFILE_SCHEMA = "spine_slot_animation_production_export_profile_v1"
POLICY_SCHEMA = "spine_slot_animation_production_export_policy_v1"
RUNTIME_EVIDENCE_SCHEMA = "spine_slot_animation_runtime_acceptance_evidence_v1"
PACKAGE_ARTIFACTS = ("shared_symbols.json", "shared_symbols.atlas", "shared_symbols.png")
APPROVED_RUNTIME_EVIDENCE_PROVENANCE = {
    "method": "runtime_probe",
    "tool": "h5g-runtime-acceptance-probe",
    "tool_version": "runtime-acceptance-probe-v1",
    "execution_mode": "browser_runtime",
}


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        return None, f"missing file: {path}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {path}: {exc}"
    if not isinstance(data, dict):
        return None, f"{path} must contain a JSON object"
    return data, None


def _resolve_from_profile(profile_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return profile_path.parent / path


def _prohibited_path_error(path: Path, label: str) -> str | None:
    return write_guard_error(path, label)


def _unknown_keys(obj: dict[str, Any], allowed: set[str], prefix: str) -> list[str]:
    return [f"{prefix}.{key} is not allowed" for key in sorted(set(obj) - allowed)]


def _require_object(obj: dict[str, Any], key: str, errors: list[str], prefix: str) -> dict[str, Any] | None:
    value = obj.get(key)
    if not isinstance(value, dict):
        errors.append(f"{prefix}.{key} is required")
        return None
    return value


def _require_string(obj: dict[str, Any], key: str, errors: list[str], prefix: str) -> str | None:
    value = obj.get(key)
    if not isinstance(value, str) or not value:
        errors.append(f"{prefix}.{key} is required")
        return None
    return value


def _validate_profile_shape(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(_unknown_keys(profile, {
        "schema",
        "package_validation_report",
        "spine_editor_version",
        "spine_cli_version",
        "runtime",
        "output_format",
        "license_posture",
        "write_policy",
        "advanced_features",
        "runtime_acceptance_evidence",
        "approver",
        "production_export_approval",
    }, "profile"))
    if profile.get("schema") != PROFILE_SCHEMA:
        errors.append(f"profile.schema must be {PROFILE_SCHEMA!r}")

    for key in ("spine_editor_version", "spine_cli_version", "runtime_acceptance_evidence"):
        _require_string(profile, key, errors, "profile")
    configured_report = profile.get("package_validation_report")
    if configured_report is not None and (not isinstance(configured_report, str) or not configured_report):
        errors.append("profile.package_validation_report must be a non-empty string")

    runtime = profile.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("profile.runtime is required")
    else:
        errors.extend(_unknown_keys(runtime, {"name", "version"}, "profile.runtime"))
        _require_string(runtime, "name", errors, "profile.runtime")
        _require_string(runtime, "version", errors, "profile.runtime")

    output_format = profile.get("output_format")
    if not isinstance(output_format, dict):
        errors.append("profile.output_format is required")
    else:
        errors.extend(_unknown_keys(output_format, {"decision", "rationale"}, "profile.output_format"))
        _require_string(output_format, "decision", errors, "profile.output_format")
        _require_string(output_format, "rationale", errors, "profile.output_format")

    license_posture = profile.get("license_posture")
    if not isinstance(license_posture, dict):
        errors.append("profile.license_posture is required")
    else:
        errors.extend(_unknown_keys(
            license_posture,
            {"approved", "approval_ticket", "approved_by", "approved_at"},
            "profile.license_posture",
        ))
        if license_posture.get("approved") is not True:
            errors.append("profile.license_posture.approved must be true")
        for key in ("approval_ticket", "approved_by", "approved_at"):
            _require_string(license_posture, key, errors, "profile.license_posture")

    write_policy = profile.get("write_policy")
    if not isinstance(write_policy, dict):
        errors.append("profile.write_policy is required")
    else:
        errors.extend(_unknown_keys(write_policy, {"perforce_writes", "source_art_writes"}, "profile.write_policy"))
        if write_policy.get("perforce_writes") is not False:
            errors.append("profile.write_policy.perforce_writes must be false")
        if write_policy.get("source_art_writes") is not False:
            errors.append("profile.write_policy.source_art_writes must be false")

    advanced_features = profile.get("advanced_features")
    if not isinstance(advanced_features, dict):
        errors.append("profile.advanced_features is required")
    else:
        errors.extend(_unknown_keys(advanced_features, {"claimed_counts"}, "profile.advanced_features"))
        claimed_counts = advanced_features.get("claimed_counts")
        if not isinstance(claimed_counts, dict):
            errors.append("profile.advanced_features.claimed_counts is required")
        else:
            errors.extend(_unknown_keys(
                claimed_counts,
                {"skins", "physics", "sequences", "clipping", "events", "blends"},
                "profile.advanced_features.claimed_counts",
            ))
            for feature in ("skins", "physics", "sequences", "clipping", "events", "blends"):
                value = claimed_counts.get(feature)
                if type(value) is not int or value < 0:
                    errors.append(f"profile.advanced_features.claimed_counts.{feature} must be a non-negative integer")

    approver = profile.get("approver")
    if not isinstance(approver, dict):
        errors.append("profile.approver is required")
    else:
        errors.extend(_unknown_keys(approver, {"name", "role", "approved_at", "approval_ticket"}, "profile.approver"))
        for key in ("name", "role", "approved_at", "approval_ticket"):
            _require_string(approver, key, errors, "profile.approver")

    export_approval = profile.get("production_export_approval")
    if not isinstance(export_approval, dict):
        errors.append("profile.production_export_approval is required")
    else:
        errors.extend(_unknown_keys(
            export_approval,
            {"manual_export_approved", "cli_invocation_approved"},
            "profile.production_export_approval",
        ))
        if export_approval.get("manual_export_approved") is not True:
            errors.append("profile.production_export_approval.manual_export_approved must be true")
        if not isinstance(export_approval.get("cli_invocation_approved"), bool):
            errors.append("profile.production_export_approval.cli_invocation_approved must be boolean")

    return errors


def _validate_package_identity_shape(identity: dict[str, Any], errors: list[str], prefix: str) -> None:
    errors.extend(_unknown_keys(identity, set(PACKAGE_ARTIFACTS), prefix))
    for artifact in PACKAGE_ARTIFACTS:
        artifact_identity = _require_object(identity, artifact, errors, prefix)
        if artifact_identity is None:
            continue
        errors.extend(_unknown_keys(artifact_identity, {"sha256"}, f"{prefix}.{artifact}"))
        digest = artifact_identity.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            errors.append(f"{prefix}.{artifact}.sha256 must be a lowercase sha256 hex digest")


def _validate_runtime_evidence_shape(evidence: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(_unknown_keys(evidence, {
        "schema",
        "runtime_name",
        "runtime_version",
        "provenance",
        "package_loaded",
        "features_loaded",
        "package_identity",
    }, "runtime evidence"))
    if evidence.get("schema") != RUNTIME_EVIDENCE_SCHEMA:
        errors.append(f"runtime evidence schema must be {RUNTIME_EVIDENCE_SCHEMA!r}")
    _require_string(evidence, "runtime_name", errors, "runtime evidence")
    _require_string(evidence, "runtime_version", errors, "runtime evidence")
    if evidence.get("package_loaded") is not True:
        errors.append("runtime evidence package_loaded must be true")
    provenance = evidence.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("runtime evidence.provenance is required")
    else:
        errors.extend(_unknown_keys(
            provenance,
            {"method", "tool", "tool_version", "execution_mode", "execution_id", "executed_at"},
            "runtime evidence.provenance",
        ))
        for key in ("method", "tool", "tool_version", "execution_mode", "execution_id", "executed_at"):
            _require_string(provenance, key, errors, "runtime evidence.provenance")
    features_loaded = evidence.get("features_loaded")
    if not isinstance(features_loaded, dict):
        errors.append("runtime evidence features_loaded is required")
    else:
        errors.extend(_unknown_keys(
            features_loaded,
            {"skins", "physics", "sequences", "clipping", "events", "blends"},
            "runtime evidence.features_loaded",
        ))
        for feature in ("skins", "physics", "sequences", "clipping", "events", "blends"):
            if not isinstance(features_loaded.get(feature), bool):
                errors.append(f"runtime evidence.features_loaded.{feature} must be boolean")
    package_identity = evidence.get("package_identity")
    if not isinstance(package_identity, dict):
        errors.append("runtime evidence.package_identity is required")
    else:
        _validate_package_identity_shape(package_identity, errors, "runtime evidence.package_identity")
    return errors


def _validate_policy_shape(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(_unknown_keys(policy, {
        "schema",
        "approved_spine_editor_version",
        "approved_spine_cli_version",
        "approved_runtime_name",
        "approved_runtime_version",
        "allowed_output_formats",
        "cli_invocation_allowed",
        "manual_export_only",
        "require_license_posture_approval",
        "require_runtime_acceptance_evidence",
        "perforce_writes_allowed",
        "source_art_writes_allowed",
        "advanced_feature_report_fields",
        "runtime_acceptance_features",
        "approved_runtime_evidence_provenance",
    }, "policy"))
    if policy.get("schema") != POLICY_SCHEMA:
        errors.append(f"policy.schema must be {POLICY_SCHEMA!r}")
    for key in ("approved_spine_editor_version", "approved_spine_cli_version", "approved_runtime_name", "approved_runtime_version"):
        _require_string(policy, key, errors, "policy")
    if policy.get("allowed_output_formats") != ["json", "binary"]:
        errors.append("policy.allowed_output_formats must be ['json', 'binary']")
    for key, expected in (
        ("cli_invocation_allowed", False),
        ("manual_export_only", True),
        ("require_license_posture_approval", True),
        ("require_runtime_acceptance_evidence", True),
        ("perforce_writes_allowed", False),
        ("source_art_writes_allowed", False),
    ):
        if policy.get(key) is not expected:
            errors.append(f"policy.{key} must be {str(expected).lower()}")
    fields = policy.get("advanced_feature_report_fields")
    if not isinstance(fields, dict):
        errors.append("policy.advanced_feature_report_fields is required")
    else:
        errors.extend(_unknown_keys(
            fields,
            {"skins", "physics", "sequences", "clipping", "events", "blends"},
            "policy.advanced_feature_report_fields",
        ))
        expected_fields = {
            "skins": "skin_variants_emitted",
            "physics": "physics_constraints_emitted",
            "sequences": "sequence_attachments_emitted",
            "clipping": "clipping_attachments_emitted",
            "events": "events_defined",
            "blends": None,
        }
        for feature, expected in expected_fields.items():
            if fields.get(feature) != expected:
                errors.append(f"policy.advanced_feature_report_fields.{feature} must be {expected!r}")
    if policy.get("runtime_acceptance_features") != ["skins", "physics", "sequences", "clipping", "events", "blends"]:
        errors.append("policy.runtime_acceptance_features must list the approved feature set")
    provenance = policy.get("approved_runtime_evidence_provenance")
    if not isinstance(provenance, dict):
        errors.append("policy.approved_runtime_evidence_provenance is required")
    else:
        errors.extend(_unknown_keys(
            provenance,
            set(APPROVED_RUNTIME_EVIDENCE_PROVENANCE),
            "policy.approved_runtime_evidence_provenance",
        ))
        for key, expected in APPROVED_RUNTIME_EVIDENCE_PROVENANCE.items():
            if provenance.get(key) != expected:
                errors.append(f"policy.approved_runtime_evidence_provenance.{key} must be {expected!r}")
    return errors


def _package_identity(package_dir: Path, errors: list[str]) -> dict[str, dict[str, str]] | None:
    identity: dict[str, dict[str, str]] = {}
    for artifact in PACKAGE_ARTIFACTS:
        path = package_dir / artifact
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except FileNotFoundError:
            errors.append(f"missing package artifact: {path}")
            return None
        identity[artifact] = {"sha256": digest}
    return identity


def _validation_count(validation_report: dict[str, Any], feature: str, policy: dict[str, Any]) -> int:
    fields = policy.get("advanced_feature_report_fields", {})
    field = fields.get(feature) if isinstance(fields, dict) else None
    if field is None:
        return 0
    value = validation_report.get(field, 0)
    return value if type(value) is int and value >= 0 else 0


def _required_runtime_features(
    validation_report: dict[str, Any],
    profile: dict[str, Any],
    policy: dict[str, Any],
) -> list[str]:
    advanced_features = profile.get("advanced_features", {})
    advanced_features = advanced_features if isinstance(advanced_features, dict) else {}
    claimed_counts = advanced_features.get("claimed_counts", {})
    claimed_counts = claimed_counts if isinstance(claimed_counts, dict) else {}
    features = []
    for feature in policy.get("runtime_acceptance_features", []):
        if feature == "skins":
            features.append(feature)
            continue
        claimed = claimed_counts.get(feature, 0) if isinstance(claimed_counts, dict) else 0
        reported = _validation_count(validation_report, feature, policy)
        if claimed > 0 or reported > 0:
            features.append(feature)
    return features


def _build_base_report(package_dir: Path, policy: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "schema": "spine_slot_animation_production_export_gate_report_v1",
        "status": "blocked",
        "errors": [],
        "warnings": [],
        "package_dir": str(package_dir),
        "policy_schema": policy.get("schema") if policy else None,
        "export_invoked": False,
        "cli_invocation_allowed": False,
        "manual_export_ready": False,
        "runtime_acceptance_status": "unverified",
    }


def run_gate(
    package_dir: Path,
    profile_path: Path | None,
    policy_path: Path | None = None,
    out_report: Path | None = None,
    run_runtime_probe: bool = False,
    runtime_probe_executed_by_gate: bool = False,
) -> tuple[dict[str, Any], int]:
    package_dir = package_dir.resolve()
    output_path = out_report.resolve() if out_report else (package_dir / REPORT_NAME)
    if policy_path is None:
        policy_path = Path(__file__).resolve().parents[1] / "assets" / "production_export_policy.json"
    policy, policy_error = _load_json(policy_path)
    report = _build_base_report(package_dir, policy)
    report["policy_path"] = str(policy_path)
    report["out_report"] = str(output_path)

    package_path_error = _prohibited_path_error(package_dir, "package_dir")
    output_path_error = _prohibited_path_error(output_path, "out_report")
    if package_path_error:
        report["errors"].append(package_path_error)
    if output_path_error:
        report["errors"].append(output_path_error)

    if policy_error:
        report["errors"].append(policy_error)
    else:
        report["errors"].extend(_validate_policy_shape(policy))

    if run_runtime_probe and not report["errors"]:
        _run_runtime_acceptance_probe(package_dir, report)
        runtime_probe_executed_by_gate = not report["errors"]

    if profile_path is None:
        report["errors"].append("production export profile is required")
    else:
        report["profile_path"] = str(profile_path)
        profile, profile_error = _load_json(profile_path)
        if profile_error:
            report["errors"].append(profile_error)
        elif not report["errors"]:
            report["errors"].extend(_validate_profile_shape(profile))
            _validate_profile_against_policy(profile, policy, report["errors"])
            validation_report = _load_validation_report(package_dir, profile, profile_path, report["errors"])
            runtime_evidence = _load_runtime_evidence(profile, profile_path, report["errors"])
            identity = _package_identity(package_dir, report["errors"])
            if validation_report and runtime_evidence and identity:
                report["package_identity"] = identity
                _validate_advanced_counts(profile, validation_report, policy, report["errors"])
                _validate_runtime_evidence(
                    profile,
                    validation_report,
                    runtime_evidence,
                    identity,
                    policy,
                    report,
                    runtime_probe_executed_by_gate=runtime_probe_executed_by_gate,
                )
            _set_ready_state(profile, policy, report)

    if report["errors"]:
        report["status"] = "blocked"
        report["manual_export_ready"] = False
        report["cli_invocation_allowed"] = False
    else:
        report["status"] = "ready_for_manual_export"
        report["manual_export_ready"] = True

    if output_path_error is None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2))
    return report, 0 if report["status"] == "ready_for_manual_export" else 2


def _run_runtime_acceptance_probe(package_dir: Path, report: dict[str, Any]) -> None:
    probe_script = Path(__file__).resolve().parent / "runtime_acceptance_probe.mjs"
    cmd = [
        "npx",
        "-p",
        "playwright",
        "node",
        str(probe_script),
        "--package-dir",
        str(package_dir),
        "--out-dir",
        str(package_dir / "runtime_probe"),
    ]
    report["runtime_probe_command"] = cmd
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    except OSError as exc:
        report["errors"].append(f"runtime acceptance probe failed to start: {exc}")
        return
    report["runtime_probe_exit_code"] = result.returncode
    report["runtime_probe_stdout"] = result.stdout[-4000:]
    report["runtime_probe_stderr"] = result.stderr[-4000:]
    if result.returncode != 0:
        report["errors"].append("runtime acceptance probe failed")


def _validate_profile_against_policy(profile: dict[str, Any], policy: dict[str, Any], errors: list[str]) -> None:
    if profile.get("spine_editor_version") != policy.get("approved_spine_editor_version"):
        errors.append("profile.spine_editor_version must match approved policy")
    if profile.get("spine_cli_version") != policy.get("approved_spine_cli_version"):
        errors.append("profile.spine_cli_version must match approved policy")

    runtime = profile.get("runtime", {})
    runtime = runtime if isinstance(runtime, dict) else {}
    if runtime.get("name") != policy.get("approved_runtime_name"):
        errors.append("profile.runtime.name must match approved policy")
    if runtime.get("version") != policy.get("approved_runtime_version"):
        errors.append("profile.runtime.version must match approved policy")

    output_format_obj = profile.get("output_format", {})
    output_format_obj = output_format_obj if isinstance(output_format_obj, dict) else {}
    output_format = output_format_obj.get("decision")
    if output_format not in policy.get("allowed_output_formats", []):
        errors.append("profile.output_format.decision must be allowed by policy")

    write_policy = profile.get("write_policy", {})
    write_policy = write_policy if isinstance(write_policy, dict) else {}
    if write_policy.get("perforce_writes") and not policy.get("perforce_writes_allowed"):
        errors.append("Perforce writes are prohibited by production export policy")
    if write_policy.get("source_art_writes") and not policy.get("source_art_writes_allowed"):
        errors.append("source-art writes are prohibited by production export policy")


def _load_validation_report(
    package_dir: Path,
    profile: dict[str, Any],
    profile_path: Path,
    errors: list[str],
) -> dict[str, Any] | None:
    configured_path = profile.get("package_validation_report")
    report_path = (
        _resolve_from_profile(profile_path, configured_path)
        if isinstance(configured_path, str) and configured_path
        else package_dir / "validation_report.json"
    )
    validation_report, validation_error = _load_json(report_path)
    if validation_error:
        errors.append(validation_error)
        return None
    if validation_report.get("status") != "ok":
        errors.append("package validation_report status must be ok")
    return validation_report


def _load_runtime_evidence(
    profile: dict[str, Any],
    profile_path: Path,
    errors: list[str],
) -> dict[str, Any] | None:
    evidence_value = profile.get("runtime_acceptance_evidence")
    if not isinstance(evidence_value, str) or not evidence_value:
        return None
    evidence_path = _resolve_from_profile(profile_path, evidence_value)
    evidence, evidence_error = _load_json(evidence_path)
    if evidence_error:
        errors.append(evidence_error)
        return None
    errors.extend(_validate_runtime_evidence_shape(evidence))
    return evidence


def _validate_advanced_counts(
    profile: dict[str, Any],
    validation_report: dict[str, Any],
    policy: dict[str, Any],
    errors: list[str],
) -> None:
    advanced_features = profile.get("advanced_features", {})
    advanced_features = advanced_features if isinstance(advanced_features, dict) else {}
    claimed_counts = advanced_features.get("claimed_counts", {})
    claimed_counts = claimed_counts if isinstance(claimed_counts, dict) else {}
    for feature in ("skins", "physics", "sequences", "clipping", "events", "blends"):
        claimed = claimed_counts.get(feature, 0)
        reported = _validation_count(validation_report, feature, policy)
        if feature == "blends" and claimed != 0:
            errors.append("blend-mode production export claims are not supported; claimed blends must be 0")
        if claimed != reported:
            errors.append(
                f"advanced feature count mismatch for {feature}: profile claims {claimed}, validation reports {reported}"
            )


def _validate_runtime_evidence(
    profile: dict[str, Any],
    validation_report: dict[str, Any],
    evidence: dict[str, Any],
    identity: dict[str, dict[str, str]],
    policy: dict[str, Any],
    report: dict[str, Any],
    runtime_probe_executed_by_gate: bool = False,
) -> None:
    errors = report["errors"]
    report["runtime_acceptance_status"] = "unverified"
    runtime = profile.get("runtime", {})
    runtime = runtime if isinstance(runtime, dict) else {}
    if evidence.get("runtime_name") != runtime.get("name"):
        errors.append("runtime evidence runtime_name must match profile.runtime.name")
    if evidence.get("runtime_version") != runtime.get("version"):
        errors.append("runtime evidence runtime_version must match profile.runtime.version")
    if evidence.get("package_loaded") is not True:
        errors.append("runtime evidence package_loaded must be true")
    if evidence.get("package_identity") != identity:
        errors.append("runtime evidence package_identity must match current package artifact hashes")

    provenance = evidence.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("runtime evidence provenance is required for runtime acceptance")
    else:
        execution_mode = provenance.get("execution_mode")
        report["runtime_acceptance_provenance"] = {
            "method": provenance.get("method"),
            "tool": provenance.get("tool"),
            "tool_version": provenance.get("tool_version"),
            "execution_mode": execution_mode,
            "execution_id": provenance.get("execution_id"),
            "report_only": execution_mode == "report_only_fixture",
        }
        if execution_mode == "report_only_fixture":
            report["runtime_acceptance_status"] = "report_only_unverified"
        elif execution_mode != "browser_runtime":
            report["runtime_acceptance_status"] = "static_unverified"
        for key, expected in APPROVED_RUNTIME_EVIDENCE_PROVENANCE.items():
            if provenance.get(key) != expected:
                errors.append(f"runtime evidence.provenance.{key} must be {expected!r}")

    features_loaded = evidence.get("features_loaded")
    if not isinstance(features_loaded, dict):
        errors.append("runtime evidence features_loaded is required")
        return

    required_features = _required_runtime_features(validation_report, profile, policy)
    report["runtime_acceptance_required_features"] = required_features
    for feature in required_features:
        if features_loaded.get(feature) is not True:
            errors.append(f"runtime evidence must show {feature} loaded")
    if (
        report.get("runtime_acceptance_provenance", {}).get("execution_mode") == "browser_runtime"
        and not runtime_probe_executed_by_gate
    ):
        report["runtime_acceptance_status"] = "browser_runtime_evidence_file_unverified"
        errors.append("production export gate must run the runtime acceptance probe before trusting browser evidence")
    if not errors:
        report["runtime_acceptance_status"] = "verified_browser_runtime"


def _set_ready_state(profile: dict[str, Any], policy: dict[str, Any], report: dict[str, Any]) -> None:
    export_approval = profile.get("production_export_approval", {})
    export_approval = export_approval if isinstance(export_approval, dict) else {}
    report["manual_export_approved_by_profile"] = export_approval.get("manual_export_approved") is True
    report["cli_invocation_approved_by_profile"] = export_approval.get("cli_invocation_approved") is True
    report["cli_invocation_approved_by_policy"] = policy.get("cli_invocation_allowed") is True
    report["manual_export_only"] = policy.get("manual_export_only") is True
    report["cli_invocation_allowed"] = bool(
        export_approval.get("cli_invocation_approved") is True
        and policy.get("cli_invocation_allowed") is True
        and not policy.get("manual_export_only", True)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Phase 10 production export gate.")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--production-export-profile")
    parser.add_argument("--policy", help="Defaults to assets/production_export_policy.json.")
    parser.add_argument("--out-report", help="Defaults to <package-dir>/production_export_gate_report.json.")
    parser.add_argument("--run-runtime-acceptance-probe", action="store_true",
                        help="Run the browser runtime probe before trusting runtime_acceptance.json.")
    args = parser.parse_args()

    report, exit_code = run_gate(
        Path(args.package_dir),
        Path(args.production_export_profile) if args.production_export_profile else None,
        Path(args.policy) if args.policy else None,
        Path(args.out_report) if args.out_report else None,
        run_runtime_probe=args.run_runtime_acceptance_probe,
    )
    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
