# Simulation Report Requirements

Every Monte Carlo or simulation result must state:

- Simulator/tool name.
- Engine, game ID, expansion, dynamic version, and jurisdiction if applicable.
- Number of game cycles.
- Seed or seed schedule.
- Bet configuration and normalization.
- Observed RTP.
- Theoretical RTP.
- Sample standard deviation.
- Standard error: `sample_sd / sqrt(n)`.
- Confidence interval, typically `mean +/- 1.96 * standard_error` when normal approximation is appropriate.
- Hit frequency and win frequency definition.
- Bonus trigger count and rate.
- Retrigger count and rate.
- Jackpot count and rate.
- Rare-event counts.
- Max observed win.
- Source config hash/version ID when available.

Block completion if:

- No theoretical comparator exists and exact math is tractable.
- Event counts are too sparse for claimed validation.
- Theoretical RTP falls outside the expected confidence interval.
- Simulation omits the feature/dynamic version/jurisdiction being reviewed.

