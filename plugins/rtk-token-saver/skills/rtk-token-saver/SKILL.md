---
name: rtk-token-saver
description: Guide Claude users through RTK-based token reduction, compact TLDR replies, model routing, context hygiene, and conflict-safe setup. Use when a user asks about token usage, Claude cost, shell output filtering, compact output, TLDR mode, RTK, rtk-ai/rtk, model choice, Haiku/Sonnet/Opus routing, context compaction, or replacing token-saver.
---

# RTK Token Saver

This plugin is an H5G wrapper around upstream RTK. RTK is the shell-output reduction engine; this skill provides H5G setup guidance, compact TLDR output guidance, Claude model-routing rules, rollout checks, and conflict warnings.

RTK is not vendored here and this plugin does not fork RTK. In Claude Code, plugin hooks check or install pinned RTK automatically and wrap selected noisy Bash commands when RTK is available. The hooks fail open so normal commands keep running if RTK cannot be installed or checked.

## First Response Checklist

When invoked, identify:

- Whether the user is using Claude Code, Claude Desktop/Cowork, Cursor, or automation.
- Whether the Claude Code plugin hook reported RTK installed, available, or unavailable.
- Whether Claude Code already has legacy token-saver or other `PreToolUse` hooks that might conflict.
- Whether compact TLDR replies would reduce generated output without hiding safety or verification details.
- Whether the task is small enough for `haiku` or `sonnet` instead of `opus`.
- Whether context is near 70% or 85%.

## Model Routing

- Use `haiku` for summaries, extraction, classification, and simple rewrites.
- Use `sonnet` for routine coding, debugging, and implementation.
- Use `opusplan` for planning that benefits from Opus reasoning while keeping execution on Sonnet.
- Use `opus` only when the task is genuinely high-risk, ambiguous, or Sonnet has already been insufficient.
- Avoid `sonnet[1m]` and `opus[1m]` unless the user explicitly approves a long-context task.

If Opus is active for a small task, recommend switching to `sonnet` or `haiku` before continuing.

## RTK Guidance

Use RTK for noisy shell workflows such as test runs, package manager output, Git/GitHub output, Docker/Kubernetes output, logs, and other verbose command results.

In Claude Code, the plugin wraps selected simple noisy Bash command prefixes as `rtk <command>`. It skips already wrapped commands, chained commands, pipes, redirection, and commands outside the selected prefixes.

Do not hide important output from the user. If RTK compacts a command and the task depends on exact details, ask for the full RTK log path or rerun the command with raw output redirected to a file.

## Context Hygiene

- Use `/clear` between unrelated tasks.
- Use `/compact` before context becomes degraded; 70-80% is the normal warning range.
- Save large logs to files and read/search only targeted ranges.
- Prefer specific file/symbol searches over broad repository reads.
- Use concise subagent handoffs for noisy exploration.

## Compact TLDR Output

Compact TLDR output reduces generated response tokens and future transcript size by keeping replies professional, TLDR-first, and safety-aware. It does not filter shell output and does not summarize existing context.

- RTK reduces noisy shell-output input/context tokens in Claude Code.
- Compact TLDR is forced by this plugin in Claude Code and reduces generated assistant output tokens.
- `/compact` summarizes existing conversation context when it is getting full.

In Claude Desktop/Cowork, RTK and Compact TLDR remain advisory unless that surface honors Claude Code plugin hooks and output styles.

For detailed compact-output rules and templates, read `COMPACT_OUTPUT.md`.

For detailed references, read:

- `RTK_SETUP.md`
- `MODEL_ROUTING.md`
- `CONTEXT_HYGIENE.md`
- `COMPACT_OUTPUT.md`
- `TROUBLESHOOTING.md`
