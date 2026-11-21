# G1.2.2 — Experimental opt-in Python module imports

**Status:** Implemented on development branch; local verification pending.
This is a **Python-only** experiment, not a stable language feature.

The existing experimental source runner now accepts `--generation g1`.
Without this flag it retains **G0** behavior. Both catalogs remain
separate and content-pinned. The standard `python -m kasa run` command
is unchanged and does **not** accept these experimental imports.

## Example (experimental)

```kasa
fa math firi stdlib: m
fa collections firi stdlib: c
ma values = [40, 60, 80, 90]
ka m.kasa_total(values)
ka m.kasa_average_or(values, 0)
ka m.kasa_count_above(values, 60)
ka c.kasa_count_distinct(values)
```

Expected output is `270`, `67.5`, `2`, `4`, each on its own line.

Execute a saved source file using:

```bash
python scripts/run_kasa_modules_experimental.py example.kasa --generation g1
```

The same runner without `--generation` uses G0 and refuses
`kasa_total` because it is not a G0 export.

## Behavior and boundaries

The opt-in parser accepts the existing provisional `fa ... firi stdlib`
syntax. G1 configuration verifies the entire G1 manifest, validates
requested IDs/aliases through the existing namespace planner, re-reads
and re-hashes reviewed G1 source, then binds function-only AST
declarations into private lexical environments. Public exports are
restricted to the G1 catalog, and aliases cannot be reassigned.
Missing/private exports, duplicate aliases, late imports and
unknown modules fail.

No arbitrary source paths, network access, OS APIs, package downloads,
host privileges or new runtime capabilities are added. This is not a
sandbox for untrusted public code; SHA-256 verifies consistency rather
than publisher authenticity, and no general filesystem race-proof
guarantee is claimed. Existing reference-runtime step limits still apply.

**Out of scope:** browser JavaScript imports, native C++/KBC imports,
normal Kasa CLI imports, Studio deployment, new Twi keywords, G0.5
production safety claims and Netlify publishing.

## Verification in Google Cloud Shell

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g122-python-g1-imports
source .venv/bin/activate
python -m pytest -q tests/test_g122_python_imports.py
python -m pytest -q tests/test_experimental_module_source.py tests/test_validate_g1_catalog.py
python scripts/verify_local.py --profile full
```

A passing Python suite here does **not** establish JavaScript or
native module parity. Record the exact revision and any skips.
