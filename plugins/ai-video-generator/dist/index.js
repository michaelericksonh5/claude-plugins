#!/usr/bin/env node
/**
 * Veo Video MCP Server
 *
 * AI video generation for Claude — Veo 3.1 (fal.ai + Gemini),
 * Happy Horse, and Seedance 2.0.
 *
 * Usage (stdio, for Claude Desktop / Claude Code):
 *   node dist/index.js
 *
 * Required environment variables (at least one):
 *   FAL_KEY         — fal.ai API key (https://fal.ai/dashboard/keys)
 *   GEMINI_API_KEY  — Google Gemini API key (https://aistudio.google.com/app/apikey)
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerSetupTools } from "./tools/setupTools.js";
import { registerUploadTools } from "./tools/uploadTools.js";
import { registerVeoTools } from "./tools/veoTools.js";
import { registerAlternativeTools } from "./tools/alternativeTools.js";
import { registerFfmpegTools } from "./tools/ffmpegTools.js";
const server = new McpServer({
    name: "ai-video-mcp-server",
    version: "1.2.0",
});
// Register all tool groups
registerSetupTools(server);
registerUploadTools(server);
registerVeoTools(server);
registerAlternativeTools(server);
registerFfmpegTools(server);
// Start stdio transport
const transport = new StdioServerTransport();
await server.connect(transport);
process.stderr.write("AI Video MCP Server running (stdio)\n");
//# sourceMappingURL=index.js.map