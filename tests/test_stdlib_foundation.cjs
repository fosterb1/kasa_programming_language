const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { executeKasa } = require('../playground/kasa-runtime.js');
const root = path.join(__dirname, '..');
const corpus = JSON.parse(fs.readFileSync(path.join(__dirname, 'conformance_stdlib_foundation.json'), 'utf8'));
const source = corpus.libraries.map(p => fs.readFileSync(path.join(root, p), 'utf8')).join('\n');
for (const fixture of corpus.cases) {
  test('experimental stdlib: ' + fixture.name, () => {
    const result = executeKasa(source + '\n' + fixture.source + '\n');
    assert.equal(result.ok, true, result.error);
    assert.equal(result.output, fixture.expected_stdout);
  });
}
