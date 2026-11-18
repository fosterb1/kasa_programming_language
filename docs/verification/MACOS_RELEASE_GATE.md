# macOS verification and 0.4-alpha release gate

**Status: planned, not executed on macOS.** Linux dry-run and explicit non-macOS refusal can be tested, but they are **not** macOS conformance evidence. GitHub Actions is not required.

## Two native macOS targets

Test **both** Apple Silicon (`arm64`) and Intel (`x86_64`) on actual macOS hosts when available. Running an Intel executable via Rosetta does not replace an independent native Apple Silicon verification. A cross-compiled artifact or Linux-based Clang build also does not count.

## Prerequisites

- A real Mac with Xcode Command Line Tools installed (`xcode-select --install`), CMake, Git, Node.js, Python 3.11+, Boost.Multiprecision development headers and `pytest` (install with `python3 -m pip install -e '.[dev]'` in a virtual environment).
- A **clean** checkout at a known Git commit SHA. Store user projects and generated binaries under `build/` or outside the repo; do not overwrite source examples.
- Homebrew-based setup is one option: `brew install cmake node boost python`. Confirm `cmake`, `ctest`, `node` and `python3` resolve on PATH. Homebrew paths differ between Apple Silicon and Intel.
- CMake must be able to find `boost/multiprecision/cpp_int.hpp`. If it cannot, supply `CMAKE_PREFIX_PATH` (for example `export CMAKE_PREFIX_PATH="$(brew --prefix boost):${CMAKE_PREFIX_PATH:-}"`) before running the script.

## Reproducible run on macOS

From the Kasa repository root, in a local virtual environment with `.[dev]` installed:

```sh
git pull --ff-only origin main
git status --porcelain
git rev-parse HEAD
python3 scripts/verify_macos_release.py --dry-run
python3 scripts/verify_macos_release.py --report build/macos-release-gate.json
```

The script will fail closed unless `platform.system() == 'Darwin'`, `platform.machine()` is `arm64` or `x86_64`, the Git checkout is clean and prerequisites are available. It runs the canonical **10-stage parity profile**, its SHA-pinned audit, **18-stage full profile**, the opt-in Boost native CMake configure/build, then **three KBC2 CTest targets** (RFC-0008 source/KBC2 round trips, ten byte-for-byte Linux reference fingerprints, 320 deterministic corrupted loader inputs). A JSON report captures each attempted command, exit code, output tail, host architecture and the unchanged Git commit. A successful local report does not certify signing, installers, memory safety or trust of downloaded bytecode.

`--dry-run` prints six planned stages on *any OS* without running any tests. A Linux dry-run is useful for checking script syntax and planning but is **not** macOS verification.

## Evidence needed before calling macOS tested

- One `build/macos-release-gate.json` report from an actual native Apple Silicon host, plus a distinct report from an Intel Mac if available. Use distinct filenames.
- Exact `git rev-parse HEAD` and toolchain versions: `clang++ --version`, `cmake --version`, `python3 --version`, `node --version`.
- Review failure messages and source status before promoting any platform claim. An account of passing tests without a machine log is user-reported evidence only.
- Run additional macOS sanitizer and packaging validation separately. The verification runner does **not** perform signing or notarization.

## Broader Kasa 0.4 readiness

| Gate | Current evidence | Open requirement |
|---|---|---|
| Windows KBC1 and opt-in KBC2 | User-reported MSVC passing native/bytecode/golden/320-loader checks | Capture exact SHA and complete report for reproducibility |
| Linux KBC1 and opt-in KBC2 | Independent parity/full, golden, 320 loader mutations and Clang sanitizers | Longer coverage-guided fuzzing and release reproducibility |
| macOS `arm64` and `x86_64` | **Not run** | Real native platform evidence |
| Browser JavaScript playground | Node tests pass | Real-browser interactive verification |
| WebAssembly | Protocol tests, development scaffolding | Genuine compiled WASM runtime executing in browser |
| Distribution | Local builds | Licensing, dependency audit, installer/signing, version and release notes |

**Planning estimates remain 90% for the defined 0.4-alpha implementation checklist and approximately 35% for Kasa 1.0 readiness.** These are not test coverage measurements or release promises.
