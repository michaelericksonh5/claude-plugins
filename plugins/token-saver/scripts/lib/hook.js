#!/usr/bin/env node
'use strict';

const { readStdin, summarizeHook } = require('./token-saver-common');

try {
  const output = summarizeHook(readStdin());
  if (output) {
    console.log(output);
  }
  process.exit(0);
} catch (error) {
  console.log(`token-saver hook warning: could not summarize output (${error.message})`);
  process.exit(0);
}
