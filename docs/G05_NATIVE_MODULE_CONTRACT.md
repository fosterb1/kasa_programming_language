# G0.5 — native compiler and KBC module integration contract (draft RFC)

**Opened:** 2026-11-21  
**Status:** DESIGN ONLY on `dev/g05-native-module-contract`. No native import parser, compiler, VM or bytecode format has been changed.  
**Prerequisite:** G0.4.3 experimental browser-worker gate **owner-confirmed**; see `docs/G04_SHARED_MODULE_CONFORMANCE.md`. Exact latest browser-run SHA and log not supplied.

## 1. Goal and non-goals

A native Kasa executable should eventually run a Kasa source program containing reviewed opt-in module imports, with the **same observable results and import diagnostics** as the Python/JavaScript experimental engines. A compiled KBC program must remain self-contained and deterministic: no dynamic lookup of host files, network resources, plugin executables, or changing standard-library sources at execution time.

**Not proposed:** an arbitrary package manager, runtime filesystem imports, external native shared libraries, sandbox guarantees, source-language stability, changing existing KBC1/KBC2 version identifiers, or publishing the native WASM build.

## 2. Starting evidence and current architecture

- Kasa's source catalog currently pins two Kasa-authored libraries with canonical UTF-8/LF SHA-256 identities: `math` and `collections`, explicit public exports, and an allowlisted dependency graph.
- The existing G0.1 source linker can build one flattened source program, which was previously run through the Python/native/KBC1 routes. **Flattened source is not namespaces**: private functions and same-named definitions can collide.
- In `native/src/main.cpp`, `kasa-native run/check/disasm` parses source using `lex` -> `parseSource` -> `compileProgram`. `compile` emits KBC1; `compile-kbc2` is gated on the experimental bigint VM. `run-bytecode` and `check-bytecode` load verified bytecode via `readBytecode`.
- Existing `native/CMakeLists.txt` compiles lexer, parser, compiler, VM and bytecode serializer from separate source files. Preserve the existing stand-alone KBC1 serializer/mutation tests and KBC2 opt-in tests.

## 3. Proposed delivery sequence (one gate at a time)

### G0.5a — contract and reversible, source-level linker experiment

1. Extend the **trusted build-time tool**, not the general Kasa parser, to consume the already validated catalog and opted-in `fa <id> firi stdlib: <alias>` declarations.
2. Preflight all imports **before emitting any executable output**: unknown/duplicate module ID, alias collision, malformed source, invalid content identity, dependency cycle, private export, unknown alias, and unsupported constructs.
3. Produce a self-contained intermediate Kasa source file *under build/* using a **specified capture-avoiding name-rewrite design**; no global/private symbol injection. Every imported function and helper is assigned a deterministic internal name derived from module ID and symbol; namespace references resolve statically to those names.
4. Reject any AST construct that the rewriting algorithm does not explicitly support. Avoid textual replacement: identifiers in string literals, comments and unrelated local variables must never be rewritten.
5. Do not overwrite the user's source or an existing output; reject linked output paths and unsafe path escapes, retaining G0.1's file-safety controls.
6. Before claiming namespace equivalence, demonstrate two synthetic modules with **same-named exports and private helpers**, and app symbols with those names. Test recursion, nested calls, shadowing, and mutation of lists separately. If no correct name-rewrite semantics are available, stop at a read-only plan instead of emitting unsafe source.

**Decision gate:** Only after G0.5a namespace preservation passes may the source linker be used as a native compilation front-end. A prelinker that merely concatenates modules is *not* acceptable as a native import implementation.

### G0.5b — opt-in native compilation against linked source

1. Invoke the existing native compiler only on **validated, self-contained output** from G0.5a. Do not extend `kasa-native run` silently: require an explicit opt-in command or build tool.
2. Run shared positive module fixtures in the Python experimental runner, JS experimental runner, and opt-in native-linked source. Compare exact UTF-8 stdout, exit category and documented diagnostic locations.
3. Prove that the compiler accepts only pinned known module source, and the resulting executable/bytecode reads **no source files at runtime**.
4. Check native line/column attribution. If generated source locations differ, define an explicit source map and test it instead of claiming parity.

### G0.5c — KBC1 compatibility gate, *without new bytecode*

1. Compile G0.5a's already self-contained valid source through existing `kasa-native compile` and execute with `run-bytecode`.
2. Verify exact output vs native source/Python/JS for the **portable signed-64-bit subset**; guard overflow and features that KBC1 does not represent.
3. Confirm KBC1 emitted bytes pass existing round-trip/check/rejection tests, including malformed mutation checks. Keep existing wire version and opcode set unchanged; all module references are resolved statically **before compilation**.
4. Check that removing or modifying the source catalog **after compilation** cannot change the compiled program's behavior. No runtime module source lookup.

### G0.5d — consider versioned native module metadata only if demonstrably needed

A true separate-module object/linker format is a **later RFC**. It must define symbol table boundaries, relocations, export ACLs, canonical encodings, quotas, version/revision compatibility, checksum/identity, and malformed-object rejection. It must not repurpose unused KBC1 bits or silently alter KBC2.

## 4. Opt-in program sketch (provisional syntax, not production)

```kasa
fa math firi stdlib: m
fa collections firi stdlib: c
ma items = [10, 20, 30]
ka m.kasa_sum(items)
ka c.kasa_contains(items, 20)
```

Expected stdout: `60\nnokware\n` when the specific opt-in implementation is accepted.

## 5. Required rejection cases

| Case | Expected result | Timing |
|---|---|---|
| Unknown module ID | `ModuleError` | Before compilation |
| Duplicate module ID or alias | `ModuleError` at second import | Before compilation |
| Invalid/unpinned source hash | Catalog validation failure | Before compilation |
| Missing private/non-exported member | `NameError` at member access | Before compilation |
| Unknown alias | `NameError` at member access | Before compilation |
| Reassign/redeclare alias | `NameError` | Before compilation |
| Import after first app statement | `SyntaxError` | Before compilation |
| Dependency cycle or unexpected module | Explicit rejection | Before compilation |
| Unsupported AST construct for hygienic renaming | Explicit rejection, no artifact | Before compilation |
| Linked or preexisting output path | Explicit rejection, source preserved | Before writing |
| Corrupt/mismatched KBC1 | Existing verifier rejects | Before VM execution |

## 6. Security and quality invariants

- Allowlisted, hash-checked module content; hashes check **consistency**, not publisher authenticity.
- Deterministic dependency order; no arbitrary host code or module search paths.
- Never call `eval` or run generated source in Python merely to validate it.
- The same runtime execution budget and call-depth limits apply to imported functions.
- Scope hygiene must prevent private exports and same-named function collisions.
- No filesystem/network/clock privileges introduced by imports.
- All binary corruption rejection, size limits, checksum and control-flow checks remain mandatory.
- No KBC2 bigint support implied by passing KBC1 module checks.
- Build outputs remain local and unreleased until Windows native+KBC and genuine browser gates pass.

## 7. Initial acceptance gates

**Documentation/design stage (current):**

```cmd
git fetch origin
git switch dev/g05-native-module-contract
python scripts/validate_kasa_catalog.py
python scripts/plan_kasa_modules.py --use math:m --use collections:c
python scripts/verify_local.py --profile parity
git rev-parse --short HEAD
```

These commands validate the **baseline**, not G0.5 native imports. No new code tests exist at design stage. The next PR must introduce a dedicated prelinker/semantic verifier and tests, then collect exact output, versions and commit before claiming G0.5a implementation.

## 8. Open decisions

1. Can deterministic function/parameter/local bindings be alpha-renamed hygienically with the present Kasa AST and lexer? If not, implement a dedicated symbol-resolution pass before link-time rewriting.
2. How should original source coordinates survive native compilation of an intermediate source?
3. Should G0.5b run an explicit wrapper command, rather than adding another mode to the native executable? Prefer the wrapper until format decisions are approved.
4. Which compile-time alias-shadowing conventions are part of experimental grammar, versus reserved name policy awaiting Twi language review?

**Next slice:** G0.5a build-time namespace-linker implementation, only after confirming AST/name-binding behavior. Do not merge incomplete native module support into `main`.
