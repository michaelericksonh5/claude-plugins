#!/usr/bin/env node
/**
 * API key setup for slot-art-creator-node
 *
 * Supports two providers — EITHER KEY ALONE is fully sufficient for all 4
 * tools. Both providers have a complete implementation of every tool. With
 * both keys set, the plugin routes each tool to its strongest backend.
 *
 *   GEMINI_API_KEY  — Google AI Studio. Routes generate/edit/upscale through
 *                     Google's direct API (gemini-3.1-flash-image-preview =
 *                     Nano Banana 2). Also runs smart_resize via NB2 + local
 *                     pngjs center-crop.
 *                     https://aistudio.google.com/apikey
 *
 *   FAL_KEY         — fal.ai. Routes generate/edit/upscale through fal-ai/
 *                     nano-banana-2 (same NB2 model, wrapped by fal). Runs
 *                     smart_resize through fal-ai/smart-resize — a purpose-
 *                     built endpoint using Nano Banana PRO (different/larger
 *                     model than NB2), single API call.
 *                     https://fal.ai/dashboard
 *
 *   OPENAI_API_KEY  — OpenAI's gpt-image-2 model (separate from NB2).
 *                     Enables the gpt2_generate and gpt2_edit tools — best
 *                     for assets with accurate in-image text (paytables,
 *                     logos, text-heavy banners) and compositional
 *                     multi-reference edits. gpt-image-2 supports 1K/2K
 *                     image_size; for 4K delivery, generate at 2K with
 *                     gpt2_* then run nb2_upscale.
 *                     https://platform.openai.com/api-keys
 *
 * Routing when both NB2 keys are set:
 *   generate / edit / upscale  -> Gemini (one fewer API hop; same NB2 model)
 *   smart_resize               -> fal.ai (NB Pro endpoint is better for resize)
 *
 * gpt2_* tools always route to OpenAI when OPENAI_API_KEY is set.
 * NB2 tools and gpt2 tools are independent -- set whichever keys you need.
 *
 * Keys are written to TWO locations so both Claude Code and Claude Cowork work:
 *
 *   ~/.claude/settings.json (env key)     <- Claude Code reads this globally.
 *                                            All plugins in the marketplace
 *                                            share these keys automatically.
 *
 *   ~/.h5g-slot-art-creator/.env          <- Claude Cowork / dotenv fallback.
 *   %USERPROFILE%\.h5g-slot-art-creator\.env  (Windows)
 *
 * Both survive plugin reinstalls and updates.
 *
 * Usage:
 *   node setup-keys.js              # interactive -- prompts for both keys
 *   node setup-keys.js --fal        # set FAL_KEY only
 *   node setup-keys.js --gemini     # set GEMINI_API_KEY only
 *   node setup-keys.js --openai     # set OPENAI_API_KEY only
 *   node setup-keys.js --check      # verify saved keys
 *   node setup-keys.js --clear-fal  # clear FAL_KEY
 *   node setup-keys.js --clear-gemini  # clear GEMINI_API_KEY
 *   node setup-keys.js --clear-openai  # clear OPENAI_API_KEY
 */

import * as fs from "fs";
import * as path from "path";
import * as readline from "readline";
import * as os from "os";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CONFIG_DIR = path.join(os.homedir(), ".h5g-slot-art-creator");
const ENV_PATH = path.join(CONFIG_DIR, ".env");
const EXAMPLE_PATH = path.join(__dirname, ".env.example");

// Legacy location -- read on first run to migrate, then ignored
const LEGACY_ENV_PATH = path.join(__dirname, ".env");

function ensureConfigDir() {
  if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
    try { fs.chmodSync(CONFIG_DIR, 0o700); } catch {}
  }
}

function migrateLegacyEnv() {
  if (!fs.existsSync(LEGACY_ENV_PATH) || fs.existsSync(ENV_PATH)) return;
  try {
    ensureConfigDir();
    fs.copyFileSync(LEGACY_ENV_PATH, ENV_PATH);
    try { fs.chmodSync(ENV_PATH, 0o600); } catch {}
    console.log(`Migrated legacy .env -> ${ENV_PATH}`);
  } catch (e) {
    console.error(`Could not migrate legacy .env: ${e.message}`);
  }
}

migrateLegacyEnv();

// ---------------------------------------------------------------------------
// .env read / write (Claude Cowork / dotenv fallback)
// ---------------------------------------------------------------------------

function readEnv() {
  if (!fs.existsSync(ENV_PATH)) return {};
  const out = {};
  for (const line of fs.readFileSync(ENV_PATH, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    out[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
  }
  return out;
}

function writeEnv(values) {
  ensureConfigDir();
  let header = "";
  if (fs.existsSync(EXAMPLE_PATH)) {
    for (const line of fs.readFileSync(EXAMPLE_PATH, "utf8").split("\n")) {
      if (line.startsWith("#")) header += line + "\n";
      else break;
    }
  }
  const body = Object.entries(values)
    .map(([k, v]) => `${k}=${v}`)
    .join("\n") + "\n";
  fs.writeFileSync(ENV_PATH, header + body, "utf8");
  try {
    fs.chmodSync(ENV_PATH, 0o600);
  } catch {}
}

// ---------------------------------------------------------------------------
// ~/.claude/settings.json merge (Claude Code global env)
// Touches only the "env" key — all other settings are preserved exactly.
// ---------------------------------------------------------------------------

function mergeIntoClaudeSettings(envVars) {
  const settingsDir = path.join(os.homedir(), ".claude");
  const settingsPath = path.join(settingsDir, "settings.json");

  let settings = {};
  if (fs.existsSync(settingsPath)) {
    try {
      settings = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
    } catch {
      console.warn(`Warning: Could not parse ${settingsPath} — skipping Claude Code settings update.`);
      return null;
    }
  } else {
    fs.mkdirSync(settingsDir, { recursive: true });
  }

  settings.env = { ...(settings.env ?? {}), ...envVars };
  fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\n", "utf8");
  return settingsPath;
}

// ---------------------------------------------------------------------------
// Input helpers (hides input like getpass)
// ---------------------------------------------------------------------------

function prompt(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

async function hiddenInput(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: true,
    });
    process.stdout.write(question);

    let input = "";
    process.stdin.setRawMode?.(true);
    process.stdin.resume();
    process.stdin.setEncoding("utf8");

    const onData = (char) => {
      if (char === "\n" || char === "\r" || char === "") {
        process.stdin.setRawMode?.(false);
        process.stdin.pause();
        process.stdin.removeListener("data", onData);
        process.stdout.write("\n");
        rl.close();
        resolve(input);
      } else if (char === "") {
        input = input.slice(0, -1);
      } else {
        input += char;
      }
    };

    process.stdin.on("data", onData);
  });
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

async function validateGemini(key) {
  if (!key || key.length < 20) return { ok: false, msg: "Key too short to be a real Gemini key." };
  try {
    const resp = await fetch(
      `https://generativelanguage.googleapis.com/v1/models?key=${encodeURIComponent(key)}&pageSize=1`,
      { signal: AbortSignal.timeout(10000) }
    );
    if (resp.status === 200) return { ok: true, msg: "Validated against Gemini API -- key works." };
    if (resp.status === 401 || resp.status === 403)
      return { ok: false, msg: "Gemini rejected the key (401/403). Verify at https://aistudio.google.com/apikey" };
    return { ok: false, msg: `Unexpected response ${resp.status} from Gemini API.` };
  } catch (err) {
    return { ok: true, msg: `Network check skipped (${err.message}). Key saved; re-run --check to verify.` };
  }
}

async function validateOpenAI(key) {
  if (!key || key.length < 20) return { ok: false, msg: "Key too short to be a real OpenAI key." };
  if (!key.startsWith("sk-")) return { ok: false, msg: "Doesn't look like an OpenAI key (expected to start with sk-)." };
  try {
    const resp = await fetch("https://api.openai.com/v1/models?limit=1", {
      headers: { "Authorization": `Bearer ${key}` },
      signal: AbortSignal.timeout(10000),
    });
    if (resp.status === 200) return { ok: true, msg: "Validated against OpenAI API -- key works." };
    if (resp.status === 401) return { ok: false, msg: "OpenAI rejected the key (401). Verify at https://platform.openai.com/api-keys" };
    if (resp.status === 429) return { ok: true, msg: "Key authenticated (got 429 rate-limit; OpenAI accepted the key)." };
    return { ok: false, msg: `Unexpected response ${resp.status} from OpenAI API.` };
  } catch (err) {
    return { ok: true, msg: `Network check skipped (${err.message}). Key saved; re-run --check to verify.` };
  }
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

async function cmdSetFal() {
  console.log("\nfal.ai API key setup for slot-art-creator-node");
  console.log("----------------------------------------------");
  console.log("Get a key at https://fal.ai/dashboard");
  console.log("Input is hidden; paste your key and press Enter.\n");

  const key = await hiddenInput("FAL_KEY: ");
  if (!key) { console.log("No key entered. Nothing written."); return 1; }
  if (key.length < 10) { console.log("FAIL: Key looks too short."); return 1; }

  const values = readEnv();
  values["FAL_KEY"] = key;
  writeEnv(values);
  const claudePath = mergeIntoClaudeSettings({ FAL_KEY: key });

  console.log(`\nWrote ${ENV_PATH}`);
  if (claudePath) console.log(`Wrote ${claudePath} (shared across all marketplace plugins)`);
  console.log("fal.ai will handle all 4 tools. If you also set GEMINI_API_KEY,");
  console.log("generate/edit/upscale switch to Gemini and smart_resize stays on fal.ai.");
  return 0;
}

async function cmdSetGemini() {
  console.log("\nGemini API key setup for slot-art-creator-node");
  console.log("-----------------------------------------------");
  console.log("Get a key at https://aistudio.google.com/apikey");
  console.log("Input is hidden; paste your key and press Enter.\n");

  const key = await hiddenInput("GEMINI_API_KEY: ");
  if (!key) { console.log("No key entered. Nothing written."); return 1; }

  const { ok, msg } = await validateGemini(key);
  console.log(`${ok ? "OK" : "FAIL"}: ${msg}`);
  if (!ok) return 1;

  const values = readEnv();
  values["GEMINI_API_KEY"] = key;
  writeEnv(values);
  // Write both GEMINI_API_KEY and GOOGLE_API_KEY — different Google APIs use different names
  const claudePath = mergeIntoClaudeSettings({ GEMINI_API_KEY: key, GOOGLE_API_KEY: key });

  console.log(`\nWrote ${ENV_PATH}`);
  if (claudePath) console.log(`Wrote ${claudePath} (GEMINI_API_KEY + GOOGLE_API_KEY, shared across all marketplace plugins)`);
  console.log("Gemini will handle all 4 tools. smart_resize uses Gemini's NB2 +");
  console.log("pngjs center-crop path (one call per target size). If you also set FAL_KEY,");
  console.log("smart_resize switches to fal.ai's purpose-built endpoint (NB Pro, single call).");
  return 0;
}

async function cmdSetOpenAI() {
  console.log("\nOpenAI API key setup for slot-art-creator-node");
  console.log("-----------------------------------------------");
  console.log("Get a key at https://platform.openai.com/api-keys");
  console.log("Input is hidden; paste your key and press Enter.\n");

  const key = await hiddenInput("OPENAI_API_KEY: ");
  if (!key) { console.log("No key entered. Nothing written."); return 1; }

  const { ok, msg } = await validateOpenAI(key);
  console.log(`${ok ? "OK" : "FAIL"}: ${msg}`);
  if (!ok) return 1;

  const values = readEnv();
  values["OPENAI_API_KEY"] = key;
  writeEnv(values);
  const claudePath = mergeIntoClaudeSettings({ OPENAI_API_KEY: key });

  console.log(`\nWrote ${ENV_PATH}`);
  if (claudePath) console.log(`Wrote ${claudePath} (shared across all marketplace plugins)`);
  console.log("OpenAI's gpt-image-2 is now available via gpt2_generate and gpt2_edit.");
  console.log("Note: gpt-image-2 is more expensive than NB2 -- use it for text-heavy");
  console.log("assets (paytables, logos) and hero composition, not routine symbols.");
  return 0;
}

async function cmdCheck() {
  const dotenvValues = readEnv();
  const claudeEnv = (() => {
    const sp = path.join(os.homedir(), ".claude", "settings.json");
    try { return JSON.parse(fs.readFileSync(sp, "utf8")).env ?? {}; } catch { return {}; }
  })();

  // Prefer settings.json (Claude Code path), fall back to .env, then process.env
  const resolve = (k) =>
    claudeEnv[k] || dotenvValues[k] || process.env[k] || "";

  const falKey = resolve("FAL_KEY");
  const geminiKey = resolve("GEMINI_API_KEY") || resolve("GOOGLE_API_KEY");
  const openaiKey = resolve("OPENAI_API_KEY");

  console.log("\nKey status:");
  console.log("-----------");

  if (geminiKey) {
    const { ok, msg } = await validateGemini(geminiKey);
    const src = claudeEnv["GEMINI_API_KEY"] ? "settings.json" : dotenvValues["GEMINI_API_KEY"] ? ".env" : "process.env";
    console.log(`GEMINI_API_KEY  ${ok ? "OK" : "FAIL"}: ${msg} [source: ${src}]`);
  } else {
    console.log("GEMINI_API_KEY  MISSING -- run: node setup-keys.js --gemini");
  }

  if (falKey) {
    const src = claudeEnv["FAL_KEY"] ? "settings.json" : dotenvValues["FAL_KEY"] ? ".env" : "process.env";
    console.log(`FAL_KEY         OK: present (length ${falKey.length}) [source: ${src}]`);
  } else {
    console.log("FAL_KEY         MISSING -- run: node setup-keys.js --fal");
  }

  if (openaiKey) {
    const { ok, msg } = await validateOpenAI(openaiKey);
    const src = claudeEnv["OPENAI_API_KEY"] ? "settings.json" : dotenvValues["OPENAI_API_KEY"] ? ".env" : "process.env";
    console.log(`OPENAI_API_KEY  ${ok ? "OK" : "FAIL"}: ${msg} [source: ${src}]`);
  } else {
    console.log("OPENAI_API_KEY  MISSING (optional -- only needed for gpt2_generate / gpt2_edit)");
  }

  // Routing summary
  console.log("");
  if (!falKey && !geminiKey && !openaiKey) {
    console.log("No keys set. At least one of GEMINI_API_KEY or FAL_KEY is required for the NB2 tools.");
    return 1;
  }

  console.log("NB2 tools (nb2_generate / nb2_edit / nb2_upscale / nb2_smart_resize):");
  if (!falKey && !geminiKey) {
    console.log("  Disabled -- neither GEMINI_API_KEY nor FAL_KEY is set.");
  } else if (geminiKey && falKey) {
    console.log("  generate / edit / upscale  -> Gemini");
    console.log("  smart_resize               -> fal.ai (NB Pro endpoint)");
  } else if (geminiKey) {
    console.log("  All 4 tools route through Gemini.");
  } else {
    console.log("  All 4 tools route through fal.ai.");
  }

  console.log("");
  console.log("GPT Image 2 tools (gpt2_generate / gpt2_edit):");
  if (openaiKey) {
    console.log("  Enabled -- gpt-image-2 available.");
  } else {
    console.log("  Disabled -- set OPENAI_API_KEY to enable.");
  }

  return 0;
}

async function cmdClearFal() {
  const values = readEnv();
  if (!values["FAL_KEY"]) { console.log("No FAL_KEY to clear."); return 0; }
  values["FAL_KEY"] = "";
  writeEnv(values);
  mergeIntoClaudeSettings({ FAL_KEY: "" });
  console.log(`Cleared FAL_KEY in ${ENV_PATH} and ~/.claude/settings.json`);
  return 0;
}

async function cmdClearGemini() {
  const values = readEnv();
  if (!values["GEMINI_API_KEY"]) { console.log("No GEMINI_API_KEY to clear."); return 0; }
  values["GEMINI_API_KEY"] = "";
  writeEnv(values);
  mergeIntoClaudeSettings({ GEMINI_API_KEY: "", GOOGLE_API_KEY: "" });
  console.log(`Cleared GEMINI_API_KEY in ${ENV_PATH} and ~/.claude/settings.json`);
  return 0;
}

async function cmdClearOpenAI() {
  const values = readEnv();
  if (!values["OPENAI_API_KEY"]) { console.log("No OPENAI_API_KEY to clear."); return 0; }
  values["OPENAI_API_KEY"] = "";
  writeEnv(values);
  mergeIntoClaudeSettings({ OPENAI_API_KEY: "" });
  console.log(`Cleared OPENAI_API_KEY in ${ENV_PATH} and ~/.claude/settings.json`);
  return 0;
}

async function cmdInteractive() {
  console.log("\nslot-art-creator-node -- API key setup");
  console.log("======================================");
  console.log("Keys are written to ~/.claude/settings.json (shared across all");
  console.log("plugins in the marketplace) AND ~/.h5g-slot-art-creator/.env");
  console.log("(Claude Cowork / dotenv fallback).");
  console.log("");
  console.log("  NB2 family (Nano Banana 2):");
  console.log("    GEMINI_API_KEY  -- Google AI Studio. Direct API, same NB2 model as fal.");
  console.log("    FAL_KEY         -- fal.ai. Wraps NB2 plus a purpose-built smart-resize");
  console.log("                       endpoint (Nano Banana Pro).");
  console.log("    Either alone runs all 4 NB2 tools. Both routes each tool to its");
  console.log("    strongest backend.");
  console.log("");
  console.log("  GPT Image 2 family (separate model, OpenAI-only):");
  console.log("    OPENAI_API_KEY  -- Enables gpt2_generate / gpt2_edit.");
  console.log("");

  const choice = await prompt("Which key(s) would you like to set? [1] GEMINI  [2] FAL  [3] OPENAI  [4] NB2 (Gemini+FAL)  [5] all three  > ");

  if (choice === "5") {
    await cmdSetGemini();
    await cmdSetFal();
    await cmdSetOpenAI();
  } else if (choice === "4") {
    await cmdSetGemini();
    await cmdSetFal();
  } else if (choice === "3") {
    await cmdSetOpenAI();
  } else if (choice === "2") {
    await cmdSetFal();
  } else {
    await cmdSetGemini();
  }
  return 0;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);

let rc = 0;
if (args.includes("--check")) {
  rc = await cmdCheck();
} else if (args.includes("--clear-fal")) {
  rc = await cmdClearFal();
} else if (args.includes("--clear-gemini")) {
  rc = await cmdClearGemini();
} else if (args.includes("--clear-openai")) {
  rc = await cmdClearOpenAI();
} else if (args.includes("--fal")) {
  rc = await cmdSetFal();
} else if (args.includes("--gemini")) {
  rc = await cmdSetGemini();
} else if (args.includes("--openai")) {
  rc = await cmdSetOpenAI();
} else {
  rc = await cmdInteractive();
}

process.exit(rc);
