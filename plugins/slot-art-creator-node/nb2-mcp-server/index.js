/**
 * slot-art-creator-node — MCP server (Node.js)
 *
 * Exposes eight MCP tools across two model families plus a QA helper:
 *
 *   Nano Banana 2 family (Gemini / fal.ai routing):
 *     nb2_generate       — text-to-image
 *     nb2_edit           — image-to-image edit / reskin
 *     nb2_upscale        — 4K upscale (the only TRUE upscale tool here)
 *     nb2_smart_resize   — pixel-perfect multi-size resize
 *
 *   GPT Image 2 family (OpenAI; OPENAI_API_KEY required):
 *     gpt2_generate      — text-to-image at 1K or 2K (gpt-image-2's stable ceiling).
 *                          Use for paytables, logos, banners with copy, hero
 *                          photorealism — anywhere text fidelity matters.
 *     gpt2_edit          — image-to-image edit with optional mask; accepts
 *                          MULTIPLE reference images for compositional editing.
 *
 *   Cross-family helpers:
 *     nb2_stage_image    — copy an external/chat-pasted image into the safe inputs
 *                          folder so it can be used as a source for any of the
 *                          above (gpt2_edit / nb2_edit / nb2_upscale /
 *                          nb2_smart_resize)
 *     nb2_measure        — opt-in measurement on an existing PNG. Returns OKLCH
 *                          dominant colors, fill %, BG uniformity, edge density,
 *                          and bounding box; writes a sidecar <basename>.metrics.json
 *                          next to the image. Generation tools accept `measure: true`
 *                          to auto-run this on each output. Used by /slot-step-08
 *                          to drive numeric audit checks (tier-pairwise saturation
 *                          deltas, LP warmth scan, non-flat-BG detection) instead
 *                          of relying on Claude's eyeball judgment alone.
 *
 *   IMPORTANT:
 *   - gpt-image-2 has NO faithful upscale mode. It always regenerates at the
 *     target size, not super-resolution from a source. For true upscaling
 *     from an approved 2K asset to 4K, use nb2_upscale.
 *   - gpt-image-2's 4K size targets (3840×2160 / 2160×3840) are flagged
 *     experimental by OpenAI — we don't expose them. For genuine 4K marketing
 *     output, generate at 2K via gpt2_generate, then run nb2_upscale.
 *   - For multi-aspect resize / smart-resize, use nb2_smart_resize (fal.ai
 *     NB Pro purpose-built endpoint, or Gemini fallback). A gpt2-based smart
 *     resize was prototyped but not shipped — output quality wasn't verified
 *     against the well-tested fal.ai path.
 *   - output_dir on every tool MUST be an absolute path. The pre-1.5.5
 *     behavior of silently joining a relative path to ~/Pictures/claude_nb2
 *     produced orphaned files when a skill meant to write to a project
 *     subfolder. Skills inside /slot-step-* always pass
 *     path.join(project_root, "<Category>"); ad-hoc callers can omit
 *     output_dir to fall back to ~/Pictures/claude_nb2.
 *
 * EITHER KEY ALONE is fully sufficient for all four tools — both providers have
 * a complete implementation of every tool. With both keys set, the plugin routes
 * each tool to its strongest backend (see below).
 *
 * Routing for generate / edit / upscale:
 *   Both providers wrap the SAME underlying model (Nano Banana 2 =
 *   gemini-3.1-flash-image-preview = fal-ai/nano-banana-2). Output quality is
 *   ~identical. Gemini wins when both keys are set because the direct Google
 *   API call is one hop fewer than going through fal.ai's wrapper.
 *     GEMINI_API_KEY present → Google Gemini (gemini-3.1-flash-image-preview)
 *     FAL_KEY present        → fal.ai (fal-ai/nano-banana-2)
 *     Neither                → startup error with setup instructions
 *
 * Routing for nb2_smart_resize:
 *   The two paths are materially different. fal.ai has a purpose-built endpoint
 *   (Nano Banana Pro under the hood, single API call). Gemini uses NB2 + N calls
 *   + pngjs center-crop, and can fail with "image smaller than target" on some
 *   sizes. fal.ai wins when both keys are present.
 *     FAL_KEY present        → fal.ai (fal-ai/smart-resize, NB Pro)
 *     GEMINI_API_KEY present → Gemini path (NB2 + center-crop)
 *     Neither                → tool returns a clean error message
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  McpError,
  ErrorCode,
} from "@modelcontextprotocol/sdk/types.js";
import { fal } from "@fal-ai/client";
import { GoogleGenAI } from "@google/genai";
import OpenAI from "openai";
import { PNG } from "pngjs";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as net from "net";
import * as http from "http";
import * as https from "https";
import { lookup } from "dns/promises";
import { fileURLToPath } from "url";
import { measureImage, writeSidecar as writeMetricsSidecar } from "./lib/measurements.js";

// ---------------------------------------------------------------------------
// Bootstrap — load .env from plugin root
// ---------------------------------------------------------------------------

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Resolve the plugin root for both layouts:
//   - Unbundled (dev):   __dirname = .../nb2-mcp-server, plugin root = ..
//   - Bundled (esbuild): __dirname = .../nb2-mcp-server/dist, plugin root = ../..
// Walk up until we find .claude-plugin/plugin.json (the canonical marker).
function findPluginRoot(startDir) {
  let dir = startDir;
  for (let i = 0; i < 4; i++) {
    if (fs.existsSync(path.join(dir, ".claude-plugin", "plugin.json"))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  // Fallback for installs where the marker is missing — preserve old behavior.
  return path.resolve(startDir, "..");
}
const PLUGIN_ROOT = findPluginRoot(__dirname);

// Read our own version from package.json so the MCP server identity and the
// User-Agent string for outbound HTTP both stay in sync with the published
// version. We use fs.readFileSync + JSON.parse rather than createRequire to
// avoid an identifier collision with the esbuild bundle banner (which injects
// its own `createRequire` import to make CJS deps like google-auth-library's
// dynamic require() of child_process work). Plain file reads sidestep that
// entire layer.
function readServerVersion() {
  const candidates = [
    path.join(__dirname, "package.json"),                       // unbundled (nb2-mcp-server/index.js)
    path.join(__dirname, "..", "package.json"),                 // bundled (nb2-mcp-server/dist/index.mjs)
    path.join(PLUGIN_ROOT, "nb2-mcp-server", "package.json"),   // any layout via plugin root
  ];
  for (const p of candidates) {
    try {
      const v = JSON.parse(fs.readFileSync(p, "utf8")).version;
      if (v) return v;
    } catch {
      // Try next candidate.
    }
  }
  return "0.0.0";
}
const SERVER_VERSION = readServerVersion();

// Load .env in priority order:
//   1. ~/.h5g-slot-art-creator/.env   (canonical, survives plugin reinstall)
//   2. PLUGIN_ROOT/.env                (legacy / fallback)
// Existing process.env values take precedence over either file (override:false).
try {
  const { default: dotenv } = await import("dotenv");
  const userEnv = path.join(os.homedir(), ".h5g-slot-art-creator", ".env");
  const pluginEnv = path.join(PLUGIN_ROOT, ".env");
  if (fs.existsSync(userEnv)) {
    dotenv.config({ path: userEnv, override: false });
  }
  if (fs.existsSync(pluginEnv)) {
    dotenv.config({ path: pluginEnv, override: false });
  }
} catch {
  // dotenv optional at runtime — env vars may come from the shell
}

// ---------------------------------------------------------------------------
// Resolve output directory.
//
// Contract (v1.5.5+): callers MUST pass an absolute path. Relative paths
// are rejected — the pre-1.5.5 behavior of silently joining a relative
// path to ~/Pictures/claude_nb2 had two real failure modes:
//   1. A skill that meant to write to <project_root>/Symbol_Art/ but passed
//      just "Symbol_Art" would silently land files in
//      ~/Pictures/claude_nb2/Symbol_Art/ — the skill would then record
//      "Symbol_Art/HP1_001.png" in project.json, and every downstream
//      skill would try to read it from the project folder and ENOENT.
//   2. The error mode was silent: the file was created, the path was
//      recorded, the failure surfaced hours later when an upscale or
//      audit tried to read the orphaned record.
//
// Empty `rawOut` still falls back to ~/Pictures/claude_nb2 — that's the
// ad-hoc / no-project use case (someone testing the MCP tools directly
// outside a /slot-step-* skill, or generating a one-off image for
// inspiration). Skills inside the /slot-step-* workflow always pass an
// absolute path joined from the active project root, so this default
// never fires for them.
// ---------------------------------------------------------------------------

function resolveOutputDir(rawOut) {
  if (!rawOut) return path.join(os.homedir(), "Pictures", "claude_nb2");
  const expanded = rawOut.startsWith("~")
    ? path.join(os.homedir(), rawOut.slice(1))
    : rawOut;
  if (path.isAbsolute(expanded)) return expanded;
  throw new Error(
    `output_dir must be absolute. Got: "${rawOut}" (relative).\n` +
    `→ Inside a /slot-step-* skill, pass:\n` +
    `    path.join(project_root, "<Category>")\n` +
    `  where <Category> is one of Key_Art, Symbol_Sheets, Symbol_Art,\n` +
    `  Backgrounds, Avatars, Bezels, HUD, Paytables, Win_Banners,\n` +
    `  Bonus_Screens, Multipliers, Logos, Lobby_Tiles, or QA_Reports.\n` +
    `  See shared/asset_naming.md for the full category list.\n` +
    `→ For ad-hoc generation outside a project workflow, pass an absolute\n` +
    `  path like "~/Pictures/claude_nb2" (tilde is expanded) or omit\n` +
    `  output_dir entirely to fall back to that default.\n` +
    `→ If you don't have an active project yet, run /slot-step-01 to set\n` +
    `  one up — the resulting project_root is the prefix every skill joins.`
  );
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

// Atomically reserve a unique filename. We open the candidate with O_CREAT|O_EXCL
// (Node's "wx" flag) so two concurrent tool calls in the same outDir can never
// both win the same name — one creates a 0-byte placeholder, the other gets
// EEXIST and bumps the counter. The placeholder is overwritten by the caller's
// real write (downloadImage → writeFileSync, or geminiSmartResize's
// writeFileSync) which happens via plain write to the same path. This trades
// one cheap fd churn for race-free concurrency, including across worker
// processes since the kernel enforces the exclusive create.
function uniqueName(outDir, baseName, ext = ".png") {
  ensureDir(outDir);
  let candidate = path.join(outDir, `${baseName}${ext}`);
  let i = 1;
  while (true) {
    try {
      const fd = fs.openSync(candidate, "wx");
      fs.closeSync(fd);
      return candidate;
    } catch (err) {
      if (err.code !== "EEXIST") throw err;
      i += 1;
      candidate = path.join(outDir, `${baseName}_${i}${ext}`);
    }
  }
}

const ALLOWED_IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".webp"]);
const MAX_REMOTE_IMAGE_BYTES = 50 * 1024 * 1024;

function isRemoteUrl(value) {
  return /^https?:\/\//i.test(value);
}

function sanitizeAssetName(rawName, fallback) {
  const value = (rawName || fallback || "image").trim();
  if (value.includes("/") || value.includes("\\") || value.includes("..") || path.basename(value) !== value) {
    throw new Error("asset_name must be a filename only, without path separators or traversal");
  }
  const slug = value
    .replace(/[^A-Za-z0-9._-]+/g, "-")
    .replace(/^[.-]+|[.-]+$/g, "");
  if (!slug) throw new Error("asset_name must include at least one safe filename character");
  return slug;
}

function validateTargetSizes(rawSizes) {
  const sizes = rawSizes || ["2048x2048", "1920x1080", "1080x1920"];
  if (!Array.isArray(sizes) || sizes.length === 0) {
    throw new Error("target_sizes must be a non-empty array of WxH strings");
  }
  return sizes.map((size) => {
    if (typeof size !== "string") {
      throw new Error("target_sizes entries must be strings in WxH format");
    }
    const match = /^(\d{2,5})x(\d{2,5})$/.exec(size);
    if (!match) {
      throw new Error(`Invalid target size "${size}" — expected format "WxH" e.g. "1920x1080"`);
    }
    const width = Number(match[1]);
    const height = Number(match[2]);
    if (width < 64 || height < 64 || width > 8192 || height > 8192) {
      throw new Error(`Invalid target size "${size}" — dimensions must be between 64 and 8192 pixels`);
    }
    return `${width}x${height}`;
  });
}

function isPrivateIpv4(address) {
  const parts = address.split(".").map((part) => Number(part));
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part) || part < 0 || part > 255)) return false;
  const [a, b] = parts;
  return (
    a === 10 ||
    a === 127 ||
    a === 0 ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 168) ||
    (a === 169 && b === 254) ||
    (a === 100 && b >= 64 && b <= 127)
  );
}

function expandIpv6(address) {
  const normalized = address.toLowerCase().replace(/^\[|\]$/g, "");
  if (normalized.includes(".")) return null;
  const halves = normalized.split("::");
  if (halves.length > 2) return null;

  const head = halves[0] ? halves[0].split(":") : [];
  const tail = halves.length === 2 && halves[1] ? halves[1].split(":") : [];
  const fill = halves.length === 2 ? new Array(8 - head.length - tail.length).fill("0") : [];
  const groups = [...head, ...fill, ...tail];
  if (groups.length !== 8) return null;

  return groups.map((group) => {
    if (!/^[0-9a-f]{1,4}$/.test(group)) return NaN;
    return parseInt(group, 16);
  });
}

function ipv4FromMappedIpv6(address) {
  const normalized = address.toLowerCase().replace(/^\[|\]$/g, "");
  const dotted = normalized.match(/^(?:0:0:0:0:0:ffff:|::ffff:)(\d+\.\d+\.\d+\.\d+)$/);
  if (dotted) return dotted[1];

  const groups = expandIpv6(normalized);
  if (!groups || groups.some((group) => !Number.isInteger(group))) return null;
  if (groups.slice(0, 5).some((group) => group !== 0) || groups[5] !== 0xffff) return null;

  return [
    (groups[6] >> 8) & 0xff,
    groups[6] & 0xff,
    (groups[7] >> 8) & 0xff,
    groups[7] & 0xff,
  ].join(".");
}

function isPrivateIpv6(address) {
  const normalized = address.toLowerCase();
  const mappedIpv4 = ipv4FromMappedIpv6(normalized);
  if (mappedIpv4) return isPrivateIpv4(mappedIpv4);
  return (
    normalized === "::" ||
    normalized === "::1" ||
    normalized.startsWith("::ffff:0:") ||
    normalized.startsWith("fe80:") ||
    normalized.startsWith("fc") ||
    normalized.startsWith("fd")
  );
}

function assertSafeRemoteImageHostname(parsed) {
  const hostname = parsed.hostname.toLowerCase().replace(/^\[|\]$/g, "");
  const ipVersion = net.isIP(hostname);
  if (
    hostname === "localhost" ||
    hostname.endsWith(".localhost") ||
    hostname === "metadata.google.internal" ||
    (ipVersion === 4 && isPrivateIpv4(hostname)) ||
    (ipVersion === 6 && isPrivateIpv6(hostname))
  ) {
    throw new Error(`Image URL host is not allowed: ${parsed.hostname}`);
  }
}

async function assertSafeRemoteImageUrl(rawUrl) {
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new Error(`Invalid image URL: ${rawUrl}`);
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`Image URL must use http or https: ${rawUrl}`);
  }

  assertSafeRemoteImageHostname(parsed);

  const hostname = parsed.hostname.replace(/^\[|\]$/g, "");
  if (net.isIP(hostname)) return parsed;

  const addresses = await lookup(hostname, { all: true });
  for (const addressInfo of addresses) {
    if (
      (addressInfo.family === 4 && isPrivateIpv4(addressInfo.address)) ||
      (addressInfo.family === 6 && isPrivateIpv6(addressInfo.address))
    ) {
      throw new Error(`Image URL resolves to a private or local address: ${parsed.hostname}`);
    }
  }
  return parsed;
}

async function resolveSafeRemoteAddress(hostname) {
  const normalized = hostname.replace(/^\[|\]$/g, "");
  const ipVersion = net.isIP(normalized);
  if (ipVersion) {
    if (
      (ipVersion === 4 && isPrivateIpv4(normalized)) ||
      (ipVersion === 6 && isPrivateIpv6(normalized))
    ) {
      throw new Error(`Image URL host is not allowed: ${hostname}`);
    }
    return { address: normalized, family: ipVersion };
  }

  const addresses = await lookup(normalized, { all: true });
  const safe = addresses.find((addressInfo) => !(
    (addressInfo.family === 4 && isPrivateIpv4(addressInfo.address)) ||
    (addressInfo.family === 6 && isPrivateIpv6(addressInfo.address))
  ));
  if (!safe) {
    throw new Error(`Image URL resolves only to private or local addresses: ${hostname}`);
  }
  return safe;
}

function responseHeader(headers, name) {
  const value = headers[name.toLowerCase()];
  if (Array.isArray(value)) return value[0] || "";
  return value || "";
}

async function fetchValidatedRemoteImage(rawUrl, init = {}, redirects = 0) {
  const parsed = await assertSafeRemoteImageUrl(rawUrl);
  const method = init.method || "GET";
  const transport = parsed.protocol === "https:" ? https : http;

  return await new Promise((resolve, reject) => {
    const req = transport.request(parsed, {
      method,
      timeout: 15000,
      lookup: (hostname, _options, callback) => {
        resolveSafeRemoteAddress(hostname)
          .then((addressInfo) => callback(null, addressInfo.address, addressInfo.family))
          .catch((error) => callback(error));
      },
      headers: {
        "User-Agent": `slot-art-creator-node/${SERVER_VERSION}`,
        Accept: "image/*,*/*;q=0.1",
      },
    }, (res) => {
      const status = res.statusCode || 0;
      if (status >= 300 && status < 400) {
        res.resume();
        if (redirects >= 3) {
          reject(new Error(`Image URL redirected too many times: ${rawUrl}`));
          return;
        }
        const location = responseHeader(res.headers, "location");
        if (!location) {
          reject(new Error(`Image URL redirected without a Location header: ${rawUrl}`));
          return;
        }
        const nextUrl = new URL(location, parsed).href;
        fetchValidatedRemoteImage(nextUrl, init, redirects + 1).then(resolve, reject);
        return;
      }

      const contentLength = Number(responseHeader(res.headers, "content-length"));
      if (Number.isFinite(contentLength) && contentLength > MAX_REMOTE_IMAGE_BYTES) {
        res.resume();
        reject(new Error(`Image URL response is too large: ${contentLength} bytes`));
        return;
      }

      const chunks = [];
      let totalBytes = 0;
      res.on("data", (chunk) => {
        totalBytes += chunk.length;
        if (totalBytes > MAX_REMOTE_IMAGE_BYTES) {
          req.destroy(new Error(`Image URL response exceeded ${MAX_REMOTE_IMAGE_BYTES} bytes`));
          return;
        }
        chunks.push(chunk);
      });
      res.on("end", () => {
        const buffer = Buffer.concat(chunks);
        resolve({
          ok: status >= 200 && status < 300,
          status,
          headers: {
            get: (name) => responseHeader(res.headers, name),
          },
          arrayBuffer: async () => buffer,
        });
      });
    });

    req.on("timeout", () => {
      req.destroy(new Error(`Image URL request timed out: ${rawUrl}`));
    });
    req.on("error", reject);
    req.end();
  });
}

async function validateRemoteImageUrl(rawUrl) {
  const resp = await fetchValidatedRemoteImage(rawUrl, { method: "HEAD" });
  if (resp.ok) {
    const contentType = resp.headers.get("content-type") || "";
    if (contentType && !contentType.toLowerCase().startsWith("image/")) {
      throw new Error(`Remote image URL returned non-image content-type: ${contentType}`);
    }
  } else if (resp.status !== 405) {
    throw new Error(`Remote image URL is not reachable: ${resp.status} ${rawUrl}`);
  }
  return rawUrl;
}

// Containment allowlist for local image inputs. The LLM controls these paths
// and prompt injection means we can't trust them. Without an allowlist, a
// malicious symlink renamed `evil.png` can point at ~/.ssh/id_rsa and we'd
// happily upload it to fal.ai or base64-inline it to Gemini.
//
// We allow paths whose realpath sits inside any of:
//   - The active project folder hierarchy (H:\Shared drives\... or wherever
//     the active-project pointer says) — slots have to read their own outputs.
//   - ~/Pictures/claude_nb2 — default output dir for ad-hoc generates.
//   - ~/.h5g-slot-art-creator/inputs — reserved drop-zone for refs.
//   - The plugin root's own assets — for KEY_ART_TEMPLATE references etc.
//   - SLOT_ART_EXTRA_ROOTS env var, semicolon-separated, for additional
//     trusted roots (e.g. team Drive mounts) configurable per machine.
//
// Symlinks are resolved BEFORE the containment check, so symlink-out-of-the-
// allowlist attempts get caught by the prefix test.
function buildAllowedImageRoots() {
  const roots = new Set();
  const add = (p) => {
    if (!p) return;
    try {
      const real = fs.realpathSync(p);
      roots.add(real);
    } catch {
      // Path may not exist yet (e.g. project folder pre-create) — store the
      // resolved-but-unrealpath'd form so it still functions as a prefix.
      roots.add(path.resolve(p));
    }
  };

  add(path.join(os.homedir(), "Pictures", "claude_nb2"));
  add(path.join(os.homedir(), ".h5g-slot-art-creator", "inputs"));
  add(PLUGIN_ROOT);

  // Active project root, if the pointer file exists.
  try {
    const pointerPath = path.join(os.homedir(), ".h5g-slot-active-project.json");
    if (fs.existsSync(pointerPath)) {
      const pointer = JSON.parse(fs.readFileSync(pointerPath, "utf8"));
      if (pointer.project_root) add(pointer.project_root);
    }
  } catch {
    // Pointer file malformed — fall through, the other roots still apply.
  }

  // Extra trusted roots from env (semicolon-separated for Windows safety).
  const extra = process.env.SLOT_ART_EXTRA_ROOTS;
  if (extra) {
    for (const r of extra.split(/[;:]/).map((s) => s.trim()).filter(Boolean)) {
      add(r);
    }
  }

  return Array.from(roots);
}

function isWithinAllowedRoot(resolvedPath, roots) {
  // Normalize both sides to absolute paths and compare prefixes by path
  // components, not raw substrings — `/a/foo` must NOT match root `/a/f`.
  const target = path.resolve(resolvedPath);
  for (const root of roots) {
    const rootAbs = path.resolve(root);
    const rel = path.relative(rootAbs, target);
    if (rel === "" || (!rel.startsWith("..") && !path.isAbsolute(rel))) {
      return true;
    }
  }
  return false;
}

function validateLocalImagePath(rawPath) {
  const expanded = rawPath.startsWith("~")
    ? path.join(os.homedir(), rawPath.slice(1))
    : rawPath;
  const resolved = fs.realpathSync(path.resolve(expanded));
  const stat = fs.statSync(resolved);
  if (!stat.isFile()) {
    throw new Error(
      `Image input must be a file (not a directory): ${rawPath}. ` +
      `→ If you meant to point at an image inside this directory, include the filename in the path.`
    );
  }
  const ext = path.extname(resolved).toLowerCase();
  if (!ALLOWED_IMAGE_EXTENSIONS.has(ext)) {
    throw new Error(
      `Image input must be .png, .jpg, .jpeg, or .webp (got "${ext || "no extension"}"): ${rawPath}. ` +
      `→ If this is a chat-attached image with a temp extension, call nb2_stage_image first — ` +
      `it handles the mime-type→extension mapping and stages the file safely.`
    );
  }
  if (path.basename(resolved).toLowerCase().startsWith(".env")) {
    throw new Error(`Image input cannot be an env file: ${rawPath}. → Use an actual image file.`);
  }
  const roots = buildAllowedImageRoots();
  if (!isWithinAllowedRoot(resolved, roots)) {
    throw new Error(
      `Image input is outside the allowed roots: ${rawPath} (resolves to ${resolved}). ` +
      `→ If this is a chat-attached image or a path outside the project folder, call ` +
      `nb2_stage_image with this path first — it copies the image into the safe inputs ` +
      `folder and returns a path you can use here. See shared/chat_image_staging.md. ` +
      `Allowed roots: the active project folder, ~/Pictures/claude_nb2, ` +
      `~/.h5g-slot-art-creator/inputs, the plugin folder, or anything in SLOT_ART_EXTRA_ROOTS.`
    );
  }
  return resolved;
}

async function validateImageInput(rawInput, label) {
  if (!rawInput || typeof rawInput !== "string") {
    throw new Error(`${label} must be an image path or URL`);
  }
  if (rawInput.includes("\0")) {
    throw new Error(`${label} contains an invalid path character`);
  }
  if (isRemoteUrl(rawInput)) return await validateRemoteImageUrl(rawInput);
  return validateLocalImagePath(rawInput);
}

async function validateImageInputs(rawInputs, label) {
  if (!rawInputs) return null;
  if (!Array.isArray(rawInputs)) throw new Error(`${label} must be an array of image paths or URLs`);
  return await Promise.all(rawInputs.map((input) => validateImageInput(input, label)));
}

// ---------------------------------------------------------------------------
// Chat-image staging
//
// validateLocalImagePath rejects any path outside the allowed roots. That's
// correct for the destructive tools (edit / upscale / smart_resize) — we
// don't want a prompt-injected path to read arbitrary user files. But it
// breaks the most natural use case: a user pastes an image in chat and asks
// to edit it. Chat-pasted images live in temp paths far outside any allowed
// root.
//
// Staging is the explicit bridge. nb2_stage_image takes any local path (no
// containment check, but every OTHER guard still applies — file exists, real
// image extension, not an env file, under the 50MB cap) or a URL (uses the
// SSRF-guarded fetch) and copies/downloads it into ~/.h5g-slot-art-creator/
// inputs/, which IS in the allowed-roots list. The staged path is what the
// caller then passes to nb2_edit / nb2_upscale / nb2_smart_resize.
//
// Filenames are auto-uniqued via uniqueName so concurrent staging never
// collides.
// ---------------------------------------------------------------------------

const STAGED_INPUTS_DIR = path.join(os.homedir(), ".h5g-slot-art-creator", "inputs");

function mimeToImageExtension(mime) {
  if (!mime) return ".png";
  const m = mime.toLowerCase().split(";")[0].trim();
  if (m === "image/jpeg" || m === "image/jpg") return ".jpg";
  if (m === "image/webp") return ".webp";
  return ".png";
}

async function stageImage({ source, label }) {
  if (!source || typeof source !== "string") {
    throw new Error("source must be an image path or URL");
  }
  if (source.includes("\0")) {
    throw new Error("source contains an invalid path character");
  }

  ensureDir(STAGED_INPUTS_DIR);
  const safeLabel = sanitizeAssetName(label, "chat_input");
  const t0 = Date.now();

  // Remote URL — re-use the SSRF-guarded fetch path. The size cap and
  // content-type check inside fetchValidatedRemoteImage protect us here.
  if (isRemoteUrl(source)) {
    const { buffer, mimeType } = await fetchRemoteImageBuffer(source);
    if (!mimeType.toLowerCase().startsWith("image/")) {
      throw new Error(`source URL did not return an image (got ${mimeType})`);
    }
    const ext = mimeToImageExtension(mimeType);
    const dest = uniqueName(STAGED_INPUTS_DIR, safeLabel, ext);
    fs.writeFileSync(dest, buffer);
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    return {
      provider: "stage",
      model: "url-fetch",
      resolution: "(source-preserved)",
      elapsed,
      paths: [dest],
      source_origin: source,
    };
  }

  // Local file path — realpath, validate is a real image, copy. We
  // intentionally do NOT apply the containment allowlist here; bypassing
  // it is the entire purpose of staging. The other guards (extension,
  // .env name, size cap, no NUL bytes) still apply.
  const expanded = source.startsWith("~")
    ? path.join(os.homedir(), source.slice(1))
    : source;
  let resolved;
  try {
    resolved = fs.realpathSync(path.resolve(expanded));
  } catch (e) {
    throw new Error(`source path not readable: ${source} (${e.code || e.message})`);
  }
  const stat = fs.statSync(resolved);
  if (!stat.isFile()) {
    throw new Error(`source must be a file: ${source}`);
  }
  const ext = path.extname(resolved).toLowerCase();
  if (!ALLOWED_IMAGE_EXTENSIONS.has(ext)) {
    throw new Error(`source must be .png, .jpg, .jpeg, or .webp (got ${ext || "(no ext)"}): ${source}`);
  }
  if (path.basename(resolved).toLowerCase().startsWith(".env")) {
    throw new Error(`source cannot be an env file: ${source}`);
  }
  if (stat.size > MAX_REMOTE_IMAGE_BYTES) {
    throw new Error(`source is too large (${stat.size} bytes; max ${MAX_REMOTE_IMAGE_BYTES})`);
  }

  const dest = uniqueName(STAGED_INPUTS_DIR, safeLabel, ext);
  fs.copyFileSync(resolved, dest);
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  return {
    provider: "stage",
    model: "local-copy",
    resolution: "(source-preserved)",
    elapsed,
    paths: [dest],
    source_origin: resolved,
  };
}

// ---------------------------------------------------------------------------
// Sidecar metadata (.meta.json) — written next to every output PNG
//
// Provenance for downstream tools, /slot-step-08, and human review.
// Schema is h5g_asset.meta.v1. Contains the prompt that produced the image,
// the model + provider, all API args, and references used. Survives moving
// the project folder.
// ---------------------------------------------------------------------------

function writeSidecar(pngPath, meta) {
  const sidecarPath = pngPath.replace(/\.png$/i, ".meta.json");
  const payload = {
    schema: "h5g_asset.meta.v1",
    filename: path.basename(pngPath),
    full_path: pngPath,
    generated_at: new Date().toISOString(),
    ...meta,
  };
  try {
    fs.writeFileSync(sidecarPath, JSON.stringify(payload, null, 2));
  } catch (e) {
    // Sidecar failure must never block the actual generation result
    console.error(`[sidecar] failed to write ${sidecarPath}: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// Provider detection
// ---------------------------------------------------------------------------

const FAL_KEY = process.env.FAL_KEY || "";
const GEMINI_KEY =
  process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || "";
const OPENAI_KEY = process.env.OPENAI_API_KEY || "";

// OpenAI client for the gpt2_* tools. Lazy: only instantiated if the key
// is set, so installs without the OpenAI key don't even load the client.
let openaiClient = null;
if (OPENAI_KEY) {
  openaiClient = new OpenAI({ apiKey: OPENAI_KEY });
}

// Configure the fal singleton once at module init. Previous versions called
// fal.config({ credentials }) at the top of every tool handler — the fal
// module is a process-wide singleton, so concurrent tool calls were each
// re-mutating shared state. Doing it once here is race-free and slightly
// faster.
if (FAL_KEY) {
  fal.config({ credentials: FAL_KEY });
}

// Create the staged-inputs folder up front so chat-image staging always
// works without a first-call mkdir race. Also surfaces permission errors
// on startup rather than at first use.
try {
  ensureDir(STAGED_INPUTS_DIR);
} catch (e) {
  console.error(`[startup] could not create staged inputs dir ${STAGED_INPUTS_DIR}: ${e.message}`);
}

// Provider selection for the three generation tools (generate / edit / upscale).
// Both Gemini and fal.ai are fully capable here — they wrap the SAME underlying
// model (Nano Banana 2 = gemini-3.1-flash-image-preview = fal-ai/nano-banana-2).
// Gemini wins when both keys are present because the direct Google API call is
// one hop fewer than going through fal.ai's wrapper. Either key alone is
// completely sufficient for these three tools.
//
// nb2_smart_resize uses its own routing (see the per-tool handler at the
// nb2_smart_resize case). Both providers have a smart-resize implementation
// but they're materially different: fal.ai uses a purpose-built endpoint
// (Nano Banana Pro, single API call); Gemini uses NB2 + N calls + pngjs
// center-crop. fal.ai wins when both keys are present because the purpose-built
// endpoint is faster and doesn't have the "returned image smaller than target"
// failure mode that the Gemini path can hit.
function getProviderForGeneration() {
  if (GEMINI_KEY) return "gemini";
  if (FAL_KEY) return "fal";
  return null;
}

// ---------------------------------------------------------------------------
// fal.ai helpers
// ---------------------------------------------------------------------------

const FAL_RESOLUTION_MAP = {
  "512": "0.5K",
  "1K": "1K",
  "2K": "2K",
  "4K": "4K",
};

async function uploadLocalFile(filePath) {
  const buffer = fs.readFileSync(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const mime = imageMimeType(ext);
  const blob = new Blob([buffer], { type: mime });
  return await fal.storage.upload(blob);
}

async function uploadRemoteImage(url) {
  const { buffer, mimeType } = await fetchRemoteImageBuffer(url);
  const blob = new Blob([buffer], { type: mimeType });
  return await fal.storage.upload(blob);
}

function imageMimeType(ext) {
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  return "image/png";
}

async function fetchRemoteImageBuffer(url) {
  const resp = await fetchValidatedRemoteImage(url);
  if (!resp.ok) throw new Error(`Failed to fetch image URL: ${resp.status} ${url}`);
  const contentType = resp.headers.get("content-type") || "";
  if (contentType && !contentType.toLowerCase().startsWith("image/")) {
    throw new Error(`Image URL returned non-image content-type: ${contentType}`);
  }
  return {
    buffer: Buffer.from(await resp.arrayBuffer()),
    mimeType: contentType.split(";")[0] || "image/png",
  };
}

async function downloadImage(url, destPath) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Download failed: ${resp.status} ${url}`);
  const buf = Buffer.from(await resp.arrayBuffer());
  fs.writeFileSync(destPath, buf);
}

async function falGenerate({ prompt, outputDir, assetName, imageSize, aspectRatio, references }) {
  // The fal.ai NanoBanana2Input schema uses `resolution` (NOT `image_size`).
  // Valid values: "0.5K" | "1K" | "2K" | "4K". Default is "1K" — we override
  // to "2K" for project minimum.
  const falRes = FAL_RESOLUTION_MAP[imageSize] || "2K";
  const input = {
    prompt,
    resolution: falRes,
  };
  if (aspectRatio && aspectRatio !== "auto") input.aspect_ratio = aspectRatio;

  // Upload reference images if provided. For nb2_generate, references are
  // STYLE ANCHORS only — we always use the base (text-to-image) endpoint and
  // pass them as reference_image_urls so output is influenced by their style
  // without becoming an edit. This matches Gemini's behavior, where
  // geminiGenerate appends references to the parts array as additional
  // image inputs without switching modes.
  //
  // If you want an edit (source image as basis for transformation), call
  // nb2_edit, which routes here via the explicit edit dispatch with a
  // `source` arg. nb2_generate must never silently become an edit just
  // because references happened to be present.
  if (references && references.length > 0) {
    const uploaded = await Promise.all(
      references.map(async (ref) => {
        if (ref.startsWith("http://") || ref.startsWith("https://")) return await uploadRemoteImage(ref);
        return await uploadLocalFile(ref);
      })
    );
    input.reference_image_urls = uploaded;
  }

  const endpoint = "fal-ai/nano-banana-2";

  const t0 = Date.now();
  const result = await fal.subscribe(endpoint, { input, logs: false });
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

  const images = result.data?.images || [];
  if (!images.length) throw new Error(
    "fal.ai returned no images. → Often transient; retry once. If it persists, the prompt may be triggering fal.ai's safety filter — soften any aggressive imagery and try again. If you have GEMINI_API_KEY set, removing FAL_KEY temporarily would route this call through Gemini's direct API."
  );

  ensureDir(outputDir);
  const saved = [];
  for (let i = 0; i < images.length; i++) {
    const suffix = images.length > 1 ? `_${i + 1}` : "";
    const dest = uniqueName(outputDir, `${assetName}${suffix}`);
    await downloadImage(images[i].url, dest);
    saved.push(dest);
    writeSidecar(dest, {
      tool: "nb2_generate",
      provider: "fal.ai",
      model: endpoint,
      prompt,
      image_size: imageSize,
      aspect_ratio: aspectRatio || null,
      reference_images: references || [],
      source_image: null,
      duration_seconds: Number(elapsed),
    });
  }

  return { provider: "fal.ai", model: "fal-ai/nano-banana-2", resolution: falRes, elapsed, paths: saved };
}

async function falEdit({ prompt, source, outputDir, assetName, imageSize, aspectRatio, extraReferences }) {
  // The fal.ai NanoBanana2EditInput schema uses `resolution` (NOT `image_size`).
  const falRes = FAL_RESOLUTION_MAP[imageSize] || "2K";

  // Build image_urls: source is always first
  const allRefs = [source, ...(extraReferences || [])];
  const uploaded = await Promise.all(
    allRefs.map(async (ref) => {
      if (ref.startsWith("http://") || ref.startsWith("https://")) return await uploadRemoteImage(ref);
      return await uploadLocalFile(ref);
    })
  );

  const input = {
    prompt,
    image_urls: uploaded,
    resolution: falRes,
  };
  if (aspectRatio && aspectRatio !== "auto") input.aspect_ratio = aspectRatio;

  const t0 = Date.now();
  const result = await fal.subscribe("fal-ai/nano-banana-2/edit", { input, logs: false });
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

  const images = result.data?.images || [];
  if (!images.length) throw new Error(
    "fal.ai returned no images. → Often transient; retry once. If it persists, the prompt may be triggering fal.ai's safety filter — soften any aggressive imagery and try again. If you have GEMINI_API_KEY set, removing FAL_KEY temporarily would route this call through Gemini's direct API."
  );

  ensureDir(outputDir);
  const saved = [];
  for (let i = 0; i < images.length; i++) {
    const suffix = images.length > 1 ? `_${i + 1}` : "";
    const dest = uniqueName(outputDir, `${assetName}${suffix}`);
    await downloadImage(images[i].url, dest);
    saved.push(dest);
    writeSidecar(dest, {
      tool: "nb2_edit",
      provider: "fal.ai",
      model: "fal-ai/nano-banana-2/edit",
      prompt,
      image_size: imageSize,
      aspect_ratio: aspectRatio || null,
      reference_images: extraReferences || [],
      source_image: source,
      duration_seconds: Number(elapsed),
    });
  }

  return { provider: "fal.ai", model: "fal-ai/nano-banana-2/edit", resolution: falRes, elapsed, paths: saved };
}

async function falSmartResize({ source, outputDir, assetName, targetSizes, prompt }) {
  let imageUrl = source;
  if (!source.startsWith("http://") && !source.startsWith("https://")) {
    imageUrl = await uploadLocalFile(source);
  } else {
    imageUrl = await uploadRemoteImage(source);
  }

  // Default target sizes match the project's 2K minimum. fal-ai/smart-resize
  // accepts any "<width>x<height>" strings; the endpoint internally picks the
  // smallest nano-banana-pro preset that fully covers each target, then
  // center-crops to the exact requested dimensions.
  const sizes = validateTargetSizes(targetSizes);

  // Schema verified against fal.ai docs (https://fal.ai/models/fal-ai/smart-resize):
  //   image_url             — string, required
  //   target_sizes          — list<"WxH" string>, required
  //   resolution            — "1K" | "2K" | "4K", optional (default "1K")
  //                           "Hint for the minimum resolution tier" — we pass
  //                           "2K" so the internal NB Pro generation doesn't
  //                           drop below project minimum quality.
  //   num_images_per_size   — int, optional (default 1)
  //   output_format         — "jpeg" | "png" | "webp", optional (default "png")
  //   prompt                — string, optional extra instruction (default "")
  //   safety_tolerance      — "1"–"6" string, optional (default "4")
  //   seed, sync_mode       — optional, not used here
  //
  // NOTE: This endpoint uses **nano-banana-pro** internally, NOT NB2. The
  // wrapper tool is named "nb2_smart_resize" because it's part of the NB2
  // workflow, but the underlying model is NB Pro per fal's docs.
  const input = {
    image_url: imageUrl,
    target_sizes: sizes,
    resolution: "2K",
    output_format: "png",
  };
  // Optional extra instruction forwarded to nano-banana-pro alongside the
  // auto-generated resize prompt (per fal.ai smart-resize docs).
  if (prompt) input.prompt = prompt;

  const t0 = Date.now();
  const result = await fal.subscribe("fal-ai/smart-resize", { input, logs: false });
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

  // Response shape (verified against fal.ai docs):
  //   data.images       — flat list<ImageFile>; one entry per (target_size × num_images_per_size)
  //   data.results      — list<SmartResizeResult> with width, height,
  //                       aspect_ratio, and resolution per target — useful provenance
  const images = result.data?.images || [];
  const perTargetResults = result.data?.results || [];
  if (!images.length) throw new Error(
    "fal-ai/smart-resize returned no images. → Often transient; retry once. If you set GEMINI_API_KEY, you can also unset FAL_KEY to fall back to the Gemini smart-resize path (uses NB2 + pngjs center-crop; slower but works for the same target sizes)."
  );

  ensureDir(outputDir);
  const saved = [];
  for (let i = 0; i < images.length; i++) {
    const requestedSize = sizes[i] || null;
    const meta = perTargetResults[i] || {};
    // Suffix format: `_resize_<W>_<H>` so the file name carries exact pixel
    // dimensions (per shared/asset_naming.md "Derived variants"). The older
    // `_<W>x<H>` form is retired — the `x` collides with the upscale-suffix
    // multiplier convention (`_upscl_x2`) when a reader scans filenames.
    const sizeSuffix = requestedSize
      ? `_resize_${requestedSize.replace("x", "_")}`
      : `_resize_${i + 1}`;
    const dest = uniqueName(outputDir, `${assetName}${sizeSuffix}`);
    await downloadImage(images[i].url, dest);
    saved.push(dest);
    writeSidecar(dest, {
      tool: "nb2_smart_resize",
      provider: "fal.ai",
      model: "fal-ai/smart-resize",
      underlying_model: "nano-banana-pro", // documented in fal's smart-resize page
      prompt: null,
      image_size: requestedSize,
      target_size: requestedSize,
      actual_width: images[i].width || meta.width || null,
      actual_height: images[i].height || meta.height || null,
      internal_aspect_ratio: meta.aspect_ratio || null,
      internal_resolution: meta.resolution || null,
      aspect_ratio: null,
      reference_images: [],
      source_image: source,
      duration_seconds: Number(elapsed),
    });
  }

  return { provider: "fal.ai", model: "fal-ai/smart-resize", resolution: sizes.join(", "), elapsed, paths: saved };
}

// ---------------------------------------------------------------------------
// Gemini helpers
// ---------------------------------------------------------------------------

function imagePartFromFile(filePath) {
  const data = fs.readFileSync(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const mime = imageMimeType(ext);
  return {
    inlineData: {
      data: data.toString("base64"),
      mimeType: mime,
    },
  };
}

// Gemini's image generation accepts these resolution strings via
// config.imageConfig.imageSize. Default is "1K" — we pass "2K" explicitly to
// match the project minimum. (Note: this is a separate axis from aspect_ratio.)
const GEMINI_IMAGE_SIZE_MAP = {
  "512": "1K",   // Gemini doesn't expose 0.5K — clamp up
  "1K": "1K",
  "2K": "2K",
  "4K": "4K",
};

async function geminiGenerate({ prompt, outputDir, assetName, imageSize, aspectRatio, references }) {
  const client = new GoogleGenAI({ apiKey: GEMINI_KEY });

  const parts = [{ text: prompt }];
  if (references) {
    for (const ref of references) {
      if (ref.startsWith("http://") || ref.startsWith("https://")) {
        const { buffer, mimeType } = await fetchRemoteImageBuffer(ref);
        parts.push({ inlineData: { data: buffer.toString("base64"), mimeType } });
      } else {
        parts.push(imagePartFromFile(ref));
      }
    }
  }

  // GenerateContentConfig schema (verified against @google/genai v1.52.0
  // genai.d.ts line 4466):
  //   - responseModalities goes at the top level of config
  //   - aspectRatio and imageSize go INSIDE config.imageConfig (per
  //     ImageConfig interface at line 6197)
  //   - numberOfImages does NOT exist on this interface — it's on
  //     GenerateImagesConfig (Imagen API) which we don't use here
  const imgCfg = {};
  if (aspectRatio && aspectRatio !== "auto") imgCfg.aspectRatio = aspectRatio;
  imgCfg.imageSize = GEMINI_IMAGE_SIZE_MAP[imageSize] || "2K";

  const config = {
    responseModalities: ["IMAGE", "TEXT"],
    imageConfig: imgCfg,
  };

  // The wrapper key on GenerateContentParameters is `config:` (NOT
  // `generationConfig:`). Confirmed against genai.d.ts line 4626-4636.
  const t0 = Date.now();
  const response = await client.models.generateContent({
    model: "gemini-3.1-flash-image-preview",
    contents: [{ role: "user", parts }],
    config,
  });
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

  ensureDir(outputDir);
  const saved = [];

  const candidates = response.candidates || [];
  for (const cand of candidates) {
    for (const part of cand.content?.parts || []) {
      if (part.inlineData?.data) {
        const dest = uniqueName(outputDir, assetName);
        const buf = Buffer.from(part.inlineData.data, "base64");
        fs.writeFileSync(dest, buf);
        saved.push(dest);
        writeSidecar(dest, {
          tool: "nb2_generate",
          provider: "Gemini",
          model: "gemini-3.1-flash-image-preview",
          prompt,
          image_size: imageSize || "2K",
          aspect_ratio: aspectRatio || null,
          reference_images: references || [],
          source_image: null,
          duration_seconds: Number(elapsed),
        });
      }
    }
  }

  if (!saved.length) throw new Error(
    "Gemini returned no image data. → Often transient; retry once. If it persists, the prompt may have hit Gemini's safety filter — soften aggressive imagery, remove anything resembling real people / public figures, and try again. If you have FAL_KEY set, unsetting GEMINI_API_KEY would route this call through fal.ai's wrapper of the same NB2 model."
  );

  return {
    provider: "Gemini",
    model: "gemini-3.1-flash-image-preview",
    resolution: imageSize || "2K",
    elapsed,
    paths: saved,
  };
}

// ---------------------------------------------------------------------------
// Gemini smart-resize — Gemini-side equivalent of fal.ai's smart-resize.
// ---------------------------------------------------------------------------
// Replicates the fal-ai/smart-resize recipe (oversample → center-crop) using
// gemini-3.1-flash-image-preview (Nano Banana 2) as the underlying model
// instead of nano-banana-pro. For each "<W>x<H>" target:
//   1. Pick the closest Gemini aspect_ratio preset to the target's W/H ratio
//   2. Pick the smallest Gemini imageSize tier ("1K"/"2K"/"4K") that should
//      cover the target's largest dimension
//   3. Call generateContent with the source image as inline data + a
//      recompose prompt
//   4. Center-crop the returned PNG to the exact requested W×H using pngjs
//
// Pixel-perfect output comes from oversample + crop, same as fal's recipe.
// ---------------------------------------------------------------------------

const GEMINI_ASPECT_RATIOS = [
  ["1:1",   1.0],
  ["2:3",   2 / 3],
  ["3:2",   3 / 2],
  ["3:4",   3 / 4],
  ["4:3",   4 / 3],
  ["9:16",  9 / 16],
  ["16:9",  16 / 9],
  ["21:9",  21 / 9],
];

// Pick the Gemini aspect-ratio preset whose ratio is closest to the target.
function pickGeminiAspectRatio(targetW, targetH) {
  const targetRatio = targetW / targetH;
  let best = GEMINI_ASPECT_RATIOS[0];
  let minDelta = Infinity;
  for (const entry of GEMINI_ASPECT_RATIOS) {
    const delta = Math.abs(entry[1] - targetRatio);
    if (delta < minDelta) {
      minDelta = delta;
      best = entry;
    }
  }
  return best[0];
}

// Pick the smallest Gemini imageSize tier that should comfortably cover the
// requested target dimensions. Conservative — defaults to 4K for any
// dimension >2048 (Gemini's "4K" tier is the largest available).
function pickGeminiResolutionTier(targetW, targetH) {
  const max = Math.max(targetW, targetH);
  if (max <= 1024) return "2K";  // 2K tier easily covers ≤1024 after preset
  if (max <= 2048) return "4K";  // 4K tier for 1080p–2K targets
  return "4K";                    // largest available; Gemini caps at 4K
}

// Center-crop a PNG buffer to exact target dimensions using pngjs (pure JS,
// no native deps). Throws if the source is smaller than the target.
function centerCropPng(srcBuf, targetW, targetH) {
  const src = PNG.sync.read(srcBuf);
  if (src.width < targetW || src.height < targetH) {
    throw new Error(
      `Gemini returned ${src.width}x${src.height}, smaller than requested ` +
      `${targetW}x${targetH}. Try a larger target or use fal.ai for this size.`
    );
  }
  const x = Math.floor((src.width - targetW) / 2);
  const y = Math.floor((src.height - targetH) / 2);
  const out = new PNG({ width: targetW, height: targetH });
  PNG.bitblt(src, out, x, y, targetW, targetH, 0, 0);
  return PNG.sync.write(out);
}

async function geminiSmartResize({ source, outputDir, assetName, targetSizes, prompt }) {
  const client = new GoogleGenAI({ apiKey: GEMINI_KEY });

  // Read source image as inline data (Gemini accepts URLs by fetch + base64,
  // or local files directly).
  let sourcePart;
  if (source.startsWith("http://") || source.startsWith("https://")) {
    const { buffer, mimeType } = await fetchRemoteImageBuffer(source);
    sourcePart = { inlineData: { data: buffer.toString("base64"), mimeType } };
  } else {
    sourcePart = imagePartFromFile(source);
  }

  ensureDir(outputDir);
  const saved = [];
  const overallT0 = Date.now();

  const sizes = validateTargetSizes(targetSizes);
  for (const size of sizes) {
    const match = /^(\d+)x(\d+)$/.exec(size);
    const targetW = parseInt(match[1], 10);
    const targetH = parseInt(match[2], 10);

    const aspectRatio = pickGeminiAspectRatio(targetW, targetH);
    const tier = pickGeminiResolutionTier(targetW, targetH);

    const recomposePrompt =
      (prompt ? prompt + " " : "") +
      `Recompose this image at ${aspectRatio} aspect ratio while preserving the ` +
      `subject, palette, style, and overall mood. Adjust framing as needed to fit ` +
      `the target shape; do not crop awkwardly. Keep the hero subject as the ` +
      `focal point. Match the rendering style of the source exactly.`;

    const t0 = Date.now();
    const response = await client.models.generateContent({
      model: "gemini-3.1-flash-image-preview",
      contents: [{
        role: "user",
        parts: [
          { text: recomposePrompt },
          sourcePart,
        ],
      }],
      config: {
        responseModalities: ["IMAGE", "TEXT"],
        imageConfig: {
          aspectRatio,
          imageSize: tier,
        },
      },
    });
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

    // Extract image bytes from the response. Gemini's SDK occasionally returns
    // JPEG instead of PNG depending on internal heuristics — we must read the
    // mimeType, not assume PNG, since pngjs's PNG.sync.read crashes on a JPEG
    // byte stream. We also surface the mimeType to centerCropPng so it can
    // transcode JPEG→PNG before the pngjs crop step.
    let imageBuf = null;
    let imageMime = null;
    const candidates = response.candidates || [];
    outer: for (const cand of candidates) {
      for (const part of cand.content?.parts || []) {
        if (part.inlineData?.data) {
          imageBuf = Buffer.from(part.inlineData.data, "base64");
          imageMime = (part.inlineData.mimeType || "image/png").toLowerCase();
          break outer;
        }
      }
    }
    if (!imageBuf) {
      throw new Error(
        `Gemini returned no image for target ${size}. → Often transient; retry once. ` +
        `If it persists, this specific aspect ratio may be triggering the safety filter ` +
        `or the input is too small for Gemini to recompose. With FAL_KEY set, the ` +
        `fal-ai/smart-resize endpoint (Nano Banana Pro) handles this in a single call ` +
        `and is much more reliable for unusual aspects.`
      );
    }

    // Center-crop to exact target dimensions. The crop function only operates
    // on PNG buffers; if Gemini returned JPEG we'd need a JPEG decoder. We
    // don't ship one (would add a native dep), so for now we error with a
    // clear message and let the caller retry. In practice Gemini returns PNG
    // when responseModalities includes "IMAGE" — JPEG returns are rare.
    if (!imageMime.startsWith("image/png")) {
      throw new Error(
        `Gemini returned ${imageMime} for target ${size}; smart_resize Gemini ` +
        `path requires PNG. Re-run, or switch to fal.ai (FAL_KEY) which uses ` +
        `the purpose-built smart-resize endpoint and is not subject to this ` +
        `failure mode.`
      );
    }
    const croppedBuf = centerCropPng(imageBuf, targetW, targetH);

    // Save — suffix format `_resize_<W>_<H>` matches shared/asset_naming.md
    // "Derived variants". Stays parallel with the fal.ai path so a project
    // folder can mix outputs from both backends without naming drift.
    const dest = uniqueName(outputDir, `${assetName}_resize_${size.replace("x", "_")}`);
    fs.writeFileSync(dest, croppedBuf);
    saved.push(dest);
    writeSidecar(dest, {
      tool: "nb2_smart_resize",
      provider: "Gemini",
      model: "gemini-3.1-flash-image-preview",
      underlying_model: "gemini-3.1-flash-image-preview", // = Nano Banana 2
      prompt: recomposePrompt,
      image_size: size,
      target_size: size,
      actual_width: targetW,
      actual_height: targetH,
      internal_aspect_ratio: aspectRatio,
      internal_resolution: tier,
      aspect_ratio: aspectRatio,
      reference_images: [],
      source_image: source,
      duration_seconds: Number(elapsed),
    });
  }

  const overallElapsed = ((Date.now() - overallT0) / 1000).toFixed(1);
  return {
    provider: "Gemini",
    model: "gemini-3.1-flash-image-preview",
    resolution: sizes.join(", "),
    elapsed: overallElapsed,
    paths: saved,
  };
}

// ---------------------------------------------------------------------------
// Dispatcher — route to gemini (when both keys set) or fal (when only fal set).
// Both providers fully implement these tools using the same underlying NB2
// model; the "preference" is just about which API path runs.
// ---------------------------------------------------------------------------

async function dispatchGenerate(args) {
  const provider = getProviderForGeneration();
  if (!provider) throw new Error(
    "No API key found. → Run /slot-setup in chat to configure keys safely " +
    "(it'll point you at the setup-keys.bat or setup-keys.sh launcher in your plugin " +
    "install — your input stays in a hidden-input terminal prompt, never in chat). " +
    "Get a key from https://aistudio.google.com/apikey (Gemini) or " +
    "https://fal.ai/dashboard (fal.ai). Either alone is sufficient for all 4 generation tools."
  );
  if (provider === "gemini") return geminiGenerate(args);
  return falGenerate(args);
}

async function dispatchEdit(args) {
  const provider = getProviderForGeneration();
  if (!provider) throw new Error(
    "No API key found. → Run /slot-setup in chat to configure keys safely. Get a key from https://aistudio.google.com/apikey (Gemini) or https://fal.ai/dashboard (fal.ai)."
  );
  if (provider === "gemini") {
    // Gemini edit = generate with source as first reference
    return geminiGenerate({
      ...args,
      references: [args.source, ...(args.extraReferences || [])],
    });
  }
  return falEdit(args);
}

// ---------------------------------------------------------------------------
// GPT Image 2 (OpenAI) helpers
//
// gpt-image-2 is a separate model from NB2 and behaves differently:
//   - Strong text rendering (use for paytables, logos, banners with copy)
//   - Stable at 1K and 2K. We don't expose 4K — OpenAI flags it experimental
//     and we only ship skills that work. For 4K marketing output: generate
//     at 2K here, then nb2_upscale.
//   - No faithful upscale mode — always regenerates at the target size
//   - Agentic planning — better at compositional briefs
//   - Returns base64 (no temp URL — write straight to disk)
//   - Edit accepts up to ~16 reference images for compositional editing
//
// We translate our abstract size ("1K"/"2K"/"4K") + aspect_ratio to
// gpt-image-2's literal pixel-size strings since gpt-image-2 doesn't
// accept aspect-ratio shorthand.
// ---------------------------------------------------------------------------

// Map (image_size, aspect_ratio) → gpt-image-2 literal size string.
// Source: https://developers.openai.com/api/docs/guides/image-generation
//
// Resolution policy: we expose only 1K and 2K. 2K (2048×2048) is gpt-image-2's
// stable native ceiling. OpenAI's API also accepts 4K sizes (3840×2160 /
// 2160×3840) but flags them experimental — they're not reliable for production.
// We deliberately don't expose them: "we only ship skills that work."
//
// For genuinely high-res output:
//   - For a NEW image at 4K: generate at 2K via gpt2_generate, then run
//     nb2_upscale (the only tested upscale path in this plugin).
//   - For an existing 2K asset → 4K: nb2_upscale directly.
//
// gpt-image-2 has NO faithful upscale mode — every call regenerates fresh
// rather than super-resolving an input.
//
// Tier reference:
//   1024x1024  square 1K
//   1536x1024  landscape ~3:2 1K
//   1024x1536  portrait ~2:3 1K
//   2048x2048  square 2K (stable native ceiling)
//   2048x1152  landscape 16:9 2K
//   1152x2048  portrait 9:16 2K
//
// Constraints (enforced by OpenAI): max edge ≤3840, multiples of 16, ratio ≤3:1.
const GPT2_SIZE_TABLE = {
  // [size][aspect_ratio] → literal string. Only 1K and 2K are exposed —
  // 2K is gpt-image-2's stable native ceiling. 4K targets are accepted
  // by OpenAI's API but flagged experimental; we don't ship them since
  // we can't promise they work. For genuine 4K, generate at 2K here and
  // run nb2_upscale on the result.
  "1K":  { "1:1": "1024x1024", "3:2": "1536x1024", "2:3": "1024x1536",
           "16:9": "1536x1024", "9:16": "1024x1536", "default": "1024x1024" },
  "2K":  { "1:1": "2048x2048", "16:9": "2048x1152", "9:16": "1152x2048",
           "3:2": "2048x1152", "2:3": "1152x2048", "default": "2048x2048" },
};

function pickGpt2Size(imageSize, aspectRatio) {
  const tier = GPT2_SIZE_TABLE[imageSize] || GPT2_SIZE_TABLE["2K"];
  if (aspectRatio && tier[aspectRatio]) return tier[aspectRatio];
  return tier.default;
}

// Decode an OpenAI base64 image response and write to disk.
function saveB64Image(b64Data, outputFormat, outputDir, baseName) {
  const ext = outputFormat === "jpeg" ? ".jpg"
            : outputFormat === "webp" ? ".webp"
            : ".png";
  const dest = uniqueName(outputDir, baseName, ext);
  const buf = Buffer.from(b64Data, "base64");
  fs.writeFileSync(dest, buf);
  return dest;
}

// Read a local image into a File-compatible object for the OpenAI SDK.
// The SDK accepts either a Node fs.ReadStream or a Web File (we use toFile).
async function gpt2ReadImageInput(srcPath) {
  if (srcPath.startsWith("http://") || srcPath.startsWith("https://")) {
    const { buffer, mimeType } = await fetchRemoteImageBuffer(srcPath);
    const ext = mimeToImageExtension(mimeType).slice(1);
    return await OpenAI.toFile(buffer, `image.${ext}`, { type: mimeType });
  }
  const buf = fs.readFileSync(srcPath);
  const ext = path.extname(srcPath).toLowerCase().slice(1) || "png";
  const mime = imageMimeType(path.extname(srcPath).toLowerCase());
  return await OpenAI.toFile(buf, `image.${ext}`, { type: mime });
}

async function gpt2Generate({ prompt, outputDir, assetName, imageSize, aspectRatio, quality, n }) {
  if (!openaiClient) {
    throw new Error(
      "OPENAI_API_KEY is not set. → Run /slot-setup in chat to configure it safely, " +
      "or get a key at https://platform.openai.com/api-keys and add it via setup-keys."
    );
  }
  const size = pickGpt2Size(imageSize || "2K", aspectRatio || null);
  const q = quality || "high";  // default to "high"; "low"/"medium"/"high"/"auto"
  const numImages = Math.max(1, Math.min(10, n || 1));

  const t0 = Date.now();
  const result = await openaiClient.images.generate({
    model: "gpt-image-2",
    prompt,
    size,
    quality: q,
    n: numImages,
    output_format: "png",
  });
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

  const data = result.data || [];
  if (!data.length) throw new Error(
    "OpenAI returned no images. → Often transient — retry once. If it persists, " +
    "the prompt may have hit OpenAI's content policy; soften aggressive imagery and try again."
  );

  ensureDir(outputDir);
  const saved = [];
  for (let i = 0; i < data.length; i++) {
    const b64 = data[i].b64_json;
    if (!b64) {
      throw new Error("OpenAI returned a result without b64_json. SDK shape may have changed; check openai package version.");
    }
    const suffix = data.length > 1 ? `_${i + 1}` : "";
    const dest = saveB64Image(b64, "png", outputDir, `${assetName}${suffix}`);
    saved.push(dest);
    writeSidecar(dest, {
      tool: "gpt2_generate",
      provider: "OpenAI",
      model: "gpt-image-2",
      prompt,
      image_size: imageSize || "2K",
      gpt2_literal_size: size,
      aspect_ratio: aspectRatio || null,
      quality: q,
      reference_images: [],
      source_image: null,
      duration_seconds: Number(elapsed),
    });
  }

  return {
    provider: "OpenAI",
    model: "gpt-image-2",
    resolution: size,
    elapsed,
    paths: saved,
  };
}

async function gpt2Edit({ prompt, source, mask, outputDir, assetName, imageSize, aspectRatio, quality, n, extraReferences }) {
  if (!openaiClient) {
    throw new Error(
      "OPENAI_API_KEY is not set. → Run /slot-setup in chat to configure it safely, " +
      "or get a key at https://platform.openai.com/api-keys and add it via setup-keys."
    );
  }
  const size = pickGpt2Size(imageSize || "2K", aspectRatio || null);
  const q = quality || "high";
  const numImages = Math.max(1, Math.min(10, n || 1));

  // gpt-image-2's edit endpoint accepts an array of images for compositional
  // editing — the source plus any extra references go in together. mask is
  // optional and standalone.
  const sources = [source, ...(extraReferences || [])];
  const imageFiles = await Promise.all(sources.map(gpt2ReadImageInput));
  const maskFile = mask ? await gpt2ReadImageInput(mask) : undefined;

  const t0 = Date.now();
  const result = await openaiClient.images.edit({
    model: "gpt-image-2",
    image: imageFiles.length === 1 ? imageFiles[0] : imageFiles,
    ...(maskFile ? { mask: maskFile } : {}),
    prompt,
    size,
    quality: q,
    n: numImages,
    output_format: "png",
  });
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

  const data = result.data || [];
  if (!data.length) throw new Error(
    "OpenAI returned no edited images. → Often transient — retry once. If it persists, " +
    "the prompt may have hit OpenAI's content policy, or the source/reference set may be " +
    "outside the model's supported configurations."
  );

  ensureDir(outputDir);
  const saved = [];
  for (let i = 0; i < data.length; i++) {
    const b64 = data[i].b64_json;
    if (!b64) throw new Error("OpenAI returned a result without b64_json.");
    const suffix = data.length > 1 ? `_${i + 1}` : "";
    const dest = saveB64Image(b64, "png", outputDir, `${assetName}${suffix}`);
    saved.push(dest);
    writeSidecar(dest, {
      tool: "gpt2_edit",
      provider: "OpenAI",
      model: "gpt-image-2",
      prompt,
      image_size: imageSize || "2K",
      gpt2_literal_size: size,
      aspect_ratio: aspectRatio || null,
      quality: q,
      reference_images: extraReferences || [],
      source_image: source,
      mask: mask || null,
      duration_seconds: Number(elapsed),
    });
  }

  return {
    provider: "OpenAI",
    model: "gpt-image-2",
    resolution: size,
    elapsed,
    paths: saved,
  };
}

// NOTE: A `gpt2_smart_resize` tool was prototyped in v1.5.0–v1.5.2 but
// removed in v1.5.3. Reason: it was shipped without verifying output
// quality against fal.ai's purpose-built smart-resize endpoint, and the
// "we only ship skills that work" bar wasn't met. For multi-aspect
// recomposition, use `nb2_smart_resize` (fal.ai NB Pro for non-text
// sources; Gemini fallback for text-heavy sources without fal access).
// If a future verified gpt-image-2-based smart-resize proves better
// than the fal.ai path for specific cases, it can be added back here.

// ---------------------------------------------------------------------------
// Format result as MCP text content
// ---------------------------------------------------------------------------

function formatResult(result, header) {
  // Derive the folder all outputs were saved to. All paths from a single tool
  // call land in the same output_dir, so dirname of the first path is enough.
  // Surfaced explicitly as a "Folder:" line so the user always sees where
  // files landed — without needing to read individual paths.
  const folder = result.paths.length > 0
    ? path.dirname(result.paths[0])
    : "(no output saved)";
  const fileUri = folder !== "(no output saved)"
    ? "file:///" + folder.replace(/\\/g, "/")
    : null;

  const lines = [
    header,
    `  Provider: ${result.provider}`,
    `  Model: ${result.model}`,
    `  Resolution: ${result.resolution}`,
    `  Elapsed: ${result.elapsed}s`,
    `  Folder: ${folder}`,
  ];
  if (fileUri) {
    lines.push(`  Open: ${fileUri}`);
  }
  lines.push(`  Outputs (${result.paths.length}):`);
  for (const p of result.paths) {
    lines.push(`    - ${p}`);
  }
  return [{ type: "text", text: lines.join("\n") }];
}

// MCP error responses MUST carry isError:true at the result level so clients
// can distinguish a tool failure ("nb2_generate threw an exception") from a
// successful tool response that happens to contain the string "ERROR" (e.g.
// the LLM commenting on an error message in an image). Callers should return
// { content: formatError(...), isError: true }.
function formatError(label, err) {
  return [{ type: "text", text: `ERROR (${label}): ${err.message || err}` }];
}

// Optional measurement attachment. When a generation tool is called with
// `measure: true`, run nb2_measure on every output path, write a sidecar
// .metrics.json next to each, and append a metrics block to the response.
// Failures here are non-fatal: measurement is opt-in QA, not a precondition.
async function maybeAttachMetrics(result, args, label) {
  if (!args || args.measure !== true) return null;
  if (!result || !Array.isArray(result.paths) || result.paths.length === 0) return null;

  const attached = [];
  for (const p of result.paths) {
    try {
      const metrics = await measureImage(p);
      const sidecar = writeMetricsSidecar(p, metrics);
      attached.push({
        path: p,
        sidecar,
        summary: {
          dominant_color_oklch: metrics.dominant_color_oklch,
          fill_pct: metrics.fill_pct,
          bg_uniformity_score: metrics.bg_uniformity_score,
          edge_density: metrics.edge_density,
        },
      });
    } catch (err) {
      attached.push({ path: p, error: err.message || String(err) });
    }
  }
  return {
    type: "text",
    text:
      `\nMeasurement (opt-in, ${label}):\n` +
      attached
        .map((a) =>
          a.error
            ? `  - ${a.path}\n      measurement FAILED: ${a.error}`
            : `  - ${a.path}\n      sidecar: ${a.sidecar}\n      fill_pct: ${a.summary.fill_pct}, bg_uniformity: ${a.summary.bg_uniformity_score}, edge_density: ${a.summary.edge_density}\n      dominant_color_oklch (top ${a.summary.dominant_color_oklch.length}): ` +
              a.summary.dominant_color_oklch
                .slice(0, 3)
                .map((c) => `{l:${c.l}, c:${c.c}, h:${c.h}, pct:${c.pct}}`)
                .join(", "),
        )
        .join("\n"),
  };
}

// ---------------------------------------------------------------------------
// Tool definitions
// ---------------------------------------------------------------------------

const TOOLS = [
  {
    name: "nb2_generate",
    description:
      "Generate a new image with Nano Banana 2 (NB2). " +
      "Use for new symbols, key art, UI surfaces, backgrounds, and contact sheets. " +
      "Always pass a fully-composed slot-art prompt following the rules in shared/nb2_prompting.md. " +
      "Returns the absolute path(s) to the saved PNG(s).",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "The fully-composed NB2 prompt." },
        output_dir: { type: "string", description: "Output directory. Defaults to ~/Pictures/claude_nb2." },
        asset_name: { type: "string", description: "Base filename (no extension). Default: image.", default: "image" },
        image_size: {
          type: "string",
          enum: ["512", "1K", "2K", "4K"],
          description: "Output resolution. Default: 2K.",
          default: "2K",
        },
        aspect_ratio: {
          type: "string",
          enum: ["16:9","1:1","1:4","1:8","21:9","2:3","3:2","3:4","4:1","4:3","4:5","5:4","8:1","9:16","auto"],
          description: "Aspect ratio. Omit to let model infer from prompt context.",
        },
        references: {
          type: "array",
          items: { type: "string" },
          description: "Optional list of reference image paths or URLs (style references).",
        },
        measure: {
          type: "boolean",
          description:
            "Opt-in: run nb2_measure on each output PNG after generation, write a sidecar <basename>.metrics.json next to it, and append the metrics summary to the response. Default false — measurement is an explicit choice (adds ~1-2s per output). Used by /slot-step-08 for numeric audit checks.",
          default: false,
        },
      },
      required: ["prompt"],
    },
  },
  {
    name: "nb2_edit",
    description:
      "In-place edit / reskin of an existing image with NB2. " +
      "Pass the source image path and a prompt describing the change. " +
      "Used by slot-step-07 and for other edit operations. " +
      "Returns the path(s) to the saved PNG(s).",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "The edit instruction prompt." },
        source: { type: "string", description: "Absolute path or URL of the source image to edit." },
        output_dir: { type: "string", description: "Output directory. Defaults to ~/Pictures/claude_nb2." },
        asset_name: { type: "string", description: "Base filename (no extension). Default: edit.", default: "edit" },
        image_size: {
          type: "string",
          enum: ["512", "1K", "2K", "4K"],
          default: "2K",
        },
        aspect_ratio: {
          type: "string",
          enum: ["16:9","1:1","1:4","1:8","21:9","2:3","3:2","3:4","4:1","4:3","4:5","5:4","8:1","9:16","auto"],
        },
        extra_references: {
          type: "array",
          items: { type: "string" },
          description: "Additional reference images (beyond the source) to guide the edit.",
        },
        measure: {
          type: "boolean",
          description:
            "Opt-in: run nb2_measure on each output PNG after generation, write a sidecar <basename>.metrics.json next to it, and append the metrics summary to the response. Default false. Used by /slot-step-08 for numeric audit checks.",
          default: false,
        },
      },
      required: ["prompt", "source"],
    },
  },
  {
    name: "nb2_upscale",
    description:
      "Path-A 4K upscale: pass an approved source image and a 6-part preservation prompt " +
      "(see shared/upscale_workflow.md). NB2 returns a 4K version that preserves the source's " +
      "identity, pose, palette, and rendering style. Review against the 8-axis rubric and iterate on failure.",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "The 6-part preservation prompt for the upscale." },
        source: { type: "string", description: "Absolute path or URL of the approved source image." },
        output_dir: { type: "string", description: "Output directory. Defaults to ~/Pictures/claude_nb2." },
        asset_name: { type: "string", description: "Base filename (no extension). Default: upscale.", default: "upscale" },
        image_size: {
          type: "string",
          enum: ["1K", "2K", "4K"],
          default: "4K",
        },
        measure: {
          type: "boolean",
          description:
            "Opt-in: run nb2_measure on each output PNG after upscale, write a sidecar <basename>.metrics.json next to it, and append the metrics summary to the response. Default false. Used by /slot-step-08 to verify the upscale preserved fill % and dominant colors against the source.",
          default: false,
        },
      },
      required: ["prompt", "source"],
    },
  },
  {
    name: "nb2_smart_resize",
    description:
      "Pixel-perfect multi-size resize of an approved asset to one or more exact target dimensions. " +
      "Either key works (both are fully implemented). When both are set, fal.ai runs because its " +
      "purpose-built endpoint (Nano Banana Pro, single API call) beats Gemini's path (NB2 + N calls + " +
      "pngjs center-crop) for this task. " +
      "Pass the source image and target sizes as 'WxH' strings. Returns paths to each resized output.",
    inputSchema: {
      type: "object",
      properties: {
        source: { type: "string", description: "Absolute path or URL of the source image." },
        output_dir: { type: "string", description: "Output directory. Defaults to ~/Pictures/claude_nb2." },
        asset_name: { type: "string", description: "Base filename prefix (no extension). Default: resize.", default: "resize" },
        target_sizes: {
          type: "array",
          items: { type: "string" },
          description: "Target sizes as WxH strings. Default: [\"2048x2048\", \"1920x1080\", \"1080x1920\"] (2K-tier marketing trio).",
        },
        prompt: {
          type: "string",
          description: "Optional extra instruction forwarded to the underlying model alongside the auto-generated recompose prompt. Leave empty to preserve the source content as closely as possible. Works on both fal.ai and Gemini backends.",
        },
      },
      required: ["source"],
    },
  },
  {
    name: "nb2_stage_image",
    description:
      "Copy an external image (chat-attached, downloaded, anywhere on disk, or a URL) into the safe inputs folder so it can then be passed as `source` or `references` to nb2_edit / nb2_upscale / nb2_smart_resize. " +
      "**Use this whenever a user pastes/attaches an image in chat and asks for an edit, upscale, or resize** — chat-attached images live in temp paths outside the allowed-roots envelope, and the other tools will reject them otherwise. " +
      "Also use it for any external image (download, screenshot, asset from another folder) that lives outside the active project root. " +
      "Returns the staged absolute path inside ~/.h5g-slot-art-creator/inputs/. Idempotent — each call gets a fresh unique filename so concurrent staging never collides.",
    inputSchema: {
      type: "object",
      properties: {
        source: {
          type: "string",
          description: "Absolute path to a local image file (PNG/JPG/JPEG/WEBP), a `~/`-relative path, OR an `http(s)://` URL. The path does NOT need to be inside any allowed root — bypassing that restriction is the purpose of staging.",
        },
        label: {
          type: "string",
          description: "Optional naming prefix for the staged file. Default: `chat_input`. Use a self-documenting prefix like `user_paste_HP1` or `ref_for_bezel` so ~/.h5g-slot-art-creator/inputs/ stays readable as it grows.",
          default: "chat_input",
        },
      },
      required: ["source"],
    },
  },
  {
    name: "gpt2_generate",
    description:
      "Generate an image with OpenAI's **gpt-image-2** model (separate from NB2). " +
      "Use this when the user explicitly asks for gpt-image-2, OR when the task " +
      "benefits from gpt-image-2's strengths over NB2: " +
      "(1) accurate text rendering in the image (paytable labels, multipliers, banner copy, logos with specific wordmarks — gpt-image-2 substantially outperforms NB2 here); " +
      "(2) compositional briefs with very specific multi-element layouts and structural reasoning. " +
      "Resolution: 1K or 2K only. 2K (2048×2048) is gpt-image-2's stable native ceiling. For genuine 4K marketing output, generate at 2K here then run nb2_upscale on the approved result — that's a tested path. (We don't expose gpt-image-2's experimental 4K sizes because OpenAI itself doesn't promise they work.) " +
      "Requires OPENAI_API_KEY. Per-image cost is meaningfully higher than NB2 — use for hero assets and text-heavy surfaces, not routine symbol generation. " +
      "Output: PNG saved to output_dir.",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "The text prompt for gpt-image-2. Plain prose works well — gpt-image-2 plans the composition internally." },
        output_dir: { type: "string", description: "Output directory. Defaults to ~/Pictures/claude_nb2." },
        asset_name: { type: "string", description: "Base filename (no extension). Default: image.", default: "image" },
        image_size: {
          type: "string",
          enum: ["1K", "2K"],
          description: "Abstract size tier (mapped to gpt-image-2 literal sizes internally). Default: 2K — gpt-image-2's stable native ceiling. For genuine 4K, generate at 2K here then run nb2_upscale on the approved result.",
          default: "2K",
        },
        aspect_ratio: {
          type: "string",
          enum: ["1:1", "16:9", "9:16", "3:2", "2:3", "auto"],
          description: "Aspect ratio. Combined with image_size to pick the literal gpt-image-2 size. Default: 1:1 (square).",
        },
        quality: {
          type: "string",
          enum: ["low", "medium", "high", "auto"],
          description: "gpt-image-2 quality tier. Higher = better but slower and more expensive. Default: high.",
          default: "high",
        },
        n: {
          type: "integer",
          minimum: 1,
          maximum: 10,
          description: "Number of variants to generate in one call. Default: 1.",
          default: 1,
        },
        measure: {
          type: "boolean",
          description:
            "Opt-in: run nb2_measure on each output PNG after generation, write a sidecar <basename>.metrics.json next to it, and append the metrics summary to the response. Default false. Used by /slot-step-08 for numeric audit checks on text-heavy assets.",
          default: false,
        },
      },
      required: ["prompt"],
    },
  },
  {
    name: "gpt2_edit",
    description:
      "Edit an image (or compose multiple images) using OpenAI's **gpt-image-2** model. " +
      "Use when the user explicitly asks for gpt-image-2, OR when the edit needs: " +
      "(1) preserving or adding precise text in the output; " +
      "(2) compositional editing combining 2+ source images (the source plus extra_references are all passed together); " +
      "(3) high-resolution edits at 4K. " +
      "Optional mask narrows the edit to a specific region. " +
      "Requires OPENAI_API_KEY. " +
      "If the source is a chat-attached image, run nb2_stage_image first (the staging tool works for any downstream tool including this one). " +
      "Output: PNG saved to output_dir.",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "Describe the desired edit — what to change, add, or compose." },
        source: { type: "string", description: "Absolute path or URL of the primary source image. Must be inside an allowed root (run nb2_stage_image first if it's chat-attached)." },
        mask: { type: "string", description: "Optional: absolute path to a mask image. Transparent regions in the mask indicate where edits are allowed; opaque regions are preserved." },
        extra_references: {
          type: "array",
          items: { type: "string" },
          description: "Additional reference images to combine compositionally with the source. gpt-image-2 accepts multiple images for compositional editing.",
        },
        output_dir: { type: "string", description: "Output directory. Defaults to ~/Pictures/claude_nb2." },
        asset_name: { type: "string", description: "Base filename (no extension). Default: edit.", default: "edit" },
        image_size: {
          type: "string",
          enum: ["1K", "2K"],
          description: "Abstract size tier. 2K is gpt-image-2's stable ceiling.",
          default: "2K",
        },
        aspect_ratio: {
          type: "string",
          enum: ["1:1", "16:9", "9:16", "3:2", "2:3", "auto"],
        },
        quality: {
          type: "string",
          enum: ["low", "medium", "high", "auto"],
          default: "high",
        },
        n: {
          type: "integer",
          minimum: 1,
          maximum: 10,
          default: 1,
        },
        measure: {
          type: "boolean",
          description:
            "Opt-in: run nb2_measure on each output PNG after edit, write a sidecar <basename>.metrics.json next to it, and append the metrics summary to the response. Default false. Used by /slot-step-08 to verify the edit preserved the source's structural metrics.",
          default: false,
        },
      },
      required: ["prompt", "source"],
    },
  },
  {
    name: "nb2_measure",
    description:
      "Measure an existing PNG and return OKLCH dominant colors, pixel fill %, " +
      "background uniformity, edge density, and bounding box. Writes a sidecar " +
      "<basename>.metrics.json next to the image. Used by /slot-step-08 to drive " +
      "numeric audit checks (tier-pairwise saturation deltas, LP warmth scan, " +
      "non-flat-BG detection). Opt-in — generation tools don't auto-measure " +
      "unless you pass `measure: true`. Read-only with respect to the image " +
      "itself (only writes the sidecar JSON).",
    inputSchema: {
      type: "object",
      properties: {
        source: {
          type: "string",
          description:
            "Absolute path to a PNG. Must be inside an allowed root (run nb2_stage_image first if it's chat-attached).",
        },
      },
      required: ["source"],
    },
  },
];

// ---------------------------------------------------------------------------
// MCP server
// ---------------------------------------------------------------------------

const server = new Server(
  { name: "slot-art-creator-node-nb2", version: SERVER_VERSION },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "nb2_generate") {
      const assetName = sanitizeAssetName(args.asset_name, "image");
      const references = await validateImageInputs(args.references || null, "references");
      const result = await dispatchGenerate({
        prompt: args.prompt,
        outputDir: resolveOutputDir(args.output_dir),
        assetName,
        imageSize: args.image_size || "2K",
        aspectRatio: args.aspect_ratio || null,
        references,
      });
      const content = formatResult(result, "nb2_generate OK");
      const metricsBlock = await maybeAttachMetrics(result, args, "nb2_generate");
      if (metricsBlock) content.push(metricsBlock);
      return { content };
    }

    if (name === "nb2_edit") {
      const assetName = sanitizeAssetName(args.asset_name, "edit");
      const source = await validateImageInput(args.source, "source");
      const extraReferences = await validateImageInputs(args.extra_references || null, "extra_references");
      const result = await dispatchEdit({
        prompt: args.prompt,
        source,
        outputDir: resolveOutputDir(args.output_dir),
        assetName,
        imageSize: args.image_size || "2K",
        aspectRatio: args.aspect_ratio || null,
        extraReferences,
      });
      const content = formatResult(result, "nb2_edit OK");
      const metricsBlock = await maybeAttachMetrics(result, args, "nb2_edit");
      if (metricsBlock) content.push(metricsBlock);
      return { content };
    }

    if (name === "nb2_upscale") {
      const assetName = sanitizeAssetName(args.asset_name, "upscale");
      const source = await validateImageInput(args.source, "source");
      const result = await dispatchEdit({
        prompt: args.prompt,
        source,
        outputDir: resolveOutputDir(args.output_dir),
        assetName,
        imageSize: args.image_size || "4K",
        aspectRatio: null,
        extraReferences: null,
      });
      const content = formatResult(result, "nb2_upscale OK");
      const metricsBlock = await maybeAttachMetrics(result, args, "nb2_upscale");
      if (metricsBlock) content.push(metricsBlock);
      return { content };
    }

    if (name === "nb2_smart_resize") {
      // Dispatch:
      //   FAL_KEY present       → fal-ai/smart-resize (purpose-built endpoint,
      //                           uses nano-banana-pro internally, single API call)
      //   Otherwise GEMINI_KEY  → our Gemini implementation using NB2
      //                           (gemini-3.1-flash-image-preview), one call per
      //                           target size + center-crop via pngjs
      //   Neither               → clear error
      const targetSizes = validateTargetSizes(args.target_sizes);
      const outputDir = resolveOutputDir(args.output_dir);
      const assetName = sanitizeAssetName(args.asset_name, "resize");
      const source = await validateImageInput(args.source, "source");

      if (FAL_KEY) {
        const result = await falSmartResize({
          source,
          outputDir,
          assetName,
          targetSizes,
          prompt: args.prompt || null,
        });
        return { content: formatResult(result, "nb2_smart_resize OK (fal.ai / nano-banana-pro)") };
      }

      if (GEMINI_KEY) {
        const result = await geminiSmartResize({
          source,
          outputDir,
          assetName,
          targetSizes,
          prompt: args.prompt || null,
        });
        return { content: formatResult(result, "nb2_smart_resize OK (Gemini / NB2)") };
      }

      return {
        content: [{
          type: "text",
          text: "ERROR: nb2_smart_resize needs at least one API key. " +
                "Either works — both providers fully implement this tool.\n" +
                "  FAL_KEY:        node setup-keys.js --fal  (purpose-built NB Pro endpoint, single API call)\n" +
                "  GEMINI_API_KEY: node setup-keys.js --gemini  (NB2 + pngjs center-crop, one call per target)",
        }],
        isError: true,
      };
    }

    if (name === "nb2_stage_image") {
      const result = await stageImage({
        source: args.source,
        label: args.label || null,
      });
      return {
        content: formatResult(
          result,
          "nb2_stage_image OK — image is now usable as `source` or `references` for nb2_edit / nb2_upscale / nb2_smart_resize / gpt2_edit"
        ),
      };
    }

    if (name === "gpt2_generate") {
      const assetName = sanitizeAssetName(args.asset_name, "image");
      const result = await gpt2Generate({
        prompt: args.prompt,
        outputDir: resolveOutputDir(args.output_dir),
        assetName,
        imageSize: args.image_size || "2K",
        aspectRatio: args.aspect_ratio || null,
        quality: args.quality || "high",
        n: args.n || 1,
      });
      const content = formatResult(result, "gpt2_generate OK (OpenAI / gpt-image-2)");
      const metricsBlock = await maybeAttachMetrics(result, args, "gpt2_generate");
      if (metricsBlock) content.push(metricsBlock);
      return { content };
    }

    if (name === "gpt2_edit") {
      const assetName = sanitizeAssetName(args.asset_name, "edit");
      const source = await validateImageInput(args.source, "source");
      const mask = args.mask ? await validateImageInput(args.mask, "mask") : null;
      const extraReferences = await validateImageInputs(args.extra_references || null, "extra_references");
      const result = await gpt2Edit({
        prompt: args.prompt,
        source,
        mask,
        extraReferences,
        outputDir: resolveOutputDir(args.output_dir),
        assetName,
        imageSize: args.image_size || "2K",
        aspectRatio: args.aspect_ratio || null,
        quality: args.quality || "high",
        n: args.n || 1,
      });
      const content = formatResult(result, "gpt2_edit OK (OpenAI / gpt-image-2)");
      const metricsBlock = await maybeAttachMetrics(result, args, "gpt2_edit");
      if (metricsBlock) content.push(metricsBlock);
      return { content };
    }

    if (name === "nb2_measure") {
      const source = await validateImageInput(args.source, "source");
      const metrics = await measureImage(source);
      const sidecar = writeMetricsSidecar(source, metrics);
      const lines = [
        "nb2_measure OK",
        `  Source: ${source}`,
        `  Sidecar: ${sidecar}`,
        `  Dimensions: ${metrics.width}x${metrics.height}`,
        `  fill_pct: ${metrics.fill_pct}`,
        `  bg_uniformity_score: ${metrics.bg_uniformity_score}`,
        `  edge_density: ${metrics.edge_density}`,
        `  bounding_box: ${metrics.bounding_box ? `${metrics.bounding_box.w}x${metrics.bounding_box.h} at (${metrics.bounding_box.x}, ${metrics.bounding_box.y})` : "(none)"}`,
        `  dominant_color_oklch (top ${metrics.dominant_color_oklch.length}):`,
      ];
      for (const c of metrics.dominant_color_oklch) {
        lines.push(`    - l:${c.l} c:${c.c} h:${c.h}° (${(c.pct * 100).toFixed(1)}%)`);
      }
      lines.push("");
      lines.push("Summary (the subset embedded into project.json.assets.*.metrics_summary):");
      lines.push(JSON.stringify({
        measured_iteration: metrics.measured_iteration,
        last_measured: metrics.last_measured,
        dominant_color_oklch: metrics.dominant_color_oklch,
        fill_pct: metrics.fill_pct,
        bg_uniformity_score: metrics.bg_uniformity_score,
        edge_density: metrics.edge_density,
      }, null, 2));
      return { content: [{ type: "text", text: lines.join("\n") }] };
    }

    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
  } catch (err) {
    if (err instanceof McpError) throw err;
    return { content: formatError(name, err), isError: true };
  }
});

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

const transport = new StdioServerTransport();
await server.connect(transport);
