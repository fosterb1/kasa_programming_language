/* G0.4 opt-in, trusted-source JS module execution regression.
 * No browser UI/worker changes; metadata obtained from locally pinned files.
 * Run: node tests/test_js_experimental_modules.js
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
const kasa = require(path.join(root, "playground/kasa-runtime.js"));
const catalog = JSON.parse(fs.readFileSync(path.join(root, "stdlib/catalog.json"), "utf8"));
const modules = Object.create(null);
for (const item of catalog.modules) {
  const filename = path.join(root, item.source);
  const source = fs.readFileSync(filename, "utf8").replace(/\r\n/g, "\n");
  const digest = "sha256:" + crypto.createHash("sha256").update(source, "utf8").digest("hex");
  assert.equal(digest, item.content_identity, "Catalog source identity mismatch: " + item.id);
  modules[item.id] = { source, exports: item.exports };
}
const run = (source, mode = "run") => kasa.executeKasa(source, "", mode, { experimentalModules: modules });
let total = 0;
function test(label, fn) { fn(); total++; process.stdout.write("PASS " + label + "\n"); }

test("two pinned Kasa modules execute independently", () => {
  const result = run("@math:m\n@collections:c\nka m.kasa_sum([10,20,30])\nka c.kasa_contains([1,2,3],2)");
  assert.equal(result.ok, true, result.error);
  assert.equal(result.output, "60\nnokware\n");
});
test("default JavaScript syntax remains unchanged", () => {
  const result = kasa.executeKasa("@math:m\nka m.kasa_sum([1])");
  assert.equal(result.ok, false);
  assert.match(result.error, /SyntaxError/);
});
test("reserved module alias rejected", () => {
  const result = run("@math:ka\nka 1");
  assert.equal(result.ok, false);
  assert.match(result.error, /reserved module alias/);
});
for (const [source, error] of [
  ["@math:m\n@collections:m\nka 1", /alias reused/],
  ["@math:m\n@math:n\nka 1", /more than once/],
  ["@missing:m\nka 1", /Unknown catalog module/],
  ['@math:m\nka "do not print"\nka m.not_public([1])', /does not export/],
  ['@math:m\nka "do not print"\nka c.kasa_sum([1])', /Unknown module alias/],
  ['@math:m\nka "do not print"\nma m = 4', /cannot be reassigned/],
  ['@math:m\nka "do not print"\n@collections:c', /precede statements/],
  ['@math:m\nka "do not print"\ndwumadie m()\nsanma 1\nawiei', /cannot be redeclared/],
]) {
  test("reject preflight: " + error.source, () => {
    const result = run(source);
    assert.equal(result.ok, false);
    assert.match(result.error, error);
    assert.equal(result.output, "");
  });
}
test("same Kasa functions still run without module opt-in", () => {
  const result = kasa.executeKasa('ka "Maakye, Ghana!"');
  assert.equal(result.ok, true, result.error);
  assert.equal(result.output, "Maakye, Ghana!\n");
});
test("experimental check mode parses but does not execute", () => {
  const result = run("@math:m\nka m.kasa_sum([1])", "check");
  assert.equal(result.ok, true, result.error);
  assert.equal(result.output, "");
  assert.equal(result.steps, 0);
});
process.stdout.write(total + " JS experimental module checks passed\n");
