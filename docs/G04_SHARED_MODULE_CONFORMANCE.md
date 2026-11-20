# Group 0.4 — shared experimental module conformance checkpoint

**Date:** 2026-11-20  
**Status:** implemented on `dev/g04-module-cross-runtime-fixtures`; **not yet executed on the Windows workstation**. Not merged into `main` and not stable Kasa syntax.

## Current behavior

The Python experimental runner and the browser JavaScript interpreter both accept an **explicit opt-in** to the provisional `fa math firi stdlib: m` form and namespace-qualified exports such as `m.kasa_sum([1, 2])`. The default Python CLI/parser and JavaScript runtime continue to reject unapproved module syntax when the option is disabled. Native C++ and serialized KBC1 do not implement native module imports.

## New shared fixtures and drivers

- `tests/conformance_experimental_modules.json`: twelve cases covering two modules, implicit aliases, math/collections exports, correct stdout, input strings, unknown modules, duplicate aliases, untrusted origins, private symbols, unknown aliases, alias reassignment, and misplaced imports.
- `tests/test_module_cross_runtime_fixtures.py`: runs each case via the catalog-pinned Python source-runner. Asserts exact output, explicit Python error category, error message fragment, zero output on preflight failure, and no module-name leakage into application globals.
- `tests/test_js_module_cross_runtime_fixtures.cjs`: validates catalog SHA-256 identities before passing locally read module source to `executeKasa`, then checks the same cases against JavaScript with explicit expected JS error category and no partial stdout.

**Known behavioral difference — not concealed:** Python currently classifies several catalog errors as `ModuleError` and unknown/private access as `NameError`. The JavaScript path currently emits `SyntaxError` for all those static preflight failures. The shared fixture records both categories to avoid falsely claiming identical diagnostics. Harmonizing error categories and source locations requires a separately reviewed language contract and implementation change.

**Scope:** JavaScript driver exercises the interpreter in Node, not a real browser worker, WASM, native C++ or KBC bytecode. The Python driver uses experimental-only import mode. It does not prove a secure package manager, arbitrary imports, or stable stdlib.

## Acceptance commands — Windows developer environment

```cmd
cd C:\Users\User\kasa_programming_language
git fetch origin
git switch dev/g04-module-cross-runtime-fixtures
python -m pytest -q tests/test_module_cross_runtime_fixtures.py tests/test_g03_source_import_acceptance.py tests/test_experimental_module_source.py
node tests/test_js_module_cross_runtime_fixtures.cjs
node tests/test_js_experimental_modules.js
python scripts/verify_local.py --profile parity
git rev-parse --short HEAD
```

Document any failures, exact tested SHA, output and skipped stages before accepting this branch. The previous Group 0.3 developer checkout reported 68/68 module tests and 11/11 parity stages passed; those results do **not** automatically certify this new suite.

## Next

1. Review and harmonize error categories and line/column diagnostics between Python and JavaScript.
2. Expand shared fixtures to module initialization budgets, shadowing and nested expressions without introducing network/filesystem capabilities.
3. Run a genuine browser worker regression separately.
4. Only after agreed semantics and tests, design native/KBC self-contained module packaging with versioning and rejections.
5. Update `docs/DEVELOPMENT_JOURNAL.md` when Windows verification results arrive, and preserve the separate Academy security PR and unreleased WASM candidate.
