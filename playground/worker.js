/* Isolate the Pyodide runtime and Kasa execution away from the UI thread. */
const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v314.0.8/full/pyodide.js";
let runtime;
let ready = false;

function post(type, data = {}) {
  self.postMessage({ type, ...data });
}

async function initialize() {
  try {
    importScripts(PYODIDE_CDN);
    runtime = await loadPyodide();
    const [coreResponse, runnerResponse] = await Promise.all([
      fetch(new URL("../src/kasa/core.py", self.location.href)),
      fetch(new URL("./runner.py", self.location.href)),
    ]);
    if (!coreResponse.ok || !runnerResponse.ok) {
      throw new Error("Could not load interpreter files. Serve the entire repository from its root.");
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
