# Kasa 0.4 — Independent parity-profile runner verification

**Date:** 2026-11-18  
**Status:** New focused verification profile **merged into main** in [PR #24](https://github.com/fosterb1/kasa_programming_language/pull/24), commit `6bb82da224496b1da92d096ca678a324ec4c4da7`; **full cross-runtime execution remains pending**.  
**Scope:** Local test orchestration and Git revision metadata, not confirmation that Python/native/KBC1 outputs are identical.

## Why this was added

Kasa already has a comprehensive `--profile full` verifier. However, frequent numeric and runtime changes should be checked with a smaller, focused conformance gate rather than waiting for a full WASM or unrelated integration run. Hosted GitHub Actions remain **manual-only** because the project owner prefers independent tests without automatic hosted-runner expenses.

The new `--profile parity` runs the following **seven sequential checks**:

| Check | Purpose |
|---|---|
| Python semantic conformance | Python interpreter regressions, remainder and source coordinates |
| JavaScript semantic conformance | Browser interpreter fixtures, including numeric and Unicode |
| Native CMake configure | Build environment and native compiler configuration |
| Native C++ build | Compile native VM, KBC1 loader and all native test executables |
| Native mixed-number precision smoke | Exact int64/binary64 comparison logic |
| Native Python conformance | Direct native and KBC1 execution versus Python reference |
| Native KBC1 round-trip and rejection tests | Serializing, validating and executing bytecode; corrupted inputs |

This is a **focused conformance** profile. It does **not** run every full-profile smoke test, browser WASM protocol checks, security audit or Windows/macOS validation.

## Reproducible commands

From a complete repository checkout with Python, Node.js, CMake and a C++20 compiler:

```sh
python -m pip install -e ".[dev]"
python scripts/verify_local.py --profile parity \
    --report build/parity-report.json

# Inspect the plan without executing code:
python scripts/verify_local.py --profile parity --dry-run \
    --report build/parity-plan.json

# Comprehensive local verification remains a separate step:
python scripts/verify_local.py --profile full
```

A **dry run produces seven `not_run` records, not seven passes**. A failed CMake configure/build marks downstream native checks `not_run` with the blocking reason and produces a failing exit code. No test result should be silently dropped.

## Source identity and dirty-worktree metadata

Each JSON report now has `source_revision.commit` (Git SHA when available) and `source_revision.working_tree_clean` (true, false or null). The helper checks both tracked and untracked working tree changes, excluding ignored generated build artifacts as Git itself does. If the repository has no valid Git metadata, both values are **null**, not invented.

This makes it easier to distinguish a verified release commit from a local working directory containing uncommitted changes.

## Independent checks performed

A focused reconstruction of the `plan()` and `source_revision()` Python functions was checked locally with Python 3.13.5, not a complete repository checkout.

- **4/4 plan shapes passed:** quick seven steps, parity seven steps with the expected sequence, full 15 steps, full-with-WASM 17 steps.
- **5/5 revision-helper scenarios passed:** non-Git directory, clean Git checkout, untracked file, modified tracked file, and restored clean checkout.

These are checks of the **extracted plan and metadata logic**; the full merged Python verifier script and its newly added pytest test module have **not** been independently executed in a complete checkout.

## Outstanding verification gate

- The **58 added Python-versus-KBC1 fixtures** and **18 numeric comparison fixtures** have not been rerun together against the complete native compiler on this exact revision.
- A full Python pytest and Node.js test run is still required before asserting 0.4 cross-runtime conformance.
- Real WASM runtime execution, malformed/untrusted bytecode security review, native Windows/macOS builds and human Twi terminology approval remain separate release gates.

**Next step:** Run `--profile parity` locally on a complete checkout, retain the JSON report, inspect any failures, and update `docs/DEVELOPMENT_JOURNAL.md` with actual observed outcomes. Do not mark the language as stable based on a planned or simulated test.
