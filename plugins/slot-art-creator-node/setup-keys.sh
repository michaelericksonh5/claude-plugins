#!/usr/bin/env bash
# slot-art-creator-node - API key setup (Mac / Linux launcher)
#
# This script is a thin launcher around setup-keys.js. The .js script is the
# actual implementation — uses hidden-input prompts so keys never echo to the
# terminal log. The .sh exists to give Mac/Linux users a one-line invocation.
#
# Keys are written to ~/.h5g-slot-art-creator/.env which survives plugin
# reinstalls and is read on MCP server startup.

set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " slot-art-creator-node - API key setup"
echo " ======================================"
echo ""
echo " Your keys will be saved to:"
echo "   $HOME/.h5g-slot-art-creator/.env"
echo ""
echo " Get keys here:"
echo "   Google Gemini   https://aistudio.google.com/apikey         (NB2 tools)"
echo "   fal.ai          https://fal.ai/dashboard                    (NB2 tools)"
echo "   OpenAI          https://platform.openai.com/api-keys        (gpt-image-2 tools, optional)"
echo ""
echo " Either GEMINI or FAL works for the 4 NB2 tools (both gives optimal routing)."
echo " OPENAI is optional and adds gpt2_generate / gpt2_edit (text rendering, 4K, composition)."
echo ""
echo " Your input is hidden - keys will not echo to this terminal."
echo ""

if ! command -v node >/dev/null 2>&1; then
    echo " ERROR: Node.js not found."
    echo ""
    echo " Install Node.js 18 or later from:"
    echo "   https://nodejs.org/en/download"
    echo ""
    echo " Then re-run this script."
    exit 1
fi

node setup-keys.js
RC=$?

echo ""
if [ $RC -eq 0 ]; then
    echo " Setup complete. Return to Claude Code."
else
    echo " Setup did not complete. Review messages above and try again."
fi
echo ""
