# Kasa programming language — Progress scorecard

**As of:** 2026-11-18  
**Reference:** `main` plus experimental verification additions in the current pull request.  
**How to interpret:** These percentages are *planning indicators*, not measured engineering-hours completed, automated test coverage, product-market fit, or a guaranteed release date.

## Kasa 0.4 alpha engineering progress: 80% (8 of 10 defined implementation checkpoints)

Each checkpoint below is scored as one implemented capability, regardless of its difficulty. A checkmark means the feature exists with at least **targeted** evidence, not that the feature is fully production-certified.

| # | Checkpoint | Status | Evidence or outstanding question |
|---:|---|---|---|
| 1 | Python reference interpreter and CLI | Implemented | Parser, runtime, command-line entry point, tests |
| 2 | JavaScript browser runtime | Implemented | 107/107 direct runtime regression checks on 2026-11-18 |
| 3 | C++20 native compiler and in-memory VM | Implemented in alpha | Independently compiled native VM; full latest-revision regression still required |
| 4 | KBC1 versioned disk bytecode | Implemented in alpha | Native round-trip, loader and adversarial tests; unsigned, not a sandbox |
| 5 | Shared numeric correctness work | Implemented with targeted tests | Exact signed remainder and large int/decimal comparison; further mixed arithmetic differences remain |
| 6 | Unicode source locations and diagnostics | Implemented with targeted tests | Shared fixture corpus, supplementary-letter lexer handling |
| 7 | Ghana-focused offline programs | Implemented | Nine root exercises including market cashbook, stock and fees |
| 8 | Independent tests and documentation | Implemented | Local quick/parity/full profiles, progress journal, verification reports |
| 9 | Full cross-runtime parity on exact release revision | **Open** | Execute the 58 Python/KBC1 fixture cases, 18 numeric cases, all Python and Node tests with full native binary |
| 10 | Cross-platform/real-browser WASM and alpha packaging validation | **Open** | Windows/macOS, actual WASM browser run, installation and resource limits |

**Arithmetic:** 8 / 10 checkpoints = **80%** of this *implementation checklist*. The remaining two checkpoints are substantial and may require multiple release cycles.

## Kasa 1.0 stable maturity: ~35% (illustrative planning estimate)

This estimate uses a separate ten-area *readiness* rubric: 1 point for broadly implemented, 0.5 for partial alpha work, 0 for not established. Areas differ greatly in effort. Therefore **35% is approximate and should not be presented as verified coverage**.

| 1.0 readiness area | Score (0–1) | Notes |
|---|---:|---|
| Language core and Python implementation | 1.0 | Working interpreter with tests |
| Browser interpreter | 1.0 | Working engine with focused conformance checks |
| Native compiler and stable portable bytecode | 0.5 | Alpha KBC1 works; backward compatibility and security posture unfinished |
| Cross-runtime semantic standard and parity | 0.5 | Shared corpora exist; full merged-revision pass pending |
| Offline practical education materials | 0.5 | Nine programs; teacher curriculum and measured classroom outcomes pending |
| Production-grade data/financial standard library | 0 | Fixed-point/currency, CSV, safe files, structured data still to build |
| Professional tools and developer ecosystem | 0 | Editor/debugging/package-manager suite remains unverified or experimental |
| Cross-platform and real WASM/browser reliability | 0 | Packaging and actual-browser WASM tests incomplete |
| Twi linguistic/educational review and pilot | 0 | Independent Asante/Akuapem and learner/teacher validation incomplete |
| Open-source license, security and stable-release governance | 0 | No explicit LICENSE decision; bytecode is not trusted/sandboxed |

**Illustrative score:** 3.5 / 10 = **~35%**. This is **not** a prediction of remaining calendar time. Availability of volunteers, research and cross-platform bugs may change the denominator.

## Verified results and their scope

| Test result | Verified meaning | What it does not establish |
|---|---|---|
| 107/107 JS regression fixtures | Direct browser-runtime interpreter logic | Real browser/PWA/WASM or full native parity |
| 14/14 KBC1 integration groups (prior milestone) | Native GCC/Clang and sanitizer alpha integration | Latest merged Python/JS/native test suite or hostile-bytecode safety |
| 18/18 C++ numeric smoke, GCC and Clang | Exact integer/decimal comparison helper | Native VM fully integrated with every language case |
| 10,080/10,080 deterministic numeric pairs, **each GCC and Clang** | Python mathematical ordering matches compiled C++ comparator | Full Kasa source/parser/KBC1 conformance |
| 58 KBC1 reference fixture cases | Added to native conformance harness | **Not yet run end-to-end on the current main revision** |

The numeric regression result above is in the review branch's [independent evidence report](./verification/2026-11-18-numeric-differential.md), not a claim that Kasa as a language has 10,080 passing conformance programs.

## Immediate technical priorities

1. Run `python scripts/verify_local.py --profile parity` on a complete local checkout; capture source SHA, exit status and all failures. **Never count dry-run stages as passes.**
2. Fix real Python/JS/native/KBC1 semantic mismatches found by that run, especially mixed arithmetic, number formatting and resource limits.
3. Establish a stable bytecode compatibility policy, true cross-platform install tests and a sandbox/provenance model before supporting untrusted KBC1.
4. Advance the product focus: authentic Twi explanations, reviewed beginner curriculum, practical data/financial libraries and a documented educator pilot.
5. Choose and publish an actual open-source license; a public GitHub repository alone is not a grant of reuse rights.

Review this scorecard after every substantive pull request. Add or reweight checkpoints when requirements change; **do not increase the percentage merely because new code was committed**.
