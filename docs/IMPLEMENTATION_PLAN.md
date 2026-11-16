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
