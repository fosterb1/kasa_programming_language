# Kasa programming language — Progress scorecard

**As of:** 2026-11-18  
**Reference:** Linux full-suite verified on merged `main` commit [`cbce6a6`](https://github.com/fosterb1/kasa_programming_language/commit/cbce6a6c6c20b9e994086fddbbeac12d42a45f71) (PR #48).  
**How to interpret:** These percentages are *planning indicators*, not measured engineering-hours completed, automated test coverage, product-market fit, or a guaranteed release date.

## Kasa 0.4 alpha engineering progress: 90% (9 of 10 defined implementation checkpoints)

Each checkpoint below is scored as one implemented capability, regardless of its difficulty. A checkmark means the feature exists with at least **targeted** evidence, not that the feature is fully production-certified.

| # | Checkpoint | Status | Evidence or outstanding question |
|---:|---|---|---|
| 1 | Python reference interpreter and CLI | Implemented | Parser, runtime, command-line entry point, tests |
| 2 | JavaScript browser runtime | Implemented | 227/227 Node semantic checks passed on merged `main` via parity suite (2026-11-18) |
| 3 | C++20 native compiler and in-memory VM | Implemented in alpha | Linked native VM built and passed full-profile Linux conformance on merged PR #48 commit |
| 4 | KBC1 versioned disk bytecode | Implemented in alpha | Native round-trip, loader and adversarial tests; unsigned, not a sandbox |
| 5 | Shared numeric correctness work | Implemented with targeted tests | Exact signed remainder and large int/decimal comparison; further mixed arithmetic differences remain |
| 6 | Unicode source locations and diagnostics | Implemented with targeted tests | Shared fixture corpus, supplementary-letter lexer handling |
| 7 | Ghana-focused offline programs | Implemented | Twenty-six root exercises including accounting, inventory, school fees and savings |
| 8 | Independent tests and documentation | Implemented | Local quick/parity/full profiles, progress journal, verification reports |
| 9 | Linux cross-runtime parity for the implemented 0.4 portable subset on exact merged revision | **Verified for Linux alpha subset** | Merged `main` commit `cbce6a6`: 10/10 audited parity + 18/18 full-profile stages; 243/243 pytest and 227/227 Node semantic; native/KBC1 tested. **Not** RFC-0008 native big integers, macOS/Windows or stable 1.0 parity |
| 10 | Cross-platform/real-browser WASM and alpha packaging validation | **Open** | Windows/macOS, actual WASM browser run, installation and resource limits |

**Arithmetic:** 9 / 10 checkpoints = **90%** of this *experimental-alpha implementation checklist*, scoped to the existing Linux-supported language subset. Cross-platform/real-browser packaging is still open, as are native arbitrary-precision integers and KBC1 big-int semantics; this is **not** 90% of a stable language release.

## Kasa 1.0 stable maturity: ~35% (illustrative planning estimate)

This estimate uses a separate ten-area *readiness* rubric: 1 point for broadly implemented, 0.5 for partial alpha work, 0 for not established. Areas differ greatly in effort. Therefore **35% is approximate and should not be presented as verified coverage**.

| 1.0 readiness area | Score (0–1) | Notes |
|---|---:|---|
| Language core and Python implementation | 1.0 | Working interpreter with tests |
| Browser interpreter | 1.0 | Working engine with focused conformance checks |
| Native compiler and stable portable bytecode | 0.5 | Alpha KBC1 works; backward compatibility and security posture unfinished |
| Cross-runtime semantic standard and parity | 0.5 | Merged Linux alpha subset parity is now green, but RFC-0008 native big integers, other platforms and future-language semantics remain incomplete |
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

**Arbitrary-precision integer decision and tests (2026-11-18):** [RFC-0008](./RFC-0008-arbitrary-precision-integers.md) selects exact arbitrary-precision integers as the intended language model under explicit resource limits; **native int64 and KBC1 big-integer support are not yet upgraded**. Ten target programs were added and registered in Python/JS (not native success gate); the updated JavaScript source passed **94/94** direct conformance checks. Python/Node full runners, native VM, KBC1 and full local parity remain unexecuted on this revision. This is specification and test infrastructure, not a new completed engineering checkpoint. Progress stays **80% / ~35%**.

**2026-11-18 parity evidence hardening:** The local auditor previously accepted any nonempty command under a correctly named stage; a report of 10 `python -V` invocations could misleadingly pass. It now checks stage argument vectors against the local parity plan, validates matching pre/post Git revisions, and supports `--expected-commit`. Runner and isolated auditor tests were updated. **Full tests and a genuine new parity report remain unexecuted**; keep checkpoint 9 open and planning estimates **80% / ~35%**.

**2026-11-18 source decimal underflow:** A second C++ `std::stod` path survived in `native/src/parser.cpp`, so correctly rounded tiny decimal source literals could fail despite the prior `nɔma` conversion fix. The native parser now uses validated `std::strtod`, and three shared source/KBC1 fixture cases were added. **97/97** shared direct JS source tests and isolated GCC/Clang sanitizer probes passed, but Python/native linked/KBC1 full parity is **not yet verified**. Score stays 80% / ~35%.

**2026-11-18 native Windows stdin parity:** `bisa()` now drops terminal CR remaining from C++ `getline` on CRLF input, matching Python/JS terminal line-end normalization while preserving internal carriage returns. Eight shared fixtures added for Python, Node, native source and KBC1, including local parity profile. **106/106** direct JS fixtures and **6/6** isolated C++ checks on each GCC/Clang with sanitizers passed; full linked VM/KBC1 remains unrun. The score stays **80% / ~35%**.

**2026-11-18 complete-checkout verification breakthrough:** Successfully cloned and built Kasa in a disposable Linux environment without GitHub Actions. On clean candidate branch commit `974f9d0d2b73804fcdc4f297716169cddcd9ef64`, **243/243** Python tests, **227/227** Node semantic tests, **10/10** parity stages with SHA-pinned audit, and **18/18** full-profile stages passed. This required fixing a stale full-profile stage-count assertion (16 → 18), ensuring native source/KBC1 conformance uses raw-byte capture so an internal `\\r` is not converted by Python universal-newline mode, and ignoring local generated artifacts. **Checkpoint 9 must not be marked complete for the final merged revision until the same parity/full checks pass against that exact commit**. Current native portable subset excludes not-yet-implemented arbitrary-precision integer targets. macOS/Windows and real-browser WASM remain open. Planning estimates stay at 80% / ~35% until the exact merged revision is verified.

**2026-11-18 verified Linux merged-main milestone:** **243/243** Python tests, **227/227** JS semantic cases, **10/10** source/Python/JS/native/KBC1 parity stages with `--expected-commit` audit and matching clean before/after revision, and **18/18** full-profile stages passed on merged `main` commit `cbce6a6c6c20b9e994086fddbbeac12d42a45f71` in an independent temporary Linux sandbox. [Verification record](./verification/2026-11-18-linux-full-parity.md). This completes checkpoint 9 *for the currently implemented Linux-portable Kasa 0.4 subset*, increasing the 0.4 implementation checklist to **9/10 = 90%**. It does **not** mean full language feature or cross-platform parity: arbitrary-precision native/KBC1, macOS/Windows and real-browser WASM remain unverified or unimplemented. The **Kasa 1.0 readiness estimate remains ~35%**.

**2026-11-18 Windows evidence + native bigint foundation:** Real Windows MSVC user output confirmed **24/24 native conformance test methods passed** after PR #50 and a **10/10** parity run; user additionally reported a clean audit and **18/18** full stages, but final SHA/report JSON were not independently reviewed. See [Windows validation record](./verification/2026-11-18-windows-user-validation.md). Introduced an *opt-in* Boost `cpp_int` native bigint **prototype** with decimal parsing and exact bounded arithmetic; Release-mode smoke **1/1** CTest passed and unchanged Linux full checkout **10/10 parity / 18/18 full** passed. This prototype does **not** extend the actual native VM or KBC1; no change to **90% 0.4** checklist or **~35% 1.0** readiness.

**2026-11-18 experimental native big-int VM:** Opt-in `KASA_ENABLE_BIGINT_VM=ON` now allows native **source** programs to pass **all 10/10** RFC-0008 large integer acceptance cases using `cpp_int`; dedicated integration CTest **1/1** passed, including old-format KBC1 arithmetic promotion, rejected KBC1 big constants, and integer resource limit. Default Linux alpha regression: **10/10 parity** and **18/18 full** passed. The default VM remains int64, full KBC2 encoding and MSVC Boost validation are pending; **0.4 score 90% and 1.0 readiness ~35% unchanged**.


**2026-11-18 KBC2 experimental bytecode:** Added opt-in `compile-kbc2` and backward-compatible KBC2 big-int constant encoding (see [KBC2 specification](./KBC2_FORMAT.md)); ten shared RFC-0008 source-to-KBC2 program round trips and seven integration test methods passed on Linux. Default KBC1 unchanged; default Linux parity **10/10** and full **18/18** stages passed. **Windows/macOS, sanitizers and production format stability remain open. Kasa 0.4: 90%; Kasa 1.0: ~35% unchanged.**


**2026-11-18 KBC2 determinism verification:** Introduced ten fixed SHA-256 byte-for-byte KBC2 golden fixtures and a Linux-verified opt-in CTest. Linux baseline **10/10** hashes matched, **2/2** opt-in CTest targets passed. User reports prior Windows KBC2 integration success, but **Windows golden hash comparison is still pending**. Percentages unchanged pending platform certification.
