/* G1.6 validation fixture runner, not a Kasa runtime integration. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {validateSchema, validateRecord} = require("../scripts/g16_validate_record.cjs");
const data = JSON.parse(fs.readFileSync(path.join(__dirname, "g16_validation_cases.json"), "utf8"));
assert.equal(data.schema_version, 1);
let passed = 0;
for (const item of data.cases) {
  assert.deepEqual(validateRecord(data.schema, item.record), item.expected, item.id);
  passed += 1;
}
for (const item of data.invalid_schemas) {
  assert.throws(() => validateSchema(item.schema), (err) => err.message.includes(item.reject), item.id);
}
process.stdout.write(JSON.stringify({
  schema_version: 1, engine: "javascript_host_validation",
  passed: true, cases: passed, invalid_schemas: data.invalid_schemas.length,
}) + "\n");
