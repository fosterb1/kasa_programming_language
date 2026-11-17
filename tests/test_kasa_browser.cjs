// Run: node --test tests/test_kasa_browser.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { executeKasa, parse, tokenize } = require('../playground/kasa-runtime.js');

const ROOT = path.join(__dirname, '..');
const sourceLocationConformance = JSON.parse(
  fs.readFileSync(path.join(ROOT, 'tests/conformance_source_locations.json'), 'utf8')
);
for (const fixture of sourceLocationConformance.cases) {
  test(`source position conformance: ${fixture.name}`, () => {
    const result = executeKasa(fixture.source, '', 'check');
    assert.equal(result.ok, false);
    assert.ok(
      result.error.includes(
        `playground.kasa:${fixture.line}:${fixture.column}: ${fixture.category}:`
      ),
      result.error
    );
  });
}

const remainderConformance = JSON.parse(
  fs.readFileSync(path.join(ROOT, 'tests/conformance_remainder.json'), 'utf8')
);
for (const fixture of remainderConformance.cases) {
  test(`remainder conformance: ${fixture.name}`, () => {
    const result = executeKasa(fixture.source);
    assert.equal(result.ok, true, result.error);
    assert.equal(result.output, fixture.expected_stdout);
  });
}
for (const fixture of remainderConformance.errors) {
  test(`remainder error: ${fixture.name}`, () => {
    const result = executeKasa(fixture.source);
    assert.equal(result.ok, false);
    assert.match(result.error, new RegExp('playground\\.kasa:\\d+:\\d+: ' + fixture.category));
  });
}

const examples = {
  'hello.kasa': 'Maakye, Ghana!\n',
  'conditions.kasa': 'Maakye, Ama\n',
  'functions.kasa': '10\n',
  'loops.kasa': '1\n2\n3\nMeda wo ase\nMeda wo ase\n',
  'lists.kasa': '99\n3\n',
  'remainder.kasa': '1\n2\n-2\n-1\n',
};
for (const [filename, expected] of Object.entries(examples)) {
  test(`execute example ${filename}`, () => {
    const src = fs.readFileSync(path.join(ROOT, 'examples', filename), 'utf8');
    const result = executeKasa(src);
    assert.equal(result.ok, true, result.error);
    assert.equal(result.output, expected);
  });
}
const programs = [
  ['ka 42\nka nokware\nka atoro\nka hwee', '42\nnokware\natoro\nhwee\n'],
  ['ka 2 + 3 * 4\nka (2 + 3) * 4', '14\n20\n'],
  ['ma x = 10\nma x = x + 5\nka x', '15\n'],
  ['ka 12 / 4\nka 7 % 3', '3.0\n1\n'],
  ['ka ɛnyɛ nokware\nka nokware ne atoro\nka nokware anaa atoro', 'atoro\natoro\nnokware\n'],
  ['ka atoro ne (1 / 0 == 0)\nka nokware anaa (1 / 0 == 0)', 'atoro\nnokware\n'],
  ['sɛ 5 > 2 a\n  ka "yes"\nanyɛ_saa_a\n  ka "no"\nawiei', 'yes\n'],
  ['mpɛn 3\n ka "x"\nawiei', 'x\nx\nx\n'],
  ['ma n = 1\nbere_a n <= 3\nka n\nma n = n + 1\nawiei', '1\n2\n3\n'],
  ['dwumadie fa_bi(a,b)\n sanma a+b\nawiei\nka fa_bi(2,7)', '9\n'],
  ['ma xs=[10,20,30]\nka xs[0]\nma xs[1]=99\nka xs[1]\nka tentɛn(xs)', '10\n99\n3\n'],
  ['ma ɛdin="Ama"\nma ɔman="Ghana"\nka ɛdin+" - "+ɔman', 'Ama - Ghana\n'],
  ['ka nɔma("12") + 3\nka nsɛm(nokware)', '15\nnokware\n'],
  ['ka bisa()', 'Ama\n', 'Ama\n'],
  ['ma edin = bisa("Wo din de sɛn? ")\nka "Akwaaba, " + edin', 'Wo din de sɛn? Akwaaba, Ama\n', 'Ama\n'],
  ['ka bisa("")', 'Ama\n', 'Ama\n'],
  ['ka 1 # inline comment\n# line\nka "# is text"', '1\n# is text\n'],
  ['ka "a\\nb"', 'a\nb\n'],
  ['ma xs=[1,[2,3]]\nka xs[1][0]', '2\n'],
  ['ka 1 == nokware\nka [1] == [nokware]', 'atoro\natoro\n'],
  ['ka 1 + -2', '-1\n'],
  ['ma x = 10\ndwumadie test()\n ma x = 20\n ka x\nawiei\ntest()\nka x\ndwumadie fact(n)\n sɛ n <= 1 a\n  sanma 1\n awiei\n sanma n * fact(n - 1)\nawiei\nka fact(5)', '20\n10\n120\n'],
  ['ma count=0\nmpɛn 5\n ma count=count+1\n sɛ count == 2 a\n toa_so\n awiei\n sɛ count == 4 a\n gyae\n awiei\n ka count\nawiei', '1\n3\n'],
  ['ka ["a", "b"]\nka 2.0\nka 0.75', "['a', 'b']\n2.0\n0.75\n"],
];
programs.forEach(([source, expected, input = '']) => {
  test(`execute interpreter fixture ${programs.findIndex(x => x[0] === source) + 1}`, () => {
    const result = executeKasa(source, input);
    assert.equal(result.ok, true, result.error);
    assert.equal(result.output, expected);
  });
});
const failures = [
  ['ka missing', 'NameError'],
  ['ka 1 / 0', 'ZeroDivisionError'],
  ['ka 1 + "a"', 'TypeError'],
  ['ka nokware + 1', 'TypeError'],
  ['ka 4 % 1.2', 'TypeError'],
  ['sɛ 1 a\nka "x"\nawiei', 'TypeError'],
  ['mpɛn -1\nka 1\nawiei', 'TypeError'],
  ['mpɛn 1.5\nka 1\nawiei', 'TypeError'],
  ['ka [1][2]', 'IndexError'],
  ['ka [1][atoro]', 'TypeError'],
  ['ka nɔma("nah")', 'TypeError'],
  ['gyae', 'SyntaxError'],
  ['toa_so', 'SyntaxError'],
  ['sanma 3', 'SyntaxError'],
  ['ka foo(2)', 'NameError'],
  ['ka tentɛn(1)', 'TypeError'],
  ['ka bisa(1)', 'TypeError'],
  ['ka bisa("One", "Two")', 'TypeError'],
  ['ka "unterminated', 'SyntaxError'],
  ['ka 5 & 3', 'SyntaxError'],
  ['sɛ nokware a\n  ka 1', 'SyntaxError'],
  ['awiei', 'SyntaxError'],
  ['anyɛ_saa_a', 'SyntaxError'],
  ['ka 1 < 2 < 3', 'SyntaxError'],
  ['ma 1 = 2', 'SyntaxError'],
  ['ma [1,2][0]=8', 'SyntaxError'],
  ['dwumadie f(a,a)\nka a\nawiei', 'SyntaxError'],
];
failures.forEach(([source, category],i) => {
  test(`source error fixture ${i+1} (${category})`, () => {
    const result = executeKasa(source);
    assert.equal(result.ok, false);
    assert.match(result.error, new RegExp('playground.kasa:\\d+:\\d+: '+category));
  });
});

test('syntax check does not run Kasa program', () => {
  const result = executeKasa('ka 1/0', '', 'check');
  assert.deepEqual(result, {ok: true,output: '',error: '',steps: 0,mode: 'check'});
});
test('Unicode Twi identifiers and CRLF locations', () => {
  const tok = tokenize('ma ɛdin = "Kɔfi"\r\nka ɛdin\r\n');
  assert.deepEqual(tok.slice(0,5).map(t => t.kind), ['ASSIGN','NAME','=','STRING','NEWLINE']);
  assert.equal(tok[5].line, 2);
  assert.equal(tok[5].column, 1);
});
test('resource limits: infinite loop', () => {
  const r = executeKasa('bere_a nokware\nawiei');
  assert.equal(r.ok, false);
  assert.match(r.error,/Execution limit/);
});
test('resource limits: recursive function', () => {
  const r = executeKasa('dwumadie f()\n sanma f()\nawiei\nka f()');
  assert.equal(r.ok, false);
  assert.match(r.error,/call depth/);
});
test('resource limits: source and input', () => {
  assert.match(executeKasa('#'.repeat(50001)).error,/Source exceeds/);
  assert.match(executeKasa('ka 1', 'x'.repeat(50001)).error,/Input exceeds/);
});
test('resource limits: bounded huge integer', () => {
  const r=executeKasa('ma x=1000000000000000000000000000000000000000\nmpɛn 100\n ma x=x*x\nawiei');
  assert.equal(r.ok, false);
  assert.match(r.error,/Integer exceeds/);
});
test('resource limits: output bound retains partial output', () => {
  const r=executeKasa('mpɛn 20000\n ka "abcdefghijklmnop"\nawiei');
  assert.equal(r.ok,false);
  assert.match(r.error,/Output exceeded/);
  assert.ok(r.output.length>0 && r.output.length<=64000);
});
test('each execution isolates variables', () => {
  assert.equal(executeKasa('ma secret="hello"').ok,true);
  const r = executeKasa('ka secret');
  assert.match(r.error,/Unknown name/);
});
test('browser uses local script without CDN', () => {
  const worker=fs.readFileSync(path.join(ROOT,'playground/worker.js'),'utf8');
  assert.match(worker,/importScripts\("\.\/kasa-runtime\.js"\)/);
  assert.doesNotMatch(worker, /https?:|pyodide/i);
});
test('worker starts and runs Kasa in isolated VM', () => {
  const worker=fs.readFileSync(path.join(ROOT,'playground/worker.js'),'utf8');
  const messages=[], paths=[];
  const context={self:{postMessage:m=>messages.push(m)}};
  context.importScripts=p=>{paths.push(p); context.self.KasaRuntime=require('../playground/kasa-runtime.js');};
  vm.runInNewContext(worker,context,{filename:'worker.js'});
  assert.deepEqual(paths,['./kasa-runtime.js']);
  assert.equal(messages[0].type,'READY');
  context.self.onmessage({data:{type:'EXECUTE',requestId:42,source:'ka "Maakye, Ghana!"',input:'',mode:'run'}});
  assert.equal(messages[1].type,'RESULT');
  assert.equal(messages[1].requestId,42);
  assert.equal(messages[1].result.output,'Maakye, Ghana!\n');
});
test('worker reports missing local script', () => {
  const worker=fs.readFileSync(path.join(ROOT,'playground/worker.js'),'utf8');
  const messages=[];
  const context={self:{postMessage:m=>messages.push(m)},importScripts(){throw new Error('Local script missing');}};
  vm.runInNewContext(worker,context);
  assert.equal(messages[0].type,'BOOT_ERROR');
  assert.match(messages[0].message,/Local script missing/);
});
