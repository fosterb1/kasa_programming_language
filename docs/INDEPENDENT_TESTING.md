# Verify Kasa without GitHub Actions

**Status:** Independent command-line test runner for the existing Kasa codebase.
**Language changes:** None. No Twi keywords or syntax rules are added.

Kasa has separate Python, JavaScript and native C++ implementations. A green result from one runtime is not sufficient to claim that all three behave alike.

## Hosted GitHub Actions policy (cost-conscious development)

As of 2026-11-18 the three GitHub Actions workflows are **manual-only** using `workflow_dispatch`. Normal pushes and pull requests should not automatically start hosted test jobs. The definitions remain in `.github/workflows/` so the project owner can explicitly run them in **GitHub → Actions → select workflow → Run workflow** after checking billing and runner permissions.

This policy is about avoiding unexpected hosted CI execution, **not marking builds green**. The local full profile is still required before release claims. When GitHub-hosted verification is affordable, re-enable push and pull-request checks deliberately; retain the exact workflow history. Earlier automatic runs recorded a failure status, but their root cause and any charge have not been confirmed.

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
| Standalone native Unicode lexer executable | No | Yes |
| Standalone KBC1 serialization and corruption-rejection executable | No | Yes |
| Deterministic KBC1 loader mutation smoke (2,000 CRC-adjusted changes) | No | Yes |
| Exact mixed integer/decimal comparison smoke | No | Yes |
| Native/Python conformance harness (direct source and KBC1-vs-reference fixtures) | No | Yes |
| Native KBC1 round-trip and malformed-bytecode tests | No | Yes |
| Emscripten native WASM and site bundle | No | Optional |

The script runs subprocesses without a shell, captures the final portion of stdout/stderr, records exit codes and durations, and returns **nonzero** if any required step fails. Missing executables are failures, not skipped passes. An unsuccessful native configuration/build marks every downstream dependent check explicitly as **not_run**, including the reason it was blocked; the complete planned check list is preserved in the report.

**A dry run reports `not_run` for every step and never claims the tests passed.** Do not compare a dry-run exit code to a completed test run.

### Exact mixed integer/decimal comparisons

`tests/conformance_numeric_comparisons.json` includes **18 shared cases** involving 64-bit integer boundaries, precision beyond `2^53`, decimal fractions and nested-list equality. This corpus is consumed by Python, JavaScript and the native source/KBC1 conformance harness. The separate native C++20 helper can be tested without the VM:

```sh
c++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
  -I native/include native/tests/numeric_comparison_smoke.cpp \
  -o kasa-numeric-comparison-smoke
./kasa-numeric-comparison-smoke
```

On 2026-11-18, **18/18 standalone C++ checks** and **107/107 direct JavaScript regression checks** passed independently, along with **3,000/3,000 randomized C++/Python numerical cross-checks**. The full native VM and Python/KBC1 fixture execution on this exact branch remain separate verification gates. See [evidence](./verification/2026-11-18-mixed-numeric-comparison.md).

### Native bytecode versus Python reference

The native conformance harness now includes additional `.kbc` comparison groups: **26 existing valid Kasa programs** (including input), **10 signed-remainder programs**, **11 runtime-error examples**, and **11 deliberately invalid Unicode/source-location cases**. Successful programs compare the Python reference output to `kasa-native compile` → `check-bytecode` → `run-bytecode`. Invalid syntax must fail **before producing executable bytecode**.

These are **new test cases, not claimed passing results**. Run the full profile on a complete local checkout and retain its JSON report to verify actual parity.

### Independent conformance-driver safety checks

The new `tests/test_native_conformance_driver.py` checks whether the `compile → check-bytecode → run-bytecode` *test harness* correctly handles success, input forwarding, compiler rejection, malformed-bytecode rejection, and runtime failure.

```sh
python -m pytest -q tests/test_native_conformance_driver.py
```

**Focused observation (2026-11-18):** Four tests passed using Python 3.13.5 and pytest 9.0.2 against the helper extracted from PR #22, reconstructed with matching 1,440-character length and FNV-1a 32-bit fingerprint (2248846160), and a disposable fake native CLI, without downloading the full repository. A non-cryptographic fingerprint is not proof of authenticity. The committed test file's Git blob matched that locally tested file. The simulated binary only checks *test orchestration*; it is **not an implementation of Kasa**. The fixture uses a POSIX shebang and is explicitly skipped on Windows.

The 58 real KBC1 reference-parity fixtures remain **not executed against the native VM**. Those must be verified separately with the local full profile. A green stage-control test does not substitute for a compiled Kasa test.

### Run the native lexer independently

You can build only the lexer test, without linking Kasa's bytecode compiler or virtual machine:

```sh
cmake -S native -B build/kasa-local -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-local --target kasa-lexer-smoke --config Release
ctest --test-dir build/kasa-local -C Release -R kasa_native_lexer_unicode --output-on-failure
```

The standalone executable evaluates **13 lexical checks**. The full local verifier invokes this binary directly and checks its exit code, avoiding the possibility of a zero-test CTest run being mistaken for success. The same test is also registered with CTest for manual use. Neither result is equivalent to the entire native VM passing.

### KBC1 checks without the full VM

```sh
cmake -S native -B build/kasa-local -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-local --target kasa-kbc1-smoke --config Release
ctest --test-dir build/kasa-local -C Release -R kasa_native_kbc1_serializer --output-on-failure
```

The C++ serializer smoke has **seven targeted checks**, including non-finite values, source coordinates and aggregate nested instruction limits, and the full profile executes its binary directly. The separate Python `native/tests/test_bytecode.py` suite additionally requires the complete native VM executable to test source/bytecode execution and malformed files.

### Mutation stress test for the KBC1 loader

```sh
cmake -S native -B build/kasa-local -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-local --target kasa-kbc1-mutation-smoke --config Release
ctest --test-dir build/kasa-local -C Release -R kasa_native_kbc1_mutation --output-on-failure
```

This test runs 2,000 seeded bit mutations, **recomputes CRC32**, and loads each modified bytecode file *without executing it*. Some modified files may remain structurally valid. A clean run means the parser completed this finite sample; **it does not certify security or bytecode authenticity**.

### Latest independent full native integration evidence

The exact PR #16 native executable compiled on Linux with **GCC 14.2** and **Clang 17**; the source→KBC1→VM adversarial suite passed **14/14 test groups** under each and **14/14 under GCC AddressSanitizer/UndefinedBehaviorSanitizer**, after a confirmed lexical-closure memory leak was fixed. See [the recorded commands, source blob hashes, failures and retests](./verification/2026-11-17-kbc1-native-integration.md). This does not replace full Python/Node/browser/Windows/macOS checks, and a CMake staged build with `BUILD_TESTING=OFF` does **not** verify all CTest targets.

## Interpreting results

```json
{
  "profile": "full",
  "dry_run": false,
  "counts": {
    "passed": 15,
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
