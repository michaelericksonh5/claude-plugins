# token-saver

`token-saver` is a Claude plugin for reducing avoidable Claude token usage and cost. It provides a model-routing skill, context-hygiene guidance, Claude Code settings examples, conservative output-filtering hooks, and a status line that makes model and context usage visible.

## What It Does

- Adds `/token-saver`, a skill for choosing Haiku/Sonnet/Opus/OpusPlan deliberately.
- Provides Claude Code settings examples for cost-aware defaults.
- Installs a status line that shows active model, effort, context usage, cache reads, and rate-limit usage when available.
- Installs a conservative output hook that summarizes very large test/log output without blocking commands.
- Includes rollout docs for self-serve users and Claude Team/Enterprise admins.

## Support Matrix

| Environment | Supported | What token-saver can do |
| --- | --- | --- |
| Claude Code | Yes | Install user settings, hook scripts, and status line; validate and package the plugin; support managed settings examples for admins. |
| Claude Cowork / Claude Desktop | Yes, advisory | Add the `/token-saver` skill for model/context hygiene guidance. Verified Cowork plugin docs do not expose hard model enforcement through plugin settings. |
| Claude Code managed settings | Yes | Provide JSON examples for server-managed or endpoint-managed settings. Admins deploy these through Claude.ai Admin Settings, MDM, registry, or system files. |

## Requirements

- Claude Code for local settings, hooks, status line, validation, and packaging.
- Node.js 20 LTS or newer for installer/tooling helpers.
- PowerShell 7 on Windows for Windows wrappers.
- A POSIX shell on macOS/Linux for Unix wrappers.

No Python is required or used.

## Model Strategy

The recommended team default is:

- `sonnet` for normal coding and debugging.
- `haiku` for simple summaries, classification, small transforms, and cheap subagents.
- `opusplan` for planning-heavy work where Opus reasoning is useful but Sonnet should execute.
- `opus` only for hard architecture or ambiguous reasoning where Sonnet is not enough.

The settings examples disable 1M context by default with `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`. Long-context models should be an intentional choice, not a default.

## Quick Install: Claude Code

From the plugin root:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

On macOS/Linux:

```sh
./scripts/install.sh
```

The installer deep-merges recommended user settings into `~/.claude/settings.json`, creates a timestamped backup when settings already exist, preserves unrelated settings, and copies the hook/status-line scripts. Restart Claude Code after installation.

The installer preserves existing hooks and appends token-saver's hook only when it is not already present. It does not store API keys or write `.env` files.

## Quick Install: Cowork

Upload or install the plugin through Browse plugins or your organization's plugin flow, then invoke:

```text
/token-saver
```

Cowork users should treat the skill as workflow guidance. For spend governance in Claude.ai/Cowork, use Team or Enterprise usage analytics and extra usage limits.

## Managed Settings

For Claude Team/Enterprise admins, start with:

- `settings/managed-settings.example.json` for a balanced rollout.
- `settings/strict-managed-settings.example.json` only if you intentionally want stronger Opus restriction.

Server-managed settings are configured in Claude.ai under Admin Settings > Claude Code > Managed settings. Endpoint-managed settings can also be deployed through MDM, Windows registry policy, or `C:\Program Files\ClaudeCode\managed-settings.json`.

Do not use the legacy `C:\ProgramData\ClaudeCode\managed-settings.json` path.

## Safety

- Existing `~/.claude/settings.json` is backed up before self-serve install.
- Existing settings are preserved unless token-saver intentionally sets the same key.
- Existing hook arrays are preserved; token-saver's hook is appended idempotently.
- Hook scripts never block commands.
- Packaging excludes `.env`, `.env.*`, `.git`, `node_modules`, `dist`, and nested `.zip` / `.plugin` artifacts.

## Validation

```powershell
claude plugin validate .
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
```

Expected package validation output includes:

```text
Plugin validation passed.
Package created: dist\token-saver.zip
Nested archive count: 0
Required files present: true
```

## Documentation

- `docs/TEAM_ROLLOUT.md`: rollout steps, admin-managed settings, pilot guidance.
- `docs/CEO_SUMMARY.md`: short leadership-facing summary.
- `docs/VERIFIED_FACTS.md`: researched Claude Code/Cowork facts and anti-patterns.
- `docs/MARKETPLACE_PUBLISHING.md`: publish checklist and archive validation.

## Troubleshooting

If `/token-saver` does not appear, run:

```powershell
claude plugin validate .
```

If the status line does not appear in Claude Code, restart Claude Code and check `~/.claude/settings.json` for the `statusLine` entry.

If a hook behaves unexpectedly, remove token-saver's hook from `~/.claude/settings.json` and restore the timestamped backup created by the installer.
