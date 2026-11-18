# Implementation plan

This milestone is an **initial functioning interpreter (0.1.0)**, not the complete version 1.0 specified in `Kasa Programming Language.md`.

## Delivered in 0.1.0

- Unicode-aware lexer, tokens with source locations, structured diagnostics
- Pratt expression parser and recursive-descent statement parser
- Arithmetic, booleans, text, variable assignment, lists and zero-based indexes
- Conditions, counted loops, while loops, break/continue
- Functions, lexical scope, return values, basic recursion-depth protection
- Four standard built-ins: `bisa`, `tentɛn`, `nɔma`, `nsɛm`
- Resource budgets (steps, function calls, container/string sizes)
- CLI for `run`, `check`, `repl`; pip-installable package; smoke examples/tests

## New language governance (2026-11-17)

New Twi grammar and built-ins now require an auditable research record and independent linguistic evidence, with fluent Asante and Akuapem review before acceptance. The current token inventory remains `legacy_review_pending`; see [policy](./LANGUAGE_RESEARCH_POLICY.md), [human-readable audit](./TWI_KEYWORD_AUDIT.md) and [structured evidence](./keyword_evidence.json). An offline test enforces documentation/change control. The test does **not** certify native-speaker approval.

## Kasa 0.4 — Exact integer/decimal comparison semantics (merged in alpha)

A cross-runtime bug was discovered on 2026-11-18: both the JavaScript and C++ engines could round a large integer through binary64 when comparing it to a decimal. The Python reference does not. The implementation in [PR #23](https://github.com/fosterb1/kasa_programming_language/pull/23) was merged into main; it preserves exact integer-versus-decimal comparisons, including nested-list equality, without adding Twi tokens.

- **18** shared fixtures in `tests/conformance_numeric_comparisons.json`, checked in browser JS (all **18/18** passed), registered for Python pytest and both native direct/KBC1 conformance.
- **107/107** total direct JS regression checks passed on the feature branch.
- **18/18** standalone C++20 numeric smoke checks passed with GNU g++14.2, and again under ASan/UBSan. **3,000/3,000** deterministic mixed int64/binary64 pairs matched Python numerical comparisons.
- **Not yet verified:** full VM compilation/integration, new Python pytest cases and compiled KBC1 fixtures on the merged revision. See [precise evidence report](./verification/2026-11-18-mixed-numeric-comparison.md).
- **Tradeoff:** Native still has 64-bit integer limits; exact comparison does not make mixed integer/decimal *arithmetic* exact. Monetary teaching examples continue to use integer pesewas.

## Focused local reference-parity profile

- Added `python scripts/verify_local.py --profile parity` for an **eight-stage** Python, JavaScript, native VM and KBC1 compatibility check locally, including a deterministic **10,080-case** Python/C++ numeric differential. Its output is machine-readable, includes the source commit and dirty-worktree status, and never treats a missing build as success.
- **Verification:** The earlier extracted command-planning logic passed four focused plan-shape checks and the Git-revision helper passed five local scenarios (Python 3.13.5). The numeric comparison differential **passed 10,080/10,080 cases under both GCC and Clang** independently; this does not certify full VM behavior. The complete native parity execution against the current revision remains **unverified**, as do the 58 Python/KBC1 fixtures and 18 recent numeric fixtures together.
- Evidence: [updated numeric differential record](./verification/2026-11-18-numeric-differential.md) and [original seven-stage parity profile record](./verification/2026-11-18-parity-profile.md). Keep GitHub Actions manual-only; do not infer a green hosted CI check.

## Cross-runtime conformance milestone

- Signed integer `%` semantics are now defined in [RFC-0003](./RFC-0003-remainder-semantics.md). The JavaScript and native VM implementations are updated to agree with Python for negative operands.
- Shared fixtures `tests/conformance_remainder.json` are consumed by Python, browser JavaScript, and native conformance harnesses. Full cross-runtime acceptance and GitHub Actions remain to be verified in a working environment.
- Further work: document numeric overflow/large-integer behavior, error category consistency, Unicode handling, execution quotas and stable runtime diagnostics.

## Unicode diagnostics (Kasa 0.4, pending integration verification)

[RFC-0004](./RFC-0004-unicode-source-locations.md) proposes one-based Unicode code-point columns across the Python, JavaScript and C++ engines. The updated browser lexer and native lexer have shared regression fixtures in `tests/conformance_source_locations.json`; Python already uses code-point indexing. Direct browser verification passed all eleven cases, while full native and Python test-suite runs remain outstanding. This milestone does not add Twi keywords or implement strict UTF-8 validation.

## Kasa 0.4 — Native bytecode portability and practical computing

- [KBC1 RFC-0005](./RFC-0005-kbc1-portable-bytecode.md) proposes experimental disk-based native bytecode; `native/src/bytecode.cpp`, CLI commands and adversarial tests have been isolated from PR #7 into a review branch.
- [Practical computing focus](./KASA_PRACTICAL_COMPUTING_FOCUS.md): Twi-first offline educational computing, especially market cashbooks, stock control and school finance. This is a hypothesis to pilot with learners, **not yet a proven edge**.
- Independent KBC1 alpha: **7/7** standalone serializer checks passed; **14/14** full native bytecode integration tests passed under GCC 14.2, Clang 17 and GCC AddressSanitizer/UndefinedBehaviorSanitizer on 2026-11-17, with exact GitHub blob hashes. Discoveries fixed: NaN writer/reader mismatch, source-column and aggregate nested instruction limits, and function/closure environment reference-cycle leaks. See [complete report](./verification/2026-11-17-kbc1-native-integration.md). Full Python/native parity, complete CTest suite and cross-platform testing remain pending.
- A separate deterministic KBC1 mutation smoke test ran 2,000 checksum-adjusted inputs with ASan/UBSan and no reported sanitizer errors (1,349 rejected, 651 structurally accepted). CRC32 is not a signature; full VM/fuzzing/security verification remains outstanding.
- Independent full-profile runner includes native KBC1 round-trip and malformed-input tests. A complete CMake native binary build and targeted integration suite passed on exact development files; full Python/Node, all CTest and WebAssembly checks remain separate release gates.
- **Next conformance work (in development):** additional Python-reference comparisons of `.kasa → .kbc → native VM` output, input cases, signed remainder and safe compile-time rejection of malformed Unicode/source code. These additional tests are **implemented but not yet executed with a full native checkout**.

## Remaining before 1.0

- Full coverage of every acceptance case in the engineering specification
- Thorough stress and adversarial resource-limit testing (including huge integers)
- Complete tutorial, teacher guide, API/grammar reference, and 15+ runnable examples
- Linguistic review of proposed Twi vocabulary by fluent speakers/teachers
- License decision and release engineering

## Implementation choices

- `a` is the conditional-header marker, but remains an identifier elsewhere.
- Negative list indexes are rejected to keep zero-based list semantics obvious.
- Lists are mutable via `ma list[index] = expression`.
- Keywords and errors are case-sensitive; diagnostics are currently English.
- Blocks end with `awiei`; indentation is cosmetic.
- `kasa check` parses but never runs source code.
- No Python code translation, `eval()`, or `exec()` is used.

## Kasa 0.4 — Browser decimal text-format parity repair (2026-11-18)

The JavaScript interpreter previously used ECMAScript decimal-formatting thresholds, producing output such as `1e-7` for a Python-reference output of `1e-07`, `0.00001` instead of `1e-05`, and `10000000000000000.0` instead of `1e+16`. A targeted browser display fix adds Python-like scientific-notation thresholds, exponent zero-padding and signed-zero preservation without changing arithmetic or Twi vocabulary. **12 new display fixtures and 129 total direct JavaScript checks passed** in isolated V8 execution using exact connected-GitHub source. This does not establish complete Python/native/KBC1 parity or a full Node test-runner pass. The [verification record](./verification/2026-11-18-browser-decimal-display.md) documents exact scope and the blocked full-checkout gate. Keep the 80% / ~35% score unchanged until the full cross-runtime milestone is independently verified.
