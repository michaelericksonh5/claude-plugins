---
name: token-saver
description: Reduce Claude token usage and cost by choosing the right model, limiting unnecessary context, using /clear and /compact deliberately, avoiding giant file/log reads, moving long instructions into skills, and applying Claude Code settings or managed settings where available. Use when a user asks about Claude costs, token limits, context window pressure, model choice, Opus/Sonnet/Haiku selection, Claude Code settings, Cowork plugin cost hygiene, prompt caching, or reducing repeated context.
---

# Token Saver

Start by identifying the user's environment:

- Claude Code
- Claude Desktop or Claude Cowork
- Claude Code SDK automation
- Direct API integration

Use this default routing:

- `haiku`: simple summarization, classification, small transforms, and cheap subagents.
- `sonnet`: normal coding, debugging, and implementation.
- `opusplan`: expensive planning where Opus reasoning helps but Sonnet should execute.
- `opus`: hard architecture, ambiguous multi-system debugging, or high-risk reasoning where Sonnet has failed or is likely insufficient.
- `sonnet[1m]` or `opus[1m]`: only for explicitly approved long-context emergencies.

Keep context small:

- Recommend `/clear` when switching unrelated tasks.
- Recommend `/rename` before clearing sessions that users may resume later.
- Recommend `/compact Focus on decisions, changed files, tests, blockers, and next steps` before context gets bloated.
- Avoid reading large logs, generated files, lockfiles, and build outputs unless the task requires them.
- Prefer targeted search, file globs, and symbol/code-intelligence tools over broad file reads.
- Use subagents for verbose exploration or log processing, returning only concise summaries to the main conversation.

For deeper guidance, read:

- `MODEL_ROUTING.md`
- `CONTEXT_HYGIENE.md`
- `AUTOMATION_GUIDE.md`
- `COWORK_GUIDE.md`

Claude Code settings can install or enforce defaults. Cowork plugin skills are advisory; do not claim they enforce Claude Code `settings.json` or hard model restrictions.
