// Tests the packaged WebAssembly worker protocol with a simulated Emscripten module.
// Real .wasm end-to-end tests must run after building with em++.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const original = fs.readFileSync(path.join(__dirname, '..', 'playground/worker.js'), 'utf8');
const JS = require('../playground/kasa-runtime.js');

async function start({ wasm = false, nativeFails = false, runtimeFails = false } = {}) {
  const messages = [], imports = [], calls = [];
  const script = wasm ? original.replace('const KASA_HAS_WASM = false;', 'const KASA_HAS_WASM = true;') : original;
  const result = JSON.stringify({ ok: true, output: 'Maakye, Ghana!\n', error: '', steps: 0, mode: 'run', engine: 'native-wasm' });
  const module = {
    ccall(name, ret, args, data) {
      calls.push({name, data});
      if (name === 'kasa_run') {
        if (runtimeFails) throw new Error('Simulated native error');
        return 128;
      }
      if (name === 'kasa_free') return null;
      throw new Error('Unknown export');
    },
    UTF8ToString(pointer) { assert.equal(pointer, 128); return result; },
  };
  const context = {
    URL,
    self: { location: { href: 'https://example.org/worker.js' }, postMessage: m => messages.push(m) },
    importScripts(file) {
      imports.push(file);
      if (file === './kasa-runtime.js') context.self.KasaRuntime = JS;
      else if (file === './native/kasa-native.js') {
        if (nativeFails) throw new Error('Simulated WASM download error');
        context.createKasaModule = async () => module;
      } else throw new Error('Unexpected import: ' + file);
    },
  };
  vm.runInNewContext(script, context, { filename: 'worker.js' });
  await new Promise(resolve => setImmediate(resolve));
  return { messages, imports, calls, context };
}

function execute(state, engine = 'auto', mode = 'run') {
  state.context.self.onmessage({ data: {
    type:'EXECUTE', source:'ka "Maakye, Ghana!"', input:'', mode, requestId:7, engine,
  } });
  const reply = state.messages.at(-1);
  assert.equal(reply.type, 'RESULT');
  assert.equal(reply.requestId, 7);
  return reply;
}

test('JavaScript-only bundle starts without any WASM or CDN downloads', async () => {
  const state = await start();
  assert.deepEqual(state.imports, ['./kasa-runtime.js']);
  assert.equal(state.messages[0].type, 'READY');
  assert.equal(execute(state).result.output, 'Maakye, Ghana!\n');
  assert.equal(execute(state).engine, 'javascript');
  assert.equal(state.messages.some(m => m.type === 'NATIVE_READY'), false);
});

test('WASM-enabled bundle loads a native module without blocking JS readiness', async () => {
  const state = await start({wasm:true});
  assert.equal(state.messages[0].type, 'READY');
  assert.deepEqual(state.imports, ['./kasa-runtime.js', './native/kasa-native.js']);
  assert.equal(state.messages.some(m => m.type === 'NATIVE_READY'), true);
  const r = execute(state);
  assert.equal(r.engine, 'native-wasm');
  assert.equal(r.result.output, 'Maakye, Ghana!\n');
  assert.deepEqual(state.calls.map(c => c.name), ['kasa_run', 'kasa_free']);
});

test('explicit native mode uses native bridge and passes syntax-check flag', async () => {
  const state = await start({wasm:true});
  assert.equal(execute(state, 'native', 'check').engine, 'native-wasm');
  assert.equal(state.calls[0].data[2], 1);
});

test('explicit JavaScript selection ignores an available native VM', async () => {
  const state = await start({wasm:true});
  assert.equal(execute(state, 'javascript').engine, 'javascript');
  assert.equal(state.calls.length, 0);
});

test('WASM asset failure falls back to working JavaScript', async () => {
  const state = await start({wasm:true,nativeFails:true});
  assert.equal(state.messages.some(m=>m.type==='NATIVE_ERROR'), true);
  assert.equal(execute(state).engine, 'javascript');
  const error = execute(state, 'native');
  assert.equal(error.result.ok, false);
  assert.match(error.result.error, /Native WebAssembly is unavailable/);
});

test('native execution exception falls back only in Auto, not forced Native', async () => {
  const state = await start({wasm:true,runtimeFails:true});
  assert.equal(execute(state).engine, 'javascript');
  const state2 = await start({wasm:true,runtimeFails:true});
  state2.context.self.onmessage({data:{type:'EXECUTE',source:'ka 1',input:'',mode:'run',requestId:8,engine:'native'}});
  assert.equal(state2.messages.at(-1).type, 'EXECUTION_ERROR');
});

test('no external runtime downloads are referenced in worker', () => {
  assert.doesNotMatch(original, /pyodide|jsdelivr|unpkg/i);
  assert.match(original, /const KASA_HAS_WASM = false;/);
});
