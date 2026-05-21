#!/usr/bin/env node
/**
 * register-marketplace.js
 *
 * Idempotently registers slot-art-creator-node with Claude Code so the
 * plugin shows up in the plugin marketplace flow after a fresh install.
 * Called by install.bat and install.sh.
 *
 * What this does (all idempotent — safe to re-run):
 *   1. Ensures the local Claude Code marketplace manifest exists and lists
 *      this plugin.
 *   2. Ensures `~/.claude/settings.json` has the `h5g-plugins` marketplace
 *      registered under `extraKnownMarketplaces`.
 *   3. (Optional) Adds `slot-art-creator-node@h5g-plugins: true` under
 *      `enabledPlugins` if invoked with --enable.
 *
 * Pulls plugin name / version / description directly from plugin.json so
 * everything stays in sync.
 *
 * Usage (from within the plugin folder):
 *   node tools/register-marketplace.js              # register only
 *   node tools/register-marketplace.js --enable     # register + enable
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { fileURLToPath } from "url";

const MARKETPLACE_NAME = "h5g-plugins";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = path.resolve(__dirname, "..");
const PLUGIN_JSON_PATH = path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json");

const HOME = os.homedir();
// Historical local marketplace location used by this installer for Claude Code.
// This is not a documented Claude Cowork user install path.
const MARKETPLACE_DIR = path.join(HOME, "Documents", "Claude_Plugins");
const MARKETPLACE_JSON = path.join(MARKETPLACE_DIR, ".claude-plugin", "marketplace.json");
const SETTINGS_DIR = path.join(HOME, ".claude");
const SETTINGS_JSON = path.join(SETTINGS_DIR, "settings.json");

const args = process.argv.slice(2);
const SHOULD_ENABLE = args.includes("--enable");

// ---------- helpers ----------

function readJson(p) {
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, "utf8"));
  } catch (e) {
    console.error(`  WARNING: ${p} exists but is not valid JSON: ${e.message}`);
    return null;
  }
}

function writeJsonAtomic(p, obj) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  const tmp = p + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 2) + "\n", "utf8");
  fs.renameSync(tmp, p);
}

function log(msg) {
  console.log(`  ${msg}`);
}

// ---------- read our own plugin.json (source of truth) ----------

const myPlugin = readJson(PLUGIN_JSON_PATH);
if (!myPlugin || !myPlugin.name || !myPlugin.version) {
  console.error("ERROR: cannot read this plugin's plugin.json");
  console.error(`  expected: ${PLUGIN_JSON_PATH}`);
  process.exit(1);
}

const PLUGIN_NAME = myPlugin.name;
const PLUGIN_VERSION = myPlugin.version;
const PLUGIN_DESCRIPTION = myPlugin.description || "";

console.log("");
console.log(`Registering ${PLUGIN_NAME} v${PLUGIN_VERSION}`);
console.log("");

// ---------- step 1: marketplace.json ----------

let marketplace = readJson(MARKETPLACE_JSON);
if (!marketplace) {
  marketplace = {
    name: MARKETPLACE_NAME,
    owner: { name: "High 5 Games" },
    plugins: [],
  };
  log(`creating marketplace.json at ${MARKETPLACE_JSON}`);
}

// Ensure plugins array exists
marketplace.plugins = Array.isArray(marketplace.plugins) ? marketplace.plugins : [];

const pluginEntry = {
  name: PLUGIN_NAME,
  source: `./${PLUGIN_NAME}`,
  description: PLUGIN_DESCRIPTION,
  version: PLUGIN_VERSION,
};

const existingIndex = marketplace.plugins.findIndex((p) => p.name === PLUGIN_NAME);
if (existingIndex >= 0) {
  const existing = marketplace.plugins[existingIndex];
  if (
    existing.version !== pluginEntry.version ||
    existing.description !== pluginEntry.description ||
    existing.source !== pluginEntry.source
  ) {
    marketplace.plugins[existingIndex] = pluginEntry;
    log(`updated existing ${PLUGIN_NAME} entry in marketplace.json`);
  } else {
    log(`marketplace.json already has ${PLUGIN_NAME} v${PLUGIN_VERSION} — no change`);
  }
} else {
  marketplace.plugins.push(pluginEntry);
  log(`added ${PLUGIN_NAME} to marketplace.json`);
}

// Also normalize: ensure the marketplace 'name' field matches our convention
if (marketplace.name !== MARKETPLACE_NAME) {
  marketplace.name = MARKETPLACE_NAME;
  log(`set marketplace name to ${MARKETPLACE_NAME}`);
}

writeJsonAtomic(MARKETPLACE_JSON, marketplace);

// ---------- step 2: settings.json — extraKnownMarketplaces ----------

let settings = readJson(SETTINGS_JSON);
if (!settings) {
  settings = {};
  log(`creating settings.json at ${SETTINGS_JSON}`);
}

settings.extraKnownMarketplaces = settings.extraKnownMarketplaces || {};

const desiredMarketplaceEntry = {
  source: { source: "directory", path: MARKETPLACE_DIR },
};

const currentEntry = settings.extraKnownMarketplaces[MARKETPLACE_NAME];
if (
  !currentEntry ||
  !currentEntry.source ||
  currentEntry.source.path !== MARKETPLACE_DIR
) {
  settings.extraKnownMarketplaces[MARKETPLACE_NAME] = desiredMarketplaceEntry;
  log(`registered ${MARKETPLACE_NAME} marketplace in settings.json`);
} else {
  log(`${MARKETPLACE_NAME} marketplace already registered in settings.json — no change`);
}

// ---------- step 3 (optional): enable the plugin ----------

if (SHOULD_ENABLE) {
  settings.enabledPlugins = settings.enabledPlugins || {};
  const enableKey = `${PLUGIN_NAME}@${MARKETPLACE_NAME}`;
  if (settings.enabledPlugins[enableKey] === true) {
    log(`${enableKey} already enabled in settings.json — no change`);
  } else {
    settings.enabledPlugins[enableKey] = true;
    log(`enabled ${enableKey} in settings.json`);
  }
}

writeJsonAtomic(SETTINGS_JSON, settings);

// ---------- done ----------

console.log("");
if (SHOULD_ENABLE) {
  console.log("Plugin registered AND enabled.");
  console.log("Restart Claude Code (Ctrl+Shift+P > Developer: Reload Window) to activate.");
} else {
  console.log("Plugin registered (not yet enabled).");
  console.log(`To enable: in Claude Code, type /plugin and select ${PLUGIN_NAME}.`);
  console.log(`Or re-run with --enable: node tools/register-marketplace.js --enable`);
}
console.log("");
