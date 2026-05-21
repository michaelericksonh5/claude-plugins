#!/usr/bin/env node
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const https = require('https');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const RTK_VERSION = '0.40.0';
const RELEASE_TAG = `v${RTK_VERSION}`;
const RELEASE_BASE = `https://github.com/rtk-ai/rtk/releases/download/${RELEASE_TAG}`;

const ASSETS = {
  'win32-x64': {
    name: 'rtk-x86_64-pc-windows-msvc.zip',
    sha256: '7fc90190f76f55dc170898d0ac755e89f405fc2d1d89f717ad8600640ab0f1ed',
    binary: 'rtk.exe'
  },
  'darwin-arm64': {
    name: 'rtk-aarch64-apple-darwin.tar.gz',
    sha256: '60c2c325b4edf0367cfa9716ac2e2c888abcd065eff45d01510da6561ab82e3c',
    binary: 'rtk'
  },
  'darwin-x64': {
    name: 'rtk-x86_64-apple-darwin.tar.gz',
    sha256: '8eac502fb812056973da2a8c2f0c00e1427ba5f71bd14c01520bc540630cb98a',
    binary: 'rtk'
  },
  'linux-x64': {
    name: 'rtk-x86_64-unknown-linux-musl.tar.gz',
    sha256: 'a75d210a445874106bc16da2b4efba01d36d297afa33ec134728f2d5f42ef5af',
    binary: 'rtk'
  },
  'linux-arm64': {
    name: 'rtk-aarch64-unknown-linux-gnu.tar.gz',
    sha256: '1d0087ad62a182c0833c2251ac678b5e05356418d91aa57305ac51a126c9b102',
    binary: 'rtk'
  }
};

function platformKey() {
  return `${process.platform}-${process.arch}`;
}

function defaultInstallDir() {
  return path.join(os.homedir(), '.local', 'bin');
}

function pathEntries() {
  return String(process.env.PATH || '').split(path.delimiter).filter(Boolean);
}

function isOnPath(dir) {
  const normalized = path.resolve(dir).toLowerCase();
  return pathEntries().some((entry) => path.resolve(entry).toLowerCase() === normalized);
}

function sha256(filePath) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

function download(url, destination, redirects = 0) {
  if (redirects > 5) throw new Error(`Too many redirects while downloading ${url}`);
  return new Promise((resolve, reject) => {
    const request = https.get(url, (response) => {
      if ([301, 302, 303, 307, 308].includes(response.statusCode)) {
        response.resume();
        download(response.headers.location, destination, redirects + 1).then(resolve, reject);
        return;
      }
      if (response.statusCode !== 200) {
        response.resume();
        reject(new Error(`Download failed with HTTP ${response.statusCode}: ${url}`));
        return;
      }
      const file = fs.createWriteStream(destination, { mode: 0o600 });
      response.pipe(file);
      file.on('finish', () => file.close(resolve));
      file.on('error', reject);
    });
    request.on('error', reject);
  });
}

function run(command, args) {
  const result = spawnSync(command, args, { encoding: 'utf8', windowsHide: true });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(' ')} failed: ${(result.stderr || result.stdout || '').trim()}`);
  }
  return result;
}

function extractArchive(archivePath, destination) {
  fs.mkdirSync(destination, { recursive: true });
  if (archivePath.endsWith('.zip')) {
    const shell = process.platform === 'win32' && spawnSync('pwsh', ['-NoProfile', '-Command', '$PSVersionTable.PSVersion'], { windowsHide: true }).status === 0
      ? 'pwsh'
      : 'powershell';
    run(shell, [
      '-NoProfile',
      '-ExecutionPolicy',
      'Bypass',
      '-Command',
      'param($ArchivePath, $DestinationPath) Expand-Archive -LiteralPath $ArchivePath -DestinationPath $DestinationPath -Force',
      archivePath,
      destination
    ]);
    return;
  }
  run('tar', ['-xzf', archivePath, '-C', destination]);
}

function findBinary(root, binaryName) {
  const entries = fs.readdirSync(root, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      const found = findBinary(fullPath, binaryName);
      if (found) return found;
    } else if (entry.isFile() && entry.name === binaryName) {
      return fullPath;
    }
  }
  return null;
}

function updateWindowsUserPath(installDir) {
  const script = [
    "param($dir)",
    "$ErrorActionPreference = 'Stop'",
    "$path = [Environment]::GetEnvironmentVariable('Path', 'User')",
    "if ([string]::IsNullOrWhiteSpace($path)) { $path = '' }",
    "$parts = $path -split ';' | Where-Object { $_ }",
    "if (-not ($parts | Where-Object { [IO.Path]::GetFullPath($_).TrimEnd('\\') -ieq [IO.Path]::GetFullPath($dir).TrimEnd('\\') })) {",
    "  $newPath = (($dir + $parts) -join ';')",
    "  [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')",
    '}'
  ].join('; ');
  const shell = spawnSync('pwsh', ['-NoProfile', '-Command', '$PSVersionTable.PSVersion'], { windowsHide: true }).status === 0
    ? 'pwsh'
    : 'powershell';
  run(shell, ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script, installDir]);
}

function updateUnixShellPath(installDir) {
  const markerStart = '# >>> rtk-token-saver PATH >>>';
  const markerEnd = '# <<< rtk-token-saver PATH <<<';
  const shellQuote = (value) => `'${String(value).replace(/'/g, "'\\''")}'`;
  const block = `${markerStart}\nexport PATH=${shellQuote(installDir)}:$PATH\n${markerEnd}\n`;
  const targets = [path.join(os.homedir(), '.profile')];
  const shellName = path.basename(process.env.SHELL || '');
  if (shellName === 'zsh') targets.push(path.join(os.homedir(), '.zshrc'));
  for (const target of targets) {
    const existing = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : '';
    if (!existing.includes(markerStart)) {
      fs.appendFileSync(target, `${existing.endsWith('\n') || existing.length === 0 ? '' : '\n'}${block}`);
    }
  }
}

async function installRtk(options = {}) {
  const key = options.platformKey || platformKey();
  const asset = ASSETS[key];
  if (!asset) {
    throw new Error(`Unsupported platform for automatic RTK install: ${key}`);
  }

  const installDir = options.installDir || defaultInstallDir();
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'rtk-token-saver-'));
  const archivePath = path.join(tempDir, asset.name);
  const extractDir = path.join(tempDir, 'extract');
  const url = `${RELEASE_BASE}/${asset.name}`;

  fs.mkdirSync(installDir, { recursive: true });
  await download(url, archivePath);
  const digest = sha256(archivePath);
  if (digest !== asset.sha256) {
    throw new Error(`RTK checksum mismatch for ${asset.name}. Expected ${asset.sha256}, got ${digest}`);
  }

  extractArchive(archivePath, extractDir);
  const binaryPath = findBinary(extractDir, asset.binary);
  if (!binaryPath) throw new Error(`Could not find ${asset.binary} in ${asset.name}`);

  const destination = path.join(installDir, asset.binary);
  fs.copyFileSync(binaryPath, destination);
  fs.chmodSync(destination, 0o755);
  const binarySha256 = sha256(destination);

  const wasOnPath = isOnPath(installDir);
  if (!wasOnPath) {
    if (process.platform === 'win32') {
      updateWindowsUserPath(installDir);
    } else {
      updateUnixShellPath(installDir);
    }
    process.env.PATH = `${installDir}${path.delimiter}${process.env.PATH || ''}`;
  }

  return {
    version: RTK_VERSION,
    asset: asset.name,
    binaryPath: destination,
    binarySha256,
    installDir,
    pathUpdated: !wasOnPath
  };
}

if (require.main === module) {
  if (!process.argv.includes('--install-rtk')) {
    console.error('Refusing to install RTK without explicit --install-rtk.');
    console.error('Use scripts/setup.ps1 -InstallRtk or scripts/setup.sh --install-rtk.');
    process.exit(1);
  }

  installRtk()
    .then((result) => {
      console.log(`Installed RTK ${result.version}: ${result.binaryPath}`);
      console.log(`Release asset: ${result.asset}`);
      console.log('Restart Claude Code or your terminal if PATH was updated.');
    })
    .catch((error) => {
      console.error(`RTK install failed: ${error.message}`);
      process.exit(1);
    });
}

module.exports = {
  ASSETS,
  RTK_VERSION,
  defaultInstallDir,
  installRtk
};
