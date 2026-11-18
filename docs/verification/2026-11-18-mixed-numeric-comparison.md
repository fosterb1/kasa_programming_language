# Kasa 0.4 — Exact mixed integer/decimal comparisons

**Date:** 2026-11-18  
**Status:** Merged into `main` via [PR #23](https://github.com/fosterb1/kasa_programming_language/pull/23) (squash `d0adbda82180ea7e1f88c3390adb1b6c7b459464`) after focused independent checks. The full native VM, Python interpreter suite, and compiled KBC1 integration have **not yet been rerun against the merged revision**.  
**Language changes:** No new Twi keywords; Python-reference behavior retained.

## Discovery

Kasa's JavaScript runtime previously converted large `BigInt` integers to JavaScript `Number` when comparing them with a decimal. C++ did likewise by converting native `int64_t` values to `double`.

That conversion can lose precision beyond **2^53**, giving incorrect equality and ordering. For example:

```kasa
ka 9007199254740993 == 9007199254740992.0
ka 9007199254740993 > 9007199254740992.0
```

The old JavaScript runtime printed `nokware` then `atoro`, which conflicts with Python reference semantics. The correct output is `atoro` then `nokware`.

Financial and school-record computations require comparisons that do not silently treat different integer amounts as equal.

## Implemented change

- **Browser JavaScript:** Compare integer and decimal equality through `BigInt(exactIntegerDecimal)` only if the decimal is integral. Preserve `bigint`/number operands for JavaScript's exact mixed-type relational operations. Do **not** round the integer through `Number()`.
- **Native C++20:** Added a small `numeric_compare.hpp` helper comparing signed `int64_t` to a finite binary64 value by first checking the signed 64-bit bounds, then comparing against the truncation and fractional component. Its special handling prevents undefined out-of-range float-to-int casts at **+2^63**.
- **Shared corpus:** 18 portable Kasa programs, including nested-list equality, negative numbers, fractions and native signed-64-bit boundary values, in `tests/conformance_numeric_comparisons.json`.
- **Python, JavaScript and native conformance tests:** Tests registered to consume the same corpus; native checks include both direct execution and serialized KBC1.
- **Native standalone smoke:** Added `kasa-numeric-comparison-smoke` CMake/CTest target and local full-profile verification stage.

The helper's domain is finite `double`; it deliberately rejects NaN or infinity. Existing Kasa runtime allocation/numeric limits remain unchanged.

## Independent verification performed

- **JavaScript runtime:** **107/107** directly executed checks on the feature branch. Breakdown: 18 new numeric fixtures, 26 existing successful programs, 27 expected errors, 15 remainder fixtures, 11 Unicode/source-location cases, nine examples and one EOF tokenization check. Tested in independent V8 execution of the actual retrieved `playground/kasa-runtime.js` source.
- **Native comparator:** **18/18** standalone C++20 cases passed (16 finite comparisons and two non-finite rejections), using GNU **g++ 14.2.0** with `-O2 -Wall -Wextra -Wpedantic -Werror`.
- **Python reference numerical cross-check:** **3,000/3,000** deterministic signed-64-bit/finite-binary64 input pairs matched Python's `(integer > float) - (integer < float)` comparison. This included powers of two, `INT64_MIN/MAX`, fractional values, subnormal values and seeded random IEEE-754 doubles.
- **Sanitizer cross-check:** The same **18/18** standalone comparator tests passed with AddressSanitizer and UndefinedBehaviorSanitizer enabled, no reported errors.

### Git blob identity of the compiled standalone code

| Path | Verified Git blob SHA-1 |
|---|---|
| `native/include/kasa/numeric_compare.hpp` | `40cb7c3a2c69699726d69e7b7e862b77c005762b` |
| `native/tests/numeric_comparison_smoke.cpp` | `deda554655a1cc970dbf9d3d8e0b27c67c4b9177` |

The locally compiled files matched the blob IDs from the development branch exactly. Git blob hashes here are for reproducibility, **not** signing/attestation.

### Standalone command

```sh
c++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
    -I native/include \
    native/tests/numeric_comparison_smoke.cpp \
    -o kasa-numeric-comparison-smoke
./kasa-numeric-comparison-smoke
```

Observed:

```text
18/18 exact numeric comparison checks passed
```

For a complete repository checkout, run:

```sh
python -m pip install -e ".[dev]"
python scripts/verify_local.py --profile full
```

## Remaining risks and next gate

1. The **full native C++ VM** has not been recompiled after integrating the comparator header in this verification environment. The standalone helper is verified; the native VM integration still requires compilation and native/KBC1 conformance execution.
2. The new **18 shared fixtures** have passed in browser JS, but have **not** yet been executed using the full Kasa Python parser or native compiled-bytecode VM in this session. Their Python reference numerical rules were independently cross-checked, which is not equivalent to running the Python runtime.
3. Native integers remain **signed 64-bit**; Python/JavaScript support much larger integers under Kasa's resource limits. This patch improves correct comparisons within the shared representable range, **not** full numeric-range parity.
4. Arithmetic combining large integers with floating-point numbers still follows decimal/float semantics and can lose integer precision during arithmetic. This patch fixes **comparisons**, not every mixed arithmetic operation.
5. GitHub Actions remains manual-only. No paid hosted CI was used.

**Next gate:** Execute the complete native CMake build, `tests/test_kasa.py`, `tests/test_kasa_browser.cjs` and `native/tests/conformance.py` with the exact feature revision. Do not claim a stable release based solely on these targeted checks.
