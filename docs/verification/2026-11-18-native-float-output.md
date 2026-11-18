# 2026-11-18 — Native binary64 output precision repair (candidate verification)

**Status:** Tested formatter component; native VM/KBC1 integration **pending**. Do not mark Kasa Step 1 complete from this report.
**Branch:** `fix/native-float-display-step1-20261118`
**Host:** Python 3.13.5, GCC 14.2.0, Clang 17, CMake 3.31.6, Node 22.16.0. No hosted GitHub Actions run.

## Reproduced defect

Native `vm.cpp` previously serialized double values with `ostringstream << setprecision(15)`. A directly compiled GCC reproducer printed `0.142857142857143` for `1.0/7.0`; Python 3.13.5 produces `0.14285714285714285`. This is a loss of output precision, not a financial rounding design.

## Candidate repair

`native/include/kasa/float_display.hpp` uses C++20 `std::to_chars` shortest-round-trip scientific conversion, renders values using Python-reference notation thresholds (scientific for nonzero |x| < 1e-4 or |x| >= 1e16), preserves signed zero, and pads exponents to a minimum of two digits. `native/src/vm.cpp` calls the shared helper; both direct program output and nested lists pass through its existing display path.

`native/tests/float_display_smoke.cpp` contains 18 targeted cases. `native/tests/float_display_probe.cpp` and `native/tests/float_display_differential.py` compare deterministic bit patterns against Python 3.13.5. Shared Kasa-source fixtures cover 15 decimal programs including `ka 1 / 7`; Python, browser JS, direct native and serialized KBC1 harnesses now register them. The local parity profile includes a native smoke stage and a numeric text differential stage, increasing the plan from 8 to **10** stages; full from 16 to **18**.

## Independently executed checks

- GCC 14.2.0: **18/18** standalone C++20 float display smoke cases passed with `-O2 -Wall -Wextra -Wpedantic -Werror`.
- Clang 17: **18/18** of the same cases passed with the same strict switches.
- GCC 14.2.0 with ASan/UBSan: **18/18** focused cases passed.
- GCC 14.2.0 compiled batch formatter versus Python 3.13.5: **9,999/9,999** finite seeded binary64 cases matched, out of 10,000 bit patterns (one non-finite sample was intentionally excluded).
- JavaScript runtime on branch content: **15/15** shared decimal-display cases passed in direct V8 execution, including the new `1/7` case.
- The existing parity report audit's eight locally reconstructed unit scenarios passed after updating stage identity/count. These verify report-audit behavior, **not** real Kasa native integration.

The native helper source and smoke source were authored for both the isolated local tests and branch. This is **component-level** evidence; a full clean repository checkout was not available in the isolated container to run CMake-linked VM execution.

## Known blockers

- `git ls-remote https://github.com/fosterb1/kasa_programming_language.git HEAD` failed due `Could not resolve host: github.com`.
- Python pytest against the complete repository, actual Node test runner, full native VM CMake, Python/native/KBC1 15-case integration and remaining 58 bytecode fixture cases remain **not run on this branch**.
- Differential tests are finite samples and do not establish mathematically exhaustive formatting agreement or portability on Windows/macOS.
- No untrusted-bytecode sandbox has been certified, and no open-source license was added.

## Gate to close Step 1

Run on a **complete clean clone** at the candidate commit, with Python 3.11+, Node 22+, CMake 3.16+ and C++20 compiler:

```sh
python -m pip install -e ".[dev]"
python scripts/verify_local.py --profile parity --report build/parity-report.json
python scripts/audit_parity_report.py build/parity-report.json
python scripts/verify_local.py --profile full --report build/full-report.json
```

Review any failing KBC1 cases and address them before merging the VM integration patch or claiming Step 1 complete. Keep the Kasa 0.4 8/10 implementation progress and ~35% 1.0-readiness planning estimate unchanged.
