#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const zlib = require('zlib');

const recommendedSettings = {
  model: 'sonnet',
  availableModels: ['sonnet', 'haiku', 'opusplan'],
  effortLevel: 'low',
  env: {
    ANTHROPIC_DEFAULT_HAIKU_MODEL: 'claude-haiku-4-5-20251001',
    ANTHROPIC_DEFAULT_SONNET_MODEL: 'claude-sonnet-4-6',
    CLAUDE_CODE_EFFORT_LEVEL: 'auto',
    CLAUDE_CODE_DISABLE_1M_CONTEXT: '1'
  }
};

function readStdin() {
  return fs.readFileSync(0, 'utf8');
}

function parseJson(text, fallback = {}) {
  if (!text || !text.trim()) return fallback;
  return JSON.parse(text);
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function deepMerge(base, overlay) {
  const output = Array.isArray(base) ? base.slice() : { ...base };
  for (const [key, value] of Object.entries(overlay)) {
    if (isPlainObject(value) && isPlainObject(output[key])) {
      output[key] = deepMerge(output[key], value);
    } else if (Array.isArray(value)) {
      output[key] = value.slice();
    } else {
      output[key] = value;
    }
  }
  return output;
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function timestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function backupFile(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const parsed = path.parse(filePath);
  const backupPath = path.join(parsed.dir, `${parsed.name}.token-saver-backup.${timestamp()}${parsed.ext}`);
  fs.copyFileSync(filePath, backupPath);
  return backupPath;
}

function tokenSaverHookGroup(hookCommand) {
  return {
    matcher: 'Bash',
    hooks: [
      {
        type: 'command',
        command: hookCommand,
        timeout: 10
      }
    ]
  };
}

function isTokenSaverHookGroup(group) {
  if (!isPlainObject(group)) return false;
  const hooks = Array.isArray(group.hooks) ? group.hooks : [];
  return hooks.some((hook) => isPlainObject(hook) && typeof hook.command === 'string' && hook.command.includes('token-saver'));
}

function appendTokenSaverHooks(settings, hookCommand) {
  const output = deepMerge(settings, {});
  output.hooks = isPlainObject(output.hooks) ? output.hooks : {};
  const existingGroups = Array.isArray(output.hooks.PostToolUse) ? output.hooks.PostToolUse.slice() : [];
  if (!existingGroups.some(isTokenSaverHookGroup)) {
    existingGroups.push(tokenSaverHookGroup(hookCommand));
  }
  output.hooks.PostToolUse = existingGroups;
  return output;
}

function installSettings(options) {
  const home = options.home || os.homedir();
  const pluginRoot = options.pluginRoot;
  const platform = options.platform;
  const claudeDir = path.join(home, '.claude');
  const hooksDir = path.join(claudeDir, 'hooks');
  const helperDir = path.join(claudeDir, 'token-saver', 'lib');
  const settingsPath = path.join(claudeDir, 'settings.json');
  ensureDir(hooksDir);
  ensureDir(helperDir);

  let existing = {};
  if (fs.existsSync(settingsPath)) {
    existing = parseJson(fs.readFileSync(settingsPath, 'utf8'), {});
  }

  const backupPath = backupFile(settingsPath);
  const statusCommand = platform === 'windows'
    ? 'pwsh -NoProfile -ExecutionPolicy Bypass -File ~/.claude/token-saver-statusline.ps1'
    : '~/.claude/token-saver-statusline.sh';
  const hookCommand = platform === 'windows'
    ? 'pwsh -NoProfile -ExecutionPolicy Bypass -File ~/.claude/hooks/token-saver-filter-output.ps1'
    : '~/.claude/hooks/token-saver-filter-output.sh';

  const overlay = deepMerge(recommendedSettings, {
    statusLine: {
      type: 'command',
      command: statusCommand
    }
  });

  const merged = appendTokenSaverHooks(deepMerge(existing, overlay), hookCommand);
  fs.writeFileSync(settingsPath, `${JSON.stringify(merged, null, 2)}\n`);
  for (const helperName of ['token-saver-common.js', 'hook.js', 'statusline.js']) {
    fs.copyFileSync(path.join(pluginRoot, 'scripts', 'lib', helperName), path.join(helperDir, helperName));
  }

  if (platform === 'windows') {
    fs.copyFileSync(path.join(pluginRoot, 'statusline', 'token-saver-statusline.ps1'), path.join(claudeDir, 'token-saver-statusline.ps1'));
    fs.copyFileSync(path.join(pluginRoot, 'hooks', 'filter-output.ps1'), path.join(hooksDir, 'token-saver-filter-output.ps1'));
  } else {
    const statusDest = path.join(claudeDir, 'token-saver-statusline.sh');
    const hookDest = path.join(hooksDir, 'token-saver-filter-output.sh');
    fs.copyFileSync(path.join(pluginRoot, 'statusline', 'token-saver-statusline.sh'), statusDest);
    fs.copyFileSync(path.join(pluginRoot, 'hooks', 'filter-output.sh'), hookDest);
    fs.chmodSync(statusDest, 0o755);
    fs.chmodSync(hookDest, 0o755);
  }

  return {
    settingsPath,
    backupPath,
    changedKeys: ['model', 'availableModels', 'effortLevel', 'env', 'statusLine', 'hooks']
  };
}

function findText(value) {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(findText).join('\n');
  if (isPlainObject(value)) {
    for (const key of ['output', 'stdout', 'stderr', 'content', 'text']) {
      if (value[key]) return findText(value[key]);
    }
    return Object.values(value).map(findText).join('\n');
  }
  return '';
}

function summarizeHook(input) {
  const payload = parseJson(input, {});
  const command = findText(payload.tool_input && payload.tool_input.command ? payload.tool_input.command : payload.tool_input);
  const output = findText(payload.tool_response);
  const threshold = 12000;
  if (output.length <= threshold) {
    return '';
  }
  const commandLooksNoisy = /\b(test|pytest|npm|pnpm|yarn|go test|cargo test|gradle|mvn|log|tail)\b/i.test(command);
  if (!commandLooksNoisy) {
    return '';
  }
  const failurePattern = /(FAIL|FAILED|ERROR|Error:|Exception|Traceback|Assertion|panic:)/;
  const lines = output.split(/\r?\n/);
  const matches = lines.filter((line) => failurePattern.test(line)).slice(0, 80);
  const summary = matches.length > 0
    ? matches.join('\n')
    : output.split(/\r?\n/).slice(-80).join('\n');
  return JSON.stringify({
    hookEventName: 'PostToolUse',
    message: `token-saver: tool output was ${output.length} characters. Focus on this concise failure summary; the hook does not block or rewrite the original command result.\n${summary}`
  });
}

function formatStatusLine(input) {
  const data = parseJson(input, {});
  const modelName = (data.model && (data.model.display_name || data.model.id)) || 'unknown';
  const modelId = (data.model && data.model.id) || modelName;
  const effort = (data.effort && data.effort.level) || 'auto';
  const context = data.context_window || {};
  const used = context.used_percentage;
  const size = context.context_window_size;
  const currentUsage = context.current_usage || {};
  const cacheRead = currentUsage.cache_read_input_tokens || 0;
  const rateLimits = data.rate_limits || {};
  const fiveHour = rateLimits.five_hour && rateLimits.five_hour.used_percentage;
  const sevenDay = rateLimits.seven_day && rateLimits.seven_day.used_percentage;
  const ctx = typeof used === 'number' ? `${Math.round(used)}%` : 'n/a';
  let ctxColor = '';
  if (typeof used === 'number') {
    ctxColor = used >= 75 ? '\u001b[31m●\u001b[0m' : used >= 50 ? '\u001b[33m●\u001b[0m' : '\u001b[32m●\u001b[0m';
  }
  const parts = [`model: ${modelName}`, `effort: ${effort}`, `ctx: ${ctx}${ctxColor ? ` ${ctxColor}` : ''}`, `cache read: ${cacheRead}`];
  if (typeof fiveHour === 'number') parts.push(`5h: ${Math.round(fiveHour)}%`);
  if (typeof sevenDay === 'number') parts.push(`7d: ${Math.round(sevenDay)}%`);

  const alerts = [];
  if (/opus/i.test(`${modelName} ${modelId}`) && !/opusplan/i.test(`${modelName} ${modelId}`)) {
    alerts.push('Opus active');
  }
  if (Number(size) === 1000000) {
    alerts.push('long context active');
    parts[2] = typeof used === 'number' ? `ctx: ${Math.round(used)}% of 1M${ctxColor ? ` ${ctxColor}` : ''}` : 'ctx: n/a of 1M';
  }
  if (alerts.length > 0) parts.push(`cost alert: ${alerts.join(', ')}`);
  return parts.join(' | ');
}

function crc32(buffer) {
  const table = crc32.table || (crc32.table = Array.from({ length: 256 }, (_, n) => {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    return c >>> 0;
  }));
  let crc = 0xffffffff;
  for (const byte of buffer) crc = table[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function dosDateTime(date) {
  const year = Math.max(date.getFullYear(), 1980);
  const dosTime = (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
  const dosDate = ((year - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate();
  return { dosDate, dosTime };
}

function createZip(files, destination) {
  const localParts = [];
  const centralParts = [];
  let offset = 0;
  for (const file of files) {
    const nameBuffer = Buffer.from(file.name.replace(/\\/g, '/'));
    const data = fs.readFileSync(file.path);
    const compressed = zlib.deflateRawSync(data);
    const checksum = crc32(data);
    const stat = fs.statSync(file.path);
    const { dosDate, dosTime } = dosDateTime(stat.mtime);

    const localHeader = Buffer.alloc(30);
    localHeader.writeUInt32LE(0x04034b50, 0);
    localHeader.writeUInt16LE(20, 4);
    localHeader.writeUInt16LE(0, 6);
    localHeader.writeUInt16LE(8, 8);
    localHeader.writeUInt16LE(dosTime, 10);
    localHeader.writeUInt16LE(dosDate, 12);
    localHeader.writeUInt32LE(checksum, 14);
    localHeader.writeUInt32LE(compressed.length, 18);
    localHeader.writeUInt32LE(data.length, 22);
    localHeader.writeUInt16LE(nameBuffer.length, 26);
    localHeader.writeUInt16LE(0, 28);
    localParts.push(localHeader, nameBuffer, compressed);

    const centralHeader = Buffer.alloc(46);
    centralHeader.writeUInt32LE(0x02014b50, 0);
    centralHeader.writeUInt16LE(20, 4);
    centralHeader.writeUInt16LE(20, 6);
    centralHeader.writeUInt16LE(0, 8);
    centralHeader.writeUInt16LE(8, 10);
    centralHeader.writeUInt16LE(dosTime, 12);
    centralHeader.writeUInt16LE(dosDate, 14);
    centralHeader.writeUInt32LE(checksum, 16);
    centralHeader.writeUInt32LE(compressed.length, 20);
    centralHeader.writeUInt32LE(data.length, 24);
    centralHeader.writeUInt16LE(nameBuffer.length, 28);
    centralHeader.writeUInt16LE(0, 30);
    centralHeader.writeUInt16LE(0, 32);
    centralHeader.writeUInt16LE(0, 34);
    centralHeader.writeUInt16LE(0, 36);
    centralHeader.writeUInt32LE(0, 38);
    centralHeader.writeUInt32LE(offset, 42);
    centralParts.push(centralHeader, nameBuffer);
    offset += localHeader.length + nameBuffer.length + compressed.length;
  }

  const centralSize = centralParts.reduce((sum, part) => sum + part.length, 0);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(0, 4);
  end.writeUInt16LE(0, 6);
  end.writeUInt16LE(files.length, 8);
  end.writeUInt16LE(files.length, 10);
  end.writeUInt32LE(centralSize, 12);
  end.writeUInt32LE(offset, 16);
  end.writeUInt16LE(0, 20);
  fs.writeFileSync(destination, Buffer.concat([...localParts, ...centralParts, end]));
}

function walkFiles(root, relativeDir = '') {
  const dir = path.join(root, relativeDir);
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const rel = path.join(relativeDir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkFiles(root, rel));
    } else if (entry.isFile()) {
      files.push(rel);
    }
  }
  return files;
}

function isNestedArchive(fileName) {
  return /\.(zip|plugin)$/i.test(fileName);
}

function validatePackage(root) {
  const pluginJsonPath = path.join(root, '.claude-plugin', 'plugin.json');
  const pluginJson = parseJson(fs.readFileSync(pluginJsonPath, 'utf8'));
  if (!pluginJson.version) throw new Error('.claude-plugin/plugin.json is missing version');

  const allFiles = walkFiles(root);
  const forbidden = allFiles.filter((file) => {
    const normalized = file.replace(/\\/g, '/');
    return isNestedArchive(normalized) && !normalized.startsWith('dist/');
  });
  if (forbidden.length > 0) throw new Error(`Archives outside dist are not allowed: ${forbidden.join(', ')}`);

  const allowedRoots = ['.claude-plugin', 'skills', 'hooks', 'statusline', 'settings', 'scripts', 'docs'];
  const packageFiles = allFiles
    .map((file) => file.replace(/\\/g, '/'))
    .filter((file) => {
      if (file === 'README.md') return true;
      if (file === '.gitignore') return false;
      if (file.startsWith('dist/') || file.startsWith('.git/') || file.startsWith('node_modules/')) return false;
      if (file === '.env' || file.startsWith('.env.') || isNestedArchive(file)) return false;
      return allowedRoots.some((rootName) => file === rootName || file.startsWith(`${rootName}/`));
    })
    .sort();

  const distDir = path.join(root, 'dist');
  ensureDir(distDir);
  const zipPath = path.join(distDir, 'token-saver.zip');
  createZip(packageFiles.map((name) => ({ name, path: path.join(root, name) })), zipPath);

  const required = [
    '.claude-plugin/plugin.json',
    'skills/token-saver/SKILL.md',
    'hooks/hooks.json',
    'settings/managed-settings.example.json'
  ];
  const missing = required.filter((entry) => !packageFiles.includes(entry));
  const nested = packageFiles.filter(isNestedArchive);
  if (missing.length > 0) throw new Error(`Required files missing from package: ${missing.join(', ')}`);
  if (nested.length > 0) throw new Error(`Nested archives found: ${nested.join(', ')}`);

  return { zipPath, nestedCount: nested.length, requiredPresent: true };
}

module.exports = {
  deepMerge,
  formatStatusLine,
  installSettings,
  parseJson,
  readStdin,
  summarizeHook,
  validatePackage
};
