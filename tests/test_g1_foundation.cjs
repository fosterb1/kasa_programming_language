"use strict";
// Shared G1 fixtures executed in the real JS interpreter; no import/catalog mutation.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { executeKasa } = require("../playground/kasa-runtime.js");
const root = path.resolve(__dirname, "..");
const cases = JSON.parse(fs.readFileSync(path.join(__dirname, "conformance_g1_foundation.json"), "utf8"));
assert.equal(cases.schema_version, 1);
const source = cases.libraries.map(p => fs.readFileSync(path.join(root, p), "utf8")).join("\n");
for (const item of cases.cases) {
  test("G1 experimental source: " + item.name, () => {
    const result = executeKasa(source + "\n" + item.source + "\n");
    assert.equal(result.ok, true, result.error);
    assert.equal(result.output, item.expected_stdout);
  });
}
