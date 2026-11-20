/* Browser editor control integration using a lightweight DOM/Worker simulation.
 * The Node VM cannot prove rendering in a real browser, but verifies actual
 * app.js event handlers, example selection and worker request payloads.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class Element {
  constructor(id = "") {
    this.id = id;
    this.value = "";
    this.textContent = "";
    this.checked = false;
    this.disabled = false;
    this.hidden = false;
    this.dataset = {};
    this.listeners = Object.create(null);
  }
  addEventListener(kind, handler) { this.listeners[kind] = handler; }
  dispatch(kind) {
    assert.ok(this.listeners[kind], "Missing listener " + kind + " on " + this.id);
    this.listeners[kind]({ preventDefault() {}, target: this });
  }
  querySelector() { return this.nativeOption || (this.nativeOption = new Element("native-option")); }
  querySelectorAll() { return []; }
  replaceChildren() {}
  append() {}
  focus() {}
  getAttribute() { return ""; }
}
const elements = new Map();
const element = id => {
  if (!elements.has(id)) elements.set(id, new Element(id));
  return elements.get(id);
};
const posted = [];
const workers = [];
class FakeWorker {
  constructor() { workers.push(this); }
  postMessage(value) { posted.push(value); }
  terminate() {}
}
const context = vm.createContext({
  document: {
    getElementById: element,
    querySelectorAll: () => [],
  },
  window: { addEventListener() {} },
  navigator: {},
  location: { protocol: "file:" },
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  Worker: FakeWorker,
  TextEncoder,
  console,
  setTimeout: () => 1,
  clearTimeout() {},
});
vm.runInContext(
  fs.readFileSync(path.join(__dirname, "../playground/app.js"), "utf8"),
  context,
  { filename: "app.js" }
);
const worker = workers[0];
assert.ok(worker, "App must create a worker");
worker.onmessage({ data: { type: "READY" } });

const example = element("example");
const optIn = element("experimental-modules");
const engine = element("engine");
const run = () => {
  element("run").dispatch("click");
  return posted[posted.length - 1];
};
example.value = "moduleMarket";
example.dispatch("change");
assert.equal(optIn.checked, true);
assert.match(element("source").value, /fa math: m/);
assert.match(element("source").value, /kasa_sum/);
assert.equal(run().experimentalModules, true);
assert.equal(run().engine, "javascript");

// Return the worker to ready before the next command.
worker.onmessage({
  data: { type: "RESULT", requestId: posted[0].requestId, engine: "javascript",
    result: {ok: true, output: "60\nnokware\n", error: "", steps: 20} }
});
assert.equal(element("output").textContent, "60\nnokware\n");
example.value = "hello";
example.dispatch("change");
assert.equal(optIn.checked, false);
engine.value = "auto";
assert.equal(run().experimentalModules, false);
assert.equal(run().engine, "auto");

worker.onmessage({
  data: { type: "RESULT", requestId: posted[1].requestId, engine: "javascript",
    result: {ok: true, output: "Maakye, Ghana!\n", error: "", steps: 4} }
});
optIn.checked = true;
optIn.dispatch("change");
engine.value = "native";
optIn.dispatch("change");
assert.equal(engine.value, "javascript");
assert.equal(run().experimentalModules, true);
assert.equal(run().engine, "javascript");
process.stdout.write("3 browser editor module-toggle integration scenarios passed\n");
