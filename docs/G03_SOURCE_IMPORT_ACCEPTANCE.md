# G0.3 opt-in source-import acceptance checkpoint — 2026-11-20

**Status:** regression tests added on development branch; **not independently executed on the Windows checkout yet**.

## Evidence received from Windows (commit `84ab2e0`)

- `python scripts/verify_local.py --profile parity`: **11 passed, 0 failed, 0 not run**, including Python, JavaScript, CMake/native C++, numeric differentials, KBC1, and diagnostics.
- `python -m pytest -q tests/test_module_namespace_isolation.py tests/test_module_member_execution.py tests/test_bind_kasa_catalog.py`: **28 passed** in 0.49 seconds.
- `python scripts/validate_kasa_catalog.py`: PASS for source fingerprints, schemas, declared exports and dependency graph.
- `python scripts/plan_kasa_modules.py --use math:m --use collections:c`: `mode: preflight_only`; dependency-first order `collections, math`; five declared exports; `capabilities_granted: []`.

## Source review

The current source **already contains an opt-in Python-only experimental import syntax** in `core.py`, gated by `experimental_modules=True`, with `fa math firi stdlib: m` and `m.kasa_sum(...)`. The separate runner `scripts/run_kasa_modules_experimental.py` parses the complete program, configures catalog-pinned namespaces and checks member references before execution. The ordinary Kasa CLI/parser still rejects imports; the syntax is **not** finalized or stable. Browser pinned modules are a separate, opt-in JavaScript implementation, not proof of full cross-runtime semantics.

## New acceptance tests

`tests/test_g03_source_import_acceptance.py` exercises:

1. Two explicit module aliases and their expected output.
2. No export or alias name leakage into Kasa globals.
3. Fail-closed handling of unknown modules, reused aliases, unpinned origin, private members and unknown aliases.
4. Rejection of alias reassignment before runtime output.
5. Stable parser rejecting opt-in syntax.
6. Step-budget enforcement for library calls.

## Windows gate — run on the new branch

```cmd
git fetch origin
git switch dev/g03-source-import-acceptance
python -m pytest -q tests/test_g03_source_import_acceptance.py tests/test_experimental_module_source.py tests/test_module_namespace_isolation.py tests/test_module_member_execution.py tests/test_bind_kasa_catalog.py
python scripts/verify_local.py --profile parity
```

Record full stdout, interpreter/toolchain version and exact commit. Do not mark this branch verified until tests run. Existing WASM candidate remains unpublished; Academy PR #9 remains separate.

## Next implementation gate

After acceptance, formalize the language policy for `fa ... firi stdlib`, define import diagnostics and source mapping, and add shared Python/JS/native/KBC test fixtures. Do not silently advertise Python opt-in import support as stable Kasa or assume KBC1 loads runtime modules.
