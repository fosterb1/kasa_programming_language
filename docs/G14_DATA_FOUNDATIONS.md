# G1.4 — source-only tabular data processing foundations

**Status:** proposed, experimental, independent verification pending.

## Compatibility review

Kasa currently has lists (including nested lists), indexes, functions, integer
and binary64 arithmetic, comparisons, equality, `tentɛn`, and bounded execution.
It does **not** have dictionaries/records, CSV/JSON I/O, file permissions,
a formally specified money type, append/growing-list operations, or a trusted
public package loader. The G1 manifest is an explicitly **closed** allowlist
of `math` and `collections` with exact function names and SHA-256 hashes.

Therefore G1.4 begins as **source-only** `stdlib/g14/tables.kasa` rather
than modifying the closed G1 manifest or claiming a shipped module. The file
can be prepended to a trusted Kasa source program in local tests. It is not
available through `fa tables firi stdlib` in any current runtime.

## Minimal model

A table is a list of rows, and a row is a list. Examples:
`[[101, 25], [102, 40], [103, -5]]`. Column indexes are zero-based.
All functions are read-only. The new pure-Kasa functions are:

| Function | Contract |
|---|---|
| `kasa_rows_have_width(rows,width)` | true for every row width equal to nonnegative `width`; empty table true |
| `kasa_column_valid(rows,column)` | true when column >= 0 and every row is long enough; empty table true for nonnegative column |
| `kasa_count_column_equal_or(rows,column,needle,fallback)` | count matching cells; fallback for invalid column or short row |
| `kasa_sum_column_or(rows,column,fallback)` | sum numeric column; fallback for invalid column or short row; empty valid table sums to 0 |
| `kasa_first_row_equal_or(rows,column,needle,fallback)` | first matching zero-based row index; fallback if absent or invalid column |

**Important limitations:** width checks do not grant structural types; wrong
input types still cause existing runtime errors. Column validity accepts
ragged rows if all rows contain the requested column; use
`kasa_rows_have_width` separately for a rectangular-table requirement.
Non-numeric column sums follow ordinary Kasa type errors. Float arithmetic
is **not** exact money arithmetic: use integer minor units for financial
examples, and explicitly specify rounding before settlements. These
helpers do not parse or validate external files.

## Independent tests

`tests/g14_table_cases.json` supplies 10 positive output fixtures.
`tests/test_g14_tables.py` executes them through Python and Node and
checks the pinned G1 manifest remains unchanged.
`tests/g14_table_js.cjs` runs identical fixtures in the JavaScript
runtime. `scripts/verify_g14_table_native_kbc.py` checks all 10 against
native C++ run and **unchanged KBC1** including source independence.

Google Cloud Shell:

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g14-data-foundations-source
source .venv/bin/activate
python -m pytest -q tests/test_g14_tables.py
node tests/g14_table_js.cjs
python scripts/verify_g14_table_native_kbc.py
python scripts/verify_g13_cross_runtime.py
python scripts/verify_local.py --profile full
git rev-parse HEAD
git status --short
```

If `build/kasa-local/kasa-native` is missing on Linux:

```bash
cmake -S native -B build/kasa-local -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-local --target kasa-native --config Release
```

**No merge until owner verification.** A local source-only test gate is
not browser G1 module integration, hostile-input safety, CSV/JSON support,
real application development or release certification. Preserve G0.5
trusted-local experimental status; Netlify remains paused.
