# Independent Python/C++ numeric differential — 2026-11-18

**Status:** Merged in [PR #25](https://github.com/fosterb1/kasa_programming_language/pull/25), commit `f2071538ab360deb133327b315b2c8af14c54710`.  
**Scope:** Targeted exact signed 64-bit integer versus finite binary64 decimal comparison only. **Not** a full Kasa parser, native VM or KBC1 conformance pass.

## Change and reproducibility

New permanent local-verification artifacts:

- `native/tests/numeric_compare_probe.cpp`: small C++20 batch executable wrapping the production `kasa::numbers::compareIntDouble()` helper
- `native/tests/numeric_differential.py`: deterministic Python-reference differential using **10,000 randomly generated finite IEEE-754 double values** with signed 64-bit integers plus **80 boundary pairs**
- `native/CMakeLists.txt`: builds `kasa-numeric-compare-probe` when `BUILD_TESTING` is enabled
- `scripts/verify_local.py`: adds the differential as a required local check in **parity (8 stages)** and **full (16 stages)**

The Python script uses `random.Random(20261118)` and compares each native result to the exact ordering computed using Python's integer/float comparison. The full 10,080 input set and each expected result are generated locally without network or additional Python dependencies.

## Verified exact source identities

| Path | Git blob SHA-1 |
|---|---|
| `native/include/kasa/numeric_compare.hpp` | `40cb7c3a2c69699726d69e7b7e862b77c005762b` |
| `native/tests/numeric_compare_probe.cpp` | `c10ab6c25f4b0176b154666187985a0c3b12f656` |
| `native/tests/numeric_differential.py` | `767fe3e3cbe7b04ca0a1a98c70c9aa8bae1b9bd8` |

All locally compiled/tested source files matched the exact GitHub Git-blob SHA-1 values above. Hashes establish content identity for this check, **not signed provenance**.

## Actual local execution and output

Environment: Linux, Python 3.13.5, GCC 14.2, Clang 17, C++20, no paid hosted CI.

```sh
# From repository root, or equivalent independently reconstructed sources:
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
  -I native/include native/tests/numeric_compare_probe.cpp \
  -o build/kasa-numeric-compare-probe
python native/tests/numeric_differential.py build/kasa-numeric-compare-probe

clang++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
  -I native/include native/tests/numeric_compare_probe.cpp \
  -o build/kasa-numeric-compare-probe-clang
python native/tests/numeric_differential.py build/kasa-numeric-compare-probe-clang
```

Observed for **both** compilers:

```text
PASS: 10080/10080 Python/native numeric comparisons matched (seed=20261118)
```

The test returned **exit 1** when the requested executable was absent, rather than implying a pass.

Also independently recompiled the existing standalone `numeric_comparison_smoke.cpp` under GCC and Clang with strict warnings; each reported **18/18 passed**.

Separately, the actual branch's browser JavaScript interpreter source passed **107/107 direct regression checks** in an isolated V8 execution, including the 18 shared numeric fixtures and nine example programs.

## Remaining limits

- The **complete Python interpreter, JavaScript Node test runner, native VM and full KBC1 integration** were not all executed from a single full checkout in this session.
- This checks **numeric comparison only**. Mixed arithmetic, decimal formatting, integer overflow and NaN behavior require separate standards and tests.
- 58 reference/KBC1 cases remain to be executed end to end; 18 numeric Kasa source cases exist as fixtures but are not the same as 10,080 raw C++ helper comparisons.
- Native integer range is signed 64-bit; the Python reference supports arbitrary precision.
- GitHub Actions remains **manual-only**. No claim of hosted CI success is made.

**Next gate:** Run the full `--profile parity` from an exact commit; archive the JSON report and any failed test details in the development journal.
