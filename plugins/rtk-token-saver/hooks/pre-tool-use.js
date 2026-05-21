#!/usr/bin/env node
'use strict';

const { handlePreToolUse, readStdin } = require('./lib/rtk-hooks');

async function main() {
  const raw = await readStdin();
  const input = raw.trim() ? JSON.parse(raw) : {};
  const output = await handlePreToolUse(input);
  process.stdout.write(`${JSON.stringify(output)}\n`);
}

main().catch((error) => {
  process.stdout.write(`${JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'allow',
      additionalContext: `rtk-token-saver failed open: ${error.message}`
    }
  })}\n`);
});
