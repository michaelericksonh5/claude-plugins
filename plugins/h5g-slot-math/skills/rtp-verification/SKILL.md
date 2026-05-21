---
name: rtp-verification
description: Plans or reviews RTP, Monte Carlo, Test Harness, SlotEngineGUI, PAR sheet, math proof, and simulation verification for H5G slot/RMG math. Use when asked to test math, verify RTP, run or assess simulations, review volatility, hit frequency, PTH, or compare theoretical and simulated results.
when_to_use: Invoke for natural-language requests such as "test the math", "verify RTP", "run Monte Carlo", "is simulation enough", "prepare RMG proof", "certification docs", "compare sim to theory", "PTH", "volatility index", or "Test Harness".
---

# RTP Verification

Verification must reconcile exact math and simulation evidence.

## Workflow

1. Identify theoretical source: exact enumeration, `calculate()`, PAR sheet, state model, or derived formula.
2. Identify simulation source: Test Harness, SlotEngineGUI, custom collector, or standalone simulator.
3. Require the fields in [simulation-report.md](simulation-report.md).
4. Compare theory and simulation using standard error/confidence interval.
5. Check H5G collector/tool fit using [h5g-tool-map.md](h5g-tool-map.md).
6. Block completion if theory and simulation do not reconcile.

## H5G Confluence Facts

- RTP Check documents 10M-20M simulations as common for RTP justification.
- Some games, including simulation-designed games, may require 1B or more simulations.
- RMG math documents use Test Harness simulation details and commonly use `StopsWithOrWithoutReplacement`.
- SlotEngineGUI reports RTP, hit frequency, PTH, volatility index, buckets, RTP by outcome type, and RTP by symbol.
- H5G Volatility Index is `1.65 * standard deviation`.

## Output Format

```markdown
## Verification Status
- PASS / BLOCKED / NEEDS MORE DATA

## Theoretical Basis
- Source:
- RTP:
- Variance/SD:
- Feature contribution:

## Simulation Evidence
- Tool/collector:
- Spins:
- Seed:
- Observed RTP:
- Standard error / CI:
- Event counts:

## Reconciliation
- Difference:
- Within expected interval:
- Follow-up:
```

