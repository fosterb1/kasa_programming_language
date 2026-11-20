/* Shared G0.4 JavaScript opt-in module conformance fixtures.
 * Runs the same source files and output/error expectations as Python.
 * Does not claim browser worker, native WASM, or KBC1 support.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const ROOT = path.resolve(__dirname, "..");
const kasa = require(path.join(ROOT, "playground/kasa-runtime.js"));
const fixtures = JSON.parse(fs.readFileSync(path.join(ROOT, "tests/conformance_experimental_modules.json"), "utf8"));
assert.equal(fixtures.schema_version, 1);

const catalog = JSON.parse(fs.readFileSync(path.join(ROOT, "stdlib/catalog.json"), "utf8"));
const modules = Object.create(null);
for (const entry of catalog.modules) {
  const source = fs.readFileSync(path.join(ROOT, entry.source), "utf8").replace(/\r\n/g, "\n");
  const identity = "sha256:" + crypto.createHash("sha256").update(source, "utf8").digest("hex");
  assert.equal(identity, entry.content_identity, "Unpinned source: " + entry.id);
  modules[entry.id] = { source, exports: entry.exports };
}

for (const item of fixtures.cases) {
  const result = kasa.executeKasa(item.source, "", "run", { experimentalModules: modules });
  if (Object.hasOwn(item, "output")) {
    assert.equal(result.ok, true, item.id + ": " + result.error);
    assert.equal(result.output, item.output, item.id);
  } else {
    assert.equal(result.ok, false, item.id);
    assert.ok(result.error.includes(": " + item.js_category + ":"), item.id + ": " + result.error);
    assert.ok(result.error.toLowerCase().includes(item.error_contains.toLowerCase()), item.id + ": " + result.error);
    assert.equal(result.output, "", item.id + ": partial output escaped preflight");
  }
  process.stdout.write("PASS " + item.id + "\n");
}
process.stdout.write(fixtures.cases.length + " shared G0.4 JavaScript module cases passed\n");
