const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const test = require('node:test');

const root = path.resolve(__dirname, '..');
const { isLegacyTokenSaverCommand, migrateTokenSaverHooks, parseRtkVersion, runDoctor } = require('../scripts/lib/doctor');
const { ASSETS, RTK_VERSION, defaultInstallDir } = require('../scripts/lib/install-rtk');
const { validatePackage } = require('../scripts/lib/validate-package');
const { handlePreToolUse, handleSessionStart } = require('../hooks/lib/rtk-hooks');

test('plugin manifest registers forced Compact TLDR and default hooks', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, '.claude-plugin', 'plugin.json'), 'utf8'));
  const outputStyle = fs.readFileSync(path.join(root, 'output-styles', 'compact-tldr.md'), 'utf8');
  assert.strictEqual(manifest.name, 'rtk-token-saver');
  assert.strictEqual(manifest.version, '0.3.1');
  assert.strictEqual(manifest.skills, undefined);
  assert.strictEqual(manifest.outputStyles, './output-styles/compact-tldr.md');
  assert.strictEqual(manifest.hooks, undefined);
  assert.strictEqual(fs.existsSync(path.join(root, 'hooks', 'hooks.json')), true);
  assert.match(outputStyle, /force-for-plugin: true/);
});

test('doctor detects legacy token-saver and RTK hook state', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-test-'));
  const claudeDir = path.join(home, '.claude');
  fs.mkdirSync(claudeDir, { recursive: true });
  fs.writeFileSync(path.join(claudeDir, 'settings.json'), JSON.stringify({
    hooks: {
      PreToolUse: [
        {
          matcher: 'Bash',
          hooks: [
            { type: 'command', command: 'rtk hook claude', timeout: 10 },
            { type: 'command', command: 'node ~/.claude/token-saver/lib/pretool-filter.js', timeout: 10 }
          ]
        }
      ]
    }
  }, null, 2));

  const report = runDoctor({ home });
  const rtkHook = report.results.find((result) => result.name === 'RTK PreToolUse hook configured');
  const legacy = report.results.find((result) => result.name === 'Legacy token-saver hooks absent');
  assert.strictEqual(rtkHook.ok, true);
  assert.strictEqual(legacy.ok, false);
});

test('doctor detects token_saver spelling and other PreToolUse hooks', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-test-'));
  const claudeDir = path.join(home, '.claude');
  fs.mkdirSync(claudeDir, { recursive: true });
  fs.writeFileSync(path.join(claudeDir, 'settings.json'), JSON.stringify({
    hooks: {
      PreToolUse: [
        {
          matcher: 'Bash',
          hooks: [
            { type: 'command', command: 'rtk hook claude', timeout: 10 },
            { type: 'command', command: 'node ~/.claude/token_saver/lib/pretool-filter.js', timeout: 10 },
            { type: 'command', command: 'node ~/.claude/custom/pretool.js', timeout: 10 }
          ]
        }
      ]
    }
  }, null, 2));

  const report = runDoctor({ home });
  const legacy = report.results.find((result) => result.name === 'Legacy token-saver hooks absent');
  const otherHooks = report.results.find((result) => result.name === 'Other PreToolUse hooks reviewed');
  assert.strictEqual(legacy.ok, false);
  assert.match(legacy.detail, /token_saver/);
  assert.strictEqual(otherHooks.ok, false);
  assert.match(otherHooks.detail, /custom\/pretool/);
});

test('migration removes only legacy token-saver hooks and backs up settings', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-test-'));
  const claudeDir = path.join(home, '.claude');
  const settingsPath = path.join(claudeDir, 'settings.json');
  fs.mkdirSync(claudeDir, { recursive: true });
  fs.writeFileSync(settingsPath, JSON.stringify({
    hooks: {
      PreToolUse: [
        {
          matcher: 'Bash',
          hooks: [
            { type: 'command', command: 'node ~/.claude/token_saver/lib/pretool-filter.js', timeout: 10 },
            { type: 'command', command: 'node ~/.claude/security/pretool-filter.js', timeout: 10 },
            { type: 'command', command: 'pwsh C:/team/filter-output.ps1', timeout: 10 },
            { type: 'command', command: 'node ~/.claude/custom/pretool.js', timeout: 10 }
          ]
        }
      ],
      PostToolUse: [
        {
          matcher: 'Bash',
          hooks: [
            { type: 'command', command: 'pwsh ~/.claude/hooks/token-saver-filter-output.ps1', timeout: 10 }
          ]
        }
      ]
    },
    keep: true
  }, null, 2));

  const result = migrateTokenSaverHooks({ home });
  const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
  const text = JSON.stringify(settings);
  assert.strictEqual(result.changed, true);
  assert.ok(fs.existsSync(result.backupPath));
  assert.match(text, /custom\/pretool/);
  assert.match(text, /security\/pretool-filter/);
  assert.match(text, /team\/filter-output/);
  assert.doesNotMatch(text, /token_saver|token-saver-filter-output/);
  assert.strictEqual(settings.keep, true);
});

test('legacy token-saver detection is path-specific', () => {
  assert.strictEqual(isLegacyTokenSaverCommand('node ~/.claude/token-saver/lib/pretool-filter.js'), true);
  assert.strictEqual(isLegacyTokenSaverCommand('pwsh ~/.claude/hooks/token-saver-filter-output.ps1'), true);
  assert.strictEqual(isLegacyTokenSaverCommand('node ~/.claude/security/pretool-filter.js'), false);
  assert.strictEqual(isLegacyTokenSaverCommand('pwsh C:/team/filter-output.ps1'), false);
});

test('package validator rejects nested archives and requires plugin files', () => {
  const result = validatePackage(root);
  assert.strictEqual(result.requiredPresent, true);
  assert.strictEqual(result.nestedArchiveCount, 0);
});

test('PreToolUse wraps safe noisy Bash commands and preserves input fields', async () => {
  const installDir = fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-bin-'));
  const binaryPath = path.join(installDir, process.platform === 'win32' ? 'rtk.exe' : 'rtk');
  fs.writeFileSync(binaryPath, 'fake rtk');
  const shellPath = `'${binaryPath.replace(/\\/g, '/')}'`;
  const result = await handlePreToolUse({
    tool_name: 'Bash',
    tool_input: {
      command: 'npm test',
      timeout: 120000,
      description: 'Run tests'
    }
  }, {
    dataDir: fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-test-')),
    installer: {
      RTK_VERSION,
      ASSETS,
      defaultInstallDir: () => installDir,
      installRtk: async () => {
        throw new Error('install should not run');
      }
    },
    commandRunner: () => ({ status: 0, stdout: `rtk ${RTK_VERSION}\n`, stderr: '' }),
    verifyBinary: () => true
  });

  assert.strictEqual(result.hookSpecificOutput.hookEventName, 'PreToolUse');
  assert.strictEqual(result.hookSpecificOutput.permissionDecision, 'allow');
  assert.deepStrictEqual(result.hookSpecificOutput.updatedInput, {
    command: `${shellPath} npm test`,
    timeout: 120000,
    description: 'Run tests'
  });
});

test('PreToolUse skips unsafe chained Bash commands', async () => {
  let installCalled = false;
  const result = await handlePreToolUse({
    tool_name: 'Bash',
    tool_input: {
      command: 'npm test && npm run build',
      timeout: 120000
    }
  }, {
    dataDir: fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-test-')),
    installer: {
      RTK_VERSION,
      ASSETS,
      defaultInstallDir,
      installRtk: async () => {
        installCalled = true;
        throw new Error('install should not run');
      }
    },
    commandRunner: () => ({ status: 1, stdout: '', stderr: 'missing' })
  });

  assert.strictEqual(result.hookSpecificOutput.permissionDecision, 'allow');
  assert.strictEqual(result.hookSpecificOutput.updatedInput, undefined);
  assert.strictEqual(installCalled, false);
});

test('PreToolUse fails open when RTK install is unavailable', async () => {
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-test-'));
  const result = await handlePreToolUse({
    tool_name: 'Bash',
    tool_input: {
      command: 'pytest',
      timeout: 120000
    }
  }, {
    dataDir,
    installer: {
      RTK_VERSION,
      ASSETS,
      defaultInstallDir,
      installRtk: async () => {
        throw new Error('offline');
      }
    },
    commandRunner: () => ({ status: 1, stdout: '', stderr: 'missing' })
  });

  const state = JSON.parse(fs.readFileSync(path.join(dataDir, 'rtk-token-saver-state.json'), 'utf8'));
  assert.strictEqual(result.hookSpecificOutput.permissionDecision, 'allow');
  assert.strictEqual(result.hookSpecificOutput.updatedInput, undefined);
  assert.match(result.hookSpecificOutput.additionalContext, /failed open|offline|unavailable/i);
  assert.strictEqual(state.status, 'unavailable');
});

test('SessionStart reports setup status with mocked installer and env file', async () => {
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-test-'));
  const installDir = path.join(dataDir, 'bin');
  const envFile = path.join(dataDir, 'claude.env');
  const result = await handleSessionStart({
    dataDir,
    envFile,
    installer: {
      RTK_VERSION,
      defaultInstallDir: () => installDir,
      ASSETS,
      installRtk: async () => ({
        version: RTK_VERSION,
        asset: 'rtk-test.zip',
        binaryPath: path.join(installDir, process.platform === 'win32' ? 'rtk.exe' : 'rtk'),
        binarySha256: 'mocked-binary-sha256',
        installDir,
        pathUpdated: true
      })
    },
    commandRunner: (command) => command === path.join(installDir, process.platform === 'win32' ? 'rtk.exe' : 'rtk')
      ? { status: 0, stdout: `rtk ${RTK_VERSION}\n`, stderr: '' }
      : { status: 1, stdout: '', stderr: 'missing' }
  });

  const state = JSON.parse(fs.readFileSync(path.join(dataDir, 'rtk-token-saver-state.json'), 'utf8'));
  const env = fs.readFileSync(envFile, 'utf8');
  assert.strictEqual(result.hookSpecificOutput.hookEventName, 'SessionStart');
  assert.match(result.hookSpecificOutput.additionalContext, /Compact TLDR is forced/);
  assert.match(result.hookSpecificOutput.additionalContext, /RTK 0\.40\.0 installed/);
  assert.strictEqual(state.status, 'installed');
  assert.match(env, /export RTK_TOKEN_SAVER_STATUS='installed'/);
  assert.match(env, /export PATH=/);
});

test('RTK installer pins reviewed release assets', () => {
  assert.strictEqual(RTK_VERSION, '0.40.0');
  assert.match(ASSETS['win32-x64'].name, /windows-msvc\.zip$/);
  assert.match(ASSETS['darwin-arm64'].name, /apple-darwin\.tar\.gz$/);
  assert.match(ASSETS['darwin-x64'].name, /apple-darwin\.tar\.gz$/);
  assert.match(ASSETS['linux-x64'].name, /linux-musl\.tar\.gz$/);
  for (const asset of Object.values(ASSETS)) {
    assert.match(asset.sha256, /^[a-f0-9]{64}$/);
  }
  assert.strictEqual(defaultInstallDir(), path.join(os.homedir(), '.local', 'bin'));
});

test('doctor parses RTK versions exactly', () => {
  assert.strictEqual(parseRtkVersion('rtk 0.40.0'), '0.40.0');
  assert.strictEqual(parseRtkVersion('rtk v0.40.0'), '0.40.0');
  assert.strictEqual(parseRtkVersion('rtk 0.40.01'), '0.40.01');
  assert.notStrictEqual(parseRtkVersion('rtk 0.40.01'), '0.40.0');
});

test('standalone installer requires explicit install flag', () => {
  const result = spawnSync(process.execPath, [path.join(root, 'scripts/lib/install-rtk.js')], {
    encoding: 'utf8'
  });
  assert.notStrictEqual(result.status, 0);
  assert.match(result.stderr, /explicit --install-rtk/);
});
