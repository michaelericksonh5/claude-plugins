#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " slot-art-creator-node | High 5 Games"
echo " ======================================="
echo " Node.js edition. No Python required."
echo ""

# -----------------------------------------------------------------------
# Check Node.js
# -----------------------------------------------------------------------

if ! command -v node &>/dev/null; then
    echo " ERROR: Node.js not found."
    echo ""
    echo " Install Node.js 18 or later:"
    echo "   macOS:   brew install node   OR   https://nodejs.org/en/download"
    echo "   Linux:   https://nodejs.org/en/download"
    echo ""
    exit 1
fi

NODE_VER="$(node --version)"
NODE_MAJOR="$(echo "$NODE_VER" | sed 's/v//;s/\..*//')"
echo " Found Node.js $NODE_VER"

if [ "$NODE_MAJOR" -lt 18 ]; then
    echo " ERROR: Node.js 18+ required. You have $NODE_VER."
    echo " Download from https://nodejs.org/en/download"
    exit 1
fi

# -----------------------------------------------------------------------
# Install npm dependencies
# -----------------------------------------------------------------------

echo ""
echo " Installing dependencies (this takes about 10 seconds)..."
cd nb2-mcp-server

# Disable -e temporarily so we can catch npm failure with a friendlier message.
# --no-audit / --no-fund suppress audit + funding noise (audit is already run
# + cleaned at build time).
#
# The deprecated `node-domexception` polyfill is replaced at install time
# with a local shim (see nb2-mcp-server/shims/node-domexception/) wired in
# via the npm `overrides` block in package.json. The shim re-exports
# globalThis.DOMException, which is native on Node >=18 (our minimum).
# Result: no deprecation warning at install time, no functional change.
set +e
if [ -f package-lock.json ]; then
    npm ci --prefer-offline --no-audit --no-fund
    NPM_RC=$?
    if [ $NPM_RC -ne 0 ]; then
        echo " Offline install failed, retrying online..."
        npm ci --no-audit --no-fund
        NPM_RC=$?
    fi
else
    npm install --no-audit --no-fund
    NPM_RC=$?
fi
set -e

if [ $NPM_RC -ne 0 ]; then
    echo ""
    echo " ERROR: npm install failed."
    echo "   Check your internet connection and try again."
    echo "   You can also try:  cd nb2-mcp-server && npm install"
    exit 1
fi

# Bundle the MCP server into a single self-contained file at dist/index.mjs.
# Marketplace cloners (Claude Code, Cowork) don't run npm install on the
# cached plugin, so the cached install can't reach node_modules. plugin.json
# points at the bundle, which has zero runtime deps.
echo " Building MCP server bundle..."
set +e
npm run build --silent
BUILD_RC=$?
set -e
if [ $BUILD_RC -ne 0 ]; then
    echo ""
    echo " ERROR: npm run build failed."
    exit 1
fi

cd "$SCRIPT_DIR"
echo " Dependencies installed and bundle built."

# -----------------------------------------------------------------------
# API key setup
# -----------------------------------------------------------------------

echo ""
echo " This plugin needs an API key to generate images."
echo " EITHER KEY ALONE is fully sufficient for all 4 tools — both providers can do everything."
echo " Setting BOTH only matters because each tool gets routed to its strongest backend."
echo ""
echo "   Option 1 - Google Gemini   https://aistudio.google.com/apikey"
echo "   Option 2 - fal.ai          https://fal.ai/dashboard"
echo ""
printf " Set up API key(s) now? [Y/n] "
read -r run_setup
# Case-insensitive "n" check — written for bash 3.2 compatibility (stock macOS).
# Don't use ${var,,} here, that's bash 4+ only.
case "$run_setup" in
    n|N) skip_setup=1 ;;
    *)   skip_setup=0 ;;
esac
if [ "$skip_setup" = "0" ]; then
    node setup-keys.js
else
    echo ""
    echo " Skipped. Run later:  node setup-keys.js"
fi

# -----------------------------------------------------------------------
# Prepare Claude Code marketplace / Cowork upload ZIP
# -----------------------------------------------------------------------

echo ""
echo " Where do you want to install this plugin?"
echo "   [1] BOTH — Claude Code (automatic) + Claude Cowork ZIP (manual upload step)  [RECOMMENDED]"
echo "   [2] Claude Code only (this machine)"
echo "   [3] Cowork upload ZIP only"
echo "   [4] Skip (I will install manually)"
echo ""
echo " Note: Claude Code and Claude Cowork are SEPARATE plugin systems even though"
echo "       they both live inside the Claude desktop app. Choosing [1] prepares"
echo "       BOTH so the plugin works no matter which one you use. The Cowork"
echo "       upload requires one manual click at the end (this script can't do"
echo "       GUI uploads for you — instructions printed below)."
echo ""
printf " Choice [1]: "
read -r install_target
install_target="${install_target:-1}"

CODE_MARKETPLACE_PLUGIN="$HOME/Documents/Claude_Plugins/slot-art-creator-node"
PLUGIN_ITEMS=(
    ".claude-plugin"
    "skills"
    "agents"
    "hooks"
    "nb2-mcp-server"
    "shared"
    "package.json"
    "README.md"
    "setup-keys.js"
)
EXCLUDED_DIRS=(
    "node_modules"
    "generated"
    "logs"
    ".git"
    ".cache"
    "cache"
    "caches"
    "__pycache__"
)
EXCLUDED_FILES=(
    ".env"
    ".env.*"
    "*.log"
    "npm-debug.log*"
    "yarn-debug.log*"
    "yarn-error.log*"
    "pnpm-debug.log*"
    "*.pem"
    "*credentials*"
    "id_rsa*"
    "id_ed25519*"
)

# Resolve realpath of source so we can compare with destinations.
# (POSIX realpath isn't always available; fall back to pwd-based.)
resolve_path() {
    if command -v realpath &>/dev/null; then
        realpath -m "$1" 2>/dev/null || echo "$1"
    else
        # macOS doesn't ship GNU realpath. Use cd+pwd as fallback.
        if [ -d "$1" ]; then
            ( cd "$1" 2>/dev/null && pwd ) || echo "$1"
        else
            echo "$1"
        fi
    fi
}

prune_staged_plugin() {
    local root="$1"
    local pattern
    for pattern in "${EXCLUDED_DIRS[@]}"; do
        find "$root" -type d -name "$pattern" -prune -exec rm -rf {} +
    done
    for pattern in "${EXCLUDED_FILES[@]}"; do
        find "$root" -type f -name "$pattern" -delete
    done
}

stage_plugin() {
    local src="$1"
    local dst="$2"
    local item
    mkdir -p "$dst"
    for item in "${PLUGIN_ITEMS[@]}"; do
        if [ -e "$src/$item" ]; then
            cp -R "$src/$item" "$dst/"
        fi
    done
    prune_staged_plugin "$dst"
}

run_claude_plugin_validate() {
    if ! command -v claude &>/dev/null; then
        echo " WARNING: claude CLI not found; skipping optional 'claude plugin validate'."
        return 0
    fi
    echo " Running optional Claude CLI validation..."
    claude plugin validate "$SCRIPT_DIR"
}

# copy_plugin <source> <dest>
# Idempotent clean install. Refuses to delete the destination when source == dest
# (which would be self-destructive when the user runs install.sh from
# inside the local marketplace source folder).
copy_plugin() {
    local src="$1"
    local dst="$2"
    local src_real dst_real tmp stage
    src_real="$(resolve_path "$src")"
    dst_real="$(resolve_path "$dst")"
    if [ "$src_real" = "$dst_real" ]; then
        echo " Skipping copy — source and destination are the same path:"
        echo "   $src_real"
        echo " (the plugin is already at the target. No files to copy.)"
        return 0
    fi
    tmp="$(mktemp -d)"
    stage="$tmp/slot-art-creator-node"
    stage_plugin "$src" "$stage"
    rm -rf "$dst"
    mkdir -p "$(dirname "$dst")"
    mv "$stage" "$dst"
    rm -rf "$tmp"
}

do_install_code() {
    echo ""
    echo " Preparing Claude Code local marketplace source..."
    copy_plugin "$SCRIPT_DIR" "$CODE_MARKETPLACE_PLUGIN"
    echo " Marketplace source ready at: $CODE_MARKETPLACE_PLUGIN"
}

package_cowork_zip() {
    echo ""
    echo " Building Claude Cowork upload ZIP..."
    if command -v pwsh &>/dev/null; then
        pwsh -NoProfile -ExecutionPolicy Bypass -File "$SCRIPT_DIR/tools/package-cowork-zip.ps1"
        return
    fi
    run_claude_plugin_validate
    if ! command -v zip &>/dev/null; then
        echo " ERROR: install PowerShell 7 (pwsh) or zip to build the Cowork upload ZIP."
        return 1
    fi
    mkdir -p "$SCRIPT_DIR/dist"
    local output="$SCRIPT_DIR/dist/slot-art-creator-node-cowork-upload.zip"
    local tmp stage
    tmp="$(mktemp -d)"
    stage="$tmp/slot-art-creator-node"
    stage_plugin "$SCRIPT_DIR" "$stage"
    rm -f "$output"
    ( cd "$stage" && zip -qr "$output" . )
    rm -rf "$tmp"
    local size_bytes
    size_bytes="$(wc -c < "$output" | tr -d ' ')"
    if [ "$size_bytes" -gt $((50 * 1024 * 1024)) ]; then
        echo " ERROR: Cowork ZIP is over the documented 50 MB organization upload limit."
        return 1
    fi
    echo " Cowork upload ZIP created:"
    echo "   $output"
    echo " Install in Claude Desktop > Cowork > Customize > Browse plugins > upload custom plugin file."
}

case "$install_target" in
    1) do_install_code; package_cowork_zip ;;
    2) do_install_code ;;
    3) package_cowork_zip ;;
    *) echo " Skipped. For Code, use the plugin marketplace flow. For Cowork, upload a packaged ZIP in Claude Desktop." ;;
esac

# -----------------------------------------------------------------------
# Register the marketplace + plugin with Claude Code
# -----------------------------------------------------------------------
# Idempotent — adds h5g-plugins to settings.json's extraKnownMarketplaces
# and writes a local marketplace manifest so the plugin shows up in the
# documented Claude Code plugin marketplace flow.

if [ "$install_target" = "1" ] || [ "$install_target" = "2" ]; then
    echo ""
    echo " Registering plugin with Claude Code..."
    printf "  Enable plugin automatically? [Y/n] "
    read -r enable_now
    # Case-insensitive "n" check — bash 3.2 compatible (stock macOS).
    case "$enable_now" in
        n|N) auto_enable=0 ;;
        *)   auto_enable=1 ;;
    esac
    if [ "$auto_enable" = "0" ]; then
        node "$SCRIPT_DIR/tools/register-marketplace.js" || \
            echo " WARNING: marketplace registration failed; re-run manually if needed."
    else
        node "$SCRIPT_DIR/tools/register-marketplace.js" --enable || \
            echo " WARNING: marketplace registration failed; re-run manually if needed."
    fi
fi

# -----------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------

echo ""
# -----------------------------------------------------------------------
# H drive detection (shared asset folder)
# -----------------------------------------------------------------------

# Try the standard Drive for Desktop mount points in order:
#  1. /Volumes/GoogleDrive/Shared drives/...   (older / classic Drive for Desktop)
#  2. /Volumes/Shared drives/...               (current Drive for Desktop)
#  3. ~/Library/CloudStorage/GoogleDrive-*/Shared drives/...   (newer macOS)
#  4. /Users/$(whoami)/Google Drive/Shared drives/...           (legacy Backup & Sync)
ASSET_SUITE_TAIL="Content Management - AI/Production_AI 2/Asset_Creation_Suite"
CANDIDATE_PATHS=(
    "/Volumes/GoogleDrive/Shared drives/$ASSET_SUITE_TAIL"
    "/Volumes/Shared drives/$ASSET_SUITE_TAIL"
)
# Glob the CloudStorage location for any GoogleDrive-* mount
if [ -d "$HOME/Library/CloudStorage" ]; then
    for d in "$HOME/Library/CloudStorage"/GoogleDrive-*/Shared\ drives; do
        if [ -d "$d/$ASSET_SUITE_TAIL" ]; then
            CANDIDATE_PATHS+=("$d/$ASSET_SUITE_TAIL")
        fi
    done
fi
CANDIDATE_PATHS+=(
    "$HOME/Google Drive/Shared drives/$ASSET_SUITE_TAIL"
)

echo ""
H_DRIVE_PATH=""
for p in "${CANDIDATE_PATHS[@]}"; do
    if [ -d "$p" ]; then
        H_DRIVE_PATH="$p"
        break
    fi
done

if [ -n "$H_DRIVE_PATH" ]; then
    echo " ✓ Asset suite detected at:"
    echo "   $H_DRIVE_PATH"
    echo "   Projects will be saved in {GameID}_$(whoami) folders here."
else
    echo " ⚠  Asset suite folder not found at any standard Drive for Desktop mount."
    echo "    Make sure Google Drive for Desktop is running and the shared drive is mounted."
    echo "    Common paths:"
    for p in "${CANDIDATE_PATHS[@]}"; do
        echo "      $p"
    done
fi

echo ""
# -----------------------------------------------------------------------
# Final verification — read the installed state and confirm everything
# is wired correctly. This is what tells the user (or a coworker) whether
# the install actually succeeded end-to-end, vs. a half-finished state.
# -----------------------------------------------------------------------
set +e
node "$SCRIPT_DIR/tools/verify-install.js"
VERIFY_RC=$?
set -e

echo ""
if [ "$VERIFY_RC" -ne 0 ]; then
    echo " Verification reported a failure above. Address the items marked [FAIL]"
    echo " before reloading Claude Code, otherwise the slot- commands will not appear."
    exit "$VERIFY_RC"
fi

# If a Cowork ZIP was built, surface the manual upload step prominently —
# this is the one part of the install we cannot automate (it requires
# a GUI click in Claude Desktop).
COWORK_ZIP="$SCRIPT_DIR/dist/slot-art-creator-node-cowork-upload.zip"
if [ -f "$COWORK_ZIP" ]; then
    echo ""
    echo " ========================================================================"
    echo "  CLAUDE COWORK (MANUAL STEP) — required for Cowork sessions to see the plugin"
    echo " ========================================================================"
    echo ""
    echo "  The Cowork upload ZIP is built and ready at:"
    echo "    $COWORK_ZIP"
    echo ""
    echo "  To install in Cowork:"
    echo "    1. Open Claude Desktop"
    echo "    2. Go to Cowork > Customize > Browse plugins > upload custom plugin file"
    echo "    3. Select the ZIP path above"
    echo "    4. Start a new Cowork session (existing sessions don't pick it up)"
    echo ""
    echo "  If your org admin has plugin uploads locked down, share this ZIP with"
    echo "  them so they can upload it under Organization Settings > Plugins."
    echo ""
fi

echo " ----------------------------------------------------------"
echo "  CLAUDE CODE — already installed and registered automatically"
echo " ----------------------------------------------------------"
echo "  Reload Claude Code (Ctrl+Shift+P > Developer: Reload Window) to activate."
echo "  Then type /slot-step- to see the 11 numbered workflow commands."
echo ""

exit 0
