# Verification Checklist

## Exact Math Checks

- Probability mass sums to `1`.
- Every reachable outcome/state is evaluated.
- No outcome is double-counted unless overlapping pays are explicit.
- Payout normalization is consistent.
- `RTP_total = RTP_base + RTP_feature + RTP_jackpot + other documented components`.
- `E[X]` from distribution matches component EV.
- `Var(X) = E[X^2] - E[X]^2`.
- Hit frequency equals probability mass with payout greater than zero.
- Max-win probability is taken from the capped/final distribution.

## Simulation Checks

Report:

- Seed or seed schedule.
- Number of game cycles.
- Observed RTP.
- Theoretical RTP.
- Sample standard deviation.
- Standard error: `sample_sd / sqrt(n)`.
- Confidence interval.
- Hit frequency.
- Bonus/retrigger/jackpot event counts.
- Max observed win.

If theoretical values fall outside expected confidence intervals, block completion and investigate.

## H5G Tool Evidence

Use internal H5G tools when applicable:

- Test Harness collectors for engine statistics.
- `StopsWithOrWithoutReplacement` for common RMG document output.
- `StopsWithReplacementForGameWithDoBonusSpin` for engines using `doBonusSpin()`.
- `ScatterBucksWithOrWithoutReplacement` when WYSIWYG information is required.
- Custom collector when a dependency-heavy feature cannot be measured by a general collector.
- SlotEngineGUI Simulation Mode for RTP, hit frequency, PTH, volatility index, buckets, RTP by outcome type, and RTP by symbol.
- SlotEngineGUI Calculation Mode or engine `calculate()` when implemented.

Simulation evidence does not replace exact math when exact math is tractable.

