---
name: internal-h5g-evidence
description: Applies internal H5G Confluence process gates to slot math, RTP, RMG, certification, release, and regulated jackpot work. Use for RMG math documents, RTP checks, SlotEngine/Test Harness/SlotEngineGUI work, Math Commons changes, substitution, dynamic gameplay, progressive jackpots, jurisdiction-specific math, or H5G internal evidence.
when_to_use: Invoke when the user mentions H5G, Confluence, RMG, certification docs, math proof, release verification, engine/expansion, Test Harness collector, SlotEngineGUI, Math Commons, progressive jackpot regulations, jurisdiction, PA, MI, NJ, WV, CT, Loto-Quebec, or Ontario.
---

# Internal H5G Evidence

Use this skill when H5G internal process or tooling affects the math answer.

## Workflow

1. Classify the task:
   - SlotEngine
   - Test Harness
   - SlotEngineGUI
   - Math Commons
   - RMG math documents
   - Release verification
   - Progressive jackpot / jurisdiction
   - Feature design
2. Load the relevant checklist from [h5g-process-gates.md](h5g-process-gates.md).
3. Require the matching internal artifacts before final math.
4. If a needed artifact is missing, stop and state what internal page, ticket, config, engine, proof, collector, or jurisdiction data is needed.

## Output Format

```markdown
## H5G Evidence Classification
- Task type:
- Internal artifact required:
- Artifact provided:
- Missing:

## Process Gate Result
- PASS / BLOCKED / NEEDS MORE DATA

## Required Next Step
- ...
```

Do not infer production behavior from feature names such as WYS, Loot Link, SF, collector, jackpot, walking wild, or expanding reel. Require the GDD, math spec, PAR sheet, engine config, or Confluence-backed process artifact.

