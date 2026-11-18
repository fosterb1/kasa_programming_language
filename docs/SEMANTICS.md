> **Historical design notes (2026-11-17).** For the currently maintained language-contract candidate, see [RFC-0007](./RFC-0007-core-language-contract.md). Examples and limits in this earlier note may predate the modern native/runtime fixes; do not treat this as the normative stable 1.0 specification.

# Kasa language semantics — shared conformance subset (draft)

The Python tree-walker, browser JavaScript interpreter, and C++ bytecode VM
implement the **Kasa language**, but the implementation language is not the
Kasa language specification. The shared fixtures at
[`tests/conformance/cases.json`](../tests/conformance/cases.json) are an
executable, backend-independent subset of the language contract.

## Confirmed common subset

- UTF-8 source; Twi keywords and identifiers (`ɛ`, `ɔ`).
- Case-sensitive names; `ma` binds in the current environment.
- Integers, decimals, text, `nokware`/`atoro`, `hwee`, heterogeneous lists.
- Operators have conventional precedence; `/` returns a decimal; `%` requires
  integers; Booleans are never numeric operands.
- Conditions require a Boolean, and `ne` / `anaa` short-circuit.
- `sɛ` headers end in `a`, blocks end in `awiei`.
- `mpɛn`, `bere_a`, `gyae`, `toa_so`, and lexically scoped functions are
  supported; list indices start at zero.
- `bisa()`, `tentɛn()`, `nɔma()` and `nsɛm()` are built in.
- Kasa source does not execute via Python `eval()`, shell commands or
  JavaScript `Function()`.

## Open semantic issues — not silently standardized

1. **Integer range:** the native C++ VM uses signed 64-bit integer arithmetic;
   Python supports larger integers, while the JS VM has its own bounds.
2. **Decimal text formatting:** native floating-point output may differ from
   Python and JavaScript in the last significant digits.
3. **Unicode column numbers:** UTF-8 byte positions, Unicode scalar values and
   grapheme clusters are not yet fully harmonized across backends.
4. **Resource budgets:** desktop and web defaults differ intentionally.
5. **Error text:** tests currently require common error **categories**, not
   identical natural-language diagnostics.

Until these are resolved with specification RFCs, the word “compatible” only
means that the documented shared conformance suite passes, not that every
possible program behaves identically.

## Run shared fixtures

```bash
python -m pytest -q tests/conformance/test_python.py
node --test tests/conformance/test_browser.cjs
cmake -S native -B build && cmake --build build
python native/tests/test_shared_conformance.py build/kasa-native
```
