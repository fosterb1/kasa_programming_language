# Kasa Programming Language

**A Twi-first programming language for learning, creating, and thinking computationally.**

Kasa is an educational programming-language project intended to become open source, designed to make introductory programming more approachable for Ghanaian learners, especially children, beginners, teachers, and communities where English-first programming syntax can be a barrier.

Kasa's guiding idea is simple: **learners should focus on solving problems, not memorizing unfamiliar English keywords.** The language uses familiar Twi-inspired vocabulary while teaching transferable concepts such as variables, conditions, loops, functions, lists, and debugging.

> **Project status — Experimental alpha (native 0.4).** Kasa includes a Python reference interpreter, a browser JavaScript runtime, and a **C++20 native compiler/VM with an experimental KBC1 `.kbc` file format**. There are twenty-six root example programs and an independent local verification runner. Full native KBC1 integration tests passed on Linux, and a **verified complete-checkout Linux parity baseline for the currently implemented Kasa 0.4 portable subset** ([10/10 parity stages, 18/18 full-profile stages on merged commit `cbce6a6`](./docs/verification/2026-11-18-linux-full-parity.md)). **Native arbitrary-precision integers/KBC1, Windows/macOS validation, real-browser WASM, classroom review and secure untrusted-code execution remain unfinished**. Kasa is not a stable 1.0 release. See the [living development journal](./docs/DEVELOPMENT_JOURNAL.md) and [native integration report](./docs/verification/2026-11-17-kbc1-native-integration.md).

## Develop on a MacBook without hosted CI

This project supports a Mac-first, local-test-first workflow (Intel or Apple Silicon, subject to the installed macOS and toolchain). After cloning, use:

```bash
bash scripts/mac_dev.sh doctor
bash scripts/mac_dev.sh setup
bash scripts/mac_dev.sh quick
bash scripts/mac_dev.sh parity
bash scripts/mac_dev.sh full
```

No Vercel, Netlify, Firecrawl or GitHub Actions invocation occurs in these commands. The scripts write reproducible local reports under `build/`. The 4C.2 shared diagnostics corpus tests matching error categories across JavaScript and Python, then the linked native VM during full verification. **Mac-specific certification requires actually running these commands on macOS**; a successful Linux or browser check is not equivalent.

[MacBook setup, Node/Python requirements, Emscripten, Academy tests and release process](./docs/MACOS_LOCAL_DEVELOPMENT.md)

## Phase 5A — local installable macOS developer preview

After a real macOS native parity/full pass, build a **private unsigned developer-preview archive** on that Mac:

```bash
source .venv/bin/activate
bash scripts/mac_dev.sh full
bash scripts/mac_dev.sh package
```

The archive and SHA-256 checksum appear under `build/dist/`. The archive includes a `kasa` launcher and a standalone `kasa-native` executable; users of that binary do not need Python, Node or CMake. No external service, automatic installation or system-wide changes are involved. **This is not a signed/notarized public installer or evidence of Apple Silicon compatibility.** See [Phase 5A packaging and safe extraction guide](./docs/PHASE_5A_MACOS_PREVIEW_PACKAGING.md).

## Phase 5B — unsigned macOS installer and future upgrades

An existing Kasa installation does **not** update when developers change source code. A changed interpreter must be rebuilt, fully tested, packaged with a newer build version, and explicitly installed by the user. The `pkgbuild`-based preview targets `/usr/local/lib/kasa-preview` and an optional `/usr/local/bin/kasa` command, with a collision-checking preinstall script. Build locally with:

```bash
bash scripts/mac_dev.sh full
bash scripts/mac_dev.sh installer
```

This creates an **unsigned `.pkg` without installing it**; inspect it and test on a real Mac before using it. No automatic updates, signing, notarization, public distributions or system changes happen during packaging. See [Phase 5B installer, upgrade and safety guide](./docs/PHASE_5B_INSTALLERS_AND_UPGRADES.md).

## Phase 5C — installed Kasa upgrade audit and uninstall planning

Following a successful **Intel macOS Ventura** installation of preview build `0.4.0.194`, the project now includes read-only checks for installed package ownership, installed release receipt, build metadata, foreign command symlinks and newer-version eligibility:

```bash
bash scripts/mac_dev.sh upgrade-audit
bash scripts/mac_dev.sh uninstall-plan
```

Neither command upgrades nor removes installed files. The uninstaller is deliberately **plan-only**, with execution disabled until safe on-device testing and review. Source programs in home directories are never targets. [Phase 5C usage and limitations](./docs/PHASE_5B_INSTALLERS_AND_UPGRADES.md#phase-5c--safe-upgrade-inspection-and-uninstall-planning-new).

## Phases 5E, 7, 8 and 9 — active Mac-first development

**Phase 6 (Windows cross-platform validation) is reserved for the office Windows machine.** Meanwhile:

- **5E recovery:** `bash scripts/mac_dev.sh recovery-snapshot` creates an ownership-verified backup of installed Kasa files only; `uninstall-plan` remains read-only. Real uninstallation is deliberately disabled.
- **7 developer tooling:** The VS Code extension defaults to the installer-provided `kasa` command and offers help when the executable is missing. Run `node --test editors/vscode-kasa/tests/*.test.cjs`.
- **8 Academy integration:** Guided lessons link to full first-party Studio, while the optional CMS Netlify URL is a validated separate link—not a replacement for the current Studio WASM build.
- **9 public alpha:** `python3 scripts/audit_public_alpha.py` reports blockers and writes `build/public-alpha-gate.json`. A nonzero result is expected until licensing, signed builds, platform evidence and educator/security reviews are complete. **No public release is authorized.**

See [Phases 5E/7/8/9 progress and local verification steps](./docs/PHASE_5E_7_8_9_PLAN_AND_PROGRESS.md).

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

Try [a market cashbook](./examples/market_cashbook.kasa), [inventory reorder logic](./examples/stock_reorder.kasa), [a school-fee calculation](./examples/school_fees.kasa), [cash reconciliation](./examples/cash_reconciliation.kasa), or [a mobile-money ledger](./examples/mobile_money_ledger.kasa). All currency values in these lessons are **integer pesewas**, avoiding floating-point rounding in financial examples.

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

## Progress toward Kasa 0.4 and 1.0

Our current [progress scorecard](./docs/PROGRESS_SCORECARD.md) rates **Kasa 0.4 implementation at 8 of 10 checkpoints (80%)** and **stable Kasa 1.0 maturity at approximately 35%** as a planning estimate. These are deliberately different metrics: code existing is not the same as complete interoperability, security, portability or a professionally reviewed educational release.

## Local cross-runtime verification

For Kasa 0.4, the focused `parity` profile independently checks Python, browser JavaScript, native C++ and compiled KBC1 execution. It requires a **complete local checkout** with Python, Node, CMake and a C++20 compiler; no paid GitHub Actions run is needed:

```bash
python -m pip install -e ".[dev]"
python scripts/verify_local.py --profile parity --report build/parity-report.json
# Includes a new 10,080-case deterministic Python/C++ numeric differential
```

The report records the Git commit and whether the checkout is clean. The profile and report design have focused unit-level checks, but **the complete Python-versus-native-KBC1 suite still requires execution before we claim full language parity**. Details: [independent verification guide](./docs/INDEPENDENT_TESTING.md).

## Current progress and roadmap

| Area | Status |
| --- | --- |
| Language vision and engineering specification | Documented |
| Lexer, parser, and AST | Implemented (0.1.0) |
| Interpreter and runtime | Implemented (0.1.0; further hardening planned) |
| CLI, REPL, and packaging | Implemented (0.1.0) |
| Tests and runnable examples | Sixteen root programs; independent browser checks on the merged educational branch passed 89/89; full current-branch native/Python suites still require end-to-end verification |
| Tutorials and teacher resources | Practical example starter set available; complete classroom guides and educator review still planned |
| Twi community language review | Needed before release |

The initial interpreter and native bytecode-VM alpha milestones have working implementations. Current engineering priorities are cross-runtime conformance, independently executed C++ integration tests, KBC1 verification, classroom documentation, linguistic review and release hardening. Follow the [implementation plan](./docs/IMPLEMENTATION_PLAN.md) and the [engineering development journal](./docs/DEVELOPMENT_JOURNAL.md), which distinguishes merged features, verified checks and outstanding risks.

A version 1.0 release will require a working, tested interpreter—not merely completed documentation. The specification's minimum of 15 runnable example programs is now met (15/15 direct JavaScript output checks passed on 2026-11-18); tests for successful behavior, invalid input, Unicode, and resource limits.

## Cross-runtime arithmetic contract

Kasa's `%` operator uses **floor-based integer remainder** consistently in Python, browser JavaScript and the native C++ VM. For example, `-7 % 3` must return `2` and `7 % -3` must return `-2`. The implementation is accompanied by [a language-semantics RFC](./docs/RFC-0003-remainder-semantics.md) and [shared conformance fixtures](./tests/conformance_remainder.json). **The test corpus covers ordinary and negative operands, large exact integers, zero divisors and type errors.**

The three engines retain other documented differences, notably the native 64-bit integer range; this is **not** a declaration of full language parity.

**Numeric precision improvement (Kasa 0.4 alpha):** [PR #23](https://github.com/fosterb1/kasa_programming_language/pull/23) corrected mixed integer/decimal comparison logic to avoid rounding large integers through binary64, with 18 shared regression cases. Focused JavaScript/C++ checks passed; full native VM and Python/KBC1 integration verification of this change remains outstanding. [Verification and known limitations](./docs/verification/2026-11-18-mixed-numeric-comparison.md). This work does not claim that mixed-type arithmetic or every financial computation is exact.


**Decimal display compatibility (targeted repair, 2026-11-18):** The browser now displays binary64 decimal values using Python-reference exponent thresholds and signed-zero conventions. **12/12 new decimal fixtures** and **129/129 combined direct JS runtime checks** passed independently. This does not establish complete C++/KBC1 output formatting parity. [Independent verification record](./docs/verification/2026-11-18-browser-decimal-display.md).

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

### Practical lesson corpus (15 examples)

Six new programs demonstrate [daily sales totals](./examples/daily_sales.kasa), [cash reconciliation](./examples/cash_reconciliation.kasa), [mobile-money balance arithmetic](./examples/mobile_money_ledger.kasa), [student score counting](./examples/student_grades.kasa), [savings targets](./examples/savings_target.kasa), and [inventory valuation](./examples/inventory_valuation.kasa). All examples are **illustrative offline exercises**, not bank integrations, production-grade bookkeeping, or financial advice. Golden stdout lives in [the shared example fixture](./tests/conformance_practical_examples.json), consumed by Python and browser JavaScript tests. On 2026-11-18, all 15 example outputs passed direct execution using the repository JavaScript interpreter in an isolated V8 environment. Full Python/native/KBC1 and actual-browser verification of these newly added examples remain outstanding.

### One-to-one reconciliation as a Kasa lesson

[Bank and ledger matching](./examples/bank_reconciliation_matching.kasa) demonstrates duplicate-safe, first-unused **amount-only** matching with integer pesewas. The [four-case fixture](./tests/conformance_reconciliation.json) covers duplicates, no matches, zero values and the baseline (4/4 direct JavaScript runtime checks passed on 2026-11-18). This is **not** production bank reconciliation: dates, references, transactions IDs, ambiguity handling, debit/credit normalization, security and audit trails are absent. See [RFC-0006](./docs/RFC-0006-financial-computing-foundation.md) for design gates. Python/native/KBC1 integration checks are registered but not yet executed.

### Kasa core language contract (candidate)

[RFC-0007 — Core Language Contract](./docs/RFC-0007-core-language-contract.md) documents the existing expression precedence, typing, lexical functions, mutable lists, blocks, built-ins and diagnostics to help human contributors and future AI coding tools reason about Kasa consistently. A [12-case executable contract corpus](./tests/conformance_language_contract.json) passed **12/12 direct JavaScript interpreter checks** on 2026-11-18 and is registered in the Node test suite. **This is not a stable 0.5 specification or four-runtime certification.** The PR #31 native reliability gate, Python/native/KBC1 contract conformance and linguistic review remain open; no new Twi vocabulary or license was added.

### Native decimal parity integration (2026-11-18)

The native VM source now uses the targeted round-trip-safe binary64 formatting helper. The native component was independently tested under GCC/Clang and compared with Python on 9,999 finite values; 15 decimal and 12 core language contract cases pass by direct JavaScript execution. **The complete linked native VM, Python, Node and serialized KBC1 suites are not yet independently verified on this merged candidate.** Merging integration work does not close Kasa Step 1 or certify Kasa 0.4 parity. See [native verification evidence](./docs/verification/2026-11-18-native-float-output.md).

### Reconciled Kasa platform experiments

Ten additional teaching programs (sorting, recursion, arithmetic practice, sales and savings) bring the root corpus to **26 examples**, each matched by the shared Python/JavaScript output fixture. A provisional [VS Code extension](./editors/vscode-kasa/) provides highlighting, snippets and local run/check commands; it is not published or end-to-end VS Code certified. The [offline playground package](./playground/build_site.py) bundles versioned service-worker assets and a web manifest, but real-browser offline/WASM operation still needs independent testing. The Python CLI can optionally show beginner-friendly source hints via `kasa run FILE --explain`. No new Twi grammar or open-source license was introduced. [Development journal](./docs/DEVELOPMENT_JOURNAL.md) records verification limits.

**Browser Unicode reliability:** The JavaScript engine now counts Unicode code points when enforcing its 64,000-character output cap for printed text and input prompts. This fixes premature failures when printing emoji and other supplementary Unicode characters. Focused tests passed 5/5 and shared JS conformance cases passed 51/51 in direct V8 execution. The native C++ engine currently measures UTF-8 bytes, and the Python reference does not enforce the same output cap; [RFC-0007](./docs/RFC-0007-core-language-contract.md) records the open standardization question. This does not certify complete runtime parity.

### Kasa output safety contract (candidate)

Kasa's Python reference, browser JavaScript and native C++ runtimes now implement a common limit of **64,000 Unicode characters (code points) of output per execution**. Text printed by `ka`, trailing newlines and `bisa` prompts count toward one budget. Exceeding it raises `ResourceError` before emitting the overflowing operation. See [shared eight-case output-budget fixtures](./tests/conformance_output_budget.json). **Current evidence:** all 8 cases passed in direct JavaScript execution, and 7 isolated native helper assertions passed under GCC/Clang sanitizers. Complete cross-runtime and KBC1 integration tests remain pending; this is not a stability or security certification.

### Intended large-integer model (RFC-0008)

Kasa's intended integer model is **exact arbitrary precision**, bounded by explicit resource limits rather than signed 64-bit overflow. The Python reference interpreter and JavaScript browser runtime already support large integers, and [10 new shared cases](./tests/conformance_arbitrary_integers.json) specify the target behavior. **The C++ native compiler and KBC1 bytecode currently use signed 64-bit integers and do not yet meet this target.** See [RFC-0008](./docs/RFC-0008-arbitrary-precision-integers.md) for the staged migration and verification requirements. This decision is not a claim that a native big-integer backend or big-integer bytecode has shipped.

### Experimental native large integers (RFC-0008)

The C++ VM can be built with `-DKASA_ENABLE_BIGINT_VM=ON` (requires Boost.Multiprecision headers) to run the RFC-0008 large-integer source examples, while the **standard Kasa build continues to use native int64 arithmetic**. The optional feature is not yet a stable, fully portable runtime: large literals are not encodable into existing KBC1 bytecode, Windows/MSVC support remains unverified and a versioned KBC2 extension is planned. See [RFC-0008](./docs/RFC-0008-arbitrary-precision-integers.md) for instructions and constraints.


### Experimental KBC2 big-integer bytecode

Build with `-DKASA_ENABLE_BIGINT_VM=ON` and Boost.Multiprecision headers, then run `kasa-native compile-kbc2 example.kasa -o example.kbc` followed by `kasa-native run-bytecode example.kbc`. KBC2 supports exact large integer constants, while **standard** `compile` continues to produce KBC1 and default native builds do not load KBC2. The format is experimental; see [KBC2 format and limits](./docs/KBC2_FORMAT.md).


### Browser playground: local source files and real-browser testing

The [Kasa playground](./playground/index.html) runs Kasa programs using a JavaScript interpreter in a browser Web Worker, even without native WASM. You can now import UTF-8 `.kasa` files, download source, save only the source draft in your browser profile and reset it. Program input is **not** saved. Draft storage is local to the browser profile, not encrypted. Native WebAssembly remains conditional on a real compiled module included in the deployment.

For reproducible headless Chromium verification (optional developer dependencies):

```sh
python -m pip install playwright
python -m playwright install chromium
python scripts/verify_browser_playground.py
```

This checks the **real JavaScript browser experience**, not native WebAssembly. See [browser verification record](./docs/verification/2026-11-18-real-browser-playground.md).


### Genuine native WebAssembly browser execution (experimental)

Kasa's C++20 native VM can now be compiled with Emscripten, packaged into the playground and run **inside a real Chromium browser Web Worker** (independently verified on Linux). The default website remains JavaScript-only unless both real generated native assets are included; loading failures fall back to JavaScript. The WASM build currently uses native **int64** arithmetic (not the opt-in KBC2/Boost big-integer VM). To build and reproduce:

```sh
bash native/wasm/build.sh
python3 playground/build_site.py --require-wasm
python3 -m pip install playwright
python3 -m playwright install chromium
python3 scripts/verify_real_wasm_browser.py
```

See [real WebAssembly browser validation](./docs/verification/2026-11-18-real-wasm-browser.md). Browser portability, offline mode, deployment and security release gates remain open.


### Netlify static playground deployment

Build a Netlify-ready production directory containing **real native WebAssembly** (the script refuses JS-only output):

```sh
bash scripts/netlify_build.sh
```

Connect the existing Netlify playground site to this GitHub repository, or upload the resulting `dist/netlify` directory to the same site. `netlify.toml` supplies the build command, publish path and embedding headers. The Learning Academy's admin dashboard manages the final Netlify URL under **Website Settings → Playground Settings**, so an administrator can change it without modifying or redeploying academy code. See [Netlify deployment instructions](./docs/NETLIFY_DEPLOYMENT.md).
