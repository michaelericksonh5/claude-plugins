# Model Decision Tree

## EV-Only Or Distribution-Sensitive?

If only EV is needed, linearity of expectation can allow component sums.

If hit frequency, win frequency, variance, volatility, max-win probability, caps, or payout distribution are needed, use full distribution or joint/state modeling.

## Finite Reel Stop Space?

Use exact full-screen enumeration when reel stop tuples are finite and tractable.

Use aggregation only if it preserves `E[X]`, `E[X^2]`, and requested distribution metrics.

## Visible-Anywhere Counts?

Use reel-window enumeration per reel and convolve count distributions.

Do not use independent-cell binomial formulas unless cells are sampled independently by implementation.

## Union Event?

For "at least one" events, use:

- Inclusion-exclusion for small event sets with known intersections.
- Full enumeration for screen-derived events.
- State model for sequence-derived events.

## Stateful Feature?

Use dynamic programming or Markov chains when there are:

- Retriggers.
- Respins or reset counters.
- Locked symbols.
- Persistent multipliers or meters.
- Collectors, upgrades, transformations.
- Cascades or multiple acts per wager.

State must contain all information needed to determine future probabilities and payouts.

## Capped Outcome?

Derive `E[min(X, cap)]` from the final path/outcome distribution.

Do not cap the final average.

## Exact Math Infeasible?

Use simulation only after defining the state/sample space and payout evaluator. Report standard error, confidence interval, rare-event counts, and reconciliation against theory.

