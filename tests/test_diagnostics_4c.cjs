// Phase 4C.2 — shared diagnostic categories, no external services.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {executeKasa} = require('../playground/kasa-runtime.js');
const corpus = JSON.parse(fs.readFileSync(path.join(__dirname,'conformance_diagnostics_4c.json'),'utf8'));
test('4C diagnostic fixture set is unique and versioned',()=>{
 assert.equal(corpus.schema_version,1);
 assert.equal(new Set(corpus.cases.map(c=>c.name)).size,corpus.cases.length);
 assert.ok(corpus.cases.length>=9);
});
for(const c of corpus.cases) {
 test('4C JS error category: '+c.name,()=>{
  const result=executeKasa(c.source,'','run');
  assert.equal(result.ok,false,c.name+' unexpectedly succeeded');
  assert.match(result.error,new RegExp('\\.kasa:[0-9]+:[0-9]+: '+c.error_category+':'),c.name+': '+result.error);
 });
}
