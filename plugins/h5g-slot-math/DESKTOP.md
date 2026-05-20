# Claude Desktop, Cowork, and Code Notes

This plugin is designed for the recent Claude Desktop app as well as the terminal CLI.

## Product Surface

Current docs distinguish three Desktop tabs:

- Chat: general conversation. Plugins are not used here.
- Cowork: Dispatch and longer agentic work. Plugins are available here.
- Code: software development sessions. Plugins are available here for local and SSH sessions.

Code remote sessions do not currently support plugins. SSH sessions do.

## Install In Desktop

Desktop path:

1. Open Claude Desktop.
2. Open Customize in the sidebar.
3. Open Plugins.
4. Install from an organization marketplace, added marketplace, or uploaded plugin package.
5. Open the installed plugin and review its skills, agent, and hook components.
6. Enable the components needed for the session.

Inside a Code session, users can also click the `+` button by the prompt box, select Plugins, and manage/install plugins from there.

Local upload package:

```text
C:\Users\merickson\Documents\Claude_Plugins\h5g-slot-math-0.2.0.zip
```

## Install From A Marketplace

For team distribution, put this plugin in a marketplace repository. This local development folder includes a marketplace catalog one level up:

```text
C:\Users\merickson\Documents\Claude_Plugins\.claude-plugin\marketplace.json
```

CLI test:

```bash
claude plugin marketplace add "C:\Users\merickson\Documents\Claude_Plugins"
claude plugin install h5g-slot-math@h5g-plugins
```

For broader team use, host the marketplace repository on GitHub or GitHub Enterprise and add that repo from Desktop's Plugins page.

## Use In Desktop

After installation, users do not need slash commands for ordinary math work.
They can ask naturally about slot math, RTP, RMG, odds, payouts, reel strips,
Monte Carlo, PAR sheets, dependent probabilities, jackpots, or certification
math. Claude should invoke the relevant H5G Slot Math skills automatically
from the skill descriptions and `when_to_use` metadata.

Slash commands remain available as explicit manual overrides:

```text
/h5g-slot-math:probability-model
/h5g-slot-math:dependency-audit
/h5g-slot-math:rtp-verification
/h5g-slot-math:internal-h5g-evidence
/h5g-slot-math:rules-install
```

The `slot-math-core` skill is model-invoked background context and is not meant
as the primary user command. The `rules-install` skill is intentionally
manual-only because it edits Claude rule files.

## Hook Expectations

The plugin includes a lightweight `UserPromptSubmit` hook. Current official Desktop/Cowork plugin docs list hooks as supported plugin components. The hook is intentionally compact and only injects context for prompts that look slot-math-related.

If an admin or Desktop environment disables hooks, the skills still carry the core rules. The hook is reinforcement, not the only enforcement layer.

