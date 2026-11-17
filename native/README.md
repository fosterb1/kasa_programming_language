# Kasa Native — independent bytecode compiler and VM

**Version:** `0.4.0-alpha` (KBC1 development branch) · **Status:** experimental native compiler and virtual machine. The KBC1 file format is a draft undergoing integration verification.

This is the first Kasa executable **that runs without a Python or JavaScript runtime**. It is written in **C++20**, uses the C++ standard library, and implements its own lexer, parser, abstract syntax tree, bytecode generator, and stack-based virtual machine. It does **not** generate Python source code, call Python, invoke Node.js, or delegate language evaluation to either existing Kasa interpreter.

The existing Python runtime (`src/kasa`) is kept as a behavioral reference. The browser's JavaScript runtime remains the current web implementation. Native and browser runtimes are independent projects, which is why **conformance tests** are essential.

## Compile

Requirements: CMake >= 3.16, a C++20-capable compiler, and Python >= 3.11 **for the conformance test harness only**.

```bash
cmake -S native -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Run from the **repository root** (executable path on multi-configuration Windows builds is normally `build/Release/kasa-native.exe`):

```bash
./build/kasa-native --version
./build/kasa-native run examples/hello.kasa
./build/kasa-native run native/examples/inventory_report.kasa
./build/kasa-native check examples/functions.kasa
./build/kasa-native disasm examples/functions.kasa
```

The `disasm` command prints the internal bytecode instructions. The VM **compiles the source into bytecode and then executes it**, rather than evaluating the AST directly. `check` parses and compiles but deliberately does not execute code.

## Standalone native lexer verification (no Python or VM required)

The C++20 lexer has a self-contained executable that checks 13 Unicode/source-location cases. Build only that target if the full compiler is not yet ready:

```bash
cmake -S native -B build/kasa-local -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-local --target kasa-lexer-smoke --config Release
ctest --test-dir build/kasa-local -C Release -R kasa_native_lexer_unicode --output-on-failure
```

The executable tests tokenization and error coordinates, **not full native program execution**. It is also included in the `python scripts/verify_local.py --profile full` verification plan.

## Experimental KBC1 file operations

From the repository root, after building `kasa-native`:

```bash
./build/kasa-native compile examples/market_cashbook.kasa -o build/market.kbc
./build/kasa-native check-bytecode build/market.kbc
./build/kasa-native disasm-bytecode build/market.kbc
./build/kasa-native run-bytecode build/market.kbc
python native/tests/test_bytecode.py build/kasa-native
```

Bytecode is validated before execution. CRC32 is **not authentication**. The loader and virtual machine are not approved to execute untrusted bytecode as a privileged service. See [KBC1 RFC-0005](../docs/RFC-0005-kbc1-portable-bytecode.md). **Full integration testing on the current base remains pending.**

## Test native/compiler conformance

```bash
python native/tests/conformance.py build/kasa-native
```

The harness compares native program output against the current **Python reference implementation** and checks error categories, bytecode generation, and all repository `.kasa` examples. Python is used only by the test harness; the native executable requires no Python installation.

## Current language support

- UTF-8 Twi source words (`ɛ`, `ɔ`, etc.), comments, strings and escapes, integer/decimal literals, Boolean and `hwee`.
- `ma`, `ka`, `sɛ`/`anyɛ_saa_a`, `mpɛn`, `bere_a`, `awiei`, `gyae`, `toa_so`.
- Precedence-aware operators, parentheses, short-circuit Boolean evaluation.
- Functions, positional parameters, return values, recursion, and lexical scope.
- Lists, zero-based indexing, nested lists, list-element assignment.
- `bisa()` / `bisa("prompt")`, `tentɛn()`, `nɔma()`, `nsɛm()`.
- Source-location diagnostics, execution-step and output budgets, recursion-depth limits.

## Deliberate alpha limitations

- **Native integer values are signed 64-bit**, while the Python reference permits considerably larger integers. Native integer overflow produces a `ResourceError` rather than wrapping. This discrepancy is documented and requires a deliberate common numeric specification (e.g. big integers) before v1.
- Decimal display precision, malformed UTF-8 handling, certain Unicode identifier categories, and numeric text conversion may still differ from Python and JavaScript. Valid UTF-8 Unicode code-point columns and selected supplementary-letter identifiers now have dedicated lexer tests, but full parity has not been established.
- Source compilation still produces in-memory bytecode internally; this branch also implements an **experimental KBC1 serialized file format and structural verifier**. It is not a security-audited sandbox, stable bytecode standard, machine-code generator, debugger, package manager, or full standard library.
- This binary is an **interpreter for compiled bytecode**, not a machine-code ahead-of-time compiler and not a self-hosted Kasa compiler.
- The VM has safety budgets but is **not a hardened sandbox** for running hostile source code on shared infrastructure.
- No open-source license has been selected yet. The existing project specification proposes MIT pending the owner's decision.

## Architecture

```
program.kasa
   │
   ▼
lexer.cpp  ──► tokens
                 │
                 ▼
parser.cpp ──► abstract syntax tree
                 │
                 ▼
compiler.cpp ──► bytecode (instructions, jumps, function bodies)
                 │
                 ▼
vm.cpp  ─────► stack machine ──► output
```

### The roadmap beyond the alpha

The proposal to evolve the project into a complete language ecosystem is documented in [`docs/RFC-0001-kasa-native-roadmap.md`](../docs/RFC-0001-kasa-native-roadmap.md). New syntax, file formats, FFI, packages and system APIs must be designed with explicit RFCs rather than silently introduced into one of the three existing interpreters.
