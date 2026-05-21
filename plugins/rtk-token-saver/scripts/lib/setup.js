#!/usr/bin/env node
'use strict';

const { spawnSync } = require('child_process');
const { migrateTokenSaverHooks, runDoctor } = require('./doctor');
const { installRtk } = require('./install-rtk');

function run(command, args) {
  return spawnSync(command, args, {
    stdio: 'inherit',
    windowsHide: true
  });
}

async function main() {
  const apply = process.argv.includes('--apply');
  const force = process.argv.includes('--force');
  const install = process.argv.includes('--install-rtk');
  const migrate = process.argv.includes('--migrate-token-saver');
  const json = process.argv.includes('--json');
  let before = runDoctor();

  if (json) {
    console.log(JSON.stringify({ before, applied: false }, null, 2));
    return before.ok ? 0 : 1;
  }

  console.log('rtk-token-saver setup');
  console.log('This wrapper installs pinned RTK only when --install-rtk is provided.');
  console.log('');

  const needsRtkInstall = [
    'RTK available on PATH',
    'RTK approved version',
    'RTK install path approved'
  ].some((name) => {
    const result = before.results.find((entry) => entry.name === name);
    return !result || !result.ok;
  });

  if (needsRtkInstall) {
    if (install) {
      console.log('RTK was missing, unapproved, or outside the approved user-local path. Installing approved RTK into a user-local bin directory...');
      const installResult = await installRtk();
      console.log(`Installed RTK ${installResult.version}: ${installResult.binaryPath}`);
      if (installResult.pathUpdated) {
        console.log('Updated user PATH. Restart Claude Code or your terminal if this session cannot see rtk yet.');
      }
      before = runDoctor();
    } else {
      console.log('RTK was missing, unapproved, or outside the approved user-local path.');
      console.log('Or run this setup with --install-rtk to install approved RTK into a user-local bin directory.');
      return 1;
    }
  }

  const legacyHooks = before.results.find((entry) => entry.name === 'Legacy token-saver hooks absent');
  if (legacyHooks && !legacyHooks.ok) {
    if (migrate) {
      const migration = migrateTokenSaverHooks();
      if (migration.changed) {
        console.log(`Removed legacy token-saver hooks from ${migration.settingsPath}`);
        console.log(`Backup created: ${migration.backupPath}`);
        for (const removed of migration.removed) {
          console.log(`Removed: ${removed}`);
        }
      }
      before = runDoctor();
    } else {
      console.log('Legacy token-saver hooks were detected. Re-run with --migrate-token-saver to remove only known H5G token-saver hooks.');
      return 1;
    }
  }

  if (!apply) {
    console.log('Dry run only. Re-run with --apply to execute `rtk init -g` for Claude Code.');
    console.log('');
    for (const result of before.results) {
      console.log(`${result.ok ? 'OK' : 'WARN'}  ${result.name} - ${result.detail}`);
    }
    return before.ok ? 0 : 1;
  }

  const blockingChecks = [
    'RTK approved version',
    'RTK install path approved',
    'Legacy token-saver hooks absent'
  ];
  const blockers = before.results.filter((result) => blockingChecks.includes(result.name) && !result.ok);
  if (blockers.length > 0 && !force) {
    console.log('Refusing to apply RTK setup because conflicts or unapproved RTK state were detected:');
    for (const blocker of blockers) {
      console.log(`WARN  ${blocker.name} - ${blocker.detail}`);
    }
    console.log('');
    console.log('Resolve these items first, or re-run with --apply --force after manual review.');
    return 1;
  }

  if (force) {
    console.log('Force mode enabled. Proceeding despite doctor warnings after manual review.');
  }

  const otherHooks = before.results.find((result) => result.name === 'Other PreToolUse hooks reviewed');
  if (otherHooks && !otherHooks.ok) {
    console.log(`WARN  ${otherHooks.name} - ${otherHooks.detail}`);
    console.log('Continuing with RTK setup; review hook ordering if behavior looks odd.');
  }

  console.log('Running: rtk init -g');
  const result = run('rtk', ['init', '-g']);
  if (result.status !== 0) return result.status || 1;

  const after = runDoctor();
  for (const check of after.results) {
    console.log(`${check.ok ? 'OK' : 'WARN'}  ${check.name} - ${check.detail}`);
  }
  return after.ok ? 0 : 1;
}

if (require.main === module) {
  main()
    .then((code) => process.exit(code))
    .catch((error) => {
      console.error(`rtk-token-saver setup failed: ${error.message}`);
      process.exit(1);
    });
}
