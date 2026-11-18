# Kasa release readiness — do not publish an official stable release yet

The changes under development are **alpha prototypes**, not Kasa 1.0.
Before an open-source public release, verify the following:

- [ ] **Owner selects a license** and commits a valid `LICENSE` file. The
      current repository has no granted open-source license. MIT was proposed
      but is **not** automatically approved.
- [ ] GitHub Actions runner billing lock resolved; all relevant CI jobs run.
- [ ] Emscripten actually builds a valid `.wasm` binary; full browser execution
      tested on Netlify, including JS fallback and offline behavior.
- [ ] Bytecode parser and VM fuzzed with untrusted input and audited; KBC1
      version and signature policy decided.
- [ ] Windows, macOS and Linux native installers built and tested.
- [ ] VS Code extension tested inside an Extension Development Host; publisher
      identity and extension marketplace rules addressed.
- [ ] Numeric semantics, Unicode diagnostics and module system specified.
- [ ] Twi vocabulary and teaching materials reviewed by fluent speakers and
      educators from relevant communities.
- [ ] Full conformance suite, security tests, and at least 15 `.kasa`
      examples pass with all applicable engines.
- [ ] Release version, checksum, changelog, reproducible build and provenance
      documented.

Do not call a feature shipped simply because it is on a development branch.
