# G0.5 experimental integration — Studio and native validation

**Integrated:** PR #61 normal-merged into `main`, commit `2074480b2111256d3767d09d6322cde054c0c6fc` (2026-11-21).  
**Security and maturity:** Experimental **trusted-local** native module-to-KBC1 source prelinker. NOT a browser-compiled module system, stable `fa` grammar, or service for processing untrusted uploads. POSIX strict-publication tests and Windows real file-symlink security tests remain an open review gate.

## What the browser Studio actually supports

The static Netlify Playground/Academy Studio currently has a **G0.4 opt-in JavaScript module engine**. It packages the already SHA-pinned `math` and `collections` catalog and accepts provisional source imports when **Experimental modules (JavaScript only)** is checked.

**G0.5 is a Python/native build-time program** (`scripts/compile_g05_modules.py`), not wired into `playground/worker.js` or the Emscripten `kasa_run` entry point. Merging G0.5 does not automatically enable G0.5 native imports, compiler output, or KBC1 execution in the browser. Do not claim that running the JavaScript preview demonstrates G0.5 native compilation.

### Studio JavaScript module smoke (after actual site deployment is verified)

1. Open the actual production Netlify Playground URL from the project's Netlify dashboard. If embedded in the Academy, open the Academy `/playground` page and confirm it shows that same production deployment.
2. Select **Experimental modules (JavaScript only)**. Choose **JavaScript** as the engine. Do **not** choose Native WebAssembly for this scenario.
3. Paste this exact Kasa source and Run:

```kasa
fa math firi stdlib: m
fa collections firi stdlib: c
ma items = [10, 20, 30]
ka m.kasa_sum(items)
ka c.kasa_contains(items, 20)
```

**Expected stdout:**

```text
60
nokware
```

4. Uncheck experimental modules and rerun the source: verify it is **rejected**, rather than silently enabling imports in normal mode.
5. Optionally select the **Native WebAssembly** engine for a separate normal-language smoke, such as `ka "Maakye, Ghana!"`. Do **not** interpret that native smoke as a G0.5 module-import pass.

**Evidence needed:** record the live URL, Netlify deploy ID/commit and time, browser and engine, exact stdout/diagnostic, screenshot or terminal output. GitHub merge status is not proof of successful production deployment.

## G0.5 native-to-KBC1 smoke on trusted Windows workstation

From `main` after `git pull --ff-only`, with an existing compiled `build/kasa-local/Release/kasa-native.exe`:

```cmd
python scripts/verify_g05_native_kbc.py
python scripts/verify_g05_kbc_independence.py
```

These are the **real G0.5** tests: Python module execution, hygienic prelink, native execution, compiled standalone KBC1 and corruption/source-independence checks.

For a single actual G0.5 compile, choose a **new output filename** (tool refuses overwrites):

```cmd
python scripts/compile_g05_modules.py --app stdlib/demos/group0_source_import_experiment.kasa --output build/g05-compiled/studio-smoke-01.kbc
build\kasa-local\Release\kasa-native.exe check-bytecode build/g05-compiled/studio-smoke-01.kbc
build\kasa-local\Release\kasa-native.exe run-bytecode build/g05-compiled/studio-smoke-01.kbc
```

Expected bytecode output: `60` and `nokware`, each on its own line. If the output file exists already, choose another unique name and **do not delete unrelated artifacts**. Windows `--strict-publication` intentionally fails closed and must not be enabled for this example.

### Remaining gates

- Collect actual POSIX strict-publication execution evidence on a real POSIX filesystem, not skipped Windows tests.
- Review directory TOCTOU and catalog/source mutation races before offering any hosted native compilation service or shared-filesystem execution.
- Design and implement browser native module import support in a separate reviewed feature branch; first-party WASM today does **not** link modules at runtime.
- Keep Netlify build status and actual Academy iframe deployment distinct from GitHub commits.

**G0.5 source integration is complete; browser G0.5 execution and production hardening are not.**
