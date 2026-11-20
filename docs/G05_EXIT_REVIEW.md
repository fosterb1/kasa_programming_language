# G0.5 Experimental Native Module Front-end — Exit Review

**Date:** 2026-11-21
**Branch:** `dev/g05-native-module-contract`
**Review outcome:** **EXPERIMENTAL FEATURE CANDIDATE; NOT A STABLE MODULE SYSTEM.**
**Evidence level:** Windows test passes are *owner-reported*. The most recent report says all corrected reproducibility tests and native/KBC1 safety tests passed. The terminal transcript and exact tested SHA of that final run were not supplied. The earlier first attempt was explicitly 53 passed, 1 failed, 1 skipped; commit `d2c5851` corrected the narrow test expectation. **Skip disposition remains unrecorded**. Do not infer that symlink security was exercised by the skipped test.

## Implemented and owner-verified in scope

| Capability | Evidence | Claim boundary |
|---|---|---|
| Twi-first experimental `fa ... firi stdlib` | Existing G0.4 Python/JS tests and G0.5 owner checkpoints | Not enabled as direct syntax in default native compiler |
| Hash-validated `math`, `collections` catalog | G0.5 preflight and linker tests | SHA pins consistency; does not authenticate third-party publishers |
| Restricted AST prelink and namespace separation | Synthetic collisions, public/private helper tests | Only function-only allowlisted libraries and direct qualified calls |
| Native source execution and KBC1 compile | Four-case Python/native/bytecode differential and one-command compile CLI | Portable tested subset, not arbitrary Kasa package imports |
| Source maps and mapped diagnostics | Source-map, mapped-runner tests | Statement-level only; no exact expression column, debugger or embedded KBC map |
| KBC1 independent execution and malformed inputs | Bytecode-without-source and five corruptions × check/execute | Existing KBC1 wire format unchanged; not a VM sandbox proof |
| Reproducible same-platform compilation | Duplicate build SHA-256 test, owner confirms corrected suite passed | One fixed native toolchain/configuration only |
| Failure without publishing artifacts | Source-size, import, link and output-path rejection tests | Excludes concurrent adversarial filesystem mutation/races |

## Review findings and residual risks

### R1 — output-directory TOCTOU / untrusted filesystem (BLOCKER for hostile multiuser environments)

`scripts/compile_g05_modules.py` checks `build/g05-compiled` is not linked, creates or reuses it and then opens the output by pathname. Another process with access to the build tree could swap a directory between checks. Exclusive `open("xb")` protects an existing target filename against overwrite, but **does not make parent-directory traversal race-free**. `scripts/link_kasa_modules_hygienic.py` has a similar directory/check-to-open interval. Remediation: explicitly document the tool as a *trusted local developer workflow* until directory-handle-based containment or an equivalent audited publication mechanism is available on Windows and POSIX. Do not describe this as safe for hostile multiuser uploads.

### R2 — local source/catalog mutation race (BLOCKER for untrusted shared workspaces)

The linker reads pinned sources and SHA-256 checks their bytes before emitting ordinary Kasa. This preserves catalog content identity for the bytes read, but the independent reads, directory path checks and subsequent native compiler call are not an audited adversarial race boundary. Only trusted, local workspace execution is supported.

### R3 — diagnostics remain approximate (NONBLOCKER for explicitly experimental usage)

Origin map reports **statement starts**. Native error expression columns and generated closing delimiters cannot always be mapped to an exact original token. No source map is embedded in KBC1. All user-facing documentation must say *statement-level annotation*.

### R4 — scope and grammar not stabilized (BLOCKER for stable language release)

The opt-in wrapper translates imports **before** invoking native parser. No native `fa` import parser, dynamic dependencies, third-party package source discovery, cyclic dependency model, versioned module artifacts or general runtime loader. Continue Twi speaker/community grammar review before freezing spelling.

### R5 — cross-platform reproducibility and browser delivery (BLOCKER for production release)

Same-platform duplicate-build comparison does not guarantee deterministic bytes across C++ compilers, OSes, or build flags. Kasa Academy/Netlify playback and true browser-import integration remain separate G0.4/browser deployment milestones and are not demonstrated by G0.5 native tests.

### R6 — skipped test explanation (EVIDENCE GAP)

Earlier eight-suite run showed one skipped test. The subsequent owner reply confirmed all passed, but did not paste the `pytest -rs` skip summary or confirm exactly which case was skipped. Until recorded, symlink rejection cannot be described as fully verified on the user's Windows account.

## Decision and exit criteria

**Decision: do not call G0.5 production-ready, do not mark PR #61 ready for merge solely from the current evidence.** The opt-in KBC1 compiler can be documented as an **experimental trusted-local workflow** for the two pinned standard libraries. No backwards-incompatible native grammar or bytecode changes should be merged to `main` as part of this proposal.

For a limited experimental merge decision, require:
1. Capture the exact `git rev-parse HEAD` and `pytest -q -rs` output from Windows, including why any test skipped; confirm native reproducibility and native diagnostic cases were **not** skipped.
2. Run `python scripts/verify_local.py --profile full` (not only `parity`) and report the result. The full profile runs wider native KBC1 smoke and mutation tests.
3. Recheck a fresh CLI compilation/output file without overwrite; capture correct `run-bytecode` stdout.
4. Keep the security caveat **trusted workspace only** prominently in the PR and end-user documentation.
5. Obtain reviewer approval of output publication and path traversal assumptions or harden the workflow before enabling shared/hosted execution.

For a **stable native module system**, require more: native import grammar specification, general semantic equivalence, exact diagnostic mapping plan, portable builds and a separate security threat model.

## Suggested next implementation

Prioritize an **experimental release-check command** collecting JSON evidence from the local revision, full native tests, G0.5 focused tests and both KBC scripts, while separating passes, failures and skips. Do not silently re-run or claim CI/GitHub tests on the owner's Windows machine.

No repository changes in this review affect the native runtime, KBC wire format or experimental language grammar.
