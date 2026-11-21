/* G1.2.3 worker-protocol simulation. This is NOT a real Chromium test. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { loadPinnedG1Modules } = require("../scripts/load_g1_js_modules.cjs");
const root = path.resolve(__dirname, "..");
const g1 = loadPinnedG1Modules();
function boot(enableG1 = false) {
  const messages = [];
  let context;
  const ctx = {
    postMessage(message) { messages.push(message); },
    importScripts(file) {
      if (file === "./kasa-runtime.js") {
        vm.runInContext(fs.readFileSync(path.join(root, "playground/kasa-runtime.js"), "utf8"), context);
      } else if (file === "./kasa-g1-pinned-modules.js" && enableG1) {
        context.KasaG1PinnedModules = g1;
      } else {
        throw new Error("Unpackaged asset requested: " + file);
      }
    },
  };
  ctx.self = ctx;
  context = vm.createContext(ctx);
  let worker = fs.readFileSync(path.join(root, "playground/worker.js"), "utf8");
  if (enableG1) worker = worker.replace(
    "const KASA_HAS_G1_PINNED_MODULES = false;",
    "const KASA_HAS_G1_PINNED_MODULES = true;"
  );
  vm.runInContext(worker, context);
  assert.equal(messages[0].type, "READY");
  function run(source, extras = {}) {
    const requestId = messages.length;
    context.onmessage({data: {type: "EXECUTE", requestId, source, input: "", mode: "run",
      experimentalModules: true, experimentalGeneration: "g1", ...extras}});
    const message = messages.find(item => item.type === "RESULT" && item.requestId === requestId);
    assert.ok(message, "worker must report result");
    return message.result;
  }
  return {run};
}
const source = "fa math firi stdlib: m\nka m.kasa_total([10, 20, 30])\n";
const unavailable = boot();
let result = unavailable.run(source);
assert.equal(result.ok, false);
assert.match(result.error, /no pinned G1 Kasa module bundle/);
const enabled = boot(true);
result = enabled.run(source);
assert.equal(result.ok, true, result.error);
assert.equal(result.output, "60\n");
result = enabled.run(source, {engine: "native"});
assert.equal(result.ok, false);
assert.match(result.error, /require the JavaScript engine/);
result = enabled.run(source, {experimentalGeneration: "g2"});
assert.equal(result.ok, false);
assert.match(result.error, /Unknown experimental/);
result = enabled.run("fa math firi stdlib: m\nka m.kasa_sum([1])\n");
assert.equal(result.ok, false);
assert.match(result.error, /does not export/);
console.log("5 simulated G1 worker-protocol cases passed (not a real browser test)");
