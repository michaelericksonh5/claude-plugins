# H5G Corpus Distilled Knowledge Pack

This plugin includes a bundled, portable knowledge pack distilled from H5G recipe specs, coverage reports, contextual layer interpretation, compiler gap bakeoffs, capability matrices, and current plugin evidence docs. Chris does not need the full H5G `research/` workspace for core family selection, rigging guidance, or report-only proposal evidence.

Machine-readable distilled evidence lives in `assets/h5g_corpus_distilled_evidence.json`. The smaller compatibility snapshot requested for skill routing lives in `assets/h5g_corpus_evidence_snapshot.json`. Original H5G paths named inside those artifacts are provenance metadata only; they are not runtime dependencies.

For full bakeoff discovery, use `references/h5g_corpus_bakeoff_usage.md` and `scripts/resolve_h5g_corpus_bakeoff.py`. The resolver may read the shared `G:/artSource/_spineResources/H5G_Corpus_Bakeoff` folder when it exists, but it must not write to it.

## What The Pack Covers

- 15 proof-ready recipe families: `hp_symbol`, `lp_symbol`, `mp_symbol`, `bo_special_symbol`, `wild_symbol`, `special_feature_symbol`, `bonus_symbol`, `jackpot_symbol`, `value_symbol`, `scatter_symbol`, `winframe_explode`, `meter`, `transition`, `celebration`, and `avatar`.
- Review-gated families: `blocker_or_bonus_symbol` and `non_symbol_or_unknown`.
- Animation intents and representative names: idle/breathe/smart loops, land/win/award/close settles, intro/outro/state transitions, meter collects, winframe explode, and celebration beats.
- Role-to-motion expectations for background, character body, head, hands/arms, frame/glow, sheen/text/value, sparkle/effects, and UI parts.
- Rig/slot/layer role evidence from contextual interpretation: semantic roles, rig roles, parent/pivot implications, additive/effect layer handling, and low-confidence review flags.
- UI/system buckets: supported proof templates for meter, transition, celebration, winframe, and symbol frame/glow; review-only buckets for buttons, row blockers, broad ambience, foreground overlays, generic VFX, and unknown UI/system records.
- Avatar/state evidence: State idle/transition/awarded/close naming and the boundary that runtime state and listener consumption belong to the game runtime.
- Mesh/weight/deform findings: first-pass mesh/weight support is review-required; final topology, weights, deform keys, linked meshes, and Spine Auto parity remain gated.
- Production export/runtime boundaries: preview proof and `.spine` import are useful, but `.skel` export, license automation, Perforce, source-art writes, and target-runtime approval remain gated.
- Known gaps: row blockers, broad UI/background ambience, generic VFX-only buckets, avatar runtime integration, final mesh/weights/deform, and production export remain gated.

## Practical Rigging Guidance

Choose a recipe family from naming, role-map/layer composition, and known layer roles. Do not classify by visual style alone. Premium art can still be `lp_symbol` if the role map says low-pay.

Use the distilled evidence to decide which motion vocabulary is appropriate:

- Symbol families use setup/default, idle, land, and often win/smart/breathe beats. Premium families can carry stronger pulse/shimmer; value/text families should stay readability-safe.
- Frame, glow, sheen, sparkle, and additive/effect layers should drive color/alpha, shimmer, text-sheen, frame-pulse, or short VFX beats when the selected family supports them.
- Character body/head/hand layers should get semantic parent bones and conservative follow-through. IK, mesh, physics, and weight binding are opt-in review artifacts, not automatic production approval.
- Meter, transition, celebration, and winframe outputs are evidence-backed proof templates, not full game-screen systems.
- Avatar packages can model state-frame proof data and event names, but persistent state, listeners, and target runtime behavior are not solved by Spine data alone.

## Bakeoff Findings To Preserve

The full deep bakeoff run `full_deep_all_20260505_1513` completed with 2534 candidate results, 766 compared candidates, 0 failed candidates, and 266 local human-authored JSON references. Its strongest result is not that generated rigs are production-close; it is that missing timeline families are now specific.

Largest compiler gaps observed across core symbol comparisons:

- `slot_attachment`
- `scale`
- `rotate`
- `translate`
- `slot_color`
- `slot_twoColor`
- `deform`

Later compiler work improved local coverage for transform motion, slot color/alpha, attachment swaps, draw order, and shared timeline composition. A fresh full deep bakeoff is still optional H5G-internal validation when motion fidelity must be re-proven.

## Production Honesty

This pack makes the skill self-contained with distilled corpus evidence. It does not make the plugin production-approved.

Final production rigging still requires Chris/art review, target runtime acceptance, approved mesh topology and weights, sparse reviewed deform usage when needed, approved export policy, and manual production export approval. Do not use the pack to claim a fully autonomous production rigger.
