# 2026-11-18 — Browser decimal-display parity regression

**Status:** Targeted verified JavaScript runtime repair; not complete four-runtime parity.
**Source:** `playground/kasa-runtime.js` from `fix/js-decimal-display-parity-20261118` and shared fixtures at `tests/conformance_decimal_display.json`.
**Tooling:** Connected GitHub file reads; direct execution in a V8 JavaScript isolate with the exact fetched browser interpreter source. Independently checked Python 3.13.5's `repr(float)` formatting for 11 scalar values locally. No paid GitHub Actions used.

## Confirmed defect

The browser engine originally formatted Kasa binary64 values with JavaScript's
`String(Number)` exponent conventions instead of the Python reference's
binary64 text conventions.

| Kasa source | Old JavaScript stdout | Python reference-style stdout |
|---|---|---|
| `ka 1 / 10000000` | `1e-7` | `1e-07` |
| `ka 1 / 100000` | `0.00001` | `1e-05` |
| `ka 10000000000000000.0` | `10000000000000000.0` | `1e+16` |
| `ka -0.0` | `0.0` | `-0.0` |

## Repair

Changed only the browser runtime decimal display function (and its test suite).
Use scientific notation for nonzero magnitudes below `1e-4` or at least
`1e16`, normalize exponent sign and minimum two-digit width, and preserve
negative zero. Apply the same formatter for nested list values.

No arithmetic operators, currency type, parsing rules, Twi keywords, native
compiler, bytecode format or Python reference code changed.

## Verification performed

The exact source/fixture content fetched through the connected GitHub repository
was evaluated, not mocked or dry-run:

- **12/12** decimal-display edge fixtures passed in direct JavaScript execution
  (including nested lists and signed zero).
- **16/16** root example programs matched the existing golden outputs.
- **48/48** other shared fixtures passed: mixed comparisons, remainder
  successes/errors, source-location syntax checks, and reconciliation edge cases.
- **53/53** browser test-file positive and negative interpreter scenarios passed
  in direct execution with the updated runtime.

**Total: 129/129 direct interpreter checks** across these disjoint sets.
This count is **not** the Node.js full test runner, browser worker, actual browser
integration, Python pytest, CMake, native compiler or serialized KBC1 validation.

Python 3.13.5 separately reproduced reference float display values used for
the scalar cases; this is not equivalent to executing the Kasa Python interpreter.

## Remaining risk and next gate

- Full checkout is blocked because `git ls-remote` cannot resolve
  `github.com` in the independent container. GitHub connector file retrieval
  still worked. No hosted Actions job was started.
- A **separate native formatter precision discrepancy** was reproduced with a standalone GCC 14.2 C++20 probe using the formatting statements in `native/src/vm.cpp`: `1.0 / 7.0` displays `0.142857142857143`, while Python 3.13.5 prints `0.14285714285714285`. This does **not** establish full VM execution. Track it as [issue #29](https://github.com/fosterb1/kasa_programming_language/issues/29), and do not merge native code without full tests. Python/Node/native/KBC1 suites still need a real complete checkout.
- Python and ECMAScript shortest binary64 conversion behavior can diverge for
  some unusual values (e.g. complex shortest-round-trip ties). Twelve fixtures
  do not constitute a general proof of exact string equivalence.
- The browser's output length budget counts UTF-16 code units while other
  runtimes may count Unicode code points; this remains a separate issue.

**Required next action:** run `python scripts/verify_local.py --profile parity
--report build/parity-report.json`, then
`python scripts/audit_parity_report.py build/parity-report.json` against a clean
full checkout. Investigate actual mismatches before claiming cross-runtime
completeness.

**Progress score:** Keep Kasa 0.4 at 8/10 (80%) and Kasa 1.0 maturity
at approximately 35%. This fixes one documented browser output incompatibility,
not either remaining alpha release checkpoint.
