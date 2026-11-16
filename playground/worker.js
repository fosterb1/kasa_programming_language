/* Offline-first Kasa interpreter worker. No remote JavaScript or Python engine.
 * Kasa source runs in the isolated browser worker via the built-in JS interpreter.
 */
"use strict";
try {
  importScripts("./kasa-runtime.js");
  if (!self.KasaRuntime || typeof self.KasaRuntime.executeKasa !== "function") {
    throw new Error("The Kasa interpreter was not initialized.");
  }
  self.postMessage({ type: "READY" });
} catch (error) {
  self.postMessage({ type: "BOOT_ERROR", message: String(error?.message || error) });
}
self.onmessage = ({ data }) => {
  if (data?.type !== "EXECUTE" || !self.KasaRuntime) return;
  const { source, input, mode, requestId } = data;
  try {
    const result = self.KasaRuntime.executeKasa(source, input, mode);
    self.postMessage({ type: "RESULT", requestId, result });
  } catch (error) {
    self.postMessage({ type: "EXECUTION_ERROR", requestId, message: String(error?.message || error) });
  }
};
