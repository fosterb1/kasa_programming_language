# G1 experimental collections: list analysis

**Status:** Experimental pure-Kasa source library. These functions are not
exports from the content-pinned G0 catalog. No changes have been made to G0.4
browser imports, G0.5 trusted-local native modules or KBC bytecode.

Source: `stdlib/g1/collections.kasa`.

## New functions

- `kasa_count_distinct(values)` counts different list values, using Kasa's
  existing `==` operation. Returns `0` for `[]`.
- `kasa_all_equal(values)` returns `nokware` when every list element is
  equal to the first. Empty and single-item lists return `nokware`.

Both helpers read the input list without mutating it. `kasa_all_equal`
runs in linear time. `kasa_count_distinct` compares each new element
with preceding elements, so its worst-case runtime is quadratic; use it for
small lists and learning exercises, not massive datasets.

## Example: count product categories

The following source uses the G1 library as a development-only source
prefix; `fa collections firi stdlib` still refers only to the pinned G0
catalog and **does not** expose these G1 functions.

```kasa
ma codes = [101, 202, 101, 303, 202]
ka kasa_count_distinct(codes)
ka kasa_all_equal(codes)
```

Expected output:

```text
3
atoro
```

## Independent test in Google Cloud Shell

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g1-collection-analysis
source .venv/bin/activate
python -m pytest -q tests/test_g1_collection_analysis.py
python scripts/verify_local.py --profile full
```

Do not report this feature as native/browser module parity until separate
runtime tests execute the same functions under those engines. No Netlify
deployment is required or requested.
