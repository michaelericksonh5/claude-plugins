"use strict";

const path = require("node:path");

const GLOBAL_DEPOT_ROOT = "//webgamedev/assets/_Common-New";
const LOCAL_DEPOT_ROOT = "//webgamedev";
const DELIVERY_ROOT = "GAMEFORGE_folderstructure/ASSETS";

const AUDIO_CATEGORIES = new Set([
  "feature",
  "interface",
  "reel",
  "rollup",
  "symbols",
  "underscores"
]);

const TEXTURE_CATEGORIES = new Map([
  ["animations/spine", "spine"],
  ["animations/video", "video"],
  ["backgrounds", "background"],
  ["bigwin", "bigwin"],
  ["effects", "effects"],
  ["loading", "loading"],
  ["logo", "logo"],
  ["platform", "platform"],
  ["symbols", "symbols"],
  ["ui", "ui"]
]);

function normalizePath(input) {
  const raw = String(input || "")
    .trim()
    .replace(/\\/g, "/")
    .replace(/^([A-Za-z]):\//, "$1:/");
  const prefix = raw.startsWith("//") ? "//" : "";
  const body = prefix ? raw.slice(2) : raw;
  return `${prefix}${body.replace(/\/+/g, "/")}`
    .replace(/\/$/, "");
}

function splitPath(input) {
  return normalizePath(input).split("/").filter(Boolean);
}

function classifyDelivery(parts) {
  const rootIndex = parts.findIndex((part, index) => {
    return part === "GAMEFORGE_folderstructure" && parts[index + 1] === "ASSETS";
  });

  if (rootIndex === -1) {
    return null;
  }

  const scope = parts[rootIndex + 2];
  if (scope !== "GLOBAL" && scope !== "LOCAL") {
    return {
      kind: "delivery",
      valid: false,
      errors: ["Expected ASSETS/GLOBAL or ASSETS/LOCAL"]
    };
  }

  const relativeParts = parts.slice(rootIndex + 3);
  return describeAssetPath("delivery", scope, relativeParts, {
    root: `${DELIVERY_ROOT}/${scope}`
  });
}

function classifyDepot(normalized) {
  if (!normalized.startsWith("//webgamedev/")) {
    return null;
  }

  if (normalized === GLOBAL_DEPOT_ROOT || normalized.startsWith(`${GLOBAL_DEPOT_ROOT}/`)) {
    const relativeParts = splitPath(normalized.slice(GLOBAL_DEPOT_ROOT.length));
    return describeAssetPath("depot", "GLOBAL", relativeParts, {
      depotRoot: `${GLOBAL_DEPOT_ROOT}/`
    });
  }

  const parts = normalized.slice(2).split("/");
  const gameFolder = parts[1];
  const relativeParts = parts.slice(2);
  return describeAssetPath("depot", "LOCAL", relativeParts, {
    depotRoot: `${LOCAL_DEPOT_ROOT}/${gameFolder}/`,
    gameFolder
  });
}

function classifySource(parts) {
  const assetsIndex = parts.findIndex((part) => part === "assets");
  if (assetsIndex === -1) {
    return null;
  }

  return {
    kind: "source",
    scope: "SOURCE",
    category: parts[assetsIndex + 2] || parts[assetsIndex + 1] || null,
    relativePath: parts.slice(assetsIndex).join("/"),
    valid: true,
    errors: [],
    warnings: ["Source assets are not final runtime delivery assets"]
  };
}

function classifyPath(input) {
  const normalized = normalizePath(input);
  const parts = splitPath(normalized);

  return classifyDepot(normalized)
    || classifyDelivery(parts)
    || classifySource(parts)
    || {
      kind: "unknown",
      scope: null,
      category: null,
      relativePath: null,
      valid: false,
      errors: ["Path is not recognized as GameForge delivery, //webgamedev depot, or source assets"],
      warnings: []
    };
}

function describeAssetPath(kind, scope, relativeParts, extra) {
  const errors = [];
  const warnings = [];
  const category = categorizeRelativePath(relativeParts);

  if (relativeParts.length === 0) {
    errors.push("Missing asset path below root");
  }

  if (!category) {
    errors.push("Path does not match a documented GameForge asset category");
  }

  if (scope === "GLOBAL") {
    warnings.push("GLOBAL changes affect shared common assets and require review");
  }

  return {
    kind,
    scope,
    category,
    relativePath: relativeParts.join("/"),
    valid: errors.length === 0,
    errors,
    warnings,
    ...extra
  };
}

function categorizeRelativePath(parts) {
  if (parts[0] === "audio") {
    const audioType = parts[1];
    return AUDIO_CATEGORIES.has(audioType) ? `audio/${audioType}` : "audio";
  }

  if (parts[0] === "data") {
    return parts[1] === "themes" ? "data/themes" : "data";
  }

  if (parts[0] === "fonts") {
    return "fonts";
  }

  if (parts[0] === "texture") {
    const orientation = parts[1];
    const texturePath = parts.slice(2).join("/");
    for (const [prefix, category] of TEXTURE_CATEGORIES.entries()) {
      if (texturePath === prefix || texturePath.startsWith(`${prefix}/`)) {
        return `texture/${orientation}/${category}`;
      }
    }
  }

  return null;
}

function localToGlobalPath(input) {
  const info = classifyPath(input);
  if (info.scope !== "LOCAL" || !info.relativePath) {
    return null;
  }
  return `${GLOBAL_DEPOT_ROOT}/${info.relativePath}`;
}

function globalToLocalPath(input, gameFolder) {
  const info = classifyPath(input);
  if (info.scope !== "GLOBAL" || !info.relativePath || !gameFolder) {
    return null;
  }
  return `${LOCAL_DEPOT_ROOT}/${gameFolder}/${info.relativePath}`;
}

function pathsCanOverride(globalPath, localPath) {
  const globalInfo = classifyPath(globalPath);
  const localInfo = classifyPath(localPath);
  return globalInfo.scope === "GLOBAL"
    && localInfo.scope === "LOCAL"
    && globalInfo.relativePath
    && globalInfo.relativePath === localInfo.relativePath;
}

module.exports = {
  AUDIO_CATEGORIES,
  GLOBAL_DEPOT_ROOT,
  LOCAL_DEPOT_ROOT,
  TEXTURE_CATEGORIES,
  classifyPath,
  globalToLocalPath,
  localToGlobalPath,
  normalizePath,
  pathsCanOverride
};
