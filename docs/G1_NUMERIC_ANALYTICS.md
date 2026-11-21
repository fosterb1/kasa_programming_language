# Experimental G1 numeric analytics

This milestone adds three **pure Kasa** functions to `stdlib/g1/math.kasa`:

- `kasa_total(values)`: sum list elements; returns 0 for empty input
- `kasa_average_or(values, fallback)`: numeric mean, or fallback on empty input
- `kasa_count_above(values, threshold)`: number strictly greater than threshold

These helpers do not mutate their input. They operate on numeric lists using
existing Kasa numeric operators and are intended for small school/retail
examples. Mixed incompatible types still follow the existing runtime errors.

For example (prepend the G1 math source when developing locally):

```kasa
ma scores = [40, 60, 80, 90]
ka kasa_total(scores)
ka kasa_average_or(scores, -1)
ka kasa_count_above(scores, 60)
```

Expected outputs: `270`, `67.5`, and `2`.

**Financial precision caveat:** `kasa_average_or` uses ordinary Kasa `/`
and may produce binary floating-point rounding. Do not use it for exact
currency settlement; represent money as integer pesewas and define explicit
rounding before using any average in accounting calculations.

**Integration boundary:** G1 functions are not yet exported in the pinned
`stdlib/catalog.json` module list. They cannot be called through the current
`fa math firi stdlib` import in the browser. This milestone does not
change KBC bytecode, native VM, G0.5 security behavior or hosting.

## Independent tests (Google Cloud Shell)

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g1-numeric-analytics
source .venv/bin/activate
python -m pytest -q tests/test_g1_numeric_analytics.py
python scripts/verify_local.py --profile full
```

Record command outputs and exact commit before merging. No Netlify build required.
