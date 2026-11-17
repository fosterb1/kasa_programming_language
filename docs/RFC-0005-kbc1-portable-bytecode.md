# RFC-0005 — Kasa Bytecode Container (KBC1) — Alpha proposal

**Status:** Implemented experimental file format, not a stable or secure public standard.

## Motivation

Kasa programs should be compiled once and executed without distributing their
source. The C++20 compiler and VM now support the first portable bytecode
container, `.kbc`, produced by `kasa-native compile program.kasa` and run with
`kasa-native run-bytecode program.kbc`.

Unlike the earlier in-memory bytecode, this is an actual cross-process file.
No Python or JavaScript is needed to execute it on the C++ VM.

## KBC1 on-disk layout

All integer fields are **little-endian**, and textual fields contain their
original UTF-8 bytes. The format is platform-independent at the serialization
layer, but executable compatibility requires the same **Kasa VM semantics**.

| Offset | Size | Field |
| --- | ---: | --- |
| 0 | 4 | ASCII `KBC1` |
| 4 | 2 | Version `1` (u16) |
| 6 | 2 | Reserved flags, must be zero |
| 8 | 4 | Payload byte length (u32) |
| 12 | 4 | CRC32 checksum of payload (u32) |
| 16 | variable | Root bytecode chunk |

Each chunk encodes a u32 instruction count followed by instructions. Each
instruction consists of a u8 opcode, source line/column u32s, numeric operand
i32, a length-prefixed UTF-8 name, a tagged literal value and an optional
recursive function definition. Literal tags: `0=null`, `1=int64`, `2=f64`,
`3=text`, `4=bool`. Nested functions also contain their names, positional
parameters and their own bytecode chunks.

Bytecode is not machine code and is **not** a Python pickle, JavaScript or a
serialized host-language object.

## Verification prior to execution

- Enforce file and instruction-count caps before allocation.
- Validate magic, version, reserved flags, exact payload length, CRC32.
- Reject unknown opcodes, unexpected instruction data, invalid source locations,
  illegal jump destinations, negative operands, excessively large lists/argument
  counts, function-definition inconsistencies, and excessive nesting.
- Perform worklist-based control-flow analysis of **operand stack heights** to
  reject underflow, oversized stacks, and incompatible branch joins.
- Check every nested function's code separately.

CRC32 detects accidental corruption; it is **not** a signature and does not
prove authenticity. The verifier only checks the enumerated structural
invariants, not arbitrary-program safety. The VM's instruction and output
budgets still apply. Do not run untrusted bytecode as a privileged shared
service; isolation, fuzzing, signature policy and stronger verification are
future work.

## Commands

```bash
kasa-native compile examples/functions.kasa -o functions.kbc
kasa-native check-bytecode functions.kbc
kasa-native disasm-bytecode functions.kbc
kasa-native run-bytecode functions.kbc
```

The compiler rejects overwriting the input `.kasa` file. `check-bytecode`
validates the file without executing it.

## Independent verification requirements

A standalone C++20 test target `kasa-kbc1-smoke` exercises the KBC1 writer/reader without the entire native VM. **Five focused smoke groups passed independently on 2026-11-17** against exact GitHub-blob-matched `bytecode.cpp` and `bytecode_smoke.cpp` sources using GNU g++ 14.2 with `-std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror`. These cover deterministic round-trip, magic/version/checksum rejection and non-finite floating-point rejection by the **writer**. The last test exposed a defect: the previous writer accepted NaN/infinity while the loader rejected them; both now reject non-finite constants. The full VM suite `native/tests/test_bytecode.py` includes deterministic encoding, corrupted payloads, invalid instructions, source overwrite aliases, and bundled-program round-trips. The isolated development branch has **not yet passed a full native CMake build and all new tests**.

The CLI performs filesystem-aware checks against the source path before writing, including relative aliases, symlinks and hardlinks. This helps prevent accidental source loss; it does **not** provide atomic output writes or prevent filesystem time-of-check/time-of-use races.

## Mutation stress and authenticity limitations

A deterministic native test `native/tests/bytecode_mutation_smoke.cpp` modifies valid KBC1 payloads 2,000 times, recalculates CRC32, and tries to parse them **without running the resulting instructions**. In independent AddressSanitizer/UndefinedBehaviorSanitizer testing on 2026-11-17, all attempts completed without reported sanitizer errors: 1,349 mutations were rejected and 651 were structurally accepted. Some mutations create another valid bytecode structure. **This is expected, not evidence of authentication.** Neither a CRC32 checksum nor structural validation establishes who authored a file or whether the program is safe to run.

The test is targeted, deterministic robustness evidence, not exhaustive fuzzing or an independent security audit.

## Compatibility and future versions

KBC1 is an **alpha-only** format. Future releases must maintain compatibility
through versioned readers or explicitly reject unsupported versions. Changing
the opcode numbering, value types or VM semantics requires a new bytecode
version. Standard-library imports, dependency resolution, debug symbol tables,
signatures, modules and WASM bytecode loading have **not yet** been implemented.
