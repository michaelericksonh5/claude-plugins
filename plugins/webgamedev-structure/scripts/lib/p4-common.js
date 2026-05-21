"use strict";

const { spawnSync } = require("node:child_process");

const READ_ONLY_OPERATIONS = new Set([
  "info",
  "set",
  "login-status",
  "client",
  "opened",
  "status",
  "changes",
  "describe",
  "filelog",
  "files",
  "fstat",
  "have",
  "print",
  "where",
  "diff"
]);

const MUTATING_OPERATIONS = new Set([
  "sync",
  "edit",
  "add",
  "reconcile",
  "submit"
]);

const PREVIEWABLE_MUTATIONS = new Set([
  "sync",
  "edit",
  "add",
  "reconcile"
]);

const BLOCKED_OPERATIONS = new Set([
  "clean",
  "delete",
  "move",
  "obliterate",
  "revert",
  "typemap",
  "resolve"
]);

const SAFE_RECONCILE_FLAGS = new Set(["-a", "-e", "-ae", "-ea"]);

function hasFlag(args, flag) {
  return args.includes(flag) || args.some((arg) => arg.startsWith(`${flag}=`));
}

function rejectDangerous(operation, args) {
  if (BLOCKED_OPERATIONS.has(operation)) {
    return `Blocked p4 ${operation}; H5G never-delete policy does not allow this plugin to automate that operation.`;
  }

  if (operation === "reconcile") {
    if (hasFlag(args, "-w")) {
      return "Blocked p4 reconcile -w; H5G never-delete policy does not allow workspace delete automation.";
    }
    if (args.some((arg) => arg === "-d" || (/^-[A-Za-z]+$/.test(arg) && arg.includes("d")))) {
      return "Blocked p4 reconcile delete behavior; H5G never-delete policy allows reconcile add/edit only.";
    }
  }

  return null;
}

function rejectUnsupportedFlags(operation, args) {
  if (!MUTATING_OPERATIONS.has(operation)) {
    return null;
  }

  const flag = args.find((arg) => arg.startsWith("-") && (operation !== "reconcile" || !SAFE_RECONCILE_FLAGS.has(arg)));
  if (flag) {
    return `Blocked unsupported p4 ${operation} flag: ${flag}`;
  }

  return null;
}

function buildP4Command(operation, options = {}) {
  const op = String(operation || "").trim();
  const args = Array.isArray(options.args) ? options.args.map(String) : [];
  const apply = Boolean(options.apply);
  const change = options.change ? String(options.change) : "";
  const description = options.description ? String(options.description) : "";
  const dangerousReason = rejectDangerous(op, args);

  if (dangerousReason) {
    return {
      ok: false,
      blocked: true,
      reason: dangerousReason,
      command: "p4",
      args: [op, ...args],
      preview: false,
      mutating: true
    };
  }

  const unsupportedFlagReason = rejectUnsupportedFlags(op, args);
  if (unsupportedFlagReason) {
    return {
      ok: false,
      blocked: true,
      reason: unsupportedFlagReason,
      command: "p4",
      args: [op, ...args],
      preview: false,
      mutating: true
    };
  }

  if (op === "doctor") {
    return {
      ok: true,
      sequence: [
        ["info"],
        ["set"],
        ["login", "-s"],
        ["client", "-o"]
      ],
      preview: false,
      mutating: false
    };
  }

  if (op === "login-status") {
    return readonly(["login", "-s"]);
  }

  if (op === "client") {
    return readonly(["client", "-o", ...args]);
  }

  if (op === "diff") {
    return readonly(["diff", "-sa", ...args]);
  }

  if (READ_ONLY_OPERATIONS.has(op)) {
    return readonly([op, ...args]);
  }

  if (!MUTATING_OPERATIONS.has(op)) {
    return {
      ok: false,
      blocked: true,
      reason: `Unknown or unsupported p4 operation: ${op}`,
      command: "p4",
      args: [op, ...args],
      preview: false,
      mutating: false
    };
  }

  if (op === "submit") {
    if (!change || !description) {
      return {
        ok: false,
        checklist: true,
        reason: "Submit requires --change and --description.",
        command: "p4",
        args: ["submit"],
        preview: true,
        mutating: true
      };
    }
    return mutating(["submit", "-c", change, "-d", description], apply, false);
  }

  if (op === "reconcile") {
    const targets = args.filter((arg) => !SAFE_RECONCILE_FLAGS.has(arg));
    return mutating(["reconcile", ...(apply ? [] : ["-n"]), "-a", "-e", ...targets], apply, !apply);
  }

  if (PREVIEWABLE_MUTATIONS.has(op) && !apply) {
    return mutating([op, "-n", ...args], false, true);
  }

  return mutating([op, ...args], apply, false);
}

function readonly(args) {
  return {
    ok: true,
    command: "p4",
    args,
    preview: false,
    mutating: false
  };
}

function mutating(args, apply, preview) {
  if (!apply && !preview) {
    return {
      ok: false,
      requiresApply: true,
      reason: "Mutating p4 operation requires --apply.",
      command: "p4",
      args,
      preview: false,
      mutating: true
    };
  }

  return {
    ok: true,
    command: "p4",
    args,
    preview,
    mutating: true
  };
}

function runP4Command(commandSpec, options = {}) {
  if (!commandSpec.ok) {
    return {
      status: 1,
      stdout: "",
      stderr: commandSpec.reason || "Command was not runnable."
    };
  }

  if (commandSpec.sequence) {
    const results = commandSpec.sequence.map((args) => runSpawn(args, options));
    const failed = results.find((result) => result.status !== 0);
    return {
      status: failed ? failed.status : 0,
      stdout: results.map((result) => result.stdout).filter(Boolean).join("\n"),
      stderr: results.map((result) => result.stderr).filter(Boolean).join("\n")
    };
  }

  return runSpawn(commandSpec.args, options);
}

function runSpawn(args, options) {
  const result = spawnSync("p4", args, {
    encoding: "utf8",
    shell: false,
    cwd: options.cwd || process.cwd()
  });

  return {
    status: typeof result.status === "number" ? result.status : 1,
    stdout: result.stdout || "",
    stderr: result.stderr || result.error?.message || ""
  };
}

module.exports = {
  BLOCKED_OPERATIONS,
  MUTATING_OPERATIONS,
  PREVIEWABLE_MUTATIONS,
  READ_ONLY_OPERATIONS,
  buildP4Command,
  rejectDangerous,
  rejectUnsupportedFlags,
  runP4Command
};
