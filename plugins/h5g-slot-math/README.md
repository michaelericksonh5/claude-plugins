# H5G Slot Math Claude Plugin

Auto-invoked, probability-first Claude plugin for High 5 Games slot math work.

This plugin packages the research in `C:\Users\merickson\Claude Slot Math` into focused skills, reference files, templates, and a lightweight prompt hook. It is designed to be conjured from natural language whenever users discuss math, RTP, RMG, odds, payouts, simulations, reel strips, PAR sheets, jackpots, or certification math.

## Contents

- `skills/slot-math-core`: standing rules for all slot math work.
- `skills/probability-model`: build or update a probability model.
- `skills/dependency-audit`: audit dependent probabilities and common Claude failure modes.
- `skills/rtp-verification`: plan or review exact math, Monte Carlo, Test Harness, and SlotEngineGUI verification.
- `skills/internal-h5g-evidence`: apply internal H5G Confluence process gates.
- `skills/rules-install`: install or update global and project Claude rule markdown.
- `hooks/slot-math-prompt-guard.mjs`: injects a compact reminder only for slot-math-like prompts.
- `scripts/validate-plugin.mjs`: local structural validation.
- `DESKTOP.md`: Claude Desktop, Cowork, Code, and marketplace installation notes.

## No Slash Commands Required

Users can ask naturally after installing the plugin. Claude should load the
relevant skills when the conversation mentions slot math, RTP, RMG, odds,
payouts, reel strips, PAR sheets, simulations, jackpots, certification math,
or dependent probabilities.

Example natural prompts:

- "Can you check whether this bonus RTP makes sense?"
- "Are these paylines independent?"
- "Prepare the RMG math proof and test it."
- "Does this scatter probability need full reel-window enumeration?"
- "Compare the Monte Carlo result to the theoretical model."

Slash commands are optional manual overrides for targeted use. The
`rules-install` skill is intentionally manual-only because it writes rule files.

## Test Locally

```bash
claude --plugin-dir .
```

Then run:

```bash
/h5g-slot-math:rules-install
/h5g-slot-math:probability-model
/h5g-slot-math:dependency-audit
```

Validate:

```bash
node scripts/validate-plugin.mjs
claude plugin validate . --strict
```

## Desktop / Cowork / Code

Most users should install this through Claude Desktop rather than starting the CLI with `--plugin-dir`.

- Plugins are available in Cowork and Code, not Chat.
- Code supports plugins for local and SSH sessions; remote sessions do not use plugins.
- Desktop users can install from Customize -> Plugins, from an organization marketplace, or from an uploaded plugin package.
- A local upload package is available at `C:\Users\merickson\Documents\Claude_Plugins\h5g-slot-math-0.2.3.zip`.
- See `DESKTOP.md` for the current workflow and marketplace notes.

## Natural-Language Invocation

The plugin uses two layers:

1. Skill `description` and `when_to_use` metadata so Claude can load the right skill when prompts mention math/RTP/RMG naturally.
2. A lightweight `UserPromptSubmit` hook that injects a compact reminder only for prompts that look slot-math-related.

Expected examples:

- "Can you check the RTP on this game?"
- "Does this scatter probability math work?"
- "Prepare the RMG math proof."
- "Run Monte Carlo and compare to the theoretical model."
- "Are these paylines independent?"
- "What is the jackpot probability for PA?"

## Design Notes

The plugin uses progressive disclosure. `SKILL.md` files are concise; detailed examples and checklists live in one-level reference files. This keeps the always-visible skill descriptions useful without loading all math research into every context window.

