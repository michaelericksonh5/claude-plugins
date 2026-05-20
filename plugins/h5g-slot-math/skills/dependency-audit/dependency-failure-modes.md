# Dependency Failure Modes

Block approval if any of these appear.

## Line And Screen Errors

- Summing marginal line-hit probabilities to get "any line wins".
- Treating paylines on the same screen as independent.
- Calculating variance from independent line assumptions without covariance or full distribution.
- Evaluating ways/cluster/cascade games as independent line games.

## Scatter And Coin Errors

- Treating visible cells on the same reel as independent.
- Using payline symbol probability for visible-anywhere scatter counts.
- Ignoring reel restrictions or multiple scatters on one reel.
- Ignoring substitution or preprocessing before scatter evaluation.

## Feature Errors

- Ignoring retriggers.
- Treating reset counters as stateless.
- Using a flat average feature award without deriving it from states.
- Ignoring locked symbols, collected values, upgrades, transformations, or persistence.
- Averaging across dynamic versions or user choices without a policy.

## Multiplier And Wild Errors

- Multiplying average win by average multiplier when the same event affects both.
- Ignoring wild-only priority, substitution order, or overlap rules.
- Treating expanding reels/wilds as independent cell events.

## Cap And Jackpot Errors

- Applying max-win cap to `E[X]` instead of each outcome/path.
- Using jackpot trigger odds without jurisdiction, qualifying wager, parameter set, and pool rules.
- Ignoring bonus/free-spin jackpot exclusion where jurisdiction/config says jackpots do not participate.

## Simulation Errors

- Calling simulation proof when exact enumeration is tractable.
- Missing seed, spin count, sample SD, standard error, or confidence interval.
- Claiming rare-event probability from too few or zero observed hits.
- Accepting simulation outside confidence interval without investigation.

