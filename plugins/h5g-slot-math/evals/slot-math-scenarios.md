# Slot Math Skill Evaluation Scenarios

Use these manually after loading the plugin with `claude --plugin-dir .`.

## Scenario 0: Natural Language Invocation

Prompt:

```text
Can you check whether the game math and RTP make sense for this bonus?
```

Expected:

- Claude invokes H5G slot math guidance without requiring a slash command.
- Claude asks for the probability model inputs before giving numbers.
- Claude treats simulation as verification, not proof.

Prompt:

```text
Prepare the RMG proof and test it.
```

Expected:

- Claude invokes internal H5G evidence and RTP verification guidance.
- Claude asks for engine, expansion, proof format, collector, math files, and simulation details.

## Scenario 1: Missing Source Data

Prompt:

```text
Make this slot 96% RTP. It has five reels and a bonus.
```

Expected:

- Claude stops.
- Lists missing reel strips, paytable, feature rules, bet model, RNG/weights, caps, and target tolerance.
- Does not invent math.

## Scenario 2: Dependent Paylines

Prompt:

```text
Can I add the hit frequency for 20 paylines by summing each line's hit frequency?
```

Expected:

- Claude says no unless line-hit events are disjoint or independence is proven.
- Explains full-screen distribution or inclusion-exclusion.
- Notes EV can sum via linearity but hit frequency cannot.

## Scenario 3: Scatter Windows

Prompt:

```text
The scatter appears on 10% of each reel strip. Can I use a binomial over 15 visible cells for a 5x3 game?
```

Expected:

- Claude blocks the binomial assumption unless cells are independently sampled.
- Requires reel-window count distribution and convolution.

## Scenario 4: Correlated Multipliers

Prompt:

```text
The wild causes the win and also applies a multiplier. Can we use average win times average multiplier?
```

Expected:

- Claude says no unless independence is proven.
- Requires joint states or conditional payout by state.

## Scenario 5: RMG Certification Docs

Prompt:

```text
Prepare the RMG math docs for this game.
```

Expected:

- Claude asks for game, engine, version, expansion, clone, math proof, math files, collector, and simulation details.
- References Test Harness and RMG collector requirements.

## Scenario 6: Jackpot Jurisdiction

Prompt:

```text
Calculate the jackpot RTP for Pennsylvania.
```

Expected:

- Claude requests jurisdiction-specific config, jackpot type, trigger, qualifying wager, parameter set, pool rules, and contribution rules.
- Notes PA-specific constraints from internal research, including probability cap and re-review needs.

