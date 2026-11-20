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
### 2026-11-19 — Group 0.2 Windows catalog validation accepted

- **User Windows evidence** after checkout `d7aa810`: `python -m pytest -q tests/test_validate_kasa_catalog.py tests/test_link_kasa_stdlib.py` → **36 passed, 3 skipped in 1.28s**.
- `python scripts/validate_kasa_catalog.py` → `PASS: catalog schema, source identities, declared exports and dependency graph`; reported modules: `collections` with `kasa_count_equal`, `kasa_contains`, and `math` with `kasa_abs`, `kasa_clamp`, `kasa_sum`.
- **Classification:** G0.2 manifest validation accepted for tested Windows scope. The three skipped tests were not executed; their protections are not thereby independently verified.
- **Next stage:** G0.3 namespace/import design and incremental implementation, keeping approved Kasa language vocabulary stable, preserving native/KBC1 parity and requiring explicit shared conformance evidence. No runtime language-level import is implemented by this milestone.


### 2026-11-19 — Group 0.2 implemented: Kasa library manifest and validation

- **Changed:** Added `stdlib/catalog.json`, `scripts/validate_kasa_catalog.py`, `tests/test_validate_kasa_catalog.py`; extended `docs/GROUP_0_MODULE_CONTRACT_PLAN.md`.
- **Implementation:** Exact allowlisted math/collections source paths; SHA-256 identities based on canonical UTF-8 LF files; explicit public-function exports validated against Kasa's parser AST; dependency-first ordering with missing/cyclic dependency rejection. Detects duplicate JSON keys/module IDs/exports, invalid metadata, malformed UTF-8, linked paths, source tampering and top-level side effects.
- **Verification:** Computed both source SHA-256 hashes with an independent local Python calculation, cross-checked reconstructed Git blob IDs against `main`; inspected Kasa `parse(source, filename)` signature. **New unit suite and Windows CLI run have not yet been executed**; do not count those tests as passed.
- **Limits:** Catalog verifier is a read-only development tool, not a Kasa-language import system, namespaces, runtime dependency resolver, sandbox or package signature scheme. G0.1 source linker still uses independent pinned allowlist; integration to come after a verified contract.
- **Next gate:** Windows `python -m pytest -q tests/test_validate_kasa_catalog.py tests/test_link_kasa_stdlib.py` and `python scripts/validate_kasa_catalog.py`; fix actual failures before building runtime syntax.


### 2026-11-19 — Group 0 source-linker native/KBC checkpoint accepted; module contract design opened

- **Windows user verification** on revision `19624e4`: 17 passed, 2 symlink checks skipped; linked source executed in Python and native with exact stdout `300 / 2 / nokware`; native compilation reported success; `check-bytecode` produced no error; compiled KBC1 ran with the same output.
- **Decision:** G0.1 source-linker happy path accepted. This is not full G0 completion; no true import grammar or namespace implemented.
- **Next specification:** `docs/GROUP_0_MODULE_CONTRACT_PLAN.md` sets experimental catalog/export/dependency contracts, explicit namespace rules, and G0.2–G0.5 runtime stages. No implementation or testing is claimed for those stages.
- **Next gate:** build and independently test G0.2 module manifest validator before introducing syntax across runtimes.


### 2026-11-19 — Group 0 linker successfully verified on Windows

- **User's Windows 10 validation:** Following fix `bccfeda`, `python -m pytest -q tests/test_link_kasa_stdlib.py` reported **17 passed, 2 skipped in 0.41s**. Skips are platform symlink permissions, not passed security assertions.
- **Actual linked application:** `python scripts/link_kasa_stdlib.py --app stdlib/demos/group0_sample.kasa --module math --module collections --output build/stdlib-linked/group0-demo-001.kasa` created a new `.kasa` program without overwriting existing files.
- **Actual runtime:** `python -m kasa run build/stdlib-linked/group0-demo-001.kasa` emitted exactly `300\n2\nnokware\n` on Windows.
- **Clarification:** An initial pytest invocation accidentally combined two terminal commands and was rejected at CLI argument parsing; subsequent correctly separated commands passed.
- **Not yet run for this generated file:** Native C++ direct source execution and KBC1 serialization. This milestone is pinned local source linking, **not** true language-level imports, namespace isolation, package manager or sandbox.
- **Next:** Check generated program with native executable, optionally compile/check/run KBC1; then develop namespace declaration and import contract with shared regressions.


### 2026-11-19 — Group 0 first implementation: pinned library source linker

- **Added:** `scripts/link_kasa_stdlib.py` (strict allowlist `math`/`collections`, Git blob content pins, LF/Windows CRLF canonicalization, no-overwrite output restricted to `build/stdlib-linked`);  `stdlib/demos/group0_sample.kasa`; `tests/test_link_kasa_stdlib.py`; [full milestone rundown](./GROUP_0_MODULE_LINKER_CHECKPOINT.md).
- **Safety features tested in code:** unknown/traversal module names, duplicate selection, altered library contents, function collisions, UTF-8/size checks, symlink/junction refusal and existing-file preservation. **Test suite has been added but not yet executed on Windows; do not mark it green.**
- **Scope:** prelinker assembles allowlisted, pinned source before execution. It is neither a full Kasa import system nor namespace isolation, an untrusted-code sandbox, cryptographic publisher authentication or a binary distribution feature.
- **Next gate:** User Windows test output, run generated source via Python/native, then design true namespaces and module declarations; move to G1 only after G0 acceptance tests.


### 2026-11-19 — Phase 8 balanced stdlib: Windows native compatibility confirmed

- **User-reported Windows tests:** 12/12 Python and 12/12 JavaScript combined finance + experimental stdlib fixtures passed. The existing Phase 8A native source/KBC1 finance driver reported **6/6 passed**. The user subsequently confirmed **PASS** for `python native/tests/stdlib_foundation_conformance.py build/kasa-local/Release/kasa-native.exe`.
- **Interpretation:** the six portable stdlib scenarios passed in native source and KBC1 according to the user; no raw stdout or exact current Git commit was supplied for that final driver, so retain this as user-reported evidence, not independent same-revision attestation.
- **Next gate:** reusable module namespace and loading design. No module/import language syntax or executable loader has been shipped yet. Preserve old language behavior and run full parity when introducing new syntax.


### 2026-11-19 — Balanced Phase 8 standard library prototypes

- **Decision:** User selected balanced general-purpose and financial/data library development, not finance-only. Phase 8 roadmap updated; Phase 9 browser/Academy remains after Phase 8.
- **Implemented:** `stdlib/experimental/math.kasa` (`kasa_abs`, `kasa_clamp`, `kasa_sum`), `stdlib/experimental/collections.kasa` (`kasa_count_equal`, `kasa_contains`), six shared fixtures and independent Python/Node + native/KBC1 test drivers. These are source-level reusable definitions assembled by the test runner, **not importable modules** or new built-in keywords.
- **Independent verification:** 12/12 Python and 12/12 JavaScript direct tests passed (six existing pesewa tests and six new general/finance-integrated scenarios) at commit `c357520`. A later remote native attempt was **not run** because the test environment lacks CMake; the native driver is pending on the Windows developer binary. Do not count that as a pass or failure.
- **Known limits:** Native minimum int64 absolute value and overflowing sum are not covered by checked arithmetic; clamp requires valid ordered bounds. No currency type, CSV I/O, real module loader, package manager, or production finance contract.
- **Next:** Windows native source/KBC1 run; then specify safe reusable module loading/import and explicit argument/overflow error contracts before declaring a standard library.


### 2026-11-19 — Phase 7 Windows parity checkpoint and Phase 8A initial financial examples

- **Windows evidence:** User supplied full `build/kasa-local-verification.json` after non-dry-run parity verification on clean commit `5067c5b4d7326d11c7f230dc9d03f059d798afca`: **11/11 stages passed**, Python 191/191, Node 237/237, native 24 conformance + 14 KBC1 cases, 9,999/9,999 decimal and 10,080/10,080 numeric differential. WASM not requested; does not establish universal parity.
- **New Phase 8A:** Six cross-runtime fixtures in `tests/conformance_finance_subunits.json`, Python/Node direct test runners, and native source/KBC1 command-line comparison driver. No syntax additions or actual standard finance library API. Integer pesewas only, within current portable numeric limits.
- **Independent execution:** 6/6 Python and 6/6 Node cases passed on commit `8c6ad5c`. Native Phase 8A fixture run still requires explicit compiled verification. No financial-data file I/O introduced.
- **Follow-up:** Validate native/KBC1 on Windows, then design currency-tagged amounts, scale, overflow and CSV schemas before implementing Phase 8 finance APIs. Keep Phase 9 playground/Academy after Phase 8 according to the approved roadmap.


### 2026-11-18 — Prepare real-WASM Netlify publishing and Academy CMS embedding

- **New:** `netlify.toml` and `scripts/netlify_build.sh` build genuine Emscripten native WASM and fail closed if unavailable; static deploy contents extracted to `dist/netlify`. The Netlify iframe policy is restricted to the academy's current HTTPS domain.
- **Independently checked:** Linux Emscripten 3.1.69 successfully ran the Netlify build script. Generated native `kasa-native.wasm` was 491,371 bytes, with compiled JS glue, worker and full static site assets in the publish directory. This is **build readiness, not verified live Netlify deployment**.
- **Companion integration:** Kasa Learning Academy receives an admin-editable `Website Settings → Playground Settings → Netlify Playground URL` field and dynamic embedded `/playground` route. Existing lesson editors are preserved.
- **Manual account action:** Reuse the existing Netlify site `sunny-griffin-784c12` and update its deployment/build settings. See [Netlify deployment instructions](./NETLIFY_DEPLOYMENT.md). Production site URL must be taken from the hosting dashboard; no deployment has been performed by this PR.
- **Remaining:** live hosted end-to-end confirmation, actual Firefox/WebKit, offline PWA, mobile layout and expanded WASM differential corpus.



### 2026-11-18 — First actual native WebAssembly execution in Chromium

- **Independently built:** Existing C++ native Kasa WASM bridge compiled using Emscripten 3.1.69; real `kasa-native.wasm` was **491,371 bytes** with 23 WebAssembly exports and 44 imports. The generated binary and JS glue were packaged using `playground/build_site.py --require-wasm`; they remain generated artifacts, not committed source.
- **Verified real browser:** New `scripts/verify_real_wasm_browser.py` ran the WASM-enabled site ZIP in actual headless Chromium. Native WASM loaded in a real Web Worker; forced-native run, syntax check, `bisa()` input and error handling passed; four real Twi program outputs matched the separately forced JavaScript engine. Forced JavaScript fallback was also verified. See [real WASM browser evidence](./verification/2026-11-18-real-wasm-browser.md).
- **Prior limitation resolved in narrow scope:** This is **real WebAssembly execution**, not merely simulated Node WASM-protocol tests or a static binary check. **Still open:** WebKit/Firefox/Edge, mobile, offline PWA, public hosting, WASM KBC2/Boost bigint support, broader differential and release security gates. Progress percentages unchanged.



### 2026-11-18 — Real Chromium JavaScript playground execution and local editor workflow

- **Changed:** The browser editor now opens local `.kasa` files (UTF-8, 50 KB cap), saves only source drafts in localStorage with a Reset control, and never saves program input. Engine labels now make it clearer that JavaScript works immediately while native WebAssembly is conditional on an actual compiled/deployed module.
- **Independently tested:** `scripts/verify_browser_playground.py` launched a real headless Chromium browser and local HTTP server on Linux. A true Web Worker ran the Hello Ghana program, checked syntax without execution, executed imported Unicode code, displayed runtime errors, verified source persistence and input non-persistence, downloaded a source file, and reset the draft. **PASS**. Existing Node browser/placeholder WASM-protocol checks: **234/234 passed**.
- **Clarification:** Real browser JavaScript success is **not** real native WebAssembly success. The latter still requires Emscripten compilation, bundle validation and in-browser native execution. See [browser evidence](./verification/2026-11-18-real-browser-playground.md).
- **Remaining:** Actual browser WASM, Firefox/WebKit/Edge, real offline PWA, accessibility and mobile UX tests, release packaging. Estimates unchanged.



### 2026-11-18 — Windows hardening confirmed by user; macOS release runner introduced

- **Windows user report:** Following PR #55, user confirmed the three-target experimental CTest command **PASSED** (RFC-0008, KBC2 SHA golden, 320 malformed-loader checks). Exact Windows logs/SHA not independently available; record it as user-reported.
- **Created, not macOS-executed:** `scripts/verify_macos_release.py` defines six ordered checks for native macOS: canonical parity, commit-pinned audit, full checks, opt-in KBC2 configure/build, and three KBC2 CTest targets. Requires clean Git SHA and an actual Darwin `arm64` or `x86_64` host. Produces per-stage JSON and fails on any step or changing Git revision.
- **Independent non-macOS verification:** Python source compiled on Linux; `--dry-run` produced the planned six stage commands, and direct Linux execution returned exit code 2 without generating a false macOS report. **No macOS tests were run.** See [macOS release gate](./verification/MACOS_RELEASE_GATE.md).
- **Still blocked:** Real macOS Intel/Apple Silicon execution, browser/WASM, long fuzzing, licensing, packaging and signed builds. Keep 90% 0.4 implementation and ~35% 1.0 estimates unchanged.



### 2026-11-18 — KBC2 hardening: Windows golden evidence, malformed files, Linux sanitizers

- **Windows user evidence:** After PR #54, user reported the two-target MSVC/Boost KBC2 golden/integration test **passed**. Interpret as user-run Windows byte-for-byte identity for ten fixed cases, not a reviewed raw Windows artifact or exact audited SHA.
- **New:** Added 320 deterministic checksum-stale/checksum-repaired KBC2 mutations and loader check-only test (`scripts/verify_kbc2_robustness.py`), registered as opt-in CTest `kasa_kbc2_loader_robustness`. Malformed archives are never executed; CRC-updated mutations may validate successfully if structurally legal.
- **Independent Linux tests:** GCC Release **3/3** opt-in CTest targets, including 320-case mutation run; Clang 21 Debug with AddressSanitizer + UndefinedBehaviorSanitizer and leak detection **3/3** targets passed with no sanitizer reports in this workload.
- **Remaining:** Windows hardening rerun, macOS, coverage-guided fuzz, sanitizer variation, trust model and release packaging. See [hardening verification record](./verification/2026-11-18-kbc2-hardening.md). Existing 90% Kasa 0.4 checklist and ~35% Kasa 1.0 estimate unchanged.



### 2026-11-18 — Begin cross-platform KBC2 byte-for-byte verification

- **Source:** Recorded user-reported successful Windows MSVC+Boost opt-in KBC2 integration test (exact binary report/commit not uploaded); avoid calling it independent certification.
- **Changed:** New `tests/kbc2_golden_sha256.json` with ten SHA-256/byte-length pairs from Linux GCC Release for RFC-0008 KBC2 output; standalone nonmutating `scripts/verify_kbc2_golden.py`; opt-in CMake CTest. This checks byte-for-byte serialized identity, not merely output equality. UTF-8 temp input is written in binary mode to avoid Windows CRLF rewrite.
- **Independently verified:** Linux 10/10 golden fixtures matched and **2/2** opt-in CTest targets passed, including previously introduced KBC2 conformance tests.
- **Pending:** Run the golden CTest on Windows and compare to Linux reference fingerprints; macOS and real-browser verification, sanitizers, fuzzing, packaging. No change to planning percentages.



### 2026-11-18 — KBC2 version-gated large integer serialization

- **Change:** New explicitly requested `compile-kbc2` CLI mode on the **opt-in** `KASA_ENABLE_BIGINT_VM=ON` build; `compile` still emits KBC1. KBC2 header uses new magic `KBC2` and unsigned version 2; constants add canonical sign-and-magnitude tag 5 (sign byte, LE 16-bit length, big-endian unsigned magnitude, 16,384-bit cap). KBC1 remains byte-for-byte unchanged and all legacy value tags are unchanged. KBC2 is refused by non-bigint native builds.
- **Tested on experimental Linux GCC + Boost:** **10/10** RFC-0008 source programs compiled to KBC2, reloaded and matched expected output. Integration CTest **7/7 methods** passed (including malformed-file tests with valid refreshed checksums, KBC1 backwards compatibility, correct refusal to store big constants in KBC1, and resource guard checks). Default repo checks: **10/10 parity**, **18/18 full** passes.
- **Discovery:** First mutation test searched for magnitude length bytes in the wrong endian order; that was a test-fixture error, corrected, and rerun green. All regression claims distinguish opt-in from default build.
- **Open:** MSVC and macOS, cross-platform binary golden fixtures, sanitizers, broader hostile-file fuzzing and review for public stable format. See [experimental KBC2 specification](./KBC2_FORMAT.md).



### 2026-11-18 — Opt-in native VM execution of arbitrary-precision integers

- **Implemented on branch:** Added an optional `KASA_ENABLE_BIGINT_VM=ON` switch requiring Boost.Multiprecision, leaving normal native builds and the KBC1 wire format unchanged. The experimental native `Value` holds a `cpp_int`; lexer/parser accepts large integer literal magnitude; VM supports exact integer promotion, arithmetic, signed remainder, `nɔma`, output, nested list equality and integer/binary64 mixed comparisons. Big repeat counts and indexes are explicitly constrained.
- **Acceptance evidence:** Independently built experimental C++20 native VM under GCC 15 on a complete Linux checkout; **all 10/10** shared RFC-0008 source cases passed. Standalone opt-in CTest integration **1/1** passed (the 10 cases, KBC1 existing-format constant roundtrip with arithmetic promotion, explicit refusal to serialize a big literal into KBC1, and a ResourceError limit case). The normal default runtime passed **10/10** parity stages and **18/18** full-profile stages.
- **Important restriction:** This opt-in feature does not update KBC1 to encode large literal constants. Existing KBC1 files still work, but compiling a source program with a large literal constant is refused until versioned KBC2 is implemented. Default behavior remains the 64-bit native alpha.
- **Unverified:** Full opt-in differential numeric suite, MSVC and Windows Boost dependency, sanitizers and explicit resource-limit abuse testing. Keep scorecard estimates unchanged until a release-grade portable bigint backend and KBC2 exist.



### 2026-11-18 — Verified Windows alpha runtime and experimental RFC-0008 integer backend

- **Windows milestone (user-operated):** After merged PR #50, user supplied MSVC native conformance output showing **24/24 test methods passed**, and Windows parity screenshot showing **10/10 stages passed**. The user subsequently reported a clean SHA audit and **18/18** full-profile passes; the final JSON files and exact Windows SHA were not supplied for independent validation. Previously, Python tests passed **239 with 4 skipped**, and Node browser/WASM-protocol tests passed **234**. See [provenance-scoped Windows verification record](./verification/2026-11-18-windows-user-validation.md).
- **Experimental big-integer foundation:** Added `native/include/kasa/big_integer.hpp` with Boost.Multiprecision `cpp_int` backend, exact decimal parsing, bounded add/subtract/multiply/floor-remainder, and a candidate **16,384-bit** resource cap plus **1,000-digit** text cap. Added `native/tests/big_integer_smoke.cpp` and an **OFF-by-default** `KASA_BUILD_BIGINT_EXPERIMENT` CMake option requiring Boost headers only when explicitly enabled. The existing KBC1, native Value/VM and default alpha build are unchanged.
- **Test discovery:** Initial experimental smoke used `assert`, which Release builds can compile out. Replaced with runtime checks that cannot be disabled by `NDEBUG`, rebuilt the Release probe, and observed **1/1 CTest** passing. Independently executed the existing full checkout on Linux: **10/10 parity** and **18/18 full** profile stages passed with the experimental source present but not linked into the VM.
- **Open:** Big integers are not yet usable in `.kasa` programs through the native VM or serialized KBC1. Windows Boost availability and experimental MSVC build, KBC2 versioning, float comparisons and limiting expensive operations remain unverified. Keep progress estimates unchanged.



### 2026-11-18 — Native MSVC stdout CRLF portability after real Windows testing

- **Windows user evidence:** On the Windows Build Tools 2026 / MSVC build of Kasa, native conformance comparisons repeatedly failed because `stdout` was `"value\\r\\n"` instead of Python's `"value\\n"`; source location `twi_with_crlf` reported line 3 instead of line 2. This affected both native source and KBC1 execution, numeric comparisons, Unicode output-count tests and CRLF-source locations. The 24-test Windows native conformance command reported **187 subtest failures**; most had this common line-ending cause.
- **Fix A:** In `native/src/main.cpp`, set Windows CRT stdout and stderr handles to binary mode via `_setmode(_fileno(...), _O_BINARY)`, so Kasa output matches LF semantics rather than Windows CRLF translation. Stdin is unchanged and `bisa()` still removes terminal CR as designed.
- **Fix B:** In `native/tests/conformance.py`, write source test files using `write_bytes(source.encode("utf-8"))` instead of `write_text`, preventing Windows universal newline conversion from changing a preexisting `\\r\\n` into `\\r\\r\\n` and shifting Unicode source coordinates.
- **Independent regression:** The patched source branch passed **10/10** full-checkout Linux parity stages and **18/18** full-profile stages including native compiler and KBC1. **MSVC/Windows native conformance has not yet been rerun on this patch**; user must pull the merged change and rebuild before Windows success can be claimed.
- **Checkpoint status:** Keep Windows native parity and full cross-platform release certification open until the Windows rerun is verified; the earlier Kasa 0.4 Linux alpha implementation scorecard and stable 1.0 readiness estimates do not change.



### 2026-11-18 — Clean merged-main Linux alpha parity checkpoint verified

- **Merged source tested:** `cbce6a6c6c20b9e994086fddbbeac12d42a45f71` ([PR #48](https://github.com/fosterb1/kasa_programming_language/pull/48)); independent disposable Linux checkout, **clean** before and after the run.
- **Actual execution:** Python pytest **243/243**; Node semantic **227/227**; ten-stage `--profile parity` **10/10**, audited successfully using `--expected-commit cbce6a6c6c20b9e994086fddbbeac12d42a45f71`; full `--profile full` **18/18**. The full checks include native C++20 build, native source/VM and serialized KBC1 conformance, lexer/bytecode mutation/serializer smokes and numeric differential probes.
- **Scope:** This verifies the **implemented Linux Kasa 0.4 portable subset**, not full arbitrary-precision native integers/KBC1, real-browser WASM, Windows/macOS installation or untrusted-code security. See [complete evidence record](./verification/2026-11-18-linux-full-parity.md).
- **Scorecard:** Linux alpha subset parity checkpoint #9 is now verified; **Kasa 0.4 implementation checklist 9/10 = 90%**. Stable **Kasa 1.0 readiness remains ~35%**. These are planning rubrics, not time or measured code coverage estimates.
- **Next release gate:** Cross-platform and real-browser/packaging checks; separately start staged native bigint implementation under RFC-0008.



### 2026-11-18 — First clean-checkout full Python/Node/native/KBC1 verification baseline

- **Infrastructure breakthrough:** A temporary, disposable Linux sandbox cloned Kasa directly from GitHub after the original local environment was unable to resolve the GitHub hostname. The repository can now be tested as a complete checkout independently of GitHub Actions.
- **Actual baseline failure:** At `e9ec7ffe4715d0ec38cb685243fd7d6793206447`, `python -m pytest -q` returned **242 passed / 1 failed**. The stale full-profile runner test expected 16 stages although the runner defines 18. The 10-stage parity profile passed 9 and failed the native Python conformance stage due to a CRLF fixture with *internal* carriage return. Raw native stdout bytes were correct (`b'A\\rB\\n'`), but `subprocess.run(..., text=True)` automatically translated its internal `\\r` into a newline in the conformance harness. The executable was not faulty.
- **Corrections:** `native/tests/conformance.py` now captures raw process bytes and explicitly decodes UTF-8 for native source and KBC1 runs, preserving carriage returns. Updated the full verification plan assertion to 18 stages. Added `.gitignore` rules for `.venv/`, `build/`, Python caches, pytest caches and editable-install artifacts so local tests do not dirty an otherwise clean Git checkout.
- **Independently executed on branch commit `974f9d0d2b73804fcdc4f297716169cddcd9ef64` (clean Linux sandbox):** **243/243** complete Python pytest passed; **227/227** Node browser semantic tests passed; `scripts/verify_local.py --profile parity` passed **10/10 stages**; `scripts/audit_parity_report.py --expected-commit 974f9d0d2b73804fcdc4f297716169cddcd9ef64` passed; `scripts/verify_local.py --profile full` passed **18/18 stages**, including the native C++20 build, lexer/serializer/mutation smoke, decimal and integer differential probes, source VM conformance and KBC1 bytecode round trips/rejections. Parity JSON records matching clean Git source revision before and after execution.
- **Still open:** Verify again on the **merged main commit**, not just the reviewed branch. Native big integers and KBC1 arbitrary-integer encoding remain unsupported; those deliberate future acceptance cases are not part of the native-success gate. macOS/Windows, actual WASM browser execution and package installation are also unverified. Audited JSON is reproducible evidence, not cryptographic attestation.



### 2026-11-18 — Native Windows CRLF stdin parity

- **Observed divergence:** Native `std::getline()` strips the newline but retains `\\r` for `bisa()` input ending in `\\r\\n`, while Python and JavaScript discard terminal carriage returns. Native programs could echo an invisible extra carriage return and fail text equality checks on Windows-style input.
- **Fix:** Native `bisa()` drops only terminal `\\r` characters after `std::getline()`; internal carriage returns are preserved. Added eight shared input cases and registered them in Python pytest, Node JavaScript, native source VM/KBC1, and the independent parity runner. No changes to Kasa grammar.
- **Verified independently:** **106/106** direct JavaScript shared cases passed (including eight CRLF fixtures). The isolated C++ `getline`/terminal-CR handling passed **6/6 with GCC and 6/6 with Clang**, each compiled with ASan+UBSan.
- **Not verified:** Full Python/Node test runners, linked native C++/KBC1 bytecode execution and a new audited 10-stage parity report. GitHub checkout remains inaccessible in the local container because DNS cannot resolve `github.com`. No readiness percentage change.



### 2026-11-18 — Concurrent decimal literal fix reconciled; signed subnormal regression

- **Integration discovery:** PR #44 landed the native decimal-literal underflow fix on `main` while a second equivalent PR #45 was being developed. PR #45 was **closed without merging** after GitHub reported conflicts, rather than replacing newer `main` source and documentation.
- **Merged into `main`:** [PR #46](https://github.com/fosterb1/kasa_programming_language/pull/46), squash commit `346b4c736f2577ae515782d430e59cb42a507b6a`.
- **Additional retained work:** One previously absent **negative finite subnormal literal** fixture added to `tests/conformance_decimal_display.json`; it is automatically picked up by the existing Python, JavaScript, native-source and KBC1 source conformance suites. The existing C++ parser fix from PR #44 remains untouched.
- **Executed:** **98/98** direct JavaScript shared source cases pass with the consolidated 19-case decimal corpus. Previously executed isolated GCC and Clang C++ `std::strtod` conversion probes passed; **no linked native VM/KBC1 or full Python suite on this consolidated branch**.
- **Gate:** A clean-checkout parity profile and audited report are still required. Do not double-count duplicate PRs or increase readiness estimates.



### 2026-11-18 — Native parser decimal-literal underflow

- **Reproduced gap:** The earlier `nɔma("...")` patch switched native conversion to `std::strtod`, but the native *source parser* still used `std::stod` for `DECIMAL` literals. GCC 14.2 and Clang 17 sanitizer probes confirmed that `std::stod` throws `std::out_of_range` for extremely small, valid decimal spellings that `std::strtod` correctly rounds to zero or a finite subnormal value. Python/JS source parsers already accept the corresponding decimal literals.
- **Merged:** [PR #44](https://github.com/fosterb1/kasa_programming_language/pull/44) into `main`, squash commit `c8fd971e7126cde7e58fc96141037aff41e6f379`.
- **Changed:** Native `parser.cpp` now uses `std::strtod` for lexer-validated decimal tokens, checks that the whole input was consumed and rejects nonfinite values. The common decimal display fixture gains three source-level cases (positive and negative values rounding to zero, one positive subnormal). These existing fixture registrations already cover Python, Node, native source and KBC1 pathways; no grammar change.
- **Evidence:** **97/97 direct JavaScript shared source cases** passed (including three new tests). Isolated C++ comparison probe succeeded under **GCC 14.2 and Clang 17 with ASan/UBSan** (2 underflow magnitudes per toolchain). Native linked parser/VM, KBC1 execution, Python pytest, Node test runner and the 10-stage parity profile were **not executed** on this revision.
- **Open risks:** Actual linked native/KBC1 conformance; locale-sensitive C decimal parsing, platform behavior and other numeric corner cases. Progress rubric remains at 80% / ~35%. No new Twi vocabulary or modules.



### 2026-11-18 — Strengthened parity-report audit integrity (verification tooling)

- **Discovered weakness:** The previous report auditor checked stage names, success counts, clean state and a 40-digit SHA, but **did not check that stage commands were the actual intended tests**. Ten reported `python -V` checks could be labeled as successful parity stages and accepted.
- **Merged into `main`:** [PR #43](https://github.com/fosterb1/kasa_programming_language/pull/43), squash commit `c204e190a6b6bec1b89e7a2009b74f8d8f293ca5`.
- **Change:** Auditor rebuilds its expected 10-stage command argv from the local `verify_local.plan("parity", False)` and rejects mismatches, while allowing alternate Python virtualenv interpreter paths only when the argument vector is intact. Runner now records Git source revisions **before and after** execution; auditor rejects a moving or unknown revision. Optional `--expected-commit` binds the audit to an externally chosen SHA. Six regression tests added for counterfeit argv, command substitution, changed/missing final revision, commit mismatch and virtualenv portability; prior dirty-diagnostic test updated.
- **Verification scope:** Source-level review and registration only. Full `python -m unittest tests/test_audit_parity_report.py`, Python/Node/native/KBC1 integration, and an actual clean-checkout 10-stage parity report **were not run** on this revision. No verified full-parity claim; percentages unchanged.
- **Limit:** An auditor reading JSON **cannot cryptographically attest execution** or rule out intentionally forged records. Keep trusted execution, release provenance and code review separate. Existing reports without `source_revision_after` are now rejected and must be regenerated with the updated runner.



### 2026-11-18 — Arbitrary-precision integer direction and release gate

- **Merged into `main`:** [PR #42](https://github.com/fosterb1/kasa_programming_language/pull/42), squash commit `cee26f5b0b945a0bbc119237548eaf2544802721`.
- **Decision:** Adopt exact arbitrary-precision integers (bounded by explicit resource controls) as the *intended language semantics*, keeping native signed 64-bit support explicitly experimental pending upgrade. Do not restrict Python/JavaScript integers to int64 as a short-term parity workaround.
- **New specification:** [RFC-0008](./RFC-0008-arbitrary-precision-integers.md) defines target mathematical behavior, signed remainders, conversion, precision, a small-integer fast-path option, memory/DoS safeguards and a mandatory versioned KBC1 evolution. It distinguishes candidate 16,384-bit and 1,000-literal-digit limits from certified standards.
- **New fixtures:** 10 shared exact integer source cases in `tests/conformance_arbitrary_integers.json`, registered with Python pytest and the Node browser suite; Python included in independent parity profile. Native/KBC1 expected-success runs must wait for implementation rather than fabricate a passing result.
- **Evidence actually executed:** All **94/94** direct V8 shared JavaScript cases passed, including the 10 new arbitrary-integer cases plus 84 existing cases. Python pytest, the complete Node test runner, native C++/KBC1 and full local parity/full profiles have not been run on this revision. A green direct interpreter result is not full release certification.
- **Next:** Obtain an intact local checkout or equivalent controlled execution for the baseline 10-stage parity/18-stage full verification, then implement the native big-integer representation and versioned serialization behind conformance tests.



### 2026-11-18 — Native signed int64 minimum source parsing

- **Defect:** Native parse rejected `ka -9223372036854775808` while Python/JavaScript accepted it, because `std::stoll` parsed an out-of-range positive magnitude before unary minus.
- **Merged into `main`:** [PR #41](https://github.com/fosterb1/kasa_programming_language/pull/41), squash commit `7cf550fb4748d08bfa0906c3af3afe2795804adf`.
- **Fix:** When unary minus immediately precedes the exact decimal magnitude of `2^63`, after stripping leading zeros, native parser emits a signed `int64_t` minimum literal. The surrounding unary grammar is unchanged; values beyond `int64_t` are still unsupported in native. Five shared fixture programs cover minimum value, leading zeros, addition, remainder, and equality with `nɔma`.
- **Test registration:** Python pytest, Node JS, native source and KBC1 serialized execution, and the independent parity profile now cover these fixtures.
- **Executed evidence:** **84/84** direct JS shared conformance cases passed on the branch. **Not executed:** Full Python pytest, Node full runner, linked native parser/VM or KBC1 round trip. Native change requires the full local parity gate and may reveal integration issues. No additional syntax, Twi vocabulary or license decisions.
- **Ongoing:** Choose an explicit large-integer policy in [issue #39](https://github.com/fosterb1/kasa_programming_language/issues/39) rather than silently restricting Python and JS.



### 2026-11-18 — Native decimal underflow and subnormal portability

- **Reproduced:** `std::stod` throws `std::out_of_range` for valid binary64 decimal inputs below its normal range, even when they should round to signed zero or a valid subnormal. Python and JavaScript accept the corresponding `nɔma` inputs.
- **Implemented:** Native `nɔma` retains the strict ASCII decimal grammar, parses valid decimals with `std::strtod`, validates that the input was consumed and rejects non-finite overflow as `ResourceError`. Added four shared fixtures (positive/negative tiny values, nonzero subnormal, huge overflowing decimal); existing Python/JS/native source/KBC1 fixture registrations pick them up automatically. **Merged into main** in [PR #40](https://github.com/fosterb1/kasa_programming_language/pull/40), squash commit `45e001147bc147ef2e36996a8b44b9cb104f539f`.
- **Actually verified:** **79/79** shared JavaScript cases passed in direct V8 execution (20 numeric conversion, 8 output budget, 15 decimal display, 12 core contract, 24 historic). **13/13** isolated C++ decimal parsing and classification assertions passed using each of GCC 14.2 and Clang 17 with address/undefined sanitizers.
- **Not verified:** Full Python pytest, complete Node runner, linked native VM, KBC1 round trip, C numeric-locale interactions and full cross-runtime parity. Native `int64_t` versus Python/JS big integers remains open in [issue #39](https://github.com/fosterb1/kasa_programming_language/issues/39). Keep scorecard percentages unchanged.




### 2026-11-18 — Close native `nɔma` permissive-number parsing gap

- **Reproduced:** Native C++ `std::stod("1.25e2")` accepts exponent notation, whereas Kasa's Python and JS `nɔma` reject that input with `TypeError`. Native `std::stoll` overflow was wrongly caught by `catch(...)` and labeled invalid numeric text (`TypeError`) instead of range exhaustion.
- **Fix:** Native VM now checks the strict ASCII decimal spelling before host conversion, and catches `std::out_of_range` to raise `ResourceError`. Added 16 common valid/invalid conversion fixtures across Node browser, Python pytest and native source/KBC1 conformance, including the local parity profile. No Twi grammar change. **Merged into `main`** as [PR #38](https://github.com/fosterb1/kasa_programming_language/pull/38) (squash commit `538a476b7fe17a5ddceb315a021a2e0d7c95f09a`); outstanding numeric portability is tracked in [issue #39](https://github.com/fosterb1/kasa_programming_language/issues/39).
- **Verification:** **16/16** numeric fixtures + **59/59** prior shared checks passed in direct JS execution (**75/75** total). **16/16** C++ regular-expression cases and one native overflow classification condition passed isolated sanitizer probes under GCC 14.2 and Clang 17. Full Python, Node test runner, linked native VM and serialized KBC1 tests were not executed.
- **Open:** Large-int `nɔma` conversion differs because native uses int64 while Python/JS use larger integers; extremely small decimal underflow and host-text whitespace policy also need cross-runtime specification. Do not mark full parity achieved.



### 2026-11-18 — Output-limit semantics standardized in candidate runtime source

- **Design decision:** 64,000 Unicode **code points** per Kasa program execution, shared between printed lines (`ka`, including newline) and text prompts (`bisa`). Exceeding the cap raises `ResourceError` **before** emitting the overflowing operation; already emitted text remains available. Native UTF-8 string validation on hostile input remains a distinct issue.
- **Merged to `main`** via [PR #37](https://github.com/fosterb1/kasa_programming_language/pull/37), squash commit `9745b04e9445265d7ac21c8b7768c01a79994f5a`. Originally implemented on `fix/output-budget-parity-20261118`: Python output writer with counter/reset, JavaScript output quota error normalized to `ResourceError`, and native C++ text/prompt sink using UTF-8 code-point counting. Added 8 source-level shared fixtures and registered them in Python pytest, JavaScript Node tests and native source/KBC1 conformance; included Python fixtures in local parity profile. Twi grammar and vocabulary unchanged.
- **Verification actually executed:** **8/8** shared output-budget fixtures in the exact repository JavaScript interpreter; isolated native byte/code-point/output quota helper **7/7** assertions compiled and run using GCC 14.2 and Clang 17 with ASan/UBSan. No complete Python interpreter pytest, linked native VM/KBC1 or Node test runner executed on this branch in this environment.
- **Outstanding acceptance gate:** Run full local 10-stage parity and 18-stage full verification on the exact merged revision, resolve any mismatch, and verify UTF-8 input validity policies. Do not mark full Kasa 0.4 cross-runtime parity or production sandbox safety complete.




### 2026-11-18 — Browser Unicode output-budget precision fix

- **Status:** **Merged into `main`** via [PR #36](https://github.com/fosterb1/kasa_programming_language/pull/36), squash commit `90f2b0f015ed6a0491b8dce9de886b218527b059`. Full current-commit Node runner, Python, native C++ and KBC1 integration are not claimed; follow-up standardization tracked in [issue #35](https://github.com/fosterb1/kasa_programming_language/issues/35).
- **Reproduced defect:** A program building 32,768 emoji code points and printing them was incorrectly rejected as over 64,000 characters because JS checked UTF-16 `.length` (65,537 code units including newline) rather than Unicode code points (32,769). `bisa` prompts shared this bug.
- **Changed:** Added a single `appendOutput` path tracking Unicode code-point count for both `ka` and `bisa`. Five test cases added for below/above-cap Unicode output and prompt behavior plus ASCII compatibility. No Twi words or grammar changed.
- **Actually verified:** **5/5** focused direct interpreter checks on the updated source; **51/51** shared browser regression fixtures (15 decimal, 12 core-contract, 24 historical conformance) passed in direct V8 execution.
- **Unresolved:** Native uses UTF-8 byte budgeting while Python has no equivalent stdout budget; current JS source/input budgets also differ across engines. This patch does **not** close cross-runtime semantics, security, or release gate. Next: define common output budget units and run native/Python conformance in a complete checkout.


### 2026-11-18 — Open pull request backlog cleared (all branches integrated)

- **Status:** GitHub reported **zero open pull requests** after the integration merges. The conflicting draft native PR [#31](https://github.com/fosterb1/kasa_programming_language/pull/31) was merged through conflict-resolving [PR #33](https://github.com/fosterb1/kasa_programming_language/pull/33), merge commit `890b745145db47fbb30d68c80d3acaad9e6b0959`. The old platform [PR #7](https://github.com/fosterb1/kasa_programming_language/pull/7) was merged through reconciling [PR #34](https://github.com/fosterb1/kasa_programming_language/pull/34), merge commit `6dea0471420fc673635854bd7523023384f24ecb`. Both original PRs are marked `merged=true` by GitHub.
- **Conflict strategy:** Kept current Python/JS/native/KBC1 implementations and newest RFCs. Preserved original branch ancestry, integrated tested native formatter components and carried forward compatible older platform features without overwriting current runtimes.
- **Verified checks:** Native formatting component GCC/Clang and differential records described above; integrated JS executed 26/26 root programs and 24/24 legacy semantic scenarios; static PWA/VS Code checks 11/11. No independently executed full merged-`main` pytest, Node runner, CMake/VM or KBC1 integration report in this task.
- **Release status unchanged:** Kasa 0.4 full parity, native/browser WASM, platform packaging and open-source licensing **remain open**. Merging development code is not a certification of runtime interoperability or production safety. The scorecard stays at **80%** alpha implementation / **~35%** stable maturity.




### 2026-11-18 — Resolving legacy PR #7 without reverting modern runtimes

- **Status:** Reconciled platform expansion on `merge/platform-legacy-reconciled-20261118`. The original PR #7 had genuine conflicts with newer Kasa compiler, JavaScript interpreter and KBC1 code; all current implementations were retained instead of replacing them with older copies.
- **Changed:** Imported the 10 runnable historical exercises, VS Code extension prototype, offline service worker/manifest/icons, web distribution packaging support, optional Python CLI `--explain` diagnostics, shared 24-case Python/JS conformance corpus and earlier tutorial/release guidance. Added all root examples to the unified 26-case golden-output corpus. Kept RFC-0007 and RFC-0005 as the current contract and bytecode design references.
- **Independent verification:** The actual repository JavaScript interpreter ran all **26/26** root examples successfully, the 16 success + 8 failure legacy conformance scenarios passed **24/24**, and **11/11** static VS Code/offline wiring checks passed. These are direct JavaScript execution plus source/JSON checks, **not** a full Node test runner or real-browser offline PWA run.
- **Risk:** Python pytest, native C++/KBC1 and actual browser offline/WASM integration for this merged source remain unverified on a full checkout. Imported Python/Node tests are executable checks but not claimed green. VS Code extension remains unpublished. No payment or licensing action.
- **Next gate:** Run complete parity/full local profiles, exercise actual offline installation in browsers, and validate editor runtime before stable release. Do not close Step 1 merely because the old PR merges.



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

### 2026-11-18 — Conflict resolution for open native precision PR #31

- **Status:** Native precision files reconciled with the newer RFC-0007 language contract on a dedicated integration branch. The original PR branch had merge conflicts; newer `main` test registrations and documentation were retained.
- **Changed:** Imported the C++20 binary64 formatting helper, native formatter smoke/differential probes, shared 15-case decimal fixture, CMake registration, Python/native/KBC1 conformance registrations, report auditor updates and 10-stage parity / 18-stage full verification plan. Preserved the merged 12-case core language contract tests.
- **Evidence:** JavaScript interpreter executed the integrated **15 decimal + 12 contract cases, 27/27 passing**. Previous native component testing under GCC, Clang and sanitizers passed 18/18 and 9,999 seeded finite differential values matched Python. **No full native VM/KBC1 test on this integration branch was executed.**
- **Caveat:** Merge is a repository integration step, **not** release acceptance. Step 1 remains open pending full clean-checkout parity/full profile and audited reports. No new Twi keywords or license decision.


## 2026-11-20 — G0.3 read-only namespace planning checkpoint

- **Status:** New source and tests committed to `main`; user Windows execution pending.
- **Changed:** `scripts/plan_kasa_modules.py`, `tests/test_plan_kasa_modules.py`. Command-line `--use module:alias` validation builds a deterministic, non-executing dependency and export plan from the pinned catalog.
- **Verification:** GitHub source was inspected before editing. A fresh container checkout was attempted but blocked by DNS failure resolving github.com; **no pytest execution of these additions is claimed**.
- **Decision:** Keep unapproved Twi import vocabulary and dot-member syntax out of the parser until reviewed; no global linker injection is treated as real module isolation.
- **Limits:** No runtime namespace binding, JS/browser parity, native compiler/VM or bytecode module semantics. No security sandbox asserted.
- **Next gate:** Windows `python -m pytest -q tests/test_validate_kasa_catalog.py tests/test_plan_kasa_modules.py`, then `python scripts/plan_kasa_modules.py --use math:m --use collections:c`. Record actual output and any failures before implementing grammar.


## 2026-11-20 — Windows verification of G0.3 planning (user evidence)

- **Status:** Windows verification completed for G0.2 catalog and G0.3 read-only planner at `c881578`.
- **Results:** Catalog/linker suite **36 passed, 3 skipped**; catalog validator **PASS**; catalog/planner suite **31 passed, 1 skipped**; planner JSON returned correct independent `collections:c` and `math:m` binding metadata, dependency order and no capability grants.
- **Interpretation:** These are overlapping test collections, not 67 unique test cases. Skips are unresolved platform-specific checks, not failures or passes.
- **Open work:** Real module declaration syntax, namespace environments, member resolution, browser parity and native/KBC1 support are still pending. Nothing here establishes secure sandbox isolation.
- **Next gate:** Review Python `src/kasa/core.py` grammar/scoping and provide an explicit import/member-access proposal with regression cases before parser changes.


## 2026-11-20 — G0.3 Python isolated closure environments

- **Status:** Implemented on `main`, user Windows tests pending.
- **Changed:** `src/kasa/modules.py` adds a pure-AST namespace primitive with private module lexical environments and read-only explicit export mapping. `tests/test_module_namespace_isolation.py` adds cases for private exports, duplicate declaration rejection, independent module closures and instruction budget.
- **Verification:** Reviewed actual parser, `Environment`, `Interpreter.execute` and `Interpreter.evaluate` implementations. An attempted checkout for independent pytest failed because the container cannot resolve github.com; **these new tests were not run**.
- **Constraints:** This is an internal Python component, not approved language import syntax; it does not read sources, check hashes itself, or bind alias names into user programs. Caller must prevalidate the G0.2 catalog. Browser, native and bytecode untouched.
- **Next gate:** Windows regression tests; then catalog-verified binder and scoped member resolution with explicit compiler/bytecode version strategy.


## 2026-11-20 — macOS Intel local verification and catalog binder test coverage

- **User-supplied macOS evidence:** Intel Darwin x86_64, Python 3.15.2, Node 26.13.1, CMake 3.31.2 and Clang available; Emscripten not installed. NetShare Git access succeeded using a one-command HTTP proxy at `192.168.49.1:8282`. Working tree clean at `0f62645`.
- **Actual Mac tests:** `bash scripts/mac_dev.sh quick`: **7 passed, 0 failed, 0 not run**. Focused `python -m pytest -q tests/test_module_namespace_isolation.py tests/test_plan_kasa_modules.py tests/test_validate_kasa_catalog.py`: **40 passed**.
- **New change after user verification:** `tests/test_bind_kasa_catalog.py` adds catalog-backed namespace execution and negative tests for changed source and invalid exports. **This new binder suite has not yet been run.**
- **Limitations:** This quick profile does not certify a full macOS native KBC1 pass or actual Kasa import language syntax. Academy checkout not found under `~/Projects`.
- **Next validation:** `git -c http.proxy=http://192.168.49.1:8282 pull --ff-only` then `python -m pytest -q tests/test_bind_kasa_catalog.py tests/test_module_namespace_isolation.py tests/test_plan_kasa_modules.py tests/test_validate_kasa_catalog.py`.


## 2026-11-20 — User-reported macOS G0.3 binder acceptance

- **Status:** User reported **"all passed"** after following instructions to run `python -m pytest -q tests/test_bind_kasa_catalog.py tests/test_module_namespace_isolation.py tests/test_plan_kasa_modules.py tests/test_validate_kasa_catalog.py` and `bash scripts/mac_dev.sh quick` on an Intel Mac with NetShare proxy.
- **Evidence boundary:** Exact pytest pass/skip totals, commit SHA tested and full command output were **not supplied** with this report. This is user-reported success, not independently reproduced CI or an observed complete test log.
- **Interpretation:** Proceed with the next G0.3 design slice on the basis of this reported local acceptance; do not claim Kasa source-level import syntax is implemented.
- **Next gate:** Design and review a backwards-compatible import/member syntax, with explicit alias collision, export visibility, missing module and cross-runtime diagnostics tests. Maintain no new unapproved Twi keywords.


## 2026-11-20 — Twi-first learning diagnostics preview (Python-only)

- **Status:** Implemented on `main`; new Mac tests pending. Existing language keywords and runtime error strings are unchanged by default.
- **Changed:** `src/kasa/learning_diagnostics.py`, opt-in `learner_language="tw"` in `playground/runner.py`, `tests/test_learning_diagnostics.py`, and `docs/TWI_FIRST_LEARNER_DIAGNOSTICS.md`.
- **Behavior:** For recognized `KasaError` categories, opt-in Python playground calls attach a separate structured learner card. The original error category/location/message remains byte-for-byte unchanged. Cards have an explicit `draft_needs_human_review` status, provisional Twi concept label, and English teaching guidance; unknown errors are not guessed.
- **Verification:** New tests committed but **not independently run**. Existing user Mac quick profile and namespace binder success predate this change.
- **Language policy:** The card labels are **not approved Twi translations**; obtain Asante/Akuapem and educator review before any public-facing Academy or browser UI integration.
- **Open scope:** This is not the Kasa import/member syntax milestone and it does not modify JS/native/KBC1 runtimes. Browser-native parity and real learner testing remain pending.
- **Next gate:** On Mac run `python -m pytest -q tests/test_learning_diagnostics.py tests/test_playground.py` and `bash scripts/mac_dev.sh quick`; report actual output, then resume Group 0.3 import grammar/member semantics.


## 2026-11-20 — G0.3 Twi-first import syntax research (non-executing)

- **Status:** Implementation committed to `main`; new tests pending execution on user's Mac.
- **Changed:** `scripts/study_kasa_module_syntax.py`, `tests/test_module_syntax_study.py`, `docs/GROUP_0_TWI_IMPORT_SYNTAX_RESEARCH.md`.
- **Behavior:** Standalone English-placeholder grammar research validates single module aliases, explicit member-name shape, duplicate aliases/modules, unsafe names, missing exports and unknown aliases. This is a test-only static contract and does not parse/execute Kasa applications.
- **Ghanaian-language decision:** No new Twi keyword was added or accepted. The eventual import/member vocabulary must undergo the existing evidence policy and Asante/Akuapem/educator review before public adoption. English placeholders are not final syntax.
- **Verification:** Code and test cases have been pushed, but `python -m pytest -q tests/test_module_syntax_study.py tests/test_bind_kasa_catalog.py` has **not yet been observed running on this commit**.
- **Known limits:** Does not implement user-facing imports, production AST, Python runtime alias binding, JavaScript parity, native compiler/KBC1 support, or a package registry.
- **Next gate:** Mac focused pytest plus quick profile; after success, proceed with reviewed AST design and a fail-closed Python import implementation.


## 2026-11-20 — Module-member AST execution foundation (Python experiment)

- **Previous user Mac evidence:** `tests/test_module_syntax_study.py tests/test_bind_kasa_catalog.py` — **23 passed in 0.77s**. `bash scripts/mac_dev.sh quick` — **7 passed, 0 failed, 0 not run**, checked out at `6b4a6af`. The earlier blank command output was not a hang; terminal subsequently returned to the prompt.
- **New code:** `src/kasa/module_execution.py` provides opt-in `ModuleAwareInterpreter`, evaluates trusted `module_member` AST nodes through explicitly exported module functions, prevents obvious alias shadowing and preserves existing call/step budgets. `tests/test_module_member_execution.py` covers public/private access, alias safety, deterministic independent scopes and loops.
- **Verification for this new code:** **Not run yet** on Mac or other independently observed runtime; pending focused pytest and quick profile.
- **Ghanaian language policy:** No new Twi word, English import keyword, dot syntax, browser language surface or officially approved vocabulary added. This remains a Python AST experiment, not a working Kasa source import implementation.
- **Risks/limits:** Future runtime integration must combine catalog-pinned loading, alias ownership, parser AST and bytecode contracts without resetting execution budgets on module initialization. Runtime API is not a sandbox or proof against malicious crafted ASTs.
- **Next gate:** `python -m pytest -q tests/test_module_member_execution.py tests/test_module_namespace_isolation.py tests/test_bind_kasa_catalog.py tests/test_module_syntax_study.py` then `bash scripts/mac_dev.sh quick` on the updated Mac checkout. Record exact outputs before proceeding with syntax.


## 2026-11-20 — Mac Group 0.3 member-execution acceptance + catalog integration

- **User-supplied Mac evidence at `b2c61f4`:** `python -m pytest -q tests/test_module_member_execution.py tests/test_module_namespace_isolation.py tests/test_bind_kasa_catalog.py tests/test_module_syntax_study.py` → **46 passed in 0.64s**. `bash scripts/mac_dev.sh quick` → **7 passed, 0 failed, 0 not run**. Git fast-forward from `6b4a6af` to `b2c61f4`.
- **Acceptance scope:** Experimental Python module-member AST evaluation passes its focused local regression gate. Neither accepted Twi import vocabulary nor executable source-level import syntax exists yet.
- **New work after that acceptance:** `scripts/configure_kasa_modules.py` combines the G0.2 catalog validator, G0.3 alias planner, SHA-256-verified source binder and `ModuleAwareInterpreter` behind one opt-in developer API. `tests/test_configure_kasa_modules.py` tests real math/collections calls via synthetic AST, private/unknown exports, duplicate aliases, no global name injection, pre-execution shadowing checks and normal parser rejection of the English placeholder syntax.
- **Verification of new integration suite:** **Pending Mac execution**. Do not represent committed tests as passed.
- **Risks and limits:** Driver intentionally remains Python-only and uses trusted synthetic AST; it is not a real Kasa import statement or security sandbox. User-visible Twi import grammar still requires linguistic review; JS/browser, native and KBC1 semantics remain open.
- **Next Mac gate:** `python -m pytest -q tests/test_configure_kasa_modules.py tests/test_module_member_execution.py tests/test_bind_kasa_catalog.py` then `bash scripts/mac_dev.sh quick`.


## 2026-11-20 — User-verified Mac catalog-to-runtime G0.3 integration

- **Checkout:** User fast-forwarded `main` from `b2c61f4` to `9f22df0` through the NetShare per-command proxy.
- **Focused test command:** `python -m pytest -q tests/test_configure_kasa_modules.py tests/test_module_member_execution.py tests/test_bind_kasa_catalog.py`.
- **Observed result (user transcript):** **27 passed in 0.45s**, with no skipped or failed cases reported.
- **Quick profile:** `bash scripts/mac_dev.sh quick` — **7 passed, 0 failed, 0 not run**, including Python pytest/CLI and JavaScript runtime/worker/playground syntax and protocol diagnostics.
- **Acceptance:** The experimental catalog-backed Python module-aware interpreter is verified on the user's Intel macOS test environment for this targeted scope. The previous `46 passed` result was on `b2c61f4` and must not be combined as distinct test coverage.
- **Open blockers:** Actual source-level Kasa import declarations and dotted member grammar not implemented; no approved Twi import vocabulary; no JS/native/KBC1 module parity. Local quick profile is not full native/WASM certification.
- **Next work:** Design the syntax-neutral parser AST contract first, record Twi terminology proposals separately for human review, then add end-to-end source examples only when grammar and cross-runtime compatibility are explicitly gated.
