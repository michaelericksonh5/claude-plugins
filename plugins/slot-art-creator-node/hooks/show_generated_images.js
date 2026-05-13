#!/usr/bin/env node
/**
 * PostToolUse hook — slot-art-creator-node
 *
 * Reads the tool result from stdin, extracts PNG paths from the text output,
 * and returns a systemMessage telling Claude to:
 *   1. Read each path so the image appears inline in the chat
 *   2. Surface the folder (with both a plain path and a file:// URI) so the
 *      user always knows where files landed and can click to open it
 *
 * This works for all 4 MCP tools (nb2_generate, nb2_edit, nb2_upscale,
 * nb2_smart_resize) since they all use the same formatResult shape.
 */

import * as path from "path";
import * as readline from "readline";

let raw = "";
const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on("line", (line) => { raw += line + "\n"; });

rl.on("close", () => {
  try {
    const payload = JSON.parse(raw.trim());

    // tool_result is an array of {type, text} blocks
    const blocks = payload?.tool_result || [];
    const paths = [];

    for (const block of blocks) {
      if (block?.type !== "text") continue;
      const text = block?.text || "";
      // Extract lines like:  "    - C:\Users\...\image.png"
      for (const line of text.split("\n")) {
        const m = line.match(/^\s+-\s+(.+\.png)\s*$/i);
        if (m) paths.push(m[1].trim());
      }
    }

    if (!paths.length) {
      process.exit(0);
    }

    // All paths from a single tool call share the same parent folder.
    // Surface it explicitly as both a plain path (copy-friendly) and a
    // file:// URI (clickable in most modern terminals + Claude Code UI).
    const folder = path.dirname(paths[0]);
    const fileUri = "file:///" + folder.replace(/\\/g, "/");

    const msg =
      `Image(s) generated and saved to:\n` +
      `  Folder: ${folder}\n` +
      `  Open:   ${fileUri}\n` +
      `\n` +
      `Use the Read tool on each path to display them inline:\n` +
      paths.map((p) => `  Read(${JSON.stringify(p)})`).join("\n") +
      `\n\nAlways Read every path returned, not just the first one. ` +
      `When you summarize back to the user, include the Folder path so they ` +
      `know where the files landed.`;

    process.stdout.write(JSON.stringify({ systemMessage: msg }));
  } catch {
    // Malformed payload — exit silently so we don't break the hook chain
    process.exit(0);
  }
});
