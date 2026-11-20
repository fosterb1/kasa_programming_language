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

## G0.5 diagnostic source maps — implementation checkpoint (2026-11-21)

**Status:** New code committed on the development branch, **Windows acceptance pending**. The earlier owner-reported four-case native/KBC1 results do not certify these changes. The separate synthetic namespace-collision suite also awaits its first logged local result.

- `scripts/link_kasa_modules_hygienic.py` now accepts an optional mutable `source_map={}` argument in `link_source(...)`. It records **one entry per generated source line**: the originating source file, statement start line/column, statement kind, and whether the generated line is synthetic. Existing calls without a map return the same source text. The map includes `generated_sha256` computed over the linked UTF-8 source.
- `scripts/annotate_g05_diagnostic.py` provides a conservative `annotate(...)` function and a CLI for interpreting an already-captured native diagnostic. It requires the exact generated filename prefix, a matching SHA-256 digest and aligned map entries. It only appends the **original statement origin** when the generated line represents a real statement. It leaves other filenames, unparseable diagnostics and synthetic statements unchanged, and refuses stale or malformed mappings.
- `tests/test_g05_source_map.py` validates generated-line alignment, nested statement origins, synthetic separators, SHA identity, and backward-compatible source emission.
- `tests/test_g05_diagnostic_mapping.py` checks Windows drive-letter paths, statement-only accuracy, stale hash rejection, malformed mapping rejection, and no false attribution for synthetic lines.

**Limits:** This is a statement-level map, **not an expression-column or debugger-grade source map**. A renamed function or a rewritten nested expression may appear at a different generated column, so the native diagnostic column is deliberately not attributed to the original source. The production linker CLI does **not yet write a map sidecar**; the map is presently available through the Python function API. Diagnostic annotation is an explicit offline helper, not wired into the native compiler or bytecode VM. Do not claim KBC1 contains embedded source maps.

### Windows acceptance gate for new diagnostic mapping

```cmd
git pull --ff-only
python -m py_compile scripts/link_kasa_modules_hygienic.py scripts/annotate_g05_diagnostic.py tests/test_g05_source_map.py tests/test_g05_diagnostic_mapping.py
python -m pytest -q tests/test_g05_source_map.py tests/test_g05_diagnostic_mapping.py tests/test_g05_namespace_collision.py tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
python scripts/verify_g05_native_kbc.py
python scripts/verify_local.py --profile parity
git rev-parse --short HEAD
```

After this gate passes, add an atomic, opt-in map sidecar to the CLI and a true native-error differential test with known runtime diagnostic locations. Keep Kasa import syntax experimental and PR #61 in draft until accepted.

## G0.5 mapped native errors and optional source-map sidecar (2026-11-21)

The user explicitly confirmed **all previous G0.5 verification commands passed** after the corrected blank-separator test, including the five-suite source-map/collision test set, four-case native/KBC1 parity and standard parity profile. This is **owner-reported acceptance**, not independent observation of the exact revision/test log.

### New implementation (NOT YET VERIFIED)

- The existing `scripts/link_kasa_modules_hygienic.py` now accepts `--emit-map`, writing `<output>.map.json` *only when explicitly requested*. Its Python `write_linked_source(..., map_output=...)` API requires the exact sibling sidecar path. Both outputs must be new; preexisting files are never overwritten. The writer creates ordinary Kasa source and a SHA-256-verified statement-only source map, rolling back newly created outputs on write errors. The existing no-sidecar CLI remains the default.
- Added `scripts/run_g05_native_mapped.py`, a bounded execution wrapper that prelinks opt-in modules to a temporary `.kasa` file, invokes the **existing** native `kasa-native run` binary, preserves the actual exit code and stdout, and uses `annotate_g05_diagnostic.py` to append original statement origins to eligible native stderr lines. It neither modifies the compiler nor embeds maps in KBC1.
- Added `tests/test_g05_native_mapped_runner.py` with sidecar/hash, no-overwrite, unrelated-path and two real-native tests (success and division-by-zero with expected original application statement). Real-native tests skip when no native executable is available; the acceptance gate must build native first and confirm they did not skip.

### Windows commands (new code, results pending)

```cmd
git pull --ff-only
python -m py_compile scripts/link_kasa_modules_hygienic.py scripts/run_g05_native_mapped.py tests/test_g05_native_mapped_runner.py
python scripts/verify_local.py --profile parity
python -m pytest -q tests/test_g05_native_mapped_runner.py tests/test_g05_source_map.py tests/test_g05_diagnostic_mapping.py tests/test_g05_namespace_collision.py tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
python scripts/verify_g05_native_kbc.py
python scripts/run_g05_native_mapped.py --app stdlib/demos/group0_source_import_experiment.kasa
git rev-parse --short HEAD
```

Expected final wrapper stdout for the sample: `60` then `nokware`. It has no normal diagnostic annotation on success.

Optional sidecar CLI example: `python scripts/link_kasa_modules_hygienic.py --app stdlib/demos/group0_source_import_experiment.kasa --output build/g05-linked/market-demo-with-map-001.kasa --emit-map`. The sibling JSON path becomes `build/g05-linked/market-demo-with-map-001.kasa.map.json`; both must not already exist.

**Limits:** diagnostic mapping remains statement-level; generated expression columns are not claimed accurate. This wrapper is explicitly opt-in, only maps the native source execution path, and does not alter native Kasa import grammar, KBC1/KBC2 wire formats, or browser/WASM builds. No production merge/deployment claim until this new gate passes.

## G0.5 native diagnostic acceptance and KBC1 standalone robustness gate (2026-11-21)

**User confirmation:** The owner reports **success** on the preceding G0.5 mapped-native-runner Windows verification. This is owner-confirmed; the individual counts, test transcript and exact checkout SHA were not supplied. The opt-in source-map sidecar, native diagnostic wrapper and parity baseline are accepted within their documented experimental scope. They do not implement native parsing of import syntax or KBC-embedded source maps.

**New test added, pending Windows verification:** `scripts/verify_g05_kbc_independence.py` builds one catalog-verified, statically linked, two-module program with the existing `kasa-native compile` command, checks KBC1 output, **deletes the generated intermediate Kasa source**, and requires the compiled program to run with the exact same stdout. It then tests five malformed copies of the compiled KBC1 artifact: wrong magic, unsupported version, truncation, trailing bytes and deterministic payload-byte mutation. For each mutation, both `check-bytecode` and `run-bytecode` must fail with **no stdout**. All files are in an isolated temporary directory. It does not mutate the production catalog, original files, or bytecode format.

```cmd
git pull --ff-only
python -m py_compile scripts/verify_g05_kbc_independence.py
python scripts/verify_local.py --profile parity
python scripts/verify_g05_native_kbc.py
python scripts/verify_g05_kbc_independence.py
git rev-parse --short HEAD
```

Expected final gate line: `PASS G0.5 KBC1 independence and 5 corruption cases (10 rejection checks), no bytecode format changes`. **Not yet independently or owner-verified.** The existing comprehensive `native/tests/test_bytecode.py` and mutation smoke checks remain separate and are not replaced by this focused gate.

**Next after a verified pass:** review what remains before a G0.5 exit: native import front-end UX, provenance and source-map robustness, malicious input budgets, reproducible-build proof, and whether to release the prelink workflow as a documented experimental feature. Keep PR #61 draft until explicit exit criteria are satisfied.

## G0.5 experimental one-command module-to-KBC1 front-end (2026-11-21)

**Owner-confirmed checkpoint:** The preceding G0.5 KBC1 independence and five-corruption rejection gate, plus native/module parity, were reported as **all passed** by the owner. Individual command logs and exact tested SHA were not provided. This confirmation does not cover the following newly added files.

**New implementation committed; not yet Windows tested:**

- `scripts/compile_g05_modules.py` accepts an explicit `--app` Kasa source path with experimental `fa ... firi stdlib` imports, plus a new `--output` filename under the fixed repo `build/g05-compiled/` directory. Uses existing catalog preflight, SHA-256 source identities and restricted AST source linker. Compiles a **temporary** plain Kasa intermediate using the **existing** `kasa-native check`, `compile`, and `check-bytecode` commands, validates KBC1 magic, then exclusively creates the requested output only after all prior steps succeed. Input and output aliases, linked directories, over-budget source, existing output, untrusted imports and failed native checks are refused. Compiler KBC1 format is unchanged. There is no native parser for `fa` and no runtime source/package lookup.
- `tests/test_g05_compile_command.py` tests unknown module rejection, out-of-directory output rejection, no-overwrite preservation, linked source refusal, and real native compilation of the two-module demonstration. The native test deletes the original application and verifies that the emitted KBC1 still executes. A missing native executable causes that test to skip: acceptance must first build native and confirm **no unexpected skips**.

**Windows acceptance (new code unverified):**

```cmd
git pull --ff-only
python -m py_compile scripts/compile_g05_modules.py tests/test_g05_compile_command.py
python scripts/verify_local.py --profile parity
python -m pytest -q tests/test_g05_compile_command.py tests/test_g05_native_mapped_runner.py tests/test_g05_source_map.py tests/test_g05_diagnostic_mapping.py tests/test_g05_namespace_collision.py tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
python scripts/verify_g05_native_kbc.py
python scripts/verify_g05_kbc_independence.py
python scripts/compile_g05_modules.py --app stdlib/demos/group0_source_import_experiment.kasa --output build/g05-compiled/market-demo-001.kbc
build\kasa-local\Release\kasa-native.exe run-bytecode build\g05-compiled\market-demo-001.kbc
git rev-parse --short HEAD
```

Expected demo execution: `60` then `nokware`. The compiler intentionally refuses an existing output; use a fresh filename when rerunning. Import language notation remains experimental and Twi-first only. The command is **not** a new native module parser or production-ready package compiler. The next exit gate is verifying compiler reproducibility, fuller malformed-input budgets, and revisiting PR #61 merge readiness.

## G0.5 one-command compiler accepted; reproducibility boundary gate (2026-11-21)

**Owner-confirmed acceptance:** The owner confirms **all previous Windows commands passed**, including Python compilation-command tests, parity, KBC1 safety, and the `compile_g05_modules.py` two-module demonstration producing `60` and `nokware`. This establishes an **experimental** CLI pipeline for the pinned modules; individual test counts/full logs and the tested revision were not provided. The native compiler continues to consume flattened Kasa, not import syntax directly.

**New, unverified gate:** `tests/test_g05_build_reproducibility.py` exercises:
- Identical linked source output from two independent invocations with the same source name.
- Two **independent temporary directory** compilations of the same application using the experimental CLI; byte-for-byte KBC1 SHA-256 must agree, and the second bytecode must execute correctly. This test **fails** if the build embeds uncontrolled paths/timestamps; it intentionally does not normalize or rewrite bytecode.
- Source-size budget over 50,000 bytes, duplicate module selection, private export rejection, generated internal-symbol spoofing, late import rejection, and missing native executable. Each invalid case must fail **before publishing any output**.

### Required Windows gate (new reproducibility test is not yet run)

```cmd
git pull --ff-only
python -m py_compile tests/test_g05_build_reproducibility.py
python scripts/verify_local.py --profile parity
python -m pytest -q tests/test_g05_build_reproducibility.py tests/test_g05_compile_command.py tests/test_g05_native_mapped_runner.py tests/test_g05_source_map.py tests/test_g05_diagnostic_mapping.py tests/test_g05_namespace_collision.py tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
python scripts/verify_g05_native_kbc.py
python scripts/verify_g05_kbc_independence.py
git rev-parse --short HEAD
```

**Do not claim reproducibility unless the new twice-compiled KBC1 comparison passes and the native-dependent tests are not skipped.** The gate is narrower than a cross-platform reproducible-build claim: compare only the same platform, compiler and configuration. A cross-toolchain/Windows-Linux bitwise reproducibility claim would need separate evidence.

**Remaining G0.5 closure work:** independent review of path/symlink race handling and error categories, stronger malformed source/quota corpus, cross-platform tests, and a release decision for the opt-in command. Keep PR #61 draft until all explicitly selected acceptance gates are evidenced.

## G0.5 reproducibility gate — first Windows run and correction (2026-11-21)

Owner-provided terminal output: `python scripts/verify_local.py --profile parity` reports **Passed: 11 | Failed: 0 | Not run: 0**. The eight-suite pytest run reports **1 failed, 53 passed, 1 skipped**. The sole failing case `test_invalid_imports_never_publish` supplied `ma __kasa_g05_math_kasa_sum = 1`: the linker correctly raised `HygienicLinkError("Application uses reserved internal linker name")`, but the new pytest assertion accepted only `KasaError` and `CompileError`. This is a **test exception-type contract mistake**, not evidence that reserved internal names bypassed the linker. The failure occurred before the test could assert the absence of an output artifact.

Commit `d2c5851` imports `HygienicLinkError` into the reproducibility tests and adds that **specific existing error type** to the expected exceptions; it does not weaken the linker or swallow arbitrary errors. **The correction has not yet been owner-tested.** The single skip was not identified by the short pytest output; determine its cause with `-rs`. Windows accounts sometimes cannot create symlinks, and such an explicit symlink test may skip; do not assume that is the reason without the skip report. The native build-dependent reproducibility test must **not** be skipped.

```cmd
git pull --ff-only
python -m pytest -q -rs tests/test_g05_build_reproducibility.py tests/test_g05_compile_command.py tests/test_g05_native_mapped_runner.py tests/test_g05_source_map.py tests/test_g05_diagnostic_mapping.py tests/test_g05_namespace_collision.py tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
git rev-parse --short HEAD
```

If the new test result is clean (except any explained, nonessential OS privilege-dependent skip), proceed with the independent four-case native/KBC1 and bytecode corruption scripts. Record the tested SHA; keep PR #61 draft until completion.
