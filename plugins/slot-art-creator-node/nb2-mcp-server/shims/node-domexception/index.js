// node-domexception shim
//
// The upstream package `node-domexception` was deprecated with the message
// "Use your platform's native DOMException instead". On Node >=18 (which
// this plugin requires), `globalThis.DOMException` is a built-in global and
// the upstream polyfill does nothing useful at runtime — it just re-exports
// the same native class.
//
// This shim is wired in via the `overrides` block in
// nb2-mcp-server/package.json so npm never installs the deprecated package
// in the first place. The only consumer in our dependency tree is
// fetch-blob, which does `import DOMException from 'node-domexception'`
// expecting the default export to be the class itself.
//
// Behavior is identical to the upstream package's behavior on Node >=18:
//   module.exports = globalThis.DOMException
//
// Verified against the upstream source at
// https://github.com/jimmywarting/node-domexception/blob/master/index.js
// where the polyfill block is a no-op when globalThis.DOMException already
// exists (always true on Node >=18).

if (typeof globalThis.DOMException !== "function") {
  // Defensive fallback. Should be unreachable on supported Node versions.
  // Keep behavior compatible with the upstream package by deriving the class
  // from a worker_threads MessageChannel structured-clone error, exactly the
  // way upstream does it on legacy Node. This branch is dead code on Node 18+.
  try {
    const { MessageChannel } = require("worker_threads");
    const port = new MessageChannel().port1;
    const ab = new ArrayBuffer(0);
    port.postMessage(ab, [ab, ab]);
  } catch (err) {
    if (err && err.constructor && err.constructor.name === "DOMException") {
      globalThis.DOMException = err.constructor;
    }
  }
}

module.exports = globalThis.DOMException;
