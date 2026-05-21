#!/usr/bin/env node
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const APPROVED_RTK_VERSION = '0.40.0';
const LEGACY_TOKEN_SAVER_PATTERNS = [
  /(?:^|\s|["'])~?[\\/]\.claude[\\/]token[-_]saver[\\/]/i,
  /(?:^|\s|["'])%USERPROFILE%[\\/]\.claude[\\/]token[-_]saver[\\/]/i,
  /(?:^|\s|["'])\$HOME[\\/]\.claude[\\/]token[-_]saver[\\/]/i,
  /(?:^|\s|["'])\$env:USERPROFILE[\\/]\.claude[\\/]token[-_]saver[\\/]/i,
  /(?:^|\s|["']).*?[\\/]\.claude[\\/]hooks[\\/]token-saver-filter-output\.(?:ps1|sh)(?:["'\s]|$)/i
];

function commandResult(command, args = ['--version']) {
  return spawnSync(command, args, { encoding: 'utf8', windowsHide: true });
}

function commandExists(command) {
  const result = commandResult(command);
  return result.status === 0;
}

function resolveCommand(command) {
  const resolver = process.platform === 'win32' ? 'where.exe' : 'which';
  const result = spawnSync(resolver, [command], { encoding: 'utf8', windowsHide: true });
  if (result.status !== 0) return '';
  return String(result.stdout || '').split(/\r?\n/).find(Boolean) || '';
}

function defaultInstallDir() {
  return path.join(os.homedir(), '.local', 'bin');
}

function samePath(left, right) {
  return path.resolve(left).toLowerCase() === path.resolve(right).toLowerCase();
}

function parseRtkVersion(text) {
  const match = String(text || '').match(/\b(?:rtk\s+)?v?(\d+\.\d+\.\d+)\b/i);
  return match ? match[1] : '';
}

function readJson(filePath) {
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function hookCommands(settings, eventName) {
  const groups = settings && settings.hooks && Array.isArray(settings.hooks[eventName])
    ? settings.hooks[eventName]
    : [];
  return groups.flatMap((group) => Array.isArray(group.hooks) ? group.hooks : [])
    .map((hook) => hook && hook.command)
    .filter((command) => typeof command === 'string');
}

function hookEntries(settings, eventName) {
  const groups = settings && settings.hooks && Array.isArray(settings.hooks[eventName])
    ? settings.hooks[eventName]
    : [];
  return groups.flatMap((group) => {
    const matcher = group && group.matcher ? String(group.matcher) : '';
    const hooks = Array.isArray(group && group.hooks) ? group.hooks : [];
    return hooks
      .filter((hook) => hook && typeof hook.command === 'string')
      .map((hook) => ({ matcher, command: hook.command }));
  });
}

function check(name, ok, detail) {
  return { name, ok: Boolean(ok), detail };
}

function isLegacyTokenSaverCommand(command) {
  return LEGACY_TOKEN_SAVER_PATTERNS.some((pattern) => pattern.test(String(command || '')));
}

function timestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function backupFile(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const parsed = path.parse(filePath);
  const backupPath = path.join(parsed.dir, `${parsed.name}.rtk-token-saver-backup.${timestamp()}${parsed.ext}`);
  fs.copyFileSync(filePath, backupPath);
  return backupPath;
}

function migrateTokenSaverHooks(options = {}) {
  const home = options.home || os.homedir();
  const settingsPath = path.join(home, '.claude', 'settings.json');
  const settings = readJson(settingsPath);
  if (!settings || !settings.hooks) {
    return { changed: false, settingsPath, backupPath: null, removed: [] };
  }

  const removed = [];
  const updatedHooks = { ...settings.hooks };
  for (const eventName of Object.keys(updatedHooks)) {
    if (!Array.isArray(updatedHooks[eventName])) continue;
    updatedHooks[eventName] = updatedHooks[eventName]
      .map((group) => {
        if (!group || !Array.isArray(group.hooks)) return group;
        const keepHooks = [];
        for (const hook of group.hooks) {
          const command = hook && typeof hook.command === 'string' ? hook.command : '';
          if (isLegacyTokenSaverCommand(command)) {
            removed.push(`${eventName}/${group.matcher || '*'}: ${command}`);
          } else {
            keepHooks.push(hook);
          }
        }
        return { ...group, hooks: keepHooks };
      })
      .filter((group) => !group || !Array.isArray(group.hooks) || group.hooks.length > 0);
    if (updatedHooks[eventName].length === 0) {
      delete updatedHooks[eventName];
    }
  }

  if (removed.length === 0) {
    return { changed: false, settingsPath, backupPath: null, removed };
  }

  const backupPath = backupFile(settingsPath);
  const nextSettings = { ...settings, hooks: updatedHooks };
  if (Object.keys(nextSettings.hooks).length === 0) {
    delete nextSettings.hooks;
  }
  writeJson(settingsPath, nextSettings);
  return { changed: true, settingsPath, backupPath, removed };
}

function runDoctor(options = {}) {
  const home = options.home || os.homedir();
  const settingsPath = path.join(home, '.claude', 'settings.json');
  const pluginRoot = path.resolve(__dirname, '..', '..');
  const pluginManifestPath = path.join(pluginRoot, '.claude-plugin', 'plugin.json');
  const pluginManifest = readJson(pluginManifestPath) || {};
  const pluginHooksPath = pluginManifest.hooks ? path.join(pluginRoot, pluginManifest.hooks) : '';
  const pluginHooks = readJson(pluginHooksPath) || {};
  const settings = readJson(settingsPath) || {};
  const preToolEntries = hookEntries(settings, 'PreToolUse');
  const preToolCommands = preToolEntries.map((entry) => entry.command);
  const postToolCommands = hookCommands(settings, 'PostToolUse');
  const rtkHooks = preToolCommands.filter((command) => /\brtk\b/i.test(command));
  const pluginPreToolCommands = hookCommands(pluginHooks, 'PreToolUse');
  const pluginHasRtkPreToolHook = pluginPreToolCommands.some((command) => /pre-tool-use\.js\b/i.test(command));
  const tokenSaverHooks = [...preToolCommands, ...postToolCommands].filter(isLegacyTokenSaverCommand);
  const nonRtkPreToolHooks = preToolEntries
    .filter((entry) => !/\brtk\b/i.test(entry.command))
    .map((entry) => `${entry.matcher || '*'}: ${entry.command}`);

  const rtkVersion = commandResult('rtk');
  const rtkVersionText = (rtkVersion.stdout || rtkVersion.stderr || '').trim();
  const parsedRtkVersion = parseRtkVersion(rtkVersionText);
  const rtkPath = resolveCommand('rtk');
  const rtkInstallDir = rtkPath ? path.dirname(rtkPath) : '';
  const approvedInstallDir = defaultInstallDir();
  const results = [
    check('RTK available on PATH', rtkVersion.status === 0, rtkVersionText || 'rtk --version failed'),
    check('RTK resolved path reviewed', rtkPath.length > 0, rtkPath || 'Could not resolve rtk path.'),
    check('RTK approved version', parsedRtkVersion === APPROVED_RTK_VERSION, `Expected ${APPROVED_RTK_VERSION}; found ${parsedRtkVersion || rtkVersionText || 'unknown'}`),
    check('RTK install path approved', rtkPath.length > 0 && samePath(rtkInstallDir, approvedInstallDir), `Expected ${approvedInstallDir}; found ${rtkInstallDir || 'unknown'}`),
    check('Claude Code CLI available', commandExists('claude'), 'Run `claude --version`.'),
    check('Claude settings file exists', fs.existsSync(settingsPath), settingsPath),
    check('RTK PreToolUse hook configured', rtkHooks.length > 0 || pluginHasRtkPreToolHook, [...rtkHooks, ...pluginPreToolCommands].join(' | ') || 'No RTK PreToolUse hook found.'),
    check('Legacy token-saver hooks absent', tokenSaverHooks.length === 0, tokenSaverHooks.join(' | ') || 'No legacy token-saver hooks found.'),
    check('Other PreToolUse hooks reviewed', nonRtkPreToolHooks.length === 0, nonRtkPreToolHooks.join(' | ') || 'No non-RTK PreToolUse command hooks found.'),
    check('Wrapper plugin hooks configured', fs.existsSync(path.join(pluginRoot, 'hooks', 'hooks.json')), 'hooks/hooks.json is auto-discovered by Claude Code.')
  ];

  return {
    ok: results.every((result) => result.ok),
    approvedRtkVersion: APPROVED_RTK_VERSION,
    approvedInstallDir,
    rtkPath,
    settingsPath,
    results
  };
}

function printText(report) {
  for (const result of report.results) {
    console.log(`${result.ok ? 'OK' : 'WARN'}  ${result.name} - ${result.detail}`);
  }
  console.log(report.ok ? 'rtk-token-saver doctor passed.' : 'rtk-token-saver doctor found items to review.');
}

if (require.main === module) {
  const json = process.argv.includes('--json');
  const report = runDoctor();
  if (json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    printText(report);
  }
  process.exit(report.ok ? 0 : 1);
}

module.exports = {
  APPROVED_RTK_VERSION,
  isLegacyTokenSaverCommand,
  migrateTokenSaverHooks,
  parseRtkVersion,
  runDoctor
};
