/* Simulate the packaged browser worker protocol with Node VM.
 * This does not replace a real browser/Netlify integration test.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
const playground = path.join(root, "playground");
const catalog = JSON.parse(fs.readFileSync(path.join(root, "stdlib/catalog.json"), "utf8"));
const modules = Object.create(null);
for (const module of catalog.modules) {
  const source = fs.readFileSync(path.join(root, module.source), "utf8").replace(/\r\n/g, "\n");
  const hash = "sha256:" + crypto.createHash("sha256").update(source).digest("hex");
  assert.equal(hash, module.content_identity);
  modules[module.id] = { source, exports: module.exports };
}
function boot(packaged) {
  const messages = [];
  const ctx = {
    console, messages,
    postMessage(value) { messages.push(value); },
    importScripts(file) {
      if (file === "./kasa-runtime.js") {
        vm.runInContext(fs.readFileSync(path.join(playground, "kasa-runtime.js"), "utf8"), context);
      } else if (file === "./kasa-pinned-modules.js" && packaged) {
        context.KasaPinnedModules = Object.freeze(modules);
      } else {
        throw new Error("Unpackaged asset requested: " + file);
      }
    },
  };
  ctx.self = ctx;
  const context = vm.createContext(ctx);
  let worker = fs.readFileSync(path.join(playground, "worker.js"), "utf8");
  if (packaged) {
    worker = worker.replace("const KASA_HAS_PINNED_MODULES = false;", "const KASA_HAS_PINNED_MODULES = true;");
  }
  vm.runInContext(worker, context);
  assert.equal(messages[0].type, "READY");
  function execute(source, extras = {}) {
    const id = messages.length;
    context.onmessage({data: {type: "EXECUTE", source, input: "", mode: "run", requestId: id, ...extras}});
    const result = messages.find(m => m.type === "RESULT" && m.requestId === id);
    assert.ok(result, "Worker must return a result");
    return result;
  }
  return { execute, messages };
}

const unpackaged = boot(false);
let result = unpackaged.execute('ka "Maakye!"');
assert.equal(result.result.ok, true, result.result.error);
assert.equal(result.result.output, "Maakye!\n");
result = unpackaged.execute("@math:m\nka m.kasa_sum([10,20,30])", {experimentalModules: true});
assert.equal(result.result.ok, false);
assert.match(result.result.error, /no pinned Kasa module bundle/);

const packaged = boot(true);
result = packaged.execute("@math:m\n@collections:c\nka m.kasa_sum([10,20,30])\nka c.kasa_contains([1,2],2)", {experimentalModules: true});
assert.equal(result.result.ok, true, result.result.error);
assert.equal(result.result.output, "60\nnokware\n");
result = packaged.execute("@math:m\nka m.kasa_sum([1])", {experimentalModules: true, engine: "native"});
assert.equal(result.result.ok, false);
assert.match(result.result.error, /require the JavaScript engine/);
result = packaged.execute('ka "Normal mode"', {experimentalModules: false});
assert.equal(result.result.ok, true, result.result.error);
assert.equal(result.result.output, "Normal mode\n");
process.stdout.write("5 simulated worker/module protocol checks passed\n");
