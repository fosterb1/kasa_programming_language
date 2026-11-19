# Kasa forward development sequence — approved 2026-11-19

This is the **forward-looking development priority order** established after the Windows recovery verification work. Historical documents using "Phase 8" or "Phase 9" for other workstreams remain historical records and are **not renumbered retroactively**. These phases define the order of upcoming work, not evidence that a phase is complete.

| Order | Phase | Primary outcome | Acceptance gate |
| ---: | --- | --- | --- |
| 1 | **7 — Cross-runtime language correctness** | Stable portable contract across Python, browser JavaScript, C++ native VM and KBC bytecode | Full local parity profile, exact build ID, shared success/error fixtures, all applicable runtimes checked; divergences documented and repaired |
| 2 | **8 — Practical Kasa data and finance libraries** | Offline money/integer-subunit, CSV, inventory and auditable reporting building blocks, no unreviewed Twi tokens | Design RFC and threat model; tests for money overflow, rounding/units, invalid CSV, I/O permissions, deterministic reports, cross-runtime behavior for supported APIs |
| 3 | **9 — Browser playground and Academy delivery** | Real browser JS/WASM playground, Netlify publication, Academy /playground iframe and configurable CMS Netlify URL | Real-browser and WASM execution, production HTTPS deployment confirmation, CMS setting save/reload, embedding, mobile/a11y/offline checks |
| 4 | **10 — Curriculum and developer experience** | Better beginner lessons, Twi review, exercises, examples, editor integration | Independent instructor review, sample learner tests, editor smoke checks |
| 5 | **11 — Public alpha / governance** | Licenses, security validation, release evidence, signed and tested supported distributions | Owner-selected license, official platform matrix, reproducible hashes, installer tests in disposable VM, public pilot |
| 6 | **12 — Kasa 1.0 stable roadmap** | Stable language contract, supported package ecosystem and compatibility policy | Versioned compatibility matrix and maintained release process; never inferred from alpha prototype completion |

## Execution rules

1. Finish and document **Phase 7** before beginning new *Phase 8 implementation*. Early research and specification may overlap, but shipping a money/data API without parity guarantees is not an approved shortcut.
2. Then prioritize **Phase 8 practical libraries**, before **Phase 9 browser + Academy integration**. Existing browser/Academy implementations remain available for regression testing; do not pause security fixes or repairs of regressions simply because their phase is later.
3. Keep a narrow independent verification loop for every change: direct unit tests, cross-runtime conformance where applicable, change logs, clear unverified gates, and Windows local commands as necessary. GitHub Actions billing is not a development blocker.
4. No language feature is invented by translating Python keywords. Any new Twi keywords must follow the evidence/review process in `docs/LANGUAGE_RESEARCH_POLICY.md`.
5. Practical computing must support Ghana-focused contexts but avoid implying production accounting correctness until fixed-point, auditability, validation and permission requirements are established.
6. Existing Windows recovery Phase 6F.5's isolated reconstruction was verified on the user's Windows workstation (37 pass, 2 skipped in its combined targeted test). Actual Windows installer lifecycle and rollback remain blocked pending isolated VM execution.

## Phase 7 kickoff

The next action on the user's Windows checkout is:

```bat
git pull --ff-only
python scripts/verify_local.py --profile parity
```

Record full stdout/stderr, exact commit, return code, and skipped stages. Fix **actual** divergent semantics in descending order: crashes or corruption, arithmetic/large-number discrepancies, Unicode/error locations, output/resource budgets, then bytecode consistency. Do not silently mark a skipped/missing native compiler step as successful.

## Phase 8 scope and research

Begin only after the core semantics gate. Specify **integer pesewas** as the beginner teaching representation, then consider explicitly scaled fixed-point money types and CSV routines with strict validation. Test multiple debit/credit cases and edge conditions. Avoid new syntax unless independently reviewed.

## Phase 9 delivery requirements

The existing playground and Academy have a partially implemented path; the Netlify deploy guide is `docs/NETLIFY_DEPLOYMENT.md`. The production URL entered via **CMS → Website Settings → Playground Settings → Netlify Playground URL** must be verified live. Do not claim hosted deployment, real WebAssembly availability or CMS persistence merely because source code and build tests pass.

## Phase 8 strategy selection — balanced standard library (2026-11-19)

The owner selected the **balanced standard library** direction. Phase 8 therefore alternates foundational general-purpose functionality (math, collections, text, statistics, data formats, safe files and tests) with carefully specified money, validation, inventory and reconciliation capabilities. Avoid optimizing solely for finance or claiming Kasa is an accounting-specific language.

Initial source-level implementation: `stdlib/experimental/math.kasa`, `stdlib/experimental/collections.kasa`, shared Python/JavaScript/native/KBC1 fixture runners. These are not true importable modules. Refer to [Phase 8 balanced library roadmap](./PHASE_8_BALANCED_STDLIB.md).

## Research-first Phase 8 development policy (2026-11-19)

Following the current module-system verification checkpoint, library development proceeds **group by group** using [the researched nine-group ecosystem map](./LIBRARY_ECOSYSTEM_RESEARCH_2026_11.md). The approach covers general language essentials, text, interchange formats, finance, storage, education and eventual optional frameworks rather than favoring a finance-only library.

Each group requires a reviewed minimum contract, shared cross-runtime test fixtures, adversarial tests and a completed acceptance note before its successor becomes the primary sprint. No new language syntax, package name, public import support or stable release claim is created merely by approving this plan. Preserve Phase 9 browser/Academy deployment for after the planned Phase 8 scope.
