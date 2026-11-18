# RFC-0008 — Kasa arbitrary-precision integer contract and native migration

**Status:** Accepted *direction*; candidate language semantics and tests, **not an implemented native feature**.  
**Date:** 2026-11-18  
**Linked:** [RFC-0007 core contract](./RFC-0007-core-language-contract.md), [numeric portability issue #39](https://github.com/fosterb1/kasa_programming_language/issues/39).  
**Test corpus:** [10 shared exact-number cases](../tests/conformance_arbitrary_integers.json).

## Decision

Kasa integer values are intended to have **exact arbitrary precision subject to explicit runtime resource limits**. A program must not silently wrap, convert to binary64, or lose integer precision when an arithmetic result crosses the signed 64-bit boundary. This preserves current Python `int` and JavaScript `BigInt` behaviors.

This is **not yet** a claim of three-engine parity: the current native C++20 compiler/VM and KBC1 use signed `int64_t` and reject larger values. Native is an **experimental restricted implementation**, not the definition of the final language. The native upgrade is a separate, gated workstream.

## Intended language behavior

- Decimal integer literals represent exact values, including a leading unary minus. Source spelling (leading zeros) does not affect value. Source literals currently have a 1,000-digit lexer cap.
- Integer `+`, `-`, `*`, unary negation and integer `%` produce mathematically exact integers unless a resource limit is reached. No signed 64-bit overflow or wraparound.
- Remainder obeys the existing floor-division sign rule: `a % b = a - floor(a/b) * b`. Remainder by zero produces `ZeroDivisionError`.
- Integer equality/ordering, including recursive list equality, must be exact. Mixed integer/float comparisons must not first round a large integer to floating point.
- `nɔma` numeric **integer text** produces an exact integer using the already documented ASCII grammar. `nsɛm` and `ka` render its full decimal representation.
- `/` remains a binary64-producing division operation; it is **not** exact rational division. Float conversion/overflow and mixed arithmetic require additional shared tests and explicit decisions.
- Booleans remain disjoint from numbers. List indexes and `mpɛn` counts must be validated and bounded independently of integer precision.

## Limits and security

Current Python and JavaScript code impose a **16,384-bit result limit** and a **1,000-digit numeric literal/text limit** (with independent execution, container and output limits). These numbers are **candidate implementation limits**, not yet certified as a uniform public language standard. An eventual compliant engine must reject excessive work with `ResourceError`, not truncate or hang.

Before shipping native big integers, implement **pre-operation guards** for expensive shifts/multiplication/conversion, benchmark the cost of 16,384-bit values, and test denial-of-service scenarios. Avoid allocating a huge result merely to detect that it exceeds the cap. This RFC does not introduce bit-shift syntax, crypto APIs or exact decimal money types.

## Native implementation approach

1. **Baseline first:** run the current complete-checkout parity profile on a pinned commit. Record failures in Python, Node, native source VM and KBC1; do not count planned fixtures as passes.
2. **Representation:** evaluate a small-int fast path (`int64_t`) plus an arbitrary-precision backend (for example Boost.Multiprecision `cpp_int`). Check packaging/build availability and licensing before selecting a dependency. Do not silently change existing `Value` variant semantics.
3. **Arithmetic and comparisons:** change the native VM's exact integer operations and mixed numeric comparisons with overflow and resource guards. Verify signed boundaries and negative remainder.
4. **Parsing and conversion:** support integer literals, `nɔma`, printing and list equality without roundtripping through `double`.
5. **Bytecode compatibility:** KBC1 currently stores int64 integers. Define a **versioned** extension/format and reject unsupported versions explicitly; never reinterpret existing KBC1 integer fields as a new format without a version gate.
6. **Release gates:** run common exact-number fixtures through Python, Node, native source, native serialized bytecode, GCC/Clang sanitizers, platform installers and limits. Record the revision and results in the engineering journal.

## Shared acceptance cases

The first 10 target fixtures cover signed 64-bit crossing in both directions, repeated powers of two, large multiplication, negative remainder, large literals, `nɔma`, mixed integer/float exact comparisons, nested list equality and text roundtripping.

**Verification state:** All 10 fixtures were run successfully using the repository's JavaScript browser interpreter in direct V8 execution. The Python pytest cases are registered but not yet executed here. Native/KBC1 currently cannot satisfy the larger-value cases and therefore must **not** be marked passing or added to a required native-success test stage until its backend and bytecode format are upgraded.

## Explicit non-goals

This decision does not introduce classes, imports, tensors, graphing, crypto, arbitrary-precision *decimal* arithmetic, or production-quality accounting/currency types. These require separate specifications. It also does not mean native Kasa is now feature-complete.

## First native arithmetic experiment (2026-11-18)

An optional, independent `native/include/kasa/big_integer.hpp` prototype now uses **Boost.Multiprecision cpp_int** for exact integer parsing, add, subtract, multiply and Python-style floor remainder under candidate result/digit caps. Its `kasa-bigint-smoke` CTest target is enabled **only** with `-DKASA_BUILD_BIGINT_EXPERIMENT=ON` and requires Boost headers; the default native/KBC1 build remains dependency-free. Run from the repository root on a machine with Boost headers:

```sh
cmake -S native -B build/kasa-bigint -DKASA_BUILD_BIGINT_EXPERIMENT=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-bigint --target kasa-bigint-smoke
ctest --test-dir build/kasa-bigint -R kasa_bigint_rfc0008_experiment --output-on-failure
```

**Actually verified on Linux:** 1/1 experimental Release-mode CTest passed; the existing VM/KBC1 alpha still passed 10/10 parity and 18/18 full-profile stages. This does **not** mean native `.kasa` code can already use large integers. Integration of the `Value` variant, VM operators, exact mixed-float comparisons, parser, numeric builtins, runtime caps, and **version-gated KBC2** remains required. Boost header packaging/licensing and MSVC support are still to be reviewed and tested.
