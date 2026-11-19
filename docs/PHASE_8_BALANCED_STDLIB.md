# Phase 8 — Balanced standard library strategy

**Decision:** 2026-11-19. Build a general-purpose language toolkit **together with** Ghana-relevant financial and data tools. The order remains Phase 7 → Phase 8 → Phase 9.

## Current implementation: Phase 8A/8B prototype (not importable packages)

Three experimental, reusable *source-level* Kasa helpers are available in `stdlib/experimental/math.kasa`: `kasa_abs`, `kasa_clamp`, `kasa_sum`. Two collection helpers are available in `stdlib/experimental/collections.kasa`: `kasa_count_equal`, `kasa_contains`.

They are written entirely in **Kasa**, use already approved syntax and run offline. A test harness currently **concatenates library source with application source**. Kasa does **not yet provide `import`, standard library packages, type signatures, or package-manager functionality**. Therefore the proposed public `kasa.math`/ `kasa.collections` API does not exist yet. Names are provisional and should not be locked into a stable contract.

The tests use `tests/conformance_stdlib_foundation.json` with six scenarios, plus six pre-existing finance-subunit scenarios. Initial independent test run: **12/12 Python** and **12/12 Node JavaScript** passed on the prototype's exact GitHub source. Native C++ source execution and KBC1 are covered by `native/tests/stdlib_foundation_conformance.py` but require an actual compiled binary run.

### Windows test commands

```bat
git pull --ff-only
python -m pytest -q tests/test_stdlib_foundation.py tests/test_finance_subunits.py
node --test tests/test_stdlib_foundation.cjs tests/test_finance_subunits.cjs
python native/tests/stdlib_foundation_conformance.py build/kasa-local/Release/kasa-native.exe
```

The new native test checks every shared scenario in native source mode and compiled/check/run KBC1 mode. None of these commands executes the Windows installer.

## Balanced library priorities

| Group | Proposed libraries | First contract to investigate | Status |
|---|---|---|---|
| General mathematics | `kasa.math`, `kasa.stats` | Deterministic integer operations, bounds, common statistical functions | Five experimental Kasa source functions across math/collections, no imports |
| Collections and text | `kasa.collections`, `kasa.text` | Iteration, strict equality, Unicode text operations | Two collection source functions; text pending |
| Business finance | `kasa.money`, `kasa.validate` | Currency + scale, checked subunit arithmetic, input validation | Six learning fixtures; proper typed money API pending |
| Structured data | `kasa.csv`, `kasa.json`, `kasa.data` | Bounded parsing, schemas and diagnostics | Pending |
| Safe system IO | `kasa.files`, `kasa.datetime` | Local permissions, path confinement, time semantics | Pending |
| Domain tools | `kasa.reconcile`, `kasa.inventory` | Auditable deterministic algorithms, no automatic ambiguous matches | Existing learning examples; libraries pending |
| Developer quality | `kasa.test`, `kasa.log` | Assertions, structured diagnostic events | Pending |

### Constraints and next engineering gate

- **Numeric limits:** KBC1 native execution uses bounded signed integers. `kasa_abs` on the minimum signed 64-bit integer can overflow; summation also risks exceeding the portable range. These provisional functions are not safe substitutes for checked arithmetic APIs.
- **Argument constraints:** `kasa_clamp` does not reject `low > high`. Collection helpers assume lists. Future typed contracts should specify failure categories consistently.
- **Security:** No file I/O, network, database, currency conversion, or untrusted plugin execution is introduced.
- **Linguistic governance:** English-oriented provisional helper identifiers are not new Twi keywords. Future localized names require independent evidence and review.
- **Next gate:** Implement a carefully scoped module/import design or another supported reusable loading mechanism, first specifying path resolution, cyclic imports, namespace isolation and compatible Python/JS/native/KBC1 behavior. Do not simulate `import` in documentation before it exists.

This strategy balances broad applicability with Kasa's educational and practical-computing mission. Mature money, CSV and system APIs must have validation, permission and resource-limit policies before release.
