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
let worker = null;
let ready = false;
let active = null;
let timeoutId = null;
let startupTimeout = null;
let sequence = 0;

source.value = EXAMPLES.hello;

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
  setReady(false);
  if (worker) worker.terminate();
  worker = null;
}

function prepareWorker() {
  stopWorker();
  setStatus("Loading Python engine…", "pending");
  worker = new Worker("./worker.js?v=0.1.1");
  worker.onmessage = ({ data }) => {
    if (data.type === "LOADING") {
      setStatus(data.message, "pending");
      return;
    }
    if (data.type === "READY") {
      clearTimeout(startupTimeout);
      startupTimeout = null;
      setReady(true);
      output.textContent = "Ready! Press Run code to execute your Kasa program.";
      setStatus("Kasa is ready", "ready");
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
      setStatus(result.ok ? (mode === "check" ? "Syntax is valid" : "Run completed") : "Kasa reported an error", result.ok ? "ready" : "error");
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
    output.textContent = "The browser could not load the Python runtime. Check your internet connection and reload this page.";
    setStatus("Interpreter startup timed out", "error");
  }, 120_000);
}

function execute(mode) {
  if (!worker || !ready || active) return;
  const requestId = ++sequence;
  active = { requestId, mode };
  setReady(false);
  setStatus(mode === "check" ? "Checking syntax…" : "Running program…", "pending");
  output.textContent = "";
  worker.postMessage({ type: "EXECUTE", source: source.value, input: input.value, mode, requestId });
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
exampleSelect.addEventListener("change", () => { source.value = EXAMPLES[exampleSelect.value] || EXAMPLES.hello; });
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
