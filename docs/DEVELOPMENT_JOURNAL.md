# Kasa — Engineering Development Journal

**Purpose:** Record *what actually changed*, *what was verified*, *what failed*, *what we discovered*, and *what is still unknown*. This is the canonical living progress record for Kasa development; do not substitute a feature plan or a green badge for evidence.

**Last reviewed:** 2026-11-18  
**Reference branch:** `main`  
**Latest merged compiler milestone:** [PR #16 — experimental KBC1 portable bytecode](https://github.com/fosterb1/kasa_programming_language/pull/16) (merged 2026-11-18). **Next risk:** native/Python/JavaScript conformance and cross-platform validation.  
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
| Offline education | Browser interpreter; nine tracked root `.kasa` examples including cashbook, stock and school fees | The three new examples executed correctly in the browser | Pilot with Ghanaian teachers/learners not yet performed |
| Independent local verification | [Runner](../scripts/verify_local.py) and [guide](./INDEPENDENT_TESTING.md) | **6/6 runner unit tests** passed in focused prior verification | Full profile requires complete checkout with Python, Node, CMake, C++ |
| Disk-based portable bytecode (KBC1) | **Merged into main as experimental alpha (PR #16)** | **7/7 serializer checks**, **14/14 full native KBC1 tests** under GCC, Clang, GCC ASan/UBSan; 2,000 mutation attempts without sanitizer reports | Alpha format is not authenticated, a sandbox, or a stable portable interchange standard |
| Native WebAssembly | Source bridge and build scripts | Source-level and worker simulation checks from previous milestones | No verified real Emscripten-generated WASM running in the browser |
| License | No `LICENSE` file | N/A | Public visibility does not grant an open-source license. Owner decision required |

**Progress percentages are planning judgments**, not a substitute for these verifiable milestones.

## Development entries

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
