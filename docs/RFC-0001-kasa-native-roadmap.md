# RFC-0001 — Kasa beyond Python: a native language ecosystem

**Status:** Draft for maintainer and community review (not adopted as a new language standard).  
**Proposed by:** Kasa contributors  
**Compatibility baseline:** Preserve `.kasa` source grammar and beginner-focused syntax from `Kasa Programming Language.md`.  
**First implementation:** `native/` includes a C++20 compiler to **in-memory bytecode** and stack VM, tagged `0.3.0-alpha`.

## 1. What "independent language" means

Kasa source should be defined by a language specification, not by incidental behavior of Python. An independent compiler and runtime should be able to execute an identical program on a computer that has **no Python or JavaScript installed**. The native runtime must pass shared language-conformance tests; the Python interpreter becomes a reference and teaching tool, not a mandatory deployment requirement.

Kasa is **not yet** self-hosting, compiling to machine code, or feature-complete. This RFC outlines a multi-release engineering program, not an announcement of finished features.

## 2. Proposed components and future ownership

| Component | Responsibility | Current state |
|---|---|---|
| Language standard | Grammar, type/value semantics, diagnostics, Unicode rules | Initial master engineering specification; must become versioned normative spec |
| Frontend | Lexer, source spans, AST, diagnostics | Python, JS and initial C++ native implementations |
| Kasa IR / bytecode | Verified portable instruction set, constants, functions, debug maps | In-memory native bytecode prototype; serialization TBD |
| Kasa VM | Value model, stack frames, GC/memory accounting, safe execution | Initial C++ VM; no GC or verified bytecode loader yet |
| Native / WASM backends | Desktop executable and browser/embedded targets | Native C++ CLI compiled for local platform; WASM and AOT targets unimplemented |
| Standard library | Strings, collections, math, files, JSON, dates, networking | Only 4 built-ins exist; permissions model required for I/O |
| Package manager / registry | Versioning, lockfiles, signed releases, dependencies | Unimplemented |
| Tooling | Formatter, REPL, LSP, VS Code integration, docs | Python REPL and browser editor exist; native disassembler added |
| Curriculum | Beginner modules, Twi translations, offline classroom packs | Playground + examples; classroom review incomplete |

## 3. Milestones, in order

**M1 — Native compiler proof (0.3.0-alpha).** Source → tokens → AST → in-memory bytecode → native VM; CLI `run`, `check`, `disasm`; port existing Kasa constructs; test against Python reference. Preserve the existing codebase. This is the deliverable in this proposal.

**M2 — Formal language conformance.** A shared, runtime-agnostic test corpus with expected stdout, error category, and source spans. Define integer and decimal semantics (including overflow), list identity, string/codepoint handling, function scoping, and stable diagnostics. Fix disparities in Python, JavaScript, and native engines. Never claim 100% parity without a suite that demonstrates it.

**M3 — Bytecode format.** Design `KBC` header, format version, fixed instruction numbers, constant encoding, relocations, source maps, feature flags, bounds, checksums and a bytecode verifier. Reject malicious/truncated files. Prefer a documented bytecode spec before caching or distributing `.kbc` files.

**M4 — Production runtime.** Profile memory/CPU, add allocator quotas, heap accounting and garbage collection, test Unicode and exceptions thoroughly, fuzz lexer/bytecode parser, run sanitizers, and establish a stable public C API only after the safety model is reviewed.

**M5 — Language modules / stdlib.** Define `fa` / import syntax through a separate RFC, module resolution, namespacing, package boundaries, deterministic builds, error handling, useful collections, Unicode text, math, and carefully permissioned file/HTTP access. No unrestricted `eval`, shell execution, or hidden network access.

**M6 — Ecosystem.** Formatter, language server, VS Code extension, automated releases for Windows/Linux/macOS, offline installers, docs website, teaching materials, package manager, and a transparent release/security policy. Conduct review of all Twi keywords with fluent speakers and teachers, including regional variants.

**M7 — WASM and native compilation.** Compile the verified VM to WASM (or build a dedicated wasm backend), evaluate an AOT compiler or LLVM/Cranelift target *after* IR is stable, benchmark alternatives. Avoid committing to a heavyweight JIT before language semantics and package boundaries are fixed.

**M8 — Self hosting (long term).** Expand Kasa enough to implement a meaningful portion of its compiler in Kasa itself. Bootstrap and reproducibly compare bytecode from the host compiler and self-hosted compiler. This is a multi-year possibility, not a current feature.

## 4. Fundamental decisions still requiring approval

- **License:** MIT has been proposed, but not selected. We must not describe the repository as legally open source without a `LICENSE` file and owner's decision.
- **Target users:** Remain approachable to Ghanaian learners while keeping advanced APIs precise enough for professional applications.
- **Numeric model:** 64-bit integer vs arbitrary precision; decimals/rounding; JSON exchange; cross-runtime conformance.
- **Error model:** category naming, source locations, `try`/`catch` semantics, and bilingual diagnostics.
- **Package trust:** registry ownership, publisher verification, reproducible builds, dependency security.
- **Concurrency and IO:** async behavior, capability permissions, browser/node/native availability and threat model.
- **Governance:** proposal/review process for vocabulary, grammar, library APIs and breaking changes.

## 5. Non-goals of the first native milestone

No promise of Python compatibility, no automatic conversion of Python packages, no unrestricted operating-system APIs, no claim to match Python speed, no claim to replace C++/Rust/Python today, and no claim of self-hosting or installable bytecode.

## 6. Acceptance criteria for the first native milestone

1. C++20 build succeeds with only a compiler and CMake.
2. `kasa-native run examples/hello.kasa` prints `Maakye, Ghana!` without invoking Python.
3. `kasa-native check` analyzes syntax without running user code.
4. `kasa-native disasm` shows genuine bytecode operations (`CONST`, `MUL`, `PRINT`, `JUMP`, etc.).
5. Reference comparison covers arithmetic, Twi Unicode identifiers, conditions, loops, functions, recursion, lists, input, and representative errors.
6. Error and resource limits are enforced; missing `awiei`, undefined variables and division by zero are diagnosed.
7. The original master spec and existing runtimes stay unchanged.
8. Cross-platform CI is ready to run when GitHub account Actions restrictions are resolved; no false claim of passing hosted CI.
