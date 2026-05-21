# Autonomous Rigging Research

This is the implementation-facing summary for the autonomous Spine rigger plan. The current result is an auditable proposal layer and acceptance gates, not a production rigger.

## Current Evidence

The H5G corpus supports a strong proof pipeline:

- `assets/compiler_evidence_index.json` indexes family specs, coverage, contextual layer evidence, UI/system evidence, motion profiles, bakeoff findings, and advanced gate summaries.
- `research/generated/family_recipe_specs/specs/avatar.md` records avatar as `proof-ready`, with 17 games, 309 animations, 46 distinct animation names, and deform evidence in real references.
- `research/generated/full_deep_animation_bakeoff/closure_full_20260506_225908/families/avatar.md` shows one generated avatar proof candidate compared against 20 references, with large missing deltas for slot attachment, slot color, transform, and draw-order behavior.
- `research/spine_mesh_weights_deform.md` records the official Spine mesh/weight/deform facts: mesh topology matters, Auto weights are topology-sensitive, weights should be tested through extremes, prune/smooth are part of the workflow, and deform keys should stay sparse.

That evidence does not justify a fully autonomous production-rigger claim. It justifies report-only rig proposals, conservative mesh candidacy, and explicit parity fixtures.

## Deliverables Added

- `assets/autonomous_rigging_evidence_index.json`: machine-readable evidence and acceptance gates for autonomous-rigging claims.
- `assets/rig_proposal_schema.json`: closed schema for report-only rig proposals with confidence, review reasons, region/mesh decisions, and policy gates.
- `references/rig_proposal.md`: human reference for proposal use and boundaries.
- `scripts/generate_rig_proposal.py`: deterministic report-only helper that can turn interpreted layer evidence into proposal JSON without emitting Spine output.
- `references/external_avatar_rigging_review.md`: Genielabs and external-avatar-pipeline prior art review with license limits.
- `assets/mesh_weight_parity_fixture_schema.json` and `scripts/compare_mesh_weight_parity.py`: fixture gate for comparing Chris-approved Spine mesh exports against candidate weighted meshes.
- `assets/avatar_runtime_contract_schema.json` and `scripts/validate_avatar_runtime_contract.py`: runtime-owner gate for avatar states, transitions, events, and target runtime verification.

## Mesh And Weight Fixtures

Before production mesh/weight support can be claimed, create fixtures with:

- approved source layer and exact output package hash;
- Chris-approved hull vertices, interior vertices, edges, triangle layout, and vertex budget;
- a Spine Editor export with Auto weights and Nonessential data preserved when editor roundtrip fidelity matters;
- a plugin first-pass output generated from the same fixture;
- diff thresholds for vertex count, triangle count, allowed bones per vertex, max weight delta, total per-vertex weight error, and estimated vertex transforms.

Initial thresholds should be strict enough to catch drift but not pretend numeric equality to Spine Auto is available:

- vertex count and triangle count: exact match for the fixed fixture;
- bones per vertex: never exceed the approved fixture budget;
- per-vertex weight sum error: less than or equal to `0.001`;
- max per-influence weight delta against the approved fixture: starts as a review threshold, not a release pass, until real H5G data proves a value.

Run the fixture comparator:

```powershell
python scripts/compare_mesh_weight_parity.py `
  --approved <chris_approved_spine_export.json> `
  --candidate <candidate_shared_symbols.json> `
  --out generated/mesh_weight_parity/<fixture>.json
```

A passing report is fixture evidence only. It does not replace the visual `__mesh_weight_test`, Spine Editor review, or Chris approval.

## Avatar Fixtures

Avatar-specific production claims need a separate fixture set:

- approved state list and default state;
- transition, awarded, and close animation names;
- expression layers and visibility rules;
- event names, times, and game-runtime listener owner;
- diff thresholds for required animation names, slot attachment timelines, slot color timelines, transform ranges, and any sparse deform references;
- target runtime acceptance, not only Spine Player preview.

The current avatar compiler remains a state-frame proof package. It emits a manifest and deterministic event names, but persistent state and runtime listener consumption are game code.

Record runtime ownership with:

```powershell
python scripts/validate_avatar_runtime_contract.py `
  --contract <avatar_runtime_contract.json> `
  --out generated/avatar_runtime_contracts/<avatar>.json
```

The contract blocks avatar runtime claims unless a named runtime owner verifies state/event consumption in the target game runtime.

## Spine CLI And Export Gates

Production `.skel` or JSON export automation remains gated. The approved current boundary is:

- JSON-to-native `.spine` import can be automated through Spine CLI only when explicitly requested and licensed.
- Production export, binary `.skel`, clean, pack, unpack, and advanced flags remain documented but policy-gated.
- A clean production export gate can mean `ready_for_manual_export`; it does not invoke CLI export.
- Version matching is mandatory: editor export and runtime must match the approved Spine runtime line.

## Final Acceptance Criteria

Do not claim autonomous production rigging until all of these are true:

- rig proposals are schema-valid, report-only, and trace every decision to evidence;
- mesh and weight parity fixtures pass documented thresholds against approved Spine exports;
- avatar runtime state, event listener, and expression contracts are verified by the target game runtime owner;
- production export policy approves the chosen output format and records no source-art or Perforce writes;
- runtime acceptance passes for the target game runtime;
- Chris or the assigned Spine reviewer approves the fixture output;
- docs and evals still say the system is not a fully autonomous production rigger until those gates are met.
