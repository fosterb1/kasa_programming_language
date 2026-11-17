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

## Cross-runtime conformance milestone

- Signed integer `%` semantics are now defined in [RFC-0003](./RFC-0003-remainder-semantics.md). The JavaScript and native VM implementations are updated to agree with Python for negative operands.
- Shared fixtures `tests/conformance_remainder.json` are consumed by Python, browser JavaScript, and native conformance harnesses. Full cross-runtime acceptance and GitHub Actions remain to be verified in a working environment.
- Further work: document numeric overflow/large-integer behavior, error category consistency, Unicode handling, execution quotas and stable runtime diagnostics.

## Unicode diagnostics (Kasa 0.4, pending integration verification)

[RFC-0004](./RFC-0004-unicode-source-locations.md) proposes one-based Unicode code-point columns across the Python, JavaScript and C++ engines. The updated browser lexer and native lexer have shared regression fixtures in `tests/conformance_source_locations.json`; Python already uses code-point indexing. Direct browser verification passed all seven cases, while full native and Python test-suite runs remain outstanding. This milestone does not add Twi keywords or implement strict UTF-8 validation.

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
