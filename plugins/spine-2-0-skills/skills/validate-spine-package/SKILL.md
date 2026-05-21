---
name: validate-spine-package
description: Manually verify a Spine 4.3 proof package using validation reports, current contract checks, runtime preview proof, eval coverage, and import-version gates.
disable-model-invocation: true
argument-hint: "[package-dir]"
---

# Validate Spine Package

Use this manual workflow before saying a package is ready for handoff, motion-fidelity review, or production-export review.

## Required Gates

1. `validation_report.json` has `status: "ok"`.
2. Loop and settle endpoint fields are clean: `animation_loop_validation`, `animation_loop_intents`, and `loop_validation_status`.
3. `preview_validation_report.json` is clean when present.
4. `shared_symbols.json` uses the current 4.x contract and `skeleton.spine` matches the intended import version.
5. `preview.html` loads in Spine Player when preview proof is claimed.
6. `spine_editor_handoff.zip` exists for animator handoff when delivery is requested.

## Commands

```powershell
python scripts/run_local_evals.py
python scripts/build_runtime_acceptance_fixtures.py
npx -p playwright node scripts/runtime_acceptance_probe.mjs --packages-root generated/runtime_acceptance/packages
```

Run the browser probe when runtime evidence is required. Unit evals do not replace browser proof.

## Optional Production Gate

For production-export review only:

```powershell
python scripts/production_export_gate.py --profile <profile.json> --package-dir <package-dir>
```

A clean gate can report `ready_for_manual_export`; it does not invoke Spine CLI export, create `.skel`, write to Perforce, or approve art.

## Blocking Conditions

Block readiness claims when validation reports are missing, import version is unproven, browser proof is self-attested, advanced feature plans lack policy approval, or final art/rigger review has not happened.

## Final Report

Use this shape:

```text
Status: ready | blocked | needs review
Passed gates: ...
Failed/missing gates: ...
Commands run: ...
Artifacts checked: ...
Remaining human approval: ...
```

Reference `references/validation.md`, `references/capability_status.md`, and `assets/eval_coverage_report.json` as needed.
