# Kasa Playground — JavaScript + native WebAssembly integration

Kasa now supports **two execution paths in the browser**:

- **JavaScript:** Existing self-contained, tested browser interpreter. Always present, no external dependencies.
- **Native WebAssembly:** Kasa's independent C++20 bytecode compiler and VM compiled with Emscripten. Available **only after** WASM artifacts are built and packaged. The repository does not include a verified precompiled `.wasm` binary.

Python CLI and native desktop compiler remain separate and unaffected.

## Deploy to your existing Netlify project

From the repo root:

```bash
# Only packages JavaScript when no native build exists
python playground/build_site.py

# To include the real C++ WASM compiler, install Emscripten first:
bash native/wasm/build.sh
python playground/build_site.py --require-wasm
```

Extract `dist/Kasa_Playground_Web.zip` and drag the containing website folder onto **your existing project's Deploys page**. Do not create a new Netlify project. Hard-refresh the URL once Netlify reports Published.

**Important:** If the new bundle contains only JavaScript, your site will still work but the native option will be disabled. The UI never claims to run WASM until a successfully initialized native module is present. See [the native WASM instructions](../native/wasm/README.md), including a Google Colab build path.

## Features and behavior

- Twi-first editing; six examples; run and check; `bisa()` input; `.kasa` downloads
- Engine selector: Auto / JavaScript / Native WebAssembly
- Auto prefers native once ready, otherwise JavaScript. An unavailable WASM engine does not break the editor.
- Source code stays in your browser; both engines are local, and no CDN/Pyodide is used.
- Execution uses a Web Worker. The UI terminates a run after five seconds; the interpreters also impose resource ceilings.
- **No guarantee of identical behavior yet:** native signed 64-bit integers and some decimal formatting differ from the JavaScript and Python implementations.

The shipped JavaScript interpreter handles all its previously supported language features. Browser-to-WASM end-to-end tests require an actual Emscripten build and have not been verified in environments lacking Emscripten.

## Offline installation (development build)

The new static bundle includes a web app manifest, icons and a versioned service worker. After loading on HTTPS (such as Netlify), users can use their browser's **Install App** option where supported. On a successfully cached installation, the JavaScript execution engine and site shell can load without an active internet connection. Native WASM files are cached if fetched through the installed service worker. Not all browsers install PWAs the same way.

The service worker uses a hash of deployment assets to replace stale caches after redeployment. The install experience and offline behavior **still require a live browser smoke test**; a headless browser navigation attempt in the authoring environment was blocked by administrator policy.
