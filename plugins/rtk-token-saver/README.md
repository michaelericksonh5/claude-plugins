# rtk-token-saver

`rtk-token-saver` is an H5G Claude Code plugin wrapper for [RTK](https://github.com/rtk-ai/rtk). When the plugin is enabled in Claude Code, Compact TLDR replies are forced, approved RTK `0.40.0` is checked or installed when needed, and selected noisy Bash commands are wrapped with RTK automatically.

This is **not a fork** of RTK. Fork only if H5G needs code changes in RTK itself.

## What This Plugin Adds

- `/rtk-token-saver` skill for RTK usage, compact TLDR replies, model routing, and context hygiene.
- Forced Claude Code `Compact TLDR` output style for professional TLDR-first replies.
- Plugin hooks that check or install pinned RTK into a user-local bin directory and wrap selected noisy Bash commands with RTK.
- Setup scripts that can still install pinned RTK into a user-local bin directory and run RTK's Claude Code initialization after explicit opt-in.
- Doctor scripts that check RTK install state, Claude Code hooks, and legacy token-saver conflicts.
- H5G rollout docs for replacing the old `token-saver` marketplace entry.

## What RTK Adds

RTK can reduce noisy shell-output input/context tokens in Claude Code from test runs, package managers, Git/GitHub commands, Docker/Kubernetes output, logs, and other verbose command results. This plugin wraps conservative command prefixes such as `npm test`, `pytest`, `cargo test`, `go test`, selected `git` inspection commands, `docker` diagnostics, and `kubectl` diagnostics. Commands that are already wrapped, chained, piped, redirected, or otherwise unsafe to rewrite run unchanged.

## Compact TLDR Mode

Compact TLDR mode is separate from RTK. RTK filters shell-output input/context tokens in Claude Code; compact replies reduce generated assistant output tokens and the amount of response text carried into future transcript context.

The plugin ships:

- `skills/rtk-token-saver/COMPACT_OUTPUT.md` with professional TLDR rules, templates, and safety escape hatches.
- `output-styles/compact-tldr.md`, a forced Claude Code output style applied when the plugin is enabled.

Compact TLDR mode is not the RTK shell hook and does not replace `/compact`. `/compact` summarizes existing conversation context; compact replies keep new replies shorter. In Claude Desktop/Cowork, the skill can advise compact behavior, but enforcement depends on that client's support for plugin output styles or user instructions.

## Install From Marketplace

```text
/plugin marketplace add michaelericksonh5/claude-plugins
/plugin install rtk-token-saver@h5g-plugins
```

Claude Code will load the forced Compact TLDR output style and bundled hooks when the plugin is enabled. You can still invoke the skill for guidance:

```text
/rtk-token-saver
```

## RTK Setup

Clone this wrapper repo when you want to run setup or doctor scripts:

```powershell
git clone https://github.com/michaelericksonh5/rtk-token-saver
cd rtk-token-saver
```

Marketplace install gives Claude Code the `/rtk-token-saver` skill, forced Compact TLDR style, and fail-open hooks. On `SessionStart`, the hook checks for approved RTK and attempts the existing checksum-verified installer if RTK is missing or the wrong version. If `CLAUDE_ENV_FILE` is present, the hook writes RTK/PATH status for Claude Code to pick up. Hook state is stored under `CLAUDE_PLUGIN_DATA`.

The setup scripts remain available from a checked-out repo for users who want to review or preinstall RTK manually before plugin use.

To install approved RTK `0.40.0` into a user-local bin directory and update user PATH where possible:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -InstallRtk
```

Then run a dry check:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Apply RTK's Claude Code initialization only when ready:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -Apply
```

Recommended one-command setup for most users:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -InstallRtk -MigrateTokenSaver -Apply
```

`-MigrateTokenSaver` backs up `~/.claude/settings.json` and removes only known H5G legacy token-saver hook commands. Other `PreToolUse` hooks are reported as warnings so users can review hook ordering without being blocked.

`-Apply` refuses to run when legacy `token-saver` hooks are still present, or when RTK is missing, the wrong version, or outside the approved user-local path. Use `-Force` only after manual review:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -Apply -Force
```

On macOS/Linux:

```sh
./scripts/setup.sh
./scripts/setup.sh --install-rtk
./scripts/setup.sh --apply
./scripts/setup.sh --install-rtk --migrate-token-saver --apply
./scripts/setup.sh --apply --force
```

The installer downloads RTK `v0.40.0` from GitHub Releases, verifies a pinned SHA-256 digest, installs only `rtk` / `rtk.exe` into `~/.local/bin`, and updates user PATH where possible. It does not require admin privileges when using the default user-local location. The plugin hooks reuse this installer; they do not add unpinned downloads, remote pipe-to-shell, or vendored binaries.

## Doctor

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
```

The doctor checks:

- RTK is on `PATH`.
- RTK resolves to the reviewed binary path and approved version.
- RTK resolves from the approved user-local install directory.
- Claude Code CLI is installed.
- `~/.claude/settings.json` exists.
- RTK `PreToolUse` integration is available through global settings or the plugin hook.
- Legacy H5G `token-saver` hooks are absent.
- Other non-RTK `PreToolUse` hooks are absent or reviewed.
- This wrapper has bundled fail-open plugin hooks configured.

## Replacing token-saver

The old `token_saver` repo remains available for rollback or reuse. The H5G marketplace now lists `rtk-token-saver` instead of `token-saver`.

Do not run legacy `token-saver` filtering and RTK filtering together unless hook ordering has been tested.

For existing `token-saver` users:

1. Run `scripts/setup.ps1 -InstallRtk -MigrateTokenSaver -Apply`.
2. Restart Claude Code.
3. Remove `~/.claude/token-saver/` only after confirming no other workflow depends on it.

## Validation

```powershell
npm test
claude plugin validate .
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
```

## Caveats

- The plugin hook wraps only selected simple Bash commands and fails open.
- RTK proxies shell commands, so this wrapper installs only pinned RTK `0.40.0` with checksum verification.
- Compact TLDR output is forced in Claude Code by this plugin and should expand when safety, exact errors, or user requests require detail.
- Cowork/Desktop users get guidance only unless that surface honors Claude Code plugin hooks and output styles.
- Full command output may still exist in RTK's local logs when RTK preserves raw output.
