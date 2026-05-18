# Team Rollout

## Executive Summary For Tony

`token-saver` reduces avoidable Claude spend by making Sonnet the default for normal work, using Haiku for simple tasks, reserving Opus for deliberate reasoning, disabling 1M context by default, and making context/model usage visible in Claude Code.

## Claude Code Rollout Options

Self-serve users can run the installer in this repository. Admins can deploy the JSON examples in `settings/` through Claude Code managed settings, endpoint-managed settings, or the file-based managed settings path.

Windows file-based managed settings path:

```text
C:\Program Files\ClaudeCode\managed-settings.json
```

Do not use `C:\ProgramData\ClaudeCode\managed-settings.json`.

## Claude Cowork Rollout Options

Install the plugin through Browse plugins or organization plugin management. Cowork users invoke `/token-saver` for model-routing and context-hygiene guidance. Cowork plugin skills are advisory; verified Cowork docs do not show local settings enforcement equivalent to Claude Code.

## Recommended Default Settings

- Default model: `sonnet`.
- Available named models: `sonnet`, `haiku`, `opusplan`.
- Default effort: `low` in settings plus `CLAUDE_CODE_EFFORT_LEVEL=auto`.
- Disable 1M context by default with `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`.
- Use Opus only through `opusplan` unless a senior user intentionally enables `opus`.

## Strict Settings Option

Use `settings/strict-managed-settings.example.json` only after pilot review. It removes `opus` from `availableModels` and maps `ANTHROPIC_DEFAULT_OPUS_MODEL` to Sonnet, which reduces accidental Opus use but may limit legitimate high-value workflows.

## Self-Serve Install Steps

Prerequisites: Claude Code, Node.js 20 LTS or newer, and PowerShell 7 on Windows.

Windows:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

macOS/Linux:

```sh
./scripts/install.sh
```

The installer preserves unrelated settings, backs up existing `settings.json`, deep-merges token-saver settings, and copies hook/status-line scripts into `~/.claude`.

## Admin-Managed Settings Steps

1. Start with `settings/managed-settings.example.json`.
2. Review whether `availableModels` should include `opusplan` for the pilot group.
3. Paste the reviewed JSON into Admin Settings > Claude Code > Managed settings, or deploy it through endpoint-managed settings.
4. Ask users to restart Claude Code.
5. Ask users to run `/status` and confirm the expected settings source.

## Verify A User's Model And Settings

- Run `/model` to inspect available model choices.
- Run `/status` to inspect settings sources and managed settings.
- Run `/usage` to inspect session usage.
- Confirm the status line shows model, effort, context percentage, cache reads, and rate-limit percentage.
- Confirm `sonnet[1m]` and `opus[1m]` are absent when `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` is active.

## Monitor Costs

Use Claude Team or Enterprise usage analytics to compare model mix and spend before and after rollout. Use extra usage and spend limits for Claude.ai/Cowork governance.

## Daily User Behaviors

- Use `sonnet` for normal coding.
- Use `haiku` for simple summaries and classifications.
- Use `opusplan` for costly planning where Opus reasoning helps.
- Use `/clear` between unrelated tasks.
- Use `/rename` before clearing a session worth resuming.
- Use `/resume` or `claude --continue` instead of restating old context.
- Use `/compact Focus on decisions, changed files, tests, blockers, and next steps` before context is bloated.
- Avoid pasting giant logs or asking Claude to read whole repositories.
