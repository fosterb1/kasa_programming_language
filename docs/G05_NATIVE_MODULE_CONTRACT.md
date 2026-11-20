# G0.5 — native compiler and KBC module integration contract (draft RFC)

**Opened:** 2026-11-21  
**Status:** Design plus G0.5a **read-only prelink preflight prototype** on `dev/g05-native-module-contract`; not yet independently verified on Windows. No native import parser, compiler, VM or bytecode format has been changed.  
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

## G0.5a first implementation — read-only prelink preflight (2026-11-21)

After owner confirmation that the baseline design-branch catalog validator and parity profile passed (individual logs and commit not supplied), the following files were committed:

- `scripts/preflight_native_modules.py`: parses opt-in `fa ... firi stdlib` import source into the existing experimental AST; validates the allowlisted source catalog and hashes, import ordering, duplicate IDs/aliases at the conflicting declaration, explicit export references, unknown aliases, function/parameter alias shadowing, and alias assignments. Returns deterministic JSON describing module bindings, dependency load order, referenced exported symbols and private functions. **Does not run Kasa, generate source, create KBC or modify the native compiler.**
- `tests/test_native_module_preflight.py`: positive two-module and nested-expression cases, fail-closed diagnostics for ten invalid inputs, string literal preservation, and no-output assertions.

**Important:** This preflight validates only the current allowlisted modules. It does not establish hygienic symbol rewriting, closure-equivalent capture, source maps, native source/KBC parity, arbitrary third-party modules, or any added host capabilities. The existing catalog validator is authoritative for source validity; checked module source is reread and SHA-256-verified before the result is returned.

### New Windows verification gate

```cmd
git pull --ff-only
python -m pytest -q tests/test_native_module_preflight.py
python scripts/validate_kasa_catalog.py
python scripts/preflight_native_modules.py stdlib/demos/group0_source_import_experiment.kasa
python scripts/verify_local.py --profile parity
git rev-parse --short HEAD
```

The demo path must exist in the checkout and contain a valid experimental import program; if missing, create a separate disposable `.kasa` sample under `build/` rather than altering the tracked demos. **Tests and commands are newly added but not yet run by the owner.** Next G0.5a slice is a symbol-binding/hygiene study; do not emit linked source until proven capture-avoiding.

## G0.5a second implementation — restricted hygienic source-linker (2026-11-21)

**Status: Committed on development branch; acceptance verification pending.** The owner confirmed earlier **read-only preflight** acceptance passed; no precise test counts or SHA were supplied. That success is not evidence for the newly generated source.

Added `scripts/link_kasa_modules_hygienic.py` and `tests/test_hygienic_module_linker.py`:

- Requires the already catalog-verified, opt-in `fa ... firi stdlib` import grammar and G0.5a read-only preflight.
- Uses the Kasa **parser AST**, not text replacement, to statically resolve qualified exported calls, rename each library function to a deterministic internal `__kasa_g05_<module>_<function>` name, and rewrite corresponding library-internal references. It keeps string literals intact, separates library function names from application declarations, and preserves the source's expression order via explicit parentheses.
- Checks that each module is still SHA-256 pinned before emission, that module definitions are top-level functions, that they contain no unresolved free variable, nested function declaration, or param/local collision with a module function. Unsupported member-as-first-class-value syntax is **rejected** rather than silently linked with changed semantics.
- Refuses application identifiers and function parameters using the reserved internal prefix, verifies the generated code parses in ordinary (non-module) Python Kasa mode, and imposes a maximum output source size.
- A CLI can write a **new file only** under `build/g05-linked/` and refuses existing targets and linked output directories. The linker itself does not invoke the C++ compiler or VM. The generated file will need a source map before exact original-source diagnostics can be claimed.
- Python tests compare output from the experimental namespace interpreter with the standalone interpreter running linked source for selected math/collections examples, nested calls and application-name collisions; they also check fail-closed behavior and no output artifact on invalid inputs.

**Supported subset limits:** only direct calls to exported functions, current known function-only libraries, no arbitrary third-party packages, no dynamic member references, no reassignment of generated internal symbols, and no first-class import-function values. A larger semantic proof (including synthetic libraries with identical public and private names) and native/KBC1 execution are still required before G0.5a is accepted as a fully hygienic linker. This implementation remains experimental and must not be merged just because its files exist.

### New Windows acceptance gate

```cmd
git pull --ff-only
python -m pytest -q tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
python scripts/link_kasa_modules_hygienic.py --app stdlib/demos/group0_source_import_experiment.kasa --output build/g05-linked/market-demo-001.kasa
python -m kasa run build/g05-linked/market-demo-001.kasa
python scripts/verify_local.py --profile parity
git rev-parse --short HEAD
```

Expected normal interpreter output for the sample: `60` on the first line and `nokware` on the second line. The CLI deliberately refuses reuse of `market-demo-001.kasa`; choose a fresh filename for subsequent attempts. **No claim of a passing native/KBC1 module test has been made.** After this source-level gate, explicitly test generated source with `kasa-native run`, `compile`, `check-bytecode`, and `run-bytecode` separately; record the output and checksum before expanding language support.

## G0.5a first Windows test failure and correction — 2026-11-21

The owner's first run of `python -m pytest -q tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py` **failed during pytest collection**: `tests/test_hygienic_module_linker.py`, line 18, contained a literal backslash-n between the two Python import statements. Pytest raised `SyntaxError: unexpected character after line continuation character`; no actual G0.5a tests executed in that run. The literal was introduced by a faulty earlier GitHub file-edit operation, not by the Kasa interpreter or Windows environment.

Commit `729e750` replaces the literal `\\n` with an actual line break. **This edit has not yet been retested on Windows.** Do not describe the new linker as passing or native-module complete. Re-run the focused tests before writing generated source, compiling, or changing the draft PR status. If a new failure appears, preserve the full traceback rather than working around assertions.

## Language import direction approved; G0.5 native/KBC1 differential gate (2026-11-21)

**Language policy:** Keep `fa <module> firi stdlib: <alias>` as the current **experimental, Twi-first** import direction. Do **not** add Python's `from ... import ...` to the Kasa parser merely because Kasa tooling is implemented in Python. The exact natural-language form remains subject to eventual linguistic review and stable-language specification. Existing default Kasa parsers continue to reject opt-in imports.

Added `scripts/verify_g05_native_kbc.py`: a strict, **not yet Windows-run** acceptance driver for four portable source cases. For each case it (1) statically links the validated catalog source to ordinary Kasa without writing into the repo, (2) compares experimental Python execution against the linked Python interpreter, (3) runs the linked source through the prebuilt native C++ binary, (4) compiles with the **existing KBC1** option, checks the `KBC1` file magic, runs `check-bytecode` and `run-bytecode`, and (5) requires byte-for-byte UTF-8 stdout agreement. It writes only into a temporary directory and refuses missing native binaries, unsupported cases, failed native commands, malformed KBC1, and output differences. No new native parser, opcode, bytecode format, runtime module loader or source catalog permissions were added.

**Windows acceptance commands (only after prior focused linker tests pass):**

```cmd
git pull --ff-only
python -m py_compile scripts/verify_g05_native_kbc.py
python -m pytest -q tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
python scripts/verify_local.py --profile parity
python scripts/verify_g05_native_kbc.py
git rev-parse --short HEAD
```

Successful driver output should end with `PASS G0.5 linked imports: 4 portable cases, Python experimental / linked / native / KBC1 outputs agree`. **No pass claimed pending owner's terminal logs.** KBC1 result parity for four examples is narrower than a general proof of native namespaces or full semantic hygiene. Continue with synthetic colliding function names/private helpers, malformed package inputs and original-source diagnostics before declaring a stable native module system.

## G0.5 user-confirmed native/KBC1 differential and collision stress test (2026-11-21)

The owner confirmed that **all requested verification commands passed**, including the four-case `python scripts/verify_g05_native_kbc.py` gate. This is **user-reported verification**: exact stdout and commit SHA for that round were not provided. It demonstrates linked-source execution through experimental/reference Python, native C++, and KBC1 for the four specified portable programs; it **does not** prove native import parsing or a general native module loader.

New `tests/test_g05_namespace_collision.py` constructs a **disposable, independent allowlisted catalog** of two synthetic function-only Kasa libraries (`alpha` and `beta`) with deliberately identical exported function `shared` and identically named private helper `helper`. Each library has a different helper implementation, while the application also declares both names. Tests require distinct generated internal symbols, separate outputs, correct nested qualified calls, private-helper access rejection, and string-literal preservation. Test code temporarily extends the catalog validator's allowlist via pytest monkeypatch only; the production `stdlib/catalog.json` remains untouched. The test runs linked code through the Python reference interpreter and **does not yet establish native/KBC parity for synthetic catalogs**.

**Status:** collision test committed; **not yet executed on Windows**. A new green gate must be recorded before claiming this invariant verified.

```cmd
git pull --ff-only
python -m pytest -q tests/test_g05_namespace_collision.py tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
python scripts/verify_g05_native_kbc.py
python scripts/verify_local.py --profile parity
git rev-parse --short HEAD
```

After this gate, implement original-source location mapping and native diagnostic differential checks. Keep import grammar experimental, maintain existing KBC1 binary wire format, and do not merge incomplete behavior into `main`.
