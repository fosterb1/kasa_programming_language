/* G1.3 opt-in JavaScript runner for the *same* fixture JSON used by Python/native.
 * Node only, no browser deployment. Outputs one JSON report, not test text.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const { loadPinnedG1Modules } = require("../scripts/load_g1_js_modules.cjs");
const kasa = require("../playground/kasa-runtime.js");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "tests/g13_cross_runtime_cases.json"), "utf8"));
assert.equal(manifest.schema_version, 1);
const modules = loadPinnedG1Modules();
const results = [];
for (const item of manifest.cases) {
  const result = kasa.executeKasa(item.source, "", "run", { experimentalModules: modules });
  const pass = Object.hasOwn(item, "output")
    ? result.ok === true && result.output === item.output
    : result.ok === false && result.output === "" && result.error.includes(item.reject);
  results.push({id: item.id, pass, ok: result.ok, output: result.output, error: result.error});
}
process.stdout.write(JSON.stringify({schema_version: 1, engine: "javascript_g1",
  results}) + "\n");
if (results.some(item => !item.pass)) process.exitCode = 1;
