#!/usr/bin/env node
'use strict';

const path = require('path');
const { installSettings } = require('./token-saver-common');

const platform = process.argv[2];
const pluginRoot = path.resolve(__dirname, '..', '..');

if (!['windows', 'unix'].includes(platform)) {
  console.error('Usage: node scripts/lib/install.js <windows|unix>');
  process.exit(1);
}

try {
  const result = installSettings({
    home: process.env.USERPROFILE || process.env.HOME,
    pluginRoot,
    platform
  });
  console.log(`Settings written: ${result.settingsPath}`);
  console.log(`Backup created: ${result.backupPath || 'none; settings.json did not exist'}`);
  console.log(`Changed keys: ${result.changedKeys.join(', ')}`);
  console.log('Restart Claude Code for the settings, hook, and status line to load.');
} catch (error) {
  console.error(`token-saver install failed: ${error.message}`);
  process.exit(1);
}
