# Kasa Programming Language

**A Twi-first programming language for learning, creating, and thinking computationally.**

Kasa is an educational programming-language project intended to become open source, designed to make introductory programming more approachable for Ghanaian learners, especially children, beginners, teachers, and communities where English-first programming syntax can be a barrier.

Kasa's guiding idea is simple: **learners should focus on solving problems, not memorizing unfamiliar English keywords.** The language uses familiar Twi-inspired vocabulary while teaching transferable concepts such as variables, conditions, loops, functions, lists, and debugging.

> **Project status — Experimental alpha (native 0.4).** Kasa includes a Python reference interpreter, a browser JavaScript runtime, and a **C++20 native compiler/VM with an experimental KBC1 `.kbc` file format**. There are nine root example programs and an independent local verification runner. Full native KBC1 integration tests passed on Linux, but **full Python/native/JavaScript conformance, Windows/macOS validation, classroom review, and secure untrusted-code execution remain unfinished**. Kasa is not a stable 1.0 release. See the [living development journal](./docs/DEVELOPMENT_JOURNAL.md) and [native integration report](./docs/verification/2026-11-17-kbc1-native-integration.md).

## See Kasa in action

A first program, saved as `hello.kasa`:

```text
ka "Maakye, Ghana!"
```

Expected output:

```text
Maakye, Ghana!
```

Variables and decisions:

```text
ma edin = "Ama"
ma mfe = 12

sɛ mfe >= 10 a
    ka "Maakye, " + edin
anyɛ_saa_a
    ka "Kɔ so sua!"
awiei
```

Functions:

```text
dwumadie fa_bi(a, b)
    sanma a + b
awiei

ka fa_bi(4, 6)
```

Expected output: `10`.

Interactive input with a Twi prompt:

```kasa
ma edin = bisa("Wo din de sɛn? ")
ka "Akwaaba, " + edin
```

`bisa()` still reads input without a prompt. `bisa("...")` displays the supplied text (without adding a newline), then reads a line; the prompt must be text.

These programs use implemented Kasa syntax. Runnable versions are available in [`examples/`](./examples/), and the local automated test suite verifies their output.

## What Kasa aims to be best at

**Offline-first practical computing education, taught through authentic Twi and Ghanaian everyday problems.** We are starting with cashbooks, shop inventory, school fees and numerical reasoning rather than pretending Kasa already competes with Python's libraries or C++ performance.

Try [a market cashbook](./examples/market_cashbook.kasa), [inventory reorder logic](./examples/stock_reorder.kasa), or [a school-fee calculation](./examples/school_fees.kasa). All currency values in these lessons are **integer pesewas**, avoiding floating-point rounding in financial examples.

This is a **product hypothesis**, not a measured competitive advantage. Read the [sources, design principles and pilot criteria](./docs/KASA_PRACTICAL_COMPUTING_FOCUS.md). No new Twi syntax was introduced.

## Why Kasa?

Programming education should not require learners to set aside the languages they already use to explain ideas, ask questions, and reason about the world. Kasa aims to offer:

- **Familiar vocabulary:** memorable, Twi-first keywords for core programming constructs.
- **Real programming foundations:** a proper lexer, parser, abstract syntax tree (AST), and interpreter—not a text-replacement wrapper around Python.
- **Offline-first learning:** a local runtime designed for classrooms and communities with unreliable connectivity.
- **Beginner-friendly feedback:** meaningful errors that identify where a problem occurred and explain what to fix.
- **Open collaboration:** a foundation that developers, teachers, and Twi speakers can improve together.

Kasa is not intended to replace Python, JavaScript, or other established languages. Its initial purpose is to make the **first steps into programming** more accessible.

## Linguistic evidence and approval gate

Kasa does **not** accept new Twi syntax on the basis of AI translation alone. Every new word requires research, exact references, review by fluent speakers from Asante and Akuapem, and classroom suitability checks before implementation.

- [Research and approval policy](./docs/LANGUAGE_RESEARCH_POLICY.md)
- [Reference-linked audit of all 22 existing language tokens](./docs/TWI_KEYWORD_AUDIT.md)
- [Structured keyword evidence register](./docs/keyword_evidence.json)

**Audit status:** All pre-existing tokens are preserved for backwards compatibility but remain pending human review. Published lexical evidence is not the same as linguistic approval. The Python test suite contains an offline guard against silently adding new undocumented keywords or built-ins.

## Proposed language vocabulary

| Kasa | Meaning |
| --- | --- |
| `ka` | Print a value |
| `ma` | Declare or assign a variable |
| `sɛ` | If |
| `anyɛ_saa_a` | Else |
| `mpɛn` | Repeat a set number of times |
| `bere_a` | While |
| `dwumadie` | Define a function |
| `sanma` | Return a value |
| `awiei` | End a block |
| `nokware` / `atoro` | True / false |
| `ne` / `anaa` / `ɛnyɛ` | Logical AND / OR / NOT |
| `gyae` / `toa_so` | Break / continue |
| `bisa()` / `bisa("prompt")` | Read user input, optionally showing a prompt |
| `tentɛn()` | Get length |
| `nɔma()` / `nsɛm()` | Convert to number / text |

**Language note:** These spellings are provisional. Fluent Twi speakers, educators, and representatives of different speaking communities should review vocabulary, grammar, readability, and regional usage before educational release.

## Planned features for version 1.0

- UTF-8 source files with the `.kasa` extension, including Twi characters such as `ɛ`, `ɔ`, `Ɛ`, and `Ɔ`.
- Variables; integers, decimals, strings, booleans, lists, and functions.
- Arithmetic, comparisons, logical operators, and precedence-aware expressions.
- Conditional statements, counted loops, while loops, and `break` / `continue`.
- Functions with parameters, return values, and lexical scope.
- Input, output, type conversion, list indexing, and length operations.
- A command-line interface, interactive REPL, and syntax-only checking.
- Helpful syntax/runtime diagnostics and safeguards against runaway execution.
- Automated tests, runnable examples, a beginner tutorial, and teaching materials.

### Implementation approach

The interpreter follows this execution pipeline:

```text
.kasa source → Lexer → Tokens → Parser → AST → Interpreter → Output
```

The initial interpreter is written in **Python 3.11+**, using only the Python standard library for its core runtime. It does not execute Kasa programs through Python `eval()` or `exec()`, translate source into Python for execution, or expose arbitrary operating-system, filesystem, or network access through language built-ins.

## Installation and usage (v0.1.0)

Install Python 3.11 or newer, clone this repository, and run the following from its root:

```bash
python -m venv .venv
# Activate the virtual environment first (Windows: .venv\\Scripts\\Activate.ps1)
python -m pip install -e ".[dev]"
pytest -q
```

Run and check Kasa programs:

```bash
kasa run examples/hello.kasa        # Prints Maakye, Ghana!
kasa check examples/hello.kasa      # Checks syntax without executing
kasa repl                           # Starts the interactive interpreter
python -m kasa --version            # Shows the installed version
```

The `kasa check` command parses source without running it. Runtime errors include source line and column. This is an early implementation: explore the examples and check [known limitations](./docs/IMPLEMENTATION_PLAN.md) before relying on it in classrooms.

## Current progress and roadmap

| Area | Status |
| --- | --- |
| Language vision and engineering specification | Documented |
| Lexer, parser, and AST | Implemented (0.1.0) |
| Interpreter and runtime | Implemented (0.1.0; further hardening planned) |
| CLI, REPL, and packaging | Implemented (0.1.0) |
| Tests and runnable examples | Nine root programs; independent browser checks on the merged educational branch passed 89/89; full current-branch native/Python suites still require end-to-end verification |
| Tutorials and teacher resources | Practical example starter set available; complete classroom guides and educator review still planned |
| Twi community language review | Needed before release |

The initial interpreter and native bytecode-VM alpha milestones have working implementations. Current engineering priorities are cross-runtime conformance, independently executed C++ integration tests, KBC1 verification, classroom documentation, linguistic review and release hardening. Follow the [implementation plan](./docs/IMPLEMENTATION_PLAN.md) and the [engineering development journal](./docs/DEVELOPMENT_JOURNAL.md), which distinguishes merged features, verified checks and outstanding risks.

A version 1.0 release will require a working, tested interpreter—not merely completed documentation. The specification calls for at least 15 runnable example programs and tests for successful behavior, invalid input, Unicode, and resource limits.

## Cross-runtime arithmetic contract

Kasa's `%` operator uses **floor-based integer remainder** consistently in Python, browser JavaScript and the native C++ VM. For example, `-7 % 3` must return `2` and `7 % -3` must return `-2`. The implementation is accompanied by [a language-semantics RFC](./docs/RFC-0003-remainder-semantics.md) and [shared conformance fixtures](./tests/conformance_remainder.json). **The test corpus covers ordinary and negative operands, large exact integers, zero divisors and type errors.**

The three engines retain other documented differences, notably the native 64-bit integer range; this is **not** a declaration of full language parity.

**Numeric precision work in progress:** Mixed integer/decimal comparison must not round large integers through binary64. An independent 2026-11-18 engineering milestone adds exact comparison logic and 18 shared cases for the browser and native engines. [Verification and known limitations](./docs/verification/2026-11-18-mixed-numeric-comparison.md). This work does not claim that mixed-type arithmetic or every financial computation is exact.

## Unicode diagnostic coordinates (Kasa 0.4 proposal)

Kasa syntax errors should report **one-based line and Unicode code-point column numbers** regardless of whether the code runs in Python, browser JavaScript, or the C++ native VM. This is especially important for Twi characters like `ɛ` and `ɔ`. The proposed rule, limitations and compatibility fixtures are documented in [RFC-0004](./docs/RFC-0004-unicode-source-locations.md). The browser runtime passed the eleven direct source-location checks; full native and Python integration tests remain pending.

## Technical specification

The detailed architecture, grammar, language semantics, implementation milestones, test requirements, and contributor guidance are in:

**[Kasa Programming Language — Master Engineering Specification](./Kasa%20Programming%20Language.md)**

This document is the project's current source of truth. If it is moved into a `docs/` folder, the link here should be updated in the same change.

## Contributing

Kasa welcomes thoughtful contributions from Python developers, programming-language enthusiasts, educators, technical writers, and Twi speakers. At this stage, the most useful help includes:

1. Reviewing proposed keywords and examples for linguistic accuracy and classroom clarity.
2. Identifying ambiguity in the grammar or runtime rules.
3. Building and testing the interpreter in small, reviewable milestones.
4. Designing beginner exercises suitable for offline teaching.
5. Improving documentation, accessibility, and cross-platform support.

Before proposing a major language change, consult the [engineering specification](./Kasa%20Programming%20Language.md) and open a GitHub issue to explain the problem, proposed behavior, and examples. A formal contribution guide and code of conduct are planned.

## License

**License decision pending.** The engineering specification proposes the **MIT License**, subject to the project owner's confirmation. Until a `LICENSE` file is added, do not assume the repository's contents are licensed for unrestricted reuse.

---

**Kasa's mission:** make learning to program feel closer to the language learners already know—while building a rigorous, reliable foundation for real computational thinking.

## Browser-based Kasa Playground (offline-first prototype)

The [Kasa Playground](./playground/) now runs a **separate JavaScript implementation of Kasa** directly inside a Web Worker, with no Pyodide download, CDN, or server-side interpreter. The browser editor provides Run, Check syntax, input, six Twi examples and downloadable `.kasa` files. The original Python interpreter (`src/kasa/core.py`) remains the language reference; the browser implementation is tested against its core behaviors but is not guaranteed identical for all edge cases.

Build the standalone hosting ZIP using `python playground/build_site.py`. Redeploy the ZIP on an existing Netlify site to replace any Pyodide-dependent version. See the [playground deployment guide](./playground/README.md).

## Kasa Native — C++20 bytecode compiler (alpha)

Kasa's third execution engine lives in [`native/`](./native/). This is a **C++20 compiler and stack-based virtual machine**, not a Python wrapper: it translates Kasa source into *in-memory bytecode* and executes it in a standalone native binary. It currently implements the core Twi syntax, functions, recursion, lists, input and control flow. See [native build and testing instructions](./native/README.md) and the [draft native ecosystem RFC](./docs/RFC-0001-kasa-native-roadmap.md).

**Status:** `0.4.0-alpha` KBC1 preview. The portable bytecode compiler and native VM have now passed independent GCC/Clang integration checks on Linux, including AddressSanitizer validation. The KBC1 format remains experimental and is not a security boundary; full Python/native parity and cross-platform release verification remain pending.

### KBC1 portable bytecode preview (experimental 0.4 alpha)

The native 0.4 alpha includes an experimental `.kbc` file format. `kasa-native compile file.kasa -o file.kbc` writes a versioned bytecode file; `check-bytecode`, `run-bytecode` and `disasm-bytecode` validate before use. See [RFC-0005](./docs/RFC-0005-kbc1-portable-bytecode.md). **The full native compiler integration passed independent Linux verification with GCC and Clang (see documentation)**, and the format is not stable or a security boundary.

## WebAssembly browser compiler integration (development)

The [native WebAssembly bridge](./native/wasm/) connects the independent C++ Kasa bytecode compiler and virtual machine to the existing [browser playground](./playground/). The website continues to run the JavaScript interpreter by default and switches to the native VM **only when real Emscripten-generated JavaScript and WASM assets are included in the deployment package**. The browser now has Auto / JavaScript / Native WebAssembly engine selection.

Build with an active Emscripten SDK:

```bash
bash native/wasm/build.sh
python playground/build_site.py --require-wasm
```

The generated ZIP includes both `native/kasa-native.js` and `native/kasa-native.wasm`. See [WebAssembly build and Colab instructions](./native/wasm/README.md). **Important:** This code has passed local C++ C-ABI tests, JavaScript worker simulation tests, and existing interpreter regressions, but this environment did not have Emscripten and therefore an actual browser WebAssembly build has **not** been verified here. The existing JS-only playground remains functional until a real WASM deployment is compiled.
