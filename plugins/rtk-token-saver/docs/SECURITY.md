# Security Notes

RTK has a high-privilege surface because it integrates with shell-command execution and Claude Code hooks.

## H5G Wrapper Policy

- This wrapper does not run remote install scripts.
- This wrapper does not vendor RTK binaries.
- `scripts/setup.* --install-rtk` and the plugin `SessionStart` hook use the same pinned RTK `v0.40.0` installer, verify SHA-256, and install only `rtk` / `rtk.exe` into a user-local bin directory.
- This wrapper does not auto-modify Claude settings during marketplace install.
- Compact TLDR output is shipped as a forced Claude Code output style, not as a shell-output hook.
- This wrapper adds fail-open `SessionStart` and `PreToolUse` plugin hooks. `SessionStart` checks or installs pinned RTK and writes status under `CLAUDE_PLUGIN_DATA`; `PreToolUse` only rewrites selected simple Bash commands to `rtk <command>`.
- The `PreToolUse` hook skips commands that are already RTK-wrapped, chained, piped, redirected, or outside the selected noisy prefixes.
- `scripts/setup.*` only applies RTK initialization when users pass `--apply` or `-Apply`.
- Setup can migrate legacy token-saver hooks with `--migrate-token-saver` / `-MigrateTokenSaver`, backing up settings before removing only known H5G token-saver hook commands.
- Setup blocks on remaining legacy token-saver hooks, non-approved RTK versions, or RTK binaries outside the approved user-local install directory unless users pass `--force` / `-Force` after manual review.
- Other non-RTK `PreToolUse` hooks are warnings, not blockers.
- Users should install approved RTK `0.40.0` through this wrapper, the plugin hook, or another reviewed user-local process.

## Review Before Broad Rollout

- Confirm RTK license terms for RTK `0.40.0`.
- Confirm telemetry defaults and disable telemetry unless explicitly approved.
- Confirm local tracking database contents are acceptable for H5G machines.
- Confirm RTK does not hide critical diagnostic output for H5G workflows.
- Confirm legacy token-saver hooks were migrated before RTK hook rollout.
- Review any other `PreToolUse` hooks if hook ordering causes odd behavior.
- Confirm Compact TLDR mode still expands for destructive commands, secrets, auth failures, production data, exact error reproduction, and security review.
- Confirm Desktop/Cowork rollout language stays advisory unless that surface honors Claude Code hooks and output styles.
