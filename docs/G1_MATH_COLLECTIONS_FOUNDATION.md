# G1.1 — Math and collections pure-source foundation

**Branch:** `dev/g1-math-collections-foundation` (started from post-G0.4 `main`).  
**Status:** Experimental implementation awaiting owner Windows acceptance, native/KBC1 parity and formal review.  
**Dependency isolation:** The G0.5 PR #61 continues separately; no edits to `stdlib/catalog.json`, `stdlib/experimental/`, its SHA-256 content identities, or native linker/safety code.

## Goal

Expand Kasa's general-purpose standard-library experience without introducing unreviewed imports or coupling release to the blocked WSL/Codespaces environment. Four new helper functions are written in Kasa itself. These are **source fragments**, not supported modules, stable Twi keywords, builtins, or safe processing of arbitrary types.

| Helper | Contract for prototype | Notes |
| --- | --- | --- |
| `kasa_min_or(values, fallback)` | Minimum among nonempty comparable integers; fallback for empty list | No sentinel collision, no arithmetic overflow inside function |
| `kasa_max_or(values, fallback)` | Maximum among nonempty comparable integers; fallback for empty list | No sentinel collision, no arithmetic overflow inside function |
| `kasa_first_index(values, needle)` | Zero-based first equality match; `-1` if missing | Read-only list scan |
| `kasa_last_index(values, needle)` | Zero-based last equality match; `-1` if missing | Read-only list scan |

**Intentional limitations:** These functions assume list inputs and comparable values, rely on current runtime equality/ordering semantics, and do not introduce checked 64-bit arithmetic, generic iterators, type signatures, list slicing, sorting, mutation APIs, runtime random, or any filesystem/network capability. They do not validate types themselves. Portable list lengths stay subject to interpreter and native engine quotas.

## Shared acceptance fixtures

`tests/conformance_g1_foundation.json` contains eight fixtures exercising negative numbers, zero, duplicate values, empty fallback, one-element lists, missing elements, stable zero-based indexing, no input mutation, and composing math with collection search. The same corpus is consumed by Python and Node tests. A dedicated native/KBC1 runner is now implemented at `native/tests/g1_foundation_conformance.py` using the exact same eight fixtures. **Its execution has not yet been confirmed** on the owner's Windows machine.

### Windows CMD acceptance (no GitHub Actions, WSL or Codespaces needed)

```cmd
git fetch origin
git switch dev/g1-math-collections-foundation
git pull --ff-only
python -m pytest -q tests/test_g1_foundation.py tests/test_stdlib_foundation.py
node --test tests/test_g1_foundation.cjs tests/test_stdlib_foundation.cjs
python native/tests/g1_foundation_conformance.py build/kasa-local/Release/kasa-native.exe
python -m pytest -q tests/test_module_cross_runtime_fixtures.py
node tests/test_js_module_cross_runtime_fixtures.cjs
```

**Exit criteria:** shared Python/Node G1 fixtures pass, existing standard library and G0.4 opt-in import tests remain green, and native source/KBC1 fixture parity is added and verified before any official promotion. G0.5 POSIX strict-publication and real Windows symlink skip reports remain independent security gates; this work does not change or waive them.

## Next decision

After owner-reported Windows results, review signed-integer extremes, semantic errors and resource limits. Only then consider integrating G1 helper prototypes into a versioned library catalog once the separate G0.5 contract and content-hash changes have been formally accepted.
