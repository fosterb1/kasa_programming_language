const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {parseKasaDiagnostic} = require('../src/diagnostic-protocol');

const file = path.resolve('examples/hello.kasa');
const make = (extra={}) => JSON.stringify({
  schema_version: 1, category: 'SyntaxError',
  message: 'Unexpected character', file, line: 2, column: 4, ...extra
});
test('parse validated source coordinates', () => {
  assert.deepEqual(parseKasaDiagnostic(make(), file), {
    category: 'SyntaxError', message: 'Unexpected character', line: 2, column: 4
  });
});
test('accept file read error with null coordinates', () => {
  assert.deepEqual(parseKasaDiagnostic(make({
    category: 'FileError', line: null, column: null
  }), file), {
    category: 'FileError', message: 'Unexpected character',
    line: null, column: null
  });
});
test('reject malformed, foreign, and unsupported schema', () => {
  assert.equal(parseKasaDiagnostic('{oops', file), null);
  assert.equal(parseKasaDiagnostic(make({schema_version: 2}), file), null);
  assert.equal(parseKasaDiagnostic(make({file: '/another/file.kasa'}), file), null);
  assert.equal(parseKasaDiagnostic(make({line: 0}), file), null);
  assert.equal(parseKasaDiagnostic(make({line: 1.5}), file), null);
  assert.equal(parseKasaDiagnostic(make({category: 'FileError', line: 3, column: null}), file), null);
  assert.equal(parseKasaDiagnostic('[]', file), null);
});
test('reject oversized diagnostic data', () => {
  assert.equal(parseKasaDiagnostic('x'.repeat(131073), file), null);
});
