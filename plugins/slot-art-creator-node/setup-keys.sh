#!/usr/bin/env bash
# slot-art-creator-node - API key setup (Mac / Linux launcher)
#
# Self-contained launcher. Keys are written to ~/.h5g-slot-art-creator/.env,
# which survives plugin reinstalls and is read by the MCP server at startup.
# This script does not depend on the plugin cache path or on Node.js.

set -euo pipefail

CONFIG_DIR="$HOME/.h5g-slot-art-creator"
ENV_PATH="$CONFIG_DIR/.env"
ORIG_STTY="$(stty -g 2>/dev/null || true)"

restore_terminal() {
    if [ -n "$ORIG_STTY" ]; then
        stty "$ORIG_STTY" 2>/dev/null || true
    else
        stty echo 2>/dev/null || true
    fi
}

trap restore_terminal EXIT HUP INT TERM

read_env_value() {
    local name="$1"
    if [ -f "$ENV_PATH" ]; then
        sed -n "s/^${name}=//p" "$ENV_PATH" | tail -n 1
    fi
}

prompt_key() {
    local name="$1"
    local label="$2"
    local url="$3"
    local value
    echo ""
    echo "$label"
    echo "Get a key: $url"
    printf "%s (input hidden, blank skips): " "$name"
    stty -echo
    IFS= read -r value || true
    restore_terminal
    echo ""
    if [ -n "$value" ]; then
        case "$name" in
            GEMINI_API_KEY) GEMINI_API_KEY="$value" ;;
            FAL_KEY) FAL_KEY="$value" ;;
            OPENAI_API_KEY) OPENAI_API_KEY="$value" ;;
            *) echo "Unsupported key name: $name"; return 1 ;;
        esac
        echo "$name saved."
    else
        echo "$name skipped."
    fi
}

GEMINI_API_KEY="$(read_env_value GEMINI_API_KEY || true)"
FAL_KEY="$(read_env_value FAL_KEY || true)"
OPENAI_API_KEY="$(read_env_value OPENAI_API_KEY || true)"
HTTPS_PROXY_VALUE="$(read_env_value HTTPS_PROXY || true)"
HTTP_PROXY_VALUE="$(read_env_value HTTP_PROXY || true)"
NO_PROXY_VALUE="$(read_env_value NO_PROXY || true)"
NODE_EXTRA_CA_CERTS_VALUE="$(read_env_value NODE_EXTRA_CA_CERTS || true)"
SSL_CERT_FILE_VALUE="$(read_env_value SSL_CERT_FILE || true)"

echo ""
echo "slot-art-creator-node - API key setup"
echo "======================================"
echo ""
echo "Keys will be saved to: $ENV_PATH"
echo "Input is hidden and never goes through Claude chat."
echo ""
echo "[1] Gemini only"
echo "[2] fal.ai only"
echo "[3] OpenAI only"
echo "[4] NB2 keys (Gemini + fal.ai)"
echo "[5] All keys"
printf "Choice [1]: "
read -r choice
choice="${choice:-1}"

case "$choice" in
    5)
        prompt_key GEMINI_API_KEY "Google Gemini / NB2" "https://aistudio.google.com/apikey"
        prompt_key FAL_KEY "fal.ai / NB2 fallback" "https://fal.ai/dashboard"
        prompt_key OPENAI_API_KEY "OpenAI / gpt-image-2 (optional)" "https://platform.openai.com/api-keys"
        ;;
    4)
        prompt_key GEMINI_API_KEY "Google Gemini / NB2" "https://aistudio.google.com/apikey"
        prompt_key FAL_KEY "fal.ai / NB2 fallback" "https://fal.ai/dashboard"
        ;;
    3)
        prompt_key OPENAI_API_KEY "OpenAI / gpt-image-2 (optional)" "https://platform.openai.com/api-keys"
        ;;
    2)
        prompt_key FAL_KEY "fal.ai / NB2 fallback" "https://fal.ai/dashboard"
        ;;
    *)
        prompt_key GEMINI_API_KEY "Google Gemini / NB2" "https://aistudio.google.com/apikey"
        ;;
esac

mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR" 2>/dev/null || true
{
    echo "# slot-art-creator-node API keys"
    echo "# Written by setup-keys.sh"
    echo "# Do not paste these values into chat."
    [ -n "${GEMINI_API_KEY:-}" ] && echo "GEMINI_API_KEY=$GEMINI_API_KEY"
    [ -n "${FAL_KEY:-}" ] && echo "FAL_KEY=$FAL_KEY"
    [ -n "${OPENAI_API_KEY:-}" ] && echo "OPENAI_API_KEY=$OPENAI_API_KEY"
    [ -n "${HTTPS_PROXY_VALUE:-}" ] && echo "HTTPS_PROXY=$HTTPS_PROXY_VALUE"
    [ -n "${HTTP_PROXY_VALUE:-}" ] && echo "HTTP_PROXY=$HTTP_PROXY_VALUE"
    [ -n "${NO_PROXY_VALUE:-}" ] && echo "NO_PROXY=$NO_PROXY_VALUE"
    [ -n "${NODE_EXTRA_CA_CERTS_VALUE:-}" ] && echo "NODE_EXTRA_CA_CERTS=$NODE_EXTRA_CA_CERTS_VALUE"
    [ -n "${SSL_CERT_FILE_VALUE:-}" ] && echo "SSL_CERT_FILE=$SSL_CERT_FILE_VALUE"
} > "$ENV_PATH"
chmod 600 "$ENV_PATH" 2>/dev/null || true

echo ""
echo "Setup complete. Saved keys to: $ENV_PATH"
echo "Restart Claude Desktop / reload Claude Code so the MCP server sees the new keys."
