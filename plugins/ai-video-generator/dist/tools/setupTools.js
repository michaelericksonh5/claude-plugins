/**
 * Setup & key management tools — help users safely configure their API keys.
 * Keys are NEVER echoed back or stored to disk by this server.
 */
import { z } from "zod";
import { getApiKeyStatus } from "../services/keyManager.js";
import * as os from "node:os";
import * as path from "node:path";
export function registerSetupTools(server) {
    // ── Check API Key Status ──────────────────────────────────────────────────
    server.registerTool("veo_check_api_keys", {
        title: "Check API Key Status",
        description: "Check which API keys are configured. Returns fal_configured, gemini_configured, active_provider, and a status message. Does NOT expose key values.",
        inputSchema: z.object({}),
        annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    }, async () => {
        const status = getApiKeyStatus();
        let message;
        if (status.active_provider === "none") {
            message = "No API keys configured. Use the veo_setup_api_key tool to get setup instructions.";
        }
        else if (status.fal_configured && status.gemini_configured) {
            message = "Both fal.ai and Gemini keys configured. fal.ai is used by default (set provider=gemini to override).";
        }
        else if (status.fal_configured) {
            message = "fal.ai key configured. All Veo 3.1, Happy Horse, and Seedance models available.";
        }
        else {
            message = "Gemini key configured. Veo 3.1 text-to-video, image-to-video, first/last frame, reference, and extend available.";
        }
        const output = { ...status, message };
        return {
            content: [{ type: "text", text: JSON.stringify(output, null, 2) }],
            structuredContent: JSON.parse(JSON.stringify(output)),
        };
    });
    // ── Setup API Key Instructions ────────────────────────────────────────────
    server.registerTool("veo_setup_api_key", {
        title: "API Key Setup Instructions",
        description: "Get safe instructions for configuring a fal.ai or Gemini API key. Pass provider=fal or provider=gemini. NEVER pass your actual key to this tool.",
        inputSchema: z.object({
            provider: z
                .enum(["fal", "gemini"])
                .describe("Which provider to set up: fal for fal.ai, gemini for Google Gemini"),
        }),
        annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    }, async ({ provider }) => {
        const settingsPath = path.join(os.homedir(), ".claude", "settings.json");
        const isWindows = process.platform === "win32";
        let instructions;
        if (provider === "fal") {
            instructions = [
                "# fal.ai API Key Setup",
                "",
                "## Step 1: Get your key",
                "Visit: https://fal.ai/dashboard/keys",
                "Click 'Create new key' and copy it.",
                "",
                "## Step 2: Run the setup script",
                "In the terminal, from the ai-video-mcp-server plugin directory:",
                "",
                isWindows
                    ? "  .\\setup-key.ps1 --fal"
                    : "  ./setup-key.sh --fal",
                "",
                "The script writes FAL_KEY to: " + settingsPath,
                "under the top-level \"env\" key. Claude Code reads this file and",
                "passes keys to all plugins — you never need to touch it manually.",
                "",
                "Keys written here are shared across all plugins in the marketplace.",
                "If you already set this key via another plugin's setup script, it",
                "is already available here.",
                "",
                "## Step 3: Verify",
                'Ask Claude: "Check my video API keys"',
                "",
                "SECURITY: Never share your key in chat, never commit it to git.",
            ].join("\n");
        }
        else {
            instructions = [
                "# Google Gemini API Key Setup",
                "",
                "## Step 1: Get your key",
                "Visit: https://aistudio.google.com/app/apikey",
                "Click 'Create API key', select a project, copy the key.",
                "",
                "## Step 2: Run the setup script",
                "In the terminal, from the ai-video-mcp-server plugin directory:",
                "",
                isWindows
                    ? "  .\\setup-key.ps1 --gemini"
                    : "  ./setup-key.sh --gemini",
                "",
                "The script validates the key live against the Gemini API, then",
                "writes GEMINI_API_KEY to: " + settingsPath,
                "under the top-level \"env\" key. Claude Code reads this file and",
                "passes keys to all plugins — you never need to touch it manually.",
                "",
                "Keys written here are shared across all plugins in the marketplace.",
                "If you already set this key via another plugin's setup script, it",
                "is already available here.",
                "",
                "## Step 3: Verify",
                'Ask Claude: "Check my video API keys"',
                "",
                "## Notes",
                "- Veo 3.1 requires the PAID Gemini API tier (not the free tier)",
                "- Model: veo-3.1-generate-preview",
                "- Generation is async and may take up to 10 minutes",
                "",
                "SECURITY: Never share your key in chat, never commit it to git.",
            ].join("\n");
        }
        return {
            content: [{ type: "text", text: instructions }],
        };
    });
}
//# sourceMappingURL=setupTools.js.map