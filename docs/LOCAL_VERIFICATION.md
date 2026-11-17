# Kasa local verification and CI triage

**Last checked:** November 17, 2026.  
**Scope:** Language-source changes; Python reference, browser JavaScript, native C++20 and optional WebAssembly.

## Known GitHub Actions blocker

On the `main` branch, the following workflow runs reported **failure** within approximately 3–4 seconds of creation:

- [Python/Node tests run 44063481891](https://github.com/fosterb1/kasa_programming_language/actions/runs/44063481891)
- [Native compiler run 44063481797](https://github.com/fosterb1/kasa_programming_language/actions/runs/44063481797)
- [WebAssembly build run 44063481814](https://github.com/fosterb1/kasa_programming_language/actions/runs/44063481814)

The accessible GitHub Actions API returned no executed job steps for the affected jobs. **This does not establish that a code test failed.** The underlying reason has not been identified, and the issue should remain open until a real runner log or configuration finding explains it.

**Investigate in this order:**
1. Open one failed run in GitHub's Actions UI. Check its top-level error annotation and runner assignment, not only the red status.
2. Inspect repository **Settings → Actions → General** for workflow/runner restrictions and permissions.
3. Check the GitHub account or organization Actions usage, payment/limits and runner availability as applicable.
4. Check [GitHub Status](https://www.githubstatus.com/) for an incident corresponding to the run time.
5. Run the commands below on a local development machine and retain the actual stdout/stderr. Do not infer the code is green from a pre-run Actions failure.

Do **not** disable security checks or turn on untrusted workflows merely to force a green status.

## Run the Python and browser test suites

From the repository root, with Python 3.11+, Node.js 22+, Git and appropriate platform build tools installed:

```sh
python -m pip install -e ".[dev]"
python -m pytest -q
node --check playground/kasa-runtime.js
node --check playground/worker.js
node --test tests/test_kasa_browser.cjs
```

If dependencies cannot be installed, record that as an environment/setup failure rather than a passing or failing test.

## Native compiler and conformance (Linux/macOS)

```sh
cmake -S native -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel 2
python native/tests/conformance.py build/kasa-native
build/kasa-native check examples/hello.kasa
build/kasa-native run examples/hello.kasa
```

For Windows with Visual Studio generators, use the built executable path `build/Release/kasa-native.exe` when invoking the conformance harness.

## Native WebAssembly

A source-level bridge is not a verified browser build. On a machine with a configured Emscripten SDK:

```sh
bash native/wasm/build.sh
python playground/build_site.py --require-wasm
node --test tests/test_kasa_wasm.cjs
```

Finally test the generated WebAssembly bundle in a **real browser** and confirm the native engine is actually selected.

## Cross-runtime acceptance

- `tests/conformance_remainder.json`: signed integer remainder parity.
- `tests/conformance_source_locations.json`: line/column diagnostics with `ɛ`, `ɔ`, supplementary characters and EOF.
- `docs/RFC-0003-remainder-semantics.md`: normative remainder rule.
- `docs/RFC-0004-unicode-source-locations.md`: proposed Unicode code-point source coordinates.

When a check fails, record **engine, OS, compiler/interpreter version, command, source fixture, expected, actual, full error, and relevant commit SHA**. Do not overwrite expected results merely to satisfy one engine.

## Release gate

No stable release claims until all supported runtime tests pass, a real WebAssembly/browser check is completed when WASM is advertised, language sources are reviewed, and the project owner chooses a valid license. The linguistic-research policy applies to any future Twi keyword; this milestone deliberately adds none.
