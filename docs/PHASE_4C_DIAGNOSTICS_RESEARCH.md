# RFC research memo — Phase 4C developer diagnostics, 2026-11-19

Status: **Research-informed prototype**, not language-standard approval.

## Primary references reviewed

1. Rust Compiler Development Guide, [Errors and lints](https://rustc-dev-guide.rust-lang.org/diagnostics.html): code spans, understandable message, notes, help and suggestions; automated edits need confidence.
2. Microsoft, [Language Server Protocol specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/): structured diagnostic range, severity, code and related information. Kasa v0.4 does **not** claim to implement LSP yet.
3. [An Introduction to Elm](https://guide.elm-lang.org/types/): friendly error feedback that helps learners reason about values and types; emulate the principle, not Elm's syntax.
4. [CodeMirror](https://codemirror.net/): editor supports mobile, syntax highlighting and extensible language modes. Evaluate for phase 4C.3 after diagnostics reliability and offline size tests.
5. [Monaco Editor accessibility guidance](https://github.com/microsoft/monaco-editor/wiki/Monaco-Editor-Accessibility-Guide): professional editor assistive-technology considerations, particularly screen-reader interaction and editing shortcuts.
6. [Africa Education Watch Ghana school infrastructure review](https://www.wathi.org/wathinotes-systemes-educatifs/ghanas-basic-education-infrastructure-progress-gaps-and-strategies-towards-2030-africa-education-watch-april-2025/): school technology and electricity access gaps; avoid assuming fast, personal desktop computers.
7. [Ghana digital participation and access–competence gap study](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1815060/full): mobile access does not guarantee ability to use digital tools effectively. Offer learning scaffolding.
8. [Research ICT Africa, After Access Ghana](https://researchictafrica.net/wp-content/uploads/2025/10/AfterAccess_Ghana-Household-Report_2022_RIA_2025.pdf): mobile-data cost constraints support a small, locally cached, usable offline UI.

## Implementation decisions and tradeoffs

- **Don't mutate language syntax.** Compiler messages remain authoritative; a tiny client-side helper reads them and presents explanation, code, source line/column, a single cautious hint and the full original message.
- **Do not silently rewrite learner code.** Suggestions such as `se`→`sɛ` occur only after the interpreter itself reports a syntax failure at that line; different languages can use `se` legitimately as an identifier. The diagnostic is advisory.
- **Use only UTF-8 source and Unicode-aware name checks.** Kasa's syntax contract requires case-sensitive Unicode names. Do not assume English word boundaries or ASCII-only identifiers.
- **No false AI certainty.** The helper recognizes a restricted set of actual existing error messages. Unknown or changed messages are displayed without invented line numbers, guesses or fake fixes.
- **One error, one next action.** Provide expert error category, exact code `KASA-...`, line/column where available, explanation and example; beginners can expand original detail.
- **Preserve original engine semantics.** JavaScript and native WebAssembly can have different wording; future LSP and editor APIs must rely on structured compiler diagnostics, not on parsing strings forever.
- **Keep offline availability.** The helper is plain JavaScript, cached by the existing service worker. No API calls, models, sign-in or paid hosting dependencies.
- **Accessible rendering.** `role="status"`, legible contrast, plain `textContent` rather than `innerHTML`; avoids HTML injection from user code or interpreter messages.
- **Localization:** Begin with simple English explanations and genuine Kasa examples; fluent Akan language review precedes any 'official Twi translation' UI. Avoid conflating Twi reserved grammar with freely chosen identifiers.

## Verified diagnostic examples (initial implementation)

- `se nokware a`: KASA-KW001, cautiously suggests `sɛ`.
- `ka sikaa` after `ma sika = 5`: KASA-NAME001, suggests `sika`.
- `sɛ nokware` missing `a`: KASA-SYN002.
- Unterminated quoted string: KASA-SYN003.
- Division by zero: KASA-MATH001.
- Out-of-bounds list item: KASA-LIST001.
- Non-Boolean if condition: KASA-TYPE001.
- Unknown message: KASA-UNKNOWN, exposes engine text without an invented location.

## Scope of 4C.1 and next gates

The initial 4C.1 presentation helper is implemented on first-party Kasa Studio and maintained in this language repository to support Phase 4A synchronization. This is **not** a new compiler error API, compiler-core rewrite, or full LSP. Next 4C.2 work must test native C++, WASM and JavaScript against a shared source/error-category fixture set and review nonportable integer and floating-point boundaries identified in RFC-0007.

Phase 4C.3 should evaluate CodeMirror versus a native textarea on real low-cost mobile phones and offline shared computers. Professional syntax coloring must never make typing impossible or less accessible.

## Known hazards

- Parsing old human-readable engine strings is transitional and inherently brittle.
- Fixed-distance name typo suggestions may still confuse similarly named identifiers; never autoapply them.
- Messages about 0-based list indexes must not claim every list has three items.
- Source positions differ in error formatting between runtimes; normalize locations only after objective parity tests.
- A source change without updating the Studio asset release manifest or service worker is invalid. Regression suite must catch it.
