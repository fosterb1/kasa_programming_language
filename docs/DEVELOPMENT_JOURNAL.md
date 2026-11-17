# Kasa — Engineering Development Journal

**Purpose:** Record *what actually changed*, *what was verified*, *what failed*, *what we discovered*, and *what is still unknown*. This is the canonical living progress record for Kasa development; do not substitute a feature plan or a green badge for evidence.

**Last reviewed:** 2026-11-17  
**Reference branch:** `main`  
**Open high-risk work:** [PR #16 — experimental KBC1 portable bytecode](https://github.com/fosterb1/kasa_programming_language/pull/16)  
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
| Browser JavaScript engine | Runs Kasa directly without Pyodide | **89/89 direct JS checks** on the educational-example branch before its merge: 26 programs, 27 expected errors, 15 remainder cases, nine examples, 11 location cases, one EOF check | These are direct runtime checks, not a complete Node/browser integration suite |
| Native compiler/VM | C++20 source to **in-memory bytecode**, VM alpha | Native lexer **13/13** focused checks in standalone executable; CTest **1/1** on lexer-only staging build | Full CMake/VM integration suite not rerun in the current isolated test environment |
| Source-coordinate consistency | Unicode code-point positions and browser supplementary-letter tokenization | Browser source-coordinate fixtures and native lexer smoke | Does not establish strict malformed UTF-8 handling or every Unicode identifier category |
| Linguistic governance | [Policy](./LANGUAGE_RESEARCH_POLICY.md), [audit](./TWI_KEYWORD_AUDIT.md), [evidence register](./keyword_evidence.json) | Automated vocabulary-change guard implemented | All legacy tokens still need human linguistic review; publication links are not speaker approval |
| Offline education | Browser interpreter; nine tracked root `.kasa` examples including cashbook, stock and school fees | The three new examples executed correctly in the browser | Pilot with Ghanaian teachers/learners not yet performed |
| Independent local verification | [Runner](../scripts/verify_local.py) and [guide](./INDEPENDENT_TESTING.md) | **6/6 runner unit tests** passed in focused prior verification | Full profile requires complete checkout with Python, Node, CMake, C++ |
| Disk-based portable bytecode (KBC1) | **Not merged into main** | **5/5 standalone C++20 serializer smoke groups passed**, with exact source blobs matched; full native VM/adversarial test suite **not yet executed** | Draft format is not stable, authenticated or security-audited |
| Native WebAssembly | Source bridge and build scripts | Source-level and worker simulation checks from previous milestones | No verified real Emscripten-generated WASM running in the browser |
| License | No `LICENSE` file | N/A | Public visibility does not grant an open-source license. Owner decision required |

**Progress percentages are planning judgments**, not a substitute for these verifiable milestones.

## Development entries

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
- **Verification:** Using GNU g++ 14.2 and strict C++20 flags, **5/5 focused standalone checks passed** after the fix. All three staged source files matched the corresponding PR #16 GitHub blob hashes.
- **Evidence:** [Full independent verification record](./verification/2026-11-17-kbc1-serializer-smoke.md).
- **Remaining risk:** This is not the complete native VM/compiler build; full `test_bytecode.py` and source→file→VM round-trips still need execution before PR #16 can merge.

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
| R-01 | Full native KBC1 CMake build and hostile-input test suite not run on extracted branch | **High** | Standalone serializer now **5/5 passed**; keep PR #16 open and run full VM/CLI tests with saved report | Open |
| R-02 | GitHub Actions jobs terminate before steps, apparently affected by account/runner constraints | Medium | Keep CI out of critical path; [issue #12](https://github.com/fosterb1/kasa_programming_language/issues/12); local runner | Open |
| R-03 | Three language engines differ on numeric ranges/formatting and resource limits | High | RFCs and shared conformance corpus; explicit known incompatibilities | Open |
| R-04 | KBC1 CRC32 checks corruption but not malicious modification | **High for untrusted distribution** | No trusted/signed bytecode claims; sandboxing and stronger review required | Open |
| R-05 | Twi keywords lack final native-speaker/dialect and educator review | High for educational adoption | Evidence policy, structured audit, Asante/Akuapem review | Open |
| R-06 | Lack of explicit open-source license | Medium | Owner chooses license and adds `LICENSE`; do not claim legal open-source status | Open |
| R-07 | No classroom pilot validating proposed accessibility advantage | Medium | Small documented, ethically designed learner/teacher pilot | Open |

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
- Complete KBC1 source→file→VM round-trips and corruption tests, if shipping bytecode files.
- Real WASM artifact/browser verification, if advertising native WebAssembly.
- Clear learner-facing tutorials, error messages, and language/cultural review.
- License choice, versioning and release checklist; no stable release until these are met.
