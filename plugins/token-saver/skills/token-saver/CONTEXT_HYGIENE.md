# Context Hygiene

Small context keeps turns cheaper and more reliable.

- Keep `CLAUDE.md` under 200 lines where possible.
- Move specialized workflows to skills.
- Use `/clear` between unrelated tasks.
- Use `/rename` before clearing important sessions.
- Use `/resume` instead of re-explaining old context.
- Use `/compact Focus on decisions, changed files, tests, blockers, and next steps`.
- Do not paste giant logs. Save logs to files and ask Claude to extract only errors.
- Do not ask Claude to "read the whole repo" when a targeted file or symbol search will do.

For large terminal output, prefer saving the output to a file and asking Claude to inspect only the failing lines or summary. For repeated automation in the same project, keep the same session warm with resume or continue flows.
