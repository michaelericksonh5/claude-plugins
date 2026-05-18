#!/usr/bin/env node
'use strict';

const { formatStatusLine, readStdin } = require('./token-saver-common');

try {
  console.log(formatStatusLine(readStdin()));
} catch (error) {
  console.log('model: unknown | effort: auto | ctx: n/a | cache read: 0');
}
