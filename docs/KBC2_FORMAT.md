# KBC2 experimental bytecode format — versioned big integers

**Status:** Experimental; available only with `-DKASA_ENABLE_BIGINT_VM=ON`. **KBC1 is unchanged and remains the default.**

## Backward compatibility and CLI

- Normal `kasa-native compile program.kasa -o program.kbc` still writes **KBC1** and rejects arbitrary-precision literal constants rather than silently truncating them.
- Experimental `kasa-native compile-kbc2 program.kasa -o program.kbc` writes **KBC2**. Only the big-int-enabled native build accepts this mode; a default build rejects it.
- With the opt-in build, `run-bytecode`, `check-bytecode`, and `disasm-bytecode` accept both validated KBC1 and KBC2 files; old KBC1 files still load.
- Without the opt-in build, KBC2 files are **rejected**, rather than interpreted as KBC1 or executed without a supported integer runtime.

## Versioned 16-byte header

| Byte offset | Type | KBC1 | KBC2 |
|---|---|---|---|
| 0–3 | ASCII magic | `KBC1` | `KBC2` |
| 4–5 | little-endian unsigned 16-bit version | `1` | `2` |
| 6–7 | little-endian unsigned 16-bit flags | `0` | `0` |
| 8–11 | little-endian unsigned 32-bit payload length | length | length |
| 12–15 | little-endian CRC32 of payload | checksum | checksum |

CRC32 detects accidental corruption but is **not a cryptographic signature** and does not establish trust or sandbox safety. Existing payload instruction framing, opcodes and all KBC1 value tags 0–4 remain unchanged.

## KBC2 extra integer value tag 5

Only valid in KBC2 and only for values outside signed int64; values within signed int64 **must** continue to use tag 1.

| Field | Width | Meaning |
|---|---|---|
| tag | 1 byte | `0x05` |
| sign | 1 byte | `0x01` positive or `0x02` negative |
| magnitude byte length | 2 bytes | unsigned little-endian (1–2048) |
| magnitude | stated length | unsigned **big-endian**, minimal byte sequence |

Encoding is sign-and-magnitude, not two's complement. The first magnitude byte must be nonzero. Negative zero, zero and values already representable by `int64_t` are not valid under tag 5. The loader rejects invalid sign, length, truncation, leading zero, noncanonical small values, values exceeding **16,384 bits**, unsupported magic/version/flags, bad CRC and invalid control flow. Recursive nested functions carry the version down to every constant.

A KBC1 reader never reinterprets tag 5. The serialized extension is independently versioned, so bytes of old KBC1 files are preserved.

## Build and test

```sh
cmake -S native -B build/kasa-kbc2 -DCMAKE_BUILD_TYPE=Release -DKASA_ENABLE_BIGINT_VM=ON
cmake --build build/kasa-kbc2 --target kasa-native
ctest --test-dir build/kasa-kbc2 -R kasa_bigint_vm_rfc0008_source_and_kbc1 --output-on-failure

build/kasa-kbc2/kasa-native compile-kbc2 my_test.kasa -o my_test.kbc
build/kasa-kbc2/kasa-native run-bytecode my_test.kbc
```

**Verification (Linux GCC/Boost):** New opt-in suite passed **7/7 test methods** (one CTest target), including ten shared RFC-0008 source and KBC2 output comparisons, bytecode backwards compatibility, malformed KBC2 cases, and result-size limits. Default Linux full checkout **10/10 parity** and **18/18 full** stages passed. The exact final merged revision should be recorded in the PR and subsequent verification report.

## Limitations

- Experimental build **off by default**; Boost dependency and MSVC behavior not yet certified.
- KBC2 loader validates structural safety, not authenticity or permission to execute a program.
- A 16,384-bit integer cap, instruction limits and output budget remain. Additional mutation/property fuzzing, sanitizers and cross-platform byte-for-byte golden fixtures are required before stable release.
- The format does not introduce arbitrary-precision decimals, floats, or exact financial currency calculations.
