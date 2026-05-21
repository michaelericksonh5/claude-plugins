# Team Rollout

## Recommendation

The marketplace now lists `rtk-token-saver` instead of H5G `token-saver`. Keep the original `token_saver` GitHub repo intact for rollback and future reuse.

Do not fork RTK unless H5G needs code-level changes. Start with this wrapper plus approved RTK `0.40.0`, forced Compact TLDR output style, and fail-open plugin hooks.

## Pilot Steps

1. Pick one developer machine.
2. Install the `rtk-token-saver` plugin from the H5G marketplace.
3. Restart Claude Code and confirm the `SessionStart` hook reports RTK status.
4. Clone `https://github.com/michaelericksonh5/rtk-token-saver` if you want to run setup and doctor scripts manually.
5. Optionally run `scripts/setup.ps1 -InstallRtk -MigrateTokenSaver -Apply` for preflight/global RTK setup.
6. Run `scripts/doctor.ps1`.
7. Review any non-RTK `PreToolUse` hook warnings if behavior looks odd.
8. Run normal H5G workflows: slot art, Spine animation, AI video, skill auditing, and regular coding/test loops.
9. Confirm RTK reduces noisy output without hiding critical failures.
10. Confirm Compact TLDR replies are automatic in Claude Code without losing safety, exact errors, or verification status.

## Compact TLDR Rollout

Compact TLDR mode is a response-style feature, not the RTK shell wrapper. It is forced by the plugin in Claude Code.

- RTK can reduce shell-output input/context tokens in Claude Code.
- Compact replies reduce generated assistant output tokens and future transcript size.
- `/compact` remains the tool for summarizing existing conversation context.
- Desktop/Cowork compact behavior is advisory skill guidance unless the client honors the shipped Claude Code output style or equivalent user settings.

Keep escape hatches explicit: users should ask for full detail whenever debugging, security review, production operations, or exact reproduction steps need more context.

## Existing token-saver Cleanup

Removing `token-saver` from the marketplace does not uninstall existing local settings. For each pilot user who previously ran the old installer:

1. Run `scripts/setup.ps1 -MigrateTokenSaver`.
2. Confirm it created a `settings.rtk-token-saver-backup.*.json` backup.
3. Keep unrelated hooks unless they also rewrite Bash command input and cause visible conflicts with RTK.
4. Remove `~/.claude/token-saver/` only after confirming the old plugin is no longer needed.

## Marketplace Change

- `token-saver` has been removed from `claude-plugins/.claude-plugin/marketplace.json`.
- `rtk-token-saver` has been added.
- Leave `michaelericksonh5/token_saver` untouched.

## Rollback

If RTK causes conflicts, disable or uninstall the `rtk-token-saver` plugin to remove the plugin hooks. If you also ran global setup, remove the RTK hook from `~/.claude/settings.json` or restore RTK's settings backup. Then reinstall or re-add the old `token-saver` marketplace entry if needed.

## Admin Notes

RTK is a local CLI/hook engine. Team-wide rollout should use approved RTK `0.40.0`, installed through this wrapper's checksum-verified user-local installer, the plugin `SessionStart` hook, or another internally reviewed process.

The plugin hooks are fail-open. `SessionStart` checks or installs RTK and writes state under `CLAUDE_PLUGIN_DATA`; `PreToolUse` wraps only selected simple Bash commands and skips already wrapped, chained, piped, or redirected commands.
