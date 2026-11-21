/* G1.4 source-only table contract; does not change pinned G1 imports. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const kasa = require("../playground/kasa-runtime.js");
const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "stdlib/g14/tables.kasa"), "utf8");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "tests/g14_table_cases.json"), "utf8"));
assert.equal(manifest.schema_version, 1);
const results = [];
for (const test of manifest.cases) {
  const result = kasa.executeKasa(source + "\n" + test.source);
  results.push({id: test.id, pass: result.ok === true && result.output === test.output,
                actual: result.output, error: result.error});
}
process.stdout.write(JSON.stringify({schema_version: 1, results}) + "\n");
if (results.some(item => !item.pass)) process.exitCode = 1;
