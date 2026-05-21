---
name: review-spine-rigging
description: Manually review Spine rigging readiness, autonomous rig proposals, mesh candidates, first-pass weights, avatar runtime contracts, and production-rigger claim boundaries.
disable-model-invocation: true
argument-hint: "[asset-or-package]"
---

# Review Spine Rigging

Use this manual workflow when the user asks if the system can rig an asset, whether meshes/weights are good, or whether autonomous production rigging is ready.

## Evidence To Load

- `references/capability_status.md`
- `references/rig_design.md`
- `references/meshes_and_deform.md`
- `references/autonomous_rigging_research.md`
- `references/rig_proposal.md`
- `assets/compiler_evidence_index.json`
- `assets/autonomous_rigging_evidence_index.json`

## Report-Only Rig Proposal

```powershell
python scripts/generate_rig_proposal.py `
  --family <recipe-family> `
  --layer-interpretation <interpreted_layers.json> `
  --out generated/rig_proposals/<asset>.rig_proposal.json
```

This does not compile a package or approve production rigging.

## Mesh And Weight Gates

For candidate vs Chris-approved fixture comparison:

```powershell
python scripts/compare_mesh_weight_parity.py `
  --approved <chris-approved-spine-export.json> `
  --candidate <candidate-shared-symbols.json> `
  --out generated/mesh_weight_parity/<fixture>.json
```

First-pass auto weights remain review artifacts. They are not Spine Auto parity or final hand-painted weights.

## Avatar Runtime Gate

```powershell
python scripts/validate_avatar_runtime_contract.py `
  --contract <avatar-runtime-contract.json> `
  --out generated/avatar_runtime_contracts/<avatar>.json
```

A Spine avatar package does not prove persistent runtime state, listener consumption, or game integration.

## Blocking Conditions

Block any claim of fully autonomous production rigging when final mesh topology, final weights, deform keys, linked meshes, runtime ownership, target runtime proof, production export, or Chris/art-owner approval is missing.

## Final Report

Use this shape:

```text
Rig readiness: supported proof | review-required | blocked
Evidence used: ...
Region decisions: ...
Mesh candidates: ...
Missing gates: ...
Human approval required: ...
```

Reference `references/progressive_skill_capability_crosswalk.md` for where each old monolith capability lives in this fork.
