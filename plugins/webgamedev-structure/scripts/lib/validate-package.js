#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "../..");

const FORBIDDEN_DIR_NAMES = new Set([
  "node_modules",
  "dist",
  "build",
  "coverage",
  "generated"
]);

const FORBIDDEN_FILE_PATTERNS = [
  /^\.env(?:\..*)?$/i,
  /^.*\.zip$/i,
  /^.*\.pem$/i,
  /^.*credentials.*$/i,
  /^id_rsa.*$/i,
  /^id_ed25519.*$/i
];

const REQUIRED_FILES = [
  ".claude-plugin/plugin.json",
  "README.md",
  "LICENSE",
  ".gitignore",
  "package.json",
  "skills/webgamedev-structure/SKILL.md",
  "skills/webgamedev-structure/GAMEFORGE_STRUCTURE.md",
  "skills/webgamedev-structure/PERFORCE_CLI_REFERENCE.md",
  "skills/webgamedev-structure/PERFORCE_ARTIST_WORKFLOWS.md",
  "skills/webgamedev-structure/ASSET_PLACEMENT.md",
  "skills/webgamedev-structure/ASSET_FOLDER_INTAKE.md",
  "skills/webgamedev-structure/INTEGRATIONS.md",
  "skills/webgamedev-structure/SAFETY_RULES.md",
  "docs/P4_CONFIG_TEMPLATE.md",
  "docs/TYPMAP_RECOMMENDATIONS.md",
  "docs/ARTIST_QUICKSTART.md",
  "docs/TEAM_ROLLOUT.md",
  "scripts/lib/gameforge-paths.js",
  "scripts/lib/p4-common.js",
  "scripts/lib/webgamedev-p4.js",
  "scripts/p4-doctor.ps1",
  "scripts/p4-doctor.sh",
  "scripts/webgamedev-p4.ps1",
  "scripts/webgamedev-p4.sh",
  "scripts/validate-package.ps1",
  "test/plugin.test.js"
];

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, relativePath), "utf8"));
}

function exists(relativePath) {
  return fs.existsSync(path.join(ROOT, relativePath));
}

function findForbiddenEntries(root = ROOT) {
  const found = [];

  function walk(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      const relativePath = path.relative(root, fullPath).replace(/\\/g, "/");

      if (entry.isDirectory()) {
        if (FORBIDDEN_DIR_NAMES.has(entry.name) || FORBIDDEN_FILE_PATTERNS.some((pattern) => pattern.test(entry.name))) {
          found.push(relativePath);
          continue;
        }
        walk(fullPath);
      } else if (FORBIDDEN_FILE_PATTERNS.some((pattern) => pattern.test(entry.name))) {
        found.push(relativePath);
      }
    }
  }

  walk(root);
  return found;
}

function validatePackage(root = ROOT) {
  const errors = [];

  for (const file of REQUIRED_FILES) {
    if (!fs.existsSync(path.join(root, file))) {
      errors.push(`Missing required file: ${file}`);
    }
  }

  for (const entry of findForbiddenEntries(root)) {
    errors.push(`Forbidden package entry: ${entry}`);
  }

  if (errors.length === 0) {
    const manifest = JSON.parse(fs.readFileSync(path.join(root, ".claude-plugin/plugin.json"), "utf8"));
    if (manifest.name !== "webgamedev-structure") {
      errors.push("Manifest name must be webgamedev-structure");
    }
    if (manifest.version !== "0.2.1") {
      errors.push("Manifest version must be 0.2.1");
    }
    if (Object.prototype.hasOwnProperty.call(manifest, "skills")) {
      errors.push("Manifest must rely on default skills/ discovery");
    }
    for (const forbidden of ["hooks", "mcpServers", "agents"]) {
      if (Object.prototype.hasOwnProperty.call(manifest, forbidden)) {
        errors.push(`Manifest must not include ${forbidden}`);
      }
    }

    const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
    if (pkg.name !== "webgamedev-structure") {
      errors.push("package.json name must be webgamedev-structure");
    }
    if (!pkg.scripts || pkg.scripts.test !== "node --test") {
      errors.push("package.json must define test as node --test");
    }
  }

  return errors;
}

function main() {
  const errors = validatePackage();
  if (errors.length > 0) {
    for (const error of errors) {
      console.error(error);
    }
    return 1;
  }

  console.log("Package validation passed.");
  return 0;
}

if (require.main === module) {
  process.exitCode = main();
}

module.exports = {
  FORBIDDEN_DIR_NAMES,
  FORBIDDEN_FILE_PATTERNS,
  REQUIRED_FILES,
  findForbiddenEntries,
  validatePackage
};
