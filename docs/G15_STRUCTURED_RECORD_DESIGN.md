# G1.5 — Experimental structured records and validation (design + source-only prototype)

**Status:** implementation proposed; local verification and merge pending.

## Compatibility audit and design decision

Kasa's shared language subset has lists, index assignment, strings,
integers, binary floating point, `nokware`, `atoro`, `hwee`, and
functions. It does **not** have records/dictionaries, introspection
(type checks), keyed map access, optional field operators, JSON/CSV
serialization, or a schema type. `stdlib/g14/tables.kasa` already uses
lists of rows. The G1 import catalog is fixed to two pinned modules.

Therefore G1.5 deliberately does **not** alter the lexer, parser,
runtime, native compiler, KBC1 encoding or G1 pinned catalog. We first
prototype a **positional record convention** in pure Kasa:

- Schema: a list of unique field-name strings (ordered).
- Record: a list of values with exactly the same width as the schema.
- Field lookup: zero-based position by name; missing field yields -1.
- Required field: present if included in a valid schema/record pair and
  its value is not `hwee`. Numeric zero, `atoro` and empty string
  are **present**. This is not truthiness-based validation.
- The prototype does not verify field-name types or value types.
  Non-text keys and non-list arguments retain existing Kasa semantics
  or diagnostics, and must not be represented as valid external schemas.
- The functions do not mutate their arguments or perform I/O.
  Duplicate names make a schema invalid; use only distinct string names.

## Five source-only helpers

File: `stdlib/g15/records.kasa`, used by source concatenation in
local tests. Not importable through `fa records firi stdlib`.

| Function | Behavior |
|---|---|
| `kasa_schema_unique(fields)` | Whether no two schema fields compare equal; empty true |
| `kasa_field_index(fields, name)` | First zero-based matching field or -1 |
| `kasa_record_shape_valid(fields, record)` | Unique names and equal field/record length |
| `kasa_field_or(fields, record, name, fallback)` | Value of matching field, or fallback on invalid shape/name |
| `kasa_required_field_present(fields, record, name)` | True only for existing non-`hwee` field in valid record |

Example:

```kasa
ma fields = ["id", "name", "amount"]
ma record = [101, "Ama", 2500]
ka kasa_record_shape_valid(fields, record)
ka kasa_field_or(fields, record, "name", "unknown")
ka kasa_required_field_present(fields, record, "amount")
```

Expected: `nokware`, `Ama`, `nokware` on separate lines.

## Future native record/JSON wire-format design: NOT IMPLEMENTED

A future design must separately decide:

1. **Field names:** unique UTF-8 text, maximum count and byte lengths,
   normalization rules (never silently normalize at runtime), ordering
   and duplicate detection before values are accessed.
2. **Value algebra:** explicit null, Boolean, signed integer,
   finite binary64, text, list, and record cases. Define bounds for
   depth, total nodes, aggregate text bytes, and cyclic structures.
   Existing Kasa lists may be mutable, so serialization must detect
   cycles and shared references or reject unsupported graphs.
3. **Error contract:** distinguish malformed schema, invalid field
   type, missing required field, invalid value type, and serialization
   failure; specify deterministic Kasa error categories and source
   positions before implementing user-visible diagnostics.
4. **Serialization:** portable UTF-8, exact field order, escaping,
   duplicate-key policy, signed integer range and float formatting.
   JSON round trips cannot promise lossless arbitrary-precision
   integers or bitwise stable decimals without a tagged representation.
5. **Native compatibility:** model the format at the Python and JS
   level first with golden fixtures, then C++ source/KBC1. Version
   incompatible binary changes rather than quietly extending KBC1.
6. **Security:** quotas, adversarial input rejection, no filesystem
   or network authority from record operations. Public/untrusted
   program execution remains outside approval.

No JSON import/export or record literal syntax is enabled here.
Especially for accounting, keep money as integer minor units until
currency and rounding policies are explicitly reviewed.

## Tests and independent verification

`tests/g15_record_cases.json`: ten source/output fixtures covering
uniqueness, missing fields, required fields, width mismatch,
`hwee`, false-like values, and no mutation. They are used by:

- `tests/test_g15_records.py` (Python reference and Node JS runner)
- `tests/g15_record_js.cjs` (same source and output fixtures)
- `scripts/verify_g15_record_native_kbc.py` (native C++ and standalone
  KBC1 with source removed)

Google Cloud Shell:

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g15-structured-record-contract
source .venv/bin/activate
python -m pytest -q tests/test_g15_records.py
node tests/g15_record_js.cjs
python scripts/verify_g15_record_native_kbc.py
python -m pytest -q tests/test_g14_tables.py
python scripts/verify_g14_table_native_kbc.py
python scripts/verify_g13_cross_runtime.py
python scripts/verify_local.py --profile full
git rev-parse HEAD
git status --short
```

If native executable is missing on Linux:
```bash
cmake -S native -B build/kasa-local -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-local --target kasa-native --config Release
```

**Limits:** prototype does not validate arbitrary hostile schemas or
claim production-security, full cross-runtime parity, stable records,
JSON, databases, or an importable module. Existing G0.5 trusted-local
restrictions remain. PR should not merge before the owner verifies tests.
No Netlify, Academy, Studio or G1 pinned catalog changes.
