---
name: dependency-audit
description: Audits H5G slot/game math for dependent-probability mistakes. Use for RTP math, RMG math, PAR sheets, paylines, scatters, visible windows, retriggers, multipliers, caps, hold-and-spin, collectors, WYS/Loot Link/SF mechanics, jackpot odds, or any concern that probability assumptions are wrong.
when_to_use: Invoke whenever the conversation includes "dependent probabilities", "are these independent", "does this math work", "review the math", "audit RTP", "check odds", "hit frequency", "volatility", "scatter chance", "retrigger chance", "multiplier average", or "cap".
---

# Dependency Audit

Use this skill to find probability errors before math is trusted.

## Audit Steps

1. Identify the requested metric: EV, RTP, hit frequency, win frequency, variance, distribution, trigger probability, max-win probability, or certification evidence.
2. List all random variables and events used by the calculation.
3. Mark each relationship: independent, dependent, disjoint, overlapping, conditional, or stateful.
4. For each independence claim, require proof from RNG, reel, screen, or state model.
5. Check every item in [dependency-failure-modes.md](dependency-failure-modes.md).
6. If any issue exists, produce a wrong-vs-correct explanation and required fix.

## Output Format

```markdown
## Dependency Audit Result
- Status: PASS / BLOCKED / NEEDS MORE DATA

## Events And Variables
- ...

## Dependency Findings
- Finding:
  - Risk:
  - Correct method:
  - Required data:

## Required Remediation
- ...
```

Do not approve math with unproven independence, missing state variables, or caps applied after expectation.

