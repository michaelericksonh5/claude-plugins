#!/usr/bin/env node
'use strict';

const { handleSessionStart } = require('./lib/rtk-hooks');

handleSessionStart()
  .then((output) => {
    process.stdout.write(`${JSON.stringify(output)}\n`);
  })
  .catch((error) => {
    process.stdout.write(`${JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext: `rtk-token-saver setup failed open: ${error.message}`
      }
    })}\n`);
  });
