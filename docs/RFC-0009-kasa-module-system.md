# RFC-0009 — Kasa reusable modules, namespaces and deterministic local resolution

**Status: DRAFT DESIGN — NO MODULE OR IMPORT KEYWORD IMPLEMENTED**  
**Date:** 2026-11-19  
**Roadmap:** Phase 8, balanced standard library.

## Motivation

`stdlib/experimental/math.kasa` and `stdlib/experimental/collections.kasa` are genuine Kasa functions, currently used by concatenating source in test runners. This is not a reusable standard library system. A module system should allow a Kasa source file to request a known local library while making name ownership and code execution explicit.

Existing built-in names (`bisa`, `tentɛn`, `nɔma`, `nsɛm`) and approved vocabulary must not change incidentally. **No new Twi keyword is approved by this RFC**; surface spelling requires vocabulary-policy review and separate acceptance.

## Proposed first milestone: library module loader contract

1. **Local, deterministic modules only.** Initially resolve library identities from a hardcoded allowlist and repository-relative standard-library directory. No HTTP, dynamic installation, runtime search paths, automatic downloads, plugin code or package manager.
2. **No filesystem escape.** Reject `..`, absolute paths, mixed path separators, symlinks and file identities outside the dedicated standard-library root. Module identifiers should be distinct from arbitrary file paths.
3. **Namespace boundaries.** Library functions remain in a module-owned namespace; importing one module must not override user variables, existing built-ins, or names from another module. The public surface must be explicitly exported; internal functions are not visible by default.
4. **Single deterministic initialization.** A module executes only once per program evaluation, in declared dependency order. Cycles must be rejected with a stable, classified diagnostic; partial initialization must not leak into user space.
5. **Quotas.** Imported modules share the program's step, recursion, string, memory and output budgets; loading a module must not reset limits or grant file/network permissions.
6. **Portable behavior.** Python reference, browser JavaScript, native C++ and KBC1 must load the same supported library definitions with equivalent results, checked by shared success/error fixtures.
7. **Bytecode identity.** Any serialized KBC module dependency needs an explicit, versioned content hash and compatibility rule. Existing KBC1 archives may not silently resolve different code on the host. Choose between a self-contained bundle and pinned dependencies in a future format; do not change KBC1 implicitly.
8. **Errors and diagnostics.** Reject unknown modules, ambiguous exports, duplicate binding names, cycles, invalid identifiers and incompatible versions before executing application code where possible. Show useful file/line/column positions.

## Candidate authoring shapes (NOT IMPLEMENTED)

The preferred user-facing shape should express module identity and an explicit namespace, such as `library math as m`. This example is *illustrative pseudocode*, not accepted Kasa syntax. A future reviewed Twi spelling should be chosen with community evidence under `docs/LANGUAGE_RESEARCH_POLICY.md`, rather than treating English keywords as final.

```text
# PSEUDOCODE ONLY
library math as m
ka m.sum([100, 200, 300])
```

A **test-driver-only prelinker**, which combines only allowlisted, pinned local source files at build/test time, is an admissible stepping stone. However it is **not** an import system and must be documented as a temporary compatibility mechanism. The current test runners already concatenate source in memory.

## Sequence and gates

- **8A complete for targeted portable examples:** six finance fixtures; six additional balanced stdlib fixtures across Python/JS and user-confirmed Windows native source/KBC1.
- **8B design first:** module grammar and namespace data model; test-only loader prototype after design approval; add fail-closed path checks and version hashes.
- **8C integration:** implement module support in Python and JS with shared test corpus before native and serialization support; do not claim cross-runtime support until native passes.
- **8D practical core:** stable math/collections contracts; only then currency-tagged money, validation and structured CSV/data facilities.
- **Phase 9:** live browser/Academy delivery remains scheduled after Phase 8 according to the user-selected roadmap.

## Required regression suite

Test one known module, two independent modules, duplicate imports, private/public exports, identical names in different namespaces, missing module, malicious traversal path, symlink escape, cycles, quota exhaustion, deterministic dependency versions and bytecode round-trip. Only the implemented language subset is covered by the existing 11-stage parity profile. A passing local profile does not mean this new RFC is implemented.

**Non-goals:** executing untrusted third-party code, network package fetching, installing packages, replacing the existing parser/VM contract, or claiming a Python-style import is already supported.
