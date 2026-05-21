#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

function walk(root, relative = '') {
  const dir = path.join(root, relative);
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const rel = path.join(relative, entry.name);
    const normalized = rel.replace(/\\/g, '/');
    if (entry.isDirectory()) {
      if (['.git', 'node_modules', 'dist'].includes(entry.name)) continue;
      files.push(...walk(root, rel));
    } else if (entry.isFile()) {
      files.push(normalized);
    }
  }
  return files;
}

function validatePackage(root) {
  const files = walk(root);
  const nestedArchives = files.filter((file) => /\.(zip|plugin)$/i.test(file));
  const forbidden = files.filter((file) => nestedArchives.includes(file) || file === '.env' || file.startsWith('.env.'));
  if (forbidden.length > 0) {
    throw new Error(`Forbidden package files: ${forbidden.join(', ')}`);
  }

  const required = [
    '.claude-plugin/plugin.json',
    'skills/rtk-token-saver/SKILL.md',
    'skills/rtk-token-saver/COMPACT_OUTPUT.md',
    'skills/rtk-token-saver/CONTEXT_HYGIENE.md',
    'skills/rtk-token-saver/MODEL_ROUTING.md',
    'skills/rtk-token-saver/RTK_SETUP.md',
    'skills/rtk-token-saver/TROUBLESHOOTING.md',
    'output-styles/compact-tldr.md',
    'hooks/hooks.json',
    'hooks/session-start.js',
    'hooks/pre-tool-use.js',
    'hooks/lib/rtk-hooks.js',
    'scripts/lib/doctor.js',
    'scripts/lib/install-rtk.js',
    'scripts/lib/setup.js',
    'docs/TEAM_ROLLOUT.md',
    'docs/SECURITY.md',
    'README.md'
  ];
  const missing = required.filter((file) => !files.includes(file));
  if (missing.length > 0) {
    throw new Error(`Missing required files: ${missing.join(', ')}`);
  }

  return {
    fileCount: files.length,
    requiredPresent: true,
    nestedArchiveCount: nestedArchives.length
  };
}

if (require.main === module) {
  const result = validatePackage(path.resolve(__dirname, '..', '..'));
  console.log(`Package file count: ${result.fileCount}`);
  console.log(`Nested archive count: ${result.nestedArchiveCount}`);
  console.log(`Required files present: ${result.requiredPresent}`);
}

module.exports = {
  validatePackage
};
