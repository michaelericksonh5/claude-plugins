#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];
const warnings = [];
const placeholderMarkers = ["TO" + "DO", "FIX" + "ME", "T" + "BD", "\\[" + "INSERT", "<" + "placeholder>"];

function exists(relativePath) {
  return fs.existsSync(path.join(root, relativePath));
}

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

function fail(message) {
  errors.push(message);
}

function warn(message) {
  warnings.push(message);
}

function parseJson(relativePath) {
  try {
    return JSON.parse(read(relativePath));
  } catch (error) {
    fail(`${relativePath}: invalid JSON: ${error.message}`);
    return null;
  }
}

const manifest = parseJson(".claude-plugin/plugin.json");
if (!manifest) process.exit(1);

if (!/^[a-z0-9-]+$/.test(manifest.name || "")) {
  fail(".claude-plugin/plugin.json: name must be kebab-case");
}

if ((manifest.skills || []).some((skillPath) => String(skillPath).startsWith("./skills/"))) {
  fail(".claude-plugin/plugin.json: do not list standard ./skills/* entries; Claude auto-discovers the skills directory and duplicate entries cause duplicate skills at runtime");
}

if (manifest.hooks) {
  const hookPath = String(manifest.hooks).startsWith("./") ? manifest.hooks.slice(2) : manifest.hooks;
  if (hookPath === "hooks/hooks.json") {
    fail(".claude-plugin/plugin.json: do not list hooks/hooks.json; Claude auto-loads the standard hooks file and duplicate entries fail at runtime");
  }
}

const skillPaths = exists("skills")
  ? fs.readdirSync(path.join(root, "skills"), { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => `./skills/${entry.name}`)
  : [];

for (const skillPath of skillPaths) {
  if (!skillPath.startsWith("./")) {
    fail(`skill path must start with ./: ${skillPath}`);
    continue;
  }

  const relativeSkillPath = skillPath.slice(2);
  const skillFile = `${relativeSkillPath}/SKILL.md`;
  if (!exists(skillFile)) {
    fail(`missing skill entrypoint: ${skillFile}`);
    continue;
  }

  const content = read(skillFile);
  const lines = content.split(/\r?\n/).length;
  if (lines > 500) {
    fail(`${skillFile}: SKILL.md exceeds 500 lines (${lines})`);
  }

  if (!content.startsWith("---")) {
    fail(`${skillFile}: missing YAML frontmatter`);
  }

  const descriptionMatch = content.match(/^description:\s*(.+)$/m);
  if (!descriptionMatch || descriptionMatch[1].trim().length < 40) {
    fail(`${skillFile}: description is missing or too thin`);
  }

  if (new RegExp(`\\b(${placeholderMarkers.join("|")})\\b`, "i").test(content)) {
    fail(`${skillFile}: contains placeholder marker`);
  }

  const refs = [...content.matchAll(/\[.*?\]\(([^)]+\.md)\)/g)].map((match) => match[1]);
  for (const ref of refs) {
    const refPath = `${relativeSkillPath}/${ref}`;
    if (!exists(refPath)) {
      fail(`${skillFile}: missing referenced file ${ref}`);
    }
  }
}

if (manifest.hooks) {
  const hookPath = manifest.hooks.startsWith("./") ? manifest.hooks.slice(2) : manifest.hooks;
  const hooks = parseJson(hookPath);
  if (hooks && !hooks.hooks) {
    fail(`${hookPath}: missing top-level hooks object`);
  }
}

for (const agentPath of manifest.agents || []) {
  if (!agentPath.startsWith("./")) {
    fail(`agent path must start with ./: ${agentPath}`);
    continue;
  }
  const relativeAgentPath = agentPath.slice(2);
  if (!exists(relativeAgentPath)) {
    fail(`missing agent file: ${relativeAgentPath}`);
    continue;
  }
  const content = read(relativeAgentPath);
  if (!content.startsWith("---")) {
    fail(`${relativeAgentPath}: missing YAML frontmatter`);
  }
  if (!/^name:\s*[a-z0-9-]+$/m.test(content)) {
    fail(`${relativeAgentPath}: missing kebab-case name`);
  }
  if (!/^description:\s*.+$/m.test(content)) {
    fail(`${relativeAgentPath}: missing description`);
  }
}

const hookScript = "hooks/slot-math-prompt-guard.mjs";
if (!exists(hookScript)) {
  fail(`missing hook script: ${hookScript}`);
} else if (!read(hookScript).includes("UserPromptSubmit")) {
  warn(`${hookScript}: does not mention UserPromptSubmit`);
}

if (warnings.length) {
  console.log("Warnings:");
  for (const message of warnings) console.log(`- ${message}`);
}

if (errors.length) {
  console.error("Validation failed:");
  for (const message of errors) console.error(`- ${message}`);
  process.exit(1);
}

console.log("OK: H5G Slot Math plugin structure validated.");

