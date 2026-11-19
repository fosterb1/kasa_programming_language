# Group 0 — Pinned local source linker (first implementation checkpoint)

**Date:** 2026-11-19  
**Status:** Implemented in source, verification pending local Windows output.  
**Roadmap:** [Kasa library ecosystem research and group plan](./LIBRARY_ECOSYSTEM_RESEARCH_2026_11.md) → G0 infrastructure first → G1 math/collections.

## What we built

A **source-linking utility**, `scripts/link_kasa_stdlib.py`, permits two exact repository-vetted module identifiers:

- `math` → `stdlib/experimental/math.kasa`
- `collections` → `stdlib/experimental/collections.kasa`

It reads the app and both libraries, verifies each library against a pinned Git blob content ID, checks that declared functions do not collide with each other or application functions, and writes a **new** combined `.kasa` file. The output is restricted to `build/stdlib-linked/`; existing files cannot be overwritten. It refuses unknown module IDs, unsafe/path-like strings, symlinked library sources, symlinked/junction output roots, missing files, invalid UTF-8 and over-50KB combined source. CRLF library checkouts on Windows are canonicalized to LF for comparison with the Git blob IDs. It does **not** run the program, invoke a compiler, update an installation, edit PATH, or download dependencies.

This is **not a Kasa language import implementation**: no `import` keyword, namespace isolation, exported metadata, package registry, dependency graph or bytecode module linkage is provided. The selected helper functions are still inserted into one application scope. It is an explicit intermediate step only, not completion of RFC-0009.

Content pins use the Git blob SHA-1 format for detecting unexpected source changes. They are **not signatures or trusted-publisher authenticity**, do not protect against adversarial SHA-1 collision attacks, and depend on the integrity of the source checkout. Path checking is defense-in-depth, not a fully adversarial race-free filesystem sandbox.

## Run on Windows (with venv activated)

```bat
git pull --ff-only
python -m pytest -q tests/test_link_kasa_stdlib.py
python scripts/link_kasa_stdlib.py --app stdlib/demos/group0_sample.kasa --module math --module collections --output build/stdlib-linked/group0-demo-001.kasa
python -m kasa run build/stdlib-linked/group0-demo-001.kasa
build\kasa-local\Release\kasa-native.exe run build\stdlib-linked\group0-demo-001.kasa
```

If `python -m kasa run` is not accepted in a given checkout, consult the CLI README/ `python -m kasa --help` and use the supported run command; never assume a binary exists if native compilation was skipped.

Expected app stdout:

```text
300
2
nokware
```

**Important:** `group0-demo-001.kasa` must not exist; the linker refuses to overwrite. For a second test use a fresh filename `group0-demo-002.kasa`, not deletion of existing user files.

## How this checkpoint was implemented

1. Investigated limitations in existing concatenation-based `stdlib/experimental` sources and reviewed RFC-0009.
2. Defined a fixed allowlist with pinned blob identity (no arbitrary path loading).
3. Added cross-platform source canonicalization and output isolation.
4. Added tests for two-library success, actual Python execution, modified library content, duplicate/unsafe module IDs, application collisions, invalid UTF-8, large source, and symlink defenses.
5. Added a plain Kasa demonstration app.
6. **Pending:** execute the tests and source-linked app on Windows and run native source/KBC1 parity; the current development environment has not independently executed this new unit suite. Do not mark it passed solely because it is committed.

## What it enables now

It offers a deterministic way for a developer to assemble an existing Kasa application from vetted library source without copying function bodies manually. A successful linked program can be tested using existing Python/native interpreters, and then compiled to KBC1 using the existing CLI if desired.

## Next G0 slices, not yet shipped

1. Formal module declarations and explicit exports.
2. Namespace isolation and name binding across Python/JS/native.
3. Dependency graph with stable cycle and duplicate diagnostics.
4. Content identity and module bundling policy for bytecode.
5. Cross-runtime, negative-case and adversarial conformance.

Then finish the G0 acceptance gate before making G1 the primary sprint. After **each group** record how it was implemented, what it can do, actual test evidence, known limits and the next group.

## Windows regression found and corrected (2026-11-19)

User executed `python -m pytest -q tests/test_link_kasa_stdlib.py` on Windows 10 / Python 3.15.2 and reported **15 passed, 2 skipped, 1 failed**. The failing test `test_windows_crlf_checkout_is_canonicalized` converted every LF into CRLF without accounting for a checkout that was already CRLF, accidentally generating **CRCRLF**. The production linker correctly refuses lone carriage returns after removing valid CRLF pairs. This failure is in the **test fixture**, not evidence of a production linker defect.

**Correction commit:** `f5b2929` first converts source CRLF to LF and only then constructs valid CRLF. Added an explicit negative test that malformed CRCRLF is refused with no output file created. The line-ending byte transformations passed an isolated Python logic check; **the full corrected pytest suite still needs to run on Windows**. Expected on a Windows workstation without symlink permission: **17 passed, 2 skipped**; actual results take precedence.

```bat
git pull --ff-only
python -m pytest -q tests/test_link_kasa_stdlib.py
```

Do not delete existing output files just to rerun an example; use a new filename.
