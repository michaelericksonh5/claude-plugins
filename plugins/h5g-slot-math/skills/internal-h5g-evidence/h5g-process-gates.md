# H5G Process Gates

Derived from internal Confluence research captured on 2026-05-20.

## RTP Check

Require:

- Test script and test parameters.
- Number of simulations.
- Bet/multiplier, lines to play, total bet.
- Expansion.
- Game ID.
- Dynamic version, if present.
- Theoretical RTP comparator.

Confluence note: 10M-20M simulations commonly justify RTP; some simulation-designed games may need 1B or more.

## RMG Math Documents

Require:

- Correct game and clone.
- Correct SlotEngine and version.
- Expansion in the RMG range, usually 960-969 when applicable.
- Math certification ticket.
- Slot engine from Nexus.
- Game summary report.
- Math proof from Perforce in RMG format.
- Math files in expansion.
- Test Harness simulation details.
- Correct RMG collector.

## Release Verification

Require:

- RTP verification before release or clone addition.
- Engine version check.
- Assembly/build success.
- Shotgun/Nexus/latest version alignment.
- Config game ID and trademarked name check.
- Default expansion check.
- Backward-compatibility analysis for outcomes, context, criteria, and math file format.
- Math Commons version compatibility.

## Math Commons

Treat as high blast radius. Require:

- Affected SlotEngines.
- Backward compatibility analysis.
- Broad regression coverage.
- Clear handling of formal vs snapshot version use.

## Dynamic Gameplay

Report separately for:

- Default version `0`.
- `200% RTP` version `1`.
- `Guaranteed Bonus Trigger` version `2`.
- `Lower Volatility Version` version `3`.
- `Lower RTP Version` version `4`.
- `Higher Hit Frequency` version `5`.

Do not average across versions unless the distribution over versions is specified.

## Substitution

Require:

- Replacement symbols and regions.
- Scheme files and weights.
- Perturb files and weights.
- PreProcessor order.
- Whether substitution is per region, symbol, reel, or mode.

Correct modeling order: reel stops first, substitution second, evaluation third.

## Independent Reels / Tumbling / Memory Features

Require:

- Position-specific strips for independent reels.
- Act/evaluation sequence for tumbling or extended-play games.
- State variables for memory features.
- Geometry and redraw rules when shapes, boards, or visible areas matter.

## Progressive Jackpots

Require:

- Jurisdiction.
- Timed vs non-timed jackpot.
- Trigger event and probability.
- Qualifying wager.
- Parameter set and change process.
- Pool rules.
- Whether bonus/free spins participate.

Known Confluence constraints include jurisdiction-specific certification, PA 1-in-50M probability cap, MI minimum qualifying wager clarification, WV linear probability blocker, CT GLI-19 disclosure, and bonus/free-spin jackpot exclusion across documented jurisdictions.

