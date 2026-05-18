#!/usr/bin/env node
'use strict';

const path = require('path');
const { validatePackage } = require('./token-saver-common');

try {
  const root = path.resolve(__dirname, '..', '..');
  const result = validatePackage(root);
  console.log(`Package created: ${path.relative(root, result.zipPath)}`);
  console.log(`Nested archive count: ${result.nestedCount}`);
  console.log(`Required files present: ${result.requiredPresent}`);
} catch (error) {
  console.error(`Package validation failed: ${error.message}`);
  process.exit(1);
}
