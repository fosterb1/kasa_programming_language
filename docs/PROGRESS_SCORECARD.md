# Kasa programming language — Progress scorecard

**As of:** 2026-11-18  
**Reference:** `main` at the previous baseline, including merged [PR #25](https://github.com/fosterb1/kasa_programming_language/pull/25) (`f2071538ab360deb133327b315b2c8af14c54710`).  
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
| 7 | Ghana-focused offline programs | Implemented | Twenty-six root exercises including accounting, inventory, school fees and savings |
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
| Offline practical education materials | 0.5 | Twenty-six programs (minimum met); teacher curriculum and measured classroom outcomes pending |
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
| 15/15 previous root example outputs directly executed in JavaScript V8 (2026-11-18) | Existing and six new financial/education lessons match the golden output corpus | Does not establish Python/native/KBC1 or actual-browser execution |
| 58 KBC1 reference fixture cases | Added to native conformance harness | **Not yet run end-to-end on the current main revision** |

| 12/12 decimal-display fixtures, plus 117 prior semantic/program checks (2026-11-18) | 129/129 direct JavaScript interpreter checks on formatting-fix branch | Python/Node full runner, native VM and KBC1 not executed on same revision |
| 4/4 amount-reconciliation edge cases directly executed in JavaScript V8 (2026-11-18) | Duplicate-safe one-to-one amount matching behavior | Does not establish Python/native/KBC1 parity or production financial reconciliation |

The numeric regression result above is in the merged [independent evidence report](./verification/2026-11-18-numeric-differential.md), not a claim that Kasa as a language has 10,080 passing conformance programs.

A [candidate core-language contract](./RFC-0007-core-language-contract.md) and [12-case corpus](../tests/conformance_language_contract.json) were added for Kasa 0.5 preparation. **12/12** direct JavaScript executions passed; Python/native/KBC1 contract parity was **not** executed. This documentation and fixture work does not complete checkpoint 9 or change either progress percentage.

## Immediate technical priorities

1. Run `python scripts/verify_local.py --profile parity` on a complete local checkout; capture source SHA, exit status and all failures. **Never count dry-run stages as passes.**
2. Fix real Python/JS/native/KBC1 semantic mismatches found by that run, especially mixed arithmetic, number formatting and resource limits.
3. Establish a stable bytecode compatibility policy, true cross-platform install tests and a sandbox/provenance model before supporting untrusted KBC1.
4. Advance the product focus: authentic Twi explanations, reviewed beginner curriculum, practical data/financial libraries and a documented educator pilot.
5. Choose and publish an actual open-source license; a public GitHub repository alone is not a grant of reuse rights.

Review this scorecard after every substantive pull request. Add or reweight checkpoints when requirements change; **do not increase the percentage merely because new code was committed**.

**Integration caveat (2026-11-18):** The native decimal formatting candidate has been reconciled with the current source and direct JavaScript tests passed 27/27 (15 decimal + 12 core contract cases). Component-level C++ results remain in the verification report. **Full cross-runtime integration is still unverified; checkpoint 9 remains open and the 80% / ~35% indicators are unchanged.**

**Platform integration evidence:** Ten more root Kasa examples passed exact expected output checks in the JavaScript interpreter; combined root corpus **26/26** passed. An earlier 24-case shared Python/JS corpus passed **24/24** in direct JavaScript execution and 11 structural checks of the experimental offline/VS Code assets passed. This is **not** full Python, native, browser, WASM, or editor integration certification. The alpha/1.0 planning percentages remain 80% / ~35%.

**2026-11-18 Unicode-output precision:** The JavaScript interpreter's output guard previously counted UTF-16 units rather than Unicode code points. A new shared output path for `ka` and `bisa` fixes the discrepancy; five focused direct V8 tests and 51 existing semantic cases pass. Native byte-based and Python output budgets remain inconsistent; cross-runtime parity and Kasa 0.4 checkpoint 9 are still open, with percentages unchanged.

**Output-budget conformance candidate (2026-11-18):** Python, JS and native source now use a 64,000 Unicode-code-point output cap with shared `ka`/`bisa` accounting and a `ResourceError` on excess. Eight new cross-runtime fixtures were added; **8/8 direct JS executions passed** and **7/7 isolated native quota assertions passed** under both GCC and Clang sanitizers. Full Python/Node/native/KBC1 parity is **not yet executed**, so checkpoint 9 stays open and the 80% / ~35% planning estimates are unchanged.

**2026-11-18 numeric conversion gap:** Native `nɔma` now validates the same strict ASCII numeric text grammar as Python and JS, preventing `std::stod` from admitting exponent syntax, and classifies native out-of-range conversions as `ResourceError`. Added 16 shared fixtures; **75/75** direct JS conformance checks passed and **16/16** isolated C++ grammar probes passed under GCC/Clang sanitizers. Full Python/native/KBC1 integration remains open, and differing large-integer ranges are not resolved. The planning percentages remain unchanged.

**Decimal underflow fix candidate (2026-11-18):** Native `nɔma` now accepts correctly rounded binary64 underflow to zero and finite subnormal results instead of treating valid decimals as out-of-range. Four shared conversion cases added; **79/79** direct JS semantic checks and **13/13** isolated GCC/Clang sanitizer decimal checks passed. Complete Python/Node/native/KBC1 integration and locale compatibility remain unverified, so the 80% / ~35% estimates and cross-runtime gate stay unchanged.

**2026-11-18 signed native integer boundary candidate:** C++ native parser source now specially handles `-9223372036854775808`, a legitimate int64 minimum previously rejected before negation. Five shared Python/Node/native/KBC1 fixtures were added and **84/84** direct JavaScript semantic cases passed. Linked native execution and bytecode were not run on this source revision, and unlimited integer support remains a separate design issue. Keep checkpoint 9 open and the 80% / ~35% planning estimates unchanged.
