/* G1.5 source-only record fixtures, no runtime imports or syntax additions. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const runtime = require("../playground/kasa-runtime.js");
const root = path.resolve(__dirname, "..");
const library = fs.readFileSync(path.join(root, "stdlib/g15/records.kasa"), "utf8");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "tests/g15_record_cases.json"), "utf8"));
assert.equal(manifest.schema_version, 1);
const results = manifest.cases.map((item) => {
  const r = runtime.executeKasa(library + "\n" + item.source);
  return {id: item.id, pass: r.ok && r.output === item.output, output: r.output, error: r.error};
});
process.stdout.write(JSON.stringify({schema_version: 1, results}) + "\n");
if (results.some((item) => !item.pass)) process.exitCode = 1;
