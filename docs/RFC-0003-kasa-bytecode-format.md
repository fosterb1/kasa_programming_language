> **Historical bytecode proposal.** This draft predates the implemented KBC1 RFC and subsequent security/resource fixes. The current bytecode reference is [RFC-0005](./RFC-0005-kbc1-portable-bytecode.md). Do not implement this older document in preference to RFC-0005.

# RFC-0003 — Kasa Bytecode Container (KBC1) — Alpha proposal

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

## Compatibility and future versions

KBC1 is an **alpha-only** format. Future releases must maintain compatibility
through versioned readers or explicitly reject unsupported versions. Changing
the opcode numbering, value types or VM semantics requires a new bytecode
version. Standard-library imports, dependency resolution, debug symbol tables,
signatures, modules and WASM bytecode loading have **not yet** been implemented.
