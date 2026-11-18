# KBC2 native hardening evidence — 2026-11-18

## Scope

This record separates **user-reported Windows portability evidence** from **independent Linux hardening runs**. It is not an audit or proof that untrusted KBC bytecode is safe to run.

### Windows–Linux golden-file comparison (user executed)

After PR #54 merged, the user reported `passed` for the instructed two-target Windows CTest command:

```bat
ctest --test-dir build\kasa-kbc2-vcpkg -C Release -R "kasa_(bigint_vm_rfc0008_source_and_kbc1|kbc2_cross_platform_golden)" --output-on-failure
```

Provided this is the command that completed, the `kasa_kbc2_cross_platform_golden` target compared ten Windows-produced KBC2 files against the fixed Linux SHA-256 and length manifest, making byte-for-byte compatibility **user-reported for these ten fixtures**. No complete Windows log, exact binary SHA, MSVC version or audit JSON was supplied for independent review. Do not extrapolate to all possible KBC2 programs.

### New deterministic malformed-KBC2 loader test

`scripts/verify_kbc2_robustness.py` compiles four representative KBC2 inputs then constructs **320 seeded mutations**:

- Bad magic, wrong version, nonzero flags and forged payload length
- Payload bit flips with invalid CRC, truncation
- Payload bit flips/byte replacement with recalculated CRC32 to exercise deeper parser checks

Each mutated archive is supplied only to `kasa-native check-bytecode`; **mutated bytecode is never executed**. Structural acceptance is possible for CRC-updated mutations and is not treated as a failure; abnormal exit codes, timeouts and sanitizer reports fail the test. Intentionally damaged header, length, checksum and truncated payload cases must be rejected. A successful run does not mean all hostile bytecode is safe: CRC32 does not authenticate code, and a valid but malicious program might behave differently when executed.

### Independent Linux regression and sanitizers

- GCC Release + Boost experimental `KASA_ENABLE_BIGINT_VM=ON`: **3/3** opt-in CTest targets passed (RFC-0008 integration, ten KBC2 fixed SHA-256 golden cases and 320 malformed-loader mutations).
- Clang 21.1.8 Debug, `-fsanitize=address,undefined -fno-omit-frame-pointer` and `ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1`: **3/3** opt-in targets passed with no sanitizer errors detected in this test workload.

Reproduce the instrumented build on Linux:

```sh
cmake -S native -B build/kbc2-sanitized -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_COMPILER=clang++ -DKASA_ENABLE_BIGINT_VM=ON \
  '-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer' \
  '-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined'
cmake --build build/kbc2-sanitized --target kasa-native
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
  ctest --test-dir build/kbc2-sanitized \
  -R 'kasa_(bigint_vm_rfc0008_source_and_kbc1|kbc2_cross_platform_golden|kbc2_loader_robustness)' \
  --output-on-failure
```

## Remaining certification gates

Windows rerun of the **new** robustness target, macOS ARM/Intel, real browser/WASM, sanitizer variation and long-duration coverage-guided fuzzing, malformed nested structures, valid-untrusted execution controls, dependency/license audits and reproducible binary packaging. KBC2 remains opt-in; the Kasa 0.4 alpha and stable 1.0 progress percentages are unchanged.
