# Independent KBC1 serializer verification — 2026-11-17

**Status:** Passed targeted **5/5** C++20 component tests; **not** a whole-compiler/VM integration pass.  
**Feature under review:** [PR #16 — KBC1 draft](https://github.com/fosterb1/kasa_programming_language/pull/16)  
**Testing route:** Local GNU compiler; **no GitHub Actions or paid CI**.

## Exact inputs

The source, test and header were reconstructed in an isolated staging directory and compared against GitHub's Git-blob SHA-1 for the corresponding PR #16 files. All three matched **before** execution:

| PR #16 path | Git blob SHA-1 (matched locally) |
| --- | --- |
| `native/src/bytecode.cpp` | `c97bc35054095f802a01ed74633f337879bad2ee` |
| `native/tests/bytecode_smoke.cpp` | `4d3e7c69d8e6c2ba45fc4e8a4b4c36c91991780f` |
| `native/include/kasa/native.hpp` | `0afbe95d525fc98a75820198945f19862eb85717` |

The SHA-1 values here identify repository blobs **for reproducibility**, not security guarantees or signed provenance. The tests were run on a focused staged copy, **not** on a cloned full Kasa working tree.

## Toolchain and commands

- Environment: Linux, GNU **g++ 14.2.0**, C++20
- Compilation with strict warnings promoted to errors:

```bash
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
    -I native/include \
    native/src/bytecode.cpp native/tests/bytecode_smoke.cpp \
    -o kasa-kbc1-smoke
./kasa-kbc1-smoke
```

### Recorded output

```text
PASS deterministic KBC1 round-trip
PASS magic validation
PASS version validation
PASS checksum rejection
PASS non-finite floating-point writer rejection
5/5 KBC1 standalone smoke checks passed
```

The binary exited with code **0**. Only the serializer/reader and selected structural checks were exercised.

## Discovery and repair

**Problem:** The writer previously serialized a non-finite floating-point constant (notably `NaN`), while `readBytecode()` rejected the same file with `Invalid KBC bytecode: non-finite constant`. This was reproduced independently with a small C++ program that directly constructed a two-instruction bytecode chunk.

**Why it matters:** A valid-looking output from the compiler must not become unreadable merely because its serialization and loading validation disagree.

**Fix:** `writeValue()` now checks `std::isfinite()` before emitting a double. The smoke suite creates both `NaN` and infinity constants and verifies that writing fails with the expected validation category **and leaves no invalid output file**.

**Result:** Before the fix, the writer accepted `NaN` and the reader rejected it. After the fix, both writer and reader reject non-finite constants. The focused smoke suite passed.

## Outstanding limitations and risks

- The entire `kasa-native` binary was **not** compiled from this branch's parser, compiler, lexer and VM sources during this check.
- `native/tests/test_bytecode.py` (adversarial loader and source→file→VM round-trip cases) still needs a complete local checkout and full native build.
- The KBC1 serializer has a CRC32 check for accidental corruption, **not** authentication or a secure sandbox for hostile code.
- Cross-platform Windows/macOS tests and real browser WebAssembly execution remain unverified.
- CI infrastructure/billing remains tracked separately in [issue #12](https://github.com/fosterb1/kasa_programming_language/issues/12) and is not being used as a prerequisite for development.

## Next independent verification gate

On the **exact commit** intended for integration, from a complete Kasa repository checkout:

```bash
python -m pip install -e ".[dev]"
python scripts/verify_local.py --profile full
```

Record exit codes, report JSON, and commit SHA. If a test fails, fix the code and append a new result; do not overwrite or silently relabel this entry as a full pass.

**Review decision as of this entry:** PR #16 stays **open** until native compiler/VM integration and adversarial tests are verified.
