# H5G Tool Map

Use internal tools when they fit the request.

## Test Harness

Use for extracting specific data from SlotEngines by simulation.

General collectors:

- `GameDataCollector`: buckets, symbol RTPs, PTH, retrigger PTH, hit frequency, volatility.
- `HitTableCollector`: base/free bonus hit frequency table.
- `PayLinesWinDistributionCollector`: payline win distribution.
- `OverTimesOfBetWonCollector`: wins beyond bet multiples.
- `RateOfExhaustionCollector`: session exhaustion model.

RMG collectors:

- `StopsWithOrWithoutReplacement`: common RMG collector for bet, win credits, stops, replacement.
- `OnlyBonusStopsWithOrWithoutReplacement`: bonus-only variant.
- `StopsWithReplacementForGameWithDoBonusSpin`: for `doBonusSpin()` engines.
- `ScatterBucksWithOrWithoutReplacement`: WYSIWYG information.
- `RMGWinmapCollector`: global/base/bonus winmaps.

Use a custom collector when a dependency-heavy feature is not covered.

## SlotEngineGUI

Use for interactive and command-line simulation:

- Base Game RTP.
- Bonus Game RTP.
- Bonus Event RTP.
- Bonus Spin RTP.
- Hit frequency.
- Bonus PTH and retrigger PTH.
- Volatility Index (`1.65 * SD`).
- Buckets / histograms.
- RTP by outcome type.
- RTP by symbol.
- Multi-Sim for bet/gaffe/choice scenarios.
- Calculation Mode when `calculate()` exists.

## RMG Documents

For certification-style docs, verify:

- Slot engine from Nexus.
- Correct game, clone, version, and expansion.
- RMG expansion 960-969 when applicable.
- Math proof from Perforce in RMG format.
- Math files in expansion.
- Correct Test Harness collector and simulation output.

