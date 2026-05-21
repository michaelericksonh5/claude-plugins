#!/usr/bin/env node
import { createHash, randomUUID } from "node:crypto";
import { createReadStream, promises as fs } from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const TOOL = "h5g-runtime-acceptance-probe";
const TOOL_VERSION = "runtime-acceptance-probe-v1";
const RUNTIME_NAME = "@esotericsoftware/spine-player";
const RUNTIME_VERSION = "4.3.1";
const PACKAGE_ARTIFACTS = ["shared_symbols.json", "shared_symbols.atlas", "shared_symbols.png"];

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.resolve(__dirname, "..");
const require = createRequire(import.meta.url);

function parseArgs(argv) {
  const opts = {
    packageDirs: [],
    packagesRoot: path.join(pluginRoot, "generated", "runtime_acceptance", "packages"),
    outDir: path.join(pluginRoot, "generated", "runtime_acceptance", "probe"),
    timeoutMs: 30000,
    browserChannel: null,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      i += 1;
      if (i >= argv.length) throw new Error(`${arg} requires a value`);
      return argv[i];
    };
    if (arg === "--package-dir") opts.packageDirs.push(path.resolve(next()));
    else if (arg === "--packages-root") opts.packagesRoot = path.resolve(next());
    else if (arg === "--out-dir") opts.outDir = path.resolve(next());
    else if (arg === "--timeout-ms") opts.timeoutMs = Number(next());
    else if (arg === "--browser-channel") opts.browserChannel = next();
    else throw new Error(`unknown argument: ${arg}`);
  }
  return opts;
}

async function discoverPackageDirs(opts) {
  if (opts.packageDirs.length) return opts.packageDirs;
  const entries = await fs.readdir(opts.packagesRoot, { withFileTypes: true });
  const dirs = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const packageDir = path.join(opts.packagesRoot, entry.name);
    try {
      await fs.access(path.join(packageDir, "preview.html"));
      dirs.push(packageDir);
    } catch {
      // Not a preview package.
    }
  }
  return dirs.sort();
}

async function sha256(filePath) {
  const hash = createHash("sha256");
  await new Promise((resolve, reject) => {
    createReadStream(filePath)
      .on("data", chunk => hash.update(chunk))
      .on("error", reject)
      .on("end", resolve);
  });
  return hash.digest("hex");
}

async function packageIdentity(packageDir) {
  const identity = {};
  for (const artifact of PACKAGE_ARTIFACTS) {
    identity[artifact] = { sha256: await sha256(path.join(packageDir, artifact)) };
  }
  return identity;
}

function walkAttachments(skel) {
  const out = [];
  for (const skin of skel.skins || []) {
    for (const slotAttachments of Object.values(skin.attachments || {})) {
      for (const attachment of Object.values(slotAttachments || {})) out.push(attachment);
    }
  }
  return out;
}

function detectFeatures(skel, validationReport) {
  const attachments = walkAttachments(skel);
  return {
    skins: Array.isArray(skel.skins) && skel.skins.length > 0,
    physics: Array.isArray(skel.physics) && skel.physics.length > 0,
    sequences: attachments.some(attachment => attachment && typeof attachment === "object" && attachment.sequence),
    clipping: Number(validationReport.clipping_attachments_emitted || 0) > 0
      || attachments.some(attachment => attachment && attachment.type === "clipping"),
    events: Object.keys(skel.events || {}).length > 0 || Number(validationReport.events_defined || 0) > 0,
    blends: (skel.slots || []).some(slot => slot.blend && slot.blend !== "normal"),
  };
}

async function startStaticServer(root) {
  const allowedFiles = new Set([
    "preview.html",
    "shared_symbols.json",
    "shared_symbols.atlas",
    "shared_symbols.png",
  ]);
  const server = http.createServer(async (req, res) => {
    let urlPath;
    try {
      urlPath = decodeURIComponent(new URL(req.url || "/", "http://127.0.0.1").pathname);
    } catch {
      res.writeHead(400);
      res.end("bad request");
      return;
    }
    if (urlPath === "/favicon.ico") {
      res.writeHead(204);
      res.end();
      return;
    }
    const requestedName = urlPath === "/" ? "preview.html" : urlPath.replace(/^\/+/, "");
    if (!allowedFiles.has(requestedName)) {
      res.writeHead(404);
      res.end("not found");
      return;
    }
    const requested = path.normalize(path.join(root, requestedName));
    const relative = path.relative(root, requested);
    if (relative.startsWith("..") || path.isAbsolute(relative)) {
      res.writeHead(403);
      res.end("forbidden");
      return;
    }
    try {
      const data = await fs.readFile(requested);
      const ext = path.extname(requested).toLowerCase();
      const contentType = {
        ".html": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".atlas": "text/plain; charset=utf-8",
        ".png": "image/png",
      }[ext] || "application/octet-stream";
      res.writeHead(200, { "content-type": contentType });
      res.end(data);
    } catch {
      res.writeHead(404);
      res.end("not found");
    }
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  return {
    url: `http://127.0.0.1:${address.port}/preview.html`,
    close: () => new Promise(resolve => server.close(resolve)),
  };
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch (directImportError) {
    for (const entry of (process.env.PATH || "").split(path.delimiter)) {
      if (!entry.endsWith(path.join("node_modules", ".bin"))) continue;
      const packageDir = path.join(path.dirname(entry), "playwright");
      try {
        return require(packageDir);
      } catch {
        // Keep searching npm/npx-provided PATH entries.
      }
    }
    throw directImportError;
  }
}

async function launchBrowser(playwright, opts) {
  const { chromium } = playwright;
  if (opts.browserChannel) {
    return chromium.launch({ channel: opts.browserChannel, headless: true });
  }
  try {
    return await chromium.launch({ channel: "msedge", headless: true });
  } catch {
    return chromium.launch({ headless: true });
  }
}

async function probePackage(browser, packageDir, opts) {
  const name = path.basename(packageDir);
  const skel = JSON.parse(await fs.readFile(path.join(packageDir, "shared_symbols.json"), "utf8"));
  let validationReport = {};
  try {
    validationReport = JSON.parse(await fs.readFile(path.join(packageDir, "validation_report.json"), "utf8"));
  } catch {
    validationReport = {};
  }

  const consoleErrors = [];
  const pageErrors = [];
  const requestFailures = [];
  const server = await startStaticServer(packageDir);
  const page = await browser.newPage();
  page.on("console", msg => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", error => pageErrors.push(String(error.message || error)));
  page.on("requestfailed", request => {
    requestFailures.push({
      url: request.url(),
      failure: request.failure()?.errorText || "request failed",
    });
  });

  let canvasCount = 0;
  let spinePlayerLoaded = false;
  let previewState = null;
  let packageLoaded = false;
  const screenshotPath = path.join(opts.outDir, "screenshots", `${name}.png`);
  try {
    await page.goto(server.url, { waitUntil: "domcontentloaded", timeout: opts.timeoutMs });
    await page.waitForFunction(() => Boolean(window.spine && window.spine.SpinePlayer), null, { timeout: opts.timeoutMs });
    spinePlayerLoaded = true;
    await page.waitForSelector("canvas", { timeout: opts.timeoutMs });
    await page.waitForTimeout(500);
    canvasCount = await page.locator("canvas").count();
    previewState = await page.evaluate(() => window.__h5gSpinePreviewState || null);
    await fs.mkdir(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ path: screenshotPath, fullPage: true });
    packageLoaded = spinePlayerLoaded
      && canvasCount > 0
      && consoleErrors.length === 0
      && pageErrors.length === 0
      && requestFailures.length === 0
      && !(previewState && previewState.status === "error");
  } finally {
    await page.close();
    await server.close();
  }

  const evidence = {
    schema: "spine_slot_animation_runtime_acceptance_evidence_v1",
    runtime_name: RUNTIME_NAME,
    runtime_version: RUNTIME_VERSION,
    provenance: {
      method: "runtime_probe",
      tool: TOOL,
      tool_version: TOOL_VERSION,
      execution_mode: "browser_runtime",
      execution_id: randomUUID(),
      executed_at: new Date().toISOString(),
    },
    package_loaded: packageLoaded,
    features_loaded: detectFeatures(skel, validationReport),
    package_identity: await packageIdentity(packageDir),
  };
  const details = {
    schema: "spine_slot_animation_runtime_acceptance_probe_details_v1",
    package_dir: packageDir,
    preview_url: server.url,
    screenshot: screenshotPath,
    spine_player_loaded: spinePlayerLoaded,
    canvas_count: canvasCount,
    preview_state: previewState,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    request_failures: requestFailures,
  };
  await fs.writeFile(path.join(packageDir, "runtime_acceptance.json"), JSON.stringify(evidence, null, 2));
  await fs.writeFile(path.join(packageDir, "runtime_acceptance_probe_details.json"), JSON.stringify(details, null, 2));
  await fs.mkdir(path.join(opts.outDir, "evidence"), { recursive: true });
  await fs.writeFile(path.join(opts.outDir, "evidence", `${name}.runtime_acceptance.json`), JSON.stringify(evidence, null, 2));
  await fs.writeFile(path.join(opts.outDir, "evidence", `${name}.details.json`), JSON.stringify(details, null, 2));
  return { name, package_dir: packageDir, status: packageLoaded ? "verified_browser_runtime" : "failed", evidence, details };
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const packageDirs = await discoverPackageDirs(opts);
  if (!packageDirs.length) throw new Error("no preview packages found");
  await fs.mkdir(opts.outDir, { recursive: true });
  const playwright = await loadPlaywright();
  const browser = await launchBrowser(playwright, opts);
  const results = [];
  try {
    for (const packageDir of packageDirs) {
      results.push(await probePackage(browser, packageDir, opts));
    }
  } finally {
    await browser.close();
  }
  const report = {
    schema: "spine_slot_animation_runtime_acceptance_probe_report_v1",
    tool: TOOL,
    tool_version: TOOL_VERSION,
    execution_mode: "browser_runtime",
    package_count: results.length,
    status: results.every(result => result.status === "verified_browser_runtime")
      ? "verified_browser_runtime"
      : "failed",
    packages: results,
  };
  const reportPath = path.join(opts.outDir, "runtime_acceptance_probe_report.json");
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ status: report.status, report: reportPath }, null, 2));
  return report.status === "verified_browser_runtime" ? 0 : 2;
}

main().then(
  code => { process.exitCode = code; },
  error => {
    console.error(error && error.stack ? error.stack : String(error));
    process.exitCode = 1;
  },
);
