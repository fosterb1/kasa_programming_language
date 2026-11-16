# Kasa Programming Language

**A Twi-first programming language for learning, creating, and thinking computationally.**

Kasa is an educational programming-language project intended to become open source, designed to make introductory programming more approachable for Ghanaian learners, especially children, beginners, teachers, and communities where English-first programming syntax can be a barrier.

Kasa's guiding idea is simple: **learners should focus on solving problems, not memorizing unfamiliar English keywords.** The language uses familiar Twi-inspired vocabulary while teaching transferable concepts such as variables, conditions, loops, functions, lists, and debugging.

> **Project status — Early implementation (v0.1.0).** Kasa now includes an initial working Python interpreter, CLI, interactive REPL, five executable examples, and automated tests. The project is **not yet a complete or classroom-ready 1.0 release**; the full engineering specification remains the longer-term target.

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

These programs use implemented Kasa syntax. Runnable versions are available in [`examples/`](./examples/), and the local automated test suite verifies their output.

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
| Tests and runnable examples | 58 local tests passed; five examples verified |
| Tutorials and teacher resources | Planned |
| Twi community language review | Needed before release |

The initial implementation milestone is complete. The next stages are deeper edge-case testing, classroom documentation, an expanded example collection, linguistic review, and release hardening. See [the implementation plan](./docs/IMPLEMENTATION_PLAN.md).

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
