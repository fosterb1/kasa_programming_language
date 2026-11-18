# Kasa Windows native verification — user-run evidence (2026-11-18)

## Scope and provenance

This record summarizes **terminal output and screenshots supplied by the user** while testing the checked-out Kasa repository on Windows with Visual Studio Build Tools 2026, MSVC, CMake, PowerShell/Command Prompt, Python and Node.js. This evidence is **user-executed**, unlike the agent-operated disposable Linux sandbox runs. The exact Windows commit SHA and JSON audit report have **not** been independently fetched; do not label this machine's commit as independently attested.

## Observed Windows results

- Kasa Python interpreter successfully executed a custom `.kasa` program printing `Akwaaba, Ama` and `40`.
- Python pytest run: **239 passed, 4 skipped, 0 failed**. Four skips concern POSIX-specific native test-driver behavior and do not constitute Windows native verification.
- Node browser and WASM-protocol tests: **234 passed, zero failures** (these test protocol/fallback logic, not real WASM execution in a browser).
- Native C++ executable and the standalone lexer, KBC1 smoke and numerical smoke projects compiled under MSVC; user executed source and compiled KBC1 programs successfully.
- Initial native conformance output reported **187 failing subtests** because MSVC converted LF to CRLF on output and Python's temporary source-file writer rewrote CRLF. Root causes fixed in merged [PR #50](https://github.com/fosterb1/kasa_programming_language/pull/50).
- Following `git pull` and rebuild, the user supplied native conformance output showing **24 test methods, all passed, 7.449 s**, including native source, KBC1, Unicode, numeric conversion and CRLF source-coordinate tests.
- User supplied screenshot showing Windows parity **10/10 stages passed**, but initial SHA audit rejected a dirty checkout due to untracked personal `my_test.kasa` / `my_test.kbc` files. User moved personal files out, reran parity and commit audit, and **reported PASS**.
- User subsequently **reported all 18 full-profile Windows stages passed**; exact final console summary and full JSON file were not provided to this repository audit.

## What remains

This establishes credible user-operated Windows alpha-subset verification, with a directly visible native conformance log and parity result. It does **not** independently verify the user's final full-profile JSON or the exact Windows commit, and it does not certify Windows installer packaging, actual native WebAssembly execution in a browser, macOS, arbitrary-precision native integers or KBC1 big-int serialization. For a future independent reproducible release gate, obtain `git rev-parse HEAD`, a clean `git status --porcelain`, the generated `build/windows-parity.json`, the full-profile JSON and its associated SHA-pinned audit result.

## Minimal reproducible Windows commands

In VS Code Command Prompt initialized with the Visual Studio x64 developer environment:

```bat
cmake -S native -B build\kasa-local
cmake --build build\kasa-local --config Release
.venv\Scripts\python.exe native\tests\conformance.py build\kasa-local\Release\kasa-native.exe
.venv\Scripts\python.exe scripts\verify_local.py --profile parity --report build\windows-parity.json
.venv\Scripts\python.exe scripts\verify_local.py --profile full --report build\windows-full.json
```

This report should not cause an automatic increase in the existing 90% Kasa 0.4 implementation checklist or ~35% Kasa 1.0 readiness estimate.
