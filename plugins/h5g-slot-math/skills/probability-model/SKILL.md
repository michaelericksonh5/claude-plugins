---
name: probability-model
description: Builds or updates explicit probability models for H5G slot/game math. Use for natural-language requests about math, RTP, RMG, odds, payouts, paytables, reel strips, weights, EV, variance, free spins, hold-and-spin, collectors, WYS symbols, jackpots, feature buys, ante bets, or PAR-style calculations.
when_to_use: Invoke when the user asks to make, change, calculate, explain, tune, review, or reason about any chance-based math model, even if they do not say "probability model" explicitly.
---

# Probability Model

Build the model before numbers.

## Workflow

1. Classify the task and game cycle.
2. Gather required inputs from [model-inputs.md](model-inputs.md).
3. If inputs are missing, stop and report blockers.
4. Define the sample space or state space.
5. Define probabilities or transition probabilities.
6. Define payout evaluation and normalization.
7. Choose the modeling method from [model-decision-tree.md](model-decision-tree.md).
8. Calculate EV, RTP, second moment, variance, SD, hit frequency, win frequency, feature EV, and max-win probability.
9. Reconcile probability mass and RTP components.
10. Produce the completion template from `slot-math-core`.

## Required Output

```markdown
## Inputs
- Provided:
- Missing:

## Probability Model
- Game cycle:
- Sample/state space:
- Probability measure:
- Payout random variable:
- Dependency proof:

## Calculation Method
- Exact enumeration / convolution / inclusion-exclusion / dynamic programming / Markov chain / simulation:
- Why this method applies:

## Results
- RTP decomposition:
- Hit/win frequency:
- Variance/SD:
- Feature EV:
- Max win:

## Verification
- Probability mass:
- Reconciliation:
- Simulation plan/results:

## Blockers
- ...
```

Do not present final math if blockers remain.

