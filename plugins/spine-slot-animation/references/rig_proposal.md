# Rig Proposal Schema

`assets/rig_proposal_schema.json` defines a closed, report-only proposal format for future autonomous rigging review. It is not a Spine package format and it is not a production export path.

Use it when Claude needs to explain what a deterministic rigger would do before compiling anything:

- which layers stay cheap `region` attachments;
- which layers become `mesh_candidate` review items;
- confidence and review reasons for every risky decision;
- explicit policy gates for Spine Auto weight parity, Chris-approved mesh fixtures, avatar runtime state, production export, and final autonomous-rigger claims.

The matching helper is:

```powershell
python scripts/generate_rig_proposal.py `
  --family hp_symbol `
  --layer-interpretation <interpreted_layers.json> `
  --out generated/rig_proposals/<asset>.rig_proposal.json
```

The helper writes only a report. It does not emit `shared_symbols.json`, `.spine`, `.skel`, mesh plans, weights, or deform timelines. The proposal may identify a mesh candidate, but production topology, final weights, and any corrective deform keys remain Spine Editor / rigger review work.

By default, the helper reads `assets/h5g_corpus_distilled_evidence.json`, the bundled portable H5G corpus/bakeoff pack. It does not require Chris to have the full H5G `research/` workspace. Advanced H5G-internal bakeoff reruns can still refresh future evidence, but proposal generation should use the bundled pack for evidence IDs and support status unless a reviewer explicitly supplies another index.

## Confidence Rules

`confidence.overall` is an average of source layer confidence when layer interpretation is provided. It is never approval. Low-confidence layers add review reasons, and mesh candidates are capped because topology and weights cannot be proven from semantic labels alone.

## Mesh Decisions

The proposal keeps static roles as regions by default. Deforming roles such as body, hair, cloth, cape, tail, wings, arms, antennae, and dangling accessories can become `mesh_candidate` entries. Every mesh candidate requires review and names why:

- topology must be approved;
- weights must be tested through extreme poses;
- prune/bone influence budgets must be checked;
- deform keys stay blocked unless a sparse corrective case is reviewed.

## Acceptance Gates

The proposal must keep these gates visible:

- `spine_auto_weight_parity_fixture`: same mesh compared between Spine Auto and plugin first-pass output.
- `chris_approved_mesh_fixture`: approved topology, edges, weights, and screenshots.
- `avatar_runtime_state_contract`: game-runtime state/listener ownership verified outside Spine data.
- `production_export_policy`: approved profile and runtime evidence; no source-art or Perforce writes.
- `target_runtime_acceptance`: target game runtime proof, not just preview loading.
- `final_autonomous_rigger_claim`: blocked until every gate above is verified.

A valid proposal can help review. It cannot by itself justify saying the system is a fully autonomous production rigger.

## Follow-On Gates

If a proposal identifies mesh candidates, compare approved and candidate mesh data with:

```powershell
python scripts/compare_mesh_weight_parity.py `
  --approved <chris_approved_spine_export.json> `
  --candidate <candidate_shared_symbols.json> `
  --out generated/mesh_weight_parity/<fixture>.json
```

If a proposal is for `avatar`, record game-runtime ownership with:

```powershell
python scripts/validate_avatar_runtime_contract.py `
  --contract <avatar_runtime_contract.json> `
  --out generated/avatar_runtime_contracts/<avatar>.json
```

These tools are acceptance gates after the proposal. They still do not emit production Spine output or approve the rig by themselves.
