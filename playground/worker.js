/* Browser worker for Kasa. The JavaScript interpreter starts immediately.
 * The bundled native WebAssembly engine is loaded opportunistically, ONLY
 * when a complete, verified WASM deployment archive was built.
 */
"use strict";

// Rewritten to true ONLY inside the deployable ZIP when .js + .wasm exist.
const KASA_HAS_WASM = false;
// Patched true only in a bundle containing hash-checked local libraries.
const KASA_HAS_PINNED_MODULES = false;
// G1 remains unavailable unless a separately verified G1 bundle is packaged.
const KASA_HAS_G1_PINNED_MODULES = false;
let pinnedModules = null;
let pinnedG1Modules = null;
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

function loadPinnedModules() {
  if (!KASA_HAS_PINNED_MODULES) throw new Error("This deployment has no pinned Kasa module bundle");
  if (pinnedModules) return pinnedModules;
  importScripts("./kasa-pinned-modules.js");
  if (!self.KasaPinnedModules || !Object.hasOwn(self.KasaPinnedModules, "math") ||
      !Object.hasOwn(self.KasaPinnedModules, "collections")) {
    throw new Error("Pinned Kasa libraries are unavailable");
  }
  pinnedModules = self.KasaPinnedModules;
  return pinnedModules;
}

function loadPinnedG1Modules() {
  if (!KASA_HAS_G1_PINNED_MODULES) throw new Error("This deployment has no pinned G1 Kasa module bundle");
  if (pinnedG1Modules) return pinnedG1Modules;
  importScripts("./kasa-g1-pinned-modules.js");
  if (!self.KasaG1PinnedModules || !Object.hasOwn(self.KasaG1PinnedModules, "math") ||
      !Object.hasOwn(self.KasaG1PinnedModules, "collections")) {
    throw new Error("Pinned G1 Kasa libraries are unavailable");
  }
  pinnedG1Modules = self.KasaG1PinnedModules;
  return pinnedG1Modules;
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
  const { source, input, mode, requestId, engine = "auto", experimentalModules = false, experimentalGeneration = "g0" } = data;
  let used = "javascript";
  try {
    if (experimentalModules === true && !["g0", "g1"].includes(experimentalGeneration)) {
      notify("RESULT", { requestId, engine: "javascript", result: {
        ok: false, output: "", error: "Unknown experimental Kasa module generation.", steps: 0, mode,
      } });
      return;
    }
    if (experimentalModules === true && engine === "native") {
      notify("RESULT", { requestId, engine: "javascript", result: {
        ok: false, output: "", error: "Experimental Kasa imports require the JavaScript engine.", steps: 0, mode,
      } });
      return;
    }
    if (engine === "native" && !nativeModule) {
      notify("RESULT", { requestId, engine: "javascript", result: {
        ok: false, output: "", error: "Native WebAssembly is unavailable in this deployment. " +
          (nativeError || "Build and upload the WASM-enabled website bundle."), steps: 0, mode,
      } });
      return;
    }
    let result;
    if (!experimentalModules && (engine === "auto" || engine === "native") && nativeModule) {
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
    if (!result) {
      if (experimentalModules === true) {
        try {
          const modules = experimentalGeneration === "g1" ? loadPinnedG1Modules() : loadPinnedModules();
          result = self.KasaRuntime.executeKasa(source, input, mode, { experimentalModules: modules });
        } catch (error) {
          result = { ok: false, output: "", error: String(error?.message || error), steps: 0, mode };
        }
      } else {
        result = self.KasaRuntime.executeKasa(source, input, mode);
      }
    }
    notify("RESULT", { requestId, engine: used, result });
  } catch (error) {
    notify("EXECUTION_ERROR", { requestId, message: String(error?.message || error) });
  }
};

void prepareNative();
