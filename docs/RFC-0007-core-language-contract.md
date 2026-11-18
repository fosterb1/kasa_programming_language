# RFC-0007 — Kasa 0.4 Core Language Contract

**Status:** Candidate reference contract, not stable language standard.  
**Date:** 2026-11-18  
**Based on:** Python `src/kasa/core.py` and browser `playground/kasa-runtime.js` in the main revision after PR #30.  
**Tests:** [Shared candidate fixtures](../tests/conformance_language_contract.json), tested in JavaScript directly; Python/native/KBC1 execution is a separate release gate.  
**Governance:** [Twi lexical-review policy](./LANGUAGE_RESEARCH_POLICY.md). This RFC freezes no new words and does not certify any existing Twi vocabulary.

## Purpose

Provide a reproducible **language contract** for humans, tooling and future AI coding assistants. Implementation details of Python/JavaScript/C++ are not the language specification; programs should use Kasa concepts, not host-language back doors. This document describes the existing subset, **not modules, classes, money types, CSV, imports, async or package APIs**. Unspecified features are not implicitly supported.

## Lexical conventions

- UTF-8 source; indentation is cosmetic; a newline generally terminates each statement.
- `#` starts a comment through the end of its line.
- Case-sensitive identifiers, names and keywords. The contextual conditional marker `a` remains a normal identifier except after the `sɛ` condition.
- Integer literals and binary64 decimal literals; string literals, lists, `nokware`, `atoro` and `hwee`.
- Existing reserved keywords are `ka`, `ma`, `sɛ`, `anyɛ_saa_a`, `mpɛn`, `bere_a`, `dwumadie`, `sanma`, `awiei`, `nokware`, `atoro`, `hwee`, `ne`, `anaa`, `ɛnyɛ`, `gyae`, `toa_so`. They remain under linguistic review.
- The initial built-in names are `bisa`, `tentɛn`, `nɔma`, `nsɛm`, not ordinary grammar keywords.

## Statements and blocks

| Form | Meaning |
|---|---|
| `ka EXPR` | Print display text and a newline |
| `ma NAME = EXPR` | Assign current environment binding |
| `ma LIST[INDEX] = EXPR` | Mutate a valid zero-based list item |
| `sɛ COND a … [anyɛ_saa_a …] awiei` | Strict-Boolean branch |
| `mpɛn COUNT … awiei` | Repeat non-negative integer number of times |
| `bere_a COND … awiei` | Loop while condition is strictly Boolean true |
| `dwumadie NAME(PARAMS) … awiei` | Declare lexically scoped function |
| `sanma [EXPR]` | Return from a function; empty return yields `hwee` |
| `gyae` / `toa_so` | Break / continue inside current loop |
| `EXPR` | Evaluate a standalone expression |

Nested blocks are terminated with explicit `awiei`. Whitespace indentation does not establish scope. Function parameters must be distinct. An inner function captures its declaration-time environment (lexical scope), not the caller's local variables.

## Expression precedence and associativity

Highest to lowest:

1. Calls `f(...)` and list indexing `a[...]`
2. Unary negation `-` and strict-Boolean negation `ɛnyɛ`
3. `*`, `/`, `%`
4. `+`, `-`
5. Relational comparisons `<`, `<=`, `>`, `>=`
6. Equality `==`, `!=`
7. Boolean AND `ne`
8. Boolean OR `anaa`

Binary operators are left-associative. Direct comparison chaining (e.g. `1 < 2 < 3`) is invalid; use independent comparisons with an explicit Boolean operator. Parentheses override precedence. Boolean `ne` and `anaa` short-circuit, evaluating the right operand only when needed.

## Data semantics

- Booleans are **not** numbers: `nokware == 1` is `atoro`; conditions and logical operators demand `nokware` or `atoro`.
- Integers and binary64 decimals compare numerically, including inside lists. Mixed arithmetic is still subject to binary64 precision; neither type is a production currency type. Kasa's native implementation currently limits integers to signed 64-bit, while Python and JavaScript have larger integer capabilities. This difference **blocks unconditional cross-runtime guarantees**.
- Lists are mutable, zero-indexed, and support nesting. Negative and out-of-range indexes raise `IndexError`; indexes must be integers. List equality compares corresponding elements recursively.
- Printing `hwee`, `nokware`, `atoro` produces those labels. Printing a list uses brackets and comma-separated representations. Exact decimal formatting is covered separately by [decimal fixtures](../tests/conformance_decimal_display.json) and remains a native parity gate.
- An absent explicit function return yields `hwee`. Function calls check arity and recursion budgets.
- Assignments inside a function belong to that function's local environment; a newly introduced local variable is not automatically global.

## Built-in contracts (existing alpha)

- `bisa([prompt])`: read one input line; optional prompt must be text.
- `tentɛn(text_or_list)`: get text length or list length.
- `nɔma(number_or_numeric_text)`: convert supported numeric text to a number.
- `nsɛm(value)`: obtain Kasa's display text for a value.

Exact Unicode text-length rules, prompt/newline handling, extreme numeric limits, errors, and bound behaviors require additional parity tests. Do not promise full host-platform portability before those pass.

## Diagnostics and resource safety

Source coordinates are intended to be one-based Unicode code-point positions. Syntax errors, type errors, index errors, unknown names, division by zero, execution-limit violations, and resource-limit violations are runtime/diagnostic categories. Cross-runtime message text is **not stable**; callers should not parse English wording as a normative API. Browser, Python and native have differing output budgets and integer ranges; these are tracked mismatches, not deliberately endorsed differences.

## Contract test policy

The 12-case JSON corpus covers successful evaluation and category-specific rejections. Each runtime must execute these cases with identical successful stdout; failures must have matching **error categories**, not necessarily identical English wording. Testing only the JavaScript runtime cannot certify native/KBC1 behavior. Do not present this RFC as a stable specification until the candidate fixtures pass Python, native direct and compiled KBC1 and all unresolved semantics have written decisions.

## Next decisions (before Kasa 0.5 stabilization)

1. Standardize supported integer range, overflow and mixed integer/decimal arithmetic.
2. Standardize error categories and resource limits across source and KBC1.
3. Define Unicode normalization and exact source/text coordinate handling.
4. Specify module loading and imports separately **before** implementing them.
5. Decide functions, serialization and host IO interfaces for library/AI tooling.
6. Seek educational and linguistic review; no new Twi tokens without approved evidence.

This preserves Kasa's goal: independent, offline-capable, Twi-first education leading to useful general-purpose programming, without pretending that an unfinished cross-runtime alpha is already 1.0.

### Browser output budget and Unicode (2026-11-18 clarification)

The browser JavaScript runtime now enforces its **64,000-character** output cap using **Unicode code points**, not JavaScript UTF-16 code units, for both `ka` printed lines and `bisa` prompts. This agrees with Kasa's documented Unicode text-length convention and preserves the difference between Unicode characters and UTF-16 storage units. A newline counts as one character. This is an **engine-specific resource cap**, not a stabilized cross-runtime limit: Python currently does not apply the same cap and the native C++ VM counts output **UTF-8 bytes**. A release-level cap must be specified and tested independently before claiming identical Python/JS/native/KBC1 behavior.

### Output budget convergence candidate (2026-11-18)

The Python reference, JavaScript browser interpreter and native C++ VM have been updated to enforce an **output budget of 64,000 Unicode code points per program invocation**. Both `ka` output (including its trailing newline) and prompts written by `bisa` consume the same budget. The output operation checks the remaining quota *before writing* and raises a Kasa `ResourceError` without writing that operation's text if the quota would be exceeded. Earlier output remains visible. A new Python `Interpreter.run(...)` invocation resets its accounting. For native UTF-8 output, code-point counting assumes validated UTF-8; arbitrary malformed bytes from host input are **not** yet subject to a shared decoding and normalization policy.

Eight shared source fixtures cover Twi multi-byte letters, emoji, cumulative prompt and print output, and exact ASCII upper boundaries. **All eight pass direct JavaScript execution, and the extracted native counting helper passed seven isolated assertions with sanitizers under both GCC and Clang.** Python pytest, the linked native C++ VM, KBC1 and full Node integration have not been run on this branch; this remains a *candidate* cross-runtime contract, not release certification.
