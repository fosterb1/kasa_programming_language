"use strict";

const EXAMPLES = Object.freeze({
  hello: 'ka "Maakye, Ghana!"\n',
  conditions: 'ma edin = "Ama"\nma mfe = 12\n\nsɛ mfe >= 10 a\n    ka "Maakye, " + edin\nanyɛ_saa_a\n    ka "Kɔ so sua!"\nawiei\n',
  loops: 'ma n = 1\nbere_a n <= 3\n    ka n\n    ma n = n + 1\nawiei\n\nmpɛn 2\n    ka "Meda wo ase"\nawiei\n',
  functions: 'dwumadie fa_bi(a, b)\n    sanma a + b\nawiei\n\nka fa_bi(4, 6)\n',
  lists: 'ma aba = [10, 20, 30]\nma aba[1] = 99\nka aba[1]\nka tentɛn(aba)\n',
  input: '# Add a name to the Program Input box\nka "Wo din de sɛn?"\nma edin = bisa()\nka "Akwaaba, " + edin\n',
});

const $ = (id) => document.getElementById(id);
const source = $("source");
const input = $("input");
const output = $("output");
const status = $("status");
const runButton = $("run");
const checkButton = $("check");
const exampleSelect = $("example");
const retryButton = $("retry");
const engineSelect = $("engine");
const nativeOption = engineSelect.querySelector('option[value="native"]');
let worker = null;
let ready = false;
let active = null;
let timeoutId = null;
let startupTimeout = null;
let sequence = 0;
let nativeAvailable = false;

// Keep only source code in local storage. Never persist program input.
const DRAFT_KEY = "kasa.playground.source.v1";
const MAX_SOURCE_BYTES = 50_000;
function saveDraft() {
  try { localStorage.setItem(DRAFT_KEY, source.value); }
  catch (_) { /* Private browsing or storage disabled: editor still works. */ }
}
function restoreDraft() {
  try {
    const saved = localStorage.getItem(DRAFT_KEY);
    if (saved !== null && new TextEncoder().encode(saved).length <= MAX_SOURCE_BYTES) return saved;
  } catch (_) { /* Local storage unavailable. */ }
  return EXAMPLES.hello;
}
source.value = restoreDraft();
source.addEventListener("input", saveDraft);

function setStatus(label, state = "pending") {
  status.textContent = label;
  status.dataset.state = state;
}

function setReady(enabled) {
  ready = enabled;
  runButton.disabled = !enabled;
  checkButton.disabled = !enabled;
}

function stopWorker() {
  if (timeoutId) clearTimeout(timeoutId);
  if (startupTimeout) clearTimeout(startupTimeout);
  timeoutId = null;
  startupTimeout = null;
  active = null;
  nativeAvailable = false;
  nativeOption.disabled = true;
  if (engineSelect.value === "native") engineSelect.value = "auto";
  setReady(false);
  if (worker) worker.terminate();
  worker = null;
}

function prepareWorker() {
  stopWorker();
  setStatus("Loading Kasa browser interpreter…", "pending");
  worker = new Worker("./worker.js?v=0.4.0");
  worker.onmessage = ({ data }) => {
    if (data.type === "NATIVE_LOADING") {
      if (!active) setStatus("Kasa ready · Native engine loading…", "ready");
      return;
    }
    if (data.type === "NATIVE_READY") {
      nativeAvailable = true;
      nativeOption.disabled = false;
      if (!active) setStatus("Kasa ready · Native WebAssembly available", "ready");
      return;
    }
    if (data.type === "NATIVE_ERROR") {
      nativeAvailable = false;
      nativeOption.disabled = true;
      if (engineSelect.value === "native") engineSelect.value = "auto";
      if (!active) setStatus("Kasa ready · JavaScript fallback", "ready");
      return;
    }
    if (data.type === "LOADING") {
      setStatus(data.message, "pending");
      return;
    }
    if (data.type === "READY") {
      clearTimeout(startupTimeout);
      startupTimeout = null;
      setReady(true);
      output.textContent = "Ready! Press Run code to execute your Kasa program.";
      setStatus("Kasa ready · JavaScript interpreter", "ready");
      return;
    }
    if (data.type === "BOOT_ERROR") {
      stopWorker();
      output.textContent = data.message;
      setStatus("Interpreter could not load · Refresh to retry", "error");
      return;
    }
    if (!active || data.requestId !== active.requestId) return;
    if (data.type === "RESULT" || data.type === "EXECUTION_ERROR") {
      clearTimeout(timeoutId);
      timeoutId = null;
      const mode = active.mode;
      active = null;
      setReady(true);
      if (data.type === "EXECUTION_ERROR") {
        output.textContent = data.message;
        setStatus("Unexpected interpreter error", "error");
        return;
      }
      const result = data.result;
      output.textContent = result.output + (result.error ? `${result.output ? "\n" : ""}${result.error}` : "") || (mode === "check" ? "Syntax OK. No program code was executed." : "Program finished without output.");
      const engineLabel = data.engine === "native-wasm" ? "Native WebAssembly" : "JavaScript";
      setStatus(result.ok ? (mode === "check" ? "Syntax valid" : "Run completed") + ` · ${engineLabel}` : "Kasa reported an error", result.ok ? "ready" : "error");
    }
  };
  worker.onerror = (event) => {
    event.preventDefault();
    stopWorker();
    output.textContent = "Interpreter worker failed. Reload the page and try again.";
    setStatus("Interpreter unavailable", "error");
  };
  startupTimeout = setTimeout(() => {
    if (ready) return;
    stopWorker();
    output.textContent = "The local Kasa interpreter could not start. Click Retry engine or reload the page.";
    setStatus("Interpreter startup timed out", "error");
  }, 12_000);
}

function execute(mode) {
  if (!worker || !ready || active) return;
  const requestId = ++sequence;
  active = { requestId, mode };
  setReady(false);
  setStatus(mode === "check" ? "Checking syntax…" : "Running program…", "pending");
  output.textContent = "";
  worker.postMessage({ type: "EXECUTE", source: source.value, input: input.value, mode, requestId, engine: engineSelect.value });
  timeoutId = setTimeout(() => {
    stopWorker();
    output.textContent = "Your program exceeded the 5-second time limit and was stopped. The interpreter is restarting.";
    setStatus("Time limit exceeded", "error");
    prepareWorker();
  }, 5_000);
}

retryButton.addEventListener("click", prepareWorker);
runButton.addEventListener("click", () => execute("run"));
checkButton.addEventListener("click", () => execute("check"));
$("clear").addEventListener("click", () => { output.textContent = ""; });
exampleSelect.addEventListener("change", () => {
  source.value = EXAMPLES[exampleSelect.value] || EXAMPLES.hello;
  saveDraft();
});
$("reset").addEventListener("click", () => {
  source.value = EXAMPLES.hello;
  input.value = "";
  exampleSelect.value = "hello";
  output.textContent = "Draft reset. Press Run code to begin.";
  try { localStorage.removeItem(DRAFT_KEY); }
  catch (_) { /* Storage may be disabled. */ }
  source.focus();
});
$("upload").addEventListener("change", async (event) => {
  const selected = event.target.files?.[0];
  if (!selected) return;
  try {
    if (selected.size > MAX_SOURCE_BYTES) throw new Error("This .kasa file is too large (50 KB maximum).");
    const text = await selected.text();
    if (new TextEncoder().encode(text).length > MAX_SOURCE_BYTES) {
      throw new Error("This .kasa file exceeds the 50 KB source limit.");
    }
    source.value = text;
    saveDraft();
    source.focus();
    output.textContent = "Opened " + selected.name + ". Press Run code to execute it.";
  } catch (error) {
    output.textContent = String(error?.message || error);
  } finally {
    event.target.value = "";
  }
});
$("download").addEventListener("click", () => {
  const url = URL.createObjectURL(new Blob([source.value], { type: "text/plain;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "main.kasa";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 500);
});
source.addEventListener("keydown", (event) => {
  if (event.key === "Tab") {
    event.preventDefault();
    const start = source.selectionStart;
    const end = source.selectionEnd;
    source.setRangeText("    ", start, end, "end");
  } else if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    execute("run");
  }
});

prepareWorker();

// Offline installation is optional and does not block interpreter startup.
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(error => {
      console.warn('Kasa offline mode unavailable:', error);
    });
  });
}
