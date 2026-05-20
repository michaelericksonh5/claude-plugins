# Worked Dependency Examples

These are toy examples for reasoning patterns only. They are not H5G production math.

## Dependent Paylines

Toy setup: three reels, each strip `[A, B, C]`; three visible rows are previous/current/next; top/middle/bottom horizontal lines pay `1` for three of a kind.

Wrong:

```text
P(any horizontal line wins) = P(top) + P(middle) + P(bottom) = 1/3
```

Correct:

```text
P(any horizontal line wins) = P(all reel stops equal) = 1/9
```

EV can still sum:

```text
EV = 1/9 + 1/9 + 1/9 = 1/3
```

Distribution-sensitive metrics must use the full payout distribution.

## Scatter Windows

Toy reel: `[S, S, B, B]`, visible window previous/current/next.

Correct per-reel scatter count:

```text
P(C = 1) = 1/2
P(C = 2) = 1/2
P(C = 0) = 0
P(C = 3) = 0
```

Wrong: treating three visible cells as independent Bernoulli draws with `P(S)=1/2`, which falsely gives `P(3 scatters)=1/8`.

Correct method: enumerate reel windows, then convolve reel distributions.

## Retriggers

Feature starts with 3 spins. Each spin retriggers 2 more spins with probability `0.10`; spin EV is `1x`; no cap.

Wrong:

```text
EV = 3 * 1 = 3x
```

Correct:

```text
m = 0.10 * 2 = 0.20
E[total_spins] = 3 / (1 - 0.20) = 3.75
EV = 3.75x
```

With caps, counters, persistence, or modifiers, use a state model instead.

## Correlated Multipliers

If the same wild event raises both base win and multiplier:

```text
E[win * multiplier] != E[win] * E[multiplier]
```

Enumerate joint states or compute `E[payout | state]`.

## Caps

If `X=1000` with probability `0.10`, `X=0` otherwise, cap is `100`:

```text
E[min(X, cap)] = 0.10 * 100 = 10
```

Do not use:

```text
min(E[X], cap)
```

