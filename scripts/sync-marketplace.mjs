#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { inspect } from "node:util";

const SYNC_FIELDS = ["version", "description", "author", "license", "homepage", "repository"];

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const marketplacePath = path.join(rootDir, ".claude-plugin", "marketplace.json");

const options = parseArgs(process.argv.slice(2));
const checkOnly = options.check;

if (options.help) {
  console.log(`Usage: node scripts/sync-marketplace.mjs [--check] [--local-root <path>]

Sync .claude-plugin/marketplace.json from each plugin's plugin.json.

Options:
  --check              Exit nonzero if marketplace.json would change.
  --local-root <path>  Read GitHub-sourced plugin manifests from local sibling
                      checkouts instead of GitHub. Useful before publishing
                      plugin repo changes.
`);
  process.exit(0);
}

const originalText = await readFile(marketplacePath, "utf8");
const marketplace = JSON.parse(originalText);

const changes = [];

for (const plugin of marketplace.plugins ?? []) {
  const manifest = await readPluginManifest(plugin);

  for (const field of SYNC_FIELDS) {
    if (!(field in manifest)) {
      continue;
    }

    const nextValue = normalizeFieldValue(field, manifest[field]);
    if (nextValue === undefined) {
      continue;
    }

    if (!deepEqual(plugin[field], nextValue)) {
      changes.push(`${plugin.name}: ${field} ${formatChange(plugin[field])} -> ${formatChange(nextValue)}`);
      plugin[field] = nextValue;
    }
  }

  if (plugin.source && typeof plugin.source === "object" && "sha" in plugin.source) {
    changes.push(`${plugin.name}: removed source.sha`);
    delete plugin.source.sha;
  }
}

const nextText = `${formatJson(marketplace)}\n`;

if (nextText !== originalText) {
  if (checkOnly) {
    console.error("marketplace.json is out of sync:");
    for (const change of changes) {
      console.error(`- ${change}`);
    }
    process.exit(1);
  }

  await writeFile(marketplacePath, nextText, "utf8");
  console.log(`Synced marketplace.json (${changes.length} change${changes.length === 1 ? "" : "s"}).`);
  for (const change of changes) {
    console.log(`- ${change}`);
  }
} else {
  console.log("marketplace.json is already in sync.");
}

async function readPluginManifest(plugin) {
  if (typeof plugin.source === "string") {
    return readLocalPluginManifest(plugin);
  }

  if (plugin.source && typeof plugin.source === "object" && isGitHubBackedSource(plugin.source)) {
    if (options.localRoot) {
      return readLocalGitHubBackedPluginManifest(plugin);
    }

    return fetchGitHubPluginManifest(plugin);
  }

  throw new Error(`${plugin.name}: unsupported source ${formatChange(plugin.source)}`);
}

async function readLocalPluginManifest(plugin) {
  const manifestPath = path.resolve(rootDir, plugin.source, ".claude-plugin", "plugin.json");
  const text = await readFile(manifestPath, "utf8");
  return JSON.parse(text);
}

async function readLocalGitHubBackedPluginManifest(plugin) {
  const repo = getGitHubRepo(plugin.source);
  if (!repo) {
    throw new Error(`${plugin.name}: cannot resolve local checkout for ${formatChange(plugin.source)}`);
  }

  const pluginRoot = path.join(options.localRoot, repo.name);
  const manifestPath = plugin.source.source === "git-subdir"
    ? path.join(pluginRoot, plugin.source.path, ".claude-plugin", "plugin.json")
    : path.join(pluginRoot, ".claude-plugin", "plugin.json");
  const text = await readFile(manifestPath, "utf8");
  return JSON.parse(text);
}

async function fetchGitHubPluginManifest(plugin) {
  const repo = getGitHubRepo(plugin.source);
  if (!repo) {
    throw new Error(`${plugin.name}: only GitHub-backed sources are supported (${formatChange(plugin.source)})`);
  }

  const manifestPath = plugin.source.source === "git-subdir"
    ? `${plugin.source.path.replace(/^\/+|\/+$/g, "")}/.claude-plugin/plugin.json`
    : ".claude-plugin/plugin.json";
  const ref = plugin.source.ref || "HEAD";
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  const headers = {
    "User-Agent": "h5g-plugins-marketplace-sync",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    `https://raw.githubusercontent.com/${repo.owner}/${repo.name}/${encodeURIComponent(ref)}/${manifestPath}`,
    { headers },
  );

  if (!response.ok) {
    throw new Error(`${plugin.name}: failed to fetch ${manifestPath} (${response.status} ${response.statusText})`);
  }

  const text = await response.text();
  return JSON.parse(text);
}

function isGitHubBackedSource(source) {
  return (
    (source.source === "url" && typeof source.url === "string")
    || (source.source === "github" && typeof source.repo === "string")
    || (source.source === "git-subdir" && typeof source.url === "string" && typeof source.path === "string")
  );
}

function getGitHubRepo(source) {
  if (source.source === "github") {
    const [owner, name] = source.repo.split("/");
    return owner && name ? { owner, name } : undefined;
  }

  return parseGitHubRepo(source.url);
}

function parseGitHubRepo(url) {
  const match = url.match(/^https:\/\/github\.com\/([^/]+)\/([^/.#?]+)(?:\.git)?(?:[/?#].*)?$/);
  if (!match) {
    return undefined;
  }

  return { owner: match[1], name: match[2] };
}

function parseArgs(argv) {
  const parsed = {
    check: false,
    help: false,
    localRoot: undefined,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--check") {
      parsed.check = true;
      continue;
    }
    if (arg === "--help" || arg === "-h") {
      parsed.help = true;
      continue;
    }
    if (arg === "--local-root") {
      const localRoot = argv[index + 1];
      if (!localRoot) {
        throw new Error("--local-root requires a path");
      }
      parsed.localRoot = path.resolve(localRoot);
      index += 1;
      continue;
    }

    throw new Error(`Unknown option: ${arg}`);
  }

  return parsed;
}

function normalizeFieldValue(field, value) {
  if (field === "repository") {
    if (typeof value === "string") {
      return value;
    }

    if (value && typeof value === "object" && typeof value.url === "string") {
      return value.url.replace(/^git\+/, "");
    }

    return undefined;
  }

  return value;
}

function deepEqual(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function formatChange(value) {
  return inspect(value, { compact: true, depth: 4, breakLength: 120 });
}

function formatJson(value) {
  return formatValue(value, 0);
}

function formatValue(value, indentLevel, key = "") {
  if (Array.isArray(value)) {
    if (value.every((item) => item === null || ["string", "number", "boolean"].includes(typeof item))) {
      return `[${value.map((item) => JSON.stringify(item)).join(", ")}]`;
    }

    const indent = " ".repeat(indentLevel);
    const childIndent = " ".repeat(indentLevel + 2);
    return `[\n${value.map((item) => `${childIndent}${formatValue(item, indentLevel + 2)}`).join(",\n")}\n${indent}]`;
  }

  if (value && typeof value === "object") {
    const entries = Object.entries(value);
    if (key === "source" && entries.every(([, entryValue]) => entryValue === null || typeof entryValue !== "object")) {
      return `{ ${entries.map(([entryKey, entryValue]) => `${JSON.stringify(entryKey)}: ${formatValue(entryValue, 0)}`).join(", ")} }`;
    }

    const indent = " ".repeat(indentLevel);
    const childIndent = " ".repeat(indentLevel + 2);
    return `{\n${entries
      .map(([entryKey, entryValue]) => `${childIndent}${JSON.stringify(entryKey)}: ${formatValue(entryValue, indentLevel + 2, entryKey)}`)
      .join(",\n")}\n${indent}}`;
  }

  return JSON.stringify(value);
}
