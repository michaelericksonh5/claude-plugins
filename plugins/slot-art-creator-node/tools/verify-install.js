#!/usr/bin/env node
/**
 * verify-install.js
 *
 * Final post-install verification for the Claude Code marketplace flow —
 * reads the actual on-disk state and reports a clean PASS or FAIL so
 * coworkers running install.bat / install.sh have unambiguous confirmation
 * that everything's wired correctly.
 *
 * Checks:
 *   1. Plugin manifest exists at the source the user ran the installer from
 *   2. Plugin folder copied to the local Claude Code marketplace source
 *   3. ~/.claude/settings.json has the h5g-plugins marketplace registered
 *   4. ~/.claude/settings.json has slot-art-creator-node enabled
 *   5. The local marketplace manifest lists the plugin
 *   6. ~/.h5g-slot-art-creator/.env exists with at least one key
 *
 * Exit code: 0 if everything is good, 1 otherwise.
 *
 * Output: human-readable status table + a final PASS/FAIL banner.
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = path.resolve(__dirname, "..");
const HOME = os.homedir();

const PLUGIN_NAME = "slot-art-creator-node";
const MARKETPLACE_NAME = "h5g-plugins";

// Historical local marketplace location used by this installer for Claude Code.
// This is not a documented Claude Cowork user install path.
const MARKETPLACE_DIR = path.join(HOME, "Documents", "Claude_Plugins");
const CODE_PLUGIN_SOURCE = path.join(MARKETPLACE_DIR, PLUGIN_NAME);
const LEGACY_DIRECT_PLUGIN = path.join(HOME, ".claude", "plugins", PLUGIN_NAME);
const SETTINGS_PATH    = path.join(HOME, ".claude", "settings.json");
const MARKETPLACE_PATH = path.join(MARKETPLACE_DIR, ".claude-plugin", "marketplace.json");
const ENV_PATH         = path.join(HOME, ".h5g-slot-art-creator", ".env");

const checks = [];
let failures = 0;
let warnings = 0;

function pass(label, detail = "") {
  checks.push({ status: "PASS", label, detail });
}
function fail(label, detail = "") {
  checks.push({ status: "FAIL", label, detail });
  failures++;
}
function warn(label, detail = "") {
  checks.push({ status: "WARN", label, detail });
  warnings++;
}

// ---------- Check 1: source plugin folder is intact ----------
const manifestPath = path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json");
if (fs.existsSync(manifestPath)) {
  try {
    const m = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    pass("Source plugin manifest", `${m.name} v${m.version}`);
  } catch (e) {
    fail("Source plugin manifest", `corrupt JSON: ${e.message}`);
  }
} else {
  fail("Source plugin manifest", `not found at ${manifestPath}`);
}

// ---------- Optional: Claude CLI plugin validation ----------
const claudeLookup = spawnSync(process.platform === "win32" ? "where" : "which", ["claude"], {
  encoding: "utf8",
  shell: false,
});
if (claudeLookup.status !== 0) {
  warn("Claude CLI plugin validation", "claude CLI not found; skipped optional `claude plugin validate`");
} else {
  const claudePath = claudeLookup.stdout.trim().split(/\r?\n/)[0] || "claude";
  const claudeValidate = spawnSync(claudePath, ["plugin", "validate", PLUGIN_ROOT], { encoding: "utf8" });
  if (claudeValidate.status === 0) {
    pass("Claude CLI plugin validation", "`claude plugin validate` passed");
  } else {
    const output = `${claudeValidate.stderr || ""}${claudeValidate.stdout || ""}`.trim();
    fail("Claude CLI plugin validation", output || `claude exited with status ${claudeValidate.status}`);
  }
}

// ---------- Check 2: plugin folder copied to the local Code marketplace ----------
if (fs.existsSync(path.join(CODE_PLUGIN_SOURCE, ".claude-plugin", "plugin.json"))) {
  pass("Code marketplace plugin source", CODE_PLUGIN_SOURCE);
} else {
  fail("Code marketplace plugin source", `not found at ${CODE_PLUGIN_SOURCE}`);
}
if (fs.existsSync(path.join(LEGACY_DIRECT_PLUGIN, ".claude-plugin", "plugin.json"))) {
  warn("Legacy direct Claude Code copy",
    `${LEGACY_DIRECT_PLUGIN} exists; current documented flow uses the marketplace source above`);
}

// ---------- Check 3 + 4: settings.json marketplace registration + enabled flag ----------
let settings = null;
if (!fs.existsSync(SETTINGS_PATH)) {
  fail("settings.json", `does not exist at ${SETTINGS_PATH}`);
} else {
  try {
    settings = JSON.parse(fs.readFileSync(SETTINGS_PATH, "utf8"));
  } catch (e) {
    fail("settings.json", `corrupt JSON: ${e.message}`);
  }
}
if (settings) {
  const mp = settings.extraKnownMarketplaces?.[MARKETPLACE_NAME];
  if (mp && mp.source && mp.source.path) {
    pass("Marketplace registered in settings.json", `${MARKETPLACE_NAME} -> ${mp.source.path}`);
  } else {
    fail("Marketplace registered in settings.json", `${MARKETPLACE_NAME} not found in extraKnownMarketplaces`);
  }
  const enableKey = `${PLUGIN_NAME}@${MARKETPLACE_NAME}`;
  if (settings.enabledPlugins?.[enableKey] === true) {
    pass("Plugin enabled in settings.json", `${enableKey}: true`);
  } else if (settings.enabledPlugins && Object.keys(settings.enabledPlugins).some((k) => k.startsWith(PLUGIN_NAME))) {
    warn("Plugin enabled in settings.json",
      `found a related entry but not the canonical key. Run: node tools/register-marketplace.js --enable`);
  } else {
    fail("Plugin enabled in settings.json",
      `${enableKey} not in enabledPlugins. Run: node tools/register-marketplace.js --enable`);
  }
}

// ---------- Check 5: marketplace.json declares the plugin ----------
if (!fs.existsSync(MARKETPLACE_PATH)) {
  fail("marketplace.json", `does not exist at ${MARKETPLACE_PATH}`);
} else {
  try {
    const mp = JSON.parse(fs.readFileSync(MARKETPLACE_PATH, "utf8"));
    const entry = (mp.plugins || []).find((p) => p.name === PLUGIN_NAME);
    if (entry && entry.source === `./${PLUGIN_NAME}`) {
      pass("marketplace.json declares plugin", `v${entry.version}`);
    } else if (entry) {
      fail("marketplace.json declares plugin", `source should be ./${PLUGIN_NAME}, found ${entry.source || "(missing)"}`);
    } else {
      fail("marketplace.json declares plugin", `${PLUGIN_NAME} not in plugins[] array`);
    }
  } catch (e) {
    fail("marketplace.json", `corrupt JSON: ${e.message}`);
  }
}

// ---------- Check 6: API keys ----------
if (!fs.existsSync(ENV_PATH)) {
  warn("API keys configured", `~/.h5g-slot-art-creator/.env not found — run: node setup-keys.js`);
} else {
  const envContent = fs.readFileSync(ENV_PATH, "utf8");
  const hasGemini = /^GEMINI_API_KEY\s*=\s*\S+/m.test(envContent);
  const hasFal    = /^FAL_KEY\s*=\s*\S+/m.test(envContent);
  if (hasGemini && hasFal) {
    pass("API keys configured", "GEMINI_API_KEY + FAL_KEY both set (full functionality)");
  } else if (hasGemini) {
    pass("API keys configured", "GEMINI_API_KEY set (smart-resize will use Gemini fallback with local crop)");
  } else if (hasFal) {
    pass("API keys configured", "FAL_KEY set (all 4 tools will use fal.ai)");
  } else {
    warn("API keys configured", "no keys present in .env — run: node setup-keys.js");
  }
}

// ---------- Check 7: Cowork upload ZIP status (informational) ----------
// Claude Cowork is a SEPARATE plugin system from Claude Code. The plugin
// works in Cowork only if the user uploads the packaged .zip via Claude
// Desktop's UI. We can't detect whether they've uploaded it (no API), but
// we CAN detect whether the ZIP is built and ready for them to upload.
const COWORK_ZIP = path.join(PLUGIN_ROOT, "dist", "slot-art-creator-node-cowork-upload.zip");
if (fs.existsSync(COWORK_ZIP)) {
  const stat = fs.statSync(COWORK_ZIP);
  const sizeMb = (stat.size / (1024 * 1024)).toFixed(2);
  pass("Cowork upload ZIP ready", `${COWORK_ZIP} (${sizeMb} MB) — upload in Claude Desktop > Cowork > Customize > Browse plugins`);
} else {
  warn("Cowork upload ZIP", "not built — re-run installer and choose option [1] BOTH, or [3] Cowork only. Cowork sessions can't see the plugin without this manual upload.");
}

// ---------- Print report ----------
console.log("");
console.log(" --- Verification report ---");
const widest = Math.max(...checks.map((c) => c.label.length));
for (const c of checks) {
  const marker = c.status === "PASS" ? " OK " : c.status === "FAIL" ? "FAIL" : "WARN";
  const label = c.label.padEnd(widest);
  const detail = c.detail ? "  " + c.detail : "";
  console.log(`  [${marker}] ${label}${detail}`);
}
console.log("");

if (failures > 0) {
  console.log(" ============================================");
  console.log(" CLAUDE CODE MARKETPLACE CHECK FAILED");
  console.log(" ============================================");
  console.log(` ${failures} check(s) failed. The plugin will NOT load in Claude Code until these are fixed.`);
  console.log("");
  console.log(" Most common fix:  re-run install.bat / install.sh");
  console.log(" Manual fix:       node tools/register-marketplace.js --enable");
  console.log("");
  process.exit(1);
}
if (warnings > 0) {
  console.log(" ============================================");
  console.log(" CLAUDE CODE MARKETPLACE OK with warnings");
  console.log(" ============================================");
  console.log(` ${warnings} warning(s) above. The plugin will load in Claude Code, but some functionality may be limited.`);
  console.log("");
  console.log(" Reload Claude Code (Ctrl+Shift+P > Developer: Reload Window)");
  console.log(" and type /slot- to see the numbered workflow.");
  console.log(" Cowork installs must be verified in Claude Desktop after uploading the ZIP.");
  console.log("");
  process.exit(0);
}
console.log(" ============================================");
console.log(" CLAUDE CODE MARKETPLACE VERIFIED");
console.log(" ============================================");
console.log(" Reload Claude Code (Ctrl+Shift+P > Developer: Reload Window)");
console.log(" and type /slot- to see the 11 numbered workflow commands.");
console.log(" Cowork installs must be verified in Claude Desktop after uploading the ZIP.");
console.log("");
console.log(" Start with:  /slot-step-00  (if you have a GDD on Drive)");
console.log("        or:   /slot-step-01   (fresh concept)");
console.log("");
process.exit(0);
