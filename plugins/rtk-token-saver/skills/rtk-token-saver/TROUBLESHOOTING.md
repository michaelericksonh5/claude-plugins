# Troubleshooting

## RTK Is Not Found

Claude Code plugin hooks attempt to install approved RTK `0.40.0` automatically on `SessionStart`. If the hook reports that setup failed open, normal commands still run unchanged.

Run:

```powershell
rtk --version
```

If the command is missing, install RTK from the reviewed upstream release or run this wrapper's setup script, then ensure it is on `PATH`.

## Noisy Command Was Not Wrapped

The `PreToolUse` hook only wraps selected simple noisy Bash prefixes. It intentionally skips commands that are already wrapped, chained with `&&` or `||`, piped, redirected, multiline, or outside the selected prefixes. This keeps the hook conservative and fail-open.

## Shell Output Looks Too Short

RTK may have compacted command output. Ask for the full RTK log path or rerun the command with output redirected to a file when exact details matter.

## Assistant Replies Look Too Short

Compact TLDR mode is automatic in Claude Code when this plugin is enabled. It shortens generated assistant replies and future transcript size; it does not filter shell output or replace `/compact`. Ask for full detail when you need rationale, exact reproduction steps, or safety context.

## Hooks Conflict

Check `~/.claude/settings.json` for global `PreToolUse` hooks that also rewrite Bash commands, and check whether the plugin hook is enabled. Do not run legacy H5G `token-saver` filtering and RTK filtering at the same time unless hook ordering has been tested.

## Cowork/Desktop

This plugin can teach RTK/model/context/compact-output practices in Cowork/Desktop, but RTK's shell-command filtering is a Claude Code or local developer-machine workflow. Compact-output behavior in Desktop/Cowork is advisory skill guidance unless that client supports and applies the shipped Claude Code output style. Do not claim Cowork/Desktop chat gets RTK hook enforcement from this plugin alone.
