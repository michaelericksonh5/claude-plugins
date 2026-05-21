---
name: slot-setup
description: >-
  Fast first-run setup and auth triage for slot-art-creator-node. Use when the user wants to set, add, rotate, or verify API keys; says "set up my keys", "add my API key", "configure the plugin", "plugin isn't working", "MCP server isn't working", "missing API key", "401", "403", "unauthorized", "forbidden", "GEMINI_API_KEY is not set", "FAL_KEY is not set", or "OPENAI_API_KEY is not set". Open the safe terminal key-entry launcher immediately; never accept API keys in chat.
---

# Fast Setup — API Keys

Goal: open a local terminal prompt where the user can paste API keys with
hidden input. Do this quickly. Do not explain the full provider matrix unless
the user asks.

## Hard Rules

- Never accept an API key in chat. If the user pastes one, tell them to delete
  it if possible and use the launcher instead.
- Never echo even partial key values.
- Keys are saved to `~/.h5g-slot-art-creator/.env`.
- In Claude Code desktop app and Cowork, never ask the user to browse
  `local-agent-mode-sessions\...\rpm\plugin_...` paths. Those are runtime
  extraction paths, not stable user-facing locations.

## Workflow

### Step 1 — Open the key-entry launcher now

Say one short sentence, then run the launcher command:

> "I'll open the local key setup terminal now. Paste keys there, not in chat."

#### Windows — Claude Code desktop app, Claude Code CLI, or Cowork

Use the Shell tool to copy the plugin's setup launcher to the user's home
folder and open it:

```powershell
$ErrorActionPreference = 'Stop'
function Test-SlotSetupCandidate($File) {
  $dir = $File.DirectoryName
  if (-not (Test-Path -LiteralPath (Join-Path $dir "setup-keys.ps1"))) { return $false }
  $manifestPath = Join-Path $dir ".claude-plugin\plugin.json"
  if (-not (Test-Path -LiteralPath $manifestPath)) { return $false }
  try {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    return $manifest.name -eq "slot-art-creator-node"
  } catch {
    return $false
  }
}
$candidates = @()
$candidates += Get-ChildItem -Path "$env:USERPROFILE\.claude\plugins\cache\h5g-plugins\slot-art-creator-node\*\setup-keys.bat" -ErrorAction SilentlyContinue |
  Where-Object { Test-SlotSetupCandidate $_ }
$desktopRoot = Join-Path $env:APPDATA "Claude\local-agent-mode-sessions"
if (Test-Path -LiteralPath $desktopRoot) {
  $candidates += Get-ChildItem -Path $desktopRoot -Filter setup-keys.bat -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '\\rpm\\plugin_[^\\]+\\setup-keys\.bat$' -and (Test-SlotSetupCandidate $_) }
}
$source = $candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $source) { throw "setup-keys.bat was not found. Update/reinstall slot-art-creator-node v1.7.19+ from the H5G marketplace." }
$launcher = Join-Path $env:USERPROFILE "H5G-Slot-Art-Key-Setup.bat"
$script = Join-Path $env:USERPROFILE "H5G-Slot-Art-Key-Setup.ps1"
Copy-Item -LiteralPath $source.FullName -Destination $launcher -Force
$psSource = Join-Path $source.DirectoryName "setup-keys.ps1"
if (-not (Test-Path -LiteralPath $psSource)) { throw "setup-keys.ps1 was not found next to setup-keys.bat. You are likely on an old cached install; update/reinstall slot-art-creator-node v1.7.19+ from the H5G marketplace." }
Copy-Item -LiteralPath $psSource -Destination $script -Force
Start-Process -FilePath $launcher
Write-Host "Launched stable key setup: $launcher"
```

After running it, tell the user only:

> "A terminal window should be open. Choose Gemini, fal.ai, OpenAI, or all
> keys, then paste keys there. Input is hidden. When it says setup complete,
> restart Claude Desktop if you're in the desktop app, then come back and say
> done."

#### Mac / Linux — Claude Code desktop app, Claude Code CLI, or Cowork

```bash
set -e
src=""
roots=(
  "$HOME/.claude/plugins/cache/h5g-plugins/slot-art-creator-node"
  "$HOME/Library/Application Support/Claude/local-agent-mode-sessions"
  "$HOME/.config/Claude/local-agent-mode-sessions"
  "$HOME/.config/claude/local-agent-mode-sessions"
)
for root in "${roots[@]}"; do
  [ -d "$root" ] || continue
  while IFS= read -r -d '' candidate; do
  dir="$(dirname "$candidate")"
  manifest="$dir/.claude-plugin/plugin.json"
  if [ -f "$manifest" ]; then
    compact="$(tr -d '\r\n\t ' < "$manifest")"
    case "$compact" in
      *'"name":"slot-art-creator-node"'*) src="$candidate"; break ;;
    esac
  fi
  done < <(find "$root" -path '*/setup-keys.sh' -type f -print0 2>/dev/null)
  [ -n "$src" ] && break
done
if [ -z "$src" ]; then
  echo "setup-keys.sh was not found. Update/reinstall slot-art-creator-node v1.7.19+ from the H5G marketplace." >&2
  exit 1
fi
launcher="$HOME/H5G-Slot-Art-Key-Setup.sh"
cp "$src" "$launcher"
chmod +x "$launcher"
opened=0
case "$(uname -s)" in
  Darwin)
    if command -v osascript >/dev/null 2>&1; then
      osascript - "$launcher" >/dev/null <<'APPLESCRIPT' && opened=1
on run argv
  tell application "Terminal" to do script "bash " & quoted form of item 1 of argv
end run
APPLESCRIPT
    fi
    ;;
  Linux)
    if command -v x-terminal-emulator >/dev/null 2>&1; then
      x-terminal-emulator -e bash "$launcher" >/dev/null 2>&1 & opened=1
    elif command -v gnome-terminal >/dev/null 2>&1; then
      gnome-terminal -- bash "$launcher" >/dev/null 2>&1 & opened=1
    elif command -v konsole >/dev/null 2>&1; then
      konsole -e bash "$launcher" >/dev/null 2>&1 & opened=1
    elif command -v xterm >/dev/null 2>&1; then
      xterm -e bash "$launcher" >/dev/null 2>&1 & opened=1
    fi
    ;;
esac
if [ "$opened" -eq 1 ]; then
  echo "Launched stable key setup: $launcher"
else
  echo "Copied stable key setup to: $launcher"
  echo "Run this in Terminal: bash $(printf '%q' "$launcher")"
fi
```

If auto-open succeeded, tell the user a terminal window should be open. If it
printed a fallback command, tell the user to run that `bash ...` command in
Terminal. Keep it brief.

### Step 2 — If launcher cannot be found

Say the plugin likely needs to be updated/reinstalled. Then give the manual
fallback, without asking for keys in chat:

> 1. Create or open this file in any text editor:
>    `~/.h5g-slot-art-creator/.env`
>    (You may need to create the folder first.)
> 2. Add one, two, or all three lines (no quotes, no spaces around the `=`):
>    ```
>    GEMINI_API_KEY=AIza...your-key-here
>    FAL_KEY=...your-key-here
>    OPENAI_API_KEY=sk-...your-key-here
>    ```
>    Either Gemini or fal.ai is enough to run the NB2 workflow; OpenAI
>    is optional and only needed if you want the `gpt2_*` tools.
> 3. Save the file, then come back here.

### Step 3 — Validate only after setup, or for auth failures

Do not run validation before opening the launcher unless the user specifically
asked only to check existing keys.

When the user says "done", find `setup-keys.js` and run `--check`. Search:

- `~/.claude/plugins/cache/h5g-plugins/slot-art-creator-node/*/setup-keys.js`
- `~/Library/Application Support/Claude/local-agent-mode-sessions/.../rpm/plugin_.../setup-keys.js`
- `~/.config/Claude/local-agent-mode-sessions/.../rpm/plugin_.../setup-keys.js`
- `%APPDATA%\Claude\local-agent-mode-sessions\...\rpm\plugin_...\setup-keys.js`

Before running a discovered script, verify adjacent `.claude-plugin/plugin.json`
exists and has `"name": "slot-art-creator-node"`.

```bash
node "<absolute path to setup-keys.js>" --check
```

Show the validator output, but do not print secrets. If the user is in Claude
Desktop, remind them to restart Claude Desktop so the MCP server reloads `.env`.

If the validator still reports a key as `MISSING` or `FAIL`:
- `MISSING` means run the launcher again or check the `.env` path.
- `FAIL: 401` means the key is wrong, disabled, or copied incorrectly.
- `fetch failed` means network/proxy/corporate TLS issue, not a missing-key issue.

### Provider Cheat Sheet

- Gemini: `GEMINI_API_KEY`, from https://aistudio.google.com/apikey, enables
  all `nb2_*` tools.
- fal.ai: `FAL_KEY`, from https://fal.ai/dashboard, also enables all `nb2_*`
  tools and is useful as fallback.
- OpenAI: `OPENAI_API_KEY`, from https://platform.openai.com/api-keys, enables
  `gpt2_generate` and `gpt2_edit` only.

Either Gemini or fal.ai is enough to start the main slot workflow.
