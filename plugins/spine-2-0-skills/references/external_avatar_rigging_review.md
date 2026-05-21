# External Avatar Rigging Review

This review records reusable concepts from external avatar-rigging pipelines while keeping licensing and evidence boundaries explicit.

## Genielabs Concepts

Reusable ideas:

- Part alignment can use feature matching, RANSAC-style geometry checks, and occlusion-aware z-order as review evidence.
- Adjustment JSON beside the generated output is useful because an artist can correct positioning without editing generated code.
- A self-contained Spine Player preview and lightweight interactive editor are good review-loop patterns.

Do not reuse:

- source code, presets, tests, or assets from PolyForm Noncommercial repositories;
- generic humanoid body assumptions as H5G slot-character production evidence;
- single-image decomposition as production intake without hidden-part, hallucination, and source-layer review.

## H5G Fit

H5G slot avatars are not generic app avatars. The corpus evidence has persistent state names such as `State0Idle`, `State0to1`, `State1Awarded`, and `State1Close`, and real references include attachment swaps, color timelines, transform motion, and deform-heavy authoring. The portable plugin currently emits proof state-frame packages plus `avatar_state_manifest.json`; it does not prove final expression rigs, IK, mesh deformation, persistent state, or listener consumption.

Use external concepts only as prompts for review questions:

- Are all hidden parts represented by approved source layers?
- Does z-order match the source state and the intended transition?
- Are manual adjustments captured as data that can be audited?
- Does preview evidence come from the intended runtime, or only from a generic web preview?

## License Boundary

Genielabs remains conceptual prior art. The plugin must not copy code or embed artifacts from PolyForm Noncommercial sources. Any future implementation should be written from H5G requirements, official Spine documentation, and approved H5G fixtures.

## Avatar Gaps To Close

Before an autonomous avatar-rigger claim, H5G still needs:

- a Chris-approved avatar source fixture with state list, expression layers, mesh/weight/deform expectations, and event timing;
- target game runtime ownership for persistent state and event listeners;
- diff thresholds against real avatar exports for animation names, slot attachment timelines, slot color timelines, transform ranges, and sparse deform usage;
- production export approval that preserves exact Spine editor/runtime version matching and nonessential data where editor roundtrip fidelity matters.
