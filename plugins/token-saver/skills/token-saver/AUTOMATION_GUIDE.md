# Automation Guide

Automation should avoid rediscovering the same repository context on every run.

- Use `claude --continue` for the most recent session when running sequential automation in the same project.
- Use `claude --resume <session-id-or-name>` when continuing a known session.
- SDK automation should capture `session_id` from result messages and use `resume`.
- Keep `cwd` stable when resuming because session lookup is tied to project path.
- For CI or ephemeral hosts, either persist `~/.claude/projects/.../*.jsonl` at the same path or pass distilled state into a fresh prompt instead of relying on resume.

For scripted tooling in this plugin, use Node.js. Do not introduce Python scripts or Python examples.
