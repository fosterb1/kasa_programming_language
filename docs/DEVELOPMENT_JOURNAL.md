# Kasa — Engineering Development Journal

**Purpose:** Record *what actually changed*, *what was verified*, *what failed*, *what we discovered*, and *what is still unknown*. This is the canonical living progress record for Kasa development; do not substitute a feature plan or a green badge for evidence.

**Last reviewed:** 2026-11-18  
**Reference branch:** `main`  
**Latest merged compiler milestone:** [PR #16 — experimental KBC1 portable bytecode](https://github.com/fosterb1/kasa_programming_language/pull/16). **Earlier test milestone:** [PR #25 — 10,080-case Python/C++ numeric differential and progress scorecard](https://github.com/fosterb1/kasa_programming_language/pull/25), merged 2026-11-18. **Next risks:** full native VM integration of this precision fix, 58 Python/KBC1 parity fixtures, and cross-platform verification remain pending.  
**Blocked external CI:** [Issue #12 — GitHub Actions jobs terminate before recorded steps](https://github.com/fosterb1/kasa_programming_language/issues/12)

## How to record future milestones

For each nontrivial change, add a dated journal entry **in the same PR** with these fields:

- **Status:** Proposed / Implemented on branch / Independently verified / Merged / Released.
- **Changed:** Specific paths, behavior, and user-visible results.
- **Independent verification:** Exact command, runtime/toolchain, number of checks, result, and commit/branch tested. Treat *configured* or *dry-run* checks as **not run**.
- **Discoveries and decisions:** What surprised us, the evidence, alternatives and tradeoffs.
- **Risks and failures:** Known bugs, incomplete checks, portability limits and next actions.
- **Documentation:** Source links, language RFC changes, learner instructions and relevant linguistic evidence.
- **Next gate:** A specific, independently executable step required to move forward.

Do not claim the project is `1.0`, safe for hostile bytecode, linguistically certified, or fully cross-runtime conformant without corresponding evidence.

## Current engineering status

| Workstream | Actually present in `main` | Verified scope | Limitations |
|---|---|---|---|
| Python reference interpreter | Lexer, parser, runtime, CLI, REPL | Existing automated pytest files; **full current-branch suite not independently rerun here** | Reference implementation still has unstandardized numeric edge cases |
| Browser JavaScript engine | Runs Kasa directly without Pyodide | **89/89 direct JS regression checks rerun on PR #16 on 2026-11-18**: 26 programs, 27 expected errors, 15 remainder cases, nine examples, 11 location cases, one EOF check | Direct V8 execution is not a complete Node/browser integration suite |
| Native compiler/VM | C++20 native compiler/VM 0.4 alpha with experimental serialized KBC1 **merged into main** in PR #16 | **Full CMake native executable built; 14/14 KBC1 tests under GCC, Clang and GCC ASan/UBSan** in reconstructed exact-source environment, after fixing a closure memory leak | Whole-repository pytest/Node and native-vs-Python conformance not yet rerun |
| Source-coordinate consistency | Unicode code-point positions and browser supplementary-letter tokenization | Browser source-coordinate fixtures and native lexer smoke | Does not establish strict malformed UTF-8 handling or every Unicode identifier category |
| Linguistic governance | [Policy](./LANGUAGE_RESEARCH_POLICY.md), [audit](./TWI_KEYWORD_AUDIT.md), [evidence register](./keyword_evidence.json) | Automated vocabulary-change guard implemented | All legacy tokens still need human linguistic review; publication links are not speaker approval |
| Offline education | Browser interpreter; sixteen tracked root `.kasa` examples including cashbook, stock, school fees and exact-amount reconciliation | Prior fifteen-example corpus and four new reconciliation scenarios passed direct JavaScript execution (separate scopes) | Pilot with Ghanaian teachers/learners not yet performed |
| Independent local verification | [Runner](../scripts/verify_local.py) and [guide](./INDEPENDENT_TESTING.md) | **6/6 runner unit tests** passed in focused prior verification | Full profile requires complete checkout with Python, Node, CMake, C++ |
| Disk-based portable bytecode (KBC1) | **Merged into main as experimental alpha (PR #16)** | **7/7 serializer checks**, **14/14 full native KBC1 tests** under GCC, Clang, GCC ASan/UBSan; 2,000 mutation attempts without sanitizer reports | Alpha format is not authenticated, a sandbox, or a stable portable interchange standard |
| Native WebAssembly | Source bridge and build scripts | Source-level and worker simulation checks from previous milestones | No verified real Emscripten-generated WASM running in the browser |
| License | No `LICENSE` file | N/A | Public visibility does not grant an open-source license. Owner decision required |

**Progress percentages are planning judgments**, not a substitute for these verifiable milestones.

## Development entries

### 2026-11-18 — Kasa 0.5 language-contract preparation (Step 1 remains open)

- **Status:** **Merged to `main`** in [PR #32](https://github.com/fosterb1/kasa_programming_language/pull/32), squash commit `86e4aa441931ab544c4f376ff70d62ccc16253f5`; not a stable language-standard announcement.
- **Changed:** Added [RFC-0007](./RFC-0007-core-language-contract.md) documenting established lexical forms, precedence, statement/block semantics, functions, lists, built-ins, typing, known runtime differences and proposed acceptance criteria. Added a 12-case JSON contract corpus and Node/JavaScript test-suite registration. No runtime semantics, keywords or open-source licensing were changed.
- **Verification executed:** All **12/12** contract programs were evaluated using the fetched repository JavaScript runtime in a V8 isolate and matched their golden stdout or expected error category. This is direct interpreter execution, **not** a complete Node runner, Python pytest, native VM or KBC1 conformance certification.
- **Discovery:** Current Python parser and JS implementation agree structurally on key rules, including explicit Boolean conditions, precedence, lexical scope, mutable zero-based lists and rejection of chained comparisons. Native integer size limits and runtime resource/diagnostic differences remain unresolved.
- **Risks:** Cross-runtime contract tests have not been executed on a complete native/Python checkout. PR #31 remains an independent draft and Step 1 is still incomplete; do not use this RFC to imply otherwise.
- **Next gate:** Execute the shared contract corpus through Python and native source/KBC1 in a complete checkout, then resolve discrepancies and update RFC-0007 before stabilizing the language.



### 2026-11-18 — Verified JavaScript decimal text-formatting mismatch

- **Status:** **Merged into `main`** through [PR #30](https://github.com/fosterb1/kasa_programming_language/pull/30), squash commit `d44cc0971e50bddfbf97072609276a6e9d25617c`. **Not** full Kasa 0.4 parity certification.
- **Reproduced defect:** Browser output used JavaScript's binary64 exponent formatting. For example `ka 1 / 10000000` returned `1e-7` instead of the Python reference's `1e-07`; large `1e16` values used fixed notation and negative zero lost its sign.
- **Changed:** `playground/kasa-runtime.js` decimal display thresholds, signed zero and exponent width; shared 12-case fixture and browser test registration. No new syntax, keywords, arithmetic APIs, Python/C++ runtime modifications, packages or licensing.
- **Verification:** Exact files read through the connected GitHub repository, executed directly in V8: **129/129 checks passed**: 12 new display fixtures, 16 root examples, 48 other shared semantic fixtures and 53 positive/negative interpreter scenarios. Python 3.13.5 `repr(float)` checked independently for 11 scalar reference values. [Detailed test record](./verification/2026-11-18-browser-decimal-display.md).
- **Known limitations:** Node's full test runner, Python interpreter suite, native CMake/VM and KBC1 were **not executed** on this revision. A separate native C++ decimal precision mismatch (`1/7` rounded by `setprecision(15)`) was reproduced with a focused GCC 14.2 probe and tracked as [issue #29](https://github.com/fosterb1/kasa_programming_language/issues/29); no native runtime patch was merged. Local Git clone remains blocked by `github.com` DNS failure. Shortest-decimal formatting still requires wider differential tests.
- **Next gate:** Run the complete real offline parity profile and audit JSON in a clean checkout, fix actual discrepancies, then consider 0.4 checkpoint closure. **Progress remains 80% alpha implementation / ~35% 1.0 maturity.**



### 2026-11-18 — One-to-one reconciliation teaching algorithm (RFC-0006)

- **Status:** Feature branch implemented for review/merge; not a stable financial standard library.
- **Changed:** Added `examples/bank_reconciliation_matching.kasa`, a shared four-case regression corpus, Python and browser tests, native source/KBC1 conformance registrations, RFC-0006, and updated learning roadmap. Existing Kasa keywords and runtime code remain unchanged.
- **Verification executed:** Four parameterized example programs executed with the actual repository JavaScript interpreter in an isolated V8 context: **4/4 exact expected outputs passed** for duplicates, no matches, zero-valued transactions, and the baseline.
- **Discovery:** One-to-one first-unused matching avoids reusing ledger entries, but **amount alone is not sufficient to identify a real financial transaction**. Duplicate/ambiguous cases require human review and future structured matching rules.
- **Risks:** Python pytest, native VM and serialized KBC1 tests have been added but were **not run against the full project checkout**. No real bank file handling or permissions were introduced.
- **Next gate:** Run the offline eight-stage parity profile in a clean full checkout, audit its recorded result, resolve any differences, and retain the unchanged 80% / ~35% progress indicators until the outstanding engineering gates are actually met.



### 2026-11-18 — Fifteen practical Ghana-focused teaching programs

- **Status:** Implemented on `feature/practical-examples-15-20261118`; proposed for merge. No new Kasa syntax or built-in names.
- **Changed:** Added six root examples (daily sales, cash reconciliation, mobile-money ledger, student grades, savings target, inventory valuation), bringing the root corpus from nine to fifteen. Both Python and JavaScript test suites now share a single golden-output JSON file, check every tracked root `.kasa` example and require at least fifteen.
- **Independent verification performed:** Fetched the actual `playground/kasa-runtime.js`, fifteen `.kasa` source files and shared JSON fixture from GitHub, executed the runtime code in a V8 JavaScript isolate and compared exact output strings: **15/15 passed** (zero errors). This is a direct JavaScript interpreter check, **not** Node's full test runner, Python pytest, real browser execution or C++ KBC1 parity.
- **Discovery:** Index-based loops and lists already support useful offline business and classroom arithmetic; no additional language grammar was necessary. Amounts are integer pesewas, so these exercises avoid decimal rounding but do not offer a production-grade currency type or audited reconciliation engine.
- **Challenges/risks:** Full repository checkout and native/Python integration remained unavailable in the isolated environment. The new shared-fixture Python and Node test-runner code is committed but has not been executed as a complete suite. Mobile-money data is illustrative, without provider integration.
- **Next gate:** Run the full clean checkout `python scripts/verify_local.py --profile parity`; inspect any cross-runtime mismatches in the new examples. Seek fluent Twi educational review and design guided lesson explanations.
- **Progress:** No increase to the existing 80% Kasa 0.4 checklist or ~35% 1.0 maturity estimate. The previously open 15-example minimum is met, but it was not one of the ten alpha checkpoint categories.



### 2026-11-18 — Mixed integer/decimal comparison precision defect

- **Status:** **Merged into main** as an experimental Kasa 0.4 compatibility fix in [PR #23](https://github.com/fosterb1/kasa_programming_language/pull/23), commit `d0adbda82180ea7e1f88c3390adb1b6c7b459464`. Focused native comparator and browser engine verified independently; full native VM/Python/KBC1 integration for this change still needs execution.
- **Discovery:** The browser converted `BigInt` to JavaScript `Number`, while the C++ VM converted signed 64-bit integers to `double` during mixed integer/decimal comparisons. Beyond **2^53**, two different values could incorrectly compare as equal, reverse ordering, or make nested lists equal. Python's reference comparisons preserve exact integer value.
- **Change:** The JavaScript engine now uses exact BigInt/Number relational semantics and BigInt equality for integral decimals. The native VM calls a new finite-int64-versus-binary64 comparison helper that handles `±2^63` conversion boundaries safely; all existing Twi syntax is unchanged.
- **Regression coverage added:** 18 shared Kasa programs consumed by browser JavaScript, Python pytest, and native direct/KBC1 conformance tests, plus a standalone C++20 numeric-comparison smoke target.
- **Independent verification:** **107/107 direct JS checks passed** (including 18 new numeric cases and 89 existing checks). **18/18 exact GitHub-blob-matched C++20 smoke checks passed** with strict GNU 14.2 compiler flags and again with ASan/UBSan. **3,000/3,000** deterministic mixed numeric comparisons matched Python reference numerical comparisons using the same C++ helper.
- **What remains unverified:** The full native CMake/VM build with the updated VM source, the complete Python parser/pytest suite, and compiled KBC1 execution of the new 18 cases. No hosted CI jobs were requested.
- **Evidence:** [Precision-bug report, source identities, commands, results and limitations](./verification/2026-11-18-mixed-numeric-comparison.md).
- **Next gate:** Run local quick/full profiles on the exact revision; if native tests pass, merge as an alpha compatibility fix, and retain the broader 58-case parity gate.

### 2026-11-18 — Focused independent parity profile and reproducible reports

- **Status:** **Merged into main** as verification tooling through [PR #24](https://github.com/fosterb1/kasa_programming_language/pull/24), commit `6bb82da224496b1da92d096ca678a324ec4c4da7`. The real native parity suite has **not** been run against the merged revision.
- **Change:** `scripts/verify_local.py --profile parity` selects seven local stages for Python, JavaScript, C++20 compiler/VM, exact numeric precision, native/Python conformance and KBC1 round-trips. The existing `quick` and `full` plans remain seven and fifteen stages respectively.
- **Discovery:** A broad full-profile run includes unrelated WebAssembly/protocol and platform tests. A smaller parity-only profile helps isolate language inconsistencies without confusing a successful component check with stable release certification.
- **Provenance:** Every JSON report now records Git `HEAD` and whether the working tree is clean. Missing Git metadata is explicitly `null`, and both tracked and untracked changes are considered.
- **Verification performed:** Four reconstructed profile-plan checks passed (quick 7, parity 7, full 15, full+WASM 17); five Git revision helper scenarios passed (non-Git, clean, untracked, modified, restored). These **are focused checks of extracted helper functions**, not a full run of the new Python pytest tests or Kasa's native compiler.
- **Evidence:** [Independent profile-verification record](./verification/2026-11-18-parity-profile.md).
- **Next gate:** Run `python scripts/verify_local.py --profile parity --report build/parity-report.json` from a complete checkout. Record its exit code, observed fixture failures and source commit before claiming the 58 Python/KBC1 cases and 18 recent numeric fixtures passed together.
- **Infrastructure:** GitHub-hosted Actions stay manual-only to avoid automatic runner execution; no hosted verification charges are necessary for this profile.

### 2026-11-18 — Numeric differential extension and milestone progress scorecard

- **Status:** **Merged into `main`** in [PR #25](https://github.com/fosterb1/kasa_programming_language/pull/25), squash commit `f2071538ab360deb133327b315b2c8af14c54710`. Changes local verification and documentation, not Kasa language semantics or Twi keywords.
- **Change:** Added a deterministic **10,080-case** Python-versus-native numeric differential runner and small C++20 batch probe. The local `parity` plan now contains **8** steps and `full` contains **16**; the numeric helper is executed as an independent required stage.
- **Evidence executed:** GitHub-matched `numeric_compare.hpp`, `numeric_compare_probe.cpp`, and `numeric_differential.py` passed **10,080/10,080** pairs under GCC 14.2 and again under Clang 17. Each compiler also passed the pre-existing standalone numeric smoke **18/18**. The newly added Python harness returned a nonzero status when the native executable was absent.
- **Browser regression:** Reexecuted the actual GitHub `playground/kasa-runtime.js` against 107 direct interpreter fixtures on 2026-11-18: **107/107 passed** (26 positive programs, 27 expected errors, 15 remainder, 11 source positions, 18 numeric, nine examples, one EOF).
- **Discovery:** Component tests can provide strong numeric correctness evidence without implying full KBC1 language parity. For the current alpha engineering checklist, **8/10 implementation checkpoints** are present; the unverified full cross-runtime and platform/release checks remain substantial.
- **Progress rubric:** [Kasa 0.4 80% implementation and approximate 1.0 35% maturity scorecard](./PROGRESS_SCORECARD.md); estimates are checklist indicators, not feature coverage, time remaining, or stable-release readiness.
- **Proof:** [Exact source fingerprints, build commands, and local output](./verification/2026-11-18-numeric-differential.md).
- **Next gate:** Run all 58 Python-to-KBC1 reference cases and 18 numeric Kasa-source cases with the complete native VM and Python runtime in the same clean checkout, then record individual failures and fixes. The new numeric differential is **not** a substitute for that.
- **Hosting:** GitHub Actions remains manual-only; no paid hosted CI runs were requested.

### 2026-11-18 — Fail-closed parity-report evidence auditing

- **Status:** Implemented on `feature/parity-report-audit-20261118`, proposed for merge. This is verification infrastructure, not new language syntax or full runtime parity.
- **Changed:** Added `scripts/audit_parity_report.py`, eight isolated unit scenarios in `tests/test_audit_parity_report.py`, and an offline usage section in `docs/INDEPENDENT_TESTING.md`.
- **Independent verification:** Eight analogous local standard-library unit scenarios passed on 2026-11-18 against a locally reconstructed report auditor; syntax compile passed. The final GitHub file version and complete repository suite have **not** been independently executed here.
- **Discovery:** Merely producing a JSON report is insufficient as a green release gate: reports can describe a dry-run, missing stage, altered counts or dirty checkout. The new audit fails those cases without paid CI.
- **Risk:** The audit verifies self-reported stage identity, ordering, statuses and commit metadata, not the truth of actual command execution; forged reports cannot be cryptographically ruled out.
- **Next gate:** Run `python scripts/verify_local.py --profile parity --report build/parity-report.json` and `python scripts/audit_parity_report.py build/parity-report.json` in a real, clean full checkout, then investigate any Python/native/KBC1 mismatches.

## Hosted CI execution policy — 2026-11-18

**Decision:** GitHub-hosted workflows (`tests.yml`, `native.yml`, `wasm.yml`) are preserved but changed to **`workflow_dispatch` only**. They do not run automatically on new pushes or pull requests during the budget-sensitive independent development phase. The user can manually trigger each workflow for final release verification once billing and runner availability have been reviewed.

**Discovery:** Merging PR #22 caused automatic GitHub Actions workflow attempts on commit `9596cc36`, even though none was requested. The observed workflows reported failure. Their failure status **does not establish failing code tests** or any charge; inspect job steps and account billing before making either claim.

**Trade-off:** Manual-only hosted verification reduces automatic coverage and is **not** a green CI result. Required local Python, Node and C++ tests remain the release gate; restore automatic CI later when practical. This repository change does not improve conformance or address the 58 pending fixture executions.


### 2026-11-18 — Conformance driver staging and fail-closed checks

- **Status:** [PR #22](https://github.com/fosterb1/kasa_programming_language/pull/22) **merged into `main`** as test-only infrastructure (squash commit `9596cc36ee4eaabfb57f1ba83fd7cfe411fbac2c`). No Kasa runtime behavior changed.
- **Change:** The cross-runtime harness now tests Python against native source→KBC1→VM execution and failure handling. It adds 58 existing-language test cases to the native reference comparison: 26 successful programs, 10 signed remainders, 11 runtime errors, and 11 malformed Unicode/source inputs. No Twi keyword was introduced.
- **Independent verification:** Four tests of the new compile→check→run *orchestration* passed locally under **Python 3.13.5 / pytest 9.0.2** using a disposable simulated native CLI. The test file matched the GitHub Git-blob SHA `cd98d4f6b39240f5545e7db62d473db820f34559`. The harness helper used for this isolated check matched the exact extracted PR #22 function text by length (**1,440 characters**) and FNV-1a 32-bit fingerprint (**2248846160**) before the **4/4** retest. This non-cryptographic fingerprint is a reconstruction check, **not** authentication or a complete checkout. The tests prove stage order, input forwarding, and fail-closed behavior after compile or check failures.
- **What was NOT run:** None of the newly added **58 reference-versus-native-KBC1 conformance cases** were executed against the real native VM in this session. The four simulated-CLI tests do **not** certify the compiler or KBC1 correctness.
- **Challenge:** Full GitHub checkout is still unavailable in the isolated local container due to external DNS restrictions. We deliberately did not use paid GitHub Actions.
- **Evidence:** [Exact isolated driver verification record](./verification/2026-11-18-kbc1-parity-driver.md), including command, matched helper fingerprint, and explicit limitations.
- **Next gate:** Run `python scripts/verify_local.py --profile full` from a complete checkout, record the output, and fix any semantic differences; **merging the tests does not mean the 58 real cases passed**.

### 2026-11-18 — Experimental KBC1 merged; shared Python/KBC1 conformance expanded

- **Status:** [PR #16](https://github.com/fosterb1/kasa_programming_language/pull/16) **merged to `main`** as Kasa native 0.4 alpha, squash SHA `637a3cee73c50dba6d1c9f6d5c024867f5207894`. The merge does **not** establish language 1.0 or a secure bytecode format.
- **Independent results supporting the merge:** Full native compiler/VM and targeted KBC1 suite previously passed under GCC 14.2, Clang 17 and GNU ASan/UBSan (**14/14 grouped tests**); [complete verification report](./verification/2026-11-17-kbc1-native-integration.md). An additional **89/89 direct browser-runtime regression checks passed** against the candidate branch on 2026-11-18.
- **New discovery:** The existing cross-runtime conformance harness compares Python with **native source execution**, while the KBC1 test suite primarily compares **compiled bytecode with native source execution**. This leaves a gap in directly asserting `Python → compiled KBC1` parity across many language constructs.
- **Change on separate development branch:** Add four KBC1 conformance groups to `native/tests/conformance.py`: 26 successful reference programs including interactive input, 10 shared signed-remainder cases, 11 representative error categories, and 11 Unicode/EOF invalid-source checks. The successful paths compile, check and execute a temporary `.kbc` file and compare its output with Python.
- **Verification status:** These **new groups are written, not independently executed against the complete native binary yet**. The JavaScript 89/89 regression checks are unrelated evidence and must not be presented as a pass of this new native test suite.
- **Challenges:** The independent development container cannot resolve GitHub download hosts for a full checkout; GitHub Actions remains deliberately outside the workflow due to runner/account limitations.
- **Next gate:** Execute `python scripts/verify_local.py --profile full` in a complete local checkout, inspect source versus compiled parity failures, and update this journal with exact observed outcomes before merging the conformance test branch.

### 2026-11-18 — KBC1 full native integration verification and closure leak repair

- **Status:** Independently verified experimental **KBC1 alpha implementation in [PR #16](https://github.com/fosterb1/kasa_programming_language/pull/16)**; ready for experimental integration but **not** a stable release.
- **Changes:** Complete six-source native C++20 executable, `compile`/`run-bytecode`/`check-bytecode`/`disasm-bytecode` CLI, size and nested-instruction limits, source overwriting safeguards and an adversarial round-trip suite.
- **Verification:** Full CMake native build completed; **14/14** bytecode test groups passed with **GCC 14.2**, **Clang 17**, and **GCC AddressSanitizer/UndefinedBehaviorSanitizer** after fixing a leaked closure cycle. Native example outputs matched nine documented JS outputs; **89/89 direct JavaScript regression checks** rerun on this development branch on 2026-11-18.
- **Challenge discovered:** The initial sanitizer run **failed** for programs defining functions. The environment kept functions, and each function retained its defining environment (`Environment → Function → Environment`). Shared-reference cycles caused real memory leaks.
- **Repair and regression:** The VM tracks environment references weakly, then clears retained values during VM destruction, after execution. A new escaping-closure round-trip verifies the returned function still reads its captured variable. The now **14/14 passing sanitizer suite** is a retest of the leak fix, not a claim of comprehensive memory safety.
- **Additional discoveries:** Writer/loader disagreements for non-finite decimals, excessive source coordinates and aggregated nested instruction counts were corrected. Standalone serializer smoke now passes **7/7** checks.
- **Evidence:** [Exact source identities, compiler commands, observed test results and limitations](./verification/2026-11-17-kbc1-native-integration.md).
- **Remaining release gates:** Full Python and Node test runners, native-vs-Python conformance, all CTest targets, macOS/Windows validation, actual WASM browser execution and security/provenance treatment for untrusted `.kbc` files.
- **Decision:** Accept only as an **experimental alpha** after documentation review. CRC32 is corruption detection, not identity verification or a sandbox.

### 2026-11-17 — KBC1 extracted for safer review

- **Status:** Implemented in [PR #16](https://github.com/fosterb1/kasa_programming_language/pull/16), **not merged**.
- **Changed:** Separated KBC1 serialization, file loading, validation, CLI commands, adversarial tests and `kasa-kbc1-smoke` from the much larger, diverged [PR #7](https://github.com/fosterb1/kasa_programming_language/pull/7).
- **Discoveries:** PR #7 mixes unrelated WASM, PWA, editor, example and bytecode features. It is safer to validate a single native file-format change independently rather than merge the whole proposal.
- **Safety checks written:** Version/magic/CRC validation, length and opcode limits, stack/control-flow verification, deterministic serialization, path-alias overwrite protection, source/compiled round-trip expectations.
- **Verification:** The C++ serializer/loader and smoke executable were compiled independently from **exact matching GitHub blob sources**; all **5/5 focused checks passed** (round-trip, header/version/checksum rejection and non-finite writer rejection). The full native VM/CLI build and Python malformed-bytecode suite remain unverified. See [the recorded command, hashes and output](./verification/2026-11-17-kbc1-serializer-smoke.md). Prior successful tests on PR #7 do not automatically transfer to this extraction.
- **Challenges:** Cannot clone GitHub by DNS from the isolated local container; exact-source staged component tests were used instead. GitHub Actions is unavailable for budget/runner reasons. Neither limitation is evidence of passing or failing complete compiler tests.
- **Next gate:** Build the **exact PR #16 source** with CMake in a complete checkout; execute `kasa-kbc1-smoke`, `native/tests/test_bytecode.py`, and the full native/Python conformance suite. Resolve failures before merge.

### 2026-11-17 — KBC1 writer/reader mismatch discovered and repaired

- **Status:** **Fixed on unmerged PR #16**, independently verified at the component level.
- **Discovery:** The bytecode writer accepted a `NaN` floating-point constant and emitted a file that the reader refused to load. This was demonstrated with a two-instruction C++ probe and recorded as a writer/reader contract violation.
- **Repair:** Validate `std::isfinite()` in the serializer before writing any floating-point value; reject both `NaN` and infinity and avoid creating an unreadable file.
- **Verification:** Using GNU g++ 14.2 and strict C++20 flags, **5/5 focused standalone checks passed** after the fix; the same **5/5 passed** with AddressSanitizer and UndefinedBehaviorSanitizer enabled, without reported sanitizer errors. All three staged source files matched the corresponding PR #16 GitHub blob hashes.
- **Evidence:** [Full independent verification record](./verification/2026-11-17-kbc1-serializer-smoke.md).
- **Remaining risk:** This is not the complete native VM/compiler build; full `test_bytecode.py` and source→file→VM round-trips still need execution before PR #16 can merge.

### 2026-11-17 — KBC1 mutation robustness and CRC32 limits

- **Status:** New deterministic loader mutation regression implemented on experimental [PR #16](https://github.com/fosterb1/kasa_programming_language/pull/16); **not merged**.
- **Changed:** A C++20 `bytecode_mutation_smoke.cpp` target runs 2,000 seeded one-bit payload mutations of a valid KBC1 file, recalculates CRC32, then attempts **parsing without executing** the modified code. Registered in CMake and the independent full verification plan.
- **Verification:** Compiled under GNU g++ 14.2 with AddressSanitizer and UndefinedBehaviorSanitizer. **2,000/2,000 attempts completed without reported sanitizer errors**; 1,349 were rejected and 651 were structurally accepted.
- **Discovery:** CRC32 is not authentication. When the checksum is recomputed, some tampered files remain structurally valid. Such accepted variants are *not automatically verifier bugs* and must not be treated as authorized software.
- **Challenges:** This is narrow, deterministic robustness evidence, **not comprehensive fuzzing, security certification, or whole-VM execution**.
- **Evidence:** [Exact-source verification record and mutation result](./verification/2026-11-17-kbc1-serializer-smoke.md).
- **Next gate:** Full native compiler/VM build, source→KBC1→VM round-trip tests and the Python adversarial loader suite on the exact review commit.

### 2026-11-17 — Practical computing specialization implemented

- **Status:** [PR #17](https://github.com/fosterb1/kasa_programming_language/pull/17) **merged**.
- **Changed:** [Market cashbook](../examples/market_cashbook.kasa), [inventory reorder](../examples/stock_reorder.kasa), [school fees](../examples/school_fees.kasa), associated Python/JS expected outputs, and [product-focus research](./KASA_PRACTICAL_COMPUTING_FOCUS.md).
- **Discovery:** Using **integer pesewas** for money is safer for beginner arithmetic than storing fractional cedi values as binary floating-point numbers. The programs are illustrative, not accounting-system replacements.
- **Verification:** **89/89 direct JS checks passed** in the reviewed branch, including nine runnable root examples. This does not establish complete Python/native VM parity.
- **Next gate:** Run full local test profile and validate lesson quality with consenting educators and Ghanaian learners before claiming any educational advantage.

### 2026-11-17 — Independent test infrastructure and Unicode portability

- **Status:** [PR #13](https://github.com/fosterb1/kasa_programming_language/pull/13), [PR #14](https://github.com/fosterb1/kasa_programming_language/pull/14), and [PR #15](https://github.com/fosterb1/kasa_programming_language/pull/15) **merged**.
- **Changed:** Unicode source-column consistency, supplementary Unicode letter identifiers in the browser lexer, end-of-file operator bugfix, local verification runner, and standalone native lexer smoke target.
- **Discoveries:** The native lexer originally counted UTF-8 bytes; JavaScript counted UTF-16 code units. During testing a malformed C++ newline literal was found and fixed *before* merge. Explicit EOF regression coverage also uncovered and fixed a browser lexer boundary bug.
- **Verification:** Browser direct tests and focused native lexer tests passed; full native VM and browser WASM remained unverified.
- **Next gate:** Maintain code-point/source-location fixtures and run whole-repository checks on a functioning independent checkout.

### 2026-11-17 — Signed remainder and Twi-language evidence gate

- **Status:** [PR #9](https://github.com/fosterb1/kasa_programming_language/pull/9), [PR #10](https://github.com/fosterb1/kasa_programming_language/pull/10), [PR #11](https://github.com/fosterb1/kasa_programming_language/pull/11) **merged**.
- **Changed:** Optional prompt in `bisa()`, linguistic-evidence policy/registry, and Python-style floor-based integer remainder across JS/native runtimes.
- **Discovery:** The same `-7 % 3` previously produced different results in Python and JavaScript/C++; semantic rules must be specified and tested across all engines rather than assumed.
- **Verification:** Focused JavaScript tests and arithmetic checks passed; full cross-runtime integration remained pending.
- **Next gate:** Broaden conformance fixtures beyond arithmetic to numeric limits, input, diagnostics and function scoping.

## Current risk register

| ID | Risk / blocker | Severity | Mitigation | Status |
|---|---|---|---|---|
| R-01 | KBC1 native compiler/VM build and targeted bytecode test coverage | High before verification | Full CMake build; 14/14 tests GCC, Clang, ASan/UBSan; [evidence](./verification/2026-11-17-kbc1-native-integration.md) | **Targeted gate cleared; wider release review remains** |
| R-02 | GitHub Actions jobs terminate before steps, apparently affected by account/runner constraints | Medium | Keep CI out of critical path; [issue #12](https://github.com/fosterb1/kasa_programming_language/issues/12); local runner | Open |
| R-03 | Three language engines differ on numeric ranges/formatting and resource limits | High | RFCs and shared conformance corpus; explicit known incompatibilities | Open |
| R-04 | KBC1 CRC32 checks corruption but not malicious modification | **High for untrusted distribution** | A 2,000-case mutation test confirmed some CRC-adjusted files remain structurally valid; require provenance/signature policy, sandboxing and stronger review | Open |
| R-05 | Twi keywords lack final native-speaker/dialect and educator review | High for educational adoption | Evidence policy, structured audit, Asante/Akuapem review | Open |
| R-06 | Lack of explicit open-source license | Medium | Owner chooses license and adds `LICENSE`; do not claim legal open-source status | Open |
| R-07 | No classroom pilot validating proposed accessibility advantage | Medium | Small documented, ethically designed learner/teacher pilot | Open |
| R-08 | Full native-vs-Python/JavaScript semantic conformance and cross-platform release checks incomplete | **High for 1.0** | Run all shared fixtures and complete local verification profile against the same commit; track numeric limits and OS results | Open |
| R-09 | Previously imprecise large integer/decimal comparisons are fixed in main; mixed arithmetic may still round | Medium for alpha; high for financial correctness | 18 shared fixtures; 18/18 C++ helper and 107/107 direct JS checks; complete native/Python/KBC1 integration pending | Comparison fix merged; follow-up open |

## Useful independent commands

```sh
# From repository root, after installing Python dev dependencies:
python -m pip install -e ".[dev]"
python scripts/verify_local.py --profile quick
python scripts/verify_local.py --profile full

# On PR #16 with C++20 tooling, separately test the KBC1 component:
cmake -S native -B build/kasa-local -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-local --target kasa-kbc1-smoke --config Release
ctest --test-dir build/kasa-local -C Release -R kasa_native_kbc1_serializer --output-on-failure
```

**No automatic claim:** Commands listed in this document are reproducibility instructions, not evidence they were run. Record the exact resulting JSON report and commit SHA when executed.

## Release gates still outstanding

- Full green Python/Node/native integration tests on exact release commit.
- KBC1 targeted source→file→VM round-trips and corruption tests passed; still require full cross-platform robustness, security review and format-compatibility policy before a stable KBC1 release.
- Real WASM artifact/browser verification, if advertising native WebAssembly.
- Clear learner-facing tutorials, error messages, and language/cultural review.
- License choice, versioning and release checklist; no stable release until these are met.
