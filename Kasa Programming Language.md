# Kasa Programming Language
## Master Engineering Specification for GitHub Copilot

**Project:** Kasa — a Twi-first programming language and interpreter  
**Document purpose:** Complete implementation instructions for an AI coding agent  
**Initial implementation language:** Python 3.11+  
**Source file extension:** `.kasa`  
**Command-line executable:** `kasa`  
**Initial target:** Windows, Linux, and macOS  
**Primary audience:** Ghanaian children, beginners, teachers, and community learning groups  
**Execution model:** Local interpreter, offline-first  
**Version target:** 1.0.0  
**License:** MIT proposed, subject to the project owner's confirmation

---

# PART I — MASTER INSTRUCTIONS TO COPILOT

## 1. Your role

You are the lead software architect, programming-language engineer, Python developer, test engineer, technical writer, and release engineer for Kasa.

Your task is to build a complete, working, maintainable programming language and interpreter based on this specification.

Do not treat this as a request to produce a demonstration script. Build a genuine language implementation with a lexer, parser, abstract syntax tree, runtime environment, evaluator, command-line interface, tests, example programs, packaging, and documentation.

The final result must be usable by someone who is learning programming for the first time.

## 1.1 Rules you must follow

1. Inspect the existing repository before making changes.
2. Preserve useful existing work.
3. If the repository is empty, create the complete project structure specified in this document.
4. Implement the project in milestones, but continue through every milestone until all required features are complete.
5. Do not stop after creating a plan or writing documentation.
6. Do not leave core functionality as pseudocode, placeholder methods, empty implementations, or unresolved TODO comments.
7. Write automated tests for every important language feature.
8. Run the tests after implementing each major component.
9. Fix failures before proceeding to the next milestone.
10. Never use Python `eval()` or `exec()` to execute Kasa programs.
11. Never translate Kasa source code into Python source code and execute it.
12. Implement a dedicated lexer, parser, AST, and interpreter.
13. Keep the core runtime dependent only on the Python standard library.
14. Use UTF-8 consistently.
15. Support Twi-specific characters such as `ɛ`, `Ɛ`, `ɔ`, and `Ɔ`.
16. Produce useful error messages instead of raw Python tracebacks for ordinary programming mistakes.
17. Make the command-line interface usable without an internet connection.
18. Document all syntax, semantics, limitations, and installation procedures.
19. Ensure that all example programs actually run.
20. Do not claim a feature works until it has been implemented and tested.

If a requested feature is ambiguous, make the simplest consistent choice, document it, and add tests. Do not silently change the language design.

## 1.2 Definition of complete

Kasa 1.0 is complete when:

- A user can install it in a Python virtual environment.
- A user can execute a `.kasa` source file.
- A user can check a program's syntax without executing it.
- A user can use an interactive REPL.
- Variables, arithmetic, comparisons, conditions, loops, functions, lists, and input work.
- Unicode source files work correctly.
- The interpreter enforces execution limits.
- The parser produces helpful syntax errors.
- The runtime produces helpful execution errors.
- Automated tests cover valid programs, invalid programs, and edge cases.
- At least 15 example programs are included.
- A beginner's tutorial is available.
- A complete language reference is available.
- The architecture is documented.
- The package can be installed using `pip install -e .`.
- The command `python -m kasa` works.
- No core feature remains a placeholder.
- The documentation matches the implemented language.

---

# PART II — PRODUCT VISION

## 2. What is Kasa?

Kasa is a programming language designed to help Ghanaian children and beginners learn how to instruct computers using familiar Twi vocabulary.

The objective is to reduce the language barrier that can make programming difficult for learners whose first language is not English.

Kasa must teach real programming concepts, including:

- Instructions
- Variables
- Numbers and text
- Arithmetic
- Comparisons
- Decisions
- Repetition
- Functions
- Lists
- Input and output
- Debugging
- Problem-solving

The language should feel simple when reading a program, while its internal implementation should follow sound programming-language engineering practices.

## 2.1 The guiding principle

**The learner should think about solving a problem, not struggle to remember unfamiliar English keywords.**

For example:

```kasa
ka "Maakye, Ghana!"

ma edin = "Ama"

ka edin
```

Expected output:

```text
Maakye, Ghana!
Ama
```

The Python implementation underneath may contain classes, tokens, parser functions, and runtime objects. A learner writing Kasa should not need to understand those internal details to use the language.

## 2.2 Target users

Kasa should support:

1. Children learning programming for the first time.
2. Secondary-school students.
3. University students exploring interpreters.
4. Teachers introducing computational thinking.
5. Rural learning groups with limited computer access.
6. Developers interested in local-language computing.
7. Fluent Twi speakers helping refine the language.
8. Community organizations promoting digital education.

## 2.3 Design principles

- Twi-first, not English-first.
- Small and memorable syntax.
- Consistent behavior.
- Beginner-friendly errors.
- Offline execution.
- Low hardware requirements.
- No mandatory accounts or cloud services.
- No hidden network activity.
- No arbitrary operating-system access from programs.
- Clear separation between source language and interpreter implementation.
- Simple code that contributors can understand.
- Room for future expansion.

## 2.4 Linguistic review

All proposed Twi keywords in this specification are provisional.

Before public educational adoption, have fluent Twi speakers and teachers review:

- Vocabulary
- Spelling
- Grammar
- Regional usage
- Readability for children
- Pronunciation
- Error-message wording

Do not claim that one set of words represents every Twi dialect or every Ghanaian language.

---

# PART III — LANGUAGE DESIGN

## 3. Canonical vocabulary

Use the following proposed keywords consistently in version 1.0.

| Keyword | Intended purpose |
|---|---|
| `ka` | Display a value |
| `ma` | Declare or assign a variable |
| `sɛ` | Begin a conditional |
| `anyɛ_saa_a` | Alternative branch |
| `mpɛn` | Repeat a specified number of times |
| `bere_a` | Repeat while a condition is true |
| `dwumadie` | Define a function |
| `sanma` | Return a value |
| `awiei` | End a block |
| `nokware` | Boolean true |
| `atoro` | Boolean false |
| `hwee` | No value |
| `ne` | Logical AND |
| `anaa` | Logical OR |
| `ɛnyɛ` | Logical NOT |
| `gyae` | Break out of a loop |
| `toa_so` | Continue to the next iteration |
| `bisa` | Read user input when called as a built-in |
| `tentɛn` | Length built-in |
| `nɔma` | Number-conversion built-in |
| `nsɛm` | Text-conversion built-in |

### 3.1 Why underscores are used

Use `anyɛ_saa_a`, `bere_a`, and `toa_so` as canonical keyword spellings in version 1.0.

Although spaces may be natural in ordinary Twi phrases, spaces introduce ambiguity into tokenization and parsing. A single token with underscores is easier to implement, teach, test, and type consistently.

This is an intentional technical choice, not a claim that underscores are linguistically more natural.

If fluent-speaker review recommends other names, update the vocabulary in one documented language-design revision before release.

### 3.2 Keyword rules

- Keywords are lowercase and case-sensitive.
- Reserved keywords cannot be used as identifiers.
- Keywords must be recognized as whole tokens.
- A keyword inside a string must remain ordinary text.
- Unicode characters must not be silently removed or changed.
- Do not create undocumented aliases.
- Keep the initial vocabulary small.
- Do not introduce English aliases merely to make implementation easier.

---

## 4. Hello world

A complete first program should be:

```kasa
ka "Maakye, Ghana!"
```

Running it should produce:

```text
Maakye, Ghana!
```

This must be the first example in the tutorial and the main smoke test for the interpreter.

## 5. Variables

Example:

```kasa
ma edin = "Ama"
ma mfe = 12
ma kurom = "Kasapin"

ka edin
ka mfe
ka kurom
```

Variables store values that can be reused later.

Reassignment is allowed:

```kasa
ma dodow = 5
ma dodow = dodow + 3

ka dodow
```

Expected output:

```text
8
```

Rules:

1. `ma` must be followed by a valid identifier.
2. An assignment must contain `=`.
3. The right-hand expression must be valid.
4. A variable can be reassigned.
5. Reading an undefined variable produces a name error.
6. Variables must not silently become global when created inside a function.
7. The assignment statement does not print a value automatically.

## 6. Data types

Support these types:

| Type | Examples |
|---|---|
| Integer | `0`, `5`, `-10` |
| Decimal | `2.5`, `0.75` |
| String | `"Ama"`, `"Maakye"` |
| Boolean | `nokware`, `atoro` |
| No-value | `hwee` |
| List | `[1, 2, 3]` |
| Function | A function defined with `dwumadie` |

The implementation must validate operations explicitly.

Python's implicit type behavior must not determine Kasa's language semantics.

For example, booleans must not be treated as integers merely because Python's `bool` is a subclass of `int`.

## 7. Arithmetic

Support these operators:

| Operator | Purpose |
|---|---|
| `+` | Addition or string concatenation |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `%` | Integer remainder |
| Unary `-` | Numeric negation |

Example:

```kasa
ma a = 10
ma b = 3

ka a + b
ka a - b
ka a * b
ka a / b
ka a % b
```

Expected output:

```text
13
7
30
3.3333333333333335
1
```

The exact displayed decimal formatting may be improved for readability, but the internal behavior must be consistent and documented.

### 7.1 Arithmetic rules

- Arithmetic operands must be numeric.
- Booleans are not numeric operands.
- `/` always returns a decimal value.
- `%` requires integer operands.
- Division by zero produces a runtime error.
- Remainder by zero produces a runtime error.
- Invalid operand combinations produce type errors.
- Arithmetic must not execute Python source code.
- Negative numbers must be parsed using the unary-minus operator.

### 7.2 String concatenation

Allow `+` between two strings.

```kasa
ma edin = "Ama"
ka "Maakye, " + edin
```

Expected output:

```text
Maakye, Ama
```

Do not silently concatenate numbers and strings.

The learner must explicitly convert values when needed.

---

# PART IV — EXPRESSIONS AND GRAMMAR

## 8. Operator precedence

Implement the following precedence from highest to lowest:

1. Parentheses, literals, variable references, calls, indexing, lists
2. Unary minus and logical NOT
3. Multiplication, division, remainder
4. Addition and subtraction
5. Comparisons
6. Equality
7. Logical AND
8. Logical OR

Example:

```kasa
ka 2 + 3 * 4
ka (2 + 3) * 4
```

Expected output:

```text
14
20
```

The parser must not evaluate expressions from left to right without respecting precedence.

## 9. Comparisons

Support:

- `==`
- `!=`
- `<`
- `<=`
- `>`
- `>=`

Example:

```kasa
ka 5 > 3
ka 5 == 5
ka 4 != 7
```

Expected output:

```text
nokware
nokware
nokware
```

Rules:

- Numeric comparisons may compare integers and decimals.
- Equality comparisons may compare compatible values.
- Ordering comparisons between incompatible types must produce errors.
- Do not allow undocumented comparison chaining.
- The result of a comparison is a Boolean.

## 10. Logical operations

Support:

```kasa
ma a = nokware
ma b = atoro

ka a ne b
ka a anaa b
ka ɛnyɛ a
```

Expected output:

```text
atoro
nokware
atoro
```

Only Boolean operands are accepted.

Implement short-circuit evaluation:

- If the left side of `ne` is false, do not evaluate the right side.
- If the left side of `anaa` is true, do not evaluate the right side.

Add tests proving that skipped expressions are not evaluated.

## 11. Parentheses

Example:

```kasa
ma mmuae = (4 + 6) * 2
ka mmuae
```

Expected output:

```text
20
```

Unmatched parentheses must produce a syntax error with a useful location.

## 12. Comments

Use `#` for single-line comments.

```kasa
# Eyi yɛ me program a edi kan.

ka "Maakye!"
```

Rules:

- Comments end at the line ending.
- `#` inside a string is ordinary text.
- Comments are ignored by the parser.
- Comments do not execute.
- Blank lines are allowed.

---

# PART V — CONDITIONS AND CONTROL FLOW

## 13. Conditional statements

Canonical syntax:

```kasa
ma mfe = 12

sɛ mfe >= 10 a
    ka "Wubetumi akɔ sukuu no mu."
anyɛ_saa_a
    ka "Ɛsɛ sɛ yɛsan hwɛ."
awiei
```

Expected output:

```text
Wubetumi akɔ sukuu no mu.
```

### 13.1 Conditional rules

- `sɛ` begins a conditional statement.
- `a` terminates the condition header.
- `anyɛ_saa_a` introduces an optional alternative branch.
- `awiei` terminates the conditional block.
- The condition must evaluate to a Boolean.
- The alternative branch is optional.
- Only one alternative branch is allowed in version 1.0.
- Nested conditions must work.
- An unmatched `awiei` must be rejected.
- A missing `awiei` must be rejected.
- Both branches must be parsed, but only the selected branch executes.

Example of a nested condition:

```kasa
ma mfe = 15
ma sika = 20

sɛ mfe >= 13 a
    sɛ sika >= 10 a
        ka "Woreyɛ krado."
    anyɛ_saa_a
        ka "Ɛsɛ sɛ wode sika sie."
    awiei
anyɛ_saa_a
    ka "Kɔ so sua."
awiei
```

The parser must handle nested blocks recursively.

## 14. Counted loops

Syntax:

```kasa
mpɛn 5
    ka "Kasa"
awiei
```

Expected output:

```text
Kasa
Kasa
Kasa
Kasa
Kasa
```

A variable may be used as the count:

```kasa
ma dodow = 3

mpɛn dodow
    ka "Maakye"
awiei
```

Rules:

- The count must evaluate to a non-negative integer.
- A count of zero executes the body zero times.
- Negative counts are errors.
- Decimal counts are errors.
- String counts are errors.
- Boolean counts are errors.
- Loop execution counts against the global execution budget.
- Nested counted loops are supported.

## 15. While loops

Syntax:

```kasa
ma n = 1

bere_a n <= 5
    ka n
    ma n = n + 1
awiei
```

Expected output:

```text
1
2
3
4
5
```

Rules:

1. Evaluate the condition before every iteration.
2. Execute the body only if the condition is true.
3. Require a Boolean condition.
4. Allow nested loops.
5. Support `gyae` and `toa_so`.
6. Enforce the execution-step limit.
7. Do not hang forever on an infinite loop.

## 16. Break and continue

Example:

```kasa
ma n = 0

bere_a nokware
    ma n = n + 1

    sɛ n == 3 a
        gyae
    awiei

    ka n
awiei
```

Expected output:

```text
1
2
```

`gyae` terminates the nearest enclosing loop.

`toa_so` skips the remainder of the current loop body and starts the next iteration.

Both commands must be rejected when used outside a loop.

They must also behave correctly inside nested loops.

---

# PART VI — FUNCTIONS

## 17. Function declarations

Syntax:

```kasa
dwumadie ka_maakye(edin)
    ka "Maakye, " + edin
awiei

ka_maakye("Ama")
ka_maakye("Kofi")
```

Expected output:

```text
Maakye, Ama
Maakye, Kofi
```

A function declaration does not execute its body.

The function executes when called.

## 18. Function parameters

Example:

```kasa
dwumadie ka_din_na_mfe(edin, mfe)
    ka edin
    ka mfe
awiei

ka_din_na_mfe("Ama", 12)
```

Rules:

- Parameters are positional.
- The number of supplied arguments must match the declared parameter count.
- Duplicate parameter names are rejected.
- Undefined functions produce a name error.
- Functions may call other functions.
- Function definitions may appear inside the top-level program.
- Nested function declarations are out of scope unless deliberately implemented and documented.

## 19. Returning values

Syntax:

```kasa
dwumadie fa_bi_na_bi(a, b)
    sanma a + b
awiei

ma mmuae = fa_bi_na_bi(4, 6)
ka mmuae
```

Expected output:

```text
10
```

Rules:

- `sanma` returns a value and exits the current function.
- A function without an explicit return produces `hwee`.
- `sanma` outside a function is an error.
- Returning from a nested loop exits the function, not just the loop.
- Return values must not leak into the next function call.
- Call depth must be limited to protect the Python runtime.

## 20. Function scope

Implement lexical scope with environment objects.

Recommended behavior:

- Global variables exist in the global environment.
- Each function call creates a local environment.
- Parameters exist in that local environment.
- Local assignments stay local.
- Local variables disappear when the function returns.
- Reading an unknown variable raises a name error.
- Functions can access global variables if they are not shadowed by local variables.
- Local assignments do not silently modify global variables.

Example:

```kasa
ma x = 10

dwumadie sɔ_hwɛ()
    ma x = 20
    ka x
awiei

sɔ_hwɛ()
ka x
```

Expected output:

```text
20
10
```

This behavior must be covered by automated tests.

---

# PART VII — LISTS AND BUILT-INS

## 21. Lists

Example:

```kasa
ma nɔma = [10, 20, 30]

ka nɔma[0]
ka nɔma[1]
ka nɔma[2]
ka tentɛn(nɔma)
```

Expected output:

```text
10
20
30
3
```

Rules:

- Lists use zero-based indexing.
- Empty lists are supported.
- List elements may have different types.
- Invalid indexes produce friendly errors.
- Boolean indexes are rejected.
- List mutation must be explicitly defined.
- No Python object attributes are exposed.
- Nested lists may be supported.
- Excessively large lists are rejected.

Support list indexing in expressions and assignment targets if the implementation can do so cleanly.

Example:

```kasa
ma nɔma = [10, 20, 30]
ma nɔma[1] = 99
ka nɔma[1]
```

Expected output:

```text
99
```

If list-element assignment is implemented, ensure that it is parsed as an assignment target rather than a normal expression.

## 22. Built-in functions

Implement the following built-ins.

### 22.1 Input

```kasa
ma edin = bisa()
```

`bisa()` reads one line from standard input and returns a string.

Rules:

- Takes zero arguments.
- Does not execute the supplied text.
- Handles end-of-input gracefully.
- Must not read files or environment variables.

### 22.2 Length

```kasa
ka tentɛn("Ghana")
ka tentɛn([1, 2, 3])
```

Expected output:

```text
5
3
```

Accept a string or list and return an integer.

### 22.3 Number conversion

```kasa
ma mfe = nɔma("12")
ka mfe
```

Expected output:

```text
12
```

Rules:

- Accept integers, decimals, and valid numeric strings.
- Reject malformed numeric strings.
- Do not accept Boolean values as numbers.
- Handle surrounding whitespace consistently.
- Explain invalid input clearly.

### 22.4 Text conversion

```kasa
ma mfe = 12
ka nsɛm(mfe)
```

Expected output:

```text
12
```

Define how strings, numbers, Booleans, lists, and `hwee` are converted to text.

### 22.5 Built-in safety

Built-ins must not expose:

- Python `eval`
- Python `exec`
- Python imports
- Filesystem operations
- Subprocess execution
- Arbitrary object introspection
- Network access
- Environment variables

Every built-in must validate its argument count and argument types.

---

# PART VIII — LANGUAGE IMPLEMENTATION

## 23. Required architecture

Implement the following pipeline:

```text
Kasa source code
       |
       v
Source reader
       |
       v
Lexer
       |
       v
Token stream
       |
       v
Parser
       |
       v
Abstract syntax tree
       |
       v
Interpreter
       |
       v
Controlled runtime operations
       |
       v
Program output
```

Keep these components separate.

Do not create a single giant function that reads strings and executes commands using `if` statements.

Do not implement the language through string replacement.

## 24. Lexer

The lexer converts source text into tokens.

Required token categories:

- Identifier
- Integer
- Decimal
- String
- Keyword
- Plus
- Minus
- Star
- Slash
- Percent
- Assignment
- Equality
- Inequality
- Less-than
- Less-than-or-equal
- Greater-than
- Greater-than-or-equal
- Left parenthesis
- Right parenthesis
- Left bracket
- Right bracket
- Comma
- Newline
- End of file

Every token should retain:

- Token type
- Original lexeme
- Parsed literal value when appropriate
- Line number
- Column number
- Source filename when available

The lexer must:

1. Recognize Unicode identifiers.
2. Preserve Twi characters.
3. Recognize strings and escapes.
4. Ignore comments outside strings.
5. Report unterminated strings.
6. Reject invalid characters.
7. Distinguish keywords from longer identifiers.
8. Recognize operators using longest-match rules.
9. Preserve accurate source positions.
10. Support LF and CRLF line endings.

Recommended implementation:

```python
tokens = Lexer(
    source,
    filename="program.kasa"
).scan_tokens()
```

This is an illustrative interface. Maintain a clean, documented API even if the exact names differ.

## 25. Parser

Build a real recursive-descent parser.

The parser must convert tokens into AST nodes.

It must:

- Implement operator precedence.
- Support nested blocks.
- Support function calls.
- Support list literals and indexing.
- Reject malformed expressions.
- Reject missing block terminators.
- Reject unexpected block terminators.
- Track source locations.
- Never execute code during parsing.
- Recover from errors where practical in the REPL.

Do not parse blocks by searching for the next string occurrence of `awiei`. Parse statements recursively until the appropriate terminator is reached.

## 26. Abstract syntax tree

Use explicit AST node types.

Suggested expression nodes:

- `LiteralExpr`
- `VariableExpr`
- `UnaryExpr`
- `BinaryExpr`
- `LogicalExpr`
- `GroupingExpr`
- `CallExpr`
- `ListExpr`
- `IndexExpr`

Suggested statement nodes:

- `PrintStmt`
- `AssignStmt`
- `IfStmt`
- `RepeatStmt`
- `WhileStmt`
- `FunctionStmt`
- `ReturnStmt`
- `BreakStmt`
- `ContinueStmt`
- `ExpressionStmt`

Use Python dataclasses where appropriate.

AST nodes should preserve sufficient source information to produce helpful diagnostics.

## 27. Interpreter

The interpreter evaluates the AST.

It must:

- Evaluate literals and expressions.
- Look up variables.
- Perform operations using Kasa semantics.
- Execute statements in order.
- Maintain environments and local scopes.
- Evaluate conditional branches.
- Execute loops.
- Call functions.
- Return function values.
- Support list operations.
- Validate types.
- Enforce resource limits.
- Produce structured Kasa errors.

Use dedicated runtime mechanisms for return, break, and continue. They may use internal control-flow exceptions or explicit result objects, but raw Python exceptions must not leak into normal user-facing output.

## 28. Environment

Create an `Environment` abstraction.

Responsibilities:

- Store variables.
- Look up variables.
- Assign values.
- Link local environments to enclosing environments.
- Enforce scope rules.
- Produce name errors for undefined variables.

Do not keep all variables in a single global dictionary after functions are introduced.

## 29. Runtime values

Create a clear runtime representation for values.

The implementation may use validated Python primitives for basic values, but user programs must never gain access to arbitrary Python objects.

Use a dedicated function representation, such as `KasaFunction`, for user-defined functions.

Centralize type checks and formatting so the interpreter does not implement slightly different rules in different places.

## 30. Diagnostics

Create structured exception classes, including:

- `KasaError`
- `KasaLexError`
- `KasaParseError`
- `KasaRuntimeError`
- `KasaNameError`
- `KasaTypeError`
- `KasaLimitError`

Errors should retain:

- Message
- Filename
- Line
- Column
- Source line where available
- Optional hint
- Error category

The CLI should format diagnostics. The lexer, parser, and interpreter should not each implement their own unrelated terminal formatting.

---

# PART IX — CLI AND REPL

## 31. Command-line interface

Create a console command named `kasa`.

### Run a program

```bash
kasa run examples/hello.kasa
```

### Check syntax

```bash
kasa check examples/hello.kasa
```

This command must parse the file without executing program statements.

### Start interactive mode

```bash
kasa repl
```

### Show version

```bash
kasa --version
```

### Show help

```bash
kasa --help
```

Use Python's `argparse` unless a clear technical reason justifies another dependency.

## 32. Exit codes

Use stable, documented exit codes.

Recommended:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Runtime error |
| `2` | Lexical or syntax error |
| `3` | File or CLI usage error |
| `4` | Resource limit exceeded |

Tests must verify exit codes.

Program output goes to stdout. Diagnostic messages go to stderr.

## 33. REPL

Example:

```text
Kasa — Twi-first programming language
Type 'firi' to exit.

Kasa> ka "Maakye!"
Maakye!
Kasa> ma n = 5
Kasa> ka n + 2
7
Kasa> firi
Meda wo ase. Goodbye!
```

Requirements:

- Variables persist during the session.
- Errors do not terminate the entire session.
- Ctrl+C exits cleanly.
- EOF exits cleanly.
- Multiline blocks are buffered until the matching `awiei`.
- A syntax error allows the user to continue.
- No telemetry is collected.
- No history is saved to disk in version 1.0.
- Prompt wording can be bilingual.

---

# PART X — SAFETY AND RESOURCE MANAGEMENT

## 34. Execution limits

Kasa must prevent accidental infinite loops and common resource-exhaustion mistakes.

Suggested initial limits:

| Resource | Default limit |
|---|---:|
| Source file size | 1 MB |
| Executed statement/expression steps | 100,000 |
| Function call depth | 100 |
| Maximum list length | 100,000 |
| Maximum string length | 1 MB |
| Maximum parser nesting depth | 200 |

These are starting values. Adjust them if testing reveals a problem, but document the chosen defaults.

Use a centralized limits configuration rather than scattering numeric constants throughout the code.

When a limit is exceeded, raise a `KasaLimitError` with a useful message.

## 35. Infinite-loop protection

Example:

```kasa
bere_a nokware
    ka "Kasa"
awiei
```

This program must not run forever.

When the execution budget is exhausted, stop execution and report a helpful error.

The error should identify the current source location when practical.

## 36. Security requirements

Never use:

- `eval()` to evaluate Kasa expressions.
- `exec()` to execute Kasa source.
- Python compilation of Kasa source.
- Shell commands originating from Kasa programs.
- Unrestricted Python imports.
- Unrestricted reflection.
- Arbitrary file access.
- Network requests from the language runtime.

Input from `bisa()` is plain text.

The interpreter must not automatically treat user input as executable code.

**Security limitation:** Resource limits and the absence of host-code execution do not make this interpreter a hardened sandbox for running untrusted programs on a shared server. Document that distinction.

---

# PART XI — PROJECT STRUCTURE

## 37. Required files

Create a project structure similar to this:

```text
kasa/
├── pyproject.toml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
├── .gitignore
├── .editorconfig
├── .github/
│   └── workflows/
│       └── tests.yml
├── src/
│   └── kasa/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── source.py
│       ├── tokens.py
│       ├── lexer.py
│       ├── ast_nodes.py
│       ├── parser.py
│       ├── environment.py
│       ├── values.py
│       ├── interpreter.py
│       ├── builtins.py
│       ├── diagnostics.py
│       ├── limits.py
│       └── version.py
├── tests/
│   ├── conftest.py
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_expressions.py
│   ├── test_variables.py
│   ├── test_conditionals.py
│   ├── test_loops.py
│   ├── test_functions.py
│   ├── test_lists.py
│   ├── test_builtins.py
│   ├── test_errors.py
│   ├── test_cli.py
│   ├── test_unicode.py
│   └── test_limits.py
├── examples/
│   ├── hello.kasa
│   ├── greetings.kasa
│   ├── variables.kasa
│   ├── arithmetic.kasa
│   ├── decisions.kasa
│   ├── repeat.kasa
│   ├── while_loop.kasa
│   ├── functions.kasa
│   ├── lists.kasa
│   ├── quiz.kasa
│   ├── calculator.kasa
│   ├── multiplication_table.kasa
│   ├── savings.kasa
│   ├── temperature.kasa
│   └── number_game.kasa
└── docs/
    ├── IMPLEMENTATION_PLAN.md
    ├── LANGUAGE_REFERENCE.md
    ├── TUTORIAL.md
    ├── GRAMMAR.md
    ├── ARCHITECTURE.md
    ├── ERROR_MESSAGES.md
    ├── TEACHER_GUIDE.md
    ├── CONTRIBUTING_LANGUAGE.md
    ├── ROADMAP.md
    └── FAQ.md
```

You may make small changes if necessary, but document them.

Do not create empty files merely to satisfy the directory structure.

## 38. Packaging

Use `pyproject.toml`.

Requirements:

- Python 3.11 or later.
- A valid package configuration.
- A console script named `kasa`.
- `python -m kasa` support.
- Editable installation support.
- Core runtime dependencies limited to the standard library.
- Pytest may be used as a development dependency.
- Include version metadata.
- Ensure installation instructions match the actual package configuration.

Developer setup:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS activation:

```bash
source .venv/bin/activate
```

Verify these commands in a clean environment.

---

# PART XII — TESTING

## 39. Test philosophy

Tests are mandatory.

Do not rely on manual demonstrations alone.

Every language feature must have:

1. At least one successful test.
2. At least one invalid-input test where applicable.
3. Tests for relevant boundary conditions.
4. A regression test for every discovered bug.

## 40. Lexer tests

Test:

- All operators.
- All punctuation.
- Integers.
- Decimals.
- Strings.
- Escape sequences.
- Comments.
- Blank lines.
- Unicode identifiers.
- Twi characters.
- Unexpected characters.
- Unterminated strings.
- Keyword recognition.
- Keywords inside strings.
- LF and CRLF files.
- Correct line and column tracking.

## 41. Parser tests

Test:

- Every statement.
- Every expression type.
- Operator precedence.
- Parentheses.
- Function calls.
- List literals.
- List indexing.
- Nested conditions.
- Nested loops.
- Missing `awiei`.
- Unexpected `awiei`.
- Invalid assignments.
- Missing expressions.
- Invalid function declarations.
- Invalid argument lists.
- Invalid multi-line blocks.
- Empty source files.

## 42. Runtime tests

Test:

- Output.
- Variables.
- Reassignment.
- Undefined names.
- Numeric arithmetic.
- String concatenation.
- Type mismatches.
- Division by zero.
- Remainder by zero.
- Comparisons.
- Logical operations.
- Short-circuit evaluation.
- Conditional execution.
- Zero-count loops.
- Positive-count loops.
- Invalid loop counts.
- While loops.
- Break and continue.
- Infinite-loop protection.
- Function calls.
- Return values.
- Local scope.
- Wrong argument counts.
- Recursion limits.
- List indexing.
- List mutation.
- Built-in validation.
- Input handling.
- Execution limits.

## 43. CLI tests

Test:

- Running a valid program.
- Running a nonexistent file.
- Checking valid syntax.
- Checking invalid syntax.
- Confirming `check` does not execute program statements.
- REPL startup.
- REPL exit.
- Version output.
- Help output.
- Exit codes.
- stdout and stderr separation.
- Unicode source files.

## 44. Unicode tests

Create explicit tests using examples such as:

```kasa
ma ɛdin = "Ama"
ma ɔman = "Ghana"

ka ɛdin
ka ɔman
```

The lexer must preserve the identifiers and the interpreter must retrieve their values correctly.

Do not use ASCII-only regular expressions that silently reject valid Twi characters.

Identifier rules should be documented and tested. Use a deliberate Unicode-aware approach rather than accepting arbitrary punctuation as part of a name.

## 45. Safety tests

Verify that:

- Kasa does not execute Python source code.
- Import statements are not accepted as Kasa statements.
- Shell commands are not executed.
- Arbitrary file access is unavailable.
- Division by zero produces a controlled runtime error.
- Infinite loops stop at the configured limit.
- Excessive recursion produces a controlled error.
- Excessive list or string allocation is limited where supported.

Also search the codebase for `eval(` and `exec(`. Review any occurrences rather than relying on a simple text search alone, because names in comments or tests may be legitimate.

---

# PART XIII — EXAMPLE PROGRAMS

## 46. Required examples

All examples must be complete, runnable, and consistent with the actual grammar.

### 46.1 Hello world

```kasa
# Our first program
ka "Maakye, Ghana!"
```

### 46.2 Greeting

```kasa
ma edin = "Kofi"
ka "Maakye, " + edin
```

### 46.3 Variables

```kasa
ma mfe = 20
ma sika = 100

ka mfe
ka sika
```

### 46.4 Arithmetic

```kasa
ma a = 12
ma b = 4

ka a + b
ka a - b
ka a * b
ka a / b
```

### 46.5 Condition

```kasa
ma sika = 15

sɛ sika >= 10 a
    ka "You have enough."
anyɛ_saa_a
    ka "Save more."
awiei
```

### 46.6 Counted loop

```kasa
mpɛn 5
    ka "Meda wo ase"
awiei
```

### 46.7 While loop

```kasa
ma n = 1

bere_a n <= 5
    ka n
    ma n = n + 1
awiei
```

### 46.8 Function

```kasa
dwumadie fa_bi(a, b)
    sanma a + b
awiei

ka fa_bi(4, 6)
```

### 46.9 Lists

```kasa
ma nɔma = [10, 20, 30]

ka nɔma[0]
ka tentɛn(nɔma)
```

### 46.10 Quiz

```kasa
ka "What is 2 + 3?"
ma mmuae = bisa()

sɛ mmuae == "5" a
    ka "Correct!"
anyɛ_saa_a
    ka "Try again."
awiei
```

### 46.11 Savings calculator

Build a simple program that asks for an initial amount and a regular savings amount, then calculates a total over a specified number of periods.

Validate user input. Do not crash when a user enters text instead of a number.

### 46.12 Multiplication table

Build a multiplication-table example using variables and a loop.

### 46.13 Temperature conversion

Build a Celsius-to-Fahrenheit converter using arithmetic and input.

### 46.14 Odd and even

Use the remainder operator to determine whether an integer is odd or even.

### 46.15 Number guessing

Build a simple guessing exercise if the implemented input and loop semantics support it safely.

### 46.16 Calculator

Ask for two numbers and display their sum. Extend it with other operations only after the basic version is reliable.

Every example must be included in automated example verification. Do not provide examples using syntax the parser does not support.

---

# PART XIV — DOCUMENTATION

## 47. README.md

The README must explain:

- What Kasa is.
- Why it exists.
- Who it is for.
- Which features are implemented.
- Which features are not implemented.
- How to install Python.
- How to install Kasa.
- How to run a program.
- How to start the REPL.
- How to check syntax.
- How to run tests.
- Where to find the tutorial.
- Where to find the language reference.
- How to contribute.
- Which license is used.
- What language review is still needed.

Include a working example:

```kasa
ma edin = "Ama"
ka "Maakye, " + edin
```

Show the expected output.

Do not describe unfinished features as complete.

## 48. TUTORIAL.md

Write a beginner-friendly tutorial in this order:

1. What is programming?
2. Your first Kasa program.
3. Displaying messages.
4. Variables.
5. Numbers.
6. Arithmetic.
7. Text.
8. Conditions.
9. Loops.
10. Functions.
11. Lists.
12. Input.
13. Common errors.
14. Debugging.
15. Mini project.

Every lesson must include:

- Learning objective.
- Code example.
- Expected output.
- Plain-language explanation.
- Practice exercise.
- Answer or teacher notes.

Use short explanations. Avoid assuming that learners know Python.

## 49. LANGUAGE_REFERENCE.md

Document:

- All keywords.
- All operators.
- Data types.
- Literals.
- Variable rules.
- Assignment rules.
- Operator precedence.
- Conditions.
- Loops.
- Functions.
- Scope.
- Lists.
- Built-ins.
- Input/output.
- Error categories.
- Execution limits.
- Unsupported features.

All examples must run exactly as written.

## 50. GRAMMAR.md

Document the actual implemented grammar.

The initial grammar should follow this general shape:

```ebnf
program          = { statement }, EOF ;

statement        = print_stmt
                  | assignment_stmt
                  | if_stmt
                  | repeat_stmt
                  | while_stmt
                  | function_decl
                  | return_stmt
                  | break_stmt
                  | continue_stmt
                  | expression_stmt ;

print_stmt       = "ka", expression, NEWLINE ;

assignment_stmt  = "ma", assignment_target, "=", expression, NEWLINE ;

if_stmt          = "sɛ", expression, "a", NEWLINE,
                   block,
                   [ "anyɛ_saa_a", NEWLINE, block ],
                   "awiei", NEWLINE ;

repeat_stmt      = "mpɛn", expression, NEWLINE,
                   block,
                   "awiei", NEWLINE ;

while_stmt       = "bere_a", expression, NEWLINE,
                   block,
                   "awiei", NEWLINE ;

function_decl    = "dwumadie", IDENTIFIER, "(",
                   [ parameters ], ")",
                   NEWLINE, block, "awiei", NEWLINE ;

parameters       = IDENTIFIER, { ",", IDENTIFIER } ;

return_stmt      = "sanma", [ expression ], NEWLINE ;

break_stmt       = "gyae", NEWLINE ;

continue_stmt    = "toa_so", NEWLINE ;

expression_stmt  = expression, NEWLINE ;
```

This grammar is a starting specification. Refine it into an unambiguous grammar that matches the actual lexer and parser.

Document assignment targets separately so ordinary variables and list-element assignment can be handled correctly.

## 51. ARCHITECTURE.md

Explain:

- Source loading.
- Tokenization.
- Parsing.
- AST nodes.
- Runtime values.
- Environments.
- Expression evaluation.
- Statement execution.
- Functions and scope.
- Control flow.
- Diagnostics.
- Resource limits.
- CLI.
- Testing.
- How to add a new language feature.

A developer should be able to understand the project without reading every source file first.

## 52. TEACHER_GUIDE.md

Include:

- A suggested first lesson.
- Offline classroom setup.
- Exercises for different ability levels.
- Pair-programming activities.
- Ways to explain variables and loops.
- Debugging guidance.
- Respectful handling of mistakes.
- Suggestions for shared computers.
- Adaptation for different Twi-speaking communities.
- Activities that do not require every learner to own a computer.

## 53. CONTRIBUTING_LANGUAGE.md

Explain how people can suggest vocabulary changes.

Every proposal should include:

- Proposed keyword.
- Intended meaning.
- Example sentences.
- Regional or dialect context.
- Why the existing term may be confusing.
- Suggested tests and documentation changes.

Encourage review by fluent speakers and teachers.

## 54. Other documentation

Create meaningful versions of:

- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/ROADMAP.md`
- `docs/ERROR_MESSAGES.md`
- `docs/FAQ.md`

Do not leave empty templates in the final repository.

---

# PART XV — CODE QUALITY AND RELEASE

## 55. Code quality standards

- Use type hints for public interfaces.
- Use descriptive names.
- Keep functions focused.
- Avoid giant classes and giant functions.
- Avoid global mutable runtime state.
- Use dataclasses where appropriate.
- Keep modules reasonably small.
- Add docstrings to public interfaces.
- Keep CLI formatting separate from interpretation.
- Centralize type checking and value formatting.
- Avoid unnecessary dependencies.
- Avoid abstractions that make the code harder for beginners to understand.
- Keep comments accurate.
- Remove dead code.
- Remove unused imports.
- Ensure tests check real behavior.

## 56. Continuous integration

If the project is hosted on GitHub, add a GitHub Actions workflow.

It should:

1. Check out the repository.
2. Set up supported Python versions.
3. Install the package and development dependencies.
4. Run the test suite.
5. Run linting if configured.
6. Run a hello-world smoke test.
7. Verify package imports.

Do not make CI depend on secrets or external services.

## 57. Release readiness

Before declaring version 1.0 ready:

- Run the complete test suite.
- Run all examples.
- Verify clean installation.
- Verify CLI commands.
- Verify Unicode support.
- Review all errors.
- Review the grammar.
- Review execution limits.
- Verify the license.
- Update the changelog.
- Ensure documentation matches the implementation.
- Record outstanding language-review needs.

---

# PART XVI — IMPLEMENTATION MILESTONES

## 58. Milestone 0: Audit and plan

Inspect the repository and create:

`docs/IMPLEMENTATION_PLAN.md`

Record existing code, architecture choices, known ambiguities, and the planned milestones.

**Do not stop after completing this milestone.**

## 59. Milestone 1: Packaging

Implement:

- `pyproject.toml`
- Package initialization
- CLI entry point
- Version command
- Help command
- Basic tests

Acceptance:

```bash
python -m kasa --help
```

works successfully.

## 60. Milestone 2: Lexer

Implement tokens, Unicode identifiers, literals, comments, operators, and source locations.

Acceptance: lexer tests pass, including invalid-character and Unicode tests.

## 61. Milestone 3: Parser and AST

Implement expression parsing, statement parsing, nested blocks, and syntax errors.

Acceptance: all valid documented examples parse, and invalid syntax produces structured errors.

## 62. Milestone 4: Runtime basics

Implement:

- Values
- Variables
- Output
- Arithmetic
- Comparisons
- String concatenation
- Type checking

Acceptance: hello-world, variable, and arithmetic examples work.

## 63. Milestone 5: Conditions

Implement:

- Boolean values
- Logical operators
- Conditional statements
- Alternative branches
- Nested conditions

Acceptance: condition tests pass.

## 64. Milestone 6: Loops

Implement:

- Counted loops
- While loops
- Break
- Continue
- Execution-step limit

Acceptance: loop tests pass, including infinite-loop protection.

## 65. Milestone 7: Functions

Implement:

- Function definitions
- Parameters
- Function calls
- Return values
- Local scope
- Call-depth limits

Acceptance: function tests pass.

## 66. Milestone 8: Lists and built-ins

Implement:

- Lists
- Indexing
- List assignment
- Length
- Input
- Number conversion
- Text conversion

Acceptance: built-in and list tests pass.

## 67. Milestone 9: CLI and REPL

Implement:

- `kasa run`
- `kasa check`
- `kasa repl`
- Multiline REPL support
- Exit codes
- User-facing diagnostics

Acceptance: CLI tests pass.

## 68. Milestone 10: Documentation and examples

Create all required examples and documentation.

Acceptance: every example runs and all documentation matches the language.

## 69. Milestone 11: Quality checks

Run tests, linting, package installation, smoke tests, safety checks, and documentation verification.

Acceptance: the final report includes actual command results and remaining limitations.

**Copilot must continue through every milestone unless blocked by a genuine technical or environmental limitation. If blocked, explain the limitation and complete all independent work that remains possible.**

---

# PART XVII — ACCEPTANCE TESTS

## 70. Test 1: Output

Source:

```kasa
ka "Maakye!"
ka 42
ka nokware
ka atoro
```

Expected output:

```text
Maakye!
42
nokware
atoro
```

## 71. Test 2: Arithmetic

Source:

```kasa
ka 2 + 3 * 4
ka (2 + 3) * 4
```

Expected output:

```text
14
20
```

## 72. Test 3: Assignment

Source:

```kasa
ma x = 10
ma x = x + 5
ka x
```

Expected output:

```text
15
```

## 73. Test 4: Condition

Source:

```kasa
sɛ 5 > 2 a
    ka "yes"
anyɛ_saa_a
    ka "no"
awiei
```

Expected output:

```text
yes
```

## 74. Test 5: Counted loop

Source:

```kasa
mpɛn 3
    ka "x"
awiei
```

Expected output:

```text
x
x
x
```

## 75. Test 6: While loop

Source:

```kasa
ma n = 1

bere_a n <= 3
    ka n
    ma n = n + 1
awiei
```

Expected output:

```text
1
2
3
```

## 76. Test 7: Function

Source:

```kasa
dwumadie fa_bi(a, b)
    sanma a + b
awiei

ka fa_bi(2, 7)
```

Expected output:

```text
9
```

## 77. Test 8: List

Source:

```kasa
ma xs = [10, 20, 30]

ka xs[0]
ka xs[2]
ka tentɛn(xs)
```

Expected output:

```text
10
30
3
```

## 78. Test 9: Undefined variable

Source:

```kasa
ka unknown_name
```

Expected behavior:

- Nonzero exit status.
- Error includes filename, line, and column.
- Error explains that the variable does not exist.
- No raw Python traceback in normal mode.

## 79. Test 10: Division by zero

Source:

```kasa
ka 1 / 0
```

Expected behavior:

- Friendly runtime error.
- No raw Python traceback in normal mode.
- Nonzero runtime-error exit code.

## 80. Test 11: Syntax checking

A file containing:

```kasa
ka "This must not be printed during syntax checking."
```

must pass:

```bash
kasa check examples/check_test.kasa
```

The string must not appear in stdout because the program must not execute.

## 81. Test 12: Infinite-loop protection

A program that never terminates must stop after the execution budget is exhausted and produce a resource-limit error.

## 82. Test 13: Unicode

A program using `ɛ`, `ɔ`, and other supported Unicode characters in strings and identifiers must execute without corruption.

---

# PART XVIII — FUTURE ROADMAP

## 83. Future features

Do not make these version 1.0 blockers:

1. A simple offline graphical editor.
2. Syntax highlighting.
3. A visual debugger.
4. A step-through execution mode.
5. Improved Twi diagnostics reviewed by fluent speakers.
6. More beginner exercises.
7. Classroom lesson packs.
8. Easier installation for school computers.
9. Optional language aliases.
10. Additional Ghanaian language support.
11. Educational graphics and simple games.
12. Dictionaries and more collection types.
13. Modules and package support.
14. A self-hosted educational playground.
15. Carefully designed translation or localization tools.

Build the interpreter first. Do not begin with a graphical IDE, cloud service, or game engine.

---

# PART XIX — FINAL COPILOT REPORT

## 84. Required report

When the work is finished, report:

1. What was implemented.
2. How the interpreter architecture works.
3. The commands required to install Kasa.
4. The command to run a program.
5. The command to check syntax.
6. The command to start the REPL.
7. The command to run tests.
8. The exact tests executed and actual pass/fail counts.
9. The example programs included.
10. The documentation files created.
11. The safety mechanisms implemented.
12. Whether any use of `eval` or `exec` was found in execution code.
13. Any syntax choices that differ from this specification.
14. Features that remain unfinished.
15. Twi vocabulary that still needs review.
16. The most important next steps.

Never claim tests passed unless they were run and passed.

Never claim the implementation is complete merely because the source files have been generated.

---

# PART XX — FINAL DIRECTIVE

Build Kasa as a real programming language.

The Python code is the machinery. Kasa is the language the learner sees.

The initial release should be small, reliable, readable, safe by design, and useful in a classroom with limited resources.

Prioritize, in order:

1. Correctness.
2. Simplicity.
3. Safety.
4. Educational value.
5. Unicode support.
6. Clear diagnostics.
7. Testability.
8. Extensibility.

Do not sacrifice a sound interpreter architecture for a quick demonstration.

Do not add unnecessary features before the required language works.

Do not present proposed Twi vocabulary as linguistically authoritative without review.

**Your final objective is to deliver a complete, tested, documented Kasa interpreter that can run real `.kasa` programs locally and can be extended by future contributors.**
