# G1.6 — Experimental typed validation boundary

**Status:** Proposed, test execution pending. This milestone implements a
**host-side validation contract** in Python and JavaScript, not a new Kasa
language builtin or stable schema type.

## Audit and decision

G1.5 records are two positional Kasa lists; the language has no `type()`
operator, typed schema primitive, object literal or stable serialization API.
Trying to infer types inside pure Kasa using equality would be incorrect:
Kasa numeric equality may equate integer and float values, and Booleans are
not a substitute for explicit type checking. We therefore implement a
**narrow pre-execution adapter** for trusted-local developer workflows and
keep native C++ and KBC1 unchanged. No `fa validation` import exists.

## Strict host-side schema v1

A schema is an ordered list of up to 32 objects with exactly three keys:
`name`, `type`, `required`.

- Names: unique ASCII identifiers `[A-Za-z_][A-Za-z0-9_]*`.
- Types: `integer`, `text`, `boolean`. **No decimal type yet.**
- `required`: Boolean. An optional `null` is accepted; required `null`
  yields `REQUIRED`, not `INVALID_TYPE`.
- A valid record is a list of exactly the schema's length.
- Integers must be within ±9,007,199,254,740,991 (the JavaScript safe
  integer range). Never coerce text, Boolean or float into an integer.
- Text is at most 1,024 Unicode code points (not bytes), without
  Unicode normalization. Empty text is present.
- Boolean is strictly `true` or `false`. `false` and integer zero are
  present, not missing.

On a valid schema, validation returns
`{"ok": true, "code": "OK", "field": null}` or a first-error result,
in field order, with `INVALID_SHAPE`, `REQUIRED` or `INVALID_TYPE`.
Bad schema objects instead raise a host-side contract exception;
they are not sent into a Kasa interpreter.

**Critical JSON numeric limitation:** JavaScript JSON decoding represents
both `1` and `1.0` as the same Number, while Python distinguishes int and
float. This milestone tests only a restricted integer-text-Boolean corpus.
It does **not** certify arbitrary untrusted JSON input or lossless numeric
type parity. A future portable wire format must use explicit type tags
and raw-input validation before accepting decimals or large integers.

## Implementation

- `scripts/g16_validate_record.py`: independent Python adapter.
- `scripts/g16_validate_record.cjs`: independent JavaScript adapter.
- `tests/g16_validation_cases.json`: 16 record cases and six bad-schema
  cases shared between the adapters.
- `tests/test_g16_validation.py` and
  `tests/g16_validation_js.cjs`: first-error and schema-rejection checks.

No new `.kasa` source, syntax, G1 catalog exports, VM changes, native
KBC format, hosted service, file I/O or network access has been added.
The G1.5 source-only record helpers still operate without runtime type
introspection. Native C++/KBC1 type validation is explicitly **not
implemented** here. Existing native regression gates check non-regression,
not native feature equivalence.

## Cloud Shell verification

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g16-validation-contract
source .venv/bin/activate
python -m pytest -q tests/test_g16_validation.py
node tests/g16_validation_js.cjs
python -m pytest -q tests/test_g15_records.py tests/test_g14_tables.py
python scripts/verify_g15_record_native_kbc.py
python scripts/verify_g14_table_native_kbc.py
python scripts/verify_g13_cross_runtime.py
python scripts/verify_local.py --profile full
git rev-parse HEAD
git status --short
```

Use the repository's documented CMake build if the native binary is
missing. No missing binary, skipped cases or dry runs should be counted
as a full pass.

**Boundary:** G0.5 remains trusted-local experimental. No Netlify,
Academy/Studio delivery, public JSON parser or production safety claims.
Keep PR draft until user verification and review.
