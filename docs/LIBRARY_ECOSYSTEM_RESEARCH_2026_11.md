# Kasa library ecosystem research and group-by-group development plan

**Research date:** 2026-11-19  
**Status:** Research-backed proposal; not a claim that named modules exist.  
**User decision:** Balanced general-purpose standard library with practical finance/data strengths. **Complete the current module-system test first; then plan and execute one group at a time.**  
**Historical roadmap:** Phase 7 → Phase 8 library ecosystem → Phase 9 browser/Academy delivery.

## 1. Method and comparative research

Reviewed primary project documentation (`RFC-0009`, `PHASE_8_BALANCED_STDLIB.md`, `RFC-0006`), official documentation for Python, Rust, Go, Node.js, and published RFC/Unicode/OWASP/SQLite technical references. References are listed below. Names in this roadmap are **candidate Kasa API namespaces**, not native keywords, existing importable packages, or approved Twi vocabulary.

**Core architecture decision:** distinguish (a) runtime primitives needed by the language, (b) versioned built-in standard-library modules that work offline, and (c) opt-in ecosystem packages with additional capabilities or dependencies. Never depend on a specific Python/Node runtime at execution time just because a similar Python/Node library exists.

| Comparison | What the reference ecosystem illustrates | Kasa decision |
| --- | --- | --- |
| Python (math, decimal, pathlib, csv, json, sqlite3, unittest) | Broad standard library, external ecosystem separate | Small and portable initial core; adopt interoperable data formats rather than cloning all APIs |
| Rust (std plus crates.io) | Conservative core, powerful third-party libraries | Keep ML, large frameworks, domain applications optional and independently versioned |
| Go (packages like encoding/json, encoding/csv, testing, net/http) | Standard solutions to routine developer tasks | Specify small composable APIs with clear test contracts |
| Node.js (built-in APIs plus npm) | Modules, file/network capabilities, async runtime | Do not pretend browser and desktop have identical host permissions; give explicit capability policy |
| CSV RFC 4180; JSON RFC 8259 | Formal widely interoperable interchange definitions | Build parsers/serializers against conformance fixtures, not undocumented behavior |
| Unicode UAX #29 and CLDR | Grapheme segmentation differs from code point counting; currency metadata exists | Specify text units and currency scales; preserve source-column contract separately |
| Python decimal | Decimal arithmetic needs precision/rounding policy | Start exact integer subunits, then tested decimal type, no automatic binary float mixing |
| OWASP CSV injection | Spreadsheet-compatible output can execute formulas from untrusted fields | Escaping alone does not prove CSV safe for spreadsheet consumers; add export-specific mitigations |
| SQLite | Mature embedded transactional database | Prefer a bound, permission-limited SQLite backend; do not build a bespoke DBMS |

## 2. Current baseline and gap

**Implemented:** Python/JavaScript interpreter, native C++/KBC1 alpha, 11/11 Windows parity stages on clean `5067c5b`, six finance-subunit lesson fixtures, and five source-level helper functions (`kasa_abs`, `kasa_clamp`, `kasa_sum`, `kasa_count_equal`, `kasa_contains`). User confirmed native/KBC1 standard-library test **PASS**; precise final stdout wasn't attached. Source-level helpers are **concatenated by test harness**, not imported.

**Not yet implemented:** import namespaces, stable module ABI/versioning, structured map/record values as a documented portable contract, permissioned host-file APIs, structured date/decimal/money runtime types, a library package manager, production CSV/JSON libraries. Building convenience functions must not be confused with completing these contracts.

## 3. Library groups and category register

Priorities: **P0 = foundational**, **P1 = first general-use standard library**, **P2 = next**, **P3 = later**, **P4 = optional ecosystem**. Subgroups may be parallel only when dependencies and test gates are satisfied.

| Group | Proposed modules | Core target and prerequisites | Tier / initial priority | Exit evidence |
| --- | --- | --- | --- | --- |
| **G0. Module and safety foundation** | `kasa.modules`, `kasa.errors`, `kasa.capabilities`, internal conformance harness | Namespaced, deterministic local library resolution; error categories; quotas; deny-by-default host permissions | Runtime, **P0** | Unknown/duplicate imports, collisions, traversal, symlinks, cycles, version mismatch, KBC identity; Python/JS/native/KBC passing |
| **G1. Math and basic collections** | `kasa.math`, `kasa.collections`, `kasa.stats`, `kasa.random` | Checked integer operators, bounds, list operations, reproducible stats; seeded vs secure random distinctly scoped | Core standard, **P1** | Empty, extreme, overflow, signed values, mutation policy, exact output parity |
| **G2. Text and language** | `kasa.text`, `kasa.unicode`, `kasa.regex`, `kasa.locale`, `kasa.twi` | UTF-8 validation; code point vs grapheme units; Unicode normalization and localization; regex limits; human-reviewed Twi | Core plus optional locale datasets, **P1/P2** | Combining marks, Akan letters, casefold, invalid UTF-8, long inputs, resource quotas, educator review |
| **G3. Validation and interchange** | `kasa.validate`, `kasa.json`, `kasa.csv`, `kasa.data` | Structured values/schema, bounded parsers, deterministic serialization, table operations, CSV formula risk | Standard and optional table engine, **P1/P2** | RFC-oriented fixtures, malformed encodings/quoting, nesting/size bounds, spreadsheet-safe exports, round trips |
| **G4. Precise numeric and money** | `kasa.decimal`, `kasa.money`, `kasa.finance` | Fixed scale, rounding policy, currency codes/subunit scales, checked arithmetic, no implicit FX conversion | Standard + domain toolkit, **P1/P2** | Half-way rounding, signed zero, overflow, currency mismatch, unsupported scale, multi-engine agreement |
| **G5. Time, files and persistence** | `kasa.datetime`, `kasa.files`, `kasa.path`, `kasa.sqlite`, `kasa.storage` | Timezone and calendar contracts; sandboxed path access; atomic save; SQLite binding | Core datetime, capability-gated OS modules, **P2/P3** | Traversal and symlink denial, process permissions, partial writes, timezone/DST edge cases, transaction rollback |
| **G6. Practical business and education** | `kasa.inventory`, `kasa.reconcile`, `kasa.report`, `kasa.education` | Compose G3/G4/G5, stable IDs, auditable exceptions, curriculum patterns, no auto-approved ambiguous matches | Optional supported packages, **P2/P3** | Duplicate ID, split settlement, currency mismatch, revisions, deterministic replay, realistic sample corpus |
| **G7. Developer tools and secure communications** | `kasa.test`, `kasa.log`, `kasa.cli`, `kasa.http`, `kasa.crypto`, `kasa.uuid` | Test assertions first; logging; CLI parsing; capability-limited network; vetted crypto primitives, UUID standards | Test tools early; network/crypto later, **P1/P3** | Assertions in all runtimes, structured errors, no secret leakage, TLS tests, crypto test vectors, UUID RFC 9562 |
| **G8. Advanced optional ecosystem** | `kasa.web`, `kasa.db`, `kasa.async`, `kasa.gui`, `kasa.ml`, `kasa.ai`, `kasa.visualize` | Significant host APIs, threading, UI, Python/C++ bindings and security governance | Optional third-party ecosystem, **P4** | Defined target platform, vetted backends, compatibility tests, realistic app examples, maintenance ownership |

The table lists **40+ proposed namespaces**; not a delivery commitment. Large frameworks, full NLP and ML systems are **not** prerequisites for a credible Kasa 0.5 standard library.

## 4. Approved working order — one group at a time

| Sprint order | Group | Deliver first | Must not start as official library until |
| ---: | --- | --- | --- |
| 0 | G0 modules/security | One minimal namespaced, local, allowlisted module | Full parser/VM/KBC versioning and namespace collision spec; reject escapes/cycles |
| 1 | G1 math/collections | Promote the current five helpers with validated contracts | Native extreme bounds, invalid clamp range, type errors and source parity |
| 2 | G2 text/unicode | UTF-8 checks, count/slice, normalize (explicit units) | Shared Unicode expectations and version pinning |
| 3 | G3 validation/JSON/CSV | Validator, pure string parse/serialize first | Records/maps contract and resource quotas; no host files |
| 4 | G4 decimal/money | Currency-tagged fixed-subunit values with checked arithmetic | Rounding, scale and overflow spec; multi-engine value representation |
| 5 | G5 date/files/storage | Date primitives first, opt-in local file I/O later | Capability model and real OS-host integration |
| 6 | G6 practical packages | Inventory and reconciliation using G3+G4 | Reviewable audit trail, transaction identities and exception handling |
| 7 | G7 developer/network | Test/log/CLI foundations can be built early; HTTP/crypto later | Separate security audits for file/network/crypto permissions |
| 8 | G8 ecosystem | App frameworks, analytics/ML/AI as independent packages | Stable modular ABI and maintainer capacity |

**Parallel exceptions:** Fundamental `kasa.test` and `kasa.errors` serve as internal harnesses from G0 and can improve alongside any group. Security hotfixes and old regression failures are not postponed by sequencing.

## 5. Every group must pass the same quality gate

1. **Design:** problem statement, minimum API, input/output types, errors, portability/permission policy, deterministic tests, non-goals.
2. **Implement:** pure Kasa source for portable logic; native bindings only when needed and guarded by capabilities; no host Python/JS interpreter dependency in the native binary.
3. **Test:** shared JSON fixture corpus across Python interpreter, Node JS runtime, native C++ source, native compiled KBC1; opt-in KBC2/WASM when relevant. Record exact revision and stage counts.
4. **Adversarial:** empty, invalid, huge, Unicode, overflow, resource cap, corrupted/truncated input; documented expected failure category.
5. **Teach:** beginner examples, Twi-first explanations with linguistic review where vocabulary changes, API/tutorial documentation.
6. **Review:** mark `experimental`, `preview` or `stable` explicitly; keep breaking changes versioned and record known gaps.
7. **Proceed:** work on next group only once the previous group's narrow acceptance gate passes. Not all listed modules in one group must be shipped simultaneously; group exit must name the agreed minimum subset.

## 6. Architecture decisions before writing APIs

- **Language type surface:** Determine whether modules can expose records/maps and namespaced functions. If not, classify advanced structures as blocked and resist pretending a list of values is a strong Money type.
- **Portability:** Core pure functions available offline on desktop and browser. `files`, `sqlite`, `http`, UI are capability/platform-dependent and must report unsupported availability explicitly.
- **Numeric interoperability:** KBC1 native signed-64-bit behavior differs from Python/JS large-integer capability; prevent silent overflow and test shared portable subset separately from expanded KBC2.
- **Text correctness:** Preserve existing code-point source coordinates; library-visible grapheme and locale operations specify their own units.
- **Security:** Parsing untrusted files/CSV/JSON and interpreting unsigned bytecode are distinct risk boundaries; never treat a checksum as authenticity.
- **Package governance:** Built-in stdlib gets fixed language-version compatibility; optional packages get separate version, dependencies, checksums and trust review. Do not call a GitHub public repo automatically open-source without a license.

## 7. Authoritative sources reviewed

1. Python standard library: https://docs.python.org/3/library/
2. Python decimal: https://docs.python.org/3/library/decimal.html
3. Python import system: https://docs.python.org/3/reference/import.html
4. Rust standard library: https://doc.rust-lang.org/std/
5. Go standard packages: https://pkg.go.dev/std
6. Node API modules: https://nodejs.org/api/
7. CSV format: https://www.rfc-editor.org/rfc/rfc4180
8. JSON standard: https://www.rfc-editor.org/rfc/rfc8259
9. Unicode UAX #29: https://www.unicode.org/reports/tr29/
10. Unicode CLDR: https://www.unicode.org/reports/tr35/
11. OWASP CSV formula injection: https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/07-Injection/21-CSV_Injection/
12. SQLite transactions: https://www.sqlite.org/lang_transaction.html
13. UUID RFC 9562: https://www.rfc-editor.org/rfc/rfc9562
14. Kasa module proposal: [RFC-0009](./RFC-0009-kasa-module-system.md)
15. Kasa balanced stdlib prototype: [Phase 8 balanced plan](./PHASE_8_BALANCED_STDLIB.md)

The sources support technical architecture and interoperability choices, **not** a claim that the proposed Kasa API names or order are mandated by any standard. Priorities reflect project constraints and the owner's chosen balanced approach.
