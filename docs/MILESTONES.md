> **Historical milestone snapshot.** Current progress estimates and unresolved release gates are maintained in [PROGRESS_SCORECARD.md](./PROGRESS_SCORECARD.md).

# Kasa expansion: implementation tracker

These are development milestones, not five completed major releases.

| Workstream | Implemented in this branch | Remaining |
|---|---|---|
| 1. Native WebAssembly | Existing browser bridge improved with a module validator and an Emscripten CI build path | A real compiled WASM artifact and live browser verification; Emscripten not installed in the authoring environment |
| 2. Cross-runtime language standard | Shared JSON fixtures + Python, Node and native conformance runners; semantics draft | Resolve integer, decimal, Unicode and diagnostic differences |
| 3. Kasa bytecode ecosystem | `.kbc` compile/read/run/check/disassemble, CRC32 integrity and structural verifier | Versioned stable format, modules, standard library, package manager, fuzzing |
| 4. Developer tools | Unpublished VS Code extension with highlighting, snippets, Run/Check commands | VS Code live testing, debugger, LSP, editor packaging and marketplace identity |
| 5. Educational offline release | Installable PWA shell, offline cache, 15 validated examples, tutorial and release checklist | Full on-device PWA testing, teaching review, license approval, CI and signed releases |

The long-term mission is to make Kasa its **own well-specified language**;
no implementation should be described as a Python syntax wrapper. Native C++
bytecode execution already runs without Python, but semantics and packages
must be carefully designed before promising a production language ecosystem.
