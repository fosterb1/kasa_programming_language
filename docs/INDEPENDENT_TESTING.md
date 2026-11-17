# Verify Kasa without GitHub Actions

**Status:** Independent command-line test runner for the existing Kasa codebase.
**Language changes:** None. No Twi keywords or syntax rules are added.

Kasa has separate Python, JavaScript and native C++ implementations. A green result from one runtime is not sufficient to claim that all three behave alike.

## Requirements

- Python 3.11+ and the project development dependencies, installed with `python -m pip install -e ".[dev]"`
- Node.js 22+
- CMake 3.16+ and a C++20 compiler for the native profile
- Emscripten SDK only for the optional WASM build

Run these commands **from the repository root**:

```sh
# Test the Python interpreter and Node-based browser runtime.
python scripts/verify_local.py --profile quick

# Include a fresh CMake compile and native-vs-Python conformance.
python scripts/verify_local.py --profile full

# Inspect the exact commands without running tests:
python scripts/verify_local.py --profile full --dry-run
```

The report defaults to `build/kasa-local-verification.json`. Choose another path with `--report path/to/report.json`.

### Optional WebAssembly build

```sh
python scripts/verify_local.py --profile full --wasm
```

This **requires the Emscripten toolchain** and confirms the WASM source builds and bundles. It **does not** replace end-to-end testing inside Chrome, Firefox, or another real browser.

## What gets tested

| Check | Quick | Full |
|---|:---:|:---:|
| Python pytest (all available tests) | Yes | Yes |
| Python CLI run/check smoke tests | Yes | Yes |
| JavaScript runtime, worker and playground syntax | Yes | Yes |
| Node interpreter and WASM protocol tests | Yes | Yes |
| Native CMake configuration | No | Yes |
| Native C++20 compiler and VM build | No | Yes |
| Standalone native Unicode lexer CTest | No | Yes |
| Native/Python conformance harness | No | Yes |
| Emscripten native WASM and site bundle | No | Optional |

The script runs subprocesses without a shell, captures the final portion of stdout/stderr, records exit codes and durations, and returns **nonzero** if any required step fails. Missing executables are failures, not skipped passes. An unsuccessful native configuration/build marks every downstream dependent check explicitly as **not_run**, including the reason it was blocked; the complete planned check list is preserved in the report.

**A dry run reports `not_run` for every step and never claims the tests passed.** Do not compare a dry-run exit code to a completed test run.

## Interpreting results

```json
{
  "profile": "full",
  "dry_run": false,
  "counts": {
    "passed": 10,
    "failed": 0,
    "not_run": 0
  }
}
```

This is an **example report fragment**, not an actual recorded verification result. A complete run must have the expected number of checks and zero failures. Review individual check details instead of relying only on counts.

If a test fails, preserve the JSON report with the commit SHA and environment details when opening an issue. The report includes up to 5,000 characters of each command's captured stdout and stderr; inspect it for paths or other sensitive information before sharing publicly.

## Known limitations

- The repository's GitHub Actions failures are tracked separately in [issue #12](https://github.com/fosterb1/kasa_programming_language/issues/12). The local runner avoids that infrastructure entirely.
- Do not claim full C++ or Python test success merely because isolated lexer or browser cases passed.
- The native engine's documented signed 64-bit integer limit remains different from Python/JavaScript. Conformance fixtures should be scoped to supported semantics.
- No real-browser WASM integration is tested by this command.
- This does not certify Twi vocabulary. All newly proposed words remain subject to [the linguistic evidence policy](./LANGUAGE_RESEARCH_POLICY.md).

This script is a foundation for reproducible Kasa 0.4 testing; it is not a substitute for release sign-off or human linguistic review.
