# Kasa Programming Language

**A Twi-first programming language for learning, creating, and thinking computationally.**

Kasa is an educational programming-language project intended to become open source, designed to make introductory programming more approachable for Ghanaian learners, especially children, beginners, teachers, and communities where English-first programming syntax can be a barrier.

Kasa's guiding idea is simple: **learners should focus on solving problems, not memorizing unfamiliar English keywords.** The language uses familiar Twi-inspired vocabulary while teaching transferable concepts such as variables, conditions, loops, functions, lists, and debugging.

> **Project status — Specification / pre-implementation.** The language design is documented, but this repository does **not yet contain a working interpreter, installable Python package, command-line tool, or automated test suite**. The examples and commands below describe the intended language and developer experience, not currently verified functionality.

## See Kasa in action — proposed syntax

A first program, saved as `hello.kasa`:

```text
ka "Maakye, Ghana!"
```

Expected output **once the interpreter is implemented**:

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

These examples follow the proposed specification; they have not yet been executed by a Kasa interpreter.

## Why Kasa?

Programming education should not require learners to set aside the languages they already use to explain ideas, ask questions, and reason about the world. Kasa aims to offer:

- **Familiar vocabulary:** memorable, Twi-first keywords for core programming constructs.
- **Real programming foundations:** a proper lexer, parser, abstract syntax tree (AST), and interpreter—not a text-replacement wrapper around Python.
- **Offline-first learning:** a local runtime designed for classrooms and communities with unreliable connectivity.
- **Beginner-friendly feedback:** meaningful errors that identify where a problem occurred and explain what to fix.
- **Open collaboration:** a foundation that developers, teachers, and Twi speakers can improve together.

Kasa is not intended to replace Python, JavaScript, or other established languages. Its initial purpose is to make the **first steps into programming** more accessible.

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
| `bisa()` | Read user input |
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

The intended execution pipeline is:

```text
.kasa source → Lexer → Tokens → Parser → AST → Interpreter → Output
```

The first interpreter will be written in **Python 3.11+**, using the Python standard library for its core runtime. It will not execute Kasa programs through Python `eval()` or `exec()`, translate source into Python for execution, or expose arbitrary operating-system, filesystem, or network access through language built-ins.

## Installation and usage — planned, not yet available

When the implementation is ready, the intended developer setup will be:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

The planned CLI is:

```bash
kasa run hello.kasa     # Run a program
kasa check hello.kasa   # Check syntax without running it
kasa repl               # Start the interactive interpreter
python -m kasa --help   # View command-line help
pytest                  # Run automated tests
```

**These commands do not work against the present specification-only repository.** Installation steps and supported commands will be verified and updated alongside the implementation.

## Current progress and roadmap

| Area | Status |
| --- | --- |
| Language vision and engineering specification | Documented |
| Lexer, parser, and AST | Not yet implemented |
| Interpreter and runtime | Not yet implemented |
| CLI, REPL, and packaging | Not yet implemented |
| Tests and runnable examples | Not yet implemented |
| Tutorials and teacher resources | Planned |
| Twi community language review | Needed before release |

The initial development sequence is: **packaging → lexer → parser/AST → runtime → control flow → functions/lists → CLI/REPL → examples/docs → testing and release checks**.

A version 1.0 release will require a working, tested interpreter—not merely completed documentation. The specification calls for at least 15 runnable example programs and tests for successful behavior, invalid input, Unicode, and resource limits.

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

## Online playground (offline-first prototype)

The browser editor at [`playground/`](./playground/) runs a **separate JavaScript implementation of Kasa** in a Web Worker, without downloading Pyodide, Python or external CDN assets. It supports Run, Check syntax, input, six examples and `.kasa` downloads. The original Python CLI in `src/kasa/core.py` remains the authoritative language runtime; the browser port is tested against its core behaviors but is not guaranteed identical for all edge cases.

Generate a self-contained Netlify site with `python playground/build_site.py`. See [setup and hosting instructions](./playground/README.md).


## WebAssembly browser compiler integration (development)

The [native WebAssembly bridge](./native/wasm/) connects the independent C++ Kasa bytecode compiler and virtual machine to the existing [browser playground](./playground/). The website continues to run the JavaScript interpreter by default and switches to the native VM **only when real Emscripten-generated JavaScript and WASM assets are included in the deployment package**. The browser now has Auto / JavaScript / Native WebAssembly engine selection.

Build with an active Emscripten SDK:

```bash
bash native/wasm/build.sh
python playground/build_site.py --require-wasm
```

The generated ZIP includes both `native/kasa-native.js` and `native/kasa-native.wasm`. See [WebAssembly build and Colab instructions](./native/wasm/README.md). **Important:** This code has passed local C++ C-ABI tests, JavaScript worker simulation tests, and existing interpreter regressions, but this environment did not have Emscripten and therefore an actual browser WebAssembly build has **not** been verified here. The existing JS-only playground remains functional until a real WASM deployment is compiled.

## Experimental Kasa platform expansion (development branch)

The next platform milestone adds a serialized `.kbc` bytecode format with
a native loader/verifier, [shared language conformance fixtures](./tests/conformance/cases.json),
[VS Code language support prototype](./editors/vscode-kasa/),
[offline-capable web packaging](./playground/), and
[15 runnable examples](./examples/). See the [implementation milestones](./docs/MILESTONES.md),
[language semantics](./docs/SEMANTICS.md), [bytecode RFC](./docs/RFC-0003-kasa-bytecode-format.md),
and [beginner tutorial](./docs/TUTORIAL.md).

**Not yet production-ready:** Emscripten `.wasm` builds, full browser
end-to-end verification, cross-platform binary releases, VS Code Marketplace
publishing and an owner-approved open-source license remain pending.
