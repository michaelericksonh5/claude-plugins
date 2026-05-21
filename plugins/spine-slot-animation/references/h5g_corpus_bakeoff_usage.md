# H5G Corpus Bakeoff Usage

The skill has three evidence tiers for H5G corpus and bakeoff guidance.

## Tier 1: Full H5G Research Workspace

When available, the full research workspace is the authoritative place to rerun bakeoffs:

```text
C:/Users/merickson/Desktop/Claude Spine/research
```

Override with `H5G_RESEARCH_ROOT` when Chris or another animator has the workspace in a different location.

The resolver looks for:

- `full_deep_animation_bakeoff.py`
- `compiler_gap_bakeoff.py`

Full bakeoff reruns are H5G-internal validation. They can support motion-fidelity claims, but they are not a substitute for Chris review or target runtime acceptance.

## Tier 2: Network Bakeoff Resource

Animators with Spine should also have access to the shared resource folder:

```text
G:/artSource/_spineResources/H5G_Corpus_Bakeoff
```

Override with `H5G_CORPUS_BAKEOFF_ROOT` when needed.

This location is a read-only reference source for the plugin. The skill may detect and reference files there, but it must not populate, update, or mutate anything under `G:/artSource`.

The preferred form is the consolidated report pack:

- `H5G_CORPUS_BAKEOFF_CONSOLIDATED_REPORT.md`
- `H5G_CORPUS_BAKEOFF_CONSOLIDATED_INDEX.json`
- `report_pack_manifest.json`
- `coverage/animation_family_coverage.md`
- `family_recipe_specs/family_recipe_specs.md`
- `contextual_layer_interpretation/contextual_layer_interpretation.md`
- `compiler_motion_profiles/latest_exact_motion_profile.json`

When these files are present, the resolver reports `network_h5g_corpus_bakeoff_report_pack_available` with evidence tier `network_report_pack`. Use the consolidated report first, then drill into the JSON index or raw report files only when exact counts or per-family evidence are needed.

The report pack intentionally excludes generated preview PNGs, atlases, HTML previews, and duplicate historical payloads. Those files made the full bundle several GB and are not needed for routine Claude guidance.

## Tier 3: Bundled Snapshot

When neither full research nor the network bakeoff resource is available, the skill falls back to the bundled snapshot:

- `assets/h5g_corpus_evidence_snapshot.json`
- `assets/h5g_corpus_distilled_evidence.json`
- `references/h5g_corpus_distilled_knowledge.md`

The bundled snapshot is enough for family, role, motion, avatar, mesh/deform, and claim-boundary guidance. It is advisory. It is not a fresh full bakeoff proof and cannot justify production-rigger claims by itself.

## Resolver

Use:

```powershell
python scripts/resolve_h5g_corpus_bakeoff.py
```

The resolver writes no files by default. It reports which evidence tier is available, the full bakeoff commands that would be used, and whether the workflow is using fresh full-bakeoff evidence, the network report pack, a generic network resource, or bundled advisory evidence.

To run a smoke bakeoff, use an explicit output directory outside source-art roots:

```powershell
python scripts/resolve_h5g_corpus_bakeoff.py `
  --run-smoke-bakeoff `
  --out-dir generated/h5g_bakeoff_smoke
```

The resolver refuses protected output roots through the shared source-art write guard.

## Claim Boundaries

- Full research workspace available: can run real bakeoff tools.
- Network report pack available: can reference the shared consolidated bakeoff/corpus report and supporting raw report files; freshness depends on when the report pack was generated.
- Generic network resource available: can reference shared bakeoff artifacts, but the skill may need a human-readable report or index before it can use the folder efficiently.
- Bundled snapshot only: advisory guidance only.

Never claim production-ready motion, final mesh weights, avatar runtime integration, or production `.skel` export solely from a bundled snapshot.
