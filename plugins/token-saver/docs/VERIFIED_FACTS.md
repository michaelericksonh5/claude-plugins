# Verified Facts

Sources:

- Claude Code costs: https://docs.anthropic.com/en/docs/claude-code/costs
- Claude Code model configuration: https://code.claude.com/docs/en/model-config
- Claude Code settings: https://code.claude.com/docs/en/settings
- Claude Code environment variables: https://code.claude.com/docs/en/env-vars
- Claude Code server-managed settings: https://code.claude.com/docs/en/server-managed-settings
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Claude Code status line: https://code.claude.com/docs/en/statusline
- Claude Code plugins: https://code.claude.com/docs/en/plugins-reference
- Plugin marketplaces: https://code.claude.com/docs/en/plugin-marketplaces
- Prompt caching: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- Cowork plugins: https://support.claude.com/en/articles/13837440-use-plugins-in-claude-cowork
- Cowork organization plugins: https://support.claude.com/en/articles/13837433-manage-claude-cowork-plugins-for-your-organization
- Team and Enterprise usage analytics: https://support.anthropic.com/en/articles/12883420-view-usage-analytics-for-team-and-enterprise-plans
- Extra usage and spend limits: https://support.anthropic.com/en/articles/12005970-manage-extra-usage-for-team-and-seat-based-enterprise-plans

## Claude Code Settings

Verified Claude Code settings used by this plugin are `model`, `availableModels`, `effortLevel`, `env`, `statusLine`, `hooks`, and managed-setting-only `forceRemoteSettingsRefresh`.

`model` sets the initial/default model. `availableModels` restricts selectable named models through `/model`, `--model`, and `ANTHROPIC_MODEL`, but it does not remove the `Default` picker option. Use `model`, `availableModels`, and `ANTHROPIC_DEFAULT_*_MODEL` environment variables together when stronger default behavior is needed.

## Model Aliases

Verified Claude Code aliases include `haiku`, `sonnet`, `opus`, `opusplan`, `sonnet[1m]`, and `opus[1m]`. `opusplan` uses Opus in plan mode and Sonnet in execution mode.

## Effort Controls

Claude Code supports `/effort low`, `/effort medium`, `/effort high`, `/effort xhigh`, `/effort max`, and `/effort auto`. It also supports `--effort <level>`, `CLAUDE_CODE_EFFORT_LEVEL=<level>`, and persistent `effortLevel` values of `low`, `medium`, `high`, or `xhigh`.

## Managed Settings

File-based Windows managed settings use:

```text
C:\Program Files\ClaudeCode\managed-settings.json
```

Server-managed settings require Claude for Teams or Enterprise and supported Claude Code versions. Server-managed settings are not available when routing through Bedrock, Vertex, Foundry, or a custom `ANTHROPIC_BASE_URL`.

## Hooks

Claude Code hooks can inspect tool events and return structured decisions. This plugin uses `PostToolUse` for `Bash` to summarize large noisy output conservatively. The hook never blocks commands and does not claim to replace returned tool output.

## Status Line

Claude Code status line commands receive JSON on stdin. This plugin reads model, effort, context window usage, cache-read input tokens, and rate-limit percentages from that JSON and prints one short line.

## Prompt Caching

Claude supports prompt caching. Cache reads cost less than base input tokens, and Claude Code already uses prompt caching and auto-compaction for interactive sessions. This plugin does not manually manage API `cache_control`.

## Cowork Limitations

Cowork plugins add skills and connectors. Verified Cowork documentation does not expose a plugin-controlled local settings mechanism equivalent to Claude Code `settings.json`; Cowork model guidance in this plugin is advisory.

## Do Not Use

- Do not use `DISABLE_NON_ESSENTIAL_MODEL_CALLS`.
- Do not claim `model` alone enforces a team policy.
- Do not claim `availableModels` removes the `Default` model picker option.
- Do not use `C:\ProgramData\ClaudeCode\managed-settings.json`.
- Do not promise hard model enforcement in Cowork from a plugin skill.
