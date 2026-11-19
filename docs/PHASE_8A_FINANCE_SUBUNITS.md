# Phase 8A — Exact subunit financial computing foundation

**Status:** Initial educational compatibility fixtures implemented; **not** a production financial library.  
**Date:** 2026-11-19.

## Phase 7 acceptance evidence (reported from Windows)

User's complete local verifier JSON identifies commit `5067c5b4d7326d11c7f230dc9d03f059d798afca`, with a clean working tree before and after verification, on Windows 10 19045 / Python 3.15.2.

- `python scripts/verify_local.py --profile parity` → **11 passed, 0 failed, 0 not run** (non-dry-run).
- Python semantic fixtures: **191 passed**.
- Node semantic and diagnostics: **237 passed**.
- Native C++/CMake configured and built successfully.
- Native decimal comparison differential **9,999/9,999**, numeric comparison differential **10,080/10,080**.
- Native/Python conformance **24 tests**, serialized bytecode **14 tests**, diagnostic categories **9 fixtures**.
- This is a verified subset and build-specific parity baseline; not a universal proof of all language or KBC2 semantics. WASM wasn't requested by this profile.

## Phase 8A scope

The new shared `tests/conformance_finance_subunits.json` has six cases using **existing** Kasa language syntax, **whole integer Ghanaian pesewas**, and no new native functions, Twi tokens, filesystem permissions or implicit currency conversion.

Test cases demonstrate:
1. Cash closing computation after receipts, refunds and expenses.
2. Refund accounting with zero edge conditions.
3. Internal transfers preserving total cash across accounts.
4. Guarding against negative or over-balance payments.
5. Explicit currency-code comparison to prevent accidental mixing.
6. Signed integer adjustments returning exact zero.

Design safety: These are **didactic pure algorithms**, not formal money objects. They don't yet enforce 64-bit overflow policy for each API, amount validation at its type boundary, transaction IDs, multiple subunit scales, audit trails, concurrency, persistence, accounting standards or reconciliation approvals. The native KBC1 runtime still uses limited signed integer ranges; programs must remain within the documented portable subset.

## Test commands

On Windows from the repository root with the Python venv active:

```bat
git pull --ff-only
python -m pytest -q tests/test_finance_subunits.py
node --test tests/test_finance_subunits.cjs
python native/tests/finance_subunits_conformance.py build/kasa-local/Release/kasa-native.exe
```

The third command checks each case via native source execution and a compile/check/run KBC1 cycle. Requires the previously built current native binary; no installer is executed.

**Initial independent verification:** Six Python fixtures and six Node fixtures passed independently at GitHub commit `8c6ad5c`; **native/KBC1 fixture execution awaits Windows or an independent compiled native check**. No finance-library API has yet been released.

## Phase 8B following gate

Specify an explicit *value + currency code + subunit scale* contract; choose safe overflow/negative/rounding policies, then build deterministic CSV validation and pure matching with stable unmatched reason codes. Check the same semantics in Python, JS, native and bytecode before enabling data file I/O. Preserve the user-approved sequence: **Phase 7 → Phase 8 → Phase 9 browser/Academy**.
