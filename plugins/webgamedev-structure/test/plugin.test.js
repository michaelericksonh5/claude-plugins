"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const assert = require("node:assert/strict");

const {
  classifyPath,
  pathsCanOverride
} = require("../scripts/lib/gameforge-paths");
const {
  buildP4Command,
  rejectDangerous
} = require("../scripts/lib/p4-common");
const {
  REQUIRED_FILES,
  findForbiddenEntries,
  validatePackage
} = require("../scripts/lib/validate-package");

const ROOT = path.resolve(__dirname, "..");

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, relativePath), "utf8"));
}

function readText(relativePath) {
  return fs.readFileSync(path.join(ROOT, relativePath), "utf8");
}

test("manifest is skills-only and inert", () => {
  const manifest = readJson(".claude-plugin/plugin.json");
  assert.equal(manifest.name, "webgamedev-structure");
  assert.equal(manifest.version, "0.2.1");
  assert.equal(Object.hasOwn(manifest, "skills"), false);
  assert.equal(Object.hasOwn(manifest, "hooks"), false);
  assert.equal(Object.hasOwn(manifest, "mcpServers"), false);
  assert.equal(Object.hasOwn(manifest, "agents"), false);
});

test("required package files exist", () => {
  for (const relativePath of [
    "README.md",
    "LICENSE",
    ".gitignore",
    "package.json",
    "scripts/lib/gameforge-paths.js",
    "scripts/lib/p4-common.js",
    "scripts/lib/webgamedev-p4.js",
    "scripts/p4-doctor.ps1",
    "scripts/p4-doctor.sh",
    "docs/ARTIST_QUICKSTART.md",
    "skills/webgamedev-structure/SKILL.md",
    "skills/webgamedev-structure/PERFORCE_CLI_REFERENCE.md",
    "skills/webgamedev-structure/ASSET_FOLDER_INTAKE.md"
  ]) {
    assert.equal(fs.existsSync(path.join(ROOT, relativePath)), true, relativePath);
  }
});

test("skill entry includes GameForge, P4, and asset-folder trigger terms", () => {
  const skill = readText("skills/webgamedev-structure/SKILL.md");
  assert.match(skill, /^name: webgamedev-structure$/m);
  for (const term of [
    "GameForge",
    "Game Forge",
    "gameforge",
    "game forge",
    "webdev",
    "webgamedev",
    "//webgamedev",
    "Perforce",
    "P4",
    "p4",
    "sync",
    "syncing",
    "synching",
    "checkout",
    "check out",
    "checking out",
    "check in",
    "checking in",
    "submit",
    "push updates",
    "pushing updates",
    "add assets",
    "asset folders",
    "dropped folders"
  ]) {
    assert.match(skill, new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});

test("skill entry references existing sibling docs", () => {
  const skill = readText("skills/webgamedev-structure/SKILL.md");
  const refs = [...skill.matchAll(/`([A-Z_]+\.md)`/g)].map((match) => match[1]);
  assert.ok(refs.length >= 5);
  for (const ref of refs) {
    assert.equal(fs.existsSync(path.join(ROOT, "skills/webgamedev-structure", ref)), true, ref);
  }
});

test("path classifier recognizes local runtime asset categories", () => {
  const symbol = classifyPath("GAMEFORGE_folderstructure\\ASSETS\\LOCAL\\texture\\portrait\\symbols\\hp1.webp");
  assert.equal(symbol.valid, true);
  assert.equal(symbol.scope, "LOCAL");
  assert.equal(symbol.category, "texture/portrait/symbols");

  const spine = classifyPath("//webgamedev/mygame/texture/portrait/animations/spine/bonus_intro.json");
  assert.equal(spine.valid, true);
  assert.equal(spine.scope, "LOCAL");
  assert.equal(spine.category, "texture/portrait/spine");

  const theme = classifyPath("//webgamedev/mygame/data/themes/theme-h5g.json");
  assert.equal(theme.valid, true);
  assert.equal(theme.category, "data/themes");
});

test("path classifier maps _Common-New as GLOBAL and verifies overrides", () => {
  const globalPath = "//webgamedev/assets/_Common-New/texture/portrait/ui/bottom_toolbar/options_modal/panel.webp";
  const localPath = "//webgamedev/mygame/texture/portrait/ui/bottom_toolbar/options_modal/panel.webp";
  const globalInfo = classifyPath(globalPath);
  assert.equal(globalInfo.scope, "GLOBAL");
  assert.equal(globalInfo.valid, true);
  assert.equal(pathsCanOverride(globalPath, localPath), true);
  assert.equal(pathsCanOverride(globalPath, "//webgamedev/mygame/texture/portrait/ui/panel.webp"), false);
});

test("source assets are classified separately from runtime delivery", () => {
  const source = classifyPath("assets/freeGames/specialSymbol/freeGames_WD1/work/photoshop/wd1.psd");
  assert.equal(source.kind, "source");
  assert.equal(source.scope, "SOURCE");
  assert.equal(source.valid, true);
});

test("p4 command builder keeps read-only diagnostics direct", () => {
  assert.deepEqual(buildP4Command("login-status").args, ["login", "-s"]);
  assert.deepEqual(buildP4Command("client").args, ["client", "-o"]);
  assert.deepEqual(buildP4Command("where", { args: ["//webgamedev/mygame/..."] }).args, ["where", "//webgamedev/mygame/..."]);
  assert.deepEqual(buildP4Command("have", { args: ["//webgamedev/mygame/..."] }).args, ["have", "//webgamedev/mygame/..."]);
  assert.deepEqual(buildP4Command("files", { args: ["//webgamedev/mygame/..."] }).args, ["files", "//webgamedev/mygame/..."]);
  assert.deepEqual(buildP4Command("describe", { args: ["12345"] }).args, ["describe", "12345"]);
  assert.deepEqual(buildP4Command("print", { args: ["//webgamedev/mygame/file.webp#3"] }).args, ["print", "//webgamedev/mygame/file.webp#3"]);
  assert.deepEqual(buildP4Command("diff", { args: ["//webgamedev/mygame/..."] }).args, ["diff", "-sa", "//webgamedev/mygame/..."]);
});

test("mutating p4 operations require apply or preview flags", () => {
  const previewTargets = {
    sync: ["//webgamedev/mygame/..."],
    edit: ["//webgamedev/mygame/file.webp"],
    add: ["//webgamedev/mygame/file.webp"]
  };

  for (const [operation, args] of Object.entries(previewTargets)) {
    const preview = buildP4Command(operation, { args });
    assert.equal(preview.ok, true, operation);
    assert.equal(preview.preview, true, operation);
    assert.deepEqual(preview.args, [operation, "-n", ...args], operation);

    const apply = buildP4Command(operation, { args, apply: true });
    assert.equal(apply.ok, true, operation);
    assert.equal(apply.preview, false, operation);
    assert.deepEqual(apply.args, [operation, ...args], operation);
  }
});

test("reconcile automation is add/edit only", () => {
  const preview = buildP4Command("reconcile", { args: ["//webgamedev/mygame/..."] });
  assert.equal(preview.ok, true);
  assert.equal(preview.preview, true);
  assert.deepEqual(preview.args, ["reconcile", "-n", "-a", "-e", "//webgamedev/mygame/..."]);

  const apply = buildP4Command("reconcile", { args: ["//webgamedev/mygame/..."], apply: true });
  assert.equal(apply.ok, true);
  assert.equal(apply.preview, false);
  assert.deepEqual(apply.args, ["reconcile", "-a", "-e", "//webgamedev/mygame/..."]);
});

test("reconcile blocks delete, workspace, combined delete, and unsupported flags", () => {
  for (const flag of ["-d", "-ad", "-da", "-w", "-x"]) {
    const spec = buildP4Command("reconcile", { args: [flag, "//webgamedev/mygame/..."] });
    assert.equal(spec.ok, false, flag);
    assert.equal(spec.blocked, true, flag);
  }
});

test("submit requires apply, changelist, and description", () => {
  const missing = buildP4Command("submit", { apply: true });
  assert.equal(missing.ok, false);
  assert.equal(missing.checklist, true);

  const ready = buildP4Command("submit", {
    apply: true,
    change: "12345",
    description: "Add symbol exports"
  });
  assert.equal(ready.ok, true);
  assert.deepEqual(ready.args, ["submit", "-c", "12345", "-d", "Add symbol exports"]);
});

test("dangerous p4 operations are blocked", () => {
  assert.match(rejectDangerous("clean", []), /Blocked/);
  assert.match(rejectDangerous("delete", []), /H5G never-delete policy/);
  assert.match(rejectDangerous("move", []), /H5G never-delete policy/);
  assert.match(rejectDangerous("obliterate", []), /Blocked/);
  assert.match(rejectDangerous("revert", []), /H5G never-delete policy/);
  assert.match(rejectDangerous("typemap", []), /Blocked/);
  assert.match(rejectDangerous("resolve", []), /Blocked/);
  assert.match(rejectDangerous("reconcile", ["-d"]), /never-delete policy/);
  assert.match(rejectDangerous("reconcile", ["-w"]), /Blocked/);
  assert.equal(buildP4Command("delete", { args: ["//webgamedev/mygame/file.webp"] }).ok, false);
  assert.equal(buildP4Command("move", { args: ["//webgamedev/mygame/old.webp", "//webgamedev/mygame/new.webp"] }).ok, false);
  assert.equal(buildP4Command("revert", { args: ["//webgamedev/mygame/file.webp"] }).ok, false);
  assert.match(buildP4Command("edit", { args: ["-x", "//webgamedev/mygame/file.webp"] }).reason, /unsupported/);
});

test("package validator requires Perforce CLI reference", () => {
  assert.equal(REQUIRED_FILES.includes("skills/webgamedev-structure/PERFORCE_CLI_REFERENCE.md"), true);
});

test("package validator passes", () => {
  assert.deepEqual(validatePackage(), []);
});

test("package validator reports excluded artifacts and likely secrets", () => {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "webgamedev-package-"));
  try {
    for (const directory of ["node_modules", "dist", "build", "coverage", "generated", "credentials"]) {
      fs.mkdirSync(path.join(tempRoot, directory));
    }
    for (const file of [".env", ".env.local", "bundle.zip", "secret.pem", "aws_credentials.json", "id_rsa_test", "id_ed25519_work"]) {
      fs.writeFileSync(path.join(tempRoot, file), "placeholder");
    }

    const forbidden = findForbiddenEntries(tempRoot).sort();
    assert.deepEqual(forbidden, [
      ".env",
      ".env.local",
      "aws_credentials.json",
      "build",
      "bundle.zip",
      "coverage",
      "credentials",
      "dist",
      "generated",
      "id_ed25519_work",
      "id_rsa_test",
      "node_modules",
      "secret.pem"
    ]);

    const errors = validatePackage(tempRoot);
    assert.ok(errors.some((error) => error === "Forbidden package entry: .env"));
    assert.ok(errors.some((error) => error === "Forbidden package entry: node_modules"));
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
});
