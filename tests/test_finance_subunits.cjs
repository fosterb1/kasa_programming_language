// Phase 8 integer-pesewa fixtures exercised in the actual JavaScript interpreter.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { executeKasa } = require('../playground/kasa-runtime.js');
const fixtures = JSON.parse(fs.readFileSync(path.join(__dirname, 'conformance_finance_subunits.json'), 'utf8'));
for (const item of fixtures.cases) {
  test('money subunits: ' + item.name, () => {
    const result = executeKasa(item.source);
    assert.equal(result.ok, true, result.error);
    assert.equal(result.output, item.expected_stdout);
  });
}
