// Offline Web Worker startup tests. Run with: node --test playground/test_worker.cjs
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const script = fs.readFileSync(path.join(__dirname, "worker.js"), "utf8");

async function boot({ failFirst = false, failAll = false } = {}) {
  const messages = [], attempts = [], assetURLs = [];
  const globals = new Map();
  const runtime = {
    FS: { mkdirTree() {}, writeFile() {} },
    globals: { set: (name,value) => globals.set(name,value), delete: (name) => globals.delete(name) },
    runPython: (code) => code.includes("json.dumps")
      ? JSON.stringify({ ok: true, output: "Maakye, Ghana!\n", error: "", mode: "run", steps: 1 })
      : undefined,
  };
  const context = {
    URL,
    self: {
      location: { href: "https://example.com/playground/worker.js" },
      postMessage: message => messages.push(message),
    },
    fetch: async () => ({ ok: true, text: async () => "mock source" }),
    importScripts: url => {
      attempts.push(url);
      if (failAll || (failFirst && attempts.length === 1)) throw new Error("CDN unavailable");
      context.loadPyodide = async ({ indexURL }) => {
        assetURLs.push(indexURL);
        return runtime;
      };
    },
  };
  vm.runInNewContext(script, context, { filename: "worker.js" });
  for (let i = 0; i < 12; ++i) await new Promise(resolve => setImmediate(resolve));
  return { messages, attempts, assetURLs, context };
}

test("first CDN initializes interpreter", async () => {
  const {messages,attempts,assetURLs} = await boot();
  assert.equal(attempts.length, 1);
  assert.match(attempts[0], /v314\.0\.8\/full\/pyodide\.js$/);
  assert.equal(assetURLs.length, 1);
  assert.equal(messages.at(-1).type, "READY");
});

test("fallback works if first provider fails", async () => {
  const {messages,attempts,assetURLs} = await boot({failFirst: true});
  assert.equal(attempts.length, 2);
  assert.match(attempts[1], /unpkg\.com\/pyodide@314\.0\.8\/pyodide\.js$/);
  assert.match(assetURLs[0], /unpkg\.com/);
  assert.equal(messages.at(-1).type, "READY");
});

test("reports all provider failures to the browser", async () => {
  const {messages,attempts} = await boot({failAll: true});
  assert.equal(attempts.length, 3);
  assert.equal(messages.at(-1).type, "BOOT_ERROR");
  assert.match(messages.at(-1).message, /Retry engine/);
  assert.match(messages.at(-1).message, /UNPKG/);
});

test("sends program result after successful startup", async () => {
  const {messages,context} = await boot({failFirst: true});
  context.self.onmessage({data:{type:"EXECUTE", source:'ka "Maakye, Ghana!"',input:"",mode:"run",requestId:9}});
  assert.equal(messages.at(-1).type, "RESULT");
  assert.equal(messages.at(-1).requestId, 9);
  assert.equal(messages.at(-1).result.output, "Maakye, Ghana!\n");
});
