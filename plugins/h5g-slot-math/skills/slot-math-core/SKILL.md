---
name: slot-math-core
description: Auto-applies H5G probability-first rules whenever a conversation involves slot math, game math, RTP, RMG, odds, payouts, reel math, probability, PAR sheets, Monte Carlo, simulation, Test Harness, SlotEngine, jackpots, free spins, hold-and-spin, WYS/collector symbols, or chance-based game mechanics.
when_to_use: Invoke for any natural-language discussion of math, RTP, RMG, volatility, hit frequency, win frequency, expected value, variance, prize odds, paytables, reel strips, symbol weights, RNG, certification math, or regulated game outcomes.
user-invocable: false
---

# H5G Slot Math Core

Use this as standing context for any H5G slot math task.

## Non-Negotiable Standard

1. Slot math must be probability-based.
2. Do not create, tune, approve, or call math complete from intuition, target feel, art theme, or simulation-only evidence when exact math is tractable.
3. If required inputs are missing, stop and list them. Do not invent assumptions.
4. Treat independence as a claim requiring proof.
5. Apply max-win caps at the outcome/path level before expectation.

## Required Probability Basis

For math-affecting work, produce or verify:

- Game cycle from wager through final settlement.
- Elementary outcomes or feature states.
- Sample space or state space.
- Probability measure or transition probabilities.
- Payout random variable and normalization unit.
- Expected value, RTP, second moment, variance, standard deviation.
- Hit frequency, win frequency definition, bonus trigger probability.
- Feature EV and RTP contribution.
- Max win and max-win probability.
- Probability mass reconciliation.

## Dependency Discipline

Use the dependency rules in [dependency-checklist.md](dependency-checklist.md). For worked examples, use [worked-examples.md](worked-examples.md).

## Verification Discipline

Simulation is verification, not the model. Use [verification-checklist.md](verification-checklist.md) for exact math, Monte Carlo, Test Harness, SlotEngineGUI, and RMG document evidence.

## Completion Format

For completed slot math work, report:

```markdown
## Probability Basis
- Sample/state space:
- Probability measure:
- Payout random variable:
- Independence/dependence proof:

## Results
- Base RTP:
- Feature RTP:
- Jackpot RTP:
- Total RTP:
- Hit frequency:
- Win frequency:
- Variance / SD:
- Max win and probability:

## Verification
- Exact enumeration/derivation:
- Probability mass check:
- Simulation evidence, if used:
- Files/artifacts updated:

## Assumptions or Blockers
- ...
```

If any required field is unknown, do not claim completion.

