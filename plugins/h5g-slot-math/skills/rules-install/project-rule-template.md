---
paths:
  - "math/**/*"
  - "src/math/**/*"
  - "src/game/**/*"
  - "src/simulation/**/*"
  - "tests/math/**/*"
  - "reports/math/**/*"
  - "reports/simulation/**/*"
---

<!-- BEGIN H5G SLOT MATH RULES -->
# H5G Probability-Based Slot Math

This project creates or verifies slot-machine math. Every math-affecting change must be traceable to a probability model.

## Math-Critical Areas

Treat these as math-critical:

- Reel strips, symbol weights, virtual stops, visible-window mappings.
- Paytables, lines, ways, cluster rules, scatter rules, wild rules.
- Weighted tables, random modifier tables, pick tables, wheel slices, jackpot tables.
- RNG adapters, scaling, shuffling, mapping, state selection, outcome evaluation.
- Bonus triggers, free spins, respins, hold-and-spin, persistence, collectors.
- Bet configuration, feature buy, ante, RTP variants, jurisdictional config.
- Caps, rounding, credit conversion, settlement.
- Math tests, simulations, PAR sheets, and generated reports.

## Required Model

For each math change, define:

- Game cycle.
- Sample/state space.
- Probability measure or transition probabilities.
- Payout random variable and normalization.
- EV, RTP, second moment, variance, SD.
- Hit frequency and win frequency definition.
- Bonus trigger probability and feature EV.
- RTP decomposition.
- Max win and max-win probability.
- Dependency proof or state model.
- Probability mass reconciliation.

## Refusal / Stop Conditions

Stop if asked to:

- "Just make it around 96%" without source data.
- Change payouts or weights without recalculating RTP and variance.
- Use simulation alone when exact math is tractable.
- Assume paylines, visible cells, scatters, multipliers, collectors, or retriggers are independent without proof.
- Ignore caps, persistence, dynamic versions, jurisdiction, or user-choice policy.
- Call math inspection-ready without reproducible artifacts.

## Verification

Simulation must include seed, spins, observed RTP, sample SD, standard error, confidence interval, hit frequency, feature counts, rare-event counts, max observed win, and comparison to theory.
<!-- END H5G SLOT MATH RULES -->

