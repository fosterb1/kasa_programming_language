# Genuine Emscripten WebAssembly execution in Chromium — 2026-11-18

## New evidence: actual native WASM, not a simulated module

Successfully built Kasa's existing C++ compiler/VM and browser C bridge using **Emscripten 3.1.69** on Linux with `bash native/wasm/build.sh`. Artifacts were generated at `playground/native/kasa-native.js` (Emscripten glue, approximately 25 KB) and `playground/native/kasa-native.wasm` (compiled native WASM, approximately 480 KB). `native/wasm/validate_artifacts.mjs` compiled the actual binary through the WebAssembly API and reported **491,371 bytes, 23 exports, 44 imports**. The binary is generated test/build output and is **not committed as a source file**.

Successfully built a WASM-required site bundle with `python3 playground/build_site.py --require-wasm`. Its packaged worker has `KASA_HAS_WASM=true`, and the generated site includes the real `.wasm` and Emscripten glue.

## Browser test

New `scripts/verify_real_wasm_browser.py` opens the **WASM-required distribution ZIP**, verifies the native assets and the enabled flag, extracts it into a temporary directory, serves it from a loopback HTTP server, and uses actual headless Chromium through Playwright.

Checks exercised on real browser DOM + Web Worker:

1. Native WebAssembly option changes from disabled to enabled after the module actually loads; UI reports `Native WebAssembly available`.
2. Forced **Native WebAssembly** executes Hello Ghana and the UI explicitly reports the native engine.
3. Forced native **Check syntax** reports success without executing print output.
4. Forced native `bisa()` consumes supplied input and prints `Akwaaba, Ama`.
5. Forced native division by zero displays `ZeroDivisionError`.
6. Four Twi programs (Unicode string, functions, lists, repeat) produce identical output via the **real WASM engine** and the JavaScript interpreter in Chromium.
7. Forced JavaScript execution succeeds while native module remains available, and the status correctly says JavaScript.
8. No uncaught browser page JavaScript errors in the exercised flow.

**Independent result:** `PASS genuine Chromium native Emscripten WASM: load, run, check, input, error, explicit JavaScript fallback` after the differential checks were added. Existing Node tests of fake WASM glue alone would **not** establish this milestone.

## Reproduce locally with actual WASM

Linux/macOS with Emscripten `em++`, Node.js and Python:

```sh
bash native/wasm/build.sh
python3 playground/build_site.py --require-wasm
python3 -m pip install playwright
python3 -m playwright install chromium
python3 scripts/verify_real_wasm_browser.py
```

Playwright's Chromium may require platform-specific system dependencies (`python3 -m playwright install-deps chromium` on supported Linux hosts with privileges). The test uses temporary files and loopback hosting; no public deployment is required.

## Scope and remaining gates

This establishes **real native WebAssembly execution on one headless Chromium/Linux environment**. It does not establish Firefox/WebKit/Safari/Edge support, mobile and offline PWA behavior, production hosted deployment, source-vs-WASM complete-language parity, KBC2 encoding inside WASM, or security of untrusted bytecode. The browser WASM build currently uses the restricted int64 C++ native VM; the opt-in Boost/KBC2 native feature was not compiled into this WASM binary. JavaScript fallback remains the default when no WASM artifacts are packaged or native loading fails.

For stable Kasa 1.0, expand the browser case corpus, fuzz more input boundaries, test browsers and offline service workers, audit security/licensing, and provide signed/reproducible release artifacts. Current 0.4 implementation checklist 90% and 1.0 readiness ~35% are planning estimates unchanged by this targeted verification.
