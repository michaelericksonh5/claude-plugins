# Context Hygiene

Small context keeps turns cheaper and more reliable.

- Keep `CLAUDE.md` under 200 lines where possible.
- Move specialized workflows to skills.
- Use `/clear` between unrelated tasks.
- Use `/rename` before clearing important sessions.
- Use `/resume` instead of re-explaining old context.
- Use `/compact Focus on goal, decisions, changed files, files read, errors, tests, blockers, and next steps`.
- Do not paste giant logs. Save logs to files and ask Claude to extract only errors.
- Do not ask Claude to "read the whole repo" when a targeted file or symbol search will do.

## Context Engineering Playbook

Use four moves in this order:

1. `Write`: save large logs, terminal output, research notes, and plans to files. Keep only a short summary and path in chat.
2. `Select`: retrieve only the relevant file, line range, symbol, or search result. Avoid broad reads and generic "scan everything" requests.
3. `Compress`: compact before the context is bloated. In Claude Code, use 70-80% context usage as the normal trigger range.
4. `Isolate`: use a fresh session or subagent for unrelated work, noisy exploration, or independent log analysis.

Optimize for tokens per task, not tokens per request. A summary that saves tokens but drops file paths, error messages, or decisions can make Claude re-read and re-discover the same facts, which costs more overall.

## Compact Summary Checklist

When compacting, preserve:

- User goal and current task.
- Decisions made and why.
- Files modified, with exact paths and important symbols.
- Files read but not changed, when they matter.
- Exact error messages, failing commands, and test status.
- Blockers, assumptions, and next steps.

Do not compress away tool schemas, important file paths, active debugging errors, early user constraints, or security-sensitive instructions.

## Degradation Signals

Context is getting unhealthy when Claude:

- Ignores information that is present in the middle of a long thread.
- Repeats an incorrect assumption after being corrected.
- Mixes requirements from unrelated tasks.
- Treats stale docs or old implementation details as current.
- Keeps reading more files instead of narrowing to the failing path.

When this happens, reduce context instead of adding more context. Compact with the checklist above, clear and restart with verified facts, or isolate the work in a subagent/session.

For large terminal output, prefer saving the output to a file and asking Claude to inspect only the failing lines or summary. For repeated automation in the same project, keep the same session warm with resume or continue flows.

For prompt caching, keep reusable instructions stable. Avoid adding timestamps, request IDs, or other changing metadata to prompts that should cache well.
