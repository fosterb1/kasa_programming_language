# RFC 0002 — Kasa Native WebAssembly Runtime (Draft)

**Status:** Integration prototype. **Scope:** Browser-hosted native Kasa execution while preserving the JavaScript interpreter. **Dependency:** Emscripten toolchain.

## Architecture

```text
.kasa source → Playground (HTML/JS)
            → Dedicated Web Worker
               ├── JS Kasa interpreter (always available)
               └── C++ Kasa compiler → bytecode → C++ VM (Emscripten WASM, when packaged)
            → plain-text output
```

## Interface

- The worker implements the existing `EXECUTE` / `RESULT` / `READY` protocol and adds `NATIVE_LOADING`, `NATIVE_READY`, `NATIVE_ERROR`.
- The native bridge exposes `kasa_run` and `kasa_free` with stable C linkage; results are UTF-8 JSON.
- The package builder verifies that **both** generated WASM/glue files are present before enabling the WASM path in the deployed worker.
- Auto mode falls back to JS on a native loading/runtime failure; an explicit Native choice produces an error if the native engine isn't ready.

## Non-goals

- A persistent server-side execution service, native machine-code compilation, self-hosted Kasa compiler, or a portable `.kbc` bytecode serialization format.
- Renaming the language version to a production v1.0 release.

## Work remaining

- Run Emscripten build and verify an actual `.wasm` artifact in a browser.
- Add shared conformance cases for native/browser edge differences and align resource limits.
- Verify browser engine selection and timeout behavior on Netlify and on mobile browsers.
- Implement release artifact signing/versioning, a verified Emscripten CI runner, and a memory safety review.
