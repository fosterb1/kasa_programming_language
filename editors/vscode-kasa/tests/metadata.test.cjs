const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = path.join(__dirname, '..');
const json = name => JSON.parse(fs.readFileSync(path.join(base,name),'utf8'));
test('VS Code extension declares Kasa language, snippets and commands', () => {
  const p=json('package.json');
  assert.equal(p.contributes.languages[0].extensions[0],'.kasa');
  assert.deepEqual(p.contributes.commands.map(x=>x.command),['kasa.runFile','kasa.checkFile']);
  assert.ok(json('snippets/kasa.code-snippets')['Function']);
  assert.ok(json('syntaxes/kasa.tmLanguage.json').patterns.length>=7);
  assert.ok(json('language-configuration.json').indentationRules);
});
test('runner does not use shell command interpolation', () => {
  const s=fs.readFileSync(path.join(base,'src/extension.js'),'utf8');
  assert.match(s,/shell: false/);
  assert.match(s,/spawn\(executable, \[mode, file\]/);
  assert.doesNotMatch(s,/\bexec\(/);
});

test('installed Kasa CLI is the default command and missing executable yields guidance', () => {
  const manifest=json('package.json');
  assert.equal(manifest.contributes.configuration.properties['kasa.executablePath'].default,'kasa');
  const source=fs.readFileSync(path.join(base,'src/extension.js'),'utf8');
  assert.match(source,/get\('executablePath', 'kasa'\)/);
  assert.match(source,/error\.code === 'ENOENT'/);
  assert.match(source,/kasa\.executablePath/);
});
