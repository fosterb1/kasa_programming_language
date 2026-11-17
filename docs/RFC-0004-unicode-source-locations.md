# RFC-0004 — Unicode-aware source coordinates

**Status:** Proposed for Kasa 0.4; implementations and shared fixtures included, full native/Python verification pending.  
**Date:** November 17, 2026  
**Scope:** Source lexer positions and error locations only. **No Twi syntax changes.**

## Problem

The Python reference interpreter counts Unicode characters when computing 1-based source columns. Before this proposal, the C++ native lexer instead counted raw UTF-8 bytes. The JavaScript browser lexer counted UTF-16 code units, which also differs for characters outside the Basic Multilingual Plane.

As a result, a syntax error after `ɛ`, `ɔ`, or a supplementary Unicode character could point to an incorrect column in different Kasa engines.

## Proposed portable rule

1. Source line and column numbers begin at **1**, not 0.
2. Source columns count **Unicode code points** (Unicode scalar values for valid Unicode input), **not** UTF-8 bytes, UTF-16 code units, or visual grapheme clusters.
3. `\r\n`, `\r`, and `\n` represent a single logical line ending for source-location purposes.
4. A syntax error's reported column identifies the **first code point of the offending token**; end-of-file errors use the current end-of-source location.
5. Source position tracking must work with both quoted strings and Unicode identifiers.
6. This rule defines offsets only. It does **not** introduce automatic Unicode NFC normalization, confusable detection, translation, new alphabet spellings, or a change in Kasa's identifier rules.

Examples: `ka "ɔ" & 3` and `ka "🙂" & 3` both identify `&` at **line 1, column 8**, despite `ɔ` being two UTF-8 bytes and the emoji occupying four UTF-8 bytes / two UTF-16 code units.

## Implementation

- Python: existing `tokenize` advances by Python Unicode code points; no runtime behavior change required.
- C++20: `native/src/lexer.cpp` increments column for the leading UTF-8 byte of a valid encoded code point, skipping continuation bytes. The logic deliberately does **not** add an unreviewed UTF-8 validation policy.
- Browser JavaScript: `playground/kasa-runtime.js` increments column for UTF-16 code units except the low surrogate of a **valid surrogate pair**.

## Verification

The shared corpus `tests/conformance_source_locations.json` contains nine intentionally invalid source snippets, including trailing-operator EOF cases. It is consumed by:

- Python pytest: `tests/test_source_locations.py`
- JavaScript Node tests: `tests/test_kasa_browser.cjs`
- Native/Python conformance harness: `native/tests/conformance.py`

Initial direct JavaScript execution of all nine cases passed. Full pytest, Node test runner and native C++ builds must be run before a stable release claim.

## Open limitations

- Native lexer currently does **not** rigorously reject malformed UTF-8 byte sequences. This RFC does not address that.
- Source offsets are **code-point positions**; editors displaying grapheme clusters or tabs may place a caret differently. Tabs are not standardized to visual display widths.
- Unicode normalization and confusable identifier rules need a separate RFC and tests.
- Kasa's existing `KEYWORDS` are subject to the [Twi evidence policy](./LANGUAGE_RESEARCH_POLICY.md). No new Twi keyword is proposed here.

Before adoption into the 1.0 language standard, confirm diagnostic offsets with actual Python, Node and C++ builds on Windows, macOS and Linux.
