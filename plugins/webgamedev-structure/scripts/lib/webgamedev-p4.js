#!/usr/bin/env node
"use strict";

const { classifyPath } = require("./gameforge-paths");
const { buildP4Command, runP4Command } = require("./p4-common");

function parseArgv(argv) {
  const [operation = "help", ...rest] = argv;
  const options = {
    apply: false,
    change: "",
    description: "",
    args: []
  };

  for (let index = 0; index < rest.length; index += 1) {
    const arg = rest[index];
    if (arg === "--") {
      options.args.push(...rest.slice(index + 1));
      break;
    }
    if (arg === "--apply") {
      options.apply = true;
    } else if (arg === "--change") {
      options.change = rest[++index] || "";
    } else if (arg === "--description") {
      options.description = rest[++index] || "";
    } else {
      options.args.push(arg);
    }
  }

  return { operation, options };
}

function formatCommand(spec) {
  if (spec.sequence) {
    return spec.sequence.map((args) => `p4 ${args.join(" ")}`).join("\n");
  }
  return `p4 ${spec.args.join(" ")}`;
}

function printHelp() {
  console.log(`Usage: webgamedev-p4 <operation> [args] [--apply]

Read-only operations:
  doctor, classify, status, opened, info, set, login-status, client, where, have, files, changes, describe, filelog, fstat, print, diff

Mutating operations requiring --apply:
  sync, edit, add, reconcile, submit

Blocked by H5G never-delete policy:
  clean, delete, move, obliterate, revert, resolve, typemap

Examples:
  webgamedev-p4 doctor
  webgamedev-p4 classify GAMEFORGE_folderstructure/ASSETS/LOCAL/texture/portrait/symbols/hp1.webp
  webgamedev-p4 sync //webgamedev/mygame/...
  webgamedev-p4 edit //webgamedev/mygame/texture/portrait/symbols/hp1.webp --apply
  webgamedev-p4 submit --change 12345 --description "Add symbols" --apply`);
}

function main(argv = process.argv.slice(2)) {
  const { operation, options } = parseArgv(argv);

  if (operation === "help" || operation === "--help" || operation === "-h") {
    printHelp();
    return 0;
  }

  if (operation === "classify") {
    const target = options.args.join(" ");
    if (!target) {
      console.error("classify requires a path.");
      return 1;
    }
    console.log(JSON.stringify(classifyPath(target), null, 2));
    return 0;
  }

  const spec = buildP4Command(operation, options);
  if (!spec.ok) {
    console.error(spec.reason);
    if (spec.checklist) {
      console.error("Checklist: run status/opened, confirm files, confirm GLOBAL impact, then retry with --change, --description, and --apply.");
    } else if (spec.requiresApply) {
      console.error(`Preview command: ${formatCommand(spec)}`);
    }
    return 1;
  }

  if (spec.preview) {
    console.error(`Preview: ${formatCommand(spec)}`);
  }

  const result = runP4Command(spec);
  if (result.stdout) {
    process.stdout.write(result.stdout);
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }
  return result.status;
}

if (require.main === module) {
  process.exitCode = main();
}

module.exports = {
  main,
  parseArgv
};
