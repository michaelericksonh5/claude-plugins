# token-saver Implementation Plan

## Goal

Build and publish a Claude plugin named `token-saver` that helps the team reduce Claude token usage and cost without making Claude less useful.

The plugin will support two environments:

1. Claude Code: enforce or install cost-aware settings, add a token-saving skill, add output-filtering hooks, and add a status line that makes model/context usage visible.
2. Claude Cowork / Claude Desktop: provide a plugin skill that teaches and guides model/context hygiene. Cowork plugins can add skills, connectors, and sub-agents, but the researched docs do not show a Cowork equivalent to Claude Code `settings.json` model enforcement.

This plan uses only verified documentation and avoids undocumented controls. In particular, do not use `DISABLE_NON_ESSENTIAL_MODEL_CALLS`; it is not a documented Claude Code variable. The documented nearby variable is `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, and that is for updater/telemetry/error reporting/feedback traffic, not reducing model-token calls.

## Verified Documentation

Use these sources during implementation and verification:

- Claude Code cost guide: https://docs.anthropic.com/en/docs/claude-code/costs
- Claude Code model configuration: https://code.claude.com/docs/en/model-config
- Claude Code settings: https://code.claude.com/docs/en/settings
- Claude Code environment variables: https://code.claude.com/docs/en/env-vars
- Claude Code server-managed settings: https://code.claude.com/docs/en/server-managed-settings
- Claude Code hooks reference: https://code.claude.com/docs/en/hooks
- Claude Code status line: https://code.claude.com/docs/en/statusline
- Claude Code plugins reference: https://code.claude.com/docs/en/plugins-reference
- Claude Code plugin marketplaces: https://code.claude.com/docs/en/plugin-marketplaces
- Claude prompt caching: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- Claude Cowork plugins: https://support.claude.com/en/articles/13837440-use-plugins-in-claude-cowork
- Claude Cowork organization plugins: https://support.claude.com/en/articles/13837433-manage-claude-cowork-plugins-for-your-organization
- Claude Team / Enterprise usage analytics: https://support.anthropic.com/en/articles/12883420-view-usage-analytics-for-team-and-enterprise-plans
- Claude Team / Enterprise extra usage and spend limits: https://support.anthropic.com/en/articles/12005970-manage-extra-usage-for-team-and-seat-based-enterprise-plans

## Confirmed Facts To Build Around

### Claude Code Model Controls

Claude Code supports these model controls:

- `model` in `settings.json`: initial/default model for Claude Code.
- `/model`: switches the current model during a session.
- `claude --model <model>`: starts a session with a model for that invocation.
- `ANTHROPIC_MODEL`: environment override for one session.
- `availableModels`: restricts selectable named models through `/model`, `--model`, and `ANTHROPIC_MODEL`.
- `availableModels` does not remove the `Default` option from the picker.
- To better control the `Default` option and aliases, combine `availableModels`, `model`, and `ANTHROPIC_DEFAULT_*_MODEL` environment variables.
- `opusplan` is a real Claude Code alias. It uses `opus` in plan mode and `sonnet` in execution mode.
- `haiku`, `sonnet`, `opus`, `sonnet[1m]`, and `opus[1m]` are real Claude Code aliases.
- `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` removes 1M variants from the picker.

### Claude Code Effort Controls

Claude Code supports these effort controls:

- `/effort low`
- `/effort medium`
- `/effort high`
- `/effort xhigh`
- `/effort max`
- `/effort auto`
- `--effort <level>` for a single launch.
- `CLAUDE_CODE_EFFORT_LEVEL=<level>` environment override.
- `effortLevel` in settings accepts persistent `low`, `medium`, `high`, or `xhigh`.
- `max` is session-only except when set through `CLAUDE_CODE_EFFORT_LEVEL`.

### Claude Code Managed Settings

Claude Code supports three central deployment options:

1. Server-managed settings from Claude.ai Admin Settings > Claude Code > Managed settings.
2. Endpoint-managed settings from MDM or OS policies.
3. System file-based managed settings.

Windows file-based managed settings path:

```text
C:\Program Files\ClaudeCode\managed-settings.json
```

Do not use the legacy Windows path:

```text
C:\ProgramData\ClaudeCode\managed-settings.json
```

It is no longer supported as of Claude Code v2.1.75.

Server-managed settings require Claude for Teams or Enterprise and Claude Code v2.1.38 or later for Teams, v2.1.30 or later for Enterprise.

Server-managed settings are not available when users route through Bedrock, Vertex, Foundry, or a custom `ANTHROPIC_BASE_URL`.

### Prompt Caching

Prompt caching is real, but the plugin should not manually manage API `cache_control` for Claude Code interactive sessions. Claude Code already uses prompt caching and auto-compaction.

API pricing facts:

- Cache reads cost 0.1x base input token price.
- 5-minute cache writes cost 1.25x base input token price.
- 1-hour cache writes cost 2x base input token price.
- Default cache TTL is 5 minutes.

For automation, prefer continuing or resuming sessions rather than repeatedly starting fresh and rediscovering context.

Claude Code session controls:

- `claude --continue`: continue the most recent session.
- `claude --resume`: choose a session.
- `claude --resume <session-id-or-name>`: resume a specific session.
- SDKs expose `session_id` and `resume`.

### Context Reduction Controls

Claude's official cost guide recommends:

- Use `/usage`.
- Use a status line showing context usage.
- Use `/clear` between unrelated tasks.
- Use `/rename` before clearing so sessions are findable.
- Use `/resume` to return to prior work.
- Use `/compact <instructions>` to control what compaction preserves.
- Keep `CLAUDE.md` short.
- Move specialized workflows out of `CLAUDE.md` and into skills.
- Disable unused MCP servers.
- Prefer CLI tools such as `gh` when available instead of MCP servers when that avoids tool definition overhead.
- Use code intelligence plugins for symbol navigation.
- Use hooks to filter huge logs/test output before Claude sees it.
- Use subagents for verbose operations so only summaries return to the main context.

### Claude Cowork / Desktop Constraints

Claude Cowork plugins are installed from Browse plugins or by uploading a custom plugin file. They add skills users can invoke with `/`.

Verified Cowork docs describe plugins as bundling skills, connectors, and sub-agents. They do not document a local `settings.json` equivalent for enforcing model selection in Cowork.

Therefore:

- The Cowork part of `token-saver` will be advisory and workflow-oriented.
- The Claude Code part can install or enforce actual model/context settings.
- Hard model restriction for the team should be done through Claude Code managed settings, endpoint-managed settings, or a self-serve settings installer, not through Cowork skill instructions.

## Target Repository

Project root:

```text
C:\Users\merickson\Documents\Claude_Plugins\token_saver
```

The folder currently exists and is empty.

## Final Project Layout

Create this exact layout:

```text
token_saver/
  .claude-plugin/
    plugin.json
  skills/
    token-saver/
      SKILL.md
      MODEL_ROUTING.md
      CONTEXT_HYGIENE.md
      AUTOMATION_GUIDE.md
      COWORK_GUIDE.md
  hooks/
    hooks.json
    filter-output.ps1
    filter-output.sh
  statusline/
    token-saver-statusline.ps1
    token-saver-statusline.sh
  settings/
    managed-settings.example.json
    user-settings.example.json
    strict-managed-settings.example.json
  scripts/
    install.ps1
    install.sh
    validate-package.ps1
  docs/
    TEAM_ROLLOUT.md
    CEO_SUMMARY.md
    VERIFIED_FACTS.md
    MARKETPLACE_PUBLISHING.md
  README.md
  .gitignore
```

Do not add MCP servers in the first version. This plugin can save tokens without adding MCP tool definitions or local server complexity.

Do not add a package manager or `package.json` unless a later implementation phase introduces Node-based scripts that cannot reasonably be written in PowerShell and POSIX shell.

## Phase 0: Documentation Lock

### What To Implement

Create `docs/VERIFIED_FACTS.md` summarizing only verified facts from the documentation links above.

This file must include:

- Confirmed Claude Code settings keys.
- Confirmed model aliases.
- Confirmed effort controls.
- Confirmed managed settings paths.
- Confirmed hook events and output format.
- Confirmed status line input fields.
- Confirmed Cowork limitations.
- Explicit "Do not use" section for undocumented or wrong claims.

### Required Content

Include these "Do not use" entries:

- Do not use `DISABLE_NON_ESSENTIAL_MODEL_CALLS`.
- Do not claim `model` alone enforces a team policy.
- Do not claim `availableModels` removes the `Default` model picker option.
- Do not use `C:\ProgramData\ClaudeCode\managed-settings.json`.
- Do not promise hard model enforcement in Cowork from a plugin skill.

### Verification

- Every fact in `docs/VERIFIED_FACTS.md` has a source URL.
- No entry says "TBD", "verify later", or "unknown".
- Search for bad variables:

```powershell
Select-String -Path .\docs\VERIFIED_FACTS.md -Pattern "DISABLE_NON_ESSENTIAL_MODEL_CALLS"
```

It should appear only in the "Do not use" warning.

## Phase 1: Plugin Scaffold

### What To Implement

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "token-saver",
  "version": "0.1.0",
  "description": "Reduce Claude token usage and cost with model-routing guidance, context hygiene, Claude Code settings examples, output-filtering hooks, and status-line visibility for model and context usage.",
  "author": {
    "name": "High 5 Games",
    "email": "michael.erickson@high5games.com"
  },
  "skills": [
    "./skills/token-saver"
  ],
  "hooks": "./hooks/hooks.json"
}
```

Create `README.md` with:

- What the plugin does.
- Difference between Claude Code and Cowork support.
- Quick install for Claude Code.
- Quick install for Cowork.
- Warning that settings enforcement is Claude Code only.
- Link to `docs/TEAM_ROLLOUT.md`.

Create `.gitignore`:

```gitignore
# Local environment
.env
.env.*

# Build artifacts
/dist/
*.zip
*.plugin

# OS/editor files
.DS_Store
Thumbs.db
.vscode/
.idea/
```

### Verification

Run from `C:\Users\merickson\Documents\Claude_Plugins\token_saver`:

```powershell
claude plugin validate .
```

Expected result:

```text
Validation passed
```

## Phase 2: Token-Saver Skill

### What To Implement

Create `skills/token-saver/SKILL.md`.

Frontmatter:

```yaml
---
name: token-saver
description: Reduce Claude token usage and cost by choosing the right model, limiting unnecessary context, using /clear and /compact deliberately, avoiding giant file/log reads, moving long instructions into skills, and applying Claude Code settings or managed settings where available. Use when a user asks about Claude costs, token limits, context window pressure, model choice, Opus/Sonnet/Haiku selection, Claude Code settings, Cowork plugin cost hygiene, prompt caching, or reducing repeated context.
---
```

The skill body must be concise and link to these deeper references:

- `MODEL_ROUTING.md`
- `CONTEXT_HYGIENE.md`
- `AUTOMATION_GUIDE.md`
- `COWORK_GUIDE.md`

The skill must instruct Claude to:

1. Start by checking the user's environment: Claude Code, Claude Desktop/Cowork, SDK automation, or API integration.
2. Recommend `haiku` for simple summarization, classification, small transforms, and cheap subagents.
3. Recommend `sonnet` for normal coding, debugging, and implementation.
4. Recommend `opusplan` for expensive planning where Opus reasoning is useful but Sonnet should execute.
5. Recommend `opus` only for hard architecture, ambiguous multi-system debugging, or high-risk reasoning where Sonnet has failed or is likely insufficient.
6. Recommend `/clear` when switching unrelated tasks.
7. Recommend `/compact` with explicit instructions before context becomes bloated.
8. Avoid reading large logs, generated files, lockfiles, and build outputs unless the task requires them.
9. Prefer targeted search and symbol/code-intelligence tools over broad file reads.
10. Use subagents for verbose exploration or log processing, returning only concise summaries to the main conversation.

### `MODEL_ROUTING.md`

Create a model routing table:

```text
Task type -> Default model
Simple summary/classification -> haiku
Routine coding/debugging -> sonnet
Multi-file implementation -> sonnet
Architectural planning -> opusplan
Deep ambiguous reasoning -> opus
Long-context emergency only -> sonnet[1m] or opus[1m] when explicitly approved
```

Also include:

- `opusplan` behavior: Opus in plan mode, Sonnet in execution mode.
- 1M context warning: do not make it default; use only for truly huge context.
- Effort guidance: default to `auto` or low/medium; raise only for complex tasks.

### `CONTEXT_HYGIENE.md`

Include exact rules:

- Keep `CLAUDE.md` under 200 lines where possible.
- Move specialized workflows to skills.
- Use `/clear` between unrelated tasks.
- Use `/rename` before clearing important sessions.
- Use `/resume` instead of re-explaining old context.
- Use `/compact Focus on decisions, changed files, tests, blockers, and next steps`.
- Do not paste giant logs. Save logs to files and ask Claude to extract only errors.
- Do not ask Claude to "read the whole repo" when a targeted file/symbol search will do.

### `AUTOMATION_GUIDE.md`

Include:

- Use `claude --continue` for the most recent session when running sequential automation in the same project.
- Use `claude --resume <session-id-or-name>` when continuing a known session.
- SDK automation should capture `session_id` from result messages and use `resume`.
- Keep `cwd` stable when resuming because session lookup is tied to project path.
- For CI or ephemeral hosts, either persist `~/.claude/projects/.../*.jsonl` at the same path or pass distilled state into a fresh prompt instead of relying on resume.

### `COWORK_GUIDE.md`

Include:

- Cowork plugins add skills and connectors.
- Cowork plugin skills can guide behavior but do not enforce Claude Code `settings.json`.
- For Cowork users, the skill should recommend starting fresh chats for unrelated tasks, using focused prompts, and choosing cheaper models from the UI when available.
- Team/Enterprise admins should use usage analytics and extra usage limits for Claude.ai/Cowork spend governance.

### Verification

Run:

```powershell
claude plugin validate .
```

Check skill length:

```powershell
(Get-Content .\skills\token-saver\SKILL.md).Count
```

Target: fewer than 250 lines for `SKILL.md`. Put detail in linked files to avoid loading too much skill content on every invocation.

## Phase 3: Claude Code Settings Examples

### What To Implement

Create `settings/user-settings.example.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "sonnet",
  "availableModels": ["sonnet", "haiku", "opusplan"],
  "effortLevel": "low",
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5-20251001",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-6",
    "CLAUDE_CODE_EFFORT_LEVEL": "auto",
    "CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"
  },
  "statusLine": {
    "type": "command",
    "command": "pwsh -NoProfile -ExecutionPolicy Bypass -File ~/.claude/token-saver-statusline.ps1"
  }
}
```

Create `settings/managed-settings.example.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "sonnet",
  "availableModels": ["sonnet", "haiku", "opusplan"],
  "effortLevel": "low",
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5-20251001",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-6",
    "CLAUDE_CODE_EFFORT_LEVEL": "auto",
    "CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"
  }
}
```

Create `settings/strict-managed-settings.example.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "sonnet",
  "availableModels": ["sonnet", "haiku"],
  "effortLevel": "low",
  "forceRemoteSettingsRefresh": true,
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5-20251001",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-6",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-sonnet-4-6",
    "CLAUDE_CODE_EFFORT_LEVEL": "auto",
    "CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"
  }
}
```

Strict mode intentionally maps the `opus` alias to Sonnet. Use it only if Tony/admins want cost enforcement stronger than the ability to run Opus.

### Important Notes

- In user/project settings, arrays merge across settings sources.
- For strict allowlists, use managed or policy settings.
- `availableModels` does not remove the `Default` option.
- The `env` block controls alias resolution and 1M picker visibility.
- `forceRemoteSettingsRefresh` is managed-only and should not be used in user settings.

### Verification

Validate JSON:

```powershell
Get-Content .\settings\user-settings.example.json -Raw | ConvertFrom-Json | Out-Null
Get-Content .\settings\managed-settings.example.json -Raw | ConvertFrom-Json | Out-Null
Get-Content .\settings\strict-managed-settings.example.json -Raw | ConvertFrom-Json | Out-Null
```

Search for undocumented variable:

```powershell
Select-String -Path .\settings\*.json -Pattern "DISABLE_NON_ESSENTIAL_MODEL_CALLS"
```

Expected: no matches.

## Phase 4: Self-Serve Installers

### What To Implement

Create `scripts/install.ps1`.

Behavior:

1. Set `$ErrorActionPreference = 'Stop'`.
2. Resolve plugin root from `$PSScriptRoot`.
3. Create `%USERPROFILE%\.claude` if missing.
4. Read existing `%USERPROFILE%\.claude\settings.json` if present.
5. Backup existing settings to `%USERPROFILE%\.claude\settings.token-saver-backup.<yyyyMMdd-HHmmss>.json`.
6. Deep-merge the token-saver recommended keys:
   - `model`
   - `availableModels`
   - `effortLevel`
   - `env`
   - `statusLine`
   - `hooks`
7. Preserve unrelated existing settings.
8. Copy `statusline/token-saver-statusline.ps1` to `%USERPROFILE%\.claude\token-saver-statusline.ps1`.
9. Copy `hooks/filter-output.ps1` to `%USERPROFILE%\.claude\hooks\token-saver-filter-output.ps1`.
10. Print a summary of changed keys.
11. Tell the user to restart Claude Code.

Create `scripts/install.sh`.

Behavior:

1. Use `set -euo pipefail`.
2. Resolve plugin root from script path.
3. Create `$HOME/.claude`.
4. Backup `$HOME/.claude/settings.json` to `$HOME/.claude/settings.token-saver-backup.<yyyyMMdd-HHmmss>.json`.
5. Require `jq`; if missing, print installation instructions and exit nonzero.
6. Deep-merge recommended settings with existing settings.
7. Copy `statusline/token-saver-statusline.sh` to `$HOME/.claude/token-saver-statusline.sh`.
8. Copy `hooks/filter-output.sh` to `$HOME/.claude/hooks/token-saver-filter-output.sh`.
9. `chmod +x` copied scripts.
10. Print a summary and restart instruction.

### Guardrails

- Do not overwrite the whole settings file.
- Do not remove user settings.
- Do not write managed settings from the self-serve installer.
- Do not require admin permissions.
- Do not store API keys.

### Verification

On Windows test with a temporary home directory:

```powershell
$tmpHome = Join-Path $env:TEMP ("token-saver-home-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tmpHome | Out-Null
$oldHome = $env:USERPROFILE
$env:USERPROFILE = $tmpHome
try {
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
  Get-Content (Join-Path $tmpHome ".claude\settings.json") -Raw | ConvertFrom-Json | Out-Null
} finally {
  $env:USERPROFILE = $oldHome
  Remove-Item -LiteralPath $tmpHome -Recurse -Force
}
```

## Phase 5: Output-Filtering Hooks

### What To Implement

Create `hooks/hooks.json`:

```json
{
  "PostToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
            "command": "node",
            "args": [
              "${CLAUDE_PLUGIN_ROOT}/scripts/lib/hook.js"
            ],
          "timeout": 10
        }
      ]
    }
  ]
}
```

Create `hooks/filter-output.ps1`.

The bundled plugin hook should call the shared Node.js helper directly so it works on Windows and macOS/Linux without requiring PowerShell on non-Windows machines. Keep the PowerShell and shell wrappers for self-serve user-settings installs.

Behavior:

1. Read hook JSON from stdin.
2. Only act when the tool output is larger than 12,000 characters.
3. If the command resembles a test/log command, extract lines matching:
   - `FAIL`
   - `FAILED`
   - `ERROR`
   - `Error:`
   - `Exception`
   - `Traceback`
   - `Assertion`
   - `panic:`
4. Return a concise JSON hook output that tells Claude to focus on the extracted failures.
5. If the hook output format cannot safely rewrite the tool result, print a concise warning to stdout rather than blocking the command.
6. Exit 0 on non-matching commands.

Create `hooks/filter-output.sh` with equivalent behavior for macOS/Linux.

### Hook Design Constraint

The Claude Code hooks docs prove hooks can inspect tool events and return structured decisions. They do not guarantee that every hook event can rewrite all previously returned tool output. Therefore, implement this phase conservatively:

- Use hooks to warn and summarize when safe.
- Do not block developer commands.
- Do not pretend filtered output replaced the full output unless verified in a real Claude Code session.

If PostToolUse cannot rewrite output as desired, keep the hook as a warning and add a `PreToolUse` command-rewrite hook in a later version for known commands such as `npm test`, `pytest`, and `go test`.

### Verification

Run script unit tests with mock hook JSON:

```powershell
@'
{
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" },
  "tool_response": { "output": "line1`nFAIL test example`nError: expected true`nline4" }
}
'@ | pwsh -NoProfile -ExecutionPolicy Bypass -File .\hooks\filter-output.ps1
```

Run:

```powershell
claude plugin validate .
```

Then verify manually in Claude Code with a command that emits more than 12,000 characters.

## Phase 6: Status Line

### What To Implement

Create `statusline/token-saver-statusline.ps1`.

Behavior:

1. Read JSON from stdin.
2. Extract:
   - `.model.display_name`
   - `.model.id`
   - `.effort.level`
   - `.context_window.used_percentage`
   - `.context_window.context_window_size`
   - `.context_window.current_usage.cache_read_input_tokens`
   - `.rate_limits.five_hour.used_percentage`
   - `.rate_limits.seven_day.used_percentage`
3. Print one short line.
4. Color context usage:
   - green under 50 percent
   - yellow from 50 to 74 percent
   - red at 75 percent or higher
5. Warn when the active model contains `opus` and not `opusplan`.
6. Warn when context window size is `1000000`.
7. Do not perform network calls.
8. Exit within 2 seconds.

Create `statusline/token-saver-statusline.sh` with equivalent behavior.

Recommended output shape:

```text
model: Sonnet | effort: auto | ctx: 34% | cache read: 8200 | 5h: 41%
```

If Opus:

```text
model: Opus | effort: xhigh | ctx: 34% | cost alert: Opus active
```

If 1M context:

```text
model: Sonnet 1M | ctx: 12% of 1M | cost alert: long context active
```

### Settings

Installers should add this to user settings on Windows:

```json
{
  "statusLine": {
    "type": "command",
    "command": "pwsh -NoProfile -ExecutionPolicy Bypass -File ~/.claude/token-saver-statusline.ps1"
  }
}
```

Installers should add this to user settings on macOS/Linux:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/token-saver-statusline.sh"
  }
}
```

### Verification

PowerShell mock:

```powershell
@'
{
  "model": { "id": "claude-sonnet-4-6", "display_name": "Claude Sonnet 4.6" },
  "effort": { "level": "auto" },
  "context_window": {
    "used_percentage": 34,
    "context_window_size": 200000,
    "current_usage": { "cache_read_input_tokens": 8200 }
  },
  "rate_limits": {
    "five_hour": { "used_percentage": 41 }
  }
}
'@ | pwsh -NoProfile -ExecutionPolicy Bypass -File .\statusline\token-saver-statusline.ps1
```

Expected output contains:

```text
Sonnet
ctx: 34%
```

## Phase 7: Team Rollout Docs

### `docs/TEAM_ROLLOUT.md`

Write a team rollout guide with these sections:

1. Executive summary for Tony.
2. Claude Code rollout options.
3. Claude Cowork rollout options.
4. Recommended default settings.
5. Strict settings option.
6. Self-serve install steps.
7. Admin-managed settings steps.
8. How to verify a user's model/settings.
9. How to monitor costs.
10. What users should do daily.

Exact recommendation:

- Default model: `sonnet`.
- Available named models: `sonnet`, `haiku`, `opusplan`.
- Default effort: `low` in settings plus `CLAUDE_CODE_EFFORT_LEVEL=auto` for adaptive behavior.
- Disable 1M context by default with `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`.
- Use Opus only through `opusplan` unless a senior user intentionally enables `opus`.

### `docs/CEO_SUMMARY.md`

Write a one-page summary:

- Problem: spend rises when users use Opus/default long-context behavior for routine tasks and let contexts bloat.
- Solution: Sonnet default, Haiku for simple tasks, Opus/OpusPlan for planning only, status visibility, hooks, skills, and managed settings.
- Expected impact: fewer accidental Opus sessions, fewer repeated large-context turns, better cache-friendly/resume-friendly workflows.
- Limits: Claude Cowork model enforcement is not exposed like Claude Code settings; use skills and admin analytics there.

### `docs/MARKETPLACE_PUBLISHING.md`

Include:

- Plugin validation command.
- ZIP packaging command.
- No nested ZIP rule learned from `slot-art-creator-node`.
- Version bump requirement.
- Marketplace repo update steps.

Include a packaging verification command:

```powershell
$zipPath = ".\dist\token-saver.zip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zipPath))
try {
  $nested = @($zip.Entries | Where-Object { $_.FullName -match '\.(zip|plugin)$' })
  if ($nested.Count -gt 0) { throw "Nested archives found: $($nested.FullName -join ', ')" }
} finally {
  $zip.Dispose()
}
```

### Verification

Read the docs as a new user and confirm:

- No undocumented settings.
- No placeholder text.
- No unverified claims about Cowork model enforcement.
- Every command is executable on the target platform or clearly marked Windows/macOS/Linux.

## Phase 8: Marketplace-Ready Packaging

### What To Implement

Create `scripts/validate-package.ps1`.

Behavior:

1. Run `claude plugin validate .`.
2. Ensure `.claude-plugin/plugin.json` version exists.
3. Ensure no `*.zip` or `*.plugin` exists outside `/dist/`.
4. Create `/dist/token-saver.zip`.
5. Stage only required plugin files:
   - `.claude-plugin`
   - `skills`
   - `hooks`
   - `statusline`
   - `settings`
   - `scripts`
   - `docs`
   - `README.md`
6. Exclude:
   - `.git`
   - `dist`
   - `.env`
   - `.env.*`
   - `node_modules`
   - `*.zip`
   - `*.plugin`
7. Verify the ZIP contains:
   - `.claude-plugin/plugin.json`
   - `skills/token-saver/SKILL.md`
   - `hooks/hooks.json`
   - `settings/managed-settings.example.json`
8. Verify the ZIP contains no nested `.zip` or `.plugin`.

### Verification

Run:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
```

Expected output:

```text
Plugin validation passed.
Package created: dist/token-saver.zip
Nested archive count: 0
Required files present: true
```

## Phase 9: Marketplace Publication

### What To Implement

When local validation passes, add this plugin to the GitHub marketplace repository:

```text
https://github.com/michaelericksonh5/claude-plugins
```

Add a marketplace entry:

```json
{
  "name": "token-saver",
  "description": "Reduce Claude token usage and cost with model-routing guidance, context hygiene, Claude Code settings examples, output-filtering hooks, and status-line visibility for model and context usage.",
  "version": "0.1.0",
  "author": {
    "name": "High 5 Games",
    "email": "michael.erickson@high5games.com"
  },
  "source": "./plugins/token-saver",
  "homepage": "https://github.com/michaelericksonh5/token_saver",
  "repository": "https://github.com/michaelericksonh5/token_saver",
  "license": "MIT",
  "category": "developer-tools",
  "tags": ["cost-control", "tokens", "claude-code", "cowork", "model-routing", "context-management"]
}
```

Copy the plugin folder to:

```text
claude-plugins/plugins/token-saver
```

Do not copy `/dist/`.

### Verification

In the marketplace clone:

```powershell
claude plugin validate .\plugins\token-saver
```

Scan for nested archives:

```powershell
Get-ChildItem -LiteralPath .\plugins\token-saver -Recurse -Force -File |
  Where-Object { $_.Extension -in ".zip", ".plugin" }
```

Expected: no output.

After pushing, fetch live GitHub tree and confirm no `.zip` or `.plugin` entries under `plugins/token-saver`.

## Phase 10: Pilot Rollout

### Pilot Group

Start with these user categories:

1. Heavy Claude Code coding users.
2. Cowork-only users.
3. Automation/CLI script users.

### Baseline

Before installing:

- Ask users to run `/usage` in active Claude Code sessions.
- Export Team/Enterprise usage analytics if available.
- Record which model they normally use.
- Record whether they use Cowork, Claude Code, CLI automation, or all three.

### Install

Claude Code self-serve:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

Claude Code admin managed:

- Paste `settings/managed-settings.example.json` into Admin Settings > Claude Code > Managed settings.
- Restart Claude Code.
- Run `/status` to confirm managed settings source.

Cowork:

- Install `token-saver` from the marketplace.
- Invoke `/token-saver`.
- Use `COWORK_GUIDE.md` behavior.

### Success Metrics

Measure after one week:

- Fewer Opus sessions for routine coding.
- More sessions using Sonnet/Haiku.
- Fewer context-limit interruptions.
- Fewer repeated "read entire repo" behaviors.
- Lower average spend per active user day.
- Users can explain when to use `haiku`, `sonnet`, `opusplan`, and `opus`.

## Phase 11: Hardening

Only after the pilot:

1. Decide whether `opus` should be absent from `availableModels`.
2. Decide whether strict managed settings should map `ANTHROPIC_DEFAULT_OPUS_MODEL` to `claude-sonnet-4-6`.
3. Decide whether `CLAUDE_CODE_DISABLE_THINKING=1` is acceptable for any groups.
4. Decide whether to disable background agents with `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` for users who do not need them.
5. Add language-specific code intelligence plugin recommendations per repo.
6. Add project-specific "move CLAUDE.md content into skills" migration plans.

Do not apply strict settings before the pilot. Strict settings can reduce spend, but they may also reduce usefulness if applied without measuring user workflows.

## Final Acceptance Criteria

The work is complete when:

1. `C:\Users\merickson\Documents\Claude_Plugins\token_saver` is a valid Claude plugin.
2. `claude plugin validate .` passes.
3. `scripts/validate-package.ps1` creates `dist/token-saver.zip`.
4. The ZIP has zero nested `.zip` or `.plugin` files.
5. `/token-saver` appears after installation.
6. The skill gives different guidance for Claude Code, Cowork, and automation.
7. Windows installer safely merges `%USERPROFILE%\.claude\settings.json` and creates a backup.
8. macOS/Linux installer safely merges `$HOME/.claude/settings.json` and creates a backup.
9. Status line displays active model and context usage.
10. Hook scripts run against mock inputs.
11. `docs/TEAM_ROLLOUT.md` is complete enough for Tony/admins to deploy without asking engineering for missing steps.
12. Marketplace copy contains no `dist/`, `.zip`, or `.plugin` artifacts.

## Recommended Execution Order

1. Phase 0: Documentation lock.
2. Phase 1: Plugin scaffold.
3. Phase 2: Token-saver skill and references.
4. Phase 3: Settings examples.
5. Phase 6: Status line.
6. Phase 4: Installers.
7. Phase 5: Hooks.
8. Phase 7: Rollout docs.
9. Phase 8: Packaging.
10. Phase 9: Marketplace publication.
11. Phase 10: Pilot.
12. Phase 11: Hardening.

This order ships the safest useful product first: guidance and settings examples, then local automation, then output filtering, then marketplace publication.
