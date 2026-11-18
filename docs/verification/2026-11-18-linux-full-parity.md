# Verified Kasa 0.4 Linux parity and full-profile baseline — 2026-11-18

## What was actually executed

**Source:** merged `main` at `cbce6a6c6c20b9e994086fddbbeac12d42a45f71` ([PR #48](https://github.com/fosterb1/kasa_programming_language/pull/48)).  
**Environment:** independent, disposable Vercel Linux sandbox; Python 3.14.4, Node.js 24.22.3, GCC 15, CMake, and a Python virtual environment. This was a fresh Git clone rather than manually copied source or isolated source snippets. The checkout was **clean** before and after the checks.

### Commands and observed results

```sh
.venv/bin/python scripts/verify_local.py --profile parity --report build/merged-parity.json
# PASSED: 10 | FAILED: 0 | NOT RUN: 0

.venv/bin/python scripts/audit_parity_report.py build/merged-parity.json \
  --expected-commit cbce6a6c6c20b9e994086fddbbeac12d42a45f71
# PASS: report records 10 successful parity stages at a known source revision

.venv/bin/python scripts/verify_local.py --profile full --report build/merged-full.json
# PASSED: 18 | FAILED: 0 | NOT RUN: 0
```

- Complete Python pytest: **243 passed**; includes the previously stale test-runner regression.
- Node semantic tests within the parity profile: **227 passed**, zero failures.
- Native CMake configuration and linked C++20 compiler/VM build: passed.
- Native lexer, KBC1 serializer and KBC1 hostile-input mutation smokes: passed.
- Native mixed-number, decimal display and 10,080-case comparison differential probes: passed.
- Python-versus-native source VM conformance: passed.
- Native KBC1 compile/check/run source round-trips and rejection tests: passed.
- Verified identical source commit and clean Git working tree before/after both profiles.

### Two confirmed failures encountered and fixed

1. Initial full Python pytest on `e9ec7ffe4715d0ec38cb685243fd7d6793206447`: **242 passed / 1 failed**, caused by obsolete expectation of 16 full-profile stages rather than 18. Corrected in PR #48.
2. Initial parity on that commit: **9 passed / 1 failed** in native conformance. The native program emitted correct raw bytes `b'A\\rB\\n'` for a fixture with an internal carriage return; **the Python test harness** had `subprocess.run(text=True)`, normalizing CR to LF. PR #48 corrected the harness to read raw process bytes and decode explicitly as UTF-8 for native source and KBC1 execution. This was **not** a bug in native line input itself.

PR #48 also added `.gitignore` patterns for build artifacts, venv and Python caches so the checkout remains clean after local runs.

### What this result does not certify

This verifies the **existing portable Kasa 0.4 alpha subset on Linux**, *not* the full intended language described in RFC-0008. Native C++ still uses signed int64 values and KBC1 has no arbitrary-precision integer encoding. The Python/JavaScript big-integer target cases are intentionally excluded from native-success tests. The result does not validate macOS/Windows, a real WebAssembly browser, installer artifacts, adversarial sandboxing, GPU acceleration, a standard library, or real-world classroom outcomes.

The ten-stage JSON report audit is a report-consistency check, **not cryptographic proof** of command execution. Re-run the commands above on future commits; do not transfer the green status to unrelated revisions.

### Scoring implication

The Linux-specific alpha subset cross-runtime parity checkpoint is now verified, raising the project's **Kasa 0.4 implementation checklist to 9/10 (90%)**. The **Kasa 1.0 stability/readiness estimate remains ~35%** because feature coverage, cross-platform packaging, real-browser WASM, native arbitrary precision, security and language review remain unfinished.
