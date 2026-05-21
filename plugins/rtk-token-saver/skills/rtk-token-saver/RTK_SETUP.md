# RTK Setup

RTK is the engine. This H5G plugin checks or installs pinned RTK for Claude Code, wraps selected noisy Bash commands when RTK is available, and does not vendor or fork RTK.

Upstream repo: https://github.com/rtk-ai/rtk

## Recommended Rollout

1. Pilot on one developer machine.
2. Install the plugin and restart Claude Code so the `SessionStart` hook can check or install pinned RTK.
3. Clone `https://github.com/michaelericksonh5/rtk-token-saver` if setup scripts should be reviewed or run manually.
4. Optionally run `scripts/setup.ps1 -InstallRtk -MigrateTokenSaver -Apply` or `./scripts/setup.sh --install-rtk --migrate-token-saver --apply` for global RTK setup.
5. Run the doctor script.
6. Review any non-RTK `PreToolUse` hook warnings if behavior looks odd.
7. Confirm regular H5G workflows still show enough diagnostic output.

## Claude Code Setup

With the plugin enabled in Claude Code, Compact TLDR is automatic. The `SessionStart` hook checks for RTK `0.40.0`, attempts the existing checksum-verified installer when RTK is missing or wrong, writes state under `CLAUDE_PLUGIN_DATA`, and writes PATH/status information when `CLAUDE_ENV_FILE` is present. The `PreToolUse` hook wraps selected simple noisy Bash commands as `rtk <command>` and skips unsafe/chained commands. Hooks fail open.

Manual setup remains available when a user wants to preinstall or inspect RTK.

To install RTK `0.40.0` into a user-local bin directory and update user PATH where possible:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -InstallRtk
```

On macOS/Linux:

```sh
./scripts/setup.sh --install-rtk
```

Then run a dry check:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Then apply:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -Apply
```

Recommended one-command setup:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -InstallRtk -MigrateTokenSaver -Apply
```

On macOS/Linux:

```sh
./scripts/setup.sh
./scripts/setup.sh --apply
./scripts/setup.sh --install-rtk --migrate-token-saver --apply
```

The setup script checks for `rtk`, legacy `token-saver` hooks, other non-RTK `PreToolUse` hooks, the approved RTK version, and the approved user-local install directory. It can migrate legacy H5G token-saver hooks while preserving unrelated hooks. It runs RTK's global Claude Code initialization only when explicitly requested. Use `--force` / `-Force` only after manually reviewing warnings.

The RTK installer downloads the pinned `v0.40.0` GitHub release asset for the user's OS/CPU, verifies SHA-256, and installs only the `rtk` binary into a user-local bin directory. It does not require admin privileges with the default install location.

## Why Global Setup Is Opt-In

RTK global setup modifies Claude Code hook settings. The plugin has its own bundled fail-open hooks, so global setup remains a deliberate per-machine choice rather than a requirement for normal plugin behavior.

## Token Saver Replacement

The original H5G `token-saver` plugin remains in GitHub for rollback or future reuse, but the marketplace now lists this RTK wrapper instead.
