"use strict";

const EXAMPLES = Object.freeze({
  hello: 'ka "Maakye, Ghana!"\n',
  conditions: 'ma edin = "Ama"\nma mfe = 12\n\nsɛ mfe >= 10 a\n    ka "Maakye, " + edin\nanyɛ_saa_a\n    ka "Kɔ so sua!"\nawiei\n',
  loops: 'ma n = 1\nbere_a n <= 3\n    ka n\n    ma n = n + 1\nawiei\n\nmpɛn 2\n    ka "Meda wo ase"\nawiei\n',
  functions: 'dwumadie fa_bi(a, b)\n    sanma a + b\nawiei\n\nka fa_bi(4, 6)\n',
  lists: 'ma aba = [10, 20, 30]\nma aba[1] = 99\nka aba[1]\nka tentɛn(aba)\n',
  input: '# Add a name to the Program Input box\nka "Wo din de sɛn?"\nma edin = bisa()\nka "Akwaaba, " + edin\n',
  market: 'ma books = 3\nma price = 12\nma pens = 2\nma pen_price = 5\nka "Total GHS: " + nsɛm(books * price + pens * pen_price)\n',
  grades: 'ma maths = 65\nma english = 70\nma science = 75\nma average = (maths + english + science) / 3\nka average\nsɛ average >= 50 a\n    ka "Pass"\nanyɛ_saa_a\n    ka "Review"\nawiei\n',
  stock: 'ma opening = 50\nma sold = 43\nma remaining = opening - sold\nka remaining\nsɛ remaining <= 10 a\n    ka "Reorder"\nawiei\n',
  savings: 'ma total = 0\nmpɛn 6\n    ma total = total + 80\nawiei\nka "Saved GHS: " + nsɛm(total)\n',
  fare: 'dwumadie fare(passengers, price)\n    sanma passengers * price\nawiei\nka "Fare GHS: " + nsɛm(fare(5, 7))\n',
});

const EXAMPLE_GUIDES = Object.freeze({
  hello: "Start with one printed greeting. Change the message between quotation marks.",
  conditions: "A decision depends on a Boolean comparison. Try changing the age across the threshold.",
  loops: "Trace the counter before and after every repetition. A changing condition prevents endless loops.",
  functions: "A function returns a value that can be reused. Try changing the two inputs.",
  lists: "List positions start at zero. Try changing the second element.",
  input: "The bisa() function reads a line from Program Input. Add your name below the editor.",
  market: "Market receipt: 3 books at GHS 12 and 2 pens at GHS 5 should total GHS 46.",
  grades: "School marks: compute the average and test a declared passing threshold of 50.",
  stock: "Inventory: subtract sales from opening stock, then print a reorder warning at 10 or fewer.",
  savings: "Savings club: six contributions of GHS 80 add to GHS 480, excluding fees and withdrawals.",
  fare: "Trotro fares: write a reusable function to calculate the total for 5 passengers.",
});

function explainError(error) {
  if (/unknown name|undefined|not defined/i.test(error)) return "Check variable spelling and declare names with ma before using them.";
  if (/zero.?division|division by zero/i.test(error)) return "A denominator cannot be zero. Check your arithmetic inputs.";
  if (/syntax|unexpected|expected/i.test(error)) return "Review punctuation, the sɛ ... a header and matching awiei endings.";
  if (/index|out of range/i.test(error)) return "Remember: the first list index is 0, and the final index is one less than the length.";
  return "Read the error's line and column, change one instruction, then try again.";
}

const $ = (id) => document.getElementById(id);
const source = $("source");
const input = $("input");
const output = $("output");
const status = $("status");
const runButton = $("run");
const checkButton = $("check");
const exampleSelect = $("example");
const exampleExplanation = $("example-explanation");
const debugGuidance = $("debug-guidance");
const structuredDiagnostic = $("kasa-diagnostic");
function showStructuredDiagnostic(error) {
  structuredDiagnostic.replaceChildren();
  const diagnostic = globalThis.KasaDiagnostics?.diagnose(source.value, error);
  if (!diagnostic) { structuredDiagnostic.hidden = true; return; }
  structuredDiagnostic.hidden = false;
  const heading = document.createElement("h3");
  heading.textContent = diagnostic.title + " · " + diagnostic.code;
  structuredDiagnostic.append(heading);
  if (diagnostic.line != null) {
    const location = document.createElement("p");
    location.className = "diagnostic-location";
    location.textContent = "Line " + diagnostic.line + ", column " + diagnostic.column + " · " + diagnostic.category;
    structuredDiagnostic.append(location);
  }
  if (diagnostic.excerpt) {
    const excerpt = document.createElement("pre");
    excerpt.className = "diagnostic-excerpt";
    excerpt.textContent = diagnostic.excerpt;
    structuredDiagnostic.append(excerpt);
  }
  const explanation = document.createElement("p");
  explanation.textContent = diagnostic.explanation;
  structuredDiagnostic.append(explanation);
  if (diagnostic.suggestion) {
    const suggestion = document.createElement("p");
    suggestion.className = "diagnostic-suggestion";
    suggestion.textContent = "Try this: " + diagnostic.suggestion;
    structuredDiagnostic.append(suggestion);
  }
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "Original Kasa engine message";
  const raw = document.createElement("pre");
  raw.textContent = diagnostic.raw;
  details.append(summary, raw);
  structuredDiagnostic.append(details);
}

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
exampleExplanation.textContent = EXAMPLE_GUIDES.hello;
source.addEventListener("input", saveDraft);

// Character bar inserts literal Unicode into the current selection; never
// rewrites ASCII code or changes the grammar.
document.querySelectorAll(".character-key[data-insert]").forEach(button => {
  button.addEventListener("mousedown", event => event.preventDefault());
  button.addEventListener("click", () => {
    const token = button.getAttribute("data-insert") || "";
    if (!token) return;
    const start = source.selectionStart;
    const end = source.selectionEnd;
    source.setRangeText(token, start, end, "end");
    source.focus();
    saveDraft();
  });
});


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
        showStructuredDiagnostic(data.message || "");
        debugGuidance.textContent = explainError(data.message || "");
        debugGuidance.hidden = false;
        setStatus("Unexpected interpreter error", "error");
        return;
      }
      const result = data.result;
      if (!result.ok) {
        showStructuredDiagnostic(result.error || "");
        debugGuidance.textContent = explainError(result.error || "");
        debugGuidance.hidden = false;
      } else {
        debugGuidance.hidden = true;
        structuredDiagnostic.hidden = true;
      }
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
  structuredDiagnostic.hidden = true;
  setStatus(mode === "check" ? "Checking syntax…" : "Running program…", "pending");
  output.textContent = "";
  debugGuidance.hidden = true;
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
  exampleExplanation.textContent = EXAMPLE_GUIDES[exampleSelect.value] || EXAMPLE_GUIDES.hello;
  debugGuidance.hidden = true;
  saveDraft();
});
$("reset").addEventListener("click", () => {
  source.value = EXAMPLES.hello;
  input.value = "";
  exampleSelect.value = "hello";
  exampleExplanation.textContent = EXAMPLE_GUIDES.hello;
  debugGuidance.hidden = true;
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
