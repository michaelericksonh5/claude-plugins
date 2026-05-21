'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

const NOISY_COMMAND_PREFIXES = [
  /^npm\s+(?:ci|install|test|run\s+(?:build|lint|test))\b/i,
  /^pnpm\s+(?:install|test|run\s+(?:build|lint|test))\b/i,
  /^yarn\s+(?:install|test|run\s+(?:build|lint|test))\b/i,
  /^npx\s+(?:eslint|jest|tsc|vitest)\b/i,
  /^cargo\s+(?:build|check|clippy|test)\b/i,
  /^go\s+test\b/i,
  /^pytest\b/i,
  /^python3?\s+-m\s+pytest\b/i,
  /^git\s+(?:diff|grep|log|show|status)\b/i,
  /^docker\s+(?:build|compose|logs)\b/i,
  /^kubectl\s+(?:describe|diff|get|logs)\b/i
];

function pluginRoot() {
  return process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, '..', '..');
}

function loadInstaller(root = pluginRoot()) {
  return require(path.join(root, 'scripts', 'lib', 'install-rtk.js'));
}

function commandResult(command, args = ['--version']) {
  return spawnSync(command, args, { encoding: 'utf8', windowsHide: true });
}

function parseRtkVersion(text) {
  const match = String(text || '').match(/\b(?:rtk\s+)?v?(\d+\.\d+\.\d+)\b/i);
  return match ? match[1] : '';
}

function binaryName() {
  return process.platform === 'win32' ? 'rtk.exe' : 'rtk';
}

function candidateBinary(defaultInstallDir) {
  return path.join(defaultInstallDir, binaryName());
}

function checkCommand(command, expectedVersion, runner = commandResult) {
  const result = runner(command, ['--version']);
  const output = `${result.stdout || ''}${result.stderr || ''}`.trim();
  const version = parseRtkVersion(output);
  return {
    ok: result.status === 0 && version === expectedVersion,
    command,
    version,
    output
  };
}

function writeState(dataDir, state) {
  if (!dataDir) return;
  fs.mkdirSync(dataDir, { recursive: true });
  fs.writeFileSync(path.join(dataDir, 'rtk-token-saver-state.json'), `${JSON.stringify(state, null, 2)}\n`);
}

function readState(dataDir) {
  if (!dataDir) return null;
  const statePath = path.join(dataDir, 'rtk-token-saver-state.json');
  if (!fs.existsSync(statePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(statePath, 'utf8'));
  } catch {
    return null;
  }
}

function shellQuote(value) {
  return `'${String(value || '').replace(/'/g, "'\\''")}'`;
}

function sha256(filePath) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

function writeEnvFile(envFile, info) {
  if (!envFile) return;
  const lines = [
    '# rtk-token-saver',
    `export RTK_TOKEN_SAVER_STATUS=${shellQuote(info.status)}`,
    `export RTK_TOKEN_SAVER_VERSION=${shellQuote(info.version || '')}`
  ];
  if (info.binaryPath) {
    lines.push(`export RTK_TOKEN_SAVER_RTK_PATH=${shellQuote(info.binaryPath)}`);
  }
  if (info.installDir) {
    const nextPath = `${info.installDir}${path.delimiter}${process.env.PATH || ''}`;
    lines.push(`export PATH=${shellQuote(nextPath)}`);
  }
  fs.appendFileSync(envFile, `${lines.join(os.EOL)}${os.EOL}`);
}

function isShellUnsafe(command) {
  return /(?:\|\||&&|[;&|<>`]|[\r\n]|\$\()/u.test(command);
}

function isAlreadyWrapped(command) {
  return /^\s*(?:"[^"]*[\\/]rtk(?:\.exe)?"|'[^']*[\\/]rtk'|rtk(?:\.exe)?)\b/i.test(command);
}

function shouldWrapCommand(command) {
  const trimmed = String(command || '').trim();
  if (!trimmed || isAlreadyWrapped(trimmed) || isShellUnsafe(trimmed)) return false;
  return NOISY_COMMAND_PREFIXES.some((pattern) => pattern.test(trimmed));
}

function platformKey() {
  return `${process.platform}-${process.arch}`;
}

function verifyApprovedBinary(binaryPath, installer, runner = commandResult, dataDir = '') {
  if (!fs.existsSync(binaryPath)) return false;
  if (!(installer.ASSETS && installer.ASSETS[platformKey()])) return false;
  const state = readState(dataDir);
  if (!state || !['installed', 'available'].includes(state.status) || state.binaryPath !== binaryPath || !state.binarySha256) return false;
  if (sha256(binaryPath) !== state.binarySha256) return false;
  return checkCommand(binaryPath, installer.RTK_VERSION, runner).ok;
}

function shellCommandPath(binaryPath) {
  const normalized = process.platform === 'win32'
    ? binaryPath.replace(/\\/g, '/')
    : binaryPath;
  return shellQuote(normalized);
}

async function ensureRtk(options = {}) {
  const installer = options.installer || loadInstaller(options.pluginRoot);
  const dataDir = options.dataDir || process.env.CLAUDE_PLUGIN_DATA || path.join(os.tmpdir(), 'rtk-token-saver');
  const envFile = options.envFile !== undefined ? options.envFile : process.env.CLAUDE_ENV_FILE;
  const runner = options.commandRunner || commandResult;
  const now = new Date().toISOString();
  const expectedVersion = installer.RTK_VERSION;
  const defaultDir = installer.defaultInstallDir();
  const installedCandidate = candidateBinary(defaultDir);
  const verifyBinary = options.verifyBinary || verifyApprovedBinary;
  const available = verifyBinary(installedCandidate, installer, runner, dataDir);

  if (available) {
    const state = {
      checkedAt: now,
      status: 'available',
      version: expectedVersion,
      binaryPath: installedCandidate,
      binarySha256: sha256(installedCandidate),
      installDir: defaultDir
    };
    writeState(dataDir, state);
    writeEnvFile(envFile, {
      status: 'available',
      version: expectedVersion,
      binaryPath: installedCandidate,
      installDir: defaultDir
    });
    return { ok: true, status: 'available', version: expectedVersion, command: shellCommandPath(installedCandidate), binaryPath: installedCandidate };
  }

  try {
    const result = await installer.installRtk(options.installOptions || {});
    if (result.installDir) {
      process.env.PATH = `${result.installDir}${path.delimiter}${process.env.PATH || ''}`;
    }
    const installedCheck = checkCommand(result.binaryPath, result.version, runner);
    if (!installedCheck.ok) {
      throw new Error(`Installed RTK did not report expected version ${result.version}: ${installedCheck.output || 'no version output'}`);
    }
    const binarySha256 = result.binarySha256 || sha256(result.binaryPath);
    const state = {
      checkedAt: now,
      status: 'installed',
      version: result.version,
      binaryPath: result.binaryPath,
      binarySha256,
      installDir: result.installDir,
      pathUpdated: Boolean(result.pathUpdated)
    };
    writeState(dataDir, state);
    writeEnvFile(envFile, state);
    return { ok: true, status: 'installed', version: result.version, command: shellCommandPath(result.binaryPath), binaryPath: result.binaryPath, install: result };
  } catch (error) {
    const detail = error && error.message ? error.message : String(error);
    const state = {
      checkedAt: now,
      status: 'unavailable',
      expectedVersion,
      detail
    };
    writeState(dataDir, state);
    writeEnvFile(envFile, { status: 'unavailable', version: expectedVersion });
    return { ok: false, status: 'unavailable', version: expectedVersion, detail };
  }
}

function allowOutput(extra = {}) {
  return {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'allow',
      ...extra
    }
  };
}

async function handlePreToolUse(input, options = {}) {
  if (!input || input.tool_name !== 'Bash') {
    return allowOutput();
  }
  const toolInput = input.tool_input && typeof input.tool_input === 'object' ? input.tool_input : {};
  const command = typeof toolInput.command === 'string' ? toolInput.command.trim() : '';
  if (!shouldWrapCommand(command)) {
    return allowOutput();
  }

  const rtk = await ensureRtk(options);
  if (!rtk.ok) {
    return allowOutput({
      additionalContext: `RTK unavailable; ran original command. ${rtk.detail || 'Install check failed open.'}`
    });
  }

  return allowOutput({
    updatedInput: {
      ...toolInput,
      command: `${rtk.command} ${command}`
    },
    additionalContext: `RTK ${rtk.version} wrapped noisy Bash command.`
  });
}

async function handleSessionStart(options = {}) {
  const rtk = await ensureRtk(options);
  const status = rtk.ok
    ? `RTK ${rtk.version} ${rtk.status}; noisy Bash commands are eligible for automatic RTK wrapping.`
    : `RTK setup failed open: ${rtk.detail || 'unavailable'}. Noisy Bash commands will run normally until RTK is available.`;
  return {
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: `Compact TLDR is forced by this plugin. ${status}`
    }
  };
}

async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

module.exports = {
  ensureRtk,
  handlePreToolUse,
  handleSessionStart,
  isShellUnsafe,
  parseRtkVersion,
  readStdin,
  shouldWrapCommand
};
