# Group 0.4 — shared experimental module conformance checkpoint

**Date:** 2026-11-20  
**Status:** Windows acceptance verified on commit `a06a9ac` using owner-provided logs; still experimental, not merged into `main`, and not stable Kasa syntax.

## Current behavior

The Python experimental runner and the browser JavaScript interpreter both accept an **explicit opt-in** to the provisional `fa math firi stdlib: m` form and namespace-qualified exports such as `m.kasa_sum([1, 2])`. The default Python CLI/parser and JavaScript runtime continue to reject unapproved module syntax when the option is disabled. Native C++ and serialized KBC1 do not implement native module imports.

## New shared fixtures and drivers

- `tests/conformance_experimental_modules.json`: twelve cases covering two modules, implicit aliases, math/collections exports, correct stdout, input strings, unknown modules, duplicate aliases, untrusted origins, private symbols, unknown aliases, alias reassignment, and misplaced imports.
- `tests/test_module_cross_runtime_fixtures.py`: runs each case via the catalog-pinned Python source-runner. Asserts exact output, explicit Python error category, error message fragment, zero output on preflight failure, and no module-name leakage into application globals.
- `tests/test_js_module_cross_runtime_fixtures.cjs`: validates catalog SHA-256 identities before passing locally read module source to `executeKasa`, then checks the same cases against JavaScript with explicit expected JS error category and no partial stdout.

**G0.4.1 implementation (pending Windows test):** JavaScript now emits `ModuleError` for catalog/binding failures and `NameError` for unknown/private members and aliases, matching the Python experimental runner for covered fixtures. Parser failures remain `SyntaxError`. The shared fixture now checks line/column on unknown modules, missing/private members, alias reassignment and misplaced imports. Duplicate-alias source positions are not yet asserted: the Python runner currently attaches certain planner failures to the first import, whereas JavaScript points at the later conflicting import. This is a documented discrepancy to resolve separately; categories alone do not establish universal diagnostic parity.

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

### Windows acceptance evidence (2026-11-20)

- Checkout: `dev/g04-module-cross-runtime-fixtures`, exact tested HEAD `a06a9ac`.
- Python focused suite: **52 passed in 0.82 seconds**.
- Shared Node JavaScript driver: **12/12 cases passed**. It was invoked twice with the same 12 results; count it once, not as 24 independent cases.
- Existing JavaScript module suite: **19 checks passed**.
- Full local parity profile: **11 passed / 0 failed / 0 not run**, including CMake native build, numeric differential, KBC1 and diagnostic-category conformance.
- Verified scope: the Python experimental runner and Node JavaScript engine execute the shared fixture corpus. This is not native import support and does not certify exact category/location parity, web worker execution, public release, or WASM imports.

**Change after verification:** This documentation update creates a new branch commit; the tested code revision remains `a06a9ac`.

## Next

1. Review and harmonize error categories and line/column diagnostics between Python and JavaScript.
2. Expand shared fixtures to module initialization budgets, shadowing and nested expressions without introducing network/filesystem capabilities.
3. Run a genuine browser worker regression separately.
4. Only after agreed semantics and tests, design native/KBC self-contained module packaging with versioning and rejections.
5. Update `docs/DEVELOPMENT_JOURNAL.md` when Windows verification results arrive, and preserve the separate Academy security PR and unreleased WASM candidate.

## G0.4.1 — diagnostic harmonization implementation (not yet accepted)

After the Windows-verified G0.4 baseline at `a06a9ac`, this branch added a small, **opt-in-only** JavaScript diagnostic classifier and tightened the existing shared fixture drivers. Ordinary JS Kasa programs are unchanged. Expected class alignment is:

- `SyntaxError`: grammar and misplaced declarations.
- `ModuleError`: missing catalog modules, duplicate module/alias selection, invalid module metadata.
- `NameError`: unknown alias, non-exported symbol, alias reassignment/redeclaration.

The test fixtures assert exact source line/column on selected errors for both engines. No attempt has been made to claim source identity, dependency/package security, KBC1 imports or Native WASM module support. This branch's **new code is not yet Windows-verified**. The previous 52 Python / 12 JS / 19 JS existing / 11 parity stage passes apply only to `a06a9ac`.

### New local verification gate

```cmd
cd C:\Users\User\kasa_programming_language
git pull --ff-only
python -m pytest -q tests/test_module_cross_runtime_fixtures.py tests/test_g03_source_import_acceptance.py tests/test_experimental_module_source.py
node tests/test_js_module_cross_runtime_fixtures.cjs
node tests/test_js_experimental_modules.js
python scripts/verify_local.py --profile parity
git rev-parse --short HEAD
```

Next: after this gate passes, resolve remaining duplicate-alias location mismatch with an explicit per-declaration Python diagnostic, add real-worker verification, then consider G0.5 native/KBC packaging design.

## G0.4.2 — duplicate module/alias diagnostics (implementation, Windows verification pending)

- The experimental Python source runner now records module IDs and aliases while reading leading import declarations. A duplicate is rejected at **the conflicting second declaration**, before catalog binding or program output, with the existing `ModuleError` category and message.
- The shared fixture corpus now has **13 cases** (previously 12): both duplicate aliases and duplicate module selections assert **line 2, column 1** in Python and JavaScript. Existing source/output tests and isolated namespace checks remain in place.
- This does **not** change the normal `python -m kasa` parser, grammar, JavaScript interpreter semantics, native C++ compiler or KBC formats. Planner-level validation remains in force for catalog identity, allowable aliases, dependency checks and other rules.
- **Known limits:** error coordinates currently point at the import statement's beginning. Exact identifier-token highlighting is future work. Python still wraps catalog failures into `ModuleError` at the first declaration for cases beyond locally detected duplicates; no universal diagnostic-location guarantee is claimed.
- **Verification:** Files committed on this development branch; **not yet executed on owner's Windows workstation**. Earlier user-reported G0.4.1 tests passed but without detailed stdout/HEAD, so do not conflate them with G0.4.2 acceptance.

### G0.4.2 Windows acceptance

```cmd
cd C:\Users\User\kasa_programming_language
git pull --ff-only
python -m pytest -q tests/test_module_cross_runtime_fixtures.py tests/test_g03_source_import_acceptance.py tests/test_experimental_module_source.py
node tests/test_js_module_cross_runtime_fixtures.cjs
node tests/test_js_experimental_modules.js
python scripts/verify_local.py --profile parity
git rev-parse --short HEAD
```

Acceptance requires the new 13-case shared suites, no regressions in existing tests, and all applicable parity stages passing. Then run real browser-worker checks before claiming the opt-in browser module path broadly tested.
