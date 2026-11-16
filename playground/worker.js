/* Browser worker for Kasa. The JavaScript interpreter starts immediately.
 * The bundled native WebAssembly engine is loaded opportunistically, ONLY
 * when a complete, verified WASM deployment archive was built.
 */
"use strict";

// Rewritten to true ONLY inside the deployable ZIP when .js + .wasm exist.
const KASA_HAS_WASM = false;
let nativeModule = null;
let nativeError = "";
let jsReady = false;

function notify(type, extra = {}) {
  self.postMessage({ type, ...extra });
}

try {
  importScripts("./kasa-runtime.js");
  if (!self.KasaRuntime || typeof self.KasaRuntime.executeKasa !== "function") {
    throw new Error("Kasa JavaScript interpreter did not initialize");
  }
  jsReady = true;
  notify("READY", { engine: "javascript", nativeAvailable: false });
} catch (error) {
  notify("BOOT_ERROR", { message: String(error?.message || error) });
}

async function prepareNative() {
  if (!jsReady || !KASA_HAS_WASM) return;
  try {
    notify("NATIVE_LOADING");
    importScripts("./native/kasa-native.js");
    if (typeof createKasaModule !== "function") throw new Error("Native compiler JavaScript glue missing");
    const module = await createKasaModule({
      locateFile: file => new URL("./native/" + file, self.location.href).href,
    });
    if (typeof module.ccall !== "function" || typeof module.UTF8ToString !== "function") {
      throw new Error("Native compiler WebAssembly exports are missing");
    }
    nativeModule = module;
    notify("NATIVE_READY");
  } catch (error) {
    nativeError = String(error?.message || error);
    notify("NATIVE_ERROR", { message: nativeError });
  }
}

function executeNative(source, input, mode) {
  const pointer = nativeModule.ccall("kasa_run", "number", ["string", "string", "number"],
    [source, input, mode === "check" ? 1 : 0]);
  if (!pointer) throw new Error("Native runtime could not allocate a result");
  let data;
  try {
    data = nativeModule.UTF8ToString(pointer);
  } finally {
    nativeModule.ccall("kasa_free", null, ["number"], [pointer]);
  }
  const result = JSON.parse(data);
  if (!result || typeof result.ok !== "boolean" || typeof result.output !== "string" || typeof result.error !== "string") {
    throw new Error("Native runtime returned an invalid result");
  }
  return result;
}

self.onmessage = ({ data }) => {
  if (data?.type !== "EXECUTE" || !jsReady) return;
  const { source, input, mode, requestId, engine = "auto" } = data;
  let used = "javascript";
  try {
    if (engine === "native" && !nativeModule) {
      notify("RESULT", { requestId, engine: "javascript", result: {
        ok: false, output: "", error: "Native WebAssembly is unavailable in this deployment. " +
          (nativeError || "Build and upload the WASM-enabled website bundle."), steps: 0, mode,
      } });
      return;
    }
    let result;
    if ((engine === "auto" || engine === "native") && nativeModule) {
      try {
        result = executeNative(source, input, mode);
        used = "native-wasm";
      } catch (error) {
        if (engine === "native") throw error;
        nativeError = String(error?.message || error);
        nativeModule = null;
        notify("NATIVE_ERROR", { message: nativeError });
      }
    }
    if (!result) result = self.KasaRuntime.executeKasa(source, input, mode);
    notify("RESULT", { requestId, engine: used, result });
  } catch (error) {
    notify("EXECUTION_ERROR", { requestId, message: String(error?.message || error) });
  }
};

void prepareNative();
