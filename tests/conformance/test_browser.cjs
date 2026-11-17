// Common language semantics are tested against both Python and the JS browser engine.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {executeKasa} = require('../../playground/kasa-runtime.js');
const cases=JSON.parse(fs.readFileSync(path.join(__dirname,'cases.json'),'utf8'));
test('shared fixture schema',()=>assert.equal(cases.schema,'kasa-conformance-v1'));
for (const spec of cases.success) {
  test('Kasa JS success: ' + spec.id, () => {
    const result=executeKasa(spec.source,spec.input || '');
    assert.equal(result.ok,true,result.error);
    assert.equal(result.output,spec.output);
  });
}
for (const spec of cases.failures) {
  test('Kasa JS error: ' + spec.id, () => {
    const result=executeKasa(spec.source);
    assert.equal(result.ok,false);
    assert.match(result.error,new RegExp(': ' + spec.error + ':'));
  });
}
