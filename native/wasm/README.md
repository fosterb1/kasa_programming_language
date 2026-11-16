# Kasa Native WebAssembly — compiler/VM inside the Playground

This integration compiles the actual C++20 Kasa **lexer + parser + bytecode compiler + virtual machine** for the browser, using Emscripten. It is not a rewrite of Kasa in JavaScript and does not use Python or Pyodide. The previously working JavaScript interpreter remains available as a reliable fallback.

## Status

The C++ WebAssembly **source bridge and build/deployment pipeline exist**, and the bridge was tested with native GCC and Clang. A real `.wasm` binary **must be built with Emscripten** before native WebAssembly can run in the browser; this repository intentionally does not contain an untested precompiled `.wasm`. Without one, the website runs with its JavaScript interpreter. An Emscripten build and browser runtime verification are still required to claim end-to-end native execution.

## Build (Linux / macOS / WSL)

1. Install and activate [Emscripten SDK](https://emscripten.org/docs/getting_started/downloads.html). The official workflow is `./emsdk install latest`, `./emsdk activate latest`, followed by `source ./emsdk_env.sh`.
2. From the Kasa repository root, run:

   ```bash
   bash native/wasm/build.sh
   python playground/build_site.py --require-wasm
   ```

3. This produces:

   ```text
   playground/native/kasa-native.js        # Emscripten JavaScript glue
   playground/native/kasa-native.wasm      # Native C++ compiler and VM
   dist/Kasa_Playground_Web.zip            # Deployable website, including WASM
   ```

4. Extract the ZIP and upload its **contents folder** to your existing Netlify project's Deploys page. Confirm that Netlify serves `.wasm` as `application/wasm` (standard for static hosts). Refresh the page and check the engine selector: **Native WebAssembly** should become enabled after loading.

   If the WASM engine fails to initialize, Kasa continues in JavaScript automatically. A deployment without both native artifacts cannot accidentally claim WASM support: `build_site.py --require-wasm` refuses to create the ZIP.

## Build from Google Colab (without installing Emscripten locally)

In a Colab notebook using a Linux runtime, run these cells in order:

```python
!git clone https://github.com/fosterb1/kasa_programming_language.git
%cd /content/kasa_programming_language
!git clone https://github.com/emscripten-core/emsdk.git /content/emsdk
!/content/emsdk/emsdk install latest
!/content/emsdk/emsdk activate latest
!bash -c 'source /content/emsdk/emsdk_env.sh && bash native/wasm/build.sh'
!python playground/build_site.py --require-wasm
from google.colab import files
files.download('dist/Kasa_Playground_Web.zip')
```

The Colab runtime needs internet access to download Emscripten and enough memory to compile C++20. If a newer emsdk changes tool flags, pin a known version after validation.

## Runtime protocol

The Emscripten module exports a narrow C ABI:

```c
char* kasa_run(const char* source_utf8, const char* input_utf8, int check_only);
void kasa_free(char* result);
```

`kasa_run()` returns a freshly allocated UTF-8 JSON string containing `ok`, `output`, `error`, `mode`, `steps`, and `engine`. The browser worker parses this JSON and calls `kasa_free()` in `finally`. `check_only=1` parses/compiles without execution. All source is treated as Kasa, not JavaScript or Python.

The worker immediately initializes the JavaScript fallback. If WASM artifacts were included in the ZIP, it also starts the native module asynchronously. **Auto** prefers native when loaded and falls back to JavaScript otherwise. Explicit **Native WebAssembly** requires a loaded native module; it does not silently switch to JS. The UI displays the engine that actually ran.

## Compatibility caveats

Native Kasa is an **alpha** compiler, not a hardened sandbox. The existing JavaScript interpreter differs in some numeric semantics (native uses signed 64-bit integers), float formatting, resource budgets, and edge-case diagnostics. The worker retains its 5-second execution watchdog for both engines. WASM runs in a separate browser worker, not a secure operating-system sandbox.

## Checks

```bash
# Check C ABI bridge even without Emscripten
c++ -std=c++20 -O1 -I native/include native/src/{lexer,parser,compiler,vm}.cpp \
  native/wasm/{bridge,bridge_smoke}.cpp -o /tmp/kasa-wasm-bridge-smoke
/tmp/kasa-wasm-bridge-smoke

# JavaScript protocol and packaging checks
node --test tests/test_kasa_wasm.cjs
python -m pytest tests/test_playground.py -q

# Emscripten + browser smoke check, when compiled artifacts exist
bash native/wasm/build.sh
python playground/build_site.py --require-wasm
```
