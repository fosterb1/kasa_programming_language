/* Isolate the Pyodide runtime and Kasa execution away from the UI thread. */
const PYODIDE_VERSION = "314.0.8";
// Browser networks sometimes block a CDN. Keep the JavaScript and its
// WebAssembly assets on the same provider to avoid mixed-version downloads.
const PYODIDE_SOURCES = Object.freeze([
  { name: "jsDelivr", indexURL: "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_VERSION + "/full/" },
  { name: "UNPKG", indexURL: "https://unpkg.com/pyodide@" + PYODIDE_VERSION + "/" },
  { name: "jsDelivr npm", indexURL: "https://cdn.jsdelivr.net/npm/pyodide@" + PYODIDE_VERSION + "/" },
]);
let runtime;
let ready = false;

function post(type, data = {}) {
  self.postMessage({ type, ...data });
}

async function loadPythonEngine() {
  const failures = [];
  for (const { name, indexURL } of PYODIDE_SOURCES) {
    post("LOADING", { message: "Connecting to Python engine via " + name + "…" });
    try {
      importScripts(indexURL + "pyodide.js");
      if (typeof loadPyodide !== "function") {
        throw new Error("The Python engine script did not initialize");
      }
      const engine = await loadPyodide({ indexURL });
      post("LOADING", { message: "Python engine loaded via " + name + ". Preparing Kasa…" });
      return engine;
    } catch (error) {
      failures.push(name + ": " + (error instanceof Error ? error.message : String(error)));
    }
  }
  throw new Error(
    "Could not download the Python engine from any of the three CDN addresses. " +
    "Try Retry engine, disable network filtering for jsdelivr.net and unpkg.com, " +
    "or try a different browser/network. If this continues, check F12 → Network.\n\n" +
    failures.join("\n")
  );
}

async function initialize() {
  try {
    runtime = await loadPythonEngine();
    const [coreResponse, runnerResponse] = await Promise.all([
      fetch(new URL("../src/kasa/core.py", self.location.href)),
      fetch(new URL("./runner.py", self.location.href)),
    ]);
    if (!coreResponse.ok || !runnerResponse.ok) {
      throw new Error("Could not load Kasa source files from this website. Redeploy the complete playground ZIP.");
    }
    const [core, bridge] = await Promise.all([coreResponse.text(), runnerResponse.text()]);
    runtime.FS.mkdirTree("/kasa_runtime/kasa");
    runtime.FS.writeFile("/kasa_runtime/kasa/__init__.py", "");
    runtime.FS.writeFile("/kasa_runtime/kasa/core.py", core);
    runtime.FS.writeFile("/kasa_runtime/runner.py", bridge);
    runtime.runPython("import sys\nsys.path.insert(0, '/kasa_runtime')\nfrom runner import execute_kasa");
    ready = true;
    post("READY");
  } catch (error) {
    post("BOOT_ERROR", { message: error instanceof Error ? error.message : String(error) });
  }
}

self.onmessage = ({ data }) => {
  if (!ready || data?.type !== "EXECUTE") return;
  const { source, input, mode, requestId } = data;
  try {
    runtime.globals.set("_kasa_source", source);
    runtime.globals.set("_kasa_input", input);
    runtime.globals.set("_kasa_mode", mode);
    const serialized = runtime.runPython(
      "import json\njson.dumps(execute_kasa(_kasa_source, _kasa_input, _kasa_mode), ensure_ascii=False)"
    );
    post("RESULT", { requestId, result: JSON.parse(serialized) });
  } catch (error) {
    post("EXECUTION_ERROR", { requestId, message: error instanceof Error ? error.message : String(error) });
  } finally {
    runtime.globals.delete("_kasa_source");
    runtime.globals.delete("_kasa_input");
    runtime.globals.delete("_kasa_mode");
  }
};

initialize();
